from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_benchmark_contract as B  # noqa: E402
import browser_benchmark_route_adapter as A  # noqa: E402
import browser_capability_router as R  # noqa: E402
import browser_use_browserless as BU  # noqa: E402


def ready() -> dict:
    return {"ready": True, "standing": "READY"}


class BrowserBenchmarkRouteAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = R.load_policy()
        self.suite = B.load_suite(policy=self.policy)
        self.cases = {row["routeId"]: row for row in B.compile_cases(self.suite)}

    def ready_receipt(self, route_id: str) -> dict:
        return B.preflight_case(
            self.cases[route_id],
            policy=self.policy,
            readiness_overrides={route_id: ready()},
        )

    def run_request(self, route_id: str) -> dict:
        return A.build_run_request(
            self.cases[route_id],
            self.ready_receipt(route_id),
            "run:test:1",
        )

    def test_build_request_binds_ready_case_and_digest(self) -> None:
        request = self.run_request("jev-fast-windows-v1")
        self.assertEqual(request["case"]["routeId"], "jev-fast-windows-v1")
        self.assertEqual(request["preflightReceipt"]["standing"], "READY")
        expected = dict(request)
        digest = expected.pop("requestDigest")
        self.assertEqual(digest, R.canonical_digest(expected))
        self.assertEqual(A.validate_run_request(request)["requestDigest"], digest)

    def test_effectful_runner_refuses_non_ready_preflight(self) -> None:
        case = self.cases["jev-fast-windows-v1"]
        blocked = B.preflight_case(
            case,
            policy=self.policy,
            readiness_overrides={
                "jev-fast-windows-v1": {
                    "ready": False,
                    "standing": "CREDENTIAL_MISSING",
                }
            },
        )
        with self.assertRaisesRegex(ValueError, "READY"):
            A.build_run_request(case, blocked, "run:test:blocked")

    def test_generic_adapter_result_finalizes_through_s2(self) -> None:
        request = self.run_request("jev-fast-windows-v1")

        def fake(case, run_id):
            self.assertEqual(run_id, "run:test:1")
            return {
                "standing": "EXECUTION_OBSERVED",
                "providerEffectMayHaveOccurred": True,
                "adapterReceipt": {"kind": "fake", "standing": "DONE"},
                "metrics": {"totalElapsedMs": 10, "actionCount": 2, "fallbackCount": 0},
                "outcomeWitness": {
                    "standing": "PASS",
                    "checks": [
                        {
                            "checkId": case["outcomeCheckIds"][0],
                            "standing": "PASS",
                            "passed": True,
                            "observedTextDigest": "sha256:" + "2" * 64,
                        }
                    ],
                },
            }

        result = A.run_request(
            request,
            adapters={"jev-fast-windows-v1": fake},
        )
        self.assertEqual(result["standing"], "EXECUTED")
        self.assertTrue(result["resultDigest"].startswith("sha256:"))
        A.validate_run_result(
            result,
            expected_run_id="run:test:1",
            expected_request_digest=request["requestDigest"],
            expected_case_digest=request["case"]["caseDigest"],
            expected_route_id="jev-fast-windows-v1",
        )
        receipt = result["benchmarkReceipt"]
        self.assertEqual(receipt["standing"], "EXECUTED")
        self.assertEqual(receipt["outcomeWitness"]["standing"], "PASS")
        self.assertEqual(receipt["metrics"]["totalElapsedMs"]["value"], 10)
        self.assertEqual(
            receipt["metrics"]["providerApiRequestCount"]["standing"],
            "NOT_OBSERVED",
        )

    def test_pre_effect_abort_never_finalizes_as_executed(self) -> None:
        request = self.run_request("jev-fast-windows-v1")

        def fake(_case, _run_id):
            return {
                "standing": "PRE_EFFECT_ABORTED",
                "providerEffectMayHaveOccurred": False,
                "adapterReceipt": {"kind": "fake", "standing": "NO_CREDENTIAL"},
                "metrics": {"totalElapsedMs": 1},
                "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
            }

        result = A.run_request(
            request,
            adapters={"jev-fast-windows-v1": fake},
        )
        self.assertEqual(result["standing"], "PRE_EFFECT_ABORTED")
        self.assertTrue(result["resultDigest"].startswith("sha256:"))
        A.validate_run_result(
            result,
            expected_run_id="run:test:1",
            expected_request_digest=request["requestDigest"],
            expected_case_digest=request["case"]["caseDigest"],
            expected_route_id="jev-fast-windows-v1",
        )
        self.assertIsNone(result["benchmarkReceipt"])
        self.assertFalse(result["providerEffectMayHaveOccurred"])

    def test_route_result_identity_drift_fails_closed(self) -> None:
        request = self.run_request("jev-fast-windows-v1")

        def fake(_case, _run_id):
            return {
                "standing": "PRE_EFFECT_ABORTED",
                "providerEffectMayHaveOccurred": False,
                "adapterReceipt": {"kind": "fake", "standing": "NO_EFFECT"},
                "metrics": {},
                "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
            }

        result = A.run_request(request, adapters={"jev-fast-windows-v1": fake})
        changed = dict(result)
        changed["routeId"] = "browser-use-browserless-v1"
        with self.assertRaisesRegex(ValueError, "routeId differs"):
            A.validate_run_result(
                changed,
                expected_route_id="jev-fast-windows-v1",
            )

    def test_jev_adapter_maps_explicit_provider_witness(self) -> None:
        case = self.cases["jev-fast-windows-v1"]

        def execute(req):
            self.assertTrue(req["url"].startswith("data:text/html;charset=utf-8,"))
            self.assertEqual(req["witness"], {"textContains": "BCR_TARGET_OK"})
            return {
                "schemaVersion": 1,
                "kind": "ordivon.jev-fastpath-receipt",
                "standing": "PASS",
                "providerEffectMayHaveOccurred": True,
                "actionCount": 3,
                "outcomeWitness": {
                    "standing": "PASS",
                    "checks": [
                        {
                            "kind": "textContains",
                            "expected": "BCR_TARGET_OK",
                            "passed": True,
                            "observedTextDigest": "sha256:" + "3" * 64,
                        }
                    ],
                },
            }

        result = A._jev_route_adapter(case, "run:jev:1", execute_fn=execute)
        self.assertEqual(result["standing"], "EXECUTION_OBSERVED")
        self.assertEqual(result["metrics"]["actionCount"], 3)
        self.assertEqual(result["outcomeWitness"]["standing"], "PASS")
        self.assertEqual(
            result["outcomeWitness"]["checks"][0]["checkId"],
            "target-state-visible",
        )

    def test_jev_credential_loss_after_preflight_is_pre_effect_abort(self) -> None:
        case = self.cases["jev-fast-windows-v1"]
        result = A._jev_route_adapter(
            case,
            "run:jev:missing",
            execute_fn=lambda _req: {
                "schemaVersion": 1,
                "kind": "ordivon.jev-fastpath-receipt",
                "standing": "CREDENTIAL_MISSING",
                "providerEffectMayHaveOccurred": False,
                "missingCredentials": ["TYPESAFE_API_KEY"],
                "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
            },
        )
        self.assertEqual(result["standing"], "PRE_EFFECT_ABORTED")
        self.assertFalse(result["providerEffectMayHaveOccurred"])

    def test_browser_use_structured_route_executes_exact_affordance(self) -> None:
        case = self.cases["browser-use-browserless-v1"]
        endpoint = SimpleNamespace(endpoint_id="browser-agent-21")
        outputs = iter(
            [
                {"standing": "OPENED", "page": {"url": "data:"}},
                {
                    "standing": "OBSERVED",
                    "affordances": [
                        {
                            "index": 4,
                            "role": "button",
                            "name": "Complete Benchmark",
                            "x": 10,
                            "y": 20,
                        }
                    ],
                    "visibleText": "BCR_TARGET_PENDING",
                },
                {"standing": "CLICKED"},
                {"standing": "OBSERVED", "affordances": [], "visibleText": "BCR_TARGET_OK"},
            ]
        )

        def fake_run(_executable, _program, _env, timeout=90):
            _ = timeout
            import json

            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(next(outputs)) + "\n",
                stderr="",
            )

        fake = SimpleNamespace(
            DEFAULT_CONFIG=Path("/fake"),
            load_config=lambda _path: ({"browserUseExecutable": "/bin/browser-use"}, object()),
            select_endpoint=lambda _pool, _session, _endpoint_id: endpoint,
            ensure_daemon=lambda *_args, **_kwargs: None,
            _generated_env=lambda *_args, **_kwargs: {},
            _run_browser_use=fake_run,
            program_open=BU.program_open,
            program_observe=BU.program_observe,
            program_click=BU.program_click,
            session_name=BU.session_name,
            close_session=lambda *_args, **_kwargs: {"standing": "CLOSED"},
        )
        result = A._browser_use_route_adapter(
            case,
            "run:browser-use:1",
            browser_module=fake,
        )
        self.assertEqual(result["standing"], "EXECUTION_OBSERVED")
        self.assertEqual(result["outcomeWitness"]["standing"], "PASS")
        self.assertEqual(result["metrics"]["actionCount"], 2)
        self.assertEqual(result["metrics"]["modelRequestCount"], 0)
        self.assertEqual(result["adapterReceipt"]["target"]["name"], "Complete Benchmark")


if __name__ == "__main__":
    unittest.main()
