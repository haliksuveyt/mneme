"""Build hook: place the installer payload inside the wheel (metadata lives in pyproject.toml)."""
from pathlib import Path
import sys

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from mneme_brain._payload import copy_payload  # noqa: E402


class BuildWithPayload(build_py):
    def run(self):
        super().run()
        copy_payload(ROOT, Path(self.build_lib) / "mneme_brain" / "payload")


setup(cmdclass={"build_py": BuildWithPayload})
