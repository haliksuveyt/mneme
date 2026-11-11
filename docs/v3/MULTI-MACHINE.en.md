Türkçe: [MULTI-MACHINE.md](MULTI-MACHINE.md)

# Using Mneme on more than one machine

Mneme is local-first: there is no cross-machine sync code, and Mneme does not install git
([UPDATE](UPDATE.en.md)). If you keep the same vault on two computers (for example work and home)
in step with git or a similar tool, this guide explains which files to sync and how the two machines
can work on the same day ([#112](https://github.com/haliksuveyt/mneme/issues/112)).

Each machine installs and updates Mneme on its own. The runtime (the SQLite database) lives outside
the vault, is specific to the machine and is not synced; each machine builds it itself from the
Markdown in the vault.

## What to sync

| Path | In git? | Why |
|---|---|---|
| Notes and companion files | yes | Markdown is the source of truth. |
| `🔮 850-Companion/Arşiv/` | yes | `companion-compact` moves text out of the live file into the archive and leaves a single pointer line in its place. If the archive stays on one machine, the other machine sees an empty pointer. `visibility: private` in the archive only keeps it out of automatic context; it does not mean the file stays out of git. |
| `receipts/` | yes | A receipt file never changes once written, and its name is a digest of the `event_id` (`mneme_v3_sync.py` `receipt()`). The other machine picks up a new receipt into its own database on the next `sync` (`_scan_receipts()`). |
| `daily/v3/`, `knowledge/v3/` | no | These views are generated from the receipts in the local database (`mneme_v3_projections.py` `project_receipts()`). If the receipts are synced, two machines in the same time zone produce the same output; the file name is the machine's local day, so machines in different time zones may put the same receipt on different days. If you commit them, a file arriving from the other machine counts as hand-edited (`manual receipt view edit preserved`) and that view is no longer updated. |
| `AGENTS.md`, `CLAUDE.md` | yes | Your own instructions live in these files too. Since 3.7.0 the Mneme block carries no machine path (`python3 mneme.py sync`), so it is identical on every machine that installs the same version. If the block from the machine that updated first arrives on the other machine through git, that machine's update treats it as its own block and reports no conflict. |
| Installation files | no | Some carry this machine's paths (`.mneme-runtime.json`, hook files, the Hermes and OMP plugins); the rest belong to the version installed on this machine. If the files from the machine that updated first reach the other one through git, they no longer match that machine's installation record, and a reinstall stops with the error `Reinstall conflict: managed file changed`. |

## Recommended `.gitignore`

```gitignore
# Mneme installation: each machine installs and updates Mneme itself
.mneme-runtime.json
.mneme-version
mneme.py
Mneme Guncelle.cmd
.claude/settings.local.json
.claude/scripts/
.claude/hermes-plugin/
.claude/skills/mneme/
.claude/skills/mneme-doktor/
.claude/skills/mneme-guncelle/
.agents/hooks.json
.agents/skills/mneme/
.agents/skills/mneme-doktor/
.agents/skills/mneme-guncelle/
.codex/config.toml
.codex/hooks.json
.opencode/plugins/mneme-v3.js
.omp/hooks/pre/mneme-v3.ts
# Views generated from the local database: each machine generates its own
daily/v3/
knowledge/v3/
```

Check: right after an install or update, `git status --short` should be empty.

- **3.6.0 and earlier:** In those versions the block carried this machine's absolute command path.
  Until both machines are on 3.7.0, keep `AGENTS.md` (and `CLAUDE.md` too, if it carries the block
  itself) in `.gitignore`; once both are updated you can remove the line.
- Your own skills, `.claude/settings.json` and other client settings are not in this list; whether
  to sync them is your call.

## Recommended `.gitattributes`

```gitattributes
# Receipt files are compared byte for byte: line endings are not converted
receipts/** -text
# Companion files laid out as cards and entries: additions from both machines are kept
**/Last-Session.md merge=union
**/Journal.md merge=union
**/Arşiv/*.md merge=union
```

**`receipts/** -text`:** Mneme compares receipt files byte for byte. The default option in a Git for
Windows installation is `core.autocrlf=true`, which converts the line endings of a receipt arriving
from the other machine to CRLF. Without this line, a `\r` ends up in the receipt digest on that
machine, the daily view differs from the one on the other machine, and resubmitting the same receipt
fails with `ReceiptConflict: event id collision`.

**`merge=union`:** Git keeps the lines from both sides and raises no conflict. It never drops lines
but can leave duplicates, so it suits only files where new entries are appended: `Last-Session.md`
with its per-session cards, `Journal.md` and the archive. `Threads.md`, `Kurallar.md` and `Core.md`
are deliberately not in the list. In those files a piece of information has exactly one current
form; if two machines change the same line, a visible conflict is better than two contradictory
lines that quietly sit side by side.

Cards merged with union may not end up in chronological order, and the blank line between two cards
may collapse. `companion-compact` orders cards by the date and time in the heading, not by position,
and keeps the newest.

## Working on two machines on the same day

- **Last-Session:** each session opens its own card and edits only that card
  ([companion protocol](COMPANION-PARITY.md), Turkish). The cards from the two machines are merged by union.
- **Threads, Kurallar, Core:** edit the relevant section in place. If git reports a conflict, pick
  the current version by hand.
- **Git steps:** `pull` before you start working; when you finish, `commit`, `pull --rebase`,
  `push`. If several sessions are open in the same vault, do not run git commands from more than one
  session at the same time; push from one session, or once at the end of the day.
- **Parallel sessions on the same machine:** with `preferences --parallel-sessions on`, the agent
  gets a one-line warning on its first prompt if another session was active in the same vault in the
  last 45 minutes ([PREFERENCES.en.md](PREFERENCES.en.md#optional-privacy-and-workflow-settings)). The
  markers live in the machine-specific runtime folder; they do not see sessions on the other
  machine, for which the git steps above apply.
- **Opening a session before a conflict is resolved:** when `pull --rebase` stops on a conflict, the
  file keeps the `<<<<<<<`, `=======` and `>>>>>>>` markers. In a session opened in that state,
  `sync` indexes the file as it is and the markers end up in later context; the agent may take them
  for content. `sync` and `doctor` do not report this. Resolve the conflict first (`git status`
  should be clean), then open a session.
- **Keep receipt `event_id` values unique across machines:** the agent chooses the `event_id`, and
  the file name is its digest. If two machines give the same name to the same topic on the same day
  (`ortak-konu-2026-09-27`), two different receipts land in one file and `pull --rebase` stops
  with `CONFLICT (add/add)`. If the conflict is resolved by picking one side's file, the other
  machine's database keeps its own digest; `sync` gives no warning and the views of the two machines
  quietly drift apart. To prevent this, append the first 8 characters of the `Receipt session=`
  value to the end of the `event_id`, as in the card heading: `ortak-konu-2026-09-27-3f9a1c2b`.

## How this was verified

Windows 11, Git 2.55 (`core.autocrlf=true`), Python 3.13, `main` @ db1f23d. A local bare
repository and two vaults; Mneme was installed in each with a separate `--state`.

- With the `.gitignore` above, `git status` stayed empty on the second machine after installation
  (`AGENTS.md` was in `.gitignore`, as in the temporary note; `CLAUDE.md` was in git and did not change).
- When a managed script was altered as if it came from another version, a reinstall on that machine
  failed with `Reinstall conflict: managed file changed`.
- A's receipt reached B's database and daily view after `sync`; B's receipt reached A.
  `daily/v3/<day>.md` and `knowledge/v3/outcomes.md` came out byte for byte identical on both machines.
- With `receipts/** -text` removed: the receipt on B turned into CRLF, the views diverged, and
  resubmitting the same receipt gave `event id collision`.
- Both machines added a card to Last-Session and an entry to Journal and changed the same Threads
  line at the same time: `pull --rebase` merged Last-Session and Journal, keeping both records, and
  stopped on a conflict in Threads.
- While Threads sat with conflict markers: the first SessionStart left the file out as a changed
  source; the SessionStart after `sync` had the markers in its context. `sync` returned
  `warnings: []` and `doctor` showed nothing.
- Two vaults wrote receipts with the same `event_id` and different summaries: both landed on the
  same `receipts/<digest>.md`, and `pull --rebase` stopped on an add/add conflict. After picking A's
  file and continuing, `sync` on B returned `conflicts: []`; B's `recap` and `daily/v3` output kept
  showing B's summary.
