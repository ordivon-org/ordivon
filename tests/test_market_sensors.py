import unittest

from ordivon_capital.market.market_sensors import (
    MarketSensorError,
    merge_market_observations,
    open_interest_change,
    reconcile_underlying_reopen,
    repeated_microstructure,
)


class MarketSensorTests(unittest.TestCase):
    def test_open_interest_change_requires_ordered_same_instrument_window(self):
        result = open_interest_change([
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 1000, "openInterestUsd": "100"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 2000, "openInterestUsd": "110"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 3000, "openInterestUsd": "121"},
        ])
        self.assertEqual(result["openInterestChangeUsd"], "21.000000")
        self.assertEqual(result["openInterestChangePct"], "21.000000")
        self.assertEqual(result["sampleCount"], 3)

    def test_oi_zero_baseline_does_not_invent_percentage(self):
        result = open_interest_change([
            {"instrumentId": "X", "observedAtMs": 1000, "openInterestUsd": "0"},
            {"instrumentId": "X", "observedAtMs": 2000, "openInterestUsd": "10"},
        ])
        self.assertIsNone(result["openInterestChangePct"])

    def test_microstructure_requires_persistence_not_one_snapshot(self):
        rows = [
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 1000, "bookImbalance": "-0.2", "tradeBuyShare": "0.45", "spreadBps": "1.0"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 2000, "bookImbalance": "-0.1", "tradeBuyShare": "0.48", "spreadBps": "1.2"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 3000, "bookImbalance": "-0.3", "tradeBuyShare": "0.40", "spreadBps": "0.9"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 4000, "bookImbalance": "0.1", "tradeBuyShare": "0.51", "spreadBps": "1.1"},
        ]
        result = repeated_microstructure(rows)
        self.assertEqual(result["negativeBookImbalanceRatio"], "0.750000")
        self.assertEqual(result["tradeBuyShareBelowHalfRatio"], "0.750000")

    def test_mixed_microstructure_is_not_forced_directional(self):
        rows = [
            {"instrumentId": "X", "observedAtMs": 1000, "bookImbalance": "-0.2", "tradeBuyShare": "0.55", "spreadBps": "1"},
            {"instrumentId": "X", "observedAtMs": 2000, "bookImbalance": "0.2", "tradeBuyShare": "0.45", "spreadBps": "1"},
            {"instrumentId": "X", "observedAtMs": 3000, "bookImbalance": "-0.1", "tradeBuyShare": "0.52", "spreadBps": "1"},
        ]
        result = repeated_microstructure(rows)

    def test_reopen_pending_without_cash_observation(self):
        result = reconcile_underlying_reopen(
            instrument_id="SNDK-USDT-SWAP",
            weekend_perp_price="1740",
            weekend_observed_at_ms=1000,
        )
        self.assertEqual(result["standing"], "RECONCILIATION_PENDING")
        self.assertIsNone(result["validationToleranceBps"])
        self.assertIsNone(result["weekendToUnderlyingGapBps"])

    def test_reopen_requires_explicit_tolerance_after_underlying_observed(self):
        with self.assertRaises(MarketSensorError):
            reconcile_underlying_reopen(
                instrument_id="SNDK-USDT-SWAP",
                weekend_perp_price="1740",
                weekend_observed_at_ms=1000,
                underlying_reopen_price="1750",
                underlying_observed_at_ms=2000,
            )

    def test_reopen_underlying_can_validate_weekend_region(self):
        result = reconcile_underlying_reopen(
            instrument_id="SNDK-USDT-SWAP",
            weekend_perp_price="1740",
            weekend_observed_at_ms=1000,
            validation_tolerance_bps="100",
            underlying_reopen_price="1750",
            underlying_observed_at_ms=2000,
        )
        self.assertEqual(result["standing"], "UNDERLYING_VALIDATED_WEEKEND_REGION")
        self.assertLess(float(result["weekendToUnderlyingGapBps"]), 100)

    def test_perp_can_reanchor_to_underlying(self):
        result = reconcile_underlying_reopen(
            instrument_id="SNDK-USDT-SWAP",
            weekend_perp_price="1740",
            weekend_observed_at_ms=1000,
            validation_tolerance_bps="50",
            underlying_reopen_price="1650",
            underlying_observed_at_ms=2000,
            post_open_perp_price="1655",
            post_open_perp_observed_at_ms=2100,
        )
        self.assertEqual(result["standing"], "PERP_REANCHORED_TO_UNDERLYING")

    def test_partial_convergence_is_descriptive_only(self):
        result = reconcile_underlying_reopen(
            instrument_id="SNDK-USDT-SWAP",
            weekend_perp_price="1740",
            weekend_observed_at_ms=1000,
            validation_tolerance_bps="20",
            underlying_reopen_price="1650",
            underlying_observed_at_ms=2000,
            post_open_perp_price="1700",
            post_open_perp_observed_at_ms=2100,
        )
        self.assertEqual(result["standing"], "PARTIAL_CONVERGENCE")
        self.assertGreater(float(result["convergenceFraction"]), 0)

    def test_sensor_enrichment_binds_instrument_identity(self):
        market = {"instrumentId": "SNDK-USDT-SWAP", "last": "100"}
        oi = open_interest_change([
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 1000, "openInterestUsd": "100"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 2000, "openInterestUsd": "105"},
        ])
        micro = repeated_microstructure([
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 1000, "bookImbalance": "-0.2", "tradeBuyShare": "0.45", "spreadBps": "1"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 2000, "bookImbalance": "-0.1", "tradeBuyShare": "0.46", "spreadBps": "1"},
            {"instrumentId": "SNDK-USDT-SWAP", "observedAtMs": 3000, "bookImbalance": "-0.3", "tradeBuyShare": "0.44", "spreadBps": "1"},
        ])
        enriched = merge_market_observations(market, oi_change=oi, microstructure=micro)
        self.assertEqual(enriched["openInterestChangePct"], "5.000000")
        self.assertEqual(enriched["openInterestChangeSpanMs"], 1000)
        self.assertEqual(enriched["openInterestChangeSampleCount"], 2)
        self.assertEqual(enriched["microstructureSampleCount"], 3)
        self.assertEqual(enriched["negativeBookImbalanceRatio"], "1.000000")
        self.assertEqual(enriched["tradeBuyShareBelowHalfRatio"], "1.000000")

    def test_bad_timestamp_order_fails_closed(self):
        with self.assertRaises(MarketSensorError):
            open_interest_change([
                {"instrumentId": "X", "observedAtMs": 2000, "openInterestUsd": "100"},
                {"instrumentId": "X", "observedAtMs": 1000, "openInterestUsd": "110"},
            ])


if __name__ == "__main__":
    unittest.main()
