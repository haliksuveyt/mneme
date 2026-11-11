"""Console entry point: run scripts/install_v3.py against the packaged template tree."""
import importlib.util
from importlib import resources
from pathlib import Path
import sys


def payload_root():
    root = Path(str(resources.files(__package__) / "payload"))
    if not (root / "scripts" / "install_v3.py").is_file() or not (root / "template").is_dir():
        raise SystemExit("mneme-brain: packaged installer files are missing; reinstall the package")
    return root


def load_installer(root):
    spec = importlib.util.spec_from_file_location("mneme_packaged_installer", root / "scripts" / "install_v3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DEFAULT_VERSION = (root / "VERSION").read_text(encoding="utf-8").strip()
    return module


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "install":
        args.pop(0)  # `mneme-brain install --vault X` reads like the pipx/uvx examples
    installer = load_installer(payload_root())
    sys.argv = ["mneme-brain"] + args
    return installer.main()


if __name__ == "__main__":
    raise SystemExit(main())
