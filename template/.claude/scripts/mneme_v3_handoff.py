"""Bounded source excerpts for a sequential handoff; no model calls or claims of completion."""
from __future__ import annotations

import json

from mneme_v3 import HARNESSES


def section_for(record):
    # Only explicit metadata makes a decision accepted. Body prose is never parsed.
    kind, status = record.get("kind"), record.get("status")
    if kind == "decision" and status == "accepted":
        return "accepted_decisions"
    if kind == "proposal" or (kind == "decision" and status == "proposed"):
        return "proposals"
    if kind == "task" and status in ("inbox", "active", "waiting", "blocked"):
        return "open_tasks"
    return "other_context"


def serialized_size(packet):
    """Match the CLI's ASCII-escaped, indented JSON including the final newline."""
    return len(json.dumps(packet, ensure_ascii=True, indent=2)) + 1


def build_packet(store, query, *, project, from_harness="codex", to_harness="claude",
                 audience="internal", limit=8, budget_chars=8000, source_sync=None):
    if from_harness not in HARNESSES or to_harness not in HARNESSES:
        raise ValueError("unsupported handoff harness")
    if not isinstance(project, str) or not project.strip() or len(project) > 128:
        raise ValueError("handoff requires a project of 1..128 characters")
    if not isinstance(query, str) or not query.strip() or len(query) > 512:
        raise ValueError("handoff requires a query of 1..512 characters")
    if audience not in ("internal", "public"):
        raise ValueError("handoff audience must be internal or public")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("handoff limit must be 1..20")
    if type(budget_chars) is not int or not 2048 <= budget_chars <= 32000:
        raise ValueError("handoff budget must be 2048..32000 characters")
    context = store.context_for(from_harness, query, project=project, audience=audience,
                                limit=limit, budget_chars=budget_chars)
    selected = list(context["records"])
    dropped = 0
    clipped = False
    # Source-sync messages can contain excluded/private filenames; only counts travel.
    sync = source_sync or {"status": "not_requested"}
    sync_status = {"status": sync.get("status", "unknown"), "warning_count": len(sync.get("warnings") or [])}
    while True:
        sections = {key: [] for key in ("accepted_decisions", "proposals", "open_tasks", "other_context")}
        for record in selected:
            sections[section_for(record)].append(record)
        packet = {
            "format": "mneme-handoff-v1", "source_data_only": True,
            "from_harness": from_harness, "to_harness": to_harness,
            "project": project, "query": query, "sections": sections,
            "citations": [{"id": record["id"], "source": record["source"]} for record in selected],
            "abstained": not selected,
            "truncated": context["truncated"] or dropped > 0 or clipped,
            "omitted_count": context["omitted_count"] + dropped,
            "stale_count": context.get("stale_count", 0),
            "source_sync": sync_status,
            "budget_chars": budget_chars, "used_chars": 0,
        }
        # The length field itself contributes digits; converge before checking the cap.
        while packet["used_chars"] != serialized_size(packet):
            packet["used_chars"] = serialized_size(packet)
        if packet["used_chars"] <= budget_chars:
            return packet
        if not selected:
            raise ValueError("handoff envelope exceeds budget; shorten query/project")
        # JSON escaping/indentation can make a record bigger than retrieval's compact
        # budget. Shorten text only; never trim metadata, facts or source identity.
        text = selected[-1].get("text", "")
        if len(text) > 64:
            selected[-1] = dict(selected[-1], text=text[:len(text) // 2], text_truncated=True)
            clipped = True
            continue
        selected.pop()
        dropped += 1
