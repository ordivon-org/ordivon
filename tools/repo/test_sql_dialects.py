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
    sqlite_direct_calls,
    sqlite_debt_issues,
    tracked_owner_sqlite_calls,
    SQLITE_LEGACY_SOURCE_CALLS,
    ROOT,
    host_postgres_only_sources,
)


class SQLDialectBoundaryTests(unittest.TestCase):
    def test_pg_preferred_sourcecut_matches_existing_core_sqlite_debt(self):
        current = tracked_owner_sqlite_calls(ROOT)
        self.assertEqual(current, SQLITE_LEGACY_SOURCE_CALLS)
        self.assertFalse(sqlite_debt_issues(current))
        self.assertGreater(len(current), 10)

    def test_legacy_debt_includes_unfenced_domain_gateway_and_workstation_owners(self):
        current = tracked_owner_sqlite_calls(ROOT)
        # Each is a real tracked and currently differently qualified consumer.
        for name in (
            "services/gateway/src/ordivon_gateway/external_worker.py",
            "domains/capital/src/ordivon_capital/accounting/sqlite_ledger.py",
            "capabilities/media/src/ordivon_studio/research_validity.py",
            "platform/workstation/scripts/host_historical_projection.py",
            "platform/workstation/scripts/host_retirement_snapshot.py",
            "meta/next/experiments/browser-security-r4/cf07_metadata_snapshot.py",
            "meta/next/experiments/chaoxing-autosign-mvp/chaoxing_mvp/ledger.py",
        ):
            with self.subTest(path=name):
                self.assertIn(name, current)

    def test_new_sqlite_owner_outside_old_runtime_harness_scope_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extra = root / "services/gateway/src/ordivon_gateway/unaudited.py"
            extra.parent.mkdir(parents=True)
            extra.write_text(
                "import sqlite3\nconn = sqlite3.connect('unreviewed.db')\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            observed = tracked_owner_sqlite_calls(root)
            self.assertEqual(observed, {"services/gateway/src/ordivon_gateway/unaudited.py": 1})
            self.assertTrue(sqlite_debt_issues(observed, {}))

    def test_pg_first_debt_accounts_for_typescript_runtime_store_owners(self):
        observed = tracked_owner_sqlite_calls(ROOT)
        for path in (
            "apps/web/src/store.ts",
            "domains/game/experiments/casefile/src/store.ts",
            "domains/game/experiments/game-e2e-r5/host-outbox-shadow.ts",
            "domains/game/experiments/station-zero-v3/src/persistence.ts",
            "domains/game/products/station-zero-v2/src/storage.ts",
            "platform/security/labs/agent-admission-rs/src/grant-store.ts",
            "platform/security/labs/agent-admission-rs/src/principal-store.ts",
        ):
            with self.subTest(path=path):
                self.assertEqual(observed[path], 1)

    def test_ts_node_sqlite_lexical_import_nonvacuity_and_type_only_exclusion(self):
        src = 'import { DatabaseSync } from "node:sqlite";\n'
        self.assertEqual(sqlite_direct_calls("apps/web/src/store.ts", src), 1)
        self.assertEqual(
            sqlite_direct_calls("apps/web/src/stub.ts", 'import type { DatabaseSync } from "node:sqlite";\n'),
            0,
        )
        self.assertEqual(
            sqlite_direct_calls("apps/web/src/nope.ts", '// import { DatabaseSync } from "node:sqlite";\n'),
            0,
        )
        self.assertEqual(
            sqlite_direct_calls("apps/web/src/import.mjs", 'const mod = require("node:sqlite");\n'),
            1,
        )
        self.assertEqual(
            sqlite_direct_calls("apps/web/src/pg.ts", 'import { Client } from "pg";\n'),
            0,
        )

    def test_ts_unfenced_sqlite_store_enters_existing_debt_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "apps/web/src/new-ledger.ts"
            source.parent.mkdir(parents=True)
            source.write_text('import { DatabaseSync } from "node:sqlite";\n', encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            actual = tracked_owner_sqlite_calls(root)
            self.assertEqual(actual, {"apps/web/src/new-ledger.ts": 1})
            self.assertTrue(sqlite_debt_issues(actual, {}))

    def test_new_core_sqlite_authority_requires_explicit_consumer_qualification(self):
        current = dict(SQLITE_LEGACY_SOURCE_CALLS)
        current["services/harness/src/unreviewed_sqlite_authority.py"] = 1
        issues = sqlite_debt_issues(current)
        self.assertEqual(len(issues), 1)
        self.assertIn("unreviewed_sqlite_authority", issues[0])

    def test_existing_sqlite_authority_growth_cannot_hide_in_old_file(self):
        current = dict(SQLITE_LEGACY_SOURCE_CALLS)
        name = next(iter(current))
        current[name] += 1
        self.assertEqual(len(sqlite_debt_issues(current)), 1)

    def test_backend_retirement_requires_explicit_sourcebound_debt_update(self):
        current = dict(SQLITE_LEGACY_SOURCE_CALLS)
        current.pop(next(iter(current)))
        self.assertEqual(len(sqlite_debt_issues(current)), 1)

    def test_core_sqlite_writer_detection_does_not_classify_pg(self):
        self.assertEqual(
            sqlite_direct_calls("services/harness/store.py", "sqlite3.connect(path)"),
            1,
        )
        self.assertEqual(
            sqlite_direct_calls("services/runtime/storage.rs", "rusqlite::Connection"),
            1,
        )
        self.assertEqual(
            sqlite_direct_calls("services/harness/pg.py", "psycopg.connect(dsn)"),
            0,
        )

    def test_py_sqlite_alias_and_direct_import_cannot_bypass_source_fence(self):
        self.assertEqual(
            sqlite_direct_calls(
                "services/runtime/alias.py",
                "import sqlite3 as sql\nsql.connect('/tmp/ledger.db')\n",
            ),
            1,
        )
        self.assertEqual(
            sqlite_direct_calls(
                "services/harness/alias.py",
                "from sqlite3 import connect as open_db\nopen_db('ledger.db')\n",
            ),
            1,
        )

    def test_python_sqlite_comments_do_not_create_false_backend_calls(self):
        self.assertEqual(
            sqlite_direct_calls(
                "services/harness/no_db.py",
                "# sqlite3.connect('/ignored')\nimport psycopg\npsycopg.connect(dsn)\n",
            ),
            0,
        )

    def test_core_sqlite_source_symlink_replacement_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            target = repo / "services/runtime/rogue.py"
            target.parent.mkdir(parents=True)
            target.write_text("import sqlite3\nsqlite3.connect('fake')\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            outside = root / "outside.py"
            outside.write_text("import sqlite3\nsqlite3.connect('other')\n", encoding="utf-8")
            target.unlink()
            target.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "symlink"):
                tracked_owner_sqlite_calls(repo)

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
