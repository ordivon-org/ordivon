import math
import unittest

from market_capital.portfolio_risk import (
    PortfolioRiskError,
    analyze_dependence,
    build_exposure_ledger,
    build_factor_observatory,
    build_portfolio_risk_report,
    completed_log_returns,
    evaluate_risk_budget,
    historical_expected_shortfall,
    validate_dependence_model,
)


class PortfolioRiskTests(unittest.TestCase):
    def test_exposure_ledger_separates_gross_net_and_overlapping_factor_exposure(self):
        ledger = build_exposure_ledger(
            equity_usd="100",
            available_equity_usd="40",
            initial_margin_usd="25",
            maintenance_margin_usd="5",
            positions=[
                {
                    "instrumentId": "A",
                    "signedNotionalUsd": "150",
                    "factorLoadings": {"tech": "1", "semiconductor": "0.8"},
                },
                {
                    "instrumentId": "B",
                    "signedNotionalUsd": "-50",
                    "factorLoadings": {"tech": "0.5"},
                },
            ],
        )
        self.assertEqual(ledger["grossNotionalUsd"], "200.000000")
        self.assertEqual(ledger["netNotionalUsd"], "100.000000")
        self.assertEqual(ledger["grossToEquity"], "2.000000")
        self.assertEqual(ledger["largestPositionGrossShare"], "0.750000")
        factors = {x["factor"]: x["signedExposureUsd"] for x in ledger["factorExposure"]}
        self.assertEqual(factors["tech"], "125.000000")
        self.assertEqual(factors["semiconductor"], "120.000000")

    def test_completed_log_returns_rejects_unsorted_prices(self):
        with self.assertRaises(PortfolioRiskError):
            completed_log_returns(
                instrument_id="X",
                observations=[
                    {"observedAtMs": 2, "close": "100"},
                    {"observedAtMs": 1, "close": "101"},
                ],
            )

    def test_dependence_reports_beta_instability_instead_of_one_static_ratio(self):
        base = {}
        proxy = {}
        # First half positively linked; second half flips proxy sign.
        for i in range(1, 81):
            x = 0.01 * math.sin(i / 3)
            y = x / 2 if i <= 40 else -x / 2
            base[i] = x
            proxy[i] = y
        out = analyze_dependence(
            base_instrument_id="A",
            base_returns=base,
            proxy_instrument_id="B",
            proxy_returns=proxy,
            short_window=20,
            medium_window=60,
            rolling_window=20,
        )
        self.assertIn("ROLLING_BETA_SIGN_CHANGE", out["structuralWarnings"])

    def test_dependence_output_has_no_unvalidated_local_classifier(self):
        base = {i: 0.01 * math.sin(i / 4) for i in range(1, 90)}
        proxy = {i: 0.008 * math.sin(i / 4 + 0.02) for i in range(1, 90)}
        out = analyze_dependence(
            base_instrument_id="A",
            base_returns=base,
            proxy_instrument_id="B",
            proxy_returns=proxy,
        )
        self.assertEqual(out["componentId"], "portfolio-dependence-analysis")
        self.assertNotIn("standing", out)
        self.assertNotIn("stabilityPolicy", out)


    def test_dependence_walk_forward_validation_uses_oot_and_challenger(self):
        base = {i: 0.002 + 1.5 * (0.001 * math.sin(i / 3)) for i in range(1, 121)}
        proxy = {i: 0.001 * math.sin(i / 3) for i in range(1, 121)}
        out = validate_dependence_model(
            base_instrument_id="A",
            base_returns=base,
            proxy_instrument_id="B",
            proxy_returns=proxy,
            n_splits=5,
        )
        self.assertEqual(out["validationMethod"], "SCIKIT_LEARN_WALK_FORWARD_TIME_SERIES_SPLIT")
        self.assertEqual(len(out["folds"]), 5)
        self.assertEqual(out["primaryEstimator"], "sklearn.linear_model.LinearRegression")
        self.assertEqual(out["challengerEstimator"], "sklearn.linear_model.HuberRegressor")
        for fold in out["folds"]:
            self.assertLess(fold["trainEndObservedAtMs"], fold["testStartObservedAtMs"])
        self.assertAlmostEqual(float(out["summary"]["primaryBeta"]["median"]), 1.5, places=3)

    def test_dependence_validation_rejects_too_little_history(self):
        with self.assertRaises(PortfolioRiskError):
            validate_dependence_model(
                base_instrument_id="A",
                base_returns={i: i / 1000 for i in range(20)},
                proxy_instrument_id="B",
                proxy_returns={i: i / 2000 for i in range(20)},
            )

    def test_empirical_expected_shortfall_is_tail_mean_without_regulatory_scaling(self):
        returns = [0.01] * 19 + [-0.20]
        out = historical_expected_shortfall(returns, confidence=0.95)
        self.assertEqual(out["componentId"], "historical-expected-shortfall")
        self.assertGreaterEqual(
            float(out["expectedShortfallLossFraction"]),
            float(out["valueAtRiskLossFraction"]),
        )
        self.assertFalse(out["liquidityHorizonScalingApplied"])
        self.assertFalse(out["regulatoryCapitalCalculation"])

    def test_factor_observatory_allows_multiple_proxies_per_factor_but_rejects_duplicate_pair(self):
        base = {i: 0.001 * math.sin(i / 5) for i in range(1, 70)}
        proxy_b = {i: 0.0008 * math.sin(i / 5) for i in range(1, 70)}
        proxy_c = {i: 0.0006 * math.sin(i / 5 + 0.1) for i in range(1, 70)}
        out = build_factor_observatory(
            base_instrument_id="A",
            base_returns=base,
            factor_proxies=[
                {"factor": "tech", "instrumentId": "B", "returns": proxy_b},
                {"factor": "tech", "instrumentId": "C", "returns": proxy_c},
            ],
        )
        self.assertEqual(out["factorCount"], 1)
        self.assertEqual(out["factorProxyCount"], 2)
        self.assertEqual(out["factors"][0]["proxyCount"], 2)

        with self.assertRaises(PortfolioRiskError):
            build_factor_observatory(
                base_instrument_id="A",
                base_returns=base,
                factor_proxies=[
                    {"factor": "tech", "instrumentId": "B", "returns": proxy_b},
                    {"factor": "tech", "instrumentId": "B", "returns": proxy_b},
                ],
            )

    def test_risk_budget_is_incomplete_not_inferred_when_inputs_missing(self):
        ledger = build_exposure_ledger(
            equity_usd="100",
            available_equity_usd="50",
            positions=[{"instrumentId": "A", "signedNotionalUsd": "100"}],
        )
        out = evaluate_risk_budget(exposure_ledger=ledger, budget={"maxGrossToEquity": "2"})
        self.assertEqual(out["standing"], "INCOMPLETE")

    def test_risk_budget_reports_named_breaches_without_recommending_trade(self):
        ledger = build_exposure_ledger(
            equity_usd="100",
            available_equity_usd="20",
            positions=[{"instrumentId": "A", "signedNotionalUsd": "300"}],
        )
        out = evaluate_risk_budget(
            exposure_ledger=ledger,
            budget={
                "maxGrossToEquity": "2",
                "maxLargestPositionGrossShare": "0.8",
                "minAvailableEquityRatio": "0.3",
                "shockMagnitudePct": "10",
                "maxEquityLossPctAtShock": "20",
            },
        )
        self.assertEqual(out["standing"], "BREACHED")
        self.assertEqual(
            set(out["breachedChecks"]),
            {
                "MAX_GROSS_TO_EQUITY",
                "MAX_LARGEST_POSITION_GROSS_SHARE",
                "MIN_AVAILABLE_EQUITY_RATIO",
                "MAX_EQUITY_LOSS_AT_NAMED_SHOCK",
            },
        )

    def test_risk_report_composes_without_allocation_fields(self):
        ledger = build_exposure_ledger(
            equity_usd="100",
            available_equity_usd="100",
            positions=[],
        )
        monitoring = {"componentId": "dependence-model-monitoring", "kind": "test-monitoring"}
        tail = {"componentId": "tail-risk-report", "kind": "test-tail"}
        out = build_portfolio_risk_report(exposure_ledger=ledger, model_monitoring=monitoring, tail_risk_report=tail)
        self.assertEqual(out["kind"], "ordivon.market-capital.portfolio-risk-report")
        self.assertNotIn("allocationProduced", out)
        self.assertEqual(out["nodes"]["modelMonitoring"], monitoring)
        self.assertEqual(out["nodes"]["tailRisk"], tail)
        self.assertEqual(out["nodes"]["riskLimitEvaluation"]["standing"], "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
