from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_benchmark_contract as B  # noqa: E402
import browser_benchmark_route_adapter as A  # noqa: E402
import browser_benchmark_runner as X  # noqa: E402
import browser_benchmark_runtime_handoff as H  # noqa: E402
import browser_capability_router as R  # noqa: E402


def ready() -> dict:
    return {"ready": True, "standing": "READY"}


def runtime_success() -> dict:
    return {
        "status": "succeeded",
        "jobId": "job-s4-test",
        "attemptId": "attempt-s4-test",
        "executionTerminal": True,
        "executionDisposition": "succeeded",
        "deliveryDisposition": "committed",
        "recoveryRequired": False,
        "semanticCompletionEvaluated": False,
        "exitCode": 0,
        "resultAvailable": True,
    }


class BrowserBenchmarkRuntimeHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = R.load_policy()
        self.suite = B.load_suite(policy=self.policy)
        self.cases = {row["routeId"]: row for row in B.compile_cases(self.suite)}

    def prepare_browser_use(self, root: Path, run_id: str = "run:s4:bu") -> dict:
        return X.prepare_case(
            "generic-navigate-click-browser-use",
            run_id,
            state_root=root,
            policy=self.policy,
            suite=self.suite,
            readiness_overrides={"browser-use-browserless-v1": ready()},
        )

    def prepare_jev(self, root: Path, run_id: str = "run:s4:jev") -> dict:
        status = {
            "healthy": True,
            "python": {
                "path": "/mnt/c/Users/test/AppData/Local/Ordivon/External/python/python.exe"
            },
            "chrome": {
                "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "profileWindows": r"C:\Users\test\AppData\Local\Ordivon\Chrome-CDP\jev",
                "cdpPort": 9338,
            },
        }
        return X.prepare_case(
            "generic-navigate-click-jev",
            run_id,
            state_root=root,
            policy=self.policy,
            suite=self.suite,
            readiness_overrides={"jev-fast-windows-v1": ready()},
            jev_status_fn=lambda: status,
            windows_path_fn=lambda p: "\\wsl.localhost\archlinux" + str(p).replace("/", "\\"),
        )

    def route_result(
        self,
        prep: dict,
        *,
        witness: str = "PASS",
        pre_effect_abort: bool = False,
    ) -> dict:
        case = self.cases[prep["routeId"]]
        request = A.build_run_request(case, prep["preflightReceipt"], prep["runId"])

        def fake(case_value, _run_id):
            if pre_effect_abort:
                return {
                    "standing": "PRE_EFFECT_ABORTED",
                    "providerEffectMayHaveOccurred": False,
                    "adapterReceipt": {"kind": "fake", "standing": "NO_EFFECT"},
                    "metrics": {"totalElapsedMs": 1},
                    "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
                }
            checks = []
            if witness in {"PASS", "FAIL"}:
                checks = [
                    {
                        "checkId": case_value["outcomeCheckIds"][0],
                        "standing": witness,
                        "passed": witness == "PASS",
                        "observedTextDigest": "sha256:" + "5" * 64,
                    }
                ]
            return {
                "standing": "EXECUTION_OBSERVED",
                "providerEffectMayHaveOccurred": True,
                "adapterReceipt": {"kind": "fake", "standing": "DONE"},
                "metrics": {
                    "totalElapsedMs": 11,
                    "actionCount": 2,
                    "fallbackCount": 0,
                },
                "outcomeWitness": {"standing": witness, "checks": checks},
            }

        return A.run_request(request, adapters={prep["routeId"]: fake})

    def test_blocked_preparation_has_no_runtime_admission(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = X.prepare_case(
                "generic-navigate-click-jev",
                "run:s4:blocked",
                state_root=Path(d),
                policy=self.policy,
                suite=self.suite,
                readiness_overrides={
                    "jev-fast-windows-v1": {
                        "ready": False,
                        "standing": "CREDENTIAL_MISSING",
                        "missingEnvironment": ["TYPESAFE_API_KEY"],
                    }
                },
            )
        template = H.build_admission_template(
            prep, workspace_id="ws-browser-benchmark-runtime-handoff-s4-20260918"
        )
        self.assertEqual(template["standing"], "PREEXEC_BLOCKED")
        self.assertIsNone(template["runtimeOperation"])
        self.assertIsNone(template["execution"])
        self.assertFalse(template["secretValuesIncluded"])
        reconciled = H.reconcile(prep, None, None)
        self.assertEqual(reconciled["standing"], "PREEXEC_BLOCKED")
        self.assertEqual(reconciled["semanticStanding"], "NOT_EXECUTED")

    def test_local_linux_template_binds_host_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d))
            template = H.build_admission_template(
                prep, workspace_id="ws-browser-benchmark-runtime-handoff-s4-20260918"
            )
        self.assertEqual(template["standing"], "ADMISSION_TEMPLATE_READY")
        self.assertEqual(template["runtimeOperation"], "workspace.exec")
        self.assertEqual(
            template["sourceContinuity"], "RUNTIME_HOST_DEPENDENCY_WITNESS"
        )
        execution = template["execution"]
        self.assertEqual(execution["executionTarget"], "local_linux")
        self.assertEqual(len(execution["hostDependencies"]), 2)
        self.assertEqual(
            execution["hostDependencies"],
            sorted(execution["hostDependencies"], key=lambda row: row["path"]),
        )
        expected_digests = {
            prep["executionProposal"]["adapterScriptDigest"],
            prep["executionProposal"]["requestFileDigest"],
        }
        self.assertEqual(
            {row["expectedDigest"] for row in execution["hostDependencies"]},
            expected_digests,
        )
        self.assertEqual(template["requiredSecretEnvironment"], [])

    def test_windows_template_never_serializes_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_jev(Path(d))
            template = H.build_admission_template(
                prep, workspace_id="ws-browser-benchmark-runtime-handoff-s4-20260918"
            )
        self.assertEqual(template["execution"]["executionTarget"], "windows_native")
        self.assertEqual(
            template["sourceContinuity"],
            "PROPOSAL_DIGEST_ONLY_NO_WINDOWS_HOST_DEPENDENCY_WITNESS",
        )
        self.assertNotIn("hostDependencies", template["execution"])
        self.assertEqual(template["requiredSecretEnvironment"], ["TYPESAFE_API_KEY"])
        self.assertNotIn("TYPESAFE_API_KEY", template["execution"]["env"])
        self.assertFalse(template["secretValuesIncluded"])

    def test_runtime_success_plus_pass_route_is_benchmark_executed_pass(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:pass")
            route = self.route_result(prep, witness="PASS")
        result = H.reconcile(prep, runtime_success(), route)
        self.assertEqual(result["standing"], "BENCHMARK_EXECUTED")
        self.assertEqual(result["semanticStanding"], "PASS")
        self.assertTrue(result["providerEffectMayHaveOccurred"])
        self.assertEqual(result["routeResultDigest"], route["resultDigest"])
        self.assertEqual(
            result["benchmarkReceiptDigest"],
            route["benchmarkReceipt"]["receiptDigest"],
        )

    def test_runtime_success_plus_unverified_route_is_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:unverified")
            route = self.route_result(prep, witness="UNVERIFIED")
        result = H.reconcile(prep, runtime_success(), route)
        self.assertEqual(result["standing"], "BENCHMARK_EXECUTED")
        self.assertEqual(result["semanticStanding"], "UNVERIFIED")

    def test_runtime_success_without_route_result_is_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:missing-result")
        result = H.reconcile(prep, runtime_success(), None)
        self.assertEqual(result["standing"], "RUNTIME_RESULT_UNRESOLVED")
        self.assertEqual(result["semanticStanding"], "UNVERIFIED")

    def test_runtime_failure_does_not_infer_route_or_semantic_failure(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:runtime-fail")
        runtime = runtime_success()
        runtime.update(
            {
                "status": "failed",
                "executionDisposition": "failed",
                "exitCode": 2,
            }
        )
        result = H.reconcile(prep, runtime, None)
        self.assertEqual(result["standing"], "RUNTIME_FAILED")
        self.assertEqual(result["semanticStanding"], "UNVERIFIED")
        self.assertIsNone(result["providerEffectMayHaveOccurred"])

    def test_runtime_reconciliation_required_remains_nonterminal_semantically(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:reconcile")
        runtime = {
            "status": "working",
            "jobId": "job-s4-reconcile",
            "attemptId": "attempt-s4-reconcile",
            "executionTerminal": False,
            "executionDisposition": None,
            "deliveryDisposition": "in_progress",
            "recoveryRequired": False,
            "semanticCompletionEvaluated": False,
            "exitCode": None,
            "resultAvailable": False,
        }
        result = H.reconcile(prep, runtime, None)
        self.assertEqual(result["standing"], "RUNTIME_RECONCILIATION_REQUIRED")
        self.assertEqual(result["semanticStanding"], "UNVERIFIED")

    def test_route_pre_effect_abort_is_not_benchmark_execution(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:pre-effect")
            route = self.route_result(prep, pre_effect_abort=True)
        result = H.reconcile(prep, runtime_success(), route)
        self.assertEqual(result["standing"], "PRE_EFFECT_ABORTED")
        self.assertEqual(result["semanticStanding"], "NOT_EXECUTED")
        self.assertFalse(result["providerEffectMayHaveOccurred"])

    def test_route_result_identity_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:mismatch")
            route = self.route_result(prep, witness="PASS")
        changed = dict(route)
        changed["requestDigest"] = "sha256:" + "0" * 64
        changed.pop("resultDigest")
        changed["resultDigest"] = R.canonical_digest(changed)
        with self.assertRaisesRegex(ValueError, "requestDigest differs"):
            H.reconcile(prep, runtime_success(), changed)

    def test_exact_browser_use_preparation_does_not_probe_sibling_jev(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            with mock.patch(
                "browser_capability_router._probe_jev",
                side_effect=AssertionError("sibling Jev readiness must stay isolated"),
            ):
                prep = self.prepare_browser_use(Path(d), "run:s4:isolated")
        self.assertEqual(prep["standing"], "READY_FOR_RUNTIME")
        self.assertEqual(prep["routeId"], "browser-use-browserless-v1")

    def test_runtime_must_not_claim_semantic_completion(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:semantic")
        runtime = runtime_success()
        runtime["semanticCompletionEvaluated"] = True
        with self.assertRaisesRegex(ValueError, "must not claim"):
            H.reconcile(prep, runtime, None)

    def test_preparation_or_proposal_digest_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            prep = self.prepare_browser_use(Path(d), "run:s4:drift")
        changed = dict(prep)
        changed["routeId"] = "jev-fast-windows-v1"
        with self.assertRaisesRegex(ValueError, "preparation digest mismatch"):
            H.build_admission_template(changed, workspace_id="ws-valid")


if __name__ == "__main__":
    unittest.main()
