import json
import tempfile
import unittest
from pathlib import Path

from ordivon_capital.markets.crypto_public_shadow import analyze


class CryptoPublicShadowTests(unittest.TestCase):
    def test_all_four_real_public_rest_quotes_reject_invalid_price_classes(self):
        import copy

        def req(start_ms, end_ms, payload):
            base = 1_000_000_000_000
            return {"wallStartNs": base + start_ms * 1_000_000,
                    "wallEndNs": base + end_ms * 1_000_000,
                    "monotonicStartNs": start_ms * 1_000_000,
                    "monotonicEndNs": end_ms * 1_000_000,
                    "durationMs": end_ms - start_ms, "payload": payload}

        capture = {
            "kind": "ordivon.capital.markets.crypto-public-rest-capture",
            "credentialsUsed": False, "privateAccountDataUsed": False,
            "externalFinancialWritesAttempted": False,
            "requests": {
                "okx_btc": req(0, 900, {"data": [{"bidPx": "100", "askPx": "101", "ts": "1000"}]}),
                "okx_eth": req(10, 910, {"data": [{"bidPx": "10", "askPx": "11", "ts": "1010"}]}),
                "binance_books": req(20, 920, [
                    {"symbol": "BTCUSDT", "bidPrice": "99", "askPrice": "100"},
                    {"symbol": "ETHUSDT", "bidPrice": "9", "askPrice": "10"}]),
                "okx_time": req(0, 800, {"data": [{"ts": "-600"}]}),
                "binance_time": req(10, 810, {"serverTime": -590}),
            },
        }
        binding = {
            "kind": "ordivon.capital.markets.network-v2-public-data-binding",
            "directFallback": False, "publicReadOnly": True,
            "authorities": {key: {"authorityDigest": "sha256:" + key}
                            for key in ("okxRest", "okxWs",
                                        "binanceSpotRest", "binanceSpotWs")},
            "brokerCredentialsUsed": False, "privateAccountDataUsed": False,
            "externalFinancialWritesAttempted": False,
            "demoExecutionAttempted": False, "liveExecutionAttempted": False,
        }
        invalid = (("crossed", "102", "101"), ("negative-bid", "-1", "101"),
                   ("negative-ask", "100", "-101"), ("zero", "0", "101"),
                   ("NaN", "NaN", "101"), ("Infinity", "Infinity", "101"),
                   ("malformed", "unavailable", "101"))
        quotes = (("okx_btc", 0, "bidPx", "askPx"),
                  ("okx_eth", 0, "bidPx", "askPx"),
                  ("binance_books", 0, "bidPrice", "askPrice"),
                  ("binance_books", 1, "bidPrice", "askPrice"))
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            raw, transport = directory / "capture.json", directory / "binding.json"
            transport.write_text(json.dumps(binding))
            raw.write_text(json.dumps(capture))
            self.assertTrue(analyze(raw, transport)["capture"][
                "boundedContemporaneousComparisonAllowed"])
            for venue, index, bid_key, ask_key in quotes:
                for label, bid, ask in invalid:
                    with self.subTest(venue=venue, index=index, invalid=label):
                        value = copy.deepcopy(capture)
                        payload = value["requests"][venue]["payload"]
                        entries = payload["data"] if venue.startswith("okx_") else payload
                        entries[index][bid_key] = bid
                        entries[index][ask_key] = ask
                        raw.write_text(json.dumps(value))
                        with self.assertRaisesRegex(ValueError, "public BBO|BBO must"):
                            analyze(raw, transport)

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
            "schemaVersion": 2,
            "kind": "ordivon.capital.markets.crypto-public-rest-capture",
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
            "schemaVersion":2,
            "kind":"ordivon.capital.markets.network-v2-public-data-binding",
            "bindingDigest":"sha256:test",
            "providerSelection":"sing-box-provider-auto",
            "directFallback":False,
            "publicReadOnly":True,
            "authorities":{k:{"authorityDigest":"sha256:"+k} for k in ("okxRest","okxWs","binanceSpotRest","binanceSpotWs")},
            "brokerCredentialsUsed":False,
            "privateAccountDataUsed":False,
            "externalFinancialWritesAttempted":False,
            "demoExecutionAttempted":False,
            "liveExecutionAttempted":False,
        }
        with tempfile.TemporaryDirectory() as td:
            c=Path(td)/"capture.json"; d=Path(td)/"network-v2-binding.json"
            c.write_text(json.dumps(capture)); d.write_text(json.dumps(discovery))
            out=analyze(c,d)
        self.assertTrue(out["capture"]["boundedContemporaneousComparisonAllowed"])
        self.assertFalse(out["clockQuality"]["hostClockWithinPrivateExecutionGate1000Ms"])
        self.assertEqual(out["standing"], "PASS_BOUNDED_DUAL_VENUE_PUBLIC_SHADOW_HOST_CLOCK_WARN")
        self.assertIn("BTC", out["comparisons"])
        self.assertEqual(out["transport"]["providerSelection"],"sing-box-provider-auto")
        self.assertFalse(out["transport"]["directFallback"])
        self.assertEqual(out["riskDataQuality"]["frameworkReference"], "BCBS239_PROPORTIONAL_REFERENCE")
        self.assertEqual(out["riskDataQuality"]["comparisonScope"], "BOUNDED_CONTEMPORANEOUS_BBO")
        self.assertTrue(out["riskDataQuality"]["requiredInputsComplete"])
        self.assertNotIn("sameCutScope", out)


if __name__ == "__main__":
    unittest.main()
