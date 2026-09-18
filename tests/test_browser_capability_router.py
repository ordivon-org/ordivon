from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "browser_capability_router", ROOT / "scripts/browser_capability_router.py"
)
assert SPEC and SPEC.loader
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


class BrowserCapabilityRouterTests(unittest.TestCase):
    def policy(self):
        return R.load_policy(ROOT / "config/browser-capability-routes.json")

    def req(self, **extra):
        value = {
            "schemaVersion": 1,
            "requestId": "route:test:1",
            "providerFlow": "generic",
            "requiredFeatures": [],
            "preferredFeatures": [],
        }
        value.update(extra)
        return value

    def ready(self, *route_ids):
        return {
            route["routeId"]: {"ready": route["routeId"] in route_ids, "standing": "FIXTURE"}
            for route in self.policy()["routes"]
        }

    def test_generic_prefers_jev_when_ready(self):
        value = R.plan_route(
            self.req(preferredFeatures=["low-latency"]),
            policy=self.policy(),
            readiness_overrides=self.ready("jev-fast-windows-v1", "browser-use-browserless-v1"),
        )
        self.assertEqual(value["standing"], "SELECTED")
        self.assertEqual(value["selectedRoute"]["routeId"], "jev-fast-windows-v1")
        self.assertEqual(value["selectedRoute"]["executor"], "jev_fast")
        self.assertEqual(value["selectedRoute"]["substrate"], "windows_chrome")

    def test_browser_use_is_fallback_when_jev_is_not_ready(self):
        value = R.plan_route(
            self.req(preferredFeatures=["low-latency"]),
            policy=self.policy(),
            readiness_overrides=self.ready("browser-use-browserless-v1"),
        )
        self.assertEqual(value["standing"], "SELECTED")
        self.assertEqual(value["selectedRoute"]["routeId"], "browser-use-browserless-v1")

    def test_visual_requirement_holds_when_visual_provider_is_not_materialized(self):
        value = R.plan_route(
            self.req(requiredFeatures=["visual-understanding"]),
            policy=self.policy(),
            readiness_overrides=self.ready(),
        )
        self.assertEqual(value["standing"], "HOLD_NO_READY_ROUTE")
        self.assertIsNone(value["selectedRoute"])

    def test_chatgpt_flow_does_not_mix_with_generic_routes(self):
        request = self.req(
            providerFlow="chatgpt_agent_automation",
            requiredFeatures=["provider-send-fence"],
        )
        value = R.plan_route(
            request,
            policy=self.policy(),
            readiness_overrides=self.ready("chatgpt-agent-automation-browserless-v1"),
        )
        self.assertEqual(
            value["selectedRoute"]["routeId"], "chatgpt-agent-automation-browserless-v1"
        )
        self.assertEqual(len(value["candidates"]), 1)

    def test_explicit_route_probes_only_the_exact_route(self):
        policy = self.policy()
        calls = []

        def probe(route, required):
            calls.append((route["routeId"], set(required)))
            if route["routeId"] == "jev-fast-windows-v1":
                raise AssertionError("sibling Jev route must not be probed")
            return {"ready": True, "standing": "READY"}

        with mock.patch.object(R, "probe_route", side_effect=probe):
            value = R.plan_route(
                self.req(explicitRouteId="browser-use-browserless-v1"),
                policy=policy,
            )
        self.assertEqual(value["standing"], "SELECTED")
        self.assertEqual(value["selectedRoute"]["routeId"], "browser-use-browserless-v1")
        self.assertEqual(
            calls,
            [("browser-use-browserless-v1", set())],
        )
        self.assertEqual(
            [row["routeId"] for row in value["candidates"]],
            ["browser-use-browserless-v1"],
        )

    def test_static_incompatible_exact_route_is_not_readiness_probed(self):
        with mock.patch.object(
            R,
            "probe_route",
            side_effect=AssertionError("incompatible route must not be probed"),
        ):
            value = R.plan_route(
                self.req(
                    requiredFeatures=["tabs"],
                    explicitRouteId="jev-fast-windows-v1",
                ),
                policy=self.policy(),
            )
        self.assertEqual(value["standing"], "HOLD_EXPLICIT_ROUTE_INCOMPATIBLE")
        self.assertEqual(len(value["candidates"]), 1)
        self.assertEqual(
            value["candidates"][0]["readiness"]["standing"],
            "NOT_PROBED_STATIC_INCOMPATIBLE",
        )

    def test_explicit_route_never_silently_falls_back(self):
        value = R.plan_route(
            self.req(explicitRouteId="jev-fast-windows-v1"),
            policy=self.policy(),
            readiness_overrides=self.ready("browser-use-browserless-v1"),
        )
        self.assertEqual(value["standing"], "HOLD_EXPLICIT_ROUTE_NOT_READY")
        self.assertIsNone(value["selectedRoute"])

    def test_incompatible_route_is_not_selected_even_if_ready(self):
        value = R.plan_route(
            self.req(requiredFeatures=["tabs"], explicitRouteId="jev-fast-windows-v1"),
            policy=self.policy(),
            readiness_overrides=self.ready("jev-fast-windows-v1"),
        )
        self.assertEqual(value["standing"], "HOLD_EXPLICIT_ROUTE_INCOMPATIBLE")

    def test_unknown_features_are_rejected_not_guessed(self):
        with self.assertRaisesRegex(ValueError, "unknown browser routing features"):
            R.plan_route(
                self.req(requiredFeatures=["magic-site-understanding"]),
                policy=self.policy(),
                readiness_overrides=self.ready(),
            )

    def test_plan_is_digest_stable_for_same_inputs(self):
        a = R.plan_route(
            self.req(),
            policy=self.policy(),
            readiness_overrides=self.ready("browser-use-browserless-v1"),
        )
        b = R.plan_route(
            self.req(),
            policy=self.policy(),
            readiness_overrides=self.ready("browser-use-browserless-v1"),
        )
        self.assertEqual(a["planDigest"], b["planDigest"])
        self.assertEqual(a["requestDigest"], b["requestDigest"])

    def test_jev_probe_requires_declared_credentials_without_exposing_values(self):
        route = next(x for x in self.policy()["routes"] if x["routeId"] == "jev-fast-windows-v1")
        fake_status = {
            "healthy": True,
            "chrome": {"version": "152"},
            "packages": {"jevVersion": "0.1.0", "browserHarnessVersion": "0.1.13"},
        }
        with (
            mock.patch.object(R, "_subprocess_json", return_value=(0, fake_status, "")),
            mock.patch.dict(R.os.environ, {}, clear=True),
        ):
            value = R._probe_jev(route, {"text-entry"})
        self.assertFalse(value["ready"])
        self.assertEqual(
            value["missingEnvironment"], ["TEXT_MODEL_API_KEY", "TYPESAFE_API_KEY"]
        )
        self.assertNotIn("secret", json.dumps(value).lower())

    def test_policy_is_browser_domain_local_not_global_registry(self):
        text = (ROOT / "scripts/browser_capability_router.py").read_text()
        self.assertIn("global_capability_registry", text)
        self.assertNotIn("HarnessProviderUsePolicy", text)


    def test_cold_browser_use_endpoint_is_ready_on_demand_without_starting_it(self):
        route = {
            "readiness": {
                "kind": "browser_use_browserless",
                "configPath": "/tmp/fake-browser-use.json",
            }
        }

        class Endpoint:
            endpoint_id = "browser-agent-22"
            service_unit = "ordivon-browserless@22.service"
            activation_unit = "ordivon-browser-agent.target"

            def health(self):
                raise AssertionError("cold activatable route must not health-probe inactive carrier")

        class Pool:
            endpoints = (Endpoint(),)

            @classmethod
            def from_dict(cls, _value):
                return cls()

        fake_config = {
            "browserUseExecutable": "/bin/true",
            "browserSubstrate": {"kind": "browserless", "endpoints": []},
        }

        def run(args, **_kwargs):
            if args[:2] == ["/usr/bin/systemctl", "is-enabled"]:
                return __import__("subprocess").CompletedProcess(args, 0, stdout="generated\n", stderr="")
            if args[:3] == ["/usr/bin/systemctl", "is-active", "--quiet"]:
                return __import__("subprocess").CompletedProcess(args, 3, stdout="", stderr="")
            if args[:4] == ["/usr/bin/systemctl", "show", "-p", "LoadState"]:
                return __import__("subprocess").CompletedProcess(args, 0, stdout="loaded\n", stderr="")
            raise AssertionError(args)

        with (
            mock.patch.object(R.Path, "is_file", return_value=True),
            mock.patch.object(R.os, "access", return_value=True),
            mock.patch.object(R, "_read_json", return_value=fake_config),
            mock.patch.dict(
                sys.modules,
                {"browserless_substrate": mock.Mock(BrowserlessPool=Pool)},
            ),
            mock.patch.object(R.subprocess, "run", side_effect=run),
        ):
            value = R._probe_browser_use(route)
        self.assertTrue(value["ready"])
        self.assertEqual(value["standing"], "READY_ON_DEMAND")
        self.assertEqual(value["activatableEndpointIds"], ["browser-agent-22"])
        self.assertEqual(value["healthyEndpointIds"], [])

class BrowserUseBindingTests(unittest.TestCase):
    def test_renderer_accepts_resolved_browser_use_executable(self):
        import browserless_podman_deploy as deploy

        binding = {
            "kind": "network-v2",
            "name": "browserless-prod",
            "namespace": "nv2-browserless-prod",
            "generationDigest": "sha256:" + "3" * 64,
            "serviceUnit": "network-v2-browserless.target",
            "receiptPath": "/receipt",
        }
        value = deploy.render_browser_use_config(
            binding, browser_use_executable="/opt/browser-use/bin/browser-use"
        )
        self.assertEqual(
            value["browserUseExecutable"], "/opt/browser-use/bin/browser-use"
        )

    def test_resolver_falls_back_to_uv_tool_environment(self):
        import browserless_podman_deploy as deploy

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            executable = root / "browser-use"
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o755)
            with (
                mock.patch.object(deploy.shutil, "which", return_value=None),
                mock.patch.object(Path, "home", return_value=root / "home"),
            ):
                expected = root / "home/.local/share/uv/tools/browser-use/bin/browser-use"
                expected.parent.mkdir(parents=True)
                expected.write_bytes(executable.read_bytes())
                expected.chmod(0o755)
                self.assertEqual(deploy.resolve_browser_use_executable(), str(expected.resolve()))


if __name__ == "__main__":
    unittest.main()


class BrowserUsePolicyReadinessTests(unittest.TestCase):
    def test_all_masked_browser_use_endpoints_are_policy_disabled_before_health_probe(self):
        route = {
            "readiness": {
                "kind": "browser_use_browserless",
                "configPath": "/tmp/fake-browser-use.json",
            }
        }

        class Endpoint:
            endpoint_id = "browser-agent-21"
            service_unit = "ordivon-browserless@21.service"

        class Pool:
            endpoints = (Endpoint(),)

            @classmethod
            def from_dict(cls, _value):
                return cls()

            def health(self):
                raise AssertionError("health probe must not run for operator-masked lane")

        fake_config = {
            "browserUseExecutable": "/bin/true",
            "browserSubstrate": {"kind": "browserless", "endpoints": []},
        }
        completed = __import__("subprocess").CompletedProcess(
            [], 1, stdout="masked\n", stderr=""
        )
        with (
            mock.patch.object(R.Path, "is_file", return_value=True),
            mock.patch.object(R, "_read_json", return_value=fake_config),
            mock.patch.dict(
                sys.modules,
                {"browserless_substrate": mock.Mock(BrowserlessPool=Pool)},
            ),
            mock.patch.object(R.subprocess, "run", return_value=completed),
        ):
            value = R._probe_browser_use(route)
        self.assertEqual(value["standing"], "POLICY_DISABLED")
        self.assertFalse(value["ready"])
        self.assertEqual(value["policyDisabledEndpointIds"], ["browser-agent-21"])
