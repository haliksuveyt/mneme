"""Bounded source excerpts for a sequential handoff; no model calls or claims of completion."""
from __future__ import annotations

import json
import difflib
from pathlib import Path
import re

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
            "project": project, "query": query, "audience": audience, "sections": sections,
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


def read_packet(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        text = stream.read(1_000_001)
    if len(text) > 1_000_000:
        raise ValueError("handoff packet exceeds 1,000,000 characters")
    return json.loads(text)


def _packet_records(packet):
    if not isinstance(packet, dict) or packet.get("format") != "mneme-handoff-v1":
        raise ValueError("expected mneme-handoff-v1 packet")
    if not all(isinstance(packet.get(key), str) and packet[key].strip() for key in ("project", "query")):
        raise ValueError("packet project/query missing")
    if "source_sync" in packet and not isinstance(packet["source_sync"], dict):
        raise ValueError("invalid packet source_sync")
    sections = packet.get("sections")
    names = ("accepted_decisions", "proposals", "open_tasks", "other_context")
    if not isinstance(sections, dict) or set(sections) != set(names):
        raise ValueError("invalid handoff sections")
    records = {}
    for section, values in sections.items():
        if not isinstance(values, list):
            raise ValueError("handoff sections must contain lists")
        for record in values:
            if (not isinstance(record, dict) or not isinstance(record.get("id"), str)
                    or not record["id"] or not isinstance(record.get("source"), str)
                    or not isinstance(record.get("text"), str)
                    or not isinstance(record.get("source_sha256"), str)
                    or not re.fullmatch(r"[0-9a-fA-F]{64}", record["source_sha256"])):
                raise ValueError("invalid source identity in handoff packet")
            if record["id"] in records or section_for(record) != section:
                raise ValueError("duplicate source ID or inconsistent classification")
            records[record["id"]] = (section, record)
    if len(records) > 20:
        raise ValueError("handoff packet contains more than 20 records")
    return records


def compare_packets(before, after, *, include_text=False):
    left, right = _packet_records(before), _packet_records(after)
    if before["project"] != after["project"] or before["query"] != after["query"]:
        raise ValueError("compare packets for the same project and query")
    if before.get("audience") != after.get("audience"):
        raise ValueError("compare packets with the same audience (legacy packets omit audience)")

    def identity(entry):
        section, record = entry
        return {"id": record["id"], "source": record["source"], "section": section,
                "revision": record.get("revision"), "source_sha256": record["source_sha256"]}

    result = {"format": "mneme-handoff-diff-v1", "source_data_only": True,
              "project": before["project"], "query": before["query"], "packet_scope_only": True,
              "partial": any(p.get("truncated") or p.get("stale_count") or
                             p.get("source_sync", {}).get("status") == "degraded" for p in (before, after)),
              "added_to_packet": [identity(right[key]) for key in sorted(right.keys() - left.keys())],
              "removed_from_packet": [identity(left[key]) for key in sorted(left.keys() - right.keys())],
              "updated": [], "unchanged_count": 0}
    for key in sorted(left.keys() & right.keys()):
        old_section, old = left[key]; new_section, new = right[key]
        metadata = sorted(name for name in old.keys() | new.keys() if name not in
                          ("id", "text", "text_truncated", "source", "source_sha256") and old.get(name) != new.get(name))
        source_changed = old["source_sha256"].lower() != new["source_sha256"].lower()
        excerpt_changed = old["text"] != new["text"] or bool(old.get("text_truncated")) != bool(new.get("text_truncated"))
        if not (source_changed or excerpt_changed or metadata or old_section != new_section or old["source"] != new["source"]):
            result["unchanged_count"] += 1
            continue
        change = {"id": key, "before": identity(left[key]), "after": identity(right[key]),
                  "source_changed": source_changed, "excerpt_changed": excerpt_changed,
                  "metadata_fields_changed": metadata,
                  "status_before": old.get("status"), "status_after": new.get("status")}
        if include_text:
            if old.get("text_truncated") or new.get("text_truncated"):
                change["text_diff_unavailable"] = "truncated_excerpt"
            else:
                change["text_diff"] = "\n".join(difflib.unified_diff(
                    old["text"].splitlines(), new["text"].splitlines(), fromfile="before", tofile="after", lineterm=""))
        result["updated"].append(change)
    return result
