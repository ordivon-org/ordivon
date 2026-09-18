import unittest

from market_capital.regime_card import RegimeCardError, build_regime_card


class RegimeCardTests(unittest.TestCase):
    def market(self):
        return {
            "instrumentId": "TEST-USDT-SWAP",
            "observedAtMs": 1000,
            "last": "110",
            "mark": "109.9",
            "index": "110.0",
            "open24h": "100",
            "high24h": "112",
            "low24h": "98",
            "fundingCurrent": "0",
            "fundingRecentMean": "0.0001",
            "openInterestUsd": "1000000",
            "bookImbalance": "-0.2",
            "tradeBuyShare": "0.45",
            "technical": {
                "1H": {"rsi14": "78"},
                "4H": {"rsi14": "82"},
                "1D": {"rsi14": "52"},
            },
        }

    def test_weekend_regime_is_explicit_and_non_predictive(self):
        card = build_regime_card(
            market=self.market(),
            context={"underlyingMarketOpen": False, "indexSourceMode": "OUT_OF_HOURS"},
        )
        self.assertEqual(card["regimeIdentity"], "DERIVATIVE_LED_OUT_OF_HOURS_DISCOVERY")
        self.assertEqual(card["truthRole"], "analysis-evidence-not-forecast-truth")
        self.assertFalse(card["forecastProbabilityProduced"])
        self.assertFalse(card["tradeRecommendationProduced"])
        self.assertFalse(card["externalFinancialWriteAttempted"])
        self.assertEqual(card["causalStanding"], "NOT_IDENTIFIED_FROM_OBSERVATIONAL_CARD")

    def test_divergence_is_recorded_without_calling_reversal(self):
        card = build_regime_card(
            market=self.market(),
            context={"underlyingMarketOpen": False, "indexSourceMode": "OUT_OF_HOURS"},
        )
        self.assertIn("PRICE_UP_WHILE_BOOK_IMBALANCE_NEGATIVE", card["divergences"])
        self.assertIn("PRICE_UP_WHILE_RECENT_TRADE_BUY_SHARE_BELOW_HALF", card["divergences"])
        self.assertIn("SHORT_HORIZON_MOMENTUM_EXTENDED_WITHOUT_DAILY_EXTENSION", card["divergences"])

    def test_missing_oi_change_prevents_false_crowding_conclusion(self):
        card = build_regime_card(
            market=self.market(),
            context={"underlyingMarketOpen": False, "indexSourceMode": "OUT_OF_HOURS"},
        )
        self.assertEqual(card["crowding"]["standing"], "NOT_IDENTIFIED_MISSING_OI_CHANGE")
        self.assertIn("OPEN_INTEREST_CHANGE_MISSING", card["evidenceGaps"])

    def test_position_signposts_are_arithmetic_not_orders(self):
        card = build_regime_card(
            market=self.market(),
            context={"underlyingMarketOpen": True, "indexSourceMode": "TRADFI_OPEN"},
            position={
                "quantity": "0.1",
                "averagePrice": "100",
                "leverage": "5",
                "marginMode": "cross",
                "liquidationPrice": "75",
            },
            signposts={"recentHigh": "120", "trendMean": "105"},
        )
        by_name = {row["name"]: row for row in card["signposts"]}
        self.assertEqual(by_name["recentHigh"]["approxGrossPositionPnlAtLevel"], "2.000000")
        self.assertEqual(by_name["trendMean"]["approxGrossPositionPnlAtLevel"], "0.500000")
        self.assertEqual(card["positionProjection"]["approxGrossPnlAtLast"], "1.000000")
        self.assertFalse(card["tradeRecommendationProduced"])
        self.assertNotIn("H2_OUT_OF_HOURS_DERIVATIVE_DISLOCATION", {h["id"] for h in card["competingHypotheses"]})

    def test_single_microstructure_snapshot_does_not_close_repeated_evidence_gap(self):
        card = build_regime_card(
            market=self.market(),
            context={"underlyingMarketOpen": False, "indexSourceMode": "OUT_OF_HOURS"},
        )
        self.assertIn("REPEATED_MICROSTRUCTURE_EVIDENCE_MISSING", card["evidenceGaps"])

    def test_repeated_microstructure_metadata_closes_repeated_gap(self):
        market = self.market()
        market["microstructureSampleCount"] = 5
        market["microstructureStanding"] = "PERSISTENT_SELL_TILT_OBSERVED"
        card = build_regime_card(
            market=market,
            context={"underlyingMarketOpen": False, "indexSourceMode": "OUT_OF_HOURS"},
        )
        self.assertNotIn("REPEATED_MICROSTRUCTURE_EVIDENCE_MISSING", card["evidenceGaps"])
        self.assertEqual(card["observedState"]["microstructureSampleCount"], 5)

    def test_invalid_market_fails_closed(self):
        market = self.market()
        market["index"] = "0"
        with self.assertRaises(RegimeCardError):
            build_regime_card(
                market=market,
                context={"underlyingMarketOpen": False, "indexSourceMode": "OUT_OF_HOURS"},
            )


if __name__ == "__main__":
    unittest.main()
