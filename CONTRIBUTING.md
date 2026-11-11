# Contributing to Mneme

Thanks for helping. Mneme is a local Markdown memory layer for AI coding agents. The engine uses only Python's standard library, and that is a hard rule: do not add a dependency.

## Requirements

- Python 3.11 or newer (CI runs 3.11 and 3.13 on Linux, macOS and Windows).
- Standard library only. No `pip install` step, now or later.

## Run the tests

From the repository root:

```bash
python -m unittest discover -s tests -p "v3_*test.py"
python scripts/evaluate_v3.py
```

The first command runs the offline V3 contract tests. The second runs the frozen development and holdout retrieval gates. These are the same two steps as in [`.github/workflows/v3.yml`](.github/workflows/v3.yml). Use `py -3` instead of `python` on Windows if needed.

Other scripts cover single areas, for example `scripts/evaluate_v3_search.py` (search quality), `scripts/evaluate_v3_handoff.py` (handoff source contracts) and `scripts/evaluate_v3_passages.py` (passage retrieval). The test files named `tests/*.sh`, `scripts_test.py` and the `Test-*.ps1` scripts belong to the older V2 tooling and the Windows workflow ([`windows.yml`](.github/workflows/windows.yml)); `scripts_test.py` needs POSIX `fcntl`.

On Windows, a few tests can fail on temporary-directory errors (WinError 145 or 183) or time out. Re-run the single module before assuming your change broke it.

## Where code lives

| Path | What it holds |
|---|---|
| `template/.claude/scripts/mneme_v3*.py` | The engine: sync, search, hooks, handoff, MCP server, secret filter, update logic. This is what gets installed into a user's vault. |
| `template/.agents/skills/` | The `mneme`, `mneme-doktor` and `mneme-guncelle` skills shipped with the package. |
| `scripts/` | Repository tools: `install_v3.py`, `mneme_entry.py`, `build_v3_release.py`, `verify_v3_release.py` and the `evaluate_v3*.py` benchmarks. |
| `tests/v3_*test.py` | The V3 test suite. Fixtures are in `tests/fixtures/v3/`. |
| `docs/v3/` | User and design docs. Release notes are in `docs/v3/releases/`. |

Code that ships to users lives under `template/` (engine, skills) and `scripts/` (installer, entry point). Changes there need a test in `tests/`. The release ZIP contains only `scripts/install_v3.py`, `scripts/mneme_v3.py`, `scripts/mneme_entry.py`, the `template/.claude/scripts/mneme_v3*.py` files and the three skills.

## Branches and pull requests

1. Fork the repository or create a branch from `main`. One topic per branch.
2. Make the change and add or update tests. Keep the change small and focused.
3. Run both commands above and make sure they pass.
4. Open a pull request against `main` and fill in the template. CI runs when you touch the paths listed in `v3.yml` (engine, `scripts/*v3*.py`, skills, V3 tests and fixtures).
5. Commit messages are short and in English, in conventional style, for example `fix: keep the MCP server alive on malformed params` or `docs: clarify update steps`.

Documentation exists in English and Turkish for the main pages. If you change `README.md`, update `README.tr.md` to match.

Do not commit secrets, real vault content or personal notes. Test fixtures must be synthetic.

## How a release is cut

Maintainers cut releases. The steps below describe the current process.

1. Pick a stable `MAJOR.MINOR.PATCH` version.
2. Add `docs/v3/releases/X.Y.Z.md` with the release notes and update the root `VERSION` file.
3. Update the version in the manual-install line of `README.md` and `README.tr.md` (`mneme-v3-X.Y.Z.zip`) and the release-notes link. The `chore: release 3.12.1` commit shows the shape of this change.
4. Build the package:

   ```bash
   python scripts/build_v3_release.py --output dist/mneme-v3-X.Y.Z.zip --version X.Y.Z
   ```

   This writes the ZIP, a manifest with per-file SHA-256 hashes, and `mneme-v3-X.Y.Z.zip.sha256` next to it.
5. Verify the same ZIP against the previous released package:

   ```bash
   python scripts/verify_v3_release.py --package dist/mneme-v3-X.Y.Z.zip --baseline mneme-v3-PREVIOUS.zip
   ```

6. Publish the ZIP and its `.sha256` as assets of a GitHub release tagged `vX.Y.Z`. The updater only installs the official stable release and checks the outer checksum before it runs any package code.

Do not use GitHub's automatic "Source code" archive as an install package.
