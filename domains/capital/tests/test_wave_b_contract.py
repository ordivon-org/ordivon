import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WaveBContractTests(unittest.TestCase):
    def test_target_fixture_is_exact_wave_a_artifact(self):
        p = ROOT / "wave_b/fixtures/wave_a_target_portfolio.json"
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), "137265667683455c302adff94466eaf38444ed7d51b5959c4ad065505792c14d")
        doc = json.loads(p.read_text())
        self.assertEqual(doc["method"], "equal_weight_validation_research_gated")
        self.assertEqual({x["symbol"] for x in doc["positions"]}, {"AAPL", "MSFT", "NVDA"})
        self.assertAlmostEqual(sum(x["target_weight"] for x in doc["positions"]), 1.0)

    def test_lean_runtime_is_non_live(self):
        doc = json.loads((ROOT / "config/lean_runtime.json").read_text())
        self.assertEqual(doc["mode"], "historical-validation-only")
        self.assertFalse(doc["brokerCredentialsAllowed"])
        self.assertFalse(doc["externalFinancialWritesAllowed"])
        self.assertEqual(doc["productionStanding"], "NOT_ADMITTED")

    def test_execution_feasibility_is_non_live_and_has_buffer(self):
        doc = json.loads((ROOT / "config/execution_feasibility.json").read_text())
        self.assertEqual(doc["orderSizingOwner"], "QuantConnect LEAN CalculateOrderQuantity / buying-power model")
        self.assertGreater(doc["executionCashBufferWeight"], 0)
        self.assertLess(doc["executionCashBufferWeight"], 1)
        self.assertFalse(doc["externalFinancialWritesAllowed"])

    def test_m3_historical_validation_data_is_scoped_and_non_live(self):
        doc = json.loads((ROOT / "config/historical_validation_data.json").read_text())
        self.assertEqual(doc["provider"], "Nasdaq")
        self.assertEqual(doc["validationPurpose"], "EXECUTION_MECHANICS_AND_DATA_PLUMBING")
        self.assertFalse(doc["strategyPerformanceInferenceAllowed"])
        self.assertEqual(doc["riskDataReference"], "BCBS239_PROPORTIONAL_REFERENCE")
        self.assertEqual(doc["symbols"], ["AAPL", "MSFT", "NVDA"])
        self.assertFalse(doc["externalFinancialWritesAllowed"])

    def test_fix44_order_semantics_are_standard_and_non_live(self):
        doc = json.loads((ROOT / "config/fix_order_semantics.json").read_text())
        self.assertEqual(doc["protocol"], "FIX.4.4")
        self.assertEqual(doc["messageType"], "D")
        self.assertEqual(doc["messageName"], "NewOrderSingle")
        self.assertEqual(doc["packages"]["QuickFIXn.FIX44"], "1.14.1")
        self.assertFalse(doc["sessionNetworkEnabled"])
        self.assertFalse(doc["brokerCredentialsAllowed"])
        self.assertFalse(doc["externalFinancialWritesAllowed"])

    def test_m5_prospective_validation_is_fail_closed_and_non_live(self):
        doc = json.loads((ROOT / "config/prospective_validation.json").read_text())
        self.assertEqual(doc["postDecisionRule"], "session_date_strictly_after_decision_date_in_session_timezone")
        self.assertEqual(doc["alignedSessionRule"], "all_required_series_must_contain_the_same_post_decision_session_date")
        self.assertNotIn("fix44Required", doc)
        self.assertNotIn("executionFeasibilityRequired", doc)
        self.assertFalse(doc["brokerCredentialsAllowed"])
        self.assertFalse(doc["externalFinancialWritesAllowed"])

    def test_m6_shadow_precommit_is_plan_only_and_non_live(self):
        doc = json.loads((ROOT / "config/shadow_precommit.json").read_text())
        self.assertEqual(doc["pricingSessionDate"], "2026-09-11")
        self.assertEqual(doc["pricingStanding"], "PRE_DECISION_PROVIDER_ORIGIN_SNAPSHOT")
        self.assertEqual(doc["fixTimeInForce"], "AT_THE_OPENING")
        self.assertEqual(doc["executionTrigger"], "first_eligible_post_decision_session_open")
        self.assertTrue(doc["planOnly"])
        self.assertFalse(doc["brokerCredentialsAllowed"])
        self.assertFalse(doc["externalFinancialWritesAllowed"])

if __name__ == "__main__":
    unittest.main()
