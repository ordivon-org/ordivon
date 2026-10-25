"""Native PostgreSQL stage proof, including non-promotability and tampered source."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from postgres_registry_stage import migrate, row_digest_update

try:
    import psycopg
except ModuleNotFoundError:
    psycopg = None


class PgStagePureLawTests(unittest.TestCase):
    def test_digest_distinguishes_binary_text_null_and_number(self) -> None:
        observed = []
        for row in ((None,), ("",), (b"",), (0,), ("0",), (b"0",)):
            h = hashlib.sha256()
            row_digest_update(h, row)
            observed.append(h.hexdigest())
        self.assertEqual(len(set(observed)), len(observed))

    def test_nonstage_namespace_rejected_without_pg_client(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid/non-stage"):
            migrate(Path("/nonexistent"), Path("/nonexistent"), "", "public")


class PgStageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dsn = os.environ.get("ORDIVON_RW12_STAGE_TEST_DSN")
        if not self.dsn:
            self.skipTest("disposable native PostgreSQL test DSN is required")
        if psycopg is None:
            self.fail("native PostgreSQL tests require psycopg: use uv run --with psycopg[binary]")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source = root / "source.sqlite3"
        self.receipt = root / "snapshot.json"
        with sqlite3.connect(self.source) as db:
            db.executescript("""
                PRAGMA foreign_keys=ON;
                CREATE TABLE jobs (job_id TEXT PRIMARY KEY NOT NULL,
                    operation_digest TEXT NOT NULL);
                CREATE TABLE attempts (
                    attempt_id TEXT PRIMARY KEY NOT NULL,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE RESTRICT,
                    payload BLOB
                );
                CREATE TABLE idempotency_keys (
                    principal TEXT NOT NULL,
                    client_request_id TEXT NOT NULL,
                    job_id TEXT NOT NULL UNIQUE REFERENCES jobs(job_id),
                    PRIMARY KEY (principal,client_request_id)
                );
            """)
            db.execute("INSERT INTO jobs VALUES('j1','sha256:ABC')")
            db.execute("INSERT INTO attempts VALUES('a1','j1',?)", (b"\x00\x01\xff",))
            db.execute("INSERT INTO idempotency_keys VALUES('agent','request','j1')")
        db.close()
        with self.source.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        self.manifest = {
            "kind": "ordivon-rw12-source-snapshot",
            "complete": True,
            "snapshotBytes": self.source.stat().st_size,
            "sha256": digest,
            "rowCounts": {"jobs": 1, "attempts": 1, "idempotency_keys": 1},
        }
        self.receipt.write_text(json.dumps(self.manifest), encoding="utf8")

    def test_stage_exact_content_and_nonpromotion_constraint(self) -> None:
        actual = migrate(self.source, self.receipt, self.dsn, "rw12_stage_native_accept")
        self.assertEqual(actual["row_total"], 3)
        self.assertFalse(actual["promotion_allowed"])
        with psycopg.connect(self.dsn, autocommit=True) as pg:
            self.assertEqual(
                pg.execute("SELECT payload FROM rw12_stage_native_accept.attempts WHERE attempt_id='a1'").fetchone()[0],
                b"\x00\x01\xff",
            )
            self.assertEqual(
                pg.execute("SELECT state FROM rw12_stage_native_accept._stage_control").fetchone()[0],
                "VERIFIED_NON_AUTHORITY",
            )
            with self.assertRaises(psycopg.errors.CheckViolation):
                pg.execute("UPDATE rw12_stage_native_accept._stage_control SET promotion_allowed=TRUE")
            with self.assertRaises(psycopg.errors.ForeignKeyViolation):
                pg.execute("INSERT INTO rw12_stage_native_accept.attempts VALUES ('a-invalid','missing-job',NULL)")
            with self.assertRaises(psycopg.errors.UniqueViolation):
                pg.execute("INSERT INTO rw12_stage_native_accept.idempotency_keys VALUES ('agent','request','j1')")

    def test_changed_source_fails_before_target_mutation(self) -> None:
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE jobs SET operation_digest='forged' WHERE job_id='j1'")
        db.close()
        with self.assertRaisesRegex(ValueError, "snapshot digest"):
            migrate(self.source, self.receipt, self.dsn, "rw12_stage_forged")

    def test_nonstage_schema_cannot_be_authorized(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid/non-stage"):
            migrate(self.source, self.receipt, self.dsn, "public")


if __name__ == "__main__":
    unittest.main()
