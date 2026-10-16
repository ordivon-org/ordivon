from __future__ import annotations

import re
import sqlite3
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/temporal_pgbackrest_restore_smoke.sh"


def restored_workflow_query(workflow_id: str) -> str:
    """Exercise the exact SQL issued by the real restore-smoke script."""
    line = next(
        line for line in SCRIPT.read_text(encoding="utf-8").splitlines()
        if line.startswith("ROW=$(")
    )
    sql = line.split(' -Atqc "', 1)[1].rsplit('")', 1)[0]
    sql, replacements = re.subn(r"\$\{WORKFLOW_ID[^}]+\}", workflow_id, sql)
    if replacements != 1:
        raise AssertionError("restore smoke query is no longer bound to WORKFLOW_ID")
    return sql


class TemporalPgBackRestRestoreSmokeQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = sqlite3.connect(":memory:")
        self.database.execute(
            "CREATE TABLE executions_visibility "
            "(workflow_id TEXT, status INTEGER, start_time TEXT)"
        )

    def tearDown(self) -> None:
        self.database.close()

    def query(self, workflow_id: str) -> list[tuple[str]]:
        return self.database.execute(restored_workflow_query(workflow_id)).fetchall()

    def test_multiple_completed_runs_prove_a_bounded_historical_record(self) -> None:
        self.database.executemany(
            "INSERT INTO executions_visibility VALUES (?, ?, ?)",
            [("repeated", 2, "2026-10-14"), ("repeated", 2, "2026-10-15")],
        )
        self.assertEqual(self.query("repeated"), [("repeated|2",)])

    def test_incomplete_runs_do_not_verify_recovery(self) -> None:
        self.database.executemany(
            "INSERT INTO executions_visibility VALUES (?, ?, ?)",
            [("running", 1, "2026-10-15"), ("running", 1, "2026-10-16")],
        )
        self.assertEqual(self.query("running"), [])

    def test_missing_workflow_fails_closed(self) -> None:
        self.assertEqual(self.query("missing"), [])


if __name__ == "__main__":
    unittest.main()
