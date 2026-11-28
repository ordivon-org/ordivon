from __future__ import annotations

import sys
import unittest
from importlib import import_module
from itertools import product
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[3]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

R = import_module("catalogs.capabilities.routing.web_interaction_route")
CENSUS = import_module("catalogs.capabilities.routing.web_provider_census")

AVAILABLE = {
    "native_connector": {"state": "caller_bound", "reason": "x"},
    "direct_http": {"state": "available", "reason": "x"},
    "firecrawl": {"state": "unavailable", "reason": "x"},
    "playwright": {"state": "available", "reason": "x"},
    "browser_use": {"state": "available", "reason": "x"},
    "computer_use": {"state": "caller_bound", "reason": "x"},
}


class WebInteractionRouteTests(unittest.TestCase):
    def resolve(self, needs, caller=()):
        with mock.patch.object(R, "census", return_value=AVAILABLE):
            return R.resolve(needs, caller_available=caller)

    def test_plain_read_uses_http_not_browser(self):
        d = self.resolve(R.TaskNeeds())
        self.assertEqual(d["selectedRoute"], "direct_http")

    def test_native_connector_precedes_other_routes_when_caller_proves_it(self):
        d = self.resolve(
            R.TaskNeeds(native_provider_available=True), ("native_connector",)
        )
        self.assertEqual(d["selectedRoute"], "native_connector")

    def test_site_scale_prefers_firecrawl_only_when_actually_available(self):
        a = dict(AVAILABLE)
        a["firecrawl"] = {"state": "available", "reason": "x"}
        with mock.patch.object(R, "census", return_value=a):
            d = R.resolve(R.TaskNeeds(site_scale_web_acquisition=True))
        self.assertEqual(d["selectedRoute"], "firecrawl")

    def test_studied_but_unavailable_firecrawl_does_not_silently_shrink_site_scale_task(
        self,
    ):
        d = self.resolve(R.TaskNeeds(site_scale_web_acquisition=True))
        self.assertIsNone(d["selectedRoute"])
        self.assertEqual(d["standing"], "NO_ADMITTED_PROVIDER")
        self.assertEqual(d["considered"][0]["route"], "firecrawl")
        self.assertEqual(d["considered"][0]["standing"], "not_available")

    def test_known_browser_flow_uses_available_playwright(self):
        d = self.resolve(
            R.TaskNeeds(requires_interaction=True, deterministic_browser_flow=True)
        )
        self.assertEqual(d["selectedRoute"], "playwright")

    def test_known_browser_flow_accepts_caller_admitted_playwright(self):
        a = dict(AVAILABLE)
        a["playwright"] = {"state": "task_local", "reason": "x"}
        with mock.patch.object(R, "census", return_value=a):
            d = R.resolve(
                R.TaskNeeds(requires_interaction=True, deterministic_browser_flow=True),
                caller_available=("playwright",),
            )
        self.assertEqual(d["selectedRoute"], "playwright")

    def test_known_browser_flow_falls_to_browser_use_when_playwright_unavailable(self):
        a = dict(AVAILABLE)
        a["playwright"] = {"state": "unavailable", "reason": "x"}
        with mock.patch.object(R, "census", return_value=a):
            d = R.resolve(
                R.TaskNeeds(requires_interaction=True, deterministic_browser_flow=True)
            )
        self.assertEqual(d["selectedRoute"], "browser_use")

    def test_adaptive_browser_prefers_agent_driven_playwright(self):
        d = self.resolve(
            R.TaskNeeds(requires_interaction=True, adaptive_browser_reasoning=True)
        )
        self.assertEqual(d["selectedRoute"], "playwright")

    def test_adaptive_browser_falls_back_only_when_playwright_unavailable(self):
        a = dict(AVAILABLE)
        a["playwright"] = {"state": "unavailable", "reason": "x"}
        with mock.patch.object(R, "census", return_value=a):
            d = R.resolve(
                R.TaskNeeds(requires_interaction=True, adaptive_browser_reasoning=True)
            )
        self.assertEqual(d["selectedRoute"], "browser_use")

    def test_adaptive_browser_without_executor_has_no_route(self):
        a = dict(AVAILABLE)
        for key in ("playwright", "browser_use"):
            a[key] = {"state": "unavailable", "reason": "x"}
        with mock.patch.object(R, "census", return_value=a):
            d = R.resolve(
                R.TaskNeeds(requires_interaction=True, adaptive_browser_reasoning=True)
            )
        self.assertEqual(d["standing"], "NO_ADMITTED_PROVIDER")
        self.assertIsNone(d["selectedRoute"])

    def test_browser_use_census_rejects_missing_or_optional_identity_contract(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "config.json"
            cfg.write_text(json.dumps({"browserSubstrate": {"endpoints": [
                {"id": "browser-agent-test"}
            ]}}))
            adapter = Path(td) / "adapter.py"
            for click, input_ in ((None, None), (True, None), (True, False), (True, True)):
                with self.subTest(click=click, input=input_):
                    adapter.write_text(
                        "import argparse,json\n"
                        "p=argparse.ArgumentParser()\n"
                        "p.add_argument('--session-id')\n"
                        "sub=p.add_subparsers(dest='cmd', required=True)\n"
                        "sub.add_parser('doctor')\n"
                        "for name, required in " + repr((("click", click), ("input", input_))) + ":\n"
                        "    action=sub.add_parser(name)\n"
                        "    if required is not None:\n"
                        "        action.add_argument('--expect-backend-dom-node-id', type=int, required=required)\n"
                        "p.parse_args()\n"
                        "print(json.dumps({'browserlessHealth': {'healthy': True}}))\n"
                    )
                    with mock.patch.object(CENSUS, "BROWSER_USE_CONFIG", cfg), mock.patch.object(
                        CENSUS, "BROWSER_USE_ACTION", adapter
                    ):
                        result = CENSUS._browser_use_health()
                    self.assertEqual(
                        result["state"], "available" if click is True and input_ is True else "unavailable"
                    )

    def test_desktop_requires_explicit_caller_capability(self):
        needs = R.TaskNeeds(requires_interaction=True, requires_desktop_gui=True)
        d = self.resolve(needs)
        self.assertEqual(d["standing"], "NO_ADMITTED_PROVIDER")
        d = self.resolve(needs, ("computer_use",))
        self.assertEqual(d["selectedRoute"], "computer_use")

    def test_playwright_health_accepts_complete_workstation_binding(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            tool = Path(td) / "binding"
            tool.write_text(
                '#!/bin/sh\necho \'{"state":"AVAILABLE","bindingDigest":"sha256:x","commandPrefix":["/usr/bin/node","/opt/pw.js"],"environment":{"PLAYWRIGHT_BROWSERS_PATH":"/cache"},"identity":{"browserExecutableDigest":"sha256:b","cliEntrypointDigest":"sha256:c"}}\'\n'
            )
            tool.chmod(0o755)
            with mock.patch.object(CENSUS, "PLAYWRIGHT_BINDING", tool):
                value = CENSUS._playwright_health()
        self.assertEqual(value["state"], "available")
        self.assertEqual(value["bindingTool"], str(tool))

    def test_invalid_mixed_browser_semantics_rejected(self):
        with self.assertRaises(ValueError):
            R.TaskNeeds(
                requires_interaction=True,
                deterministic_browser_flow=True,
                adaptive_browser_reasoning=True,
            )

    def test_caller_cannot_invent_browser_use_availability(self):
        with self.assertRaises(ValueError):
            self.resolve(R.TaskNeeds(), ("browser_use",))


# Independent finite-domain contract: cognition selects actions, not a carrier.
# Readiness here is a synthetic availability observation, neither permission
# to execute nor a domain completion witness.
class RouteBehaviorSpec(unittest.TestCase):
    def test_cognition_is_orthogonal_to_interactive_carrier(self):
        for direct, fallback, native_requested, native_available, caller_pw in product(
            (False, True), repeat=5
        ):
            availability = {
                name: {"state": "unavailable", "reason": "synthetic"}
                for name in AVAILABLE
            }
            if direct:
                availability["playwright"]["state"] = "available"
            if fallback:
                availability["browser_use"]["state"] = "available"
            caller = tuple(
                name
                for name, present in (
                    ("native_connector", native_available),
                    ("playwright", caller_pw),
                )
                if present
            )
            expected = next(
                (
                    route
                    for route, adequate in (
                        ("native_connector", native_requested and native_available),
                        ("playwright", direct or caller_pw),
                        ("browser_use", fallback),
                    )
                    if adequate
                ),
                None,
            )
            with mock.patch.object(R, "census", return_value=availability):
                for deterministic, adaptive in ((True, False), (False, True), (False, False)):
                    with self.subTest(
                        direct=direct,
                        fallback=fallback,
                        native_requested=native_requested,
                        native_available=native_available,
                        caller_pw=caller_pw,
                        deterministic=deterministic,
                        adaptive=adaptive,
                    ):
                        decision = R.resolve(
                            R.TaskNeeds(
                                native_provider_available=native_requested,
                                requires_interaction=True,
                                deterministic_browser_flow=deterministic,
                                adaptive_browser_reasoning=adaptive,
                            ),
                            caller_available=caller,
                        )
                        self.assertEqual(decision["selectedRoute"], expected)
                        self.assertEqual(
                            decision["standing"],
                            "ROUTED" if expected else "NO_ADMITTED_PROVIDER",
                        )
                        self.assertEqual(decision["semanticSelector"], "agent_or_caller")
                        self.assertEqual(decision["completionAuthority"], "owning_domain")
                        self.assertEqual(
                            sum(x["standing"] == "selected" for x in decision["considered"]),
                            int(expected is not None),
                        )

    def test_primary_intent_cannot_silently_fall_back_to_browser(self):
        availability = {
            name: {
                "state": "available" if name in ("playwright", "browser_use") else "unavailable",
                "reason": "synthetic",
            }
            for name in AVAILABLE
        }
        desktop = R.TaskNeeds(requires_interaction=True, requires_desktop_gui=True)
        acquisition = R.TaskNeeds(site_scale_web_acquisition=True)
        for needs, caller, expected in (
            (R.TaskNeeds(), (), None),
            (acquisition, (), None),
            (desktop, (), None),
            (desktop, ("computer_use",), "computer_use"),
            (acquisition, ("firecrawl",), "firecrawl"),
        ):
            with self.subTest(needs=needs, caller=caller):
                with mock.patch.object(R, "census", return_value=availability):
                    decision = R.resolve(needs, caller_available=caller)
                self.assertEqual(decision["selectedRoute"], expected)
                self.assertEqual(decision["completionAuthority"], "owning_domain")


if __name__ == "__main__":
    unittest.main()
