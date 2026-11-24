from __future__ import annotations

import copy
import importlib.util
import os
from dataclasses import replace
from unittest.mock import patch
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_adaptive_edit_r2_live_ab.py"
spec = importlib.util.spec_from_file_location("adaptive_edit_r2_live_ab", SCRIPT)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class AdaptiveEditR2LiveABRunnerTests(unittest.TestCase):
    def test_treatments_expose_exactly_one_codec_schema(self) -> None:
        exact = runner.treatment_edit_definition("exact-replacement-v1")
        anchored = runner.treatment_edit_definition("anchored-line-v1")
        self.assertEqual(
            exact.input_schema["properties"]["codec"]["const"],
            "exact-replacement-v1",
        )
        self.assertIn("oldText", exact.input_schema["properties"])
        self.assertNotIn("startAnchor", exact.input_schema["properties"])
        self.assertEqual(
            anchored.input_schema["properties"]["codec"]["const"],
            "anchored-line-v1",
        )
        self.assertIn("startAnchor", anchored.input_schema["properties"])
        self.assertNotIn("oldText", anchored.input_schema["properties"])

    def test_runner_registers_repeated_target_task(self) -> None:
        task = runner.TASK_SPECS["HARNESS-EDIT-ADDRESSING-002"]
        self.assertEqual(task.target_path, "feature_flags.py")
        self.assertIn("test_feature_flags.py", task.read_paths)
        runtime = runner.MemoryRuntime(task)
        self.assertEqual(
            runtime.files["feature_flags.py"].count("return False"),
            2,
        )
        overfit = (
            runner.ROOT / "evals/harness-edit-addressing-002/known-invalid/both-enabled.py"
        ).read_text()
        outcome = runner.verify(overfit, task)
        self.assertEqual(outcome, {"visiblePassed": True, "hiddenPassed": False})

    def test_runner_registers_multiregion_task(self) -> None:
        task = runner.TASK_SPECS["HARNESS-EDIT-MULTIREGION-003"]
        self.assertEqual(task.target_path, "pipeline.py")
        runtime = runner.MemoryRuntime(task)
        before = runtime.files["pipeline.py"]
        self.assertIn("DEFAULT_TIMEOUT_SECONDS = 15", before)
        self.assertIn("return 1", before)
        oracle = task.oracle.read_text()
        self.assertEqual(
            runner.verify(oracle, task),
            {"visiblePassed": True, "hiddenPassed": True},
        )

    def test_memory_runtime_applies_digest_fenced_runtime_patch_shape(self) -> None:
        runtime = runner.MemoryRuntime()
        before = runtime.files["allocation.py"]
        old = "    return [(total * weight) // weight_total for weight in weights]"
        start = before.index(old)
        prefix = before[:start]
        line = prefix.count("\n") + 1
        column = len(prefix.rsplit("\n", 1)[-1])
        request = {
            "schemaVersion": 1,
            "clientRequestId": "request:test-live-ab-memory-runtime",
            "workspaceId": "ws-live-ab",
            "files": [
                {
                    "relativePath": "allocation.py",
                    "expectedDigest": runner.sha(before),
                    "edits": [
                        {
                            "range": {
                                "start": {"line": line, "column": column},
                                "end": {"line": line, "column": column + len(old)},
                            },
                            "expectedText": old,
                            "replacement": "    return [0 for _ in weights]",
                        }
                    ],
                }
            ],
            "maxDiffBytes": 4096,
        }
        receipt = runtime.call_tool("workspace.patch", request)
        self.assertEqual(receipt["clientRequestId"], request["clientRequestId"])
        self.assertNotEqual(runtime.files["allocation.py"], before)
        self.assertIn("return [0 for _ in weights]", runtime.files["allocation.py"])

    def test_memory_runtime_replay_identity_is_request_content_addressed(self) -> None:
        runtime = runner.MemoryRuntime()
        before = runtime.files["allocation.py"]
        request = {
            "clientRequestId": "request:live-ab-replay-identity",
            "files": [
                {
                    "relativePath": "allocation.py",
                    "expectedDigest": runner.sha(before),
                    "edits": [
                        {
                            "range": {
                                "start": {"line": 1, "column": 0},
                                "end": {"line": 1, "column": 0},
                            },
                            "expectedText": "",
                            "replacement": "# header\\n",
                        }
                    ],
                }
            ],
        }
        first = runtime.call_tool("workspace.patch", request)
        after = runtime.files["allocation.py"]
        self.assertNotEqual(before, after)
        duplicate = runtime.call_tool("workspace.patch", copy.deepcopy(request))
        self.assertEqual(duplicate["requestDigest"], first["requestDigest"])
        self.assertTrue(duplicate["replayed"])

        conflicting = copy.deepcopy(request)
        conflicting["files"][0]["edits"][0]["replacement"] = "# different header\\n"
        with self.assertRaisesRegex(runner.HarnessRuntimeToolRejected, "identity"):
            runtime.call_tool("workspace.patch", conflicting)
        self.assertEqual(runtime.files["allocation.py"], after)
        self.assertEqual(len(runtime.receipts), 1)

    def test_memory_runtime_overlapping_intervals_cannot_commit(self) -> None:
        runtime = runner.MemoryRuntime()
        before = runtime.files["allocation.py"]
        request = {
            "clientRequestId": "request:live-ab-overlap",
            "files": [
                {
                    "relativePath": "allocation.py",
                    "expectedDigest": runner.sha(before),
                    "edits": [
                        {
                            "range": {
                                "start": {"line": 1, "column": 0},
                                "end": {"line": 1, "column": 0},
                            },
                            "expectedText": "",
                            "replacement": "# first\\n",
                        },
                        {
                            "range": {
                                "start": {"line": 1, "column": 0},
                                "end": {"line": 1, "column": 0},
                            },
                            "expectedText": "",
                            "replacement": "# second\\n",
                        },
                    ],
                }
            ],
        }
        with self.assertRaisesRegex(runner.HarnessRuntimeToolRejected, "overlap"):
            runtime.call_tool("workspace.patch", request)
        self.assertEqual(runtime.files["allocation.py"], before)
        self.assertEqual(runtime.receipts, {})

    def test_memory_runtime_duplicate_file_producers_fail_before_effect(self) -> None:
        runtime = runner.MemoryRuntime()
        before = runtime.files["allocation.py"]
        first_file = {
            "relativePath": "allocation.py",
            "expectedDigest": runner.sha(before),
            "edits": [
                {
                    "range": {
                        "start": {"line": 1, "column": 0},
                        "end": {"line": 1, "column": 0},
                    },
                    "expectedText": "",
                    "replacement": "# first\\n",
                }
            ],
        }
        second_file = copy.deepcopy(first_file)
        second_file["edits"][0]["replacement"] = "# second\\n"
        request = {
            "clientRequestId": "request:live-ab-duplicate-producer",
            "files": [first_file, second_file],
        }
        with self.assertRaisesRegex(runner.HarnessRuntimeToolRejected, "more than one producer"):
            runtime.call_tool("workspace.patch", request)
        self.assertEqual(runtime.files["allocation.py"], before)
        self.assertFalse(runtime.receipts)

    def test_live_entry_requires_explicit_test_db_before_credentials(self) -> None:
        with patch.dict(os.environ, {"HARNESS_PG_TEST_DSN": "", "ORDIVON_HARNESS_PG_DSN": "unused"}, clear=True):
            with (
                patch("sys.argv", [str(SCRIPT)]),
                patch.object(runner.DeepSeekSettings, "from_secret_file",
                             side_effect=AssertionError("no provider setup without test database")) as secret,
                self.assertRaises(SystemExit) as exc,
            ):
                runner.main()
            self.assertEqual(exc.exception.code, 2)
            secret.assert_not_called()

    def test_original_experiment_runs_on_real_pg_without_live_provider(self) -> None:
        import psycopg
        from ordivon_harness.ordivon.model import ScriptedTurnAdapter
        from tests.test_r3_supported_agent_run import completed
        from tests.test_adaptive_edit_bridge import scripted_tool_turn

        dsn = os.environ.get("HARNESS_PG_TEST_DSN")
        if not dsn:
            self.skipTest("dedicated PostgreSQL test database required")
        settings = runner.DeepSeekSettings(api_key="test-only-not-a-real-key")
        original_adapter_id = runner.DeepSeekTurnAdapter.adapter_id

        class TestAdapter(ScriptedTurnAdapter):
            adapter_id = original_adapter_id
            model_id = settings.model

            def __init__(self, settings, *, completion_contract):
                del completion_contract
                task = runner.DEFAULT_TASK
                before = (task.fixture / task.target_path).read_text()
                after = task.oracle.read_text()
                read = runner.AgentToolCall(
                    "tool-call:pg-adaptive:read", "read_workspace",
                    {"relativePath": task.target_path, "maxBytes": 4096},
                )
                edit = runner.AgentToolCall(
                    "tool-call:pg-adaptive:edit", "edit_workspace",
                    {"relativePath": task.target_path, "sourceDigest": runner.sha(before),
                     "codec": "exact-replacement-v1", "oldText": before, "newText": after},
                )
                super().__init__(tuple(replace(item, model_id=settings.model) for item in (
                    scripted_tool_turn("pg-adaptive", 1, read),
                    scripted_tool_turn("pg-adaptive", 2, edit),
                    completed("model-call:pg-adaptive:3"),
                )))

        with psycopg.connect(dsn, autocommit=True) as connection:
            def schemas():
                return {row[0] for row in connection.execute(
                    "SELECT nspname FROM pg_namespace WHERE nspname LIKE 'hpg_edit_%'"
                )}
            before = schemas()
            with patch.object(runner, "DeepSeekTurnAdapter", TestAdapter):
                result = runner.run_one("exact-replacement-v1", 1, settings, dsn=dsn)
            self.assertEqual(schemas(), before)
        self.assertEqual(result["status"], "completed", result)
        self.assertTrue(result["candidateCompleted"], result)
        self.assertEqual(result["storageBackend"], "postgresql")
        self.assertTrue(result["journalHealthy"])
        self.assertGreater(result["journalEvents"], 1)
        self.assertEqual(result["modelCalls"], 3)
        self.assertEqual(result["toolCalls"], 2)
        self.assertEqual(result["runtimeOperations"], ["workspace.read", "workspace.read", "workspace.patch"])
        self.assertEqual(result["editObservationStatuses"], ["observed"])
        self.assertTrue(result["visiblePassed"])
        self.assertTrue(result["hiddenPassed"])
        self.assertTrue(result["oracleExact"])

    def test_failed_adapter_setup_removes_only_owned_pg_schema(self) -> None:
        import psycopg

        dsn = os.environ.get("HARNESS_PG_TEST_DSN")
        if not dsn:
            self.skipTest("dedicated PostgreSQL test database required")
        settings = runner.DeepSeekSettings(api_key="test-only-not-a-real-key")
        with psycopg.connect(dsn, autocommit=True) as connection:
            def schemas():
                return {row[0] for row in connection.execute(
                    "SELECT nspname FROM pg_namespace WHERE nspname LIKE 'hpg_edit_%'"
                )}
            before = schemas()
            with (
                patch.object(runner, "DeepSeekTurnAdapter",
                             adapter_id=runner.DeepSeekTurnAdapter.adapter_id,
                             side_effect=RuntimeError("injected setup failure")),
                self.assertRaisesRegex(RuntimeError, "injected setup failure"),
            ):
                runner.run_one("exact-replacement-v1", 1, settings, dsn=dsn)
            self.assertEqual(schemas(), before)

    def test_fixtures_follow_script_location_not_invoking_directory(self) -> None:
        import tempfile

        original = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            try:
                os.chdir(temporary)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(module.ROOT, ROOT)
                self.assertTrue(module.DEFAULT_TASK.fixture.is_dir())
                self.assertTrue(module.DEFAULT_TASK.oracle.is_file())
            finally:
                os.chdir(original)

    def test_summary_is_descriptive_only(self) -> None:
        records = [
            {
                "treatment": "exact-replacement-v1",
                "candidateCompleted": True,
                "visiblePassed": True,
                "hiddenPassed": True,
                "modelCalls": 4,
                "toolCalls": 5,
                "elapsedMs": 1000,
                "rejectedObservations": 0,
                "usage": {"totalTokens": 100},
            }
        ]
        summaries = runner._summaries(records)
        runner.validate_json_value(summaries)
        summary = summaries["exact-replacement-v1"]
        self.assertEqual(summary["runs"], 1)
        self.assertEqual(summary["hiddenPassed"], 1)
        self.assertEqual(summary["totals"]["totalTokens"], 100)
        self.assertEqual(summary["meansTimes10"]["totalTokens"], 1000)
        report = {
            "schemaVersion": 1,
            "kind": "test-live-ab-report",
            "summaries": summaries,
        }
        self.assertTrue(runner.canonical_digest(report).startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
