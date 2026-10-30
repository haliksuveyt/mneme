#!/usr/bin/env python3
"""Stdio MCP server: protocol shape, argument mapping and subprocess protocol."""
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'template' / '.claude' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import mneme_v3_mcp as mcp  # noqa: E402


def call(name, arguments, run):
    return mcp.handle({'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call',
                       'params': {'name': name, 'arguments': arguments}}, run)


class McpTest(unittest.TestCase):
    def test_initialize_lists_tools_and_ignores_notifications(self):
        init = mcp.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                           'params': {'protocolVersion': '2024-11-05'}}, None)
        self.assertEqual(init['result']['protocolVersion'], '2024-11-05')
        self.assertIn('tools', init['result']['capabilities'])
        self.assertIsNone(mcp.handle({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, None))
        listed = mcp.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'}, None)
        names = {tool['name'] for tool in listed['result']['tools']}
        self.assertEqual(names, {'mneme_search', 'mneme_note_create', 'mneme_note_edit', 'mneme_supersede', 'mneme_doctor'})
        self.assertEqual(mcp.handle({'jsonrpc': '2.0', 'id': 3, 'method': 'nope'}, None)['error']['code'], -32601)

    def test_unknown_protocol_version_falls_back_to_a_supported_one(self):
        init = mcp.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '1999-01-01'}}, None)
        self.assertIn(init['result']['protocolVersion'], mcp.PROTOCOL_VERSIONS)

    def test_search_maps_to_context_command(self):
        seen = []
        out = call('mneme_search', {'query': 'doğrulama kelimesi', 'project': 'beyin', 'limit': 3},
                   lambda argv, payload: (seen.append((argv, payload)) or (0, '{"records": []}')))
        self.assertEqual(seen[0][0], ['context', 'doğrulama kelimesi', '--limit', '3', '--project', 'beyin'])
        self.assertFalse(out['result']['isError'])

    def test_write_tools_send_json_on_stdin(self):
        seen = []
        run = lambda argv, payload: (seen.append((argv, payload)) or (0, '{}'))
        call('mneme_note_create', {'source': 'notes/a.md', 'text': 'x', 'metadata': {'id': 'a'}}, run)
        call('mneme_note_edit', {'source': 'notes/a.md', 'op': 'append', 'text': 'y'}, run)
        self.assertEqual(seen[0], (['note-create', '--file', '-'], {'source': 'notes/a.md', 'text': 'x', 'metadata': {'id': 'a'}}))
        self.assertEqual(seen[1], (['note-edit', '--file', '-'], {'source': 'notes/a.md', 'op': 'append', 'text': 'y'}))

    def test_bad_arguments_and_cli_failures_are_tool_errors(self):
        out = call('mneme_search', {}, lambda *a: (0, ''))
        self.assertTrue(out['result']['isError'])
        out = call('mneme_search', {'query': 'x', 'limit': 99}, lambda *a: (0, ''))
        self.assertTrue(out['result']['isError'])
        out = call('mneme_doctor', {}, lambda *a: (1, '{"error": "ValueError"}'))
        self.assertTrue(out['result']['isError'])
        self.assertIn('ValueError', out['result']['content'][0]['text'])

        def boom(*a):
            raise OSError('gone')
        self.assertTrue(call('mneme_doctor', {}, boom)['result']['isError'])
        self.assertEqual(call('mneme_delete', {}, None)['error']['code'], -32602)

    def test_long_output_is_truncated(self):
        out = call('mneme_doctor', {}, lambda *a: (0, 'a' * (mcp.OUTPUT_LIMIT + 50)))
        self.assertTrue(out['result']['content'][0]['text'].endswith('[truncated]'))

    def test_serve_loop_over_streams_skips_garbage(self):
        lines = [json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}).encode(), b'not json', b'',
                 json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}).encode()]
        stdin = io.BytesIO(b'\n'.join(lines) + b'\n')
        stdout = io.BytesIO()
        mcp.serve(SCRIPTS, stdin, stdout)
        responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(responses[0]['result'], {})
        self.assertEqual(responses[1]['error']['code'], -32700)
        self.assertEqual(len(responses), 2)

    def test_malformed_requests_get_an_error_and_the_server_keeps_serving(self):
        """#7: each of these used to end the process, and every tool with it."""
        def serve(*requests):
            stdout = io.BytesIO()
            mcp.serve(SCRIPTS, io.BytesIO(b'\n'.join(requests) + b'\n'), stdout)
            return [json.loads(line) for line in stdout.getvalue().splitlines()]

        ping = b'{"jsonrpc":"2.0","id":9,"method":"ping"}'
        for method in ('initialize', 'tools/call'):
            with self.subTest(method=method):
                bad = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': [1]}).encode()
                first, second = serve(bad, ping)
                self.assertEqual(first['error']['code'], -32602)
                self.assertEqual(first['id'], 1)
                self.assertEqual(second['result'], {})
        surrogate = b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"\\ud800"}}'
        first, second = serve(surrogate, ping)
        self.assertEqual(first['error']['code'], -32602)
        self.assertEqual(second['result'], {})
        first, second = serve(b'[' * 200000, ping)
        self.assertEqual(first['error']['code'], -32700)
        self.assertEqual(second['result'], {})

    def test_unexpected_handler_failure_is_an_internal_error(self):
        original, mcp.handle = mcp.handle, lambda *a: 1 / 0
        self.addCleanup(setattr, mcp, 'handle', original)
        stdout = io.BytesIO()
        mcp.serve(SCRIPTS, io.BytesIO(b'{"jsonrpc":"2.0","id":4,"method":"ping"}\n[1]\n'), stdout)
        first, second = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual((first['id'], first['error']['code']), (4, -32603))
        self.assertEqual((second['id'], second['error']['code']), (None, -32603))

    def test_non_ascii_tool_output_survives_the_wire(self):
        stdout = io.BytesIO()
        original, mcp.make_runner = mcp.make_runner, lambda vault: lambda *a: (0, 'doğrulama')
        self.addCleanup(setattr, mcp, 'make_runner', original)
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'mneme_doctor', 'arguments': {}}}
        mcp.serve(SCRIPTS, io.BytesIO(json.dumps(request).encode() + b'\n'), stdout)
        self.assertEqual(json.loads(stdout.getvalue())['result']['content'][0]['text'], 'doğrulama')

    def test_real_process_speaks_json_rpc(self):
        request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}) + '\n'
        done = subprocess.run([sys.executable, str(SCRIPTS / 'mneme_v3_mcp.py')], input=request.encode(),
                              capture_output=True, timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(json.loads(done.stdout)['result']['tools']), 5)


if __name__ == '__main__':
    unittest.main()
