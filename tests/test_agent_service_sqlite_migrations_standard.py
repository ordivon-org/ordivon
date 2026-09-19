from __future__ import annotations

import ast
import sqlite3
import tempfile
import tomllib
import unittest
from pathlib import Path


DOMAIN_SCHEMA_MODULES = (
    "slice1",
    "task_runtime",
    "evidence",
    "goals",
    "semantics",
    "delivery",
    "trust",
    "remote_evidence",
    "failover",
    "transport_credentials",
    "effect_authority",
)


class SqliteMigrationsStandardTests(unittest.TestCase):
    def test_runtime_lock_resolves_expected_sqlite_utils_release(self) -> None:
        lock = tomllib.loads(Path("uv.lock").read_text(encoding="utf-8"))
        versions = {
            package["name"]: package["version"]
            for package in lock["package"]
            if "version" in package
        }
        self.assertEqual(versions["sqlite-utils"], "4.2.1")

    def test_domain_modules_no_longer_own_schema_initializers(self) -> None:
        offenders = []
        for module in DOMAIN_SCHEMA_MODULES:
            path = Path("agent_service") / f"{module}.py"
            tree = ast.parse(path.read_text())
            if any(
                isinstance(node, ast.FunctionDef) and node.name == "_initialize_schema"
                for node in tree.body
            ):
                offenders.append(module)
        self.assertEqual(offenders, [])

    def test_fresh_database_has_migration_ledger_and_current_schema(self) -> None:
        from agent_service.schema_migrations import apply_schema_migrations

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "service.db"
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            apply_schema_migrations(connection)
            names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertIn("_sqlite_migrations", names)
            self.assertTrue(
                {
                    "agent_definitions",
                    "agent_revisions",
                    "agent_instances",
                    "service_tasks",
                    "transport_bindings",
                    "execution_quiescence_requests",
                }.issubset(names)
            )
            applied = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM _sqlite_migrations "
                    "WHERE migration_set='agent-service' ORDER BY id"
                )
            ]
            self.assertEqual(
                applied,
                [
                    "001_current_schema",
                    "002_request_identity",
                    "003_transport_protocol_version",
                ],
            )
            connection.close()

    def test_birth_request_identity_is_migrated_transactionally(self) -> None:
        from agent_service.schema_migrations import apply_schema_migrations

        with tempfile.TemporaryDirectory() as td:
            connection = sqlite3.connect(Path(td) / "service.db")
            connection.row_factory = sqlite3.Row
            connection.executescript(
                """
                CREATE TABLE agent_definitions (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at_ns INTEGER NOT NULL
                );
                CREATE TABLE agent_revisions (
                    id TEXT PRIMARY KEY,
                    definition_id TEXT NOT NULL REFERENCES agent_definitions(id),
                    spec_json TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL
                );
                CREATE TABLE agent_instances (
                    id TEXT PRIMARY KEY,
                    birth_request_id TEXT NOT NULL UNIQUE,
                    revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
                    state TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL
                );
                INSERT INTO agent_definitions VALUES ('d1','x',1);
                INSERT INTO agent_revisions VALUES ('r1','d1','{}',1);
                INSERT INTO agent_instances VALUES ('i1','legacy:req','r1','READY',1);
                """
            )
            apply_schema_migrations(connection)
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(agent_instances)")
            }
            self.assertNotIn("birth_request_id", columns)
            self.assertIn("client_request_id", columns)
            self.assertEqual(
                connection.execute(
                    "SELECT client_request_id FROM agent_instances WHERE id='i1'"
                ).fetchone()[0],
                "legacy:req",
            )
            connection.close()

    def test_transport_protocol_version_is_adopted_without_rewrite(self) -> None:
        from agent_service.schema_migrations import apply_schema_migrations

        with tempfile.TemporaryDirectory() as td:
            connection = sqlite3.connect(Path(td) / "service.db")
            connection.row_factory = sqlite3.Row
            connection.execute(
                """
                CREATE TABLE transport_bindings (
                    id TEXT PRIMARY KEY,
                    delegation_id TEXT NOT NULL,
                    policy_receipt_id TEXT NOT NULL,
                    policy_revision TEXT NOT NULL,
                    granted_permissions_json TEXT NOT NULL,
                    interface_id TEXT NOT NULL,
                    transport TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    delivery_request_id TEXT NOT NULL UNIQUE,
                    security_requirements_json TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL,
                    UNIQUE(delegation_id, policy_receipt_id, interface_id)
                )
                """
            )
            apply_schema_migrations(connection)
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(transport_bindings)")
            }
            self.assertIn("protocol_version", columns)
            connection.close()

    def test_known_legacy_schema_fails_before_migration_ledger_is_created(self) -> None:
        from agent_service.schema_migrations import apply_schema_migrations

        with tempfile.TemporaryDirectory() as td:
            connection = sqlite3.connect(Path(td) / "service.db")
            connection.execute("CREATE TABLE task_verifications (id TEXT PRIMARY KEY)")
            with self.assertRaisesRegex(RuntimeError, "legacy task_verifications"):
                apply_schema_migrations(connection)
            names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertNotIn("_sqlite_migrations", names)
            connection.close()


if __name__ == "__main__":
    unittest.main()


class SqliteMigrationBehaviorTests(unittest.TestCase):
    def test_repeated_apply_is_idempotent_and_does_not_duplicate_ledger(self) -> None:
        from agent_service.schema_migrations import apply_schema_migrations

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "service.db"
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            apply_schema_migrations(connection)
            connection.execute(
                "INSERT INTO agent_definitions(id,name,created_at_ns) VALUES ('d1','persist',1)"
            )
            connection.commit()
            apply_schema_migrations(connection)
            self.assertEqual(
                connection.execute(
                    "SELECT name FROM agent_definitions WHERE id='d1'"
                ).fetchone()[0],
                "persist",
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM _sqlite_migrations "
                    "WHERE migration_set='agent-service'"
                ).fetchone()[0],
                3,
            )
            connection.close()

    def test_fresh_business_schema_matches_frozen_pre_migration_contract(self) -> None:
        from agent_service.schema_migrations import CURRENT_TABLE_DDL, apply_schema_migrations

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "service.db"
            connection = sqlite3.connect(path)
            apply_schema_migrations(connection)

            actual = {
                row[0]: " ".join(row[1].split())
                for row in connection.execute(
                    "SELECT name, sql FROM sqlite_master "
                    "WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' "
                    "AND name <> '_sqlite_migrations'"
                )
            }

            expected_connection = sqlite3.connect(":memory:")
            for ddl in CURRENT_TABLE_DDL:
                expected_connection.execute(ddl)
            expected = {
                row[0]: " ".join(row[1].split())
                for row in expected_connection.execute(
                    "SELECT name, sql FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }

            self.assertEqual(actual, expected)
            expected_connection.close()
            connection.close()
