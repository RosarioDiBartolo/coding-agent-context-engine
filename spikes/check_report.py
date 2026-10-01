"""Validate actual probe evidence, without promoting blocked Jev to success."""
import argparse
import json
from pathlib import Path


def assess(report):
    entries = {(r['provider'], r['operation']): r for r in report['results']}

    def record(provider, operation):
        return entries.get((provider, operation), {})

    required_ok = [('pydeps', 'package'), ('pydeps', 'unmapped'),
                   ('serena', 'startup'), ('serena', 'overview_cold'), ('serena', 'overview_warm'),
                   ('serena', 'symbol_before'), ('serena', 'references'), ('serena', 'definition'),
                   ('serena', 'empty'), ('serena', 'symbol_after_edit'), ('serena', 'edit_observed'),
                   ('serena', 'symbol_after_delete'), ('serena', 'delete_observed'), ('serena', 'shutdown')]
    checks = {f'{p}.{op}': record(p, op).get('status') == 'ok' for p, op in required_ok}
    for p, op in [('pydeps', 'invalid_target'), ('serena', 'missing_file'), ('serena', 'deleted_file')]:
        checks[f'{p}.{op}_is_error'] = record(p, op).get('status') == 'error'
    checks['empty_is_empty'] = record('serena', 'empty').get('data') == []
    checks['edit_is_fresh'] = (record('serena', 'edit_observed').get('data') or {}).get('fresh') is True
    checks['delete_is_fresh'] = (record('serena', 'delete_observed').get('data') or {}).get('deleted_definition_absent') is True
    shutdown = record('serena', 'shutdown').get('data') or {}
    checks['no_children_left'] = shutdown.get('remaining_pids') == [] and shutdown.get('tracked_children', 0) >= 2
    reference_paths = set((record('serena', 'references').get('data') or {}).keys())
    checks['references_include_unmapped_and_tests'] = {'maintenance.py', 'tests/test_session.py',
        'demo/api/session.py', 'demo/auth/tokens.py'}.issubset(reference_paths)
    definition = record('serena', 'definition').get('data') or {}
    checks['definition_is_target'] = definition.get('relative_path') == 'demo/auth/tokens.py' and definition.get('name_path') == 'create_refresh_token'
    jev = record('jev', 'live_noul')
    live_verified = report.get('live_jev_requested') is True and jev.get('status') == 'ok'
    local_passed = all(checks.values())
    return {'schema_version': 1, 'local_provider_checks': checks, 'local_providers_passed': local_passed,
            'jev_live_verified': live_verified, 'step0_status': 'completed' if local_passed and live_verified else 'partial',
            'step1_deterministic_prerequisites': local_passed,
            'jev_blocker': jev.get('error') if not live_verified else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    assessment = assess(json.loads(args.report.read_text()))
    print(json.dumps(assessment, indent=2))
    return 1 if not assessment['local_providers_passed'] else 0 if assessment['jev_live_verified'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
