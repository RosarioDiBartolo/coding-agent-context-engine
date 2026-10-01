"""Reproducible real provider probes: python -m spikes.run [pydeps|serena|jev|all]."""
import argparse
import asyncio
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from .contracts import ProbeResult, normalize_jev, normalize_pydeps, normalize_symbols

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/python_repo'


def version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def fail(provider, operation, code, *, status='error', details=None, elapsed_ms=None):
    return ProbeResult(provider, operation, status, version=version(
        {'serena': 'serena-agent', 'jev': 'typesafe-sdk'}.get(provider, provider)),
        error={'code': code, 'details': details}, elapsed_ms=elapsed_ms).to_dict()


def ok(provider, operation, data, elapsed_ms=None):
    return ProbeResult(provider, operation, 'ok', version=version(
        {'serena': 'serena-agent', 'jev': 'typesafe-sdk'}.get(provider, provider)),
        data=data, elapsed_ms=elapsed_ms).to_dict()


def run_pydeps(out):
    if not version('pydeps'):
        return [fail('pydeps', 'snapshot', 'dependency_missing', status='blocked')]
    results = []
    expected = json.loads((FIXTURE / 'expected.json').read_text())
    flags = ['--show-deps', '--no-output', '--noshow', '--nodot', '--no-config',
             '--include-missing', '--max-bacon', '2']
    # Project-level target also tests unmapped files and test imports.
    for label, target in [('package', FIXTURE / 'demo'), ('unmapped', FIXTURE / 'maintenance.py'),
                          ('invalid_target', FIXTURE / 'absent.py')]:
        cmd = [sys.executable, '-m', 'pydeps', str(target), *flags]
        start = time.perf_counter()
        try:
            p = subprocess.run(cmd, cwd=FIXTURE, capture_output=True, text=True, timeout=45,
                               env={**os.environ, 'PYTHONPATH': str(FIXTURE)})
            elapsed = (time.perf_counter() - start) * 1000
            if p.returncode:
                results.append(fail('pydeps', label, 'process_error', details={
                    'exit_code': p.returncode, 'stderr': p.stderr[-2000:]}, elapsed_ms=elapsed))
                continue
            raw = json.loads(p.stdout)
            (out / f'pydeps-{label}-raw.json').write_text(json.dumps(raw, indent=2))
            normalized = normalize_pydeps(raw, FIXTURE)
            if label == 'package':
                edges = {(e['source'], e['target']) for e in normalized['edges']}
                assert all(tuple(edge) in edges for edge in expected['required_imports'])
                nodes = {n['module']: n for n in normalized['nodes']}
                assert nodes[expected['missing_import']]['resolution'] == 'unresolved'
                assert nodes['yaml']['resolution'] == 'external'
                assert not any(e['target'] == 'runtime_plugin' for e in normalized['edges'])
            (out / f'pydeps-{label}-normalized.json').write_text(json.dumps(normalized, indent=2))
            results.append(ok('pydeps', label, {'command': cmd, **normalized}, elapsed))
        except subprocess.TimeoutExpired:
            results.append(fail('pydeps', label, 'timeout'))
        except (ValueError, AssertionError) as e:
            results.append(fail('pydeps', label, 'contract_error', details=type(e).__name__))
    return results


async def run_serena(out):
    if not version('serena-agent') or not version('mcp'):
        return [fail('serena', 'lifecycle', 'dependency_missing', status='blocked')]
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import psutil

    results = []
    # The cloud sandbox uses a PID namespace with a host-mounted /proc.
    # psutil.Process() would mistake namespace PID 5 for unrelated host PID 5.
    proc_pid = int(os.readlink('/proc/self')) if sys.platform == 'linux' else os.getpid()
    own_process = psutil.Process(proc_pid)
    existing_pids = {p.pid for p in own_process.children(recursive=True)}
    with tempfile.TemporaryDirectory(prefix='contextengine-', dir=out) as tmp:
        repo = Path(tmp) / 'repo'
        shutil.copytree(FIXTURE, repo, ignore=shutil.ignore_patterns('__pycache__'))
        (repo / '.serena').mkdir()
        (repo / '.serena/project.yml').write_text(
            'project_name: contextengine-fixture\nlanguage_servers: [python_jedi]\nencoding: utf-8\n')
        env = {**os.environ, 'SERENA_HOME': str(Path(tmp) / 'serena-home'),
               'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')}
        cmd = str(Path(sys.executable).parent / ('serena.exe' if os.name == 'nt' else 'serena'))
        parameters = StdioServerParameters(command=cmd, args=[
            'start-mcp-server', '--project', str(repo), '--context', 'desktop-app',
            '--mode', 'planning', '--mode', 'no-memories', '--transport', 'stdio',
            '--enable-web-dashboard', 'false', '--open-web-dashboard', 'false',
            '--enable-gui-log-window', 'false', '--tool-timeout', '30'], env=env)
        tracked_pids = set()
        start = time.perf_counter()
        try:
            with (out / 'serena-stderr.log').open('w') as log:
                async with stdio_client(parameters, errlog=log) as (read, write):
                    async with ClientSession(read, write) as client:
                        async with asyncio.timeout(180):
                            await client.initialize()
                            tools = await client.list_tools()
                        tool_map = {t.name: t.model_dump(mode='json') for t in tools.tools}
                        (out / 'serena-tools.json').write_text(json.dumps(tool_map, indent=2))
                        tracked_pids = {p.pid for p in own_process.children(recursive=True)} - existing_pids
                        results.append(ok('serena', 'startup', {'tools': sorted(tool_map)},
                                          (time.perf_counter() - start) * 1000))

                        async def call(name, arguments, label=None):
                            label = label or name
                            if name not in tool_map:
                                r = fail('serena', label, 'capability_absent', status='unsupported')
                            else:
                                t = time.perf_counter()
                                try:
                                    async with asyncio.timeout(45):
                                        answer = await client.call_tool(name, arguments)
                                    raw = answer.model_dump(mode='json')
                                    text = '\n'.join(b.text for b in answer.content if b.type == 'text')
                                    if answer.isError or text.startswith(('Error:', 'Error executing tool')):
                                        r = fail('serena', label, 'tool_error', details=text,
                                                 elapsed_ms=(time.perf_counter() - t) * 1000)
                                    else:
                                        try:
                                            value = json.loads(text)
                                        except json.JSONDecodeError:
                                            r = fail('serena', label, 'unstructured_response', details=text)
                                        else:
                                            r = ok('serena', label, value, (time.perf_counter() - t) * 1000)
                                    (out / f'serena-{label}-raw.json').write_text(json.dumps(raw, indent=2))
                                except TimeoutError:
                                    r = fail('serena', label, 'timeout')
                            results.append(r)
                            return r

                        relative = 'demo/auth/tokens.py'
                        args = {'name_path_pattern': 'create_refresh_token', 'relative_path': relative,
                                'include_body': True}
                        await call('get_symbols_overview', {'relative_path': relative}, 'overview_cold')
                        await call('get_symbols_overview', {'relative_path': relative}, 'overview_warm')
                        before = await call('find_symbol', args, 'symbol_before')
                        await call('find_referencing_symbols', {'name_path': 'create_refresh_token',
                                                              'relative_path': relative}, 'references')
                        definition = await call('find_declaration', {'relative_path': 'demo/api/session.py',
                                   'regex': r'(create_refresh_token)\(get_user', 'include_body': True}, 'definition')
                        await call('find_symbol', {'name_path_pattern': 'no_such_fixture_symbol'}, 'empty')
                        await call('get_symbols_overview', {'relative_path': 'absent.py'}, 'missing_file')
                        target = repo / relative
                        target.write_text('# saved edit\n' + target.read_text().replace('refresh:', 'refresh-v2:'))
                        after = await call('find_symbol', args, 'symbol_after_edit')
                        # Normalize before/after against their own content snapshot.
                        normalized_before = normalize_symbols(before['data'], FIXTURE, acquisition='find_symbol') if before['status'] == 'ok' else []
                        normalized_after = normalize_symbols(after['data'], repo, acquisition='find_symbol') if after['status'] == 'ok' else []
                        sample = {'before': normalized_before, 'after': normalized_after,
                                  'definition': normalize_symbols(definition['data'], FIXTURE, acquisition='find_declaration') if definition['status'] == 'ok' else []}
                        (out / 'serena-normalized.json').write_text(json.dumps(sample, indent=2))
                        results.append(ok('serena', 'edit_observed', {
                            'fresh': 'refresh-v2:' in json.dumps(after.get('data')),
                            'before': before.get('data'), 'after': after.get('data'),
                            'snapshot_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}))
                        target.unlink()
                        deleted = await call('find_symbol', {'name_path_pattern': 'create_refresh_token'}, 'symbol_after_delete')
                        if deleted['status'] == 'ok':
                            results.append(ok('serena', 'delete_observed', {
                                'deleted_definition_absent': all(s.get('relative_path') != relative for s in deleted['data']),
                                'remaining_search_candidates': deleted['data']}))
                        await call('get_symbols_overview', {'relative_path': relative}, 'deleted_file')
                        tracked_pids |= {p.pid for p in own_process.children(recursive=True)} - existing_pids
        except Exception as e:
            # Only synthetic fixture operations; no credentials are sent to Serena.
            results.append(fail('serena', 'lifecycle', type(e).__name__, details=str(e)[:1000]))
        remaining = [pid for pid in tracked_pids if
                     (Path(f'/proc/{pid}').exists() if sys.platform == 'linux' else psutil.pid_exists(pid))]
        results.append(ok('serena', 'shutdown', {'tracked_children': len(tracked_pids),
                                                'remaining_pids': remaining}))
    return results


def run_jev(live):
    if not live:
        return [fail('jev', 'live_noul', 'live_not_requested', status='blocked')]
    if not os.getenv('TYPESAFE_API_KEY'):
        return [fail('jev', 'live_noul', 'credentials_missing', status='blocked')]
    if not version('typesafe-sdk'):
        return [fail('jev', 'live_noul', 'dependency_missing', status='blocked')]
    from typesafe_sdk import Noul, NoulAnswer, SystemOneResponse, TypeSafeClient, RetryPolicy

    class RelevantResponse(SystemOneResponse):
        relevant: NoulAnswer

    start = time.perf_counter()
    try:
        with TypeSafeClient(retry=RetryPolicy(max_retries=0), timeout=10) as client:
            response = client.system_one(
                state={'task': 'Find refresh token creation', 'candidate': 'def create_refresh_token(user): ...'},
                questions={'relevant': Noul(instructions='Does this candidate implement refresh token creation?')},
                response_model=RelevantResponse)
        raw = response.model_dump(mode='json')
        return [ok('jev', 'live_noul', normalize_jev(raw), (time.perf_counter() - start) * 1000)]
    except Exception as e:
        # Do not log URLs, response bodies, headers or SDK exception strings.
        return [fail('jev', 'live_noul', type(e).__name__, details={
            'http_status': getattr(e, 'status', None)}, elapsed_ms=(time.perf_counter() - start) * 1000)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('provider', choices=['all', 'pydeps', 'serena', 'jev'], default='all', nargs='?')
    parser.add_argument('--live-jev', action='store_true', help='One bounded request using existing environment configuration')
    parser.add_argument('--output', type=Path, default=ROOT / 'spikes/output')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    if args.provider in ['all', 'pydeps']:
        results += run_pydeps(args.output)
    if args.provider in ['all', 'serena']:
        results += asyncio.run(run_serena(args.output))
    if args.provider in ['all', 'jev']:
        results += run_jev(args.live_jev)
    report = {'schema_version': 1, 'python': sys.version.split()[0], 'platform': sys.platform,
              'live_jev_requested': args.live_jev, 'results': results}
    report_path = args.output / f'{args.provider}-report.json'
    report_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    # Expected error probes are excluded, but never hidden in the report.
    expected_errors = {'invalid_target', 'missing_file', 'deleted_file'}
    unexpected = [r for r in results if r['status'] != 'ok' and r['operation'] not in expected_errors]
    checks_failed = any(r['operation'] == 'edit_observed' and not r['data']['fresh'] or
                        r['operation'] == 'shutdown' and r['data']['remaining_pids'] or
                        r['operation'] == 'delete_observed' and not r['data']['deleted_definition_absent']
                        for r in results if r['status'] == 'ok')
    return 1 if checks_failed or any(r['status'] == 'error' for r in unexpected) else (2 if unexpected else 0)


if __name__ == '__main__':
    raise SystemExit(main())
