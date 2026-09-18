from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SCRIPT = ROOT / "scripts" / "browser_benchmark_contract.py"
spec = importlib.util.spec_from_file_location("browser_benchmark_contract", SCRIPT)
assert spec and spec.loader
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

import browser_capability_router as R  # noqa: E402


def ready() -> dict:
    return {"ready": True, "standing": "READY"}


def blocked(standing: str, **extra) -> dict:
    return {"ready": False, "standing": standing, **extra}


class BrowserBenchmarkContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = R.load_policy()
        self.suite = B.load_suite(policy=self.policy)
        self.cases = B.compile_cases(self.suite)
        self.by_route = {row["routeId"]: row for row in self.cases}

    def test_suite_has_two_explicit_route_locked_variants(self) -> None:
        self.assertEqual(len(self.cases), 2)
        self.assertEqual(
            set(self.by_route),
            {"jev-fast-windows-v1", "browser-use-browserless-v1"},
        )
        for case in self.cases:
            self.assertEqual(case["routeRequest"]["explicitRouteId"], case["routeId"])
            self.assertEqual(case["routeRequest"]["requiredFeatures"], ["navigate", "click"])
            self.assertEqual(case["outcomeCheckIds"], ["target-state-visible"])
            self.assertEqual(case["executionContract"]["kind"], "inline-html-click-v1")
            self.assertEqual(case["executionContract"]["buttonName"], "Complete Benchmark")
            self.assertEqual(case["executionContract"]["successText"], "BCR_TARGET_OK")
            self.assertEqual(
                case["executionContractDigest"],
                R.canonical_digest(case["executionContract"]),
            )

    def test_task_digest_binds_executable_task_semantics(self) -> None:
        baseline = self.suite["tasks"][0]
        original = baseline["taskDigest"]
        changed_contract = dict(baseline["executionContract"])
        changed_contract["buttonName"] = "Different Button"
        changed_task = {
            "taskId": baseline["taskId"],
            "providerFlow": baseline["providerFlow"],
            "requiredFeatures": list(baseline["requiredFeatures"]),
            "preferredFeatures": list(baseline["preferredFeatures"]),
            "outcomeCheckIds": list(baseline["outcomeCheckIds"]),
            "executionContract": changed_contract,
        }
        self.assertNotEqual(original, R.canonical_digest(changed_task))

    def test_preflight_ready_does_not_execute_or_fake_metrics(self) -> None:
        case = self.by_route["jev-fast-windows-v1"]
        receipt = B.preflight_case(
            case,
            policy=self.policy,
            readiness_overrides={"jev-fast-windows-v1": ready()},
        )
        self.assertEqual(receipt["standing"], "READY")
        self.assertFalse(receipt["providerEffectMayHaveOccurred"])
        self.assertEqual(receipt["outcomeWitness"]["standing"], "NOT_EXECUTED")
        self.assertEqual(receipt["outcomeCheckIds"], ["target-state-visible"])
        self.assertTrue(
            all(
                row == {"standing": "NOT_OBSERVED", "value": None}
                for row in receipt["metrics"].values()
            )
        )
        self.assertFalse(receipt["fallback"]["attempted"])

    def test_preflight_blocked_preserves_credential_gate_without_fallback(self) -> None:
        case = self.by_route["jev-fast-windows-v1"]
        receipt = B.preflight_case(
            case,
            policy=self.policy,
            readiness_overrides={
                "jev-fast-windows-v1": blocked(
                    "CREDENTIAL_MISSING", missingEnvironment=["TYPESAFE_API_KEY"]
                ),
                "browser-use-browserless-v1": ready(),
            },
        )
        self.assertEqual(receipt["standing"], "PREEXEC_BLOCKED")
        self.assertEqual(receipt["blocker"]["routeReadinessStanding"], "CREDENTIAL_MISSING")
        self.assertEqual(receipt["blocker"]["missingEnvironmentNames"], ["TYPESAFE_API_KEY"])
        self.assertEqual(receipt["fallback"], {"attempted": False, "routeIds": []})

    def test_preflight_blocked_preserves_operator_policy_mask(self) -> None:
        case = self.by_route["browser-use-browserless-v1"]
        receipt = B.preflight_case(
            case,
            policy=self.policy,
            readiness_overrides={
                "browser-use-browserless-v1": blocked(
                    "POLICY_DISABLED", policyDisabledEndpointIds=["browser-agent-21"]
                )
            },
        )
        self.assertEqual(receipt["standing"], "PREEXEC_BLOCKED")
        self.assertEqual(receipt["blocker"]["routeReadinessStanding"], "POLICY_DISABLED")
        self.assertEqual(
            receipt["blocker"]["policyDisabledEndpointIds"], ["browser-agent-21"]
        )

    def test_preflight_report_never_executes_effects(self) -> None:
        report = B.preflight_suite(
            self.suite,
            policy=self.policy,
            readiness_overrides={
                "jev-fast-windows-v1": blocked("CREDENTIAL_MISSING"),
                "browser-use-browserless-v1": blocked("POLICY_DISABLED"),
            },
        )
        self.assertFalse(report["effectsExecuted"])
        self.assertEqual(report["counts"], {"READY": 0, "PREEXEC_BLOCKED": 2})

    def _ready_receipt(self) -> dict:
        case = self.by_route["jev-fast-windows-v1"]
        return B.preflight_case(
            case,
            policy=self.policy,
            readiness_overrides={"jev-fast-windows-v1": ready()},
        )

    def _observation(self, receipt: dict, witness: str = "PASS") -> dict:
        metrics = {
            name: {"standing": "NOT_OBSERVED", "value": None}
            for name in B.METRIC_CONTRACT
        }
        metrics["totalElapsedMs"] = {"standing": "OBSERVED", "value": 712}
        metrics["actionCount"] = {"standing": "OBSERVED", "value": 4}
        return {
            "schemaVersion": 1,
            "kind": "ordivon.browser-benchmark-execution-observation",
            "caseDigest": receipt["caseDigest"],
            "routePlanDigest": receipt["routePlanDigest"],
            "routeId": receipt["routeId"],
            "adapterReceiptDigest": "sha256:" + "1" * 64,
            "providerEffectMayHaveOccurred": True,
            "metrics": metrics,
            "expectedOutcomeCheckIds": list(receipt["outcomeCheckIds"]),
            "outcomeWitness": {
                "standing": witness,
                "checks": (
                    [{"checkId": "target-state-visible", "standing": witness}]
                    if witness in {"PASS", "FAIL"}
                    else []
                ),
            },
        }

    def test_finalize_ready_receipt_as_executed_with_explicit_witness(self) -> None:
        ready_receipt = self._ready_receipt()
        result = B.finalize_execution(ready_receipt, self._observation(ready_receipt))
        self.assertEqual(result["standing"], "EXECUTED")
        self.assertEqual(result["outcomeWitness"]["standing"], "PASS")
        self.assertEqual(result["metrics"]["totalElapsedMs"]["value"], 712)
        self.assertTrue(result["providerEffectMayHaveOccurred"])
        B.validate_receipt(result)

    def test_finalize_allows_unverified_but_never_promotes_it_to_pass(self) -> None:
        ready_receipt = self._ready_receipt()
        result = B.finalize_execution(
            ready_receipt, self._observation(ready_receipt, witness="UNVERIFIED")
        )
        self.assertEqual(result["standing"], "EXECUTED")
        self.assertEqual(result["outcomeWitness"]["standing"], "UNVERIFIED")

    def test_finalize_rejects_blocked_preflight(self) -> None:
        case = self.by_route["jev-fast-windows-v1"]
        receipt = B.preflight_case(
            case,
            policy=self.policy,
            readiness_overrides={"jev-fast-windows-v1": blocked("CREDENTIAL_MISSING")},
        )
        with self.assertRaisesRegex(ValueError, "only READY"):
            B.finalize_execution(receipt, self._observation(receipt))

    def test_finalize_rejects_route_identity_drift(self) -> None:
        receipt = self._ready_receipt()
        obs = self._observation(receipt)
        obs["routeId"] = "browser-use-browserless-v1"
        with self.assertRaisesRegex(ValueError, "differs from preflight: routeId"):
            B.finalize_execution(receipt, obs)

    def test_finalize_rejects_outcome_contract_drift(self) -> None:
        receipt = self._ready_receipt()
        obs = self._observation(receipt)
        obs["expectedOutcomeCheckIds"] = ["easier-check"]
        with self.assertRaisesRegex(ValueError, "outcome contract differs from preflight"):
            B.finalize_execution(receipt, obs)

    def test_missing_metric_is_not_zero(self) -> None:
        receipt = self._ready_receipt()
        obs = self._observation(receipt)
        obs["metrics"].pop("providerApiRequestCount")
        with self.assertRaisesRegex(ValueError, "metric set mismatch"):
            B.finalize_execution(receipt, obs)

    def test_not_observed_metric_cannot_carry_zero(self) -> None:
        receipt = self._ready_receipt()
        obs = self._observation(receipt)
        obs["metrics"]["providerApiRequestCount"] = {
            "standing": "NOT_OBSERVED",
            "value": 0,
        }
        with self.assertRaisesRegex(ValueError, "must have null value"):
            B.finalize_execution(receipt, obs)

    def test_route_locked_receipt_forbids_fallback(self) -> None:
        receipt = self._ready_receipt()
        receipt["fallback"] = {
            "attempted": True,
            "routeIds": ["browser-use-browserless-v1"],
        }
        receipt.pop("receiptDigest")
        receipt["receiptDigest"] = R.canonical_digest(receipt)
        with self.assertRaisesRegex(ValueError, "forbids fallback"):
            B.validate_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
