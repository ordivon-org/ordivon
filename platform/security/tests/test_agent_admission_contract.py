"""Native Security Owner contract tests for the agent-to-effect admission seam.

The owner verifies with unittest discover. These cases exercise the
outcome partition ALLOW / STEP_UP / DENY through the actual OPA provider.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "contracts" / "agent-admission-v1" / "evaluate.py"
FIXTURE = ROOT / "fixtures" / "agent-admission" / "v0-allow.json"


def _run(payload: dict[str, object]) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(EVALUATOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


class AgentAdmissionContractTests(unittest.TestCase):
    """Provider/consumer obligation: an effect is projected only after ALLOW."""

    def assert_outcome(self, result: dict[str, object], outcome: str, reason: str) -> None:
        self.assertEqual(result["kind"], "ordivon.security.agent-admission-chain")
        self.assertEqual(result["agent"]["outcome"], outcome)
        self.assertEqual(result["agent"]["reason"], reason)
        if outcome != "ALLOW":
            self.assertIsNone(result["effect"])

    def test_public_contract_composes_agent_and_effect_admission(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = _run(payload)
        self.assert_outcome(result, "ALLOW", "admitted")
        self.assertIs(result["effect"]["admitted"], True)
        self.assertEqual(result["effect"]["requestId"], payload["effect"]["effectId"])

    def test_public_contract_preserves_step_up_without_effect_projection(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["effect"]["riskClass"] = "R4"
        payload["grant"]["maxRiskClass"] = "R4"
        payload["grant"]["stepUpAtOrAbove"] = "R4"
        payload["approval"] = {
            "verified": False,
            "principalId": None,
            "effectId": None,
            "method": None,
        }
        self.assert_outcome(_run(payload), "STEP_UP", "principal-step-up-required")

    def test_public_contract_denies_ungranted_action_without_effect_projection(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["grant"]["allowedActions"] = []
        self.assert_outcome(_run(payload), "DENY", "action-not-granted")


if __name__ == "__main__":
    unittest.main()
