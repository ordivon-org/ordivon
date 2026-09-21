from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_benchmark_contract as B  # noqa: E402
import browser_benchmark_prospective as P  # noqa: E402
import browser_capability_router as R  # noqa: E402


def fake_jev_status() -> dict:
    return {
        "healthy": True,
        "python": {
            "path": "/mnt/c/Users/test/AppData/Local/Ordivon/External/python/python.exe",
            "providerVenvPath": "/mnt/c/Users/test/AppData/Local/Ordivon/External/jev-ultrafast/rev/.venv/Scripts/python.exe",
        },
        "chrome": {
            "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "profileWindows": r"C:\Users\test\AppData\Local\Ordivon\Chrome-CDP\jev",
            "cdpPort": 9338,
        },
    }


class BrowserBenchmarkProspectiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = R.load_policy()
        self.suite = B.load_suite(policy=self.policy)

    def plan_fn(self, ready_routes: set[str]):
        overrides = {
            route_id: {
                "ready": route_id in ready_routes,
                "standing": "READY" if route_id in ready_routes else "FIXTURE_BLOCKED",
            }
            for route_id in P.PAIRED_ROUTES
        }

        def plan(request, *, policy):
            return R.plan_route(
                request,
                policy=policy,
                readiness_overrides=overrides,
            )

        return plan

    def manifest(self, pair_count: int = 4) -> dict:
        return P.build_manifest(
            campaign_id="campaign-r1",
            pair_count=pair_count,
            suite=self.suite,
            policy=self.policy,
        )

    def test_manifest_freezes_pairing_before_readiness(self) -> None:
        manifest = self.manifest(pair_count=4)
        self.assertEqual(manifest["pairCount"], 4)
        self.assertFalse(manifest["effectsExecuted"])
        self.assertFalse(
            manifest["readinessContract"]["callerReadinessOverridesAccepted"]
        )
        self.assertEqual(
            [t["routeId"] for t in manifest["pairs"][0]["trials"]],
            list(P.PAIRED_ROUTES),
        )
        self.assertEqual(
            [t["routeId"] for t in manifest["pairs"][1]["trials"]],
            list(reversed(P.PAIRED_ROUTES)),
        )
        self.assertEqual(
            manifest,
            P.validate_manifest(
                manifest,
                suite=self.suite,
                policy=self.policy,
            ),
        )

    def test_manifest_digest_binds_pair_count_and_order(self) -> None:
        a = self.manifest(pair_count=2)
        b = self.manifest(pair_count=3)
        self.assertNotEqual(a["manifestDigest"], b["manifestDigest"])
        changed = dict(a)
        changed["pairs"] = list(reversed(a["pairs"]))
        with self.assertRaisesRegex(ValueError, "differs"):
            P.validate_manifest(changed, suite=self.suite, policy=self.policy)

    def test_blocked_route_prevents_all_trial_materialization(self) -> None:
        manifest = self.manifest(pair_count=3)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            result = P.gate_manifest(
                manifest,
                workspace_id="ws-browser-benchmark-prospective-s5-20260918",
                state_root=root,
                suite=self.suite,
                policy=self.policy,
                plan_fn=self.plan_fn({"browser-use-browserless-v1"}),
                jev_status_fn=lambda: (_ for _ in ()).throw(
                    AssertionError("blocked campaign must not read Jev proposal status")
                ),
            )
            files = list(root.rglob("*"))
        self.assertEqual(result["standing"], "BLOCKED_BY_ROUTE_READINESS")
        self.assertEqual(result["trialBundles"], [])
        self.assertFalse(result["effectsExecuted"])
        self.assertFalse(result["runtimeJobsCreated"])
        self.assertEqual(files, [])
        by_route = {row["routeId"]: row for row in result["readiness"]}
        self.assertFalse(by_route["jev-fast-windows-v1"]["ready"])
        self.assertTrue(by_route["browser-use-browserless-v1"]["ready"])

    def test_ready_gate_materializes_exact_paired_templates_only(self) -> None:
        manifest = self.manifest(pair_count=2)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            calls = {"jevStatus": 0}

            def status():
                calls["jevStatus"] += 1
                return fake_jev_status()

            result = P.gate_manifest(
                manifest,
                workspace_id="ws-browser-benchmark-prospective-s5-20260918",
                state_root=root,
                suite=self.suite,
                policy=self.policy,
                plan_fn=self.plan_fn(set(P.PAIRED_ROUTES)),
                jev_status_fn=status,
                windows_path_fn=lambda p: "WINDOWS_PATH:" + str(p),
            )
            request_files = list(root.rglob("route-run-request.json"))

        self.assertEqual(result["standing"], "READY_FOR_PAIRED_RUNTIME_BINDING")
        self.assertEqual(len(result["trialBundles"]), 4)
        self.assertEqual(len(request_files), 4)
        self.assertEqual(calls["jevStatus"], 1)
        self.assertFalse(result["effectsExecuted"])
        self.assertFalse(result["runtimeJobsCreated"])

        expected_order = [
            "jev-fast-windows-v1",
            "browser-use-browserless-v1",
            "browser-use-browserless-v1",
            "jev-fast-windows-v1",
        ]
        self.assertEqual(
            [row["routeId"] for row in result["trialBundles"]],
            expected_order,
        )
        for bundle in result["trialBundles"]:
            template = bundle["admissionTemplate"]
            prep = bundle["preparation"]
            self.assertEqual(template["standing"], "ADMISSION_TEMPLATE_READY")
            self.assertEqual(template["runId"], bundle["runId"])
            self.assertEqual(prep["runId"], bundle["runId"])
            self.assertEqual(prep["caseDigest"], bundle["caseDigest"])
            self.assertEqual(template["templateDigest"], bundle["templateDigest"])
            self.assertEqual(prep["preparationDigest"], bundle["preparationDigest"])

    def test_ready_gate_never_serializes_jev_secret_value(self) -> None:
        manifest = self.manifest(pair_count=1)
        with tempfile.TemporaryDirectory() as d:
            result = P.gate_manifest(
                manifest,
                workspace_id="ws-browser-benchmark-prospective-s5-20260918",
                state_root=Path(d),
                suite=self.suite,
                policy=self.policy,
                plan_fn=self.plan_fn(set(P.PAIRED_ROUTES)),
                jev_status_fn=fake_jev_status,
                windows_path_fn=lambda p: "WINDOWS_PATH:" + str(p),
            )
        jev = next(
            row
            for row in result["trialBundles"]
            if row["routeId"] == "jev-fast-windows-v1"
        )
        template = jev["admissionTemplate"]
        self.assertEqual(template["requiredSecretEnvironment"], ["TYPESAFE_API_KEY"])
        self.assertNotIn("TYPESAFE_API_KEY", template["execution"]["env"])
        self.assertFalse(template["secretValuesIncluded"])

    def test_gate_digest_is_stable_for_same_readiness_snapshot(self) -> None:
        manifest = self.manifest(pair_count=1)
        kwargs = {
            "workspace_id": "ws-browser-benchmark-prospective-s5-20260918",
            "suite": self.suite,
            "policy": self.policy,
            "plan_fn": self.plan_fn({"browser-use-browserless-v1"}),
            "jev_status_fn": fake_jev_status,
        }
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first = P.gate_manifest(manifest, state_root=Path(a), **kwargs)
            second = P.gate_manifest(manifest, state_root=Path(b), **kwargs)
        self.assertEqual(first["gateDigest"], second["gateDigest"])


if __name__ == "__main__":
    unittest.main()
