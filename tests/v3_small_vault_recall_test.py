"""A first-time user's obvious question must find a small vault's note; unrelated ones must not."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
from v3_package_helpers import inherited_env, TemporaryDirectory

DATABASE = "Orbit stores data in SQLite for the first release. Revisit PostgreSQL after beta."


class SmallVaultRecallTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.vault = Path(self.temp.name) / "vault"
        (self.vault / "notes").mkdir(parents=True)
        self.state = Path(self.temp.name) / "state"
        self.note("orbit-database", "decision", "accepted", "orbit", DATABASE)
        self.note("orbit-auth", "task", "active", "orbit", "Add login with email links before the beta.")
        self.note("atlas-hosting", "decision", "accepted", "atlas", "Atlas runs on a single virtual machine.")
        self.assertEqual(self.run_cli("sync").returncode, 0)

    def note(self, note_id, kind, status, project, text):
        metadata = {"id": note_id, "kind": kind, "status": status, "project": project, "revision": 1, "visibility": "internal"}
        (self.vault / "notes" / (note_id + ".md")).write_text(
            "---\n" + json.dumps(metadata) + "\n---\n\n" + text + "\n", encoding="utf-8", newline="\n")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/mneme_v3.py"), "--vault", str(self.vault), "--state", str(self.state), *args],
                              capture_output=True, text=True, encoding="utf-8", env=inherited_env())

    def ids(self, query, project="orbit"):
        result = self.run_cli("context", query, "--project", project, "--harness", "claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["abstained"], not output["records"])
        return [record["id"] for record in output["records"]]

    def test_questions_find_the_decision(self):
        for query in ("SQLite", "Orbit stores data", "Orbit database", "which database does Orbit use"):
            with self.subTest(query=query):
                self.assertEqual(self.ids(query), ["orbit-database"])

    def test_unrelated_queries_still_abstain(self):
        for query in ("kubernetes ingress", "Orbit pricing", "which hosting does Orbit use", "database"):
            with self.subTest(query=query):
                self.assertEqual(self.ids(query), [])

    def test_other_project_does_not_borrow_the_note(self):
        self.assertEqual(self.ids("which database does Atlas use"), [])
        self.assertEqual(self.ids("Atlas database", project="atlas"), [])
        self.assertEqual(self.ids("Atlas hosting", project="atlas"), ["atlas-hosting"])


if __name__ == "__main__":
    unittest.main()
