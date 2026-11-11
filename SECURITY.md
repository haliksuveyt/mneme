# Security policy

## Supported versions

Only the latest release receives security fixes. Check the [releases page](https://github.com/haliksuveyt/mneme/releases/latest) and update with `python3 mneme.py update` (Windows: `py -3 mneme.py update`).

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Use GitHub's private vulnerability reporting: open the repository's **Security** tab, choose **Report a vulnerability**, and describe the problem. Include:

- the Mneme version (`VERSION` or the `doctor` output),
- your OS, Python version and client (Claude Code, Codex, Antigravity, Hermes, OpenCode or OMP),
- steps to reproduce, using synthetic notes only. Do not attach real vault content or real secrets.

Follow-up happens in the advisory thread. Fixes ship in a new release, and the release notes credit the reporter unless you prefer otherwise.

## Scope

In scope:

- **Hooks and installer.** The managed hook definitions, the installer and the updater, including checksum and path handling, and anything that lets note text run as a command or write outside the vault.
- **Secret filter.** The optional `secret_filter` preference and `secret-patterns.txt` handling, which redact secrets before notes, receipts and tasks are written. It is off by default. A secret that should have been redacted and was not is a valid report.
- **MCP server.** `mneme.py mcp`, the stdio server. Inputs that crash it, bypass its rules (for example overwriting notes or deleting content, which it must not do) or leak data are in scope.
- **Visibility and trust rules.** Notes marked private or untrusted must not reach exported context, handoff packets or other projects.

Out of scope: vulnerabilities in the AI clients themselves, the model providers, or third-party tools; issues that require an attacker who already has write access to your vault and your user account; and loss of data you stored in notes without enabling the secret filter.

Earlier design reviews are recorded in [docs/archive/GATE-REVIEW-SECURITY.md](docs/archive/GATE-REVIEW-SECURITY.md). It covers the legacy V2 scripts, which are no longer the supported engine.
