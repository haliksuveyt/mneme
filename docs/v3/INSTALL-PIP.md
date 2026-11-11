# Install with uv / pipx

Mneme can be installed as a regular Python package straight from this repository. The package carries the same template tree and installer as the release ZIP, so the result in your notes folder (the "vault") is identical. Python 3.11 or newer is required; there are no runtime dependencies.

```bash
# uv (no permanent install)
uvx --from git+https://github.com/haliksuveyt/mneme mneme-install --vault ~/Notes

# pipx (installs the command once)
pipx install git+https://github.com/haliksuveyt/mneme
mneme-install --vault ~/Notes
```

To pin a release, append its tag to the URL, for example `git+https://github.com/haliksuveyt/mneme@v3.12.1`. Tags older than the one that introduced `pyproject.toml` cannot be installed this way; use the release ZIP for those.

The package is named `mneme-brain`. It is not on PyPI yet, so `pipx run mneme-brain` and `uvx mneme-brain` do not work; use the repository URL above.

`mneme-install` and `mneme-brain` are the same command, and a leading `install` word is optional. It accepts every option of `scripts/install_v3.py` (`--plan`, `--state`, `--uninstall`, `--exclude-component`, and so on). Preview first:

```bash
uvx --from git+https://github.com/haliksuveyt/mneme mneme-install --vault ~/Notes --plan
```

After installing, check the vault with `python ~/Notes/mneme.py doctor`.

Updating does not change: the vault's `mneme.py update` pulls GitHub releases. Running the installer again from a newer package version also works, as it does with a newer release ZIP.

The package only installs files into the vault; the pip environment itself is not used at runtime afterwards.
