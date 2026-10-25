"""Rules and identity the opening had to cut arrive whole, once, on the session's first real turn."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(os.environ.get('MNEME_TEST_REPO', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / 'template/.claude/scripts'))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evaluator = load('mneme_v3_topup_evaluator', 'scripts/evaluate_v3.py')
companion = load('mneme_v3_topup_companion', 'template/.claude/scripts/mneme_v3_companion.py')
COMPANION = '🔮 850-Companion'
# Shaped like a real vault (25 Oct 2026): 6.2k of rules, 2.4k identity, 2.5k handoff and 8k
# threads against Claude Code's ~9.5k opening, where rules and identity both lost their middle.
RULES = '# Kurallar\n' + ''.join(f'- RULE_{i:02d}_CANARY: kullanıcının açık bir düzeltmesi, tarih, kapsam ve kısa bir alıntıyla birlikte yazılır.\n'
                                 for i in range(75))
BODIES = {
    'Core.md': '# Kimlik\nIDENTITY_HEAD\n' + 'kimlik ayrıntısı satırı\n' * 40 + 'IDENTITY_TAIL\n',
    'Kurallar.md': RULES,
    'Last-Session.md': '# Son oturum\n## kart\nHANDOFF_CANARY\n' + 'oturum ayrıntısı satırı\n' * 100,
    'Threads.md': '# Threads\n## Active Threads\nTHREAD_CANARY\n' + 'açık konu ayrıntısı satırı\n' * 300,
    'Journal.md': '# Journal\n',
}


class TopupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='topup-')
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
                               'source': source, 'updated_at': '2026-10-25T10:00:00Z'})

    def test_cut_opening_names_rules_and_identity(self):
        clipped = []
        text = companion.context(self.store, 9500, 'topup', 'claude', clipped=clipped)
        self.assertLessEqual(len(text), 9500)
        self.assertNotIn('RULE_27_CANARY', text)
        self.assertEqual(sorted(clipped), [f'{COMPANION}/Core.md', f'{COMPANION}/Kurallar.md'])

    def test_first_turn_carries_them_whole_once(self):
        clipped = []
        companion.context(self.store, 9500, 'topup', 'claude', clipped=clipped)
        companion.save_topup(self.store.state_dir, 'topup', clipped)
        text = companion.take_topup(self.store, 'topup', 9500)
        self.assertLessEqual(len(text), 9500)
        for i in range(75):
            self.assertIn(f'RULE_{i:02d}_CANARY', text)
        self.assertIn('IDENTITY_HEAD', text)
        self.assertIn('IDENTITY_TAIL', text)
        self.assertLess(text.index('RULE_00_CANARY'), text.index('IDENTITY_HEAD'))
        self.assertEqual(companion.take_topup(self.store, 'topup', 9500), '')

    def test_whole_opening_owes_nothing(self):
        clipped = []
        companion.context(self.store, 24000, 'topup', 'codex', clipped=clipped)
        self.assertEqual(clipped, [])
        companion.save_topup(self.store.state_dir, 'topup', clipped)
        self.assertEqual(companion.take_topup(self.store, 'topup', 9500), '')

    def test_other_session_is_not_served(self):
        companion.save_topup(self.store.state_dir, 'one', [f'{COMPANION}/Kurallar.md'])
        self.assertEqual(companion.take_topup(self.store, 'two', 9500), '')
        self.assertIn('RULE_00_CANARY', companion.take_topup(self.store, 'one', 9500))


if __name__ == '__main__':
    unittest.main()
