# Changelog

One entry per release, newest first. Each entry links to its full release notes in `docs/v3/releases/` (most notes are written in Turkish).

## 3.12.1
[Release notes](docs/v3/releases/3.12.1.md)
- Secret filter now redacts prefixed names such as `DB_PASSWORD=`, `OPENAI_API_KEY=` and `refresh_token=` in text, query strings and fact keys.
- Custom literals in `secret-patterns.txt` are replaced in a single longest-first pass, so a short literal can no longer leave the tail of a longer secret.
- The MCP server answers malformed input (non-object `params`, lone surrogates, deeply nested JSON, handler failures) with a JSON-RPC error instead of exiting.

## 3.12.0
[Release notes](docs/v3/releases/3.12.0.md)
- New `handoff` command builds a bounded packet with source paths, SHA-256 hashes, revisions and explicit decision and task metadata.
- New `handoff-diff` compares two packets of the same scope: sources, metadata and excerpts.
- Freshness, visibility and validity checks also apply to exported context.
- Adds a 60-scenario source-contract fixture, packet-diff tests, a case study, a complete English README and new SVG artwork.

## 3.11.0
[Release notes](docs/v3/releases/3.11.0.md)
- Rules cut off by the client's context limit are delivered in full on the first turn.
- If the source sync is slow, per-turn search falls back to the previous index and says so.
- Optional in-session de-duplication of context (`preferences --context-dedupe on`).
- A note whose title, file name or alias appears in the question ranks first.
- New `recap --since/--until`, `stats`, and an optional `yakala` capture shortcut.
- Includes the 3.10.0 changes, which were not published separately.

## 3.10.0
[Release notes](docs/v3/releases/3.10.0.md)
- Not published separately; shipped in 3.11.0.
- One-line open-loop warning at session start for tasks untouched for 3+ days and for watched files that have gone stale (`.mneme-freshness.json`).
- `Kurallar.md` is never truncated when it fits 70% of the startup budget.
- The Stop hook turns a session's Last-Session card into a receipt when none was written.

## 3.9.1
[Release notes](docs/v3/releases/3.9.1.md)
- `install_v3.py --uninstall` now removes only Mneme's part of shared files: the managed block in `AGENTS.md` / `CLAUDE.md` and Mneme hooks in settings files. Your own rules and hooks stay.
- New `--plan-uninstall` shows what would happen to each file without changing anything.

## 3.9.0
[Release notes](docs/v3/releases/3.9.0.md)
- Search ranking uses idf and length normalization (BM25 style) with title and alias weighting.
- New `note-edit` command (`append`, `replace_section`, `upsert_card`) for existing notes.
- New stdio MCP server (`mneme.py mcp`) with search, note create/edit, supersede and doctor tools; no delete tool.
- Offline benchmark, standard search: Recall@1 71.9% to 93.8% on an engineering vault (35 notes, 32 queries) and 70% to 100% on a Turkish personal vault (8 notes, 10 queries).

## 3.8.2
[Release notes](docs/v3/releases/3.8.2.md)
- Adds the `note-edit` command and the matching skill guidance.

## 3.8.1
[Release notes](docs/v3/releases/3.8.1.md)
- Search ranking by idf, length normalization and title/alias weight. The hook's strict context path is unchanged.

## 3.8.0
[Release notes](docs/v3/releases/3.8.0.md)
- Hardening release: `doctor` states why a problem needs attention.
- Tolerant handling of YAML headers outside the supported subset; receipt views are owned correctly and `sync --rebuild-receipts` restores hidden ones.
- Turkish possessive, case and `-ki` suffixes are reduced to the stem in search.
- New `supersede` command and a warning when one project holds conflicting `facts` values.

## 3.7.1
[Release notes](docs/v3/releases/3.7.1.md)
- Fixes `doctor` and the session-start notice wrongly reporting the installed version as ahead of the official release for 24 hours after an update.
- Fixes updates stopping with "Reinstall conflict" on vaults synced between machines with git.

## 3.7.0
[Release notes](docs/v3/releases/3.7.0.md)
- Session-start context now stays under the Claude Code (10,000 characters) and Codex (10,000 bytes) hook limits, so `Last-Session`, `Threads` and `Journal` are no longer dropped.
- Receipts linked to private or untrusted notes no longer enter session start.
- `companion-compact` takes a full backup before rewriting; `recover` no longer stalls after a successful V2 migration.
- Optional parallel-session notice and usage report.

## 3.6.0
[Release notes](docs/v3/releases/3.6.0.md)
- Fix-focused release: the OpenCode 2.x plugin loads again, `update` and `recover` work on older Windows MSIX installs, and the secret filter recognises keys from eight more providers.
- Sub-agent reports are no longer searched as if they were user questions.
- Optional folder-based project scope for the Jev evaluator, a separate larger session-start context budget and note-hygiene signals (off by default).

## 3.5.1
[Release notes](docs/v3/releases/3.5.1.md)
- The updater accepts both official repository names (`Mehximus/mneme` and `Mehximus/Mneme`) so updates keep working after a possible rename. Other names are rejected.

## 3.5.0
[Release notes](docs/v3/releases/3.5.0.md)
- Parallel sessions and multiple machines: `Last-Session.md` holds one handoff card per session; new multi-machine guide.
- New `recap` command lists recent receipts with source links; no model call.
- Components and skills can be excluded (`preferences --exclude-component`).
- Projects outside the vault can get their own session-start context; reminders for knowledge distillation; MSIX state-path pinning on Windows.

## 3.4.0
[Release notes](docs/v3/releases/3.4.0.md)
- Per-turn context now delivers the passage that answers the question instead of the start of a note. On the repository's synthetic corpus, short questions went from 24/42 to 33/42 at a 5000-character budget.
- Size limits and lossless `companion-compact` for `Last-Session.md` and `Threads.md`.
- Stop-time receipt reminder; rejected inferences leave the context; optional strict completion contract for tasks.
- The secret filter also covers quoted and escaped values, URL query values and database URI passwords.

## 3.3.0
[Release notes](docs/v3/releases/3.3.0.md)
- Claude Code now sees the rules in `AGENTS.md` after install: `CLAUDE.md` is created with an `@AGENTS.md` import.
- OMP (Oh My Pi) becomes the sixth supported client.
- `--keep-customized-legacy` keeps a customised V2 runner alongside V3.

## 3.2.1
[Release notes](docs/v3/releases/3.2.1.md)
- Fixes the `invalid legacy skill hashes` error that blocked updates for vaults installed from `main` and showing version 3.0.2.

## 3.2.0
[Release notes](docs/v3/releases/3.2.0.md)
- Source continuity for short follow-ups within a session, and alias search from `aliases:` in frontmatter, both working without the optional Jev evaluator.
- Rewritten handoff packing: a source is never cut mid-envelope, and `omitted_count` and `truncated` are preserved.
- Optional `jev-memory` command and an optional global bridge for chosen projects outside the vault (both off by default).

## 3.1.0
[Release notes](docs/v3/releases/3.1.0.md)
- Daily release discovery with a single notification per session; the main session never waits on the network.
- `update --check --metadata-only` shows version information without downloading the ZIP.
- The downloaded ZIP's outer SHA-256 is verified before any package code runs; `recover` and `rollback` handle interrupted or unwanted updates.
- `context --no-sync` opens the existing index read-only.
