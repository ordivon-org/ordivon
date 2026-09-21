import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/crypto_execution_lane.json"


class CryptoExecutionLaneTests(unittest.TestCase):
    def test_lane_is_public_data_only_candidate_fixture(self):
        cfg = json.loads(CONFIG.read_text())
        self.assertEqual(cfg["standing"], "SHADOW_PUBLIC_DATA_ONLY")
        self.assertEqual(cfg["marketModel"], "CONTINUOUS_24_7_CRYPTO_SPOT")
        self.assertTrue(cfg["publicMarketDataAllowed"])
        self.assertFalse(cfg["privateAccountDataAllowed"])
        self.assertFalse(cfg["demoExecutionAllowed"])
        self.assertFalse(cfg["liveExecutionAllowed"])
        self.assertFalse(cfg["brokerCredentialsAllowed"])
        self.assertFalse(cfg["externalFinancialWritesAllowed"])
        self.assertEqual(cfg["networkTransport"]["preferred"], "NETWORK_V2_EXACT_PUBLIC_AUTHORITIES")
        self.assertEqual(cfg["networkTransport"]["providerSelectionOwner"], "network-v2-sing-box-provider-auto")
        self.assertFalse(cfg["networkTransport"]["directFallback"])

    def test_nautilus_candidate_public_data_configs_construct_without_credentials(self):
        out = subprocess.check_output([str(ROOT / "tools/nautilus_rc4/check-crypto-execution-lane")], text=True)
        result = json.loads(out)
        self.assertEqual(result["standing"], "CRYPTO_DUAL_VENUE_PUBLIC_DATA_CONFIG_READY")
        self.assertFalse(result["venues"]["OKX"]["credentialsPresent"])
        self.assertFalse(result["venues"]["BINANCE"]["credentialsPresent"])
        self.assertFalse(result["externalFinancialWritesAllowed"])

    def test_equity_opening_semantics_are_not_reused(self):
        cfg = json.loads(CONFIG.read_text())
        joined = " ".join(cfg["rules"])
        self.assertIn("not reused", joined)
        self.assertIn("continuous-market semantics", joined)


if __name__ == "__main__":
    unittest.main()
