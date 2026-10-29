# Mneme: agent installation guide

This file is the canonical installation procedure for the following user request:

> Install my second brain in this folder. If Mneme is already installed, update it while
> preserving my notes. Handle the required download and installation steps. At the end,
> save an example fact and retrieve it in a new session so we can verify it together.

The user should not have to download a ZIP, extract an archive, or look up an install
command. The agent does those things. Only the ordinary folder, workspace, or hook trust
review shown by the client is the user's responsibility.

## Non-negotiable rules

1. Install into the current vault/workspace folder where the user made this request.
2. Never delete, move, rename, or overwrite user notes with `git reset`.
3. Detect any existing V1, V2, or V3 installation first. The official installer and
   updater handle backups, conflicts, and `rollback`; do not bypass those checks manually.
4. Use only the latest stable GitHub release package from haliksuveyt/mneme. Do not use
   source-code archives or third-party packages.
5. Never expose raw notes, credentials, private paths, or secret values in terminal output,
   the conversation, or external services.
6. Do not claim success until installation is complete. Check the installer or updater exit
   code, version stamp, and the `mneme.py` doctor result. Read the installer's companion and
   skills.conflicts fields too. If needs_attention appears, do not complete the related
   step without asking the user.

## 1. Find the target and Python

- The vault path is the current workspace root. Use its absolute, canonical path.
- Find Python 3.11 or newer:
  - macOS/Linux: try `python3`, then python
  - Windows: try `py -3`, then python
- Run the interpreter and check its actual version.
- If no suitable Python is installed, treat this installation request as authorization
  to install a stable Python 3 release using the operating system's official package
  manager. Ask the user for approval only if administrator permission or operating-system
  approval is required. Do not use random download sites.

Obsidian is for opening notes; no Obsidian plugin is needed during installation. Git, pip,
Node, Mem0, an API key, and a continuously running server are not required.

## 2. Download and verify the official package in a temporary location

First determine the latest stable release tag. The first method is the GitHub API:

https://api.github.com/repos/haliksuveyt/mneme/releases/latest

Use the response's `tag_name`; `draft` and `prerelease` must both be false. Unauthenticated API
requests are rate-limited per IP and hour. If the API returns HTTP 403 or 429, do not
keep retrying it or guess the version. Instead, read the redirect from:

https://github.com/haliksuveyt/mneme/releases/latest

It redirects to https://github.com/haliksuveyt/mneme/releases/tag/`vX.Y.Z`; the final path
component is the tag.

The release tag must be a stable `vMAJOR.MINOR.PATCH`. For a `vX.Y.Z` tag, the required
assets are:

- mneme-v3-`X.Y.Z`.zip
- mneme-v3-`X.Y.Z`.zip.sha256

Do not pin the version or mistake the `X.Y.Z` placeholders in these examples for a real
version: derive the names from the actual tag. The API response's `browser_download_url`
fields are the download URLs. If you used the redirect, the URLs have this form:

https://github.com/haliksuveyt/mneme/releases/download/`vX.Y.Z`/mneme-v3-`X.Y.Z`.zip
https://github.com/haliksuveyt/mneme/releases/download/`vX.Y.Z`/mneme-v3-`X.Y.Z`.zip.sha256

Download both files over HTTPS to the operating system's temporary directory. Compare the
first field in the `SHA-256` file with the ZIP's local `SHA-256` value. If they differ, stop,
do not extract the archive, and report the problem.

When extracting the ZIP to a temporary directory, check that every member's destination
stays inside that directory. Reject archives containing absolute paths, .. traversal, or
symbolic links. The package root must contain `manifest.json` and `scripts/install_v3.py`.

## 3. Install or update

Check the vault root's `.mneme-version` file first, then choose the matching path.

### 3a. No `.mneme-version`, or an existing V1/V2 installation: official installer

Use the same Python interpreter you found:

```
<python> <temporary-package>/scripts/install_v3.py --vault <absolute-vault-path>
```

For an existing V1/V2 installation, first run the same command with `--plan` appended.
This changes nothing and shows what would be written or retired. If the user manually
customized an old runner, the installer exits with code 1 and reports
`Customized legacy runner requires review <path>`. Do not delete or overwrite that file.
Briefly summarize its contents and get the user's explicit approval; only then use
`--accept-customized-legacy <vault-relative-path>` for that one file. There is no bulk
migration. Details are in the [Turkish migration guide](https://github.com/haliksuveyt/mneme/blob/main/docs/v3/MIGRATION.md).

### 3b. `.mneme-version` already starts with 3.: installed updater

For an existing V3 installation, the preferred route is the `mneme.py` updater in the
vault. From the vault root, run it with the ZIP you downloaded and verified:

```
<python> mneme.py update --check --package <downloaded-zip>
<python> mneme.py update --package <downloaded-zip>
```

A result of `updated` means the version changed; `noop` means the vault is already current.
Both are successful. This route avoids an unnecessary new client trust review and can be
fully rolled back with `<python>` `mneme.py` `rollback` if needed. It also works without
`--package` when network access is available; a network error such as `http_403` does not
mean the installation is current. If a very old V3 package does not recognize update,
use path 3a. The `mneme.py` --help output does not list update, `rollback`, or `recover`; they
are implemented separately in the entry script and still work. Do not fall back to 3a
just because --help omits them.

### Applies to both paths

If the vault has `.mneme-runtime.json`, the installer and updater preserve its external,
local state location. On a new installation, state is written outside the vault to the
appropriate local application-data directory on macOS, Linux, or Windows. Do not move the
state into the vault or into iCloud, OneDrive, or Dropbox.

If a managed file was changed manually, either path exits with code 1 and reports
Reinstall conflict: managed file changed <path>. Do not overwrite the user's file.
Briefly explain which file conflicts and why the installer cannot continue automatically.
For an interrupted official V3 operation, first use `mneme.py` `recover` in the existing
vault; do not copy files again unless recovery fails. Do not update an installed vault
with your own curl, copy, or git pull sequence.

## 4. Verify the installation

Run these checks from the vault root:

```
<python> mneme.py doctor --human
<python> mneme.py preferences --human
```

Also check that `.mneme-version`, `.agents/skills/mneme/SKILL.md`,
`.agents/skills/mneme-doktor/SKILL.md`, and
`.agents/skills/mneme-guncelle/SKILL.md` exist. After installation, delete the temporary
ZIP and extraction folder; do not touch the user's notes. Installation adds a managed
section marked `<!-- mneme-v3:start -->` to the vault-root `AGENTS.md`, preserving its
existing content. If `CLAUDE.md` does not exist, it is created with only the @`AGENTS.md`
import line. A `CLAUDE.md` that already imports `AGENTS.md` does not get a duplicate
section; one that does not import it receives the same section. Tell the user what was
added in your summary.

The installer leaves only the platform's update shortcut in the vault root: Mneme
Güncelle.command on macOS, `Mneme Guncelle.cmd` on Windows, or `Mneme Güncelle.sh` and
the desktop entry that calls it on Linux. Each calls the installed `mneme.py` update
command; none contains separate update logic. The user can later update by asking the
agent or using the shortcut.

For Codex, show the user the `/hooks` review. For Claude Code and Antigravity, use the
normal workspace/folder trust review. Do not invent a trust hash or bypass approval.
OpenCode has no additional trust step; the plugin loads when OpenCode opens the vault
folder. OMP has no additional trust step; its `.omp/hooks/pre/mneme-v3.ts` hook loads when
OMP opens the vault folder. If Hermes Agent is used, the installer writes plugin files
into the vault, but the user must run `hermes plugins enable mneme-v3` and restart Hermes
to connect it; see the [Hermes guide](https://github.com/haliksuveyt/mneme/blob/main/docs/v3/HERMES.md).
Then ask the user to open a new client session. If automatic hook context does not appear
in Codex Desktop, do not claim installation success on that basis; context can be refreshed
directly with the installed `mneme.py` context and sync commands.

## 5. Meet the user and verify a real readback

After installation, read `.agents/skills/mneme/SKILL.md`. Ask the user no more than three
short onboarding questions. Save their answers in source Markdown notes: identity and
address preferences belong in `Core.md` in the companion folder. Only the official
installer creates this folder. It is not created immediately on path 3b (updating from an
older V3), and it is also not created when the installer's companion field reports
needs_attention. In either case, do not create a new identity folder: look for an
existing `Core.md` or `Soul.md` in the vault and ask the user which one to use if there
are multiple candidates.

Create new semantic notes only under `notes/` or `knowledge/`, using
`<python>` `mneme.py` note-create --file NOTE_JSON; the folder is created if needed. Then
run `<python>` `mneme.py` sync and retrieve the same information in a separate command with
`<python>` `mneme.py` context "<topic to look up>". Tell the user the returned source path.
Opening and reading the file directly does not count as readback. Do not invent profile
details.

Finally, ask the user to open a new session and ask about the saved example fact. Do not say
that cross-session memory has been verified until that readback happens in the new session.

The default consumption profile is Normal. The user can request a change through the mneme
skill, for example, "switch to economical mode," "set the check interval to 30 minutes,"
or "turn off automatic checks." Local checks do not call a model and no timer is installed
to wake a closed application.

## Optional Jev advisor

Jev is not part of installation and is off by default. To check it, run
`<python> mneme.py jev status --human` and confirm that the mode is off and no key is configured. The CLI labels may be Turkish; do nothing else.
Do not enable it, ask for an API key, or bring it up unless the user explicitly asks.

If the user asks, follow the Jev section of the installed
`.agents/skills/mneme/SKILL.md` and the steps in the Turkish [Jev guide](https://github.com/haliksuveyt/mneme/blob/main/docs/v3/JEV.md).
(The installed package has no docs/ folder.) The key belongs in the `TYPESAFE_API_KEY`
environment variable; never put it in Markdown, version control, or a command argument.
The jev command does not accept or print the key. If you use `env_file`, it must be an
absolute path. Under rule 5, do not ask for the key in chat or print it into chat; the
user sets it in their own shell. First measure with jev shadow, then use jev on.

While Jev is on, the agent's context ... --jev, jev-answer, and jev-review calls also
send data to the provider: context --jev sends the query and a snippet from each eligible
candidate. auto_context is a separate opt-in. When enabled with jev on --enable
auto_context, every turn sends the prompt and the titles plus first 600 characters of up
to 8 candidate notes to the provider. Private notes are never sent. In V3.2.0 and later,
records with remote_allowed: false or sensitivity: sensitive are also never sent.
Tell the user about this before enabling either option. When the mode is not off and no
key is available, the command warns and calls fall back to local results. Turn it off with
`<python>` `mneme.py` jev off; in an emergency, set `MNEME_JEV_DISABLE=1` to stop calls
without changing the saved mode.

A local alternative that does not require a key is available if the user explicitly asks:
use an independently installed laya-serve (LAYA_HOST=127.0.0.1, LAYA_PORT=8765) with
`<python> mneme.py jev shadow --provider laya`, then `jev status --check`. Do not install
Laya, PyTorch, or model weights into Mneme's environment. Laya runs only in shadow mode:
its measured output is much weaker than Jev's, so scores are recorded for measurement
only and do not change any result. jev on --provider laya is rejected with
`laya_shadow_only`, and jev status reports the mode as shadow (only). The same data
rules apply: private, remote_allowed: false, and sensitivity: sensitive records are
not sent to Laya either. To return to Jev, use jev on --provider typesafe.

## Manual fallback

If the agent truly lacks network or file permissions, direct the user to:

https://github.com/haliksuveyt/mneme

The V3 ZIP button on that page points to the latest official stable GitHub release package
and its `SHA-256` file. The same files are available directly from
https://github.com/haliksuveyt/mneme/releases/latest. After a manual installation, verify
that the version is current from the vault root with `<python>` `mneme.py` update --check.
This is a last-resort alternative to automatic installation, not the first choice.