"""Negative controls for bounded, non-mutating selective PostgreSQL import."""
from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "pg_retention_census.py"
spec = importlib.util.spec_from_file_location("pg_retention_census", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RetentionCensusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "runtime#physical?source%.sqlite"
        with closing(sqlite3.connect(self.path)) as c, c:
            c.executescript("""
                CREATE TABLE jobs(job_id TEXT PRIMARY KEY,resolution TEXT);
                CREATE TABLE attempts(
                    attempt_id TEXT PRIMARY KEY,job_id TEXT,state TEXT,recovery_required INTEGER
                );
                CREATE TABLE concurrency_reservations(
                    reservation_id TEXT PRIMARY KEY,attempt_id TEXT,state TEXT
                );
                CREATE TABLE idempotency_keys(key TEXT PRIMARY KEY,job_id TEXT);
                CREATE TABLE job_events(event_id TEXT PRIMARY KEY,job_id TEXT);
                CREATE TABLE artifacts(artifact_id TEXT PRIMARY KEY,job_id TEXT);
                CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY);
                CREATE TABLE attempt_supervisor_owners(attempt_id TEXT);
                CREATE TABLE job_execution_providers(job_id TEXT);
                CREATE TABLE job_host_dependencies(job_id TEXT);
                CREATE TABLE job_runtime_release_effects(job_id TEXT);
                INSERT INTO schema_migrations VALUES (1);
                INSERT INTO jobs VALUES ('active',NULL),('done','succeeded');
                INSERT INTO attempts VALUES ('a1','active','running',0),
                                          ('a2','done','succeeded',0);
                INSERT INTO concurrency_reservations VALUES ('r1','a1','active'),
                                                            ('r2','a2','released');
                INSERT INTO idempotency_keys VALUES ('k1','done'),('k2','active');
                INSERT INTO job_events VALUES ('e1','done');
                INSERT INTO artifacts VALUES ('ar1','done');
            """)

    def test_active_and_completed_cohorts_are_distinct(self) -> None:
        r = mod.census(self.path)
        self.assertEqual(r["requiredOperationalClosure"]["distinctJobsRequiringLiveRecovery"], 1)
        self.assertEqual(r["historicalReview"]["terminalJobs"], 1)
        self.assertEqual(r["historicalReview"]["idempotencyKeys"], 2)
        self.assertFalse(r["physicalPgCutoverQualified"])
        self.assertEqual(r["admission"], "STOP_UNTIL_CONSUMER_AND_PG_PHYSICAL_PARITY_PROVEN")

    def test_terminal_job_with_held_reservation_is_still_live(self) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE concurrency_reservations SET state='held_orphaned' "
                       "WHERE attempt_id='a2'")
        r = mod.census(self.path)
        self.assertEqual(
            r["requiredOperationalClosure"]["distinctJobsRequiringLiveRecovery"], 2
        )
        self.assertEqual(r["historicalReview"]["terminalJobs"], 1)

    def test_recovery_required_terminal_job_is_still_live(self) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE attempts SET recovery_required=1 WHERE attempt_id='a2'")
        r = mod.census(self.path)
        self.assertEqual(
            r["requiredOperationalClosure"]["distinctJobsRequiringLiveRecovery"], 2
        )

    def test_literal_uri_special_characters_not_aliased(self) -> None:
        r = mod.census(self.path)
        self.assertEqual(r["recordCounts"]["jobs"], 2)

    def test_source_is_not_mutated(self) -> None:
        before = self.path.read_bytes()
        mod.census(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_schema_fails_closed(self) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DROP TABLE idempotency_keys")
        with self.assertRaisesRegex(mod.SourceUnqualified, "idempotency_keys"):
            mod.census(self.path)

    def test_unclassified_new_table_fails_closed(self) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE orphan_future_store(data TEXT)")
        with self.assertRaisesRegex(mod.SourceUnqualified, "unclassified Registry tables"):
            mod.census(self.path)

    def test_orphan_attempt_fails_closed(self) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO attempts VALUES ('bad','absent','running',0)")
        with self.assertRaisesRegex(mod.SourceUnqualified, "missing parent Jobs"):
            mod.census(self.path)

    def test_unknown_database_does_not_create_empty_source(self) -> None:
        missing = Path(self.tmp.name) / "missing.db"
        with self.assertRaises(mod.SourceUnqualified):
            mod.census(missing)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
