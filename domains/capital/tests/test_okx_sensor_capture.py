import unittest
from unittest.mock import patch

from ordivon_capital.market.okx_sensor_capture import (
    OkxSensorCaptureError,
    capture_window,
    completed_open_interest_change,
    parse_open_interest_history,
    parse_round,
)


class OkxSensorCaptureTests(unittest.TestCase):
    def test_parse_round_derives_bounded_observations(self):
        result = parse_round(
            instrument_id="SNDK-USDT-SWAP",
            observed_at_ms=5000,
            open_interest_payload={
                "code": "0",
                "data": [{"instId": "SNDK-USDT-SWAP", "oiUsd": "1000", "ts": "4900"}],
            },
            books_payload={
                "code": "0",
                "data": [{
                    "ts": "4950",
                    "bids": [["99", "2", "0", "1"], ["98", "1", "0", "1"]],
                    "asks": [["101", "1", "0", "1"]],
                }],
            },
            trades_payload={
                "code": "0",
                "data": [
                    {"instId": "SNDK-USDT-SWAP", "side": "buy", "sz": "3", "ts": "4960"},
                    {"instId": "SNDK-USDT-SWAP", "side": "sell", "sz": "1", "ts": "4970"},
                ],
            },
            ticker_payload={
                "code": "0",
                "data": [{
                    "instId": "SNDK-USDT-SWAP",
                    "last": "100",
                    "bidPx": "99",
                    "askPx": "101",
                    "ts": "4980",
                }],
            },
        )
        self.assertEqual(result["openInterest"]["openInterestUsd"], "1000")
        self.assertEqual(result["microstructure"]["bookImbalance"], "0.5")
        self.assertEqual(result["microstructure"]["tradeBuyShare"], "0.75")
        self.assertEqual(result["marketReference"]["last"], "100")
        self.assertEqual(result["observedAtMs"], 5000)

    def test_oi_history_uses_only_completed_buckets(self):
        payload = {
            "code": "0",
            "data": [
                ["1800000", "0", "0", "130"],
                ["1500000", "0", "0", "120"],
                ["1200000", "0", "0", "110"],
                ["900000", "0", "0", "100"],
            ],
        }
        parsed = parse_open_interest_history(instrument_id="X", payload=payload)
        self.assertEqual(
            [x["observedAtMs"] for x in parsed],
            [900000, 1200000, 1500000, 1800000],
        )

        result = completed_open_interest_change(
            instrument_id="X",
            payload=payload,
            period_ms=300000,
            as_of_ms=1750000,
        )
        self.assertEqual(result["startObservedAtMs"], 900000)
        self.assertEqual(result["endObservedAtMs"], 1200000)
        self.assertEqual(result["openInterestChangePct"], "10.000000")
        self.assertTrue(result["completedBucketsOnly"])

    def test_capture_window_uses_descriptive_microstructure_without_retired_persistence_heuristic(self):
        rows = [
            {
                "observedAtMs": 1000 + i,
                "openInterest": {"instrumentId": "X", "observedAtMs": 1000 + i, "openInterestUsd": str(100 + i)},
                "microstructure": {
                    "instrumentId": "X",
                    "observedAtMs": 1000 + i,
                    "bookImbalance": "0",
                    "tradeBuyShare": "0.5",
                    "spreadBps": "1",
                },
                "marketReference": {"instrumentId": "X", "observedAtMs": 1000 + i},
            }
            for i in range(3)
        ]
        with (
            patch("ordivon_capital.market.okx_sensor_capture.capture_round", side_effect=rows),
            patch("ordivon_capital.market.okx_sensor_capture._request", return_value={}),
            patch("ordivon_capital.market.okx_sensor_capture.completed_open_interest_change", return_value={}),
            patch(
                "ordivon_capital.market.okx_sensor_capture.repeated_microstructure",
                return_value={"componentId": "repeated-microstructure-summary"},
            ) as summarize,
        ):
            result = capture_window(
                instrument_id="X",
                proxy="http://127.0.0.1:19283",
                rounds=3,
                interval_seconds=0,
            )
        self.assertEqual(result["standing"], "PASS_OKX_REPEATED_SENSOR_WINDOW")
        summarize.assert_called_once()
        self.assertEqual(summarize.call_args.kwargs, {"minimum_samples": 3})

    def test_parse_round_rejects_provider_error(self):
        with self.assertRaises(OkxSensorCaptureError):
            parse_round(
                instrument_id="X",
                observed_at_ms=1,
                open_interest_payload={"code": "1", "data": []},
                books_payload={"code": "0", "data": [{}]},
                trades_payload={"code": "0", "data": [{}]},
                ticker_payload={"code": "0", "data": [{}]},
            )


if __name__ == "__main__":
    unittest.main()
