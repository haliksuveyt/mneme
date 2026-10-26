"""Packet diffs never infer that omitted sources were deleted from the vault."""
import contextlib
from copy import deepcopy
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
from mneme_v3_handoff import compare_packets, read_packet


def packet(text='Orbit old choice', **updates):
    record = dict(id='decision', source='notes/decision.md', source_sha256='a' * 64,
                  revision=1, kind='decision', status='accepted', text=text, facts={'owner': 'Synthetic'})
    record.update(updates)
    return {'format': 'mneme-handoff-v1', 'project': 'orbit', 'query': 'Orbit', 'audience': 'internal',
            'sections': {'accepted_decisions': [record], 'proposals': [], 'open_tasks': [], 'other_context': []},
            'truncated': False}


class PacketDiffTest(unittest.TestCase):
    def test_same_packet_has_no_changes(self):
        result = compare_packets(packet(), packet())
        self.assertEqual((result['updated'], result['added_to_packet'], result['removed_from_packet']), ([], [], []))
        self.assertEqual(result['unchanged_count'], 1)

    def test_source_revision_and_decision_status_changes_are_visible(self):
        after = packet('Orbit new choice', source_sha256='b' * 64, revision=2, status='proposed')
        after['sections']['proposals'] = after['sections']['accepted_decisions']
        after['sections']['accepted_decisions'] = []
        result = compare_packets(packet(), after)
        change, = result['updated']
        self.assertTrue(change['source_changed'])
        self.assertEqual(change['after']['section'], 'proposals')
        self.assertEqual(change['status_after'], 'proposed')
        self.assertIn('revision', change['metadata_fields_changed'])

    def test_membership_changes_are_not_called_file_deletions(self):
        after = packet(); after['sections']['accepted_decisions'] = []
        after['truncated'] = True
        result = compare_packets(packet(), after)
        self.assertEqual(result['removed_from_packet'][0]['id'], 'decision')
        self.assertTrue(result['packet_scope_only'] and result['partial'])
        self.assertNotIn('deleted_sources', result)

    def test_excerpt_change_is_separate_from_source_change(self):
        result = compare_packets(packet(), packet('Orbit', text_truncated=True))
        self.assertFalse(result['updated'][0]['source_changed'])
        self.assertTrue(result['updated'][0]['excerpt_changed'])

    def test_text_is_opt_in_and_partial_text_is_never_presented_as_full_diff(self):
        after = packet('Orbit SECRET_CANARY', source_sha256='b' * 64)
        self.assertNotIn('SECRET_CANARY', json.dumps(compare_packets(packet(), after)))
        self.assertIn('SECRET_CANARY', compare_packets(packet(), after, include_text=True)['updated'][0]['text_diff'])
        after['sections']['accepted_decisions'][0]['text_truncated'] = True
        item = compare_packets(packet(), after, include_text=True)['updated'][0]
        self.assertEqual(item['text_diff_unavailable'], 'truncated_excerpt')
        self.assertNotIn('text_diff', item)

    def test_cross_project_query_or_audience_comparisons_fail(self):
        for key, value in [('project', 'other'), ('query', 'different'), ('audience', 'public')]:
            after = packet(); after[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                compare_packets(packet(), after)

    def test_duplicates_or_mislabeled_decisions_fail(self):
        duplicate = packet()
        duplicate['sections']['accepted_decisions'] *= 2
        with self.assertRaises(ValueError): compare_packets(packet(), duplicate)
        mislabeled = packet(status='proposed')
        with self.assertRaises(ValueError): compare_packets(packet(), mislabeled)

    def test_input_bound_and_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'packet.json'
            path.write_text(json.dumps(packet()), encoding='utf-8-sig')
            self.assertEqual(read_packet(path), packet())
            path.write_text('x' * 1_000_001, encoding='utf-8')
            with self.assertRaises(ValueError): read_packet(path)

    def test_cli_diff_never_creates_state_or_changes_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); vault = root / 'vault'; vault.mkdir()
            before, after = root / 'before.json', root / 'after.json'
            before.write_text(json.dumps(packet()), encoding='utf-8')
            after.write_text(json.dumps(packet('Orbit new', source_sha256='b' * 64)), encoding='utf-8')
            spec = importlib.util.spec_from_file_location('mneme_diff_cli_test', ROOT / 'scripts/mneme_v3.py')
            cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = cli.main(['--vault', str(vault), '--state', str(root / 'state'), 'handoff-diff',
                                 '--before', str(before), '--after', str(after)])
            self.assertEqual(code, 0)
            self.assertEqual(len(json.loads(output.getvalue())['updated']), 1)
            self.assertFalse((root / 'state').exists())
            self.assertEqual(list(vault.iterdir()), [])

    def test_human_view_shows_requested_diff_and_partial_warning(self):
        spec = importlib.util.spec_from_file_location('mneme_diff_entry_test', ROOT / 'scripts/mneme_entry.py')
        entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
        after = packet('Orbit new choice', source_sha256='b' * 64)
        result = compare_packets(packet(), after, include_text=True)
        text = entry.human_result(result, 'handoff-diff')
        self.assertIn('+Orbit new choice', text)
        after['truncated'] = True
        self.assertIn('Kismi paketler', entry.human_result(compare_packets(packet(), after), 'handoff-diff'))

    def test_installed_diff_command_works_without_reading_referenced_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); vault = root / 'vault'; vault.mkdir()
            before, after = root / 'before.json', root / 'after.json'
            before.write_text(json.dumps(packet()), encoding='utf-8')
            after.write_text(json.dumps(packet('Orbit new choice', source_sha256='b' * 64)), encoding='utf-8')
            installed = subprocess.run([sys.executable, str(ROOT / 'scripts/install_v3.py'), '--vault', str(vault),
                                        '--state', str(root / 'state')], capture_output=True, timeout=40)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            result = subprocess.run([sys.executable, str(vault / 'mneme.py'), 'handoff-diff',
                                     '--before', str(before), '--after', str(after), '--json'],
                                    capture_output=True, text=True, encoding='utf-8', timeout=40)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['updated'][0]['source_changed'])
            self.assertFalse((vault / 'notes/decision.md').exists())

    def test_invalid_sync_metadata_fails_explicitly(self):
        after = packet(); after['source_sync'] = 'invalid'
        with self.assertRaises(ValueError): compare_packets(packet(), after)


if __name__ == '__main__':
    unittest.main()
