"""Offline contract tests are explicitly distinct from live Jev evidence."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from spikes.contracts import ProbeResult, normalize_jev, normalize_pydeps, normalize_symbols
from spikes.run import FIXTURE, run_jev


class ContractTests(unittest.TestCase):
    def test_empty_is_success_not_error(self):
        self.assertEqual(ProbeResult('x', 'find', 'ok', data=[]).to_dict()['data'], [])
        with self.assertRaises(ValueError):
            ProbeResult('x', 'find', 'error', data=[])
        with self.assertRaises(ValueError):
            ProbeResult('x', 'find', 'ok')

    def test_invalid_timing(self):
        for value in [-1, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                ProbeResult('x', 'find', 'ok', data=[], elapsed_ms=value)

    def test_paths_are_not_inferred_and_edges_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / 'a.py').write_text('')
            raw = {'a': {'path': str(repo / 'a.py'), 'imports': ['b']},
                   'b': {'path': None, 'imported_by': ['a']}}
            result = normalize_pydeps(raw, repo)
            self.assertEqual(len(result['edges']), 1)
            self.assertEqual(result['nodes'][0]['path'], 'a.py')
            self.assertIsNone(result['nodes'][1]['path'])
            self.assertEqual(result['nodes'][1]['resolution'], 'unresolved')

    def test_invalid_dependency_payload(self):
        for raw in [[], {'a': []}, {'a': {'imports': 'b'}}]:
            with self.assertRaises(ValueError):
                normalize_pydeps(raw, FIXTURE)

    def test_probability_validation(self):
        for p in [-0.1, 1.1, math.nan, True, '0.7']:
            with self.assertRaises(ValueError):
                normalize_jev({'answers': {'relevant': {'type': 'noul', 'noul': p}}})
        result = normalize_jev({'answers': {'relevant': {'type': 'noul', 'noul': 0.7}}})
        self.assertEqual(result['probability_yes'], 0.7)
        self.assertIsNone(result['usage'])

    def test_live_requires_explicit_flag(self):
        result = run_jev(False)[0]
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['error']['code'], 'live_not_requested')

    def test_symbol_locator_survives_line_move_but_snapshot_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / 'a.py'
            path.write_text('def f(): pass\n')
            raw = [{'name_path': 'f', 'relative_path': 'a.py', 'kind': 'Function',
                    'body_location': {'start_line': 0, 'end_line': 0}}]
            before = normalize_symbols(raw, repo, acquisition='find_symbol')[0]
            path.write_text('# edit\ndef f(): pass\n')
            raw[0]['body_location'] = {'start_line': 1, 'end_line': 1}
            after = normalize_symbols(raw, repo, acquisition='find_symbol')[0]
            self.assertEqual(before['locator'], after['locator'])
            self.assertNotEqual(before['file_sha256'], after['file_sha256'])
            self.assertIsNone(before['provider_id'])
            raw[0]['relative_path'] = '../outside.py'
            with self.assertRaises(ValueError):
                normalize_symbols(raw, repo, acquisition='find_symbol')

    def test_fixture_and_deliberately_unresolved_import(self):
        p = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'],
                           cwd=FIXTURE, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        p = subprocess.run([sys.executable, '-c',
                            'from demo.plugins import load_optional_provider; load_optional_provider()'],
                           cwd=FIXTURE, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('contextengine_missing_fixture_provider', p.stderr)


class SDKContractTests(unittest.TestCase):
    """Use the real SDK with a synthetic transport. These are NOT Jev live tests."""
    def test_typed_response_request_and_usage(self):
        import httpx2
        from typesafe_sdk import TypeSafeClient, RetryPolicy, Noul, NoulAnswer, SystemOneResponse

        class Response(SystemOneResponse):
            relevant: NoulAnswer

        captured = []

        def handler(request):
            captured.append(json.loads(request.content))
            return httpx2.Response(200, json={
                'model': 'synthetic-test-only',
                'answers': {'relevant': {'type': 'noul', 'noul': 0.8}},
                'usage': {'input_tokens': 10, 'output_tokens': 1}}, request=request)

        with TypeSafeClient(api_key='offline-test-key', transport=httpx2.MockTransport(handler),
                            retry=RetryPolicy(max_retries=0)) as client:
            response = client.system_one({'candidate': 'fixture'}, {'relevant': Noul(instructions='Relevant?')},
                                         response_model=Response)
        self.assertEqual(response.relevant.noul, 0.8)
        normalized = normalize_jev(response.model_dump(mode='json'))
        self.assertEqual(normalized['usage']['input_tokens'], 10)
        self.assertEqual(captured[0]['questions']['relevant']['type'], 'noul')

    def test_timeout_and_http_error_are_distinct(self):
        import httpx2
        from typesafe_sdk import (TypeSafeClient, RetryPolicy, Noul, TypeSafeAPITimeoutError,
                                 TypeSafeAuthenticationError)
        calls = []

        def timeout(request):
            calls.append(1)
            raise httpx2.ReadTimeout('synthetic timeout', request=request)

        def unauthorized(request):
            return httpx2.Response(401, json={'error': 'synthetic unauthorized'}, request=request)

        for handler, error in [(timeout, TypeSafeAPITimeoutError), (unauthorized, TypeSafeAuthenticationError)]:
            with TypeSafeClient(api_key='offline-test-key', transport=httpx2.MockTransport(handler),
                                retry=RetryPolicy(max_retries=0), timeout=0.1) as client:
                with self.assertRaises(error):
                    client.system_one('fixture', {'relevant': Noul(instructions='Relevant?')})
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
