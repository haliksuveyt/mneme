# Install, update, and rollback

The vault's mneme.py is the single command entry point. Run commands from the vault
folder. Examples use python3 on macOS/Linux and py -3 on Windows. Python 3.11 or newer
is required.

## First install without Git

Download the product ZIP and its .sha256 file from the [latest stable release](https://github.com/haliksuveyt/mneme/releases/latest).
Verify the ZIP's SHA-256 against the accompanying file before extracting it. The product
ZIP is different from GitHub's automatically generated source archive. Choose or create
a vault folder, then run from the extracted package:

~~~sh
python3 scripts/install_v3.py --vault "/path/to/My Brain"
~~~

Windows:

~~~powershell
py -3 scripts/install_v3.py --vault "C:\Notes\My Brain"
~~~

Runtime state is stored outside the vault in the operating system's local application
data directory. To choose another dedicated local directory, pass --state at install:

~~~sh
python3 scripts/install_v3.py --vault "/path/to/My Brain" --state "/local/mneme-state"
~~~

The installed entry points and launchers remember this choice. No Git, pip, new account,
or service is required. Open the vault in the AI client and start a new session. If hook
definitions changed, complete the client's required trust review; the updater does not
create a trust record.

## Check and update

~~~sh
python3 mneme.py doctor
python3 mneme.py update --check
python3 mneme.py update
~~~

Doctor reports local records, pending work, and issues. A metadata report does not prove
that a real client received context or interpreted every note correctly.

update --check inspects the official stable release and verifies the package in a
temporary location without changing the vault or existing runtime files. Without a
local package, it needs network access. update applies the verified version. Repeating
an update to the same version is a no-op. Version ordering is numeric; an older package
is not installed as a downgrade. Use rollback to return to the previous installation.

The default source is the official GitHub stable release for haliksuveyt/mneme. Preview
builds, moving development branches, and third-party package sources are not selected
automatically. If the stable release or expected ZIP is unavailable, Mneme reports an
error instead of claiming that the vault is current.

For a ZIP already downloaded and trusted, update can work without network access:

~~~sh
python3 mneme.py update --check --package "/downloads/mneme-v3-X.Y.Z.zip"
python3 mneme.py update --package "/downloads/mneme-v3-X.Y.Z.zip"
~~~

A checksum checks file integrity; it is not an independent publisher signature or a
replacement for trusting the source.

## Update shortcuts

The installer places only the applicable platform shortcut in the vault:

| Platform | Shortcut |
|---|---|
| macOS | Mneme Güncelle.command |
| Windows | Mneme Guncelle.cmd |
| Linux | Mneme Güncelle.desktop and Mneme Güncelle.sh |

Each calls the installed mneme.py update command and contains no separate update logic.
The operating system may ask permission to open or run the file. The selected Python
runtime path is recorded during setup; if Python is later moved, review the installation.

## Recover or roll back

~~~sh
python3 mneme.py recover
python3 mneme.py rollback
~~~

recover reads the journal of an interrupted operation and resumes the planned work. An
error message does not necessarily mean that the operation was cancelled: system files
may have been written before the successful version stamp.

rollback restores the backup from the last system operation. It does not roll back the
entire history of the vault, and user notes added later are not deleted. A clean V3
install is reported as uninstalled; Mneme does not invent an older version. If a managed
file has an intervening user change, the operation stops with a conflict rather than
overwriting it. Supported JSON settings preserve unrelated changes.

Wait for a locked or active writer to finish before retrying. Do not delete a lock or
sentinel file for a lost operation without investigating it. A line-ending-only change
does not count as a user edit; files are restored to stock LF format when rewritten.

## State directory

Runtime state belongs outside the vault, on a local disk that is not cloud-synced.
Installer option --state pins a dedicated directory. The database is associated with
the vault root, so moving state for the same vault does not invalidate it. Moving the
vault is a separate operation: local state is rebuilt from Markdown.

If you need to move state, close agent sessions first. Read the pinned path from
.mneme-runtime.json but do not edit that file manually. Copy the entire state directory
and compare file hashes, then run the installer with the new --state path and inspect
the plan first. Do not copy a pending update-journal.json; recover the interrupted
operation in the old location before moving state. Verify doctor from both inside and
outside any packaged client environment. Delete the old directory only after the
verification succeeds.

Windows MSIX containers can make the same LOCALAPPDATA path resolve differently inside
and outside the package. Mneme doctor reports multiple sibling state roots and related
diagnostics. These are informational; investigate which copy is current and move it
using the supported installer path.

## Advanced and historical cases

This English guide covers the normal user workflow. Detailed MSIX recovery, legacy
installer issues, historical release incidents, package exclusions, maintainer release
steps, and platform verification are in the [full update guide in Turkish](UPDATE.md).
