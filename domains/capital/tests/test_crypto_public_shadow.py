from pathlib import Path
import json
import tempfile
import unittest

from market_capital.crypto_public_shadow import analyze


class CryptoPublicShadowTests(unittest.TestCase):
    def test_overlapping_capture_allows_bounded_comparison_but_blocks_private_on_clock_skew(self):
        base = 1_000_000_000_000
        def req(start_ms, end_ms, payload):
            return {
                "wallStartNs": base + start_ms * 1_000_000,
                "wallEndNs": base + end_ms * 1_000_000,
                "monotonicStartNs": start_ms * 1_000_000,
                "monotonicEndNs": end_ms * 1_000_000,
                "durationMs": end_ms - start_ms,
                "payload": payload,
            }
        capture = {
            "schemaVersion": 1,
            "kind": "ordivon.market-capital.crypto-public-rest-capture",
            "credentialsUsed": False,
            "privateAccountDataUsed": False,
            "externalFinancialWritesAttempted": False,
            "requests": {
                "okx_btc": req(0, 900, {"data": [{"bidPx":"100", "askPx":"101", "ts":"1000"}]}),
                "okx_eth": req(10, 910, {"data": [{"bidPx":"10", "askPx":"11", "ts":"1010"}]}),
                "binance_books": req(20, 920, [
                    {"symbol":"BTCUSDT", "bidPrice":"99", "askPrice":"100"},
                    {"symbol":"ETHUSDT", "bidPrice":"9", "askPrice":"10"},
                ]),
                "okx_time": req(0, 800, {"data": [{"ts":"-600"}]}),
                "binance_time": req(10, 810, {"serverTime": -590}),
            },
        }
        discovery = {
            "observationDigest":"sha256:test",
            "recommendedPathDigest":"sha256:path",
            "requiredTargets":["okx","binance"],
        }
        with tempfile.TemporaryDirectory() as td:
            c=Path(td)/"capture.json"; d=Path(td)/"discovery.json"
            c.write_text(json.dumps(capture)); d.write_text(json.dumps(discovery))
            out=analyze(c,d)
        self.assertTrue(out["capture"]["boundedContemporaneousComparisonAllowed"])
        self.assertFalse(out["clockQuality"]["hostClockWithinPrivateExecutionGate1000Ms"])
        self.assertEqual(out["standing"], "PASS_BOUNDED_DUAL_VENUE_PUBLIC_SHADOW_HOST_CLOCK_WARN")
        self.assertIn("BTC", out["comparisons"])


if __name__ == "__main__":
    unittest.main()
