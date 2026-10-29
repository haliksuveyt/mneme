# Preferences for checks and context

User preferences are stored in .mneme-preferences.json, which is not a managed release
file. The installer, updater, and rollback do not change it. If it is absent, Mneme
keeps the normal behavior. The shared Python implementation reads the same settings on
Windows, macOS, and Linux; no service or model dependency is added.

Choose a profile with:

~~~sh
python3 mneme.py preferences --profile economical
python3 mneme.py preferences --profile normal
python3 mneme.py preferences --profile manual
~~~

With no arguments, preferences displays the current settings. The mneme skill applies
them for the user; --human requests readable output.

Core fields:

| Setting | Values |
|---|---|
| auto_sync | true/false |
| interval_minutes | 0–1440; 0 means every event |
| context_mode | turn, session, or off |
| context_chars | 1,000–12,000 characters for additional hook context |

The character budget is not a token quota. Numeric values and unknown fields are
validated; a malformed preference file is not silently overwritten.

The economical profile sets auto_sync=true, interval_minutes=15,
context_mode=session, and context_chars=2000. The manual profile sets auto_sync=false
and context_mode=off. Selecting a profile resets automatic-check and context fields to
that profile while preserving independent secret-filter preferences. Changing the
interval does not turn checks on when they are off.

## Companion file and startup-context limits

Last-Session.md defaults to 3,000 characters and Threads.md to 8,000. Adjust them with
last-session-chars and threads-chars (1,000–200,000; 0 disables that limit):

~~~sh
python3 mneme.py preferences --last-session-chars 4000 --threads-chars 12000
~~~

These machine-specific limits live in the runtime directory's companion-limits.json,
not the vault preference file, so older versions can safely roll back. Profile changes
do not reset them. The startup companion context can have a separate 1,000–24,000
character budget using companion-context-chars; 0 reuses context_chars. Other turns
remain limited by context_chars. These settings also live outside the vault and are
rollback-safe.

Client limits can reduce the context further. Claude Code and Codex spill large hook
contexts to a file and provide a limited preview; Mneme accounts for their observed
limits when generating context. The exact client behavior, companion compaction, and
measurement notes are in the [full preferences guide in Turkish](PREFERENCES.md).

## Optional privacy and workflow settings

The secret filter is off by default. When enabled, common access-key patterns in
receipt summaries and note/task creation or updates are replaced with [REDACTED] before
writing. Additional literal secrets can be listed, one per line, in the runtime
directory's secret-patterns.txt. It is a safeguard against accidental writes, not full
DLP and not a tool for cleaning existing notes.

~~~sh
python3 mneme.py preferences --secret-filter on
~~~

Other opt-in settings include:

- project-context on adds a bounded, read-only summary of the current project's latest
  eligible receipt and due tasks to a session outside the vault. It is off by default.
- word-cap-warning, folder-questions, and promotion provide optional note hygiene
  signals. They are off by default and do not edit or move notes.
- parallel-sessions on adds a one-line warning when another recent session is active
  in the same vault. Markers stay in the local runtime directory and contain no prompt
  text or working folder.
- context-dedupe on avoids repeating unchanged notes during a turn-based context mode.
  Delivery state is local to the session and is reset at compaction or session end.
- Receipt reminders can ask Claude or Codex to save a source-linked receipt after file
  edits. The reminder can be dismissed in a session or disabled with
  MNEME_V3_NO_RECEIPT_REMINDER=1.

These options and their exact switches are available with preferences --help. Detailed
event behavior, thresholds, retrieval benchmarks, and client limitations remain in the
[full preferences guide in Turkish](PREFERENCES.md).

## Strict passage retrieval

Turn context uses passage-level strict retrieval: a Markdown note is split into blocks
and the best matching block is returned with its heading path. Visibility, trust,
project, freshness, supersession, budget, and citation checks use the same gates as
record-level retrieval. Empty results remain abstentions; no model call or dependency is
added.

The optional retrieval.json settings control strict_floor (default 0.20) and up to 64
strict_exclude path prefixes. daily/ and receipts/ are always excluded. This is a
machine-specific runtime setting, separate from .mneme-preferences.json. The detailed
algorithm and evaluation tables are documented in Turkish in PREFERENCES.md.

## Exclude optional components

Install-time optional components and skills can be excluded or re-enabled with
preferences --exclude-component and --include-component. The exclusion list is stored
separately in .mneme-exclusions.json at the vault root. On the next install or update,
unchanged managed files for excluded components are removed; user-modified files are
preserved and reported. Doctor reports applied and pending exclusions.

See the [full preferences guide in Turkish](PREFERENCES.md) for supported components,
rollback details, and the full behavior of each opt-in.
