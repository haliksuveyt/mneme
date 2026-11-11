"""Packaged-payload lookup: the pip entry point must run the installer against bundled files."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mneme_brain import _payload, cli


class PackagingTest(unittest.TestCase):
    def test_payload_mirrors_source_layout(self):
        with tempfile.TemporaryDirectory(prefix='v3-packaging-') as t:
            payload = _payload.copy_payload(ROOT, Path(t) / 'payload')
            for name in _payload.SCRIPTS:
                self.assertEqual((payload / 'scripts' / name).read_bytes(), (ROOT / 'scripts' / name).read_bytes())
            self.assertEqual((payload / 'VERSION').read_text(), (ROOT / 'VERSION').read_text())
            source = sorted(p.relative_to(ROOT / 'template').as_posix() for p in (ROOT / 'template').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
            copied = sorted(p.relative_to(payload / 'template').as_posix() for p in (payload / 'template').rglob('*') if p.is_file())
            self.assertEqual(source, copied)
            self.assertTrue((payload / 'template/.agents/skills/mneme/SKILL.md').is_file())

    def test_installer_resolves_template_from_payload_and_stamps_version(self):
        with tempfile.TemporaryDirectory(prefix='v3-packaging-') as t:
            payload = _payload.copy_payload(ROOT, Path(t) / 'payload')
            installer = cli.load_installer(payload)
            self.assertEqual(installer.ROOT, payload)
            self.assertEqual(installer.DEFAULT_VERSION, (ROOT / 'VERSION').read_text().strip())
            vault = Path(t) / 'vault'; vault.mkdir()
            plan = installer.install(vault, Path(t) / 'state', plan_only=True)
            self.assertEqual(plan['manifest']['version'], installer.DEFAULT_VERSION)
            self.assertIn('mneme.py', plan['planned'])

    def test_source_checkout_keeps_legacy_default_version(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('v3_packaging_source_installer', ROOT / 'scripts/install_v3.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.assertEqual(module.DEFAULT_VERSION, '3.0.0')

    def test_missing_payload_is_a_clear_error(self):
        with tempfile.TemporaryDirectory(prefix='v3-packaging-') as t:
            original = cli.resources.files
            cli.resources.files = lambda package: Path(t)
            try:
                with self.assertRaises(SystemExit) as caught:
                    cli.payload_root()
            finally:
                cli.resources.files = original
            self.assertIn('missing', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
