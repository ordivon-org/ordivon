import unittest

from ordivon_capital.market.crypto_stream_health import StreamHealthPolicy, evaluate_stream_health


def row(source_ms: int, recv_ns: int):
    return {"sourceTimeMs": source_ms, "recvMonoNs": recv_ns, "bid": "100", "ask": "101"}


class CryptoStreamHealthTests(unittest.TestCase):
    def setUp(self):
        self.now = 10_000_000_000
        self.good = {
            "OKX:BTC": row(9000, 9_700_000_000),
            "OKX:ETH": row(9010, 9_710_000_000),
            "BINANCE:BTC": row(9100, 9_800_000_000),
            "BINANCE:ETH": row(9110, 9_810_000_000),
        }

    def test_healthy(self):
        x = evaluate_stream_health(self.good, now_mono_ns=self.now)
        self.assertEqual(x["standing"], "PASS_STREAM_HEALTHY")
        self.assertTrue(x["crossVenueObservationAllowed"])

    def test_missing_stream_fails_closed(self):
        latest = dict(self.good)
        latest.pop("BINANCE:ETH")
        x = evaluate_stream_health(latest, now_mono_ns=self.now)
        self.assertEqual(x["standing"], "BLOCK_MISSING_STREAM")
        self.assertFalse(x["crossVenueObservationAllowed"])

    def test_stale_stream_fails_closed(self):
        latest = dict(self.good)
        latest["OKX:BTC"] = row(9000, 1_000_000_000)
        x = evaluate_stream_health(latest, now_mono_ns=self.now)
        self.assertEqual(x["standing"], "BLOCK_STALE_STREAM")
        self.assertFalse(x["crossVenueObservationAllowed"])

    def test_time_divergence_fails_closed(self):
        latest = dict(self.good)
        latest["BINANCE:ETH"] = row(12_500, 9_810_000_000)
        x = evaluate_stream_health(latest, now_mono_ns=self.now)
        self.assertEqual(x["standing"], "BLOCK_TIME_DIVERGENCE")
        self.assertFalse(x["crossVenueObservationAllowed"])

    def test_policy_is_explicit(self):
        p = StreamHealthPolicy()
        self.assertEqual(p.max_receive_age_ms, 5000.0)
        self.assertEqual(p.max_source_span_ms, 1200.0)
        self.assertEqual(p.max_receive_span_ms, 1200.0)


if __name__ == "__main__":
    unittest.main()
