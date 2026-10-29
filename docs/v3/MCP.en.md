# Mneme MCP server

Clients without hook support, such as Claude Desktop, Cursor, or Zed, can use Mneme
through MCP. The server uses Python's standard library and needs no additional package.
Each tool runs the vault's own mneme.py --json command, so secret filtering, revision
checks, and rejection rules match the CLI.

## Tools

| Tool | Purpose |
|---|---|
| mneme_search | Search the vault with source links (query, optional project, limit) |
| mneme_note_create | Create a note under notes/ or knowledge/ without overwriting an existing file |
| mneme_note_edit | Edit an existing note body (append, replace_section, upsert_card) |
| mneme_supersede | Mark an older note as superseded by a newer one; nothing is deleted |
| mneme_doctor | Check memory health |

There is no delete tool. Tasks, receipts, and generated views cannot be changed with
note-edit.

## Setup

For Claude Desktop (claude_desktop_config.json) or a similar client:

~~~json
{"mcpServers":{"mneme":{"command":"py","args":["-3","C:\\Notes\\Vault\\mneme.py","mcp"]}}}
~~~

On macOS/Linux, use command python3 and args ["/path/to/vault/mneme.py", "mcp"].

For Claude Code:

~~~sh
claude mcp add mneme -- py -3 C:\Notes\Vault\mneme.py mcp
~~~
