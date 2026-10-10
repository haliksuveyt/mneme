"""A rule set within RULES_WHOLE_SHARE arrives whole even when long Threads and handoff cards fill the opening."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(os.environ.get('MNEME_TEST_REPO', Path(__file__).resolve().parents[1]))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evaluator = load('mneme_v3_rules_whole_evaluator', 'scripts/evaluate_v3.py')
companion = load('mneme_v3_rules_whole_companion', 'template/.claude/scripts/mneme_v3_companion.py')
COMPANION = '🔮 850-Companion'
# Shaped like a real vault (10 Oct 2026): ~2.6k of rules beside ~4k Threads and ~3.4k handoff,
# where the even water-fill cut the middle rules ("sormadan yap") out of a 9.5k opening.
RULES = ('# Kurallar\n' + ''.join(f'- RULE_{i:02d}_CANARY: kullanıcının açık bir düzeltmesi, tarih ve kapsamıyla birlikte.\n'
                                  for i in range(30)))
BODIES = {
    'Core.md': '# Kimlik\nIDENTITY_CANARY\n' + 'kimlik ayrıntısı\n' * 100,
    'Kurallar.md': RULES,
    'Last-Session.md': '# Son oturum\n## kart\nHANDOFF_CANARY\n' + 'oturum ayrıntısı satırı\n' * 150,
    'Threads.md': '# Threads\n## Active Threads\nTHREAD_CANARY\n' + 'açık konu ayrıntısı satırı\n' * 160,
    'Journal.md': '# Journal\n',
}


class RulesWholeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='rules-whole-')
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.vault = root / 'vault'
        (self.vault / COMPANION).mkdir(parents=True)
        module = evaluator.load_runtime()
        self.store = module.MemoryStore(root / 'runtime', self.vault)
        self.addCleanup(lambda: evaluator.close_store(self.store))
        for name, body in BODIES.items():
            source = f'{COMPANION}/{name}'
            (self.vault / source).write_text(body, encoding='utf-8')
            self.store.ingest({'id': name, 'kind': 'note', 'status': 'active', 'text': body,
                               'source': source, 'updated_at': '2026-10-10T10:00:00Z'})

    def test_rules_within_the_whole_share_are_never_cut(self):
        for budget in (5000, 9500, 12000):  # 5000 = default context_chars
            with self.subTest(budget=budget):
                text = companion.context(self.store, budget, 'rules-whole', 'claude')
                self.assertLessEqual(len(text), budget)
                for i in range(30):
                    self.assertIn(f'RULE_{i:02d}_CANARY', text)
                self.assertIn('HANDOFF_CANARY', text)
                self.assertIn('THREAD_CANARY', text)

    def test_rules_over_the_share_still_keep_both_ends(self):
        text = companion.context(self.store, 3000, 'rules-whole', 'claude')
        self.assertLessEqual(len(text), 3000)
        self.assertIn('RULE_00_CANARY', text)
        self.assertIn('RULE_29_CANARY', text)


if __name__ == '__main__':
    unittest.main()
