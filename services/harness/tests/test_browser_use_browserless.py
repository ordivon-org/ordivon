from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class BrowserUseBrowserlessTests(unittest.TestCase):
    def binding(self):
        return {
            "kind": "network-v2",
            "name": "browserless-prod",
            "namespace": "nv2-browserless-prod",
            "generationDigest": "sha256:" + "3" * 64,
            "serviceUnit": "network-v2-browserless.target",
            "receiptPath": "/receipt",
        }

    def test_browser_use_pool_is_separate_from_agent_birth_pool(self):
        import browserless_podman_deploy as deploy

        birth = deploy.render_config(self.binding())
        browser = deploy.render_browser_use_config(
            self.binding(), browser_use_executable="/bin/true"
        )
        self.assertEqual(
            [x["id"] for x in birth["browserSubstrate"]["endpoints"]],
            ["chatgpt-carrier-11", "chatgpt-carrier-12", "chatgpt-carrier-13"],
        )
        self.assertEqual(
            [x["id"] for x in browser["browserSubstrate"]["endpoints"]], ["browser-agent-22"]
        )
        self.assertTrue(
            set(x["id"] for x in birth["browserSubstrate"]["endpoints"]).isdisjoint(
                x["id"] for x in browser["browserSubstrate"]["endpoints"]
            )
        )

    def test_launcher_rejects_non_browser_agent_endpoint(self):
        import browser_use_browserless as launcher

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            token = root / "token"
            token.write_text("x" * 32)
            cfg = root / "cfg.json"
            cfg.write_text(
                json.dumps(
                    {
                        "kind": "ordivon.browser-use-browserless-pool",
                        "browserUseExecutable": "/bin/true",
                        "browserSubstrate": {
                            "kind": "browserless",
                            "endpoints": [
                                {
                                    "id": "chatgpt-carrier-11",
                                    "websocketEndpoint": "ws://127.0.0.1:1/chromium",
                                    "httpEndpoint": "http://127.0.0.1:1",
                                    "tokenFile": str(token),
                                }
                            ],
                        },
                    }
                )
            )
            with self.assertRaisesRegex(ValueError, "browser-agent"):
                launcher.load_config(cfg)

    def test_generated_action_process_does_not_receive_token_bearing_cdp_env(self):
        import browser_use_browserless as launcher

        class Endpoint:
            endpoint_id = "browser-agent-21"

            def authenticated_operator_connection_endpoint(self, timeout_ms=None):
                return "ws://secret.example/chromium?token=TOPSECRET"

        calls = []

        def fake_run(executable, program, env, timeout=90):
            calls.append((program, env))
            return mock.Mock(returncode=0, stdout="ok\n", stderr="")

        with mock.patch.object(launcher, "_run_browser_use", side_effect=fake_run):
            rc = launcher._execute_generated(
                "/bin/browser-use", Endpoint(), "task:1", launcher.program_tabs()
            )
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2)
        self.assertIn("TOPSECRET", calls[0][1]["BU_CDP_WS"])
        self.assertNotIn("BU_CDP_WS", calls[1][1])
        self.assertNotIn("BU_CDP_URL", calls[1][1])
        self.assertEqual(calls[1][1]["BH_REQUIRE_EXISTING_DAEMON"], "1")

    def test_ensure_daemon_activates_explicit_cold_lane_before_cdp(self):
        import browser_use_browserless as launcher

        class Endpoint:
            endpoint_id = "browser-agent-22"
            activation_unit = "ordivon-browser-agent.target"

            def ensure_active(self, start_timeout_seconds=20.0):
                self.timeout = start_timeout_seconds
                return {"healthy": True, "lifecycleStarted": True}

            def authenticated_operator_connection_endpoint(self, timeout_ms=None):
                return "ws://127.0.0.1:13122/chromium?token=secret"

        endpoint = Endpoint()
        with mock.patch.object(
            launcher,
            "_run_browser_use",
            return_value=mock.Mock(returncode=0, stdout="{}", stderr=""),
        ) as run:
            launcher.ensure_daemon("/bin/browser-use", endpoint, "task:1")
        self.assertEqual(endpoint.timeout, 20.0)
        self.assertEqual(run.call_count, 1)

    def test_close_reclaims_explicit_cold_lane_only_after_session_close(self):
        import browser_use_browserless as launcher

        class Endpoint:
            endpoint_id = "browser-agent-22"
            idle_stop_units = (
                "ordivon-browser-agent.target",
                "ordivon-browserless@22.service",
            )

            def authenticated_operator_connection_endpoint(self, timeout_ms=None):
                return "ws://127.0.0.1:13122/chromium?token=secret"

            def release_if_idle(self):
                return {
                    "standing": "COLD",
                    "stoppedUnits": list(self.idle_stop_units),
                }

        with mock.patch.object(
            launcher.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout="", stderr=""),
        ):
            value = launcher.close_session("/bin/browser-use", Endpoint(), "task:1")
        self.assertEqual(value["standing"], "CLOSED")
        self.assertEqual(value["lifecycle"]["standing"], "COLD")

    def test_public_surface_is_structured_not_arbitrary_python(self):
        import browser_use_browserless as launcher

        text = (ROOT / "scripts/browser_use_browserless.py").read_text()
        self.assertNotIn("sys.stdin.read()", text)
        self.assertNotIn('sub.add_parser("run")', text)
        for action in (
            "open",
            "observe",
            "click",
            "input",
            "scroll",
            "back",
            "tabs",
            "close",
            "doctor",
        ):
            self.assertIn(f'add_parser("{action}")', text)
        click = launcher.program_click(2, "button", "Submit", 120)
        self.assertIn("affordance-changed", click)
        self.assertIn("Submit", click)
        with self.assertRaisesRegex(ValueError, "permits only"):
            launcher.program_open("file:///etc/passwd")

    def test_session_name_is_deterministic_and_safe(self):
        import browser_use_browserless as launcher

        a = launcher.session_name("task:paper1-A01")
        b = launcher.session_name("task:paper1-A01")
        self.assertEqual(a, b)
        self.assertRegex(a, r"^ordivon-bu-[0-9a-f]{24}$")
        with self.assertRaises(ValueError):
            launcher.session_name("../bad")

    def test_same_named_replacement_is_rejected_before_coordinate_effect(self):
        """An index + ARIA role/name is not an identity when duplicate nodes re-order."""
        import browser_use_browserless as launcher

        target = {"role": "button", "name": "Delete", "backendDOMNodeId": 107}
        current = {"role": "button", "name": "Delete", "backendDOMNodeId": 204}
        calls = []

        def cdp(method, **kwargs):
            if method == "Accessibility.getFullAXTree":
                return {
                    "nodes": [
                        {
                            "role": {"value": current["role"]},
                            "name": {"value": current["name"]},
                            "backendDOMNodeId": current["backendDOMNodeId"],
                        }
                    ]
                }
            if method == "DOM.getBoxModel":
                return {"model": {"content": [0, 0, 30, 0, 30, 30, 0, 30]}}
            raise AssertionError(method)

        def click_at_xy(x, y):
            calls.append((x, y))

        def wait(_secs):
            pass

        program = launcher.program_click(
            0, target["role"], target["name"], target["backendDOMNodeId"]
        )
        with self.assertRaisesRegex(AssertionError, "affordance-identity-changed"):
            exec(
                program,
                {
                    "cdp": cdp,
                    "click_at_xy": click_at_xy,
                    "wait": wait,
                    "page_info": lambda: {"url": "about:blank"},
                },
            )
        self.assertEqual(calls, [], "wrong duplicate must never receive the browser effect")

    def test_exact_backend_node_is_preserved_and_bool_rejected(self):
        import browser_use_browserless as launcher

        text = launcher.program_observe(include_text=False, max_chars=40)
        self.assertIn('"backendDOMNodeId"', text)

        program = launcher.program_click(0, "button", "Delete", 107)
        self.assertIn("backendDOMNodeId", program)
        self.assertIn("affordance-identity-changed", program)
        for bad in (True, 0, -1, "107", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                launcher.program_click(0, "button", "Delete", bad)

        # Strict default prevents silent legacy index-only clicks or text entry.
        with self.assertRaises(TypeError):
            launcher.program_click(0, "button", "Delete")
        with self.assertRaises(TypeError):
            launcher.program_input(0, "textbox", "Task", "value")

    def test_same_backend_node_can_execute_exactly_one_click(self):
        import browser_use_browserless as launcher

        effects = []

        def cdp(method, **kwargs):
            if method == "Accessibility.getFullAXTree":
                return {
                    "nodes": [
                        {
                            "role": {"value": "button"},
                            "name": {"value": "Delete"},
                            "backendDOMNodeId": 107,
                        }
                    ]
                }
            if method == "DOM.getBoxModel":
                return {"model": {"content": [0, 0, 30, 0, 30, 30, 0, 30]}}
            raise AssertionError(method)

        exec(
            launcher.program_click(0, "button", "Delete", 107),
            {
                "cdp": cdp,
                "click_at_xy": lambda x, y: effects.append((x, y)),
                "wait": lambda _secs: None,
                "page_info": lambda: {"url": "about:blank"},
            },
        )
        self.assertEqual(effects, [(15.0, 15.0)])


if __name__ == "__main__":
    unittest.main()
