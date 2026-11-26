from __future__ import annotations

import importlib.util
from pathlib import Path
import os
import subprocess
import tempfile
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "harness_p0_scale_acceptance.py"
SPEC = importlib.util.spec_from_file_location("harness_p0_scale_acceptance", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HarnessP0ScaleAcceptanceTests(unittest.TestCase):
    def test_p95_nearest_rank_does_not_hide_one_slow_inspection(self) -> None:
        self.assertEqual(MODULE._percentile([1.0, 2.0, 3.0, 100.0], 0.95), 100.0)
        self.assertEqual(MODULE._percentile([1.0, 2.0, 3.0, 100.0], 0.50), 2.0)

    def test_small_scale_receipt_is_exact_and_healthy(self) -> None:
        dsn = os.environ.get("HARNESS_PG_TEST_DSN")
        if not dsn:
            self.skipTest("dedicated PostgreSQL test database required")
        receipt = MODULE.run_acceptance(
            dsn=dsn,
            run_count=8,
            events_per_run=12,
            batch_size=11,
            inspect_samples=4,
            max_write_ms=30_000,
            max_reopen_ms=30_000,
            max_inspect_p95_ms=1_000,
        )
        self.assertTrue(receipt["passed"])
        self.assertEqual(receipt["counts"]["runs"], 8)
        self.assertEqual(receipt["counts"]["events"], 96)
        self.assertEqual(receipt["configuration"]["storageBackend"], "postgresql")
        self.assertEqual(receipt["counts"]["payload_edges"], 96)
        self.assertEqual(receipt["counts"]["object_edges"], 104)
        self.assertEqual(receipt["counts"]["objects"], 104)
        self.assertEqual(receipt["counts"]["orphan_objects"], 0)
        self.assertEqual(receipt["counts"]["leases"], 0)
        self.assertTrue(all(receipt["checks"].values()))
        self.assertTrue(
            receipt["integrity"]["payloadDigest"].startswith("sha256:")
        )

    def test_receipt_revision_binds_script_source_not_invoking_checkout(self) -> None:
        expected = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory)
            subprocess.run(["git", "init", "-q", str(other)], check=True)
            subprocess.run(
                ["git", "-C", str(other), "-c", "user.name=Test",
                 "-c", "user.email=test@example.invalid", "commit", "--allow-empty",
                 "-qm", "unrelated checkout"], check=True,
            )
            try:
                os.chdir(other)
                self.assertEqual(MODULE._revision(), expected)
            finally:
                os.chdir(original_cwd)

    def test_scale_requires_explicit_test_dsn_not_production_fallback(self) -> None:
        with patch.dict(os.environ, {"HARNESS_PG_TEST_DSN": "", "HARNESS_PG_DSN": "unused"}, clear=True):
            with patch("sys.argv", [str(SCRIPT)]), self.assertRaises(SystemExit) as exc:
                MODULE.main()
            self.assertEqual(exc.exception.code, 2)

    def test_acceptance_schema_collision_never_removes_existing_schema(self) -> None:
        import psycopg
        from psycopg import sql
        from types import SimpleNamespace
        import uuid
        from scripts import harness_acceptance_pg

        dsn = os.environ.get("HARNESS_PG_TEST_DSN")
        if not dsn:
            self.skipTest("dedicated PostgreSQL test database required")
        suffix = uuid.uuid4().hex
        name = "hpg_edit_" + suffix
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
            try:
                connection.execute(sql.SQL("CREATE TABLE {}.sentinel (id integer)").format(sql.Identifier(name)))
                connection.execute(sql.SQL("INSERT INTO {}.sentinel VALUES (42)").format(sql.Identifier(name)))
                with (
                    patch.object(harness_acceptance_pg.uuid, "uuid4", return_value=SimpleNamespace(hex=suffix)),
                    self.assertRaises(psycopg.errors.DuplicateSchema),
                ):
                    with harness_acceptance_pg.isolated_acceptance_schema(dsn, purpose="edit"):
                        self.fail("colliding schema is not owned")
                self.assertEqual(connection.execute(
                    sql.SQL("SELECT id FROM {}.sentinel").format(sql.Identifier(name))
                ).fetchone(), (42,))
            finally:
                connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(name)))

    def test_formal_queue_requires_pg_authority_before_running_tools(self) -> None:
        import tomllib

        queue = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]["queue"]["run"]
        # No executable lookup path: this specifically tests the precondition,
        # not a second invocation of the real queue or external package tools.
        result = subprocess.run(
            ["/usr/bin/bash", "-c", queue],
            cwd=ROOT, env={"PATH": "/nonexistent"}, text=True,
            capture_output=True, timeout=5,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("HARNESS_PG_TEST_DSN", result.stderr)

    def test_existing_agent_run_schema_fixture_never_takes_over_collision(self) -> None:
        import psycopg
        from psycopg import sql
        import uuid
        from tests.pg_test_support import isolated_harness_schema

        dsn = os.environ.get("HARNESS_PG_TEST_DSN")
        if not dsn:
            self.skipTest("dedicated PostgreSQL test database required")
        candidate = uuid.uuid4()
        names = ("hpg_test_" + candidate.hex[:20], "hpg_behavior_" + candidate.hex)
        with psycopg.connect(dsn, autocommit=True) as connection:
            for name in names:
                connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
                connection.execute(sql.SQL("CREATE TABLE {}.sentinel (id integer)").format(sql.Identifier(name)))
                connection.execute(sql.SQL("INSERT INTO {}.sentinel VALUES (42)").format(sql.Identifier(name)))
            try:
                with patch.object(uuid, "uuid4", return_value=candidate):
                    with self.assertRaises(psycopg.errors.DuplicateSchema):
                        with isolated_harness_schema():
                            pass
                for name in names:
                    self.assertEqual(connection.execute(
                        sql.SQL("SELECT id FROM {}.sentinel").format(sql.Identifier(name))
                    ).fetchone(), (42,))
            finally:
                for name in names:
                    connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(name)))

    def test_failed_workload_removes_only_its_fresh_schema(self) -> None:
        import psycopg

        dsn = os.environ.get("HARNESS_PG_TEST_DSN")
        if not dsn:
            self.skipTest("dedicated PostgreSQL test database required")
        with psycopg.connect(dsn, autocommit=True) as connection:
            def schemas():
                return {row[0] for row in connection.execute(
                    "SELECT nspname FROM pg_namespace WHERE nspname LIKE 'hpg_scale_%'"
                )}
            before = schemas()
            with patch.object(MODULE, "_run_scale", side_effect=RuntimeError("injected")):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    MODULE.run_acceptance(
                        dsn=dsn, run_count=1, events_per_run=2, batch_size=1,
                        inspect_samples=1, max_write_ms=1000,
                        max_reopen_ms=1000, max_inspect_p95_ms=1000,
                    )
            self.assertEqual(schemas(), before)


if __name__ == "__main__":
    unittest.main()
