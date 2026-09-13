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

if __name__ == "__main__":
    unittest.main()
