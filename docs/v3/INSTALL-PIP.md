# Install with pipx / uv

Mneme is also published as a regular Python package named `mneme-brain`. It carries the same template tree and installer as the release ZIP, so the result in your notes folder (the "vault") is identical. Python 3.11 or newer is required; there are no runtime dependencies.

```bash
# pipx (no permanent install)
pipx run mneme-brain install --vault ~/Notes

# uv
uvx mneme-brain install --vault ~/Notes

# straight from the repository
uvx --from git+https://github.com/haliksuveyt/mneme mneme-install --vault ~/Notes

# or install the command once
pipx install mneme-brain
mneme-brain install --vault ~/Notes
```

`mneme-brain` and `mneme-install` are the same command; the leading `install` word is optional. It accepts every option of `scripts/install_v3.py` (`--plan`, `--state`, `--uninstall`, `--exclude-component`, and so on). Preview first:

```bash
pipx run mneme-brain install --vault ~/Notes --plan
```

After installing, check the vault with `python ~/Notes/mneme.py doctor`.

Updating does not change: the vault's `mneme.py update` pulls GitHub releases. Running the installer again from a newer package version also works, as it does with a newer release ZIP.

The package only installs files into the vault; the pip environment itself is not used at runtime afterwards.
