"""`stats`: counts over the committed index, read only, no summaries repeated."""
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'template/.claude/scripts'))
sys.path.insert(0, str(ROOT / 'scripts'))

import mneme_v3 as cli
from mneme_entry import human_result


class FakeStore:
    def __init__(self, records, receipts):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE records(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE receipts(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        for i, record in enumerate(records):
            self.db.execute('INSERT INTO records VALUES (?,?)', (str(i), json.dumps(record)))
        for i, receipt in enumerate(receipts):
            self.db.execute('INSERT INTO receipts VALUES (?,?)', (str(i), json.dumps(receipt)))

    @contextlib.contextmanager
    def _connect(self):
        yield self.db


class StatsTest(unittest.TestCase):
    def store(self):
        records = [{'kind': 'note', 'source': 'knowledge/a.md'}, {'kind': 'note', 'source': 'knowledge/v3/outcomes.md'},
                   {'kind': 'task', 'status': 'active', 'source': 'tasks/t1.md'},
                   {'kind': 'task', 'status': 'done', 'source': 'tasks/t2.md'}]
        receipts = [{'created_at': '2026-10-01T10:00:00+00:00', 'harness': 'claude', 'session': 's1',
                     'refs': ['knowledge/a.md'], 'summary': 'SUMMARY_CANARY'},
                    {'created_at': '2026-10-03T10:00:00+00:00', 'harness': 'codex', 'session': 's2',
                     'refs': ['knowledge/a.md', 'tasks/t1.md']},
                    {'created_at': '2026-10-03T11:00:00+00:00', 'harness': 'claude', 'session': 's2', 'refs': [7]}]
        return FakeStore(records, receipts)

    def test_counts(self):
        result = cli.vault_stats(self.store(), top=1)
        self.assertEqual(result['sources'], 4)
        self.assertEqual(result['kinds'], {'note': 2, 'task': 2})
        self.assertEqual(result['knowledge_notes'], 1)  # generated knowledge/v3 views are not notes
        self.assertEqual(result['open_tasks'], 1)
        self.assertEqual((result['receipts'], result['sessions'], result['active_days']), (3, 2, 2))
        self.assertEqual((result['first_receipt'], result['last_receipt']), ('2026-10-01', '2026-10-03'))
        self.assertEqual(result['harnesses'], {'claude': 2, 'codex': 1})
        self.assertEqual(result['top_refs'], [{'source': 'knowledge/a.md', 'receipts': 2}])

    def test_human_view_never_repeats_summaries(self):
        text = human_result(cli.vault_stats(self.store()), 'stats')
        self.assertIn('3 kayit, 2 oturum, 2 etkin gun', text)
        self.assertNotIn('SUMMARY_CANARY', text)

    def test_empty_index(self):
        result = cli.vault_stats(FakeStore([], []))
        self.assertEqual((result['receipts'], result['first_receipt'], result['top_refs']), (0, None, []))
        self.assertIn('0 kayit', human_result(result, 'stats'))

    def test_cli_runs_on_an_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault, state = Path(tmp) / 'vault', Path(tmp) / 'state'
            vault.mkdir()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = cli.main(['--vault', str(vault), '--state', str(state), 'stats'])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())['receipts'], 0)


if __name__ == '__main__':
    unittest.main()
