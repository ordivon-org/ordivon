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
    host_postgres_only_sources,
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

    def test_git_index_symlink_cannot_be_masked_by_local_regular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            outside = root / "external.sql"
            outside.write_text("SELECT 1;", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            tracked = repo / "query.sql"
            tracked.symlink_to(outside)
            subprocess.run(["git", "-C", str(repo), "add", "query.sql"], check=True)
            tracked.unlink()
            tracked.write_text("SELECT 1;", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "symlink|index"):
                tracked_sql(repo)

    def test_git_tracked_sql_parent_symlink_inside_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            (repo / "queries").mkdir(parents=True)
            (repo / "queries" / "sample.sql").write_text("SELECT 1;", encoding="utf-8")
            (repo / "other").mkdir()
            (repo / "other" / "sample.sql").write_text("SELECT 2;", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "queries/sample.sql"], check=True)
            (repo / "queries" / "sample.sql").unlink()
            (repo / "queries").rmdir()
            (repo / "queries").symlink_to(repo / "other", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                tracked_sql(repo)

    def test_host_postgres_authority_rejects_new_embedded_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "services/host/src/ordivon_host_v2"
            host.mkdir(parents=True)
            (root / "services/host/migrations").mkdir(parents=True)
            (host / "social_store.py").write_text(
                "import psycopg\npsycopg.connect('postgresql://example')\n",
                encoding="utf-8",
            )
            self.assertEqual(host_postgres_only_sources(root), [])
            for source in (
                "import sqlite3 as pg\n",
                "__import__('sqlite3')\n",
                "from importlib import import_module\nimport_module('aiosqlite')\n",
                "from sqlite3 import connect\n",
                "import aiosqlite\n",
                "dsn = 'sqlite:///tmp/host.db'\n",
                "from sqlalchemy.dialects import sqlite\n",
            ):
                (host / "rogue.py").write_text(source, encoding="utf-8")
                with self.subTest(source=source):
                    issues = host_postgres_only_sources(root)
                    self.assertEqual(len(issues), 1, issues)
                    self.assertIn("rogue.py", issues[0])

    def test_host_postgres_authority_rejects_vacuous_empty_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "services/host/src").mkdir(parents=True)
            (root / "services/host/migrations").mkdir(parents=True)
            self.assertTrue(host_postgres_only_sources(root))

    def test_host_postgres_authority_rejects_symlinked_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host = root / "services/host/src/ordivon_host_v2"
            host.mkdir(parents=True)
            outside = root / "external.py"
            outside.write_text("import sqlite3\n", encoding="utf-8")
            (host / "rogue.py").symlink_to(outside)
            self.assertTrue(
                any("rogue.py" in issue for issue in host_postgres_only_sources(root))
            )

    def test_unknown_sql_is_not_certified(self):
        for name in ("domains/game/later.sql", "services/runtime/crates/ordivon-runtime-core/src/runtime/bad.sql"):
            with self.subTest(name=name):
                self.assertIsNone(classify(name))


if __name__ == "__main__":
    unittest.main()
