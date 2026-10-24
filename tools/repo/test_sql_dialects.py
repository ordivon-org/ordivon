"""Deliberate counterexamples to the SQL source/dialect gate."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.repo.check_sql_dialects import (
    OSQUERY_DEFAULT_TIMEOUT_SECONDS,
    OSQUERY_TIMEOUT_SECONDS,
    classify,
    tracked_sql,
)


class SQLDialectBoundaryTests(unittest.TestCase):
    def test_known_sql_are_classified(self):
        self.assertEqual(classify("services/runtime/crates/ordivon-runtime-core/migrations/runtime/0001_runtime.sql"), "sqlite")
        self.assertEqual(classify("services/runtime/crates/ordivon-runtime-core/src/runtime/attempt_supervisor_owner_storage.sql"), "sqlite")
        self.assertEqual(classify("platform/workstation/inventory/queries/uptime.sql"), "osquery")
        self.assertEqual(classify("meta/next/scripts/experimental_episode_r5c_source_r1.sql"), "postgresql")

    def test_full_host_package_queries_are_bounded_and_not_downgraded(self):
        self.assertEqual(OSQUERY_TIMEOUT_SECONDS["python_packages.sql"], 120)
        self.assertEqual(OSQUERY_TIMEOUT_SECONDS["npm_packages.sql"], 120)
        self.assertEqual(OSQUERY_DEFAULT_TIMEOUT_SECONDS, 30)
        self.assertLessEqual(max(OSQUERY_TIMEOUT_SECONDS.values()), 120)

    def test_tracked_sql_symlink_cannot_certify_external_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "external-query"
            outside.write_text("SELECT 1;", encoding="utf-8")
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "query.sql").symlink_to(outside)
            subprocess.run(["git", "-C", str(repo), "add", "query.sql"], check=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                tracked_sql(repo)

    def test_tracked_sql_rejects_parent_directory_symlink_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            (repo / "queries").mkdir(parents=True)
            (repo / "queries" / "sample.sql").write_text("SELECT 1;", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "queries/sample.sql"], check=True)
            self.assertEqual(tracked_sql(repo), ["queries/sample.sql"])

            (repo / "queries" / "sample.sql").unlink()
            (repo / "queries").rmdir()
            outside = root / "elsewhere"
            outside.mkdir()
            (outside / "sample.sql").write_text("SELECT 2;", encoding="utf-8")
            (repo / "queries").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "external source"):
                tracked_sql(repo)

    def test_unknown_sql_is_not_certified(self):
        for name in ("domains/game/later.sql", "services/runtime/crates/ordivon-runtime-core/src/runtime/bad.sql"):
            with self.subTest(name=name):
                self.assertIsNone(classify(name))


if __name__ == "__main__":
    unittest.main()
