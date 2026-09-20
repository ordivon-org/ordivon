from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_automation_browserless as automation  # noqa: E402


def spec() -> dict:
    return {
        "campaignId": "campaign:reconcile-surface",
        "sharedPrompt": "Do bounded work.",
        "roster": [{"agentId": "A01", "roleCard": "Reviewer."}],
    }


def config(root: Path) -> dict:
    token = root / "token"
    token.write_text("secret")
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
        "browserlessHumanHandoffMs": 300000,
        "waitStableSeconds": 150,
        "browserlessSessionTimeoutMs": 480000,
        "browserSubstrate": {
            "kind": "browserless",
            "endpoints": [
                {
                    "id": "carrier-a",
                    "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                    "httpEndpoint": "http://127.0.0.1:3011",
                    "operatorHttpEndpoint": "http://127.0.0.1:13111",
                    "tokenFile": str(token),
                    "networkNamespace": "surfpath-test",
                }
            ],
        },
    }


class AgentAutomationReconcileSurfaceTests(unittest.TestCase):
    def test_cli_exposes_reconcile_not_birth(self) -> None:
        subparsers = next(
            action
            for action in automation.parser()._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        self.assertIn("reconcile", subparsers.choices)
        self.assertNotIn("birth", subparsers.choices)

    def test_service_and_mcp_expose_reconcile_without_birth_facade(self) -> None:
        self.assertFalse(hasattr(automation.BrowserlessAutomationService, "launch_occurrence"))
        mcp = (ROOT / "scripts/agent_automation_mcp.py").read_text()
        self.assertNotIn('name="occurrence.birth"', mcp)
        self.assertIn('name="materialization.reconcile"', mcp)

    def test_internal_execution_uses_materialization_not_birth_ontology(self) -> None:
        self.assertFalse((ROOT / "scripts/campaign_birth.py").exists())
        self.assertTrue((ROOT / "scripts/campaign_materialization.py").exists())
        sources = "".join(
            (ROOT / path).read_text()
            for path in (
                "scripts/temporal_agent_automation.py",
                "scripts/temporal_agent_automation_launch.py",
                "scripts/agent_automation_browserless_effects.py",
            )
        )
        for retired in (
            "AGENT_BIRTH_WORKFLOW",
            "BIRTH_ACTIVITY",
            "AgentBirthInput",
            "materialize_birth",
            "reconcile_birth",
            "campaign-birth",
            "agent-birth",
            "temporal-birth-admissions",
        ):
            self.assertNotIn(retired, sources)
        self.assertIn("MATERIALIZE_WORKFLOW", sources)
        self.assertIn("CAMPAIGN_MATERIALIZE_WORKFLOW", sources)
        for retired in (
            "OCCURRENCE_MATERIALIZE_WORKFLOW",
            "OccurrenceMaterializeWorkflow",
            "OccurrenceInput",
            "ordivon.occurrence.materialize",
        ):
            self.assertNotIn(retired, sources)
        self.assertIn("MATERIALIZE_ACTIVITY", sources)
        self.assertIn("MaterializationInput", sources)


    def test_reconcile_admits_unrecorded_occurrence_with_stable_temporal_identity(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sp = root / "spec.json"
            sp.write_text(json.dumps(spec()))
            service = automation.BrowserlessAutomationService(
                automation.BrowserlessAutomationConfig.from_dict(config(root))
            )
            census = {
                "campaignId": "campaign:reconcile-surface",
                "materializations": [
                    {
                        "agentId": "A01",
                        "materializationStanding": None,
                    }
                ],
            }
            admitted = {
                "workflowId": "wf-a",
                "workflowType": "ordivon.materialize",
                "disposition": "started",
            }
            with (
                mock.patch("agent_automation_browserless.campaign_census", return_value=census),
                mock.patch.object(service, "_require_materialization_substrate_available") as substrate,
                mock.patch.object(service, "_temporal_admit", return_value=admitted) as temporal,
            ):
                out = service.launch_reconcile(sp, "A01")

            substrate.assert_called_once()
            temporal.assert_called_once_with(sp, "materialize", agent_id="A01")
            self.assertEqual(out["agentId"], "A01")
            self.assertEqual(out["temporal"]["workflowId"], "wf-a")
            self.assertEqual(out["safeToResend"], False)


if __name__ == "__main__":
    unittest.main()
