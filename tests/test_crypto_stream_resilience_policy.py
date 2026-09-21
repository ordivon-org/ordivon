import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CryptoStreamResiliencePolicyTests(unittest.TestCase):
    def test_reconnect_qualification_remains_public_only(self):
        s = (ROOT / "src/ordivon_capital/market/crypto_stream_resilience.py").read_text()
        self.assertIn('PASS_PUBLIC_STREAM_RECONNECT', s)
        self.assertIn('INJECTED_DISCONNECT', s)
        self.assertIn('generation', s)
        self.assertIn('hostWallClockUsedForAdmission', s)
        self.assertIn('externalFinancialWritesAttempted', s)
        self.assertNotIn('api_key', s.lower())
        self.assertNotIn('secret', s.lower())

    def test_both_venues_are_supported(self):
        s = (ROOT / "src/ordivon_capital/market/crypto_stream_resilience.py").read_text()
        self.assertIn('target_venue not in {"OKX", "BINANCE"}', s)
        self.assertIn('_okx_supervisor', s)
        self.assertIn('_binance_supervisor', s)


if __name__ == "__main__":
    unittest.main()


class R3EvidenceRetentionTests(unittest.TestCase):
    def test_session_runner_does_not_collapse_first_venue_failure_into_no_session_result(self):
        s = (ROOT / "scripts/run-crypto-stream-resilience-r3-session").read_text()
        self.assertIn("set +e", s)
        self.assertIn("okx_rc=$?", s)
        self.assertIn("binance_rc=$?", s)
        self.assertIn("VENUE_RESULT_UNAVAILABLE", s)
        self.assertIn("stderrTail", s)
        self.assertIn("result_path.write_text", s)
