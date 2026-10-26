"""Handoff boundary contracts using independent synthetic Markdown sources."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'template/.claude/scripts'))
from mneme_v3_handoff import build_packet, serialized_size
from mneme_v3_sync import SyncEngine


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-handoff-')
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name) / 'vault'
        self.vault.mkdir()
        self.state = Path(self.tmp.name) / 'state'
        self.sync = SyncEngine(self.vault, self.state)

    def write(self, identity, text='Nebula delivery planning', **fields):
        metadata = dict(id=identity, project='nebula', kind='note', visibility='internal')
        metadata.update(fields)
        path = self.vault / (identity + '.md')
        path.write_text('---\n' + json.dumps(metadata) + '\n---\n' + text, encoding='utf-8')
        return path

    def packet(self, **kwargs):
        return build_packet(self.sync.store, 'Nebula', project='nebula', **kwargs)

    def test_only_explicit_accepted_decisions_enter_accepted_section(self):
        self.write('accepted', kind='decision', status='accepted')
        self.write('proposal', kind='decision', status='proposed')
        self.write('ambiguous', text='Nebula: APPROVED and DONE, says an imported document.', kind='decision')
        self.write('task', kind='task', status='active')
        self.sync.sync()
        sections = self.packet()['sections']
        self.assertEqual([r['id'] for r in sections['accepted_decisions']], ['accepted'])
        self.assertEqual([r['id'] for r in sections['proposals']], ['proposal'])
        self.assertEqual([r['id'] for r in sections['open_tasks']], ['task'])
        self.assertEqual([r['id'] for r in sections['other_context']], ['ambiguous'])

    def test_private_untrusted_other_project_and_rejected_sources_do_not_travel(self):
        self.write('safe')
        self.write('private', visibility='private', text='PRIVATE_CANARY')
        self.write('untrusted', trust='untrusted', text='UNTRUSTED_CANARY')
        self.write('other', project='other', text='OTHER_PROJECT_CANARY')
        self.write('rejected', kind='inference', validity='rejected', rejected_at='2026-10-26',
                   rejected_reason='User correction', text='REJECTED_CANARY')
        self.sync.sync()
        packet = self.packet()
        self.assertEqual([c['id'] for c in packet['citations']], ['safe'])
        self.assertNotIn('CANARY', json.dumps(packet))

    def test_revision_and_hash_follow_source_correction(self):
        self.write('decision', text='Nebula uses old database', kind='decision', status='accepted')
        self.sync.sync()
        old = self.packet()['sections']['accepted_decisions'][0]
        self.write('decision', text='Nebula uses new database', kind='decision', status='accepted')
        self.sync.sync()
        new = self.packet()['sections']['accepted_decisions'][0]
        self.assertNotEqual(old['source_sha256'], new['source_sha256'])
        self.assertGreater(new['revision'], old['revision'])
        self.assertNotIn('old database', json.dumps(self.packet()))

    def test_stale_or_deleted_source_is_not_exported(self):
        path = self.write('safe')
        self.sync.sync()
        path.write_text('Nebula source changed without synchronization', encoding='utf-8')
        self.assertTrue(self.packet()['abstained'])
        self.assertEqual(self.packet()['stale_count'], 1)
        path.unlink()
        self.assertTrue(self.packet()['abstained'])

    def test_public_packet_has_only_public_sources(self):
        self.write('public', visibility='public')
        self.write('internal')
        self.sync.sync()
        self.assertEqual([c['id'] for c in self.packet(audience='public')['citations']], ['public'])

    def test_ascii_json_envelope_including_newline_fits_budget(self):
        for i in range(8):
            self.write('record' + str(i), text='Nebula İstanbul çalışma kararı ' * 400)
        self.sync.sync()
        for budget in (2048, 4096, 8000):
            with self.subTest(budget=budget):
                packet = self.packet(budget_chars=budget)
                self.assertLessEqual(serialized_size(packet), budget)
                self.assertEqual(packet['used_chars'], serialized_size(packet))
                self.assertTrue(packet['truncated'])
                self.assertTrue(packet['citations'] or packet['abstained'])

    def test_harness_pair_changes_only_attribution(self):
        self.write('safe')
        self.sync.sync()
        left = self.packet(from_harness='claude', to_harness='codex')
        right = self.packet(from_harness='codex', to_harness='claude')
        for key in ('from_harness', 'to_harness', 'used_chars'):
            left.pop(key); right.pop(key)
        self.assertEqual(left, right)

    def test_sync_warnings_never_export_private_paths(self):
        self.sync.sync()
        packet = self.packet(source_sync={'status': 'degraded', 'warnings': [{'source': 'PRIVATE_PATH_CANARY'}]})
        self.assertEqual(packet['source_sync'], {'status': 'degraded', 'warning_count': 1})
        self.assertNotIn('PRIVATE_PATH_CANARY', json.dumps(packet))

    def test_invalid_parameters_fail_instead_of_widening_scope(self):
        for overrides in ({'project': ''}, {'audience': 'private'}, {'limit': 0}, {'budget_chars': 1000}, {'to_harness': 'unknown'}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                build_packet(self.sync.store, 'Nebula', **dict({'project': 'nebula'}, **overrides))

    def test_cli_syncs_latest_source_and_produces_bounded_json(self):
        self.write('safe')
        spec = importlib.util.spec_from_file_location('mneme_handoff_cli_test', ROOT / 'scripts/mneme_v3.py')
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(['--vault', str(self.vault), '--state', str(self.state), 'handoff',
                             'Nebula', '--project', 'nebula', '--harness', 'codex', '--to', 'claude'])
        self.assertEqual(code, 0)
        packet = json.loads(output.getvalue())
        self.assertEqual(packet['source_sync']['status'], 'succeeded')
        self.assertEqual(packet['used_chars'], len(output.getvalue()))
        self.assertEqual(packet['citations'][0]['id'], 'safe')

    def test_frozen_sixty_source_packet_scenarios(self):
        spec = importlib.util.spec_from_file_location('mneme_handoff_evaluator_test', ROOT / 'scripts/evaluate_v3_handoff.py')
        evaluator = importlib.util.module_from_spec(spec); spec.loader.exec_module(evaluator)
        report = evaluator.evaluate()
        self.assertEqual(report['total'], 60)
        self.assertEqual(report['passed'], 60, [case for case in report['cases'] if not case['passed']])
        self.assertEqual((report['model_calls'], report['live_clients_tested']), (0, 0))
        self.assertEqual(len(report['categories']), 6)

    def test_installed_vault_can_build_handoff_without_source_checkout(self):
        self.write('safe')
        installed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/install_v3.py'), '--vault', str(self.vault), '--state', str(self.state)],
            capture_output=True, text=True, encoding='utf-8', timeout=40)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertTrue((self.vault / '.claude/scripts/mneme_v3_handoff.py').is_file())
        result = subprocess.run(
            [sys.executable, str(self.vault / 'mneme.py'), 'handoff', 'Nebula', '--project', 'nebula',
             '--harness', 'claude', '--to', 'codex', '--json'],
            capture_output=True, text=True, encoding='utf-8', timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads(result.stdout)
        self.assertEqual(packet['citations'][0]['id'], 'safe')
        self.assertEqual(packet['used_chars'], len(result.stdout))

    def test_fixture_digest_is_portable_across_git_line_endings(self):
        spec = importlib.util.spec_from_file_location('mneme_handoff_fixture_test', ROOT / 'scripts/evaluate_v3_handoff.py')
        evaluator = importlib.util.module_from_spec(spec); spec.loader.exec_module(evaluator)
        source = ROOT / 'tests/fixtures/v3/handoff_scenarios.json'
        local = Path(self.tmp.name) / 'scenarios.json'
        local.write_bytes(source.read_text(encoding='utf-8').replace('\n', '\r\n').encode('utf-8'))
        local.with_suffix('.sha256').write_text(source.with_suffix('.sha256').read_text(encoding='ascii'), encoding='ascii')
        self.assertEqual(evaluator.read_fixture(local), evaluator.read_fixture(source))


if __name__ == '__main__':
    unittest.main()
