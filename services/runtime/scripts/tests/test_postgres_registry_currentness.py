"""Fail-closed Runtime PostgreSQL stage/source-currentness consumer tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "postgres_registry_currentness.py"


class PgSourceCurrentnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ordivon-pg-source-proof-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.sqlite3"
        self.snapshot = self.root / "snapshot.json"
        self.stage = self.root / "pg-stage.json"
        db = sqlite3.connect(self.source)
        try:
            db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
            db.execute("CREATE TABLE artifacts (id TEXT PRIMARY KEY)")
            db.execute("INSERT INTO jobs (id) VALUES ('job1')")
            db.commit()
        finally:
            db.close()
        self.row_digest = hashlib.sha256(b"test").hexdigest()
        self.snapshot_data = {
            "kind": "ordivon-rw12-source-snapshot",
            "complete": True,
            "quickCheck": "ok",
            "sourcePath": str(self.source),
            "sha256": hashlib.sha256(b"frozen").hexdigest(),
            "rowCounts": {"jobs": 1, "artifacts": 0},
        }
        self.stage_data = {
            "kind": "ordivon-runtime-pg-staging-non-authority",
            "postgres_schema": "rw12_stage_cutover_r1",
            "promotion_allowed": False,
            "snapshot_sha256": self.snapshot_data["sha256"],
            "row_total": 1,
            "tables": {
                key: {
                    "count": value,
                    "source_row_sha256": self.row_digest,
                    "target_row_sha256": self.row_digest,
                }
                for key, value in self.snapshot_data["rowCounts"].items()
            },
        }
        self.save()

    def save(self) -> None:
        self.snapshot.write_text(json.dumps(self.snapshot_data))
        self.stage.write_text(json.dumps(self.stage_data))

    def invoke(self) -> tuple[int, dict]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source",
                str(self.source),
                "--snapshot",
                str(self.snapshot),
                "--stage",
                str(self.stage),
            ],
            text=True,
            capture_output=True,
            timeout=15,
        )
        self.assertFalse(result.stderr, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_equal_counts_are_still_unknown_not_cutover_admission(self):
        code, result = self.invoke()
        self.assertEqual(code, 4)
        self.assertEqual(result["verdict"], "UNKNOWN_COUNTS_ONLY")
        self.assertFalse(result["promotion_admitted"])
        self.assertEqual(result["delta_rows"], 0)

    def test_new_source_row_blocks_old_pg_stage(self):
        db = sqlite3.connect(self.source)
        db.execute("INSERT INTO artifacts (id) VALUES ('new-effect')")
        db.commit()
        db.close()
        code, result = self.invoke()
        self.assertEqual(code, 3)
        self.assertEqual(result["verdict"], "BLOCKED_SOURCE_DRIFT")
        self.assertEqual(result["delta_rows"], 1)
        self.assertEqual(next(x for x in result["table_rows"] if x["table"] == "artifacts")["delta"], 1)
        self.assertFalse(result["promotion_admitted"])

    def test_stage_cannot_claim_writer_authority(self):
        self.stage_data["promotion_allowed"] = True
        self.save()
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(result["verdict"], "INVALID_EVIDENCE")

    def test_receipt_must_bind_exact_source_snapshot(self):
        self.stage_data["snapshot_sha256"] = "0" * 64
        self.save()
        self.assertEqual(self.invoke()[0], 2)

    def test_receipt_requires_independent_historical_row_parity(self):
        self.stage_data["tables"]["jobs"]["target_row_sha256"] = "0" * 64
        self.save()
        self.assertEqual(self.invoke()[0], 2)

    def test_table_census_cannot_drop_a_consumer(self):
        self.stage_data["tables"].pop("artifacts")
        self.save()
        self.assertEqual(self.invoke()[0], 2)

    def test_untrusted_table_name_never_reaches_sql_identifier(self):
        self.stage_data["tables"]["jobs; DROP TABLE jobs"] = self.stage_data["tables"].pop("jobs")
        self.snapshot_data["rowCounts"]["jobs; DROP TABLE jobs"] = self.snapshot_data["rowCounts"].pop("jobs")
        self.save()
        self.assertEqual(self.invoke()[0], 2)
        db = sqlite3.connect(self.source)
        self.assertEqual(db.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)
        db.close()

    def test_wrong_source_is_not_qualified_by_old_manifest(self):
        second = self.root / "other.sqlite3"
        second.write_bytes(self.source.read_bytes())
        self.source = second
        self.assertEqual(self.invoke()[0], 2)


if __name__ == "__main__":
    unittest.main()
