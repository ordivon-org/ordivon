import json
import tempfile
import unittest
from pathlib import Path

from ordivon_capital.governance.policy_decision import (
    PolicyDecisionError,
    enforce_external_write,
    enforce_non_live,
    evaluate_execution_policy,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/execution_policy.json"


class ExecutionPolicyTests(unittest.TestCase):
    def test_external_write_policy_is_local_and_denied(self):
        result = evaluate_execution_policy(ROOT, CONFIG)
        self.assertEqual(result["externalWritePolicyStanding"], "NOT_ADMITTED")
        self.assertFalse(result["allowExternalWrite"])
        self.assertEqual(result["externalWriteVerifier"], "NOT_IMPLEMENTED")
        self.assertFalse(result["providerWriteCapabilityBound"])
        self.assertEqual(result["decisionImplementation"], "LOCAL_DETERMINISTIC_PYTHON")

    def test_non_live_gate_passes_fail_closed_contract(self):
        result = enforce_non_live(ROOT, CONFIG)
        self.assertEqual(result["standing"], "NON_LIVE_POLICY_ALLOWED")
        self.assertFalse(result["externalFinancialWritesAllowed"])

    def test_external_write_is_not_admitted(self):
        with self.assertRaisesRegex(PolicyDecisionError, "policy denied external financial write"):
            enforce_external_write(ROOT, CONFIG)

    def test_execution_lane_does_not_bypass_external_write_denial(self):
        result = evaluate_execution_policy(ROOT, CONFIG)
        self.assertTrue(result["allowNonLive"])
        self.assertFalse(result["allowExternalWrite"])
        with tempfile.TemporaryDirectory() as td:
            config = json.loads(CONFIG.read_text())
            config["currentLane"] = "EXTERNAL_WRITE"
            path = Path(td) / "policy.json"
            path.write_text(json.dumps(config))
            changed = evaluate_execution_policy(ROOT, path)
            self.assertFalse(changed["allowNonLive"])
            self.assertFalse(changed["allowExternalWrite"])

    def test_contract_path_escape_is_rejected(self):
        doc = json.loads(CONFIG.read_text())
        doc["externalWritePolicyInputContract"] = "../outside/contract.json"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "execution-policy.json"
            path.write_text(json.dumps(doc))
            with self.assertRaisesRegex(PolicyDecisionError, "escapes repository"):
                evaluate_execution_policy(ROOT, path)


if __name__ == "__main__":
    unittest.main()
