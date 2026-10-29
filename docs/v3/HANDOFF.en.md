# Source-linked agent handoffs

The handoff command creates a size-bounded JSON packet for continuing the same project in
another client. It needs no new model, service, or dependency. From a source checkout:

~~~sh
python3 scripts/mneme_v3.py --vault /notes/vault --state /notes/runtime handoff "Orbit" --project orbit --harness codex --to claude
~~~

In a vault installed from this code, use:

~~~sh
python3 mneme.py handoff "Orbit" --project orbit --harness codex --to claude
~~~

On Windows, use an appropriate Python 3.11+ launcher instead of python3. Both --project
and --to are required. For notes without a project field, the existing
.mneme-projects.json folder mapping can be used. Choosing a recipient client does not send
it a message: the packet is written to stdout, and source excerpts are carried as data.
--harness names the client that created the packet; --to labels its recipient. For a local
handoff between clients, set --harness to the client you are using and --to to the target
client. Examples in this guide use --audience internal, the default, which includes
public and internal notes.

## Packet fields

| Section | Required explicit metadata |
|---|---|
| accepted_decisions | kind: decision, status: accepted |
| proposals | kind: proposal or kind: decision, status: proposed |
| open_tasks | kind: task, status: inbox/active/waiting/blocked |
| other_context | Other eligible sources; no decision or completion is inferred from prose |

JSON frontmatter example:

~~~json
{"id":"orbit-db","kind":"decision","status":"accepted","project":"orbit","revision":1,"visibility":"internal"}
~~~

Writing “approved” in a note body does not make it an accepted decision. Existing
free-form notes are not rewritten. Receipts are outcome claims; even when they remain in
other_context, they are not independently verified outcomes.

Packets preserve source paths, hashes, revisions, facts, and citations. Existing search,
project, privacy, rejection, and invalidation boundaries still apply. The
--audience public option includes only public sources; automatic handoffs do not include
private notes. This is not a security boundary that replaces the recipient's own file
access controls.

The CLI synchronizes sources before building a packet and does not produce one on
conflict. If damaged sources leave a partial index, the packet includes the source_sync
status and warning count. Excluded or private filenames are not copied into packet
warnings. Files may change after packet creation, so the recipient should reread the
source before taking an important action.

The --budget-chars range is 2048–32000 (default 8000) and includes the CLI's indented,
ASCII-escaped JSON output and final newline. used_chars uses the same measure; it is not
a token count. If needed, only text is shortened and text_truncated/truncated is set.
Identity, facts, and source fields are not cut; records that do not fit are omitted and
omitted_count increases. An empty result has abstained: true. A packet is not a complete
summary of every project note or a new decision written in natural language.

## Compare two handoff packets

This example runs from the repository root, installs only a temporary synthetic vault
with the official installer, and uses the installed mneme.py entry point. The first
packet contains an accepted SQLite decision; the note is then changed to a PostgreSQL
proposal. Two UTF-8 packets are generated with the same project, query, source client,
recipient, audience, record limit, and character budget. The real installed handoff-diff
command compares them. No hook runs; no personal vault is read, and there are no network
or model calls.

~~~text
# Windows PowerShell
py -3 docs/v3/examples/handoff_diff_demo.py

# macOS / Linux
python3 docs/v3/examples/handoff_diff_demo.py
~~~

The example captures Python stdout and writes the JSON as UTF-8, so it does not rely on
Windows PowerShell 5's redirection encoding. Packet files, vault, and runtime live in a
temporary directory that is removed when the example finishes. The summary diff shows
the accepted-to-proposed change, the source change, and an excerpt difference.

handoff-diff reads the two UTF-8 packets from disk and compares them directly. It does
not change notes, the index, or tasks, and does not open the source files referenced by
the packets. It reports source hash/revision changes, a decision changing from accepted
to proposed, changed metadata fields, and excerpt shortening separately. Full-text
differences are included only when --include-text is explicitly supplied and both
excerpts are complete. The default output contains no note bodies or fact values.

added_to_packet and removed_from_packet describe packet membership only. A file missing
from a packet is not proof that it was deleted; search order or the budget may have
changed. Packets based on a partial or stale index carry a partial warning. This
comparison does not verify that a model completed an action or establish what is in the
entire vault. Packets are source data, not instructions to execute. Each input file is
limited to 1,000,000 characters and each packet to 20 records. Packets without the older
audience field can only be compared with packets of that same older shape.

## Evaluation

~~~sh
python3 scripts/evaluate_v3_handoff.py
python3 -m unittest discover -s tests -p "v3_handoff_test.py"
~~~

The fixture is normalized to UTF-8/LF and its hash is frozen in a sidecar. It contains
six categories of ten synthetic-source scenarios: source preservation, correction,
explicit classification, freshness, data parity across client adapters, and abstention
and privacy. The runner uses no personal data or model. It reports the fixture hash,
category results, and timings.

This evaluation does not prove that a model will follow rules or answer open-ended
questions correctly in real Claude, Codex, or Hermes sessions. Client-pair tests measure
consistency across adapters to the shared memory engine. A further experiment should
measure continuation quality in real client sessions using the same sources and budget.
