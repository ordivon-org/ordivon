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

from ordivon_harness.cli import build_parser, main
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from tests.test_p0_core_contracts import contract as store_contract
from tests.test_p0_sqlite_agent_loop import needs_input_result, contract


@unittest.skipUnless(os.environ.get("HARNESS_PG_TEST_DSN"), "real PG DSN needed")
class PgOnlyHarnessCli(unittest.TestCase):
    def setUp(self) -> None:
        self.dsn = os.environ["HARNESS_PG_TEST_DSN"]
        self.schema = "hpg_cli_" + uuid.uuid4().hex[:18]
        self.env = patch.dict(
            os.environ,
            {
                "HARNESS_PG_DSN": self.dsn,
                "HARNESS_PG_SCHEMA": self.schema,
            },
        )
        self.env.start()
        with PostgresHarnessStore(self.dsn, schema=self.schema, initialize=True):
            pass

    def tearDown(self) -> None:
        self.env.stop()
        with psycopg.connect(self.dsn, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(self.schema))
            )

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
            run = store_contract()
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

    def test_removed_sqlite_cli_surface_and_missing_pg_fail_closed(self) -> None:
        parser = build_parser()
        for argv in (
            ["store-backup", "/tmp/harness-retired-backup"],
            ["--state-root", "/tmp/old-harness", "store-init"],
        ):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parser.parse_args(argv)
        with patch.dict(os.environ, {"HARNESS_PG_DSN": ""}):
            code, _, error = self.invoke("store-init")
        self.assertEqual(code, 1)
        self.assertIn("HARNESS_PG_DSN required", error)

    def test_run_with_real_pg_store_and_scripted_pause(self) -> None:
        run = contract("pg-only-cli-run")
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            contract_path.write_text(json.dumps(run.to_dict()), encoding="utf-8")
            with patch(
                "ordivon_harness.independent_cli._adapter",
                return_value=ScriptedTurnAdapter((needs_input_result("pg-only-pause"),)),
            ):
                code, result, error = self.invoke(
                    "run", str(contract_path), "--message", "new pg run"
                )
            self.assertEqual(code, 0, error)
            self.assertEqual(result["storageBackend"], "postgresql")
            self.assertEqual(result["run"]["status"], "paused")
            code, status, error = self.invoke("status", run.harness_run_id)
            self.assertEqual(code, 0, error)
            self.assertEqual(status["run"]["status"], "paused")

    @unittest.skipUnless(
        os.environ.get("HARNESS_REAL_PROVIDER_TEST") == "1",
        "explicit, potentially billable, live Provider acceptance only",
    )
    def test_live_deepseek_cli_run_persists_to_pg_across_processes(self) -> None:
        """Actual Provider HTTP + original PG Journal + three separate public CLI calls.

        Run only on an explicitly enabled test node. The existing per-test PG
        schema setup/teardown owns isolation; no additional store or schema API.
        """
        import subprocess
        import sys
        from dataclasses import replace

        from ordivon_harness.core_contracts import HarnessPrivacyPolicy
        from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter

        settings = DeepSeekSettings.from_secret_file()
        run = replace(
            contract("pg-live-deepseek-" + uuid.uuid4().hex[:12]),
            provider_id="provider:deepseek",
            adapter_id=DeepSeekTurnAdapter.adapter_id,
            requested_model_id=settings.model,
            budget={
                "maxModelCalls": 1,
                "maxToolCalls": 0,
                "maxWallTimeMs": 120_000,
                "maxTotalTokens": 16_384,
                "maxObservationBytes": 8_192,
                "maxModelRetries": 0,
                "maxToolCorrections": 0,
                "maxConclusionCorrections": 0,
                "maxObservationOnlyTurns": 2,
                "maxNoProgressTurns": 2,
            },
            privacy=HarnessPrivacyPolicy(
                content_policy="bounded-private-content",
                allow_model_content=True,
                allow_tool_content=False,
            ),
        )

        def cli(*arguments: str) -> dict[str, object]:
            result = subprocess.run(
                [sys.executable, "-m", "ordivon_harness.cli", *arguments],
                check=False,
                capture_output=True,
                text=True,
                timeout=160,
            )
            self.assertEqual(result.returncode, 0, result.stderr[-1_500:])
            value = json.loads(result.stdout)
            self.assertTrue(value["ok"])
            return value

        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            contract_path.write_text(json.dumps(run.to_dict()), encoding="utf-8")
            completed = cli(
                "run",
                str(contract_path),
                "--message",
                "通过结论动作结束真实测试，简短总结：Ordivon 模型执行链路已响应。不要调用工具。",
            )
            status = cli("status", run.harness_run_id)
            inspected = cli("inspect", run.harness_run_id)

        self.assertEqual(completed["stopCode"], "candidate_completed")
        self.assertEqual(completed["run"]["status"], "completed")
        self.assertEqual(status["run"]["status"], "completed")
        self.assertEqual(inspected["run"]["status"], "completed")
        self.assertIsNotNone(inspected["runReceipt"])
        self.assertIsNotNone(inspected["completionProposal"])

        with PostgresHarnessStore(self.dsn, schema=self.schema) as store:
            events = store.list_run_events(run.harness_run_id)
        kinds = [item.event_kind for item in events]
        self.assertIn("harness.run-created", kinds)
        self.assertIn("harness.provider-call-claimed", kinds)
        self.assertIn("harness.provider-call-dispatching", kinds)
        self.assertIn("harness.provider-call-completed", kinds)
        self.assertIn("harness.run-completed", kinds)
