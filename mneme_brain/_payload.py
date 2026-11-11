"""Files the installer needs, as paths relative to the repository root.

The wheel carries them under mneme_brain/payload/ with the same layout, so
scripts/install_v3.py resolves its template tree exactly as it does in a
source checkout or an extracted release ZIP.
"""
from pathlib import Path
import shutil

SCRIPTS = ("install_v3.py", "mneme_v3.py", "mneme_entry.py")


def copy_payload(source_root, destination):
    source_root, destination = Path(source_root), Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    (destination / "scripts").mkdir(parents=True)
    for name in SCRIPTS:
        shutil.copyfile(source_root / "scripts" / name, destination / "scripts" / name)
    shutil.copyfile(source_root / "VERSION", destination / "VERSION")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(source_root / "template", destination / "template", ignore=ignore)
    return destination
