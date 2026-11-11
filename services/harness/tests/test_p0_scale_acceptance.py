from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

from tests.pg_test_support import isolated_harness_schema

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

    def test_schema_cleanup_on_failing_scale_bound(self) -> None:
        import psycopg

        with isolated_harness_schema() as (dsn, _schema):
            def scale_schemas() -> set[str]:
                with psycopg.connect(dsn) as connection:
                    return {
                        str(row[0])
                        for row in connection.execute(
                            "SELECT nspname FROM pg_namespace "
                            "WHERE nspname LIKE 'hpg\\_scale\\_%' ESCAPE '\\'"
                        )
                    }

            before = scale_schemas()
            receipt = MODULE.run_acceptance(
                dsn=dsn,
                run_count=1,
                events_per_run=2,
                batch_size=1,
                inspect_samples=1,
                max_write_ms=0,
                max_reopen_ms=30_000,
                max_inspect_p95_ms=1_000,
            )
            self.assertFalse(receipt["passed"])
            self.assertFalse(receipt["checks"]["writeWithinBound"])
            self.assertEqual(scale_schemas(), before)

    def test_missing_database_authority_fails_before_creating_schema(self) -> None:
        with self.assertRaisesRegex(ValueError, "HARNESS_PG_TEST_DSN"):
            MODULE.run_acceptance(
                dsn="", run_count=1, events_per_run=2, batch_size=1,
                inspect_samples=1, max_write_ms=30_000,
                max_reopen_ms=30_000, max_inspect_p95_ms=1_000,
            )

    def test_small_scale_receipt_is_exact_and_healthy(self) -> None:
        with isolated_harness_schema() as (dsn, _schema):
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
        self.assertEqual(receipt["kind"], "ordivon.harness-pg-scale-acceptance")
        self.assertTrue(all(receipt["checks"].values()))
        self.assertTrue(
            receipt["integrity"]["payloadDigest"].startswith("sha256:")
        )


if __name__ == "__main__":
    unittest.main()
