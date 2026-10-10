"""Open-loop notice: quiet open tasks and stale watched files are named in one line."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(os.environ.get('MNEME_TEST_REPO', Path(__file__).resolve().parents[1]))
SCRIPTS = ROOT / 'template/.claude/scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


freshness = load('mneme_v3_freshness_under_test', 'template/.claude/scripts/mneme_v3_freshness.py')
evaluator = load('mneme_v3_freshness_evaluator', 'scripts/evaluate_v3.py')
companion = load('mneme_v3_freshness_companion', 'template/.claude/scripts/mneme_v3_companion.py')
DAY = 86400


def task(status):
    return '---\n' + json.dumps({'id': 'x', 'kind': 'task', 'status': status}) + '\n---\nbody\n'


class FreshnessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='freshness-')
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name) / 'vault'
        (self.vault / 'tasks').mkdir(parents=True)
        self.now = time.time()

    def write(self, relative, text, days_old):
        path = self.vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        moment = self.now - days_old * DAY
        os.utime(path, (moment, moment))

    def test_quiet_open_tasks_are_named_oldest_first(self):
        self.write('tasks/new.md', task('active'), 1)
        self.write('tasks/old.md', task('waiting'), 9)
        self.write('tasks/mid.md', task('inbox'), 4)
        self.write('tasks/done.md', task('done'), 20)
        line = freshness.notice(self.vault, self.now)
        self.assertIn('2 open task(s) untouched for 3+ days (old, mid)', line)
        self.assertNotIn('new', line)
        self.assertNotIn('done', line)

    def test_names_are_bounded(self):
        for i in range(6):
            self.write(f'tasks/t{i}.md', task('active'), 5 + i)
        line = freshness.notice(self.vault, self.now)
        self.assertIn('6 open task(s)', line)
        self.assertIn(', …)', line)
        self.assertLess(len(line), 300)

    def test_watched_file_age_and_missing_file(self):
        self.write('data/last_sync.json', '{}', 5)
        self.write('data/fresh.json', '{}', 0)
        (self.vault / freshness.CONFIG_NAME).write_text(json.dumps({'watch': [
            {'path': 'data/last_sync.json', 'max_days': 3, 'label': 'Hevy'},
            {'path': 'data/fresh.json', 'max_days': 3},
            {'path': 'data/gone.json', 'max_days': 1, 'label': 'Gone'},
            {'path': '../outside.json', 'max_days': 1, 'label': 'Outside'}]}), encoding='utf-8')
        line = freshness.notice(self.vault, self.now)
        self.assertIn('Hevy 5 days old', line)
        self.assertIn('Gone missing', line)
        self.assertNotIn('fresh', line)
        self.assertNotIn('Outside', line)

    def test_nothing_quiet_means_no_line_and_bad_config_means_defaults(self):
        self.write('tasks/new.md', task('active'), 0)
        (self.vault / freshness.CONFIG_NAME).write_text('{not json', encoding='utf-8')
        self.assertEqual(freshness.notice(self.vault, self.now), '')

    def test_task_days_zero_turns_task_check_off(self):
        self.write('tasks/old.md', task('active'), 30)
        (self.vault / freshness.CONFIG_NAME).write_text('{"task_days": 0}', encoding='utf-8')
        self.assertEqual(freshness.notice(self.vault, self.now), '')

    def test_opening_context_carries_the_line(self):
        root = Path(self.tmp.name)
        (self.vault / '🔮 850-Companion').mkdir()
        store = evaluator.load_runtime().MemoryStore(root / 'runtime', self.vault)
        self.addCleanup(lambda: evaluator.close_store(store))
        body = '# Kurallar\n- kural\n'
        (self.vault / '🔮 850-Companion/Kurallar.md').write_text(body, encoding='utf-8')
        store.ingest({'id': 'k', 'kind': 'note', 'status': 'active', 'text': body,
                      'source': '🔮 850-Companion/Kurallar.md', 'updated_at': '2026-10-10T10:00:00Z'})
        self.write('tasks/old.md', task('active'), 6)
        text = companion.context(store, 5000, 'freshness', 'claude')
        self.assertIn('Open loops: 1 open task(s) untouched for 3+ days (old)', text)


if __name__ == '__main__':
    unittest.main()
