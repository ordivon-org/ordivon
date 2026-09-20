from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AgentAutomationJcsStandardTests(unittest.TestCase):
    def test_temporal_runtime_contract_pins_rfc8785(self) -> None:
        requirements = (ROOT / "config/agent-automation-temporal-requirements.txt").read_text()
        self.assertIn("rfc8785==0.1.4", requirements.splitlines())

    def test_effect_identity_uses_rfc8785_not_hand_rolled_json_sorting(self) -> None:
        for relative in (
            "scripts/campaign_materialization.py",
            "scripts/conversation_relay_carrier.py",
        ):
            source = (ROOT / relative).read_text()
            self.assertIn("import rfc8785", source)
            tree = ast.parse(source)
            funcs = {
                node.name: ast.get_source_segment(source, node) or ""
                for node in tree.body
                if isinstance(node, ast.FunctionDef)
            }
            canonical = funcs.get("canonical_digest") or funcs.get("_canonical_digest")
            self.assertIsNotNone(canonical)
            self.assertIn("rfc8785.dumps", canonical)
            self.assertNotIn("json.dumps", canonical)

    def test_release_preflight_verifies_exact_temporal_runtime_versions(self) -> None:
        source = (ROOT / "scripts/agent_automation_release.py").read_text()
        self.assertIn('"temporalio": "1.32.0"', source)
        self.assertIn('"rfc8785": "0.1.4"', source)
        self.assertIn("worker runtime dependency versions differ", source)

    def test_temporal_deployer_verifies_exact_rfc8785_version(self) -> None:
        source = (ROOT / "scripts/temporal_agent_automation_deploy.py").read_text()
        self.assertIn('"rfc8785": "0.1.4"', source)
        self.assertIn('"temporalio": "1.32.0"', source)


if __name__ == "__main__":
    unittest.main()
