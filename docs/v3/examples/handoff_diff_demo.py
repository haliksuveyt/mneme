#!/usr/bin/env python3
"""Run a complete, offline handoff and diff demo against temporary synthetic data."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[3]
INSTALLER = REPO / "scripts" / "install_v3.py"
PROJECT = "orbit"
QUERY = "Orbit database migration"
FROM_HARNESS = "claude"
TO_HARNESS = "codex"
AUDIENCE = "internal"
LIMIT = 8
BUDGET_CHARS = 8000


def note(status, revision, database, text):
    metadata = {
        "id": "orbit-database",
        "kind": "decision",
        "status": status,
        "project": PROJECT,
        "revision": revision,
        "visibility": "internal",
        "facts": {"database": database},
    }
    return "---\n" + json.dumps(metadata, ensure_ascii=False, sort_keys=True) + "\n---\n\n" + text + "\n"


def run_command(command, cwd):
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            "CLI command failed ({}): {}\n{}".format(
                result.returncode, " ".join(command), result.stderr.strip()
            )
        )
    return result.stdout


def write_packet(path, output):
    packet = json.loads(output)
    path.write_text(output, encoding="utf-8", newline="\n")
    return packet


def handoff_arguments():
    return (
        "handoff",
        QUERY,
        "--project",
        PROJECT,
        "--harness",
        FROM_HARNESS,
        "--to",
        TO_HARNESS,
        "--audience",
        AUDIENCE,
        "--limit",
        str(LIMIT),
        "--budget-chars",
        str(BUDGET_CHARS),
    )


def main():
    if not INSTALLER.is_file():
        raise SystemExit("Run this example from a Mneme source checkout with scripts/install_v3.py present.")

    with tempfile.TemporaryDirectory(prefix="mneme-handoff-demo-") as temporary:
        root = Path(temporary)
        vault = root / "vault"
        state = root / "runtime"
        notes = vault / "notes"
        notes.mkdir(parents=True)
        vault_cli = vault / "mneme.py"
        source = notes / "orbit.md"
        before_path = root / "before.json"
        after_path = root / "after.json"

        run_command(
            [sys.executable, str(INSTALLER), "--vault", str(vault), "--state", str(state)],
            REPO,
        )
        if not vault_cli.is_file():
            raise AssertionError("The installer did not create the synthetic vault's mneme.py entrypoint.")
        run_command([sys.executable, str(vault_cli), "init"], vault)
        source.write_text(
            note(
                "accepted",
                1,
                "SQLite",
                "Orbit release uses SQLite. Database migration stays in the current launch plan.",
            ),
            encoding="utf-8",
            newline="\n",
        )
        before = write_packet(before_path, run_command([sys.executable, str(vault_cli), *handoff_arguments()], vault))

        source.write_text(
            note(
                "proposed",
                2,
                "PostgreSQL",
                "Orbit release now proposes PostgreSQL. Database migration needs a revised launch plan.",
            ),
            encoding="utf-8",
            newline="\n",
        )
        after = write_packet(after_path, run_command([sys.executable, str(vault_cli), *handoff_arguments()], vault))

        if before["from_harness"] != FROM_HARNESS or before["to_harness"] != TO_HARNESS:
            raise AssertionError("The packet did not keep the requested source and recipient labels.")
        if len(before["sections"]["accepted_decisions"]) != 1:
            raise AssertionError("The first packet should contain the accepted synthetic decision.")
        if len(after["sections"]["proposals"]) != 1:
            raise AssertionError("The second packet should contain the proposed synthetic decision.")
        for field in ("from_harness", "to_harness", "project", "query", "audience", "budget_chars"):
            if before.get(field) != after.get(field):
                raise AssertionError("The packet scope changed between runs: {}".format(field))
        if (
            before["sections"]["accepted_decisions"][0].get("facts", {}).get("database") != "SQLite"
            or after["sections"]["proposals"][0].get("facts", {}).get("database") != "PostgreSQL"
        ):
            raise AssertionError("The synthetic database decision did not change as described.")

        diff_output = run_command(
            [sys.executable, str(vault_cli),
             "handoff-diff",
             "--before",
             str(before_path),
             "--after",
             str(after_path),
             "--include-text",
            ],
            vault,
        )
        diff = json.loads(diff_output)
        if len(diff["updated"]) != 1:
            raise AssertionError("The demo should produce one updated source in the packet diff.")
        change = diff["updated"][0]
        if (
            change["before"]["section"] != "accepted_decisions"
            or change["after"]["section"] != "proposals"
            or not change["source_changed"]
            or not change.get("text_diff")
        ):
            raise AssertionError("The demo diff did not show the decision and source change.")

        print("Synthetic handoff demo passed; no model or network calls were made.")
        print("scope: project={}, query={!r}, harness={} -> {}, audience={}, limit={}, budget_chars={}".format(
            PROJECT, QUERY, FROM_HARNESS, TO_HARNESS, AUDIENCE, LIMIT, BUDGET_CHARS
        ))
        print("before packet: {}".format(before_path))
        print("after packet:  {}".format(after_path))
        print("handoff-diff --include-text:")
        print(json.dumps(diff, ensure_ascii=False, indent=2))
        print("The synthetic vault, runtime, and packet files are removed when this script exits.")


if __name__ == "__main__":
    main()
