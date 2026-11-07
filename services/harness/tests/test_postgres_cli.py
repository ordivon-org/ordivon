"""Real independent Harness CLI on PostgreSQL, without SQLite migration."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch

import psycopg
from psycopg import sql

from ordivon_harness.cli import main
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from tests.test_p0_sqlite_store import run_contract
from tests.test_p0_sqlite_agent_loop import needs_input_result, contract


@unittest.skipUnless(os.environ.get("HARNESS_PG_TEST_DSN"), "real PG DSN needed")
class PgOnlyHarnessCli(unittest.TestCase):
    def setUp(self) -> None:
        self.dsn = os.environ["HARNESS_PG_TEST_DSN"]
        self.schema = "hpg_cli_" + uuid.uuid4().hex[:18]
        self.env = patch.dict(os.environ, {
            "HARNESS_PG_DSN": self.dsn,
            "HARNESS_PG_SCHEMA": self.schema,
        })
        self.env.start()
        with PostgresHarnessStore(self.dsn, schema=self.schema, initialize=True):
            pass

    def tearDown(self) -> None:
        self.env.stop()
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(self.schema)))

    @staticmethod
    def invoke(*args: str):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(args)
        return code, json.loads(stdout.getvalue()) if stdout.getvalue() else None, stderr.getvalue()

    def test_pg_store_cli_real_create_inspect_events_and_no_sqlite_paths(self) -> None:
        code, result, error = self.invoke("store-init")
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(result["storageBackend"], "postgresql")
        self.assertTrue(result["store"]["healthy"])
        with PostgresHarnessStore(self.dsn, schema=self.schema) as store:
            run = run_contract()
            store.create_run(run)
        code, result, error = self.invoke("store-inspect", run.harness_run_id)
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(result["run"]["revision"], 1)
        code, result, error = self.invoke("store-events", run.harness_run_id)
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(result["events"][0]["eventKind"], "harness.run-created")
        code, result, error = self.invoke("store-doctor")
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(result["store"]["runs"], 1)

    def test_sqlite_backup_state_root_and_missing_pg_fail_closed(self) -> None:
        code, _, error = self.invoke("store-backup", "/tmp/harness-retired-backup")
        self.assertEqual(code, 1)
        self.assertIn("legacy SQLite backup and restore are retired", error)
        code, _, error = self.invoke("--state-root", "/tmp/old-harness", "store-init")
        self.assertEqual(code, 1)
        self.assertIn("--state-root is retired", error)
        with patch.dict(os.environ, {"HARNESS_PG_DSN": ""}):
            code, _, error = self.invoke("store-init")
        self.assertEqual(code, 1)
        self.assertIn("HARNESS_PG_DSN required", error)

    def test_run_with_real_pg_store_and_scripted_pause(self) -> None:
        run = contract("pg-only-cli-run")
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            contract_path.write_text(json.dumps(run.to_dict()), encoding="utf-8")
            with patch("ordivon_harness.independent_cli._adapter", return_value=ScriptedTurnAdapter((needs_input_result("pg-only-pause"),))):
                code, result, error = self.invoke("run", str(contract_path), "--message", "new pg run")
            self.assertEqual(code, 0, error)
            self.assertEqual(result["storageBackend"], "postgresql")
            self.assertEqual(result["run"]["status"], "paused")
            code, status, error = self.invoke("status", run.harness_run_id)
            self.assertEqual(code, 0, error)
            self.assertEqual(status["run"]["status"], "paused")
