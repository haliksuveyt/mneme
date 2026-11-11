"""Offline product fixture helpers. Never downloads a release or reads user state."""
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / 'scripts/install_v3.py'
BUILDER = ROOT / 'scripts/build_v3_release.py'


def _transient(error):
    return os.name == 'nt' and getattr(error, 'winerror', None) in (5, 32, 145, 183)


def _gone(path):
    """True once the name is really free. A directory whose delete is still pending reports
    PermissionError from stat() (or still exists) until the last open handle on it closes."""
    try:
        os.stat(path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return False


def remove_tree(path, attempts=60, delay=0.05):
    """rmtree that survives the short Windows window in which a just-closed file is still busy.

    A SQLite handle released by the garbage collector, a child process that has exited but whose
    handles are not yet closed, or an indexer or scanner touching a fresh file all make a delete
    fail with WinError 5, 32 or 145, or leave the directory in delete-pending state so that the
    name cannot be reused (WinError 183) for a few hundred milliseconds. Only those errors are
    retried and the last one is raised, so a real leak still fails the test.
    """
    path = Path(path)
    for attempt in range(attempts):
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
        except OSError as error:
            if not _transient(error) or attempt == attempts - 1:
                raise
            gc.collect()
            time.sleep(delay * min(attempt + 1, 10))
            continue
        if os.name != 'nt' or _gone(path):
            return
        gc.collect()
        time.sleep(delay * min(attempt + 1, 10))
    raise OSError(str(path) + ' is still present after removal')


def copy_tree(source, target, attempts=60, delay=0.05):
    """shutil.copytree that waits out a target name Windows has not released yet."""
    for attempt in range(attempts):
        try:
            return shutil.copytree(source, target)
        except OSError as error:
            if not _transient(error) or attempt == attempts - 1:
                raise
            gc.collect()
            time.sleep(delay * min(attempt + 1, 10))


class TemporaryDirectory(tempfile.TemporaryDirectory):
    """tempfile.TemporaryDirectory whose cleanup retries transient Windows delete failures."""

    def cleanup(self):
        gc.collect()
        remove_tree(self.name)
        self._finalizer.detach()


def windows_runtime_env():
    """Variables Windows needs even in a cleared test environment. Without SYSTEMROOT,
    ssl.SSLContext() fails on Python 3.14 (OpenSSL 3.5): '[SSL] unknown error (0xa080024)'."""
    return {key: os.environ[key] for key in ('SYSTEMROOT', 'WINDIR') if key in os.environ}


# Every MNEME_* variable is a user setting or a hook flag (MNEME_V3_SKIP, MNEME_JEV_DISABLE,
# MNEME_V3_FILTER_HARNESS_TURNS, MNEME_V3_NO_RECEIPT_REMINDER, MNEME_UPDATES_OFF, ...). A suite run
# from a configured shell or an agent session must not inherit them. Only the values the suite
# itself inherited are dropped: one a test sets in os.environ (MNEME_PYTHON for a missing
# interpreter) still reaches its child, as does one passed explicitly.
USER_ENV_PREFIX = 'MNEME_'
_INHERITED = {key: value for key, value in os.environ.items() if key.upper().startswith(USER_ENV_PREFIX)}


def inherited_env(**extra):
    """The current environment without the user Mneme settings the suite inherited, plus extra."""
    env = {key: value for key, value in os.environ.items() if _INHERITED.get(key) != value}
    env.update(extra)
    return env


def clean_environ(**extra):
    """In-process counterpart of inherited_env: a patch.dict for os.environ (start/stop or with)."""
    return patch.dict(os.environ, inherited_env(**extra), clear=True)


def isolated_env(home):
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    env = {'HOME': str(home), 'USERPROFILE': str(home), 'APPDATA': str(home / 'appdata'),
           'LOCALAPPDATA': str(home / 'localappdata'), 'TEMP': str(home), 'TMP': str(home),
           'PATH': str(Path(sys.executable).parent) + os.pathsep + os.defpath,
           'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8', 'MNEME_V3_NO_SPAWN': '1'}
    env.update(windows_runtime_env())
    return env


def run_python(script, args, cwd, env, payload=None):
    return subprocess.run([sys.executable, str(script), *map(str, args)], cwd=cwd, env=env,
                          input=json.dumps(payload).encode('utf-8') if payload is not None else None,
                          capture_output=True, timeout=60)


def install(vault, state, env):
    return run_python(INSTALLER, ['--vault', vault, '--state', state], ROOT, env)


def build_package(path, version, env):
    if not BUILDER.is_file():
        raise AssertionError('Versioned release builder not implemented')
    result = run_python(BUILDER, ['--output', path, '--version', version], ROOT, env)
    if result.returncode:
        raise AssertionError('Offline package build failed: ' + result.stderr.decode('utf-8', errors='replace'))
    return Path(path)


def snapshot(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): ('symlink:' + os.readlink(p) if p.is_symlink()
            else hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(root.rglob('*')) if p.is_file() or p.is_symlink()}


def rewrite_zip(source, target, mutate):
    with zipfile.ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    mutate(files)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return Path(target)
