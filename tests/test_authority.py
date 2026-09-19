from pathlib import Path
import json
import tempfile
import unittest

from market_capital.authority import AuthorityError, evaluate_external_write, evaluate_non_live, verify_internal_authority

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/execution_authority.json"


class AuthorityTests(unittest.TestCase):
    def test_external_write_policy_is_opa_owned_and_denied(self):
        result = verify_internal_authority(ROOT, CONFIG)
        self.assertEqual(result["externalWritePolicyStanding"], "NOT_ADMITTED")
        self.assertFalse(result["externalWritePolicyAllowed"])
        self.assertEqual(result["externalWriteVerifier"], "NOT_IMPLEMENTED")
        self.assertFalse(result["providerWriteCapabilityBound"])
        self.assertEqual(result["policyEngine"], "OPA")

    def test_non_live_gate_passes_fail_closed_contract(self):
        result = evaluate_non_live(ROOT, CONFIG)
        self.assertEqual(result["standing"], "NON_LIVE_EFFECT_BOUNDARY")
        self.assertFalse(result["externalFinancialWritesAllowed"])

    def test_external_write_is_not_admitted(self):
        with self.assertRaisesRegex(AuthorityError, "external financial write policy denied"):
            evaluate_external_write(ROOT, CONFIG)

    def test_contract_path_escape_is_rejected(self):
        doc = json.loads(CONFIG.read_text())
        doc["policyEngine"]["policy"] = "../outside/policy.rego"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "authority.json"
            path.write_text(json.dumps(doc))
            with self.assertRaisesRegex(AuthorityError, "escapes repository"):
                verify_internal_authority(ROOT, path)


if __name__ == "__main__":
    unittest.main()
