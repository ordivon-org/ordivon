from __future__ import annotations
import asyncio
import json
import os
import sys
import tempfile
import unittest
import importlib.util
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if importlib.util.find_spec("mcp") is None:
    raise unittest.SkipTest(
        "exact Agent Automation MCP runtime is not installed in the Harness owner environment"
    )
os.environ["ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT"] = str(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
from agent_automation_mcp import McpSettings, build_server, _read_token, _transport_security  # noqa: E402


def config(root: Path):
    token = root / "browserless.token"
    token.write_text("secret-token-value-long-enough-for-test")
    return {
        "schemaVersion": 1,
        "stateRoot": str(root / "state"),
        "playwrightPython": "/venv/bin/python",
        "browserlessSubmitScript": str(ROOT / "scripts/playwright_browserless_chatgpt_submit.py"),
        "browserlessReconcileScript": str(
            ROOT / "scripts/playwright_browserless_binding_reconcile.py"
        ),
        "browserlessTurnScript": str(ROOT / "scripts/playwright_browserless_turn_once.py"),
        "browserlessPreflightScript": str(
            ROOT / "scripts/playwright_browserless_provider_preflight.py"
        ),
        "temporalPython": "/temporal/bin/python",
        "temporalLaunchScript": str(ROOT / "scripts/temporal_agent_automation_launch.py"),
        "temporalAddress": "127.0.0.1:7233",
        "temporalNamespace": "default",
        "temporalTaskQueue": "ordivon-agent-automation",
        "browserSubstrate": {
            "kind": "browserless",
            "endpoints": [
                {
                    "id": "carrier-a",
                    "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                    "httpEndpoint": "http://127.0.0.1:3011",
                    "tokenFile": str(token),
                }
            ],
        },
    }


class McpCatalogTests(unittest.TestCase):
    def test_catalog_is_semantic_and_has_no_spec_paths(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            cp = r / "config.json"
            cp.write_text(json.dumps(config(r)))
            tp = r / "token"
            tp.write_text("x" * 48)
            tp.chmod(0o600)
            s = build_server(McpSettings(config_file=cp, token_file=tp))
            tools = {t.name: t for t in s._tool_manager.list_tools()}
            expected = {
                "automation.doctor",
                "campaign.register",
                "campaign.inspect",
                "campaign.launch",
                "campaign.census",
                "occurrence.reconcile",
                "occurrence.humanHandoff",
                "occurrence.humanResume",
                "occurrence.continue",
                "provider.preflight",
            }
            self.assertEqual(set(tools), expected)
            reg = json.dumps(tools["campaign.register"].parameters, sort_keys=True)
            self.assertIn("CampaignSpecInput", reg)
            self.assertNotIn("specPath", reg)
            [
                self.assertNotIn(x, reg)
                for x in (
                    "campaignRevision",
                    "maxOccurrences",
                    "maxConcurrentBirths",
                    "occurrenceSlot",
                )
            ]
            self.assertNotIn("campaign.registerInquiry", tools)
            self.assertIn(
                "L1/L2 registration is unavailable", tools["campaign.register"].description
            )
            cont = json.dumps(tools["occurrence.continue"].parameters, sort_keys=True)
            self.assertIn("turnRequestId", cont)
            self.assertIn("prompt", cont)
            self.assertNotIn("promptFile", cont)
            self.assertIn("^[0-9a-f]{8}", cont)
            self.assertTrue(tools["campaign.census"].annotations.read_only_hint)
            self.assertTrue(tools["campaign.launch"].annotations.idempotent_hint)
            self.assertTrue(tools["campaign.launch"].annotations.open_world_hint)
            self.assertTrue(tools["provider.preflight"].annotations.read_only_hint)
            self.assertTrue(tools["provider.preflight"].annotations.open_world_hint)
            self.assertTrue(tools["occurrence.humanHandoff"].annotations.read_only_hint)
            self.assertFalse(tools["occurrence.humanResume"].annotations.read_only_hint)

    def test_register_then_census_through_registered_tool_functions(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            cp = r / "config.json"
            cp.write_text(json.dumps(config(r)))
            tp = r / "token"
            tp.write_text("x" * 48)
            tp.chmod(0o600)
            server = build_server(McpSettings(config_file=cp, token_file=tp))
            tools = {t.name: t for t in server._tool_manager.list_tools()}
            from agent_automation_mcp import CampaignSpecInput  # noqa: E402

            semantic = CampaignSpecInput(
                campaignId="campaign:structured",
                sharedPrompt="Do one bounded task.",
                roster=[{"agentId": "A01", "roleCard": "Verifier."}],
            )
            registered = asyncio.run(tools["campaign.register"].fn(spec=semantic))
            self.assertFalse(registered.is_error)
            ref = registered.structured_content["campaignRef"]
            self.assertRegex(ref, r"^sha256:[0-9a-f]{64}$")
            census = asyncio.run(tools["campaign.census"].fn(campaignRef=ref))
            self.assertFalse(census.is_error)
            self.assertEqual(census.structured_content["counts"]["unrecorded"], 1)
            self.assertNotIn("born", census.structured_content["counts"])
            replay = asyncio.run(tools["campaign.register"].fn(spec=semantic))
            self.assertEqual(replay.structured_content["campaignRef"], ref)
            self.assertEqual(replay.structured_content["disposition"], "existing")

    def test_reconcile_tool_admits_temporal_instead_of_direct_raw_reconcile(self):
        text = (ROOT / "scripts/agent_automation_mcp.py").read_text()
        self.assertIn("current_service().launch_reconcile", text)
        self.assertNotIn("_invoke(current_service().reconcile", text)

    def test_long_lived_server_reenters_current_config_for_each_tool_call(self):
        import agent_automation_mcp as module

        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            cp = r / "config.json"
            first = config(r)
            cp.write_text(json.dumps(first))
            tp = r / "token"
            tp.write_text("x" * 48)
            tp.chmod(0o600)
            server = build_server(McpSettings(config_file=cp, token_file=tp))
            tools = {t.name: t for t in server._tool_manager.list_tools()}

            def observe(self, endpoint_id):
                return {
                    "configuredEndpoint": self.config.browserless_pool.endpoints[0].endpoint_id,
                    "requestedEndpoint": endpoint_id,
                }

            with mock.patch.object(
                module.BrowserlessAutomationService, "provider_preflight", new=observe
            ):
                before = asyncio.run(
                    tools["provider.preflight"].fn(endpointId="probe")
                ).structured_content
                second = config(r)
                second["browserSubstrate"]["endpoints"][0]["id"] = "carrier-b"
                cp.write_text(json.dumps(second))
                after = asyncio.run(
                    tools["provider.preflight"].fn(endpointId="probe")
                ).structured_content
            self.assertEqual(before["configuredEndpoint"], "carrier-a")
            self.assertEqual(after["configuredEndpoint"], "carrier-b")

    def test_campaign_compile_derived_cache_is_not_a_current_mcp_surface(self):
        text = (ROOT / "scripts/agent_automation_mcp.py").read_text()
        self.assertNotIn('name="campaign.compile"', text)

    def test_shared_browser_substrate_has_no_release_or_retain_browser_compatibility_surface(self):
        text = (ROOT / "scripts/agent_automation_mcp.py").read_text()
        self.assertNotIn('name="occurrence.release"', text)
        self.assertNotIn("retainBrowser", text)

    def test_board_lifecycle_is_not_a_current_mcp_registration_or_tool_surface(self):
        text = (ROOT / "scripts/agent_automation_mcp.py").read_text()
        self.assertNotIn('lifecycleProtocol: Literal["board-v1"]', text)
        self.assertNotIn("boardTopic: str = Field", text)
        self.assertNotIn('name="campaign.lifecycle"', text)

    def test_mcp_backend_is_browserless_temporal_not_legacy_per_birth_browser(self):
        text = (ROOT / "scripts/agent_automation_mcp.py").read_text()
        unit = (ROOT / "systemd/ordivon-agent-automation-mcp.service").read_text()
        self.assertIn("BrowserlessAutomationService", text)
        self.assertNotIn("agent_automation_tool", text)
        self.assertIn("/etc/ordivon/agent-automation-browserless.json", unit)
        self.assertNotIn("/etc/ordivon/agent-automation.json", unit)

    def test_transport_security_keeps_rebinding_protection_with_loopback_allowlist(self):
        sec = _transport_security()
        self.assertTrue(sec.enable_dns_rebinding_protection)
        self.assertIn("127.0.0.1:*", sec.allowed_hosts)
        self.assertIn("http://127.0.0.1:*", sec.allowed_origins)

    def test_token_must_be_private_and_long(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "token"
            p.write_text("x" * 48)
            p.chmod(0o600)
            self.assertEqual(_read_token(p), "x" * 48)
            p.chmod(0o644)
            with self.assertRaises(RuntimeError):
                _read_token(p)

    def test_tool_execution_errors_use_problem_details_shape_without_legacy_envelope(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            cp = r / "config.json"
            cp.write_text(json.dumps(config(r)))
            tp = r / "token"
            tp.write_text("x" * 48)
            tp.chmod(0o600)
            server = build_server(McpSettings(config_file=cp, token_file=tp))
            tools = {t.name: t for t in server._tool_manager.list_tools()}
            result = asyncio.run(tools["campaign.inspect"].fn(campaignRef="not-a-ref"))
            self.assertTrue(result.is_error)
            value = result.structured_content
            self.assertEqual(set(value), {"detail"})
            self.assertIn("campaignRef", value["detail"])
            self.assertEqual(result.content[0].text, value["detail"])
            for removed in (
                "type",
                "title",
                "status",
                "schemaVersion",
                "kind",
                "code",
                "message",
                "retryClass",
                "commitState",
                "origin",
            ):
                self.assertNotIn(removed, value)

    def test_ambiguous_temporal_admission_is_fenced_as_unknown_effect(self):
        import agent_automation_mcp as module

        async def run():
            return await module._invoke(
                lambda: (_ for _ in ()).throw(
                    module.BrowserlessAutomationAmbiguous(
                        "receipt lost; observe same identity before retry"
                    )
                )
            )

        result = asyncio.run(run())
        self.assertTrue(result.is_error)
        value = result.structured_content
        self.assertEqual(set(value), {"detail", "effectCommitState"})
        self.assertEqual(value["effectCommitState"], "unknown")
        self.assertIn("observe same identity", value["detail"])
        self.assertEqual(result.content[0].text, value["detail"])
        self.assertNotIn("retryClass", value)
        self.assertNotIn("commitState", value)
        self.assertNotIn("status", value)

    def test_http_auth_problem_uses_rfc9457_media_type_and_members(self):
        import agent_automation_mcp as module

        sent = []

        async def send(message):
            sent.append(message)

        asyncio.run(
            module._http_problem(
                send, 401, "A valid Bearer credential is required.", authenticate=True
            )
        )
        start, body = sent
        headers = dict(start["headers"])
        value = json.loads(body["body"])
        self.assertEqual(start["status"], 401)
        self.assertEqual(headers[b"content-type"], b"application/problem+json")
        self.assertEqual(headers[b"www-authenticate"], b"Bearer")
        self.assertEqual(
            value,
            {
                "type": "about:blank",
                "title": "Unauthorized",
                "status": 401,
                "detail": "A valid Bearer credential is required.",
            },
        )


if __name__ == "__main__":
    unittest.main()
