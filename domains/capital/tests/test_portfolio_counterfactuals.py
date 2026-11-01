import unittest
from decimal import Decimal

from ordivon_capital.portfolio.portfolio_counterfactuals import (
    PortfolioCounterfactualError,
    build_action_counterfactual,
    build_counterfactual_gate_set,
    build_counterfactual_set,
    evaluate_constraint_gate,
)
from ordivon_capital.risk.portfolio_risk import build_exposure_ledger


class PortfolioCounterfactualTests(unittest.TestCase):
    def setUp(self):
        self.ledger = build_exposure_ledger(
            equity_usd="100",
            available_equity_usd="40",
            initial_margin_usd="30",
            maintenance_margin_usd="5",
            positions=[
                {
                    "instrumentId": "SNDK",
                    "signedNotionalUsd": "300",
                    "factorLoadings": {"memory": "1", "semiconductor": "0.7"},
                }
            ],
        )

    def test_factor_identity_fails_closed_in_both_real_counterfactual_inputs(self):
        ledger = dict(self.ledger)
        position = dict(ledger["positions"][0])
        position["factorLoadings"] = {"memory": "0.5", " memory ": "0.25"}
        ledger["positions"] = [position]
        with self.assertRaisesRegex(PortfolioCounterfactualError, "duplicate normalized factor"):
            build_action_counterfactual(
                exposure_ledger=ledger, scenario={"scenarioId": "bad-ledger", "action": "HOLD"}
            )

        for action, fields in (
            (
                "HEDGE",
                {
                    "instrumentId": "MU",
                    "targetFactor": "memory",
                    "signedNotionalDeltaUsd": "-10",
                    "factorLoadings": {"memory": "0.5", " memory ": "0.25"},
                },
            ),
            (
                "DIVERSIFY",
                {
                    "sourceInstrumentId": "SNDK",
                    "destinationInstrumentId": "MU",
                    "reallocationFraction": "0.5",
                    "destinationSignedNotionalUsd": "10",
                    "destinationFactorLoadings": {"memory": "0.5", " memory ": "0.25"},
                },
            ),
        ):
            with self.subTest(action=action):
                with self.assertRaisesRegex(
                    PortfolioCounterfactualError, "duplicate normalized factor"
                ):
                    build_action_counterfactual(
                        exposure_ledger=self.ledger,
                        scenario={"scenarioId": "bad-scenario", "action": action, **fields},
                    )

    def test_counterfactual_rejects_malformed_present_factor_mapping(self):
        # A present falsy []/false/null is not an absent declared machine map.
        for raw in ([], "", False, 0, None):
            ledger = dict(self.ledger)
            row = dict(self.ledger["positions"][0])
            row["factorLoadings"] = raw
            ledger["positions"] = [row]
            with self.subTest(source="ledger", raw=repr(raw)):
                with self.assertRaisesRegex(PortfolioCounterfactualError, "must be an object"):
                    build_action_counterfactual(
                        exposure_ledger=ledger,
                        scenario={"scenarioId": "malformed-ledger", "action": "HOLD"},
                    )
            with self.subTest(source="hedge", raw=repr(raw)):
                if raw is None:
                    continue  # None means no asserted new factor loadings.
                with self.assertRaisesRegex(PortfolioCounterfactualError, "must be an object"):
                    build_action_counterfactual(
                        exposure_ledger=self.ledger,
                        scenario={
                            "scenarioId": "malformed-scenario",
                            "action": "HEDGE",
                            "instrumentId": "NEW",
                            "targetFactor": "memory",
                            "signedNotionalDeltaUsd": "-10",
                            "factorLoadings": raw,
                        },
                    )

    def test_scenario_factor_alias_is_canonicalized_before_hedge_consumer(self):
        out = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "exact-existing-factor",
                "action": "HEDGE",
                "instrumentId": "SNDK",
                "targetFactor": "memory",
                "signedNotionalDeltaUsd": "-10",
                "factorLoadings": {" memory ": "1", " semiconductor ": "0.7"},
            },
        )
        self.assertEqual(
            out["hedgeMechanics"]["standing"], "TARGET_FACTOR_ABSOLUTE_EXPOSURE_REDUCED"
        )
        self.assertEqual(
            out["projected"]["positions"][0]["factorLoadings"],
            {"memory": "1.000000", "semiconductor": "0.700000"},
        )

    def test_lossless_factor_output_is_recomputable_from_serialized_scenario(self):
        out = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "fractional-factor-hedge",
                "action": "HEDGE",
                "instrumentId": "MU",
                "targetFactor": "memory",
                "signedNotionalDeltaUsd": "-12.3456789",
                "factorLoadings": {" memory ": "0.333333333"},
            },
        )
        projected = out["projected"]["positions"]
        mu = next(row for row in projected if row["instrumentId"] == "MU")
        self.assertEqual(mu["signedNotionalUsd"], "-12.3456789")
        self.assertEqual(mu["factorLoadings"], {"memory": "0.333333333"})
        before = Decimal("300.000000")
        expected_delta = Decimal(mu["signedNotionalUsd"]) * Decimal(mu["factorLoadings"]["memory"])
        actual = next(row for row in out["deltas"]["factorExposure"] if row["factor"] == "memory")
        self.assertEqual(Decimal(actual["beforeUsd"]), before)
        self.assertEqual(Decimal(actual["deltaUsd"]), expected_delta)
        self.assertEqual(Decimal(actual["afterUsd"]), before + expected_delta)
        self.assertNotIn("tradeSignal", out)
        self.assertNotIn("order", out)

    def test_lossless_ledger_projection_is_the_only_higher_order_baseline(self):
        ledger = dict(self.ledger)
        ledger["positions"] = [
            {
                "instrumentId": "SNDK",
                "signedNotionalUsd": "12.3456789",
                "factorLoadings": {"memory": "0.333333333"},
            }
        ]
        out = build_action_counterfactual(
            exposure_ledger=ledger, scenario={"scenarioId": "precision-roundtrip", "action": "HOLD"}
        )
        row = out["projected"]["positions"][0]
        self.assertEqual(row["signedNotionalUsd"], "12.3456789")
        self.assertEqual(row["factorLoadings"], {"memory": "0.333333333"})
        expected = Decimal(row["signedNotionalUsd"]) * Decimal(row["factorLoadings"]["memory"])
        factors = out["deltas"]["factorExposure"]
        self.assertEqual(len(factors), 1)
        self.assertEqual(Decimal(factors[0]["beforeUsd"]), expected)
        self.assertEqual(factors[0]["deltaUsd"], "0.000000")
        self.assertEqual(out["action"], "HOLD")

    def test_tiny_real_factor_exposure_is_not_erased_by_display_precision(self):
        # A load of 1e-7 over 10 million USD equals a real 1 USD factor.
        ledger = {
            "equityUsd": "10000000",
            "availableEquityUsd": "2000000",
            "positions": [
                {
                    "instrumentId": "ASSET-A",
                    "signedNotionalUsd": "10000000",
                    "factorLoadings": {" sector ": "0.0000001"},
                }
            ],
        }
        out = build_action_counterfactual(
            exposure_ledger=ledger, scenario={"scenarioId": "exact-1-dollar", "action": "HOLD"}
        )
        self.assertEqual(out["projected"]["positions"][0]["factorLoadings"]["sector"], "0.0000001")
        factor = out["deltas"]["factorExposure"][0]
        self.assertEqual(Decimal(factor["beforeUsd"]), Decimal("1"))
        self.assertEqual(Decimal(factor["afterUsd"]), Decimal("1"))
        self.assertEqual(Decimal(factor["deltaUsd"]), Decimal("0"))
        self.assertFalse(out["exactMarginDeltaMeasured"])

    def test_finite_scenario_product_factor_deltas_match_visible_portfolio(self):
        # A real higher-order consumer must reproduce every machine-reported
        # factor delta from lossless source ports; display rounding is NOT a gate.
        # 4 notionals × 3 loadings × 4 caller actions = 48 bounded cases.
        q = Decimal
        notionals = ("10.1234567", "-10.1234567", "100", "-100")
        loadings = ("0.123456789", "-0.333333333", "1")
        for notional in notionals:
            for loading in loadings:
                ledger = {
                    "equityUsd": "100.000000",
                    "availableEquityUsd": "20.000000",
                    "positions": [
                        {
                            "instrumentId": "ASSET-A",
                            "signedNotionalUsd": notional,
                            "factorLoadings": {" sector ": loading},
                        }
                    ],
                }
                cases = {
                    "HOLD": {},
                    "DE_RISK": {"instrumentId": "ASSET-A", "reductionFraction": "0.333333333"},
                    "HEDGE": {
                        "instrumentId": "HEDGE-B",
                        "targetFactor": "sector",
                        "signedNotionalDeltaUsd": "-7.1234567",
                        "factorLoadings": {" sector ": "0.222222222"},
                    },
                    "DIVERSIFY": {
                        "sourceInstrumentId": "ASSET-A",
                        "destinationInstrumentId": "ASSET-B",
                        "reallocationFraction": "0.5",
                        "destinationSignedNotionalUsd": "2.1234567",
                        "destinationFactorLoadings": {" sector ": "0.222222222"},
                    },
                }
                for action, args in cases.items():
                    with self.subTest(notional=notional, loading=loading, action=action):
                        out = build_action_counterfactual(
                            exposure_ledger=ledger,
                            scenario={
                                "scenarioId": "finite-domain-identity",
                                "action": action,
                                **args,
                            },
                        )
                        factor = next(
                            row
                            for row in out["deltas"]["factorExposure"]
                            if row["factor"] == "sector"
                        )
                        expected_before = q(q(notional) * q(loading))
                        projected = out["projected"]["positions"]
                        expected_after = q(
                            sum(
                                (
                                    Decimal(row["signedNotionalUsd"])
                                    * Decimal(row["factorLoadings"]["sector"])
                                    for row in projected
                                    if "sector" in row["factorLoadings"]
                                ),
                                Decimal("0"),
                            )
                        )
                        self.assertEqual(Decimal(factor["beforeUsd"]), expected_before)
                        self.assertEqual(Decimal(factor["afterUsd"]), expected_after)
                        self.assertEqual(
                            Decimal(factor["deltaUsd"]),
                            q(expected_after - expected_before),
                        )
                        self.assertIsNone(out["projectedAvailableEquityUsd"])
                        self.assertFalse(out["exactMarginDeltaMeasured"])

    def test_derisk_reduces_gross_and_named_shock_without_new_position(self):
        out = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "derisk-50",
                "action": "DE_RISK",
                "instrumentId": "SNDK",
                "reductionFraction": "0.5",
                "sizingBasis": "EXPLICIT_CALLER_COUNTERFACTUAL",
                "shock": {"instrumentId": "SNDK", "magnitudePct": "10"},
            },
        )
        self.assertEqual(out["projected"]["grossToEquity"], "1.500000")
        self.assertEqual(out["deltas"]["grossToEquity"], "-1.500000")
        self.assertEqual(out["shockProjection"]["afterEquityLossPctFirstOrder"], "15.000000")

    def test_hedge_can_reduce_net_while_increasing_gross(self):
        out = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "hedge-explicit",
                "action": "HEDGE",
                "instrumentId": "MU",
                "targetFactor": "memory",
                "signedNotionalDeltaUsd": "-100",
                "factorLoadings": {"memory": "1"},
                "sizingBasis": "EXPLICIT_CALLER_COUNTERFACTUAL",
            },
        )
        self.assertEqual(out["projected"]["grossToEquity"], "4.000000")
        self.assertEqual(out["projected"]["netToEquity"], "2.000000")
        self.assertEqual(out["deltas"]["grossToEquity"], "1.000000")
        self.assertEqual(out["deltas"]["netToEquity"], "-1.000000")
        self.assertEqual(
            out["hedgeMechanics"]["standing"],
            "TARGET_FACTOR_ABSOLUTE_EXPOSURE_REDUCED",
        )

    def test_diversify_reallocation_is_not_assumed_gross_reduction(self):
        out = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "reallocate",
                "action": "DIVERSIFY",
                "sourceInstrumentId": "SNDK",
                "reallocationFraction": "0.25",
                "destinationInstrumentId": "XAU",
                "destinationSignedNotionalUsd": "75",
                "destinationFactorLoadings": {"alternative_macro": "1"},
                "sizingBasis": "EXPLICIT_CALLER_COUNTERFACTUAL",
            },
        )
        self.assertEqual(out["projected"]["grossToEquity"], "3.000000")
        self.assertEqual(out["projected"]["largestPositionGrossShare"], "0.750000")

    def test_hold_and_reconcile_cannot_smuggle_position_change(self):
        for action in ("HOLD", "RECONCILE"):
            with self.assertRaises(PortfolioCounterfactualError):
                build_action_counterfactual(
                    exposure_ledger=self.ledger,
                    scenario={
                        "scenarioId": action.lower(),
                        "action": action,
                        "instrumentId": "MU",
                        "signedNotionalDeltaUsd": "-20",
                    },
                )

    def test_sizing_basis_must_be_explicit_counterfactual(self):
        with self.assertRaises(PortfolioCounterfactualError):
            build_action_counterfactual(
                exposure_ledger=self.ledger,
                scenario={
                    "scenarioId": "bad",
                    "action": "HEDGE",
                    "instrumentId": "MU",
                    "targetFactor": "memory",
                    "signedNotionalDeltaUsd": "-50",
                    "sizingBasis": "SYSTEM_RECOMMENDED",
                },
            )

    def test_derisk_gate_requires_execution_liquidity_evidence(self):
        cf = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "d25-gate",
                "action": "DE_RISK",
                "instrumentId": "SNDK",
                "reductionFraction": "0.25",
            },
        )
        gate = evaluate_constraint_gate(
            counterfactual=cf,
            risk_budget_evaluation={"standing": "SATISFIED"},
        )
        self.assertEqual(gate["standing"], "INCOMPLETE")
        self.assertEqual(gate["incompleteChecks"], ["LIQUIDITY_COST"])
        passed = evaluate_constraint_gate(
            counterfactual=cf,
            risk_budget_evaluation={"standing": "SATISFIED"},
            evidence={"liquidity": {"measured": True, "spreadBps": "1.0"}},
        )
        self.assertEqual(passed["standing"], "PASS")

    def test_hedge_label_cannot_override_target_factor_mechanics(self):
        cf = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "fake-hedge",
                "action": "HEDGE",
                "instrumentId": "MU",
                "targetFactor": "memory",
                "signedNotionalDeltaUsd": "50",
                "factorLoadings": {"memory": "1"},
            },
        )
        self.assertEqual(
            cf["hedgeMechanics"]["standing"],
            "TARGET_FACTOR_ABSOLUTE_EXPOSURE_INCREASED",
        )
        gate = evaluate_constraint_gate(
            counterfactual=cf,
            risk_budget_evaluation={"standing": "SATISFIED"},
            evidence={
                "margin": {"measured": True},
                "liquidity": {"measured": True},
                "carry": {"measured": True},
                "dependence": {
                    "componentId": "portfolio-dependence-analysis",
                    "overlapReturnCount": 178,
                },
            },
        )
        self.assertEqual(gate["standing"], "FAIL")
        self.assertIn("TARGET_FACTOR_MECHANICS", gate["failedChecks"])

    def test_hedge_gate_is_incomplete_without_budget_margin_liquidity_carry_and_dependence(self):
        cf = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "hedge",
                "action": "HEDGE",
                "instrumentId": "MU",
                "targetFactor": "memory",
                "signedNotionalDeltaUsd": "-50",
                "factorLoadings": {"memory": "1"},
            },
        )
        gate = evaluate_constraint_gate(counterfactual=cf)
        self.assertEqual(gate["standing"], "INCOMPLETE")
        self.assertEqual(
            set(gate["incompleteChecks"]),
            {
                "RISK_BUDGET",
                "MARGIN_DELTA",
                "LIQUIDITY_COST",
                "FUNDING_BASIS_CARRY",
                "DEPENDENCE_EVIDENCE",
            },
        )

    def test_hedge_gate_can_pass_evidence_completeness_without_approving_action(self):
        cf = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={
                "scenarioId": "hedge",
                "action": "HEDGE",
                "instrumentId": "MU",
                "targetFactor": "memory",
                "signedNotionalDeltaUsd": "-50",
                "factorLoadings": {"memory": "1"},
            },
        )
        gate = evaluate_constraint_gate(
            counterfactual=cf,
            risk_budget_evaluation={"standing": "SATISFIED"},
            evidence={
                "margin": {"measured": True},
                "liquidity": {"measured": True},
                "carry": {"measured": True},
                "dependence": {
                    "componentId": "portfolio-dependence-analysis",
                    "overlapReturnCount": 178,
                },
            },
        )
        self.assertEqual(gate["standing"], "PASS")

    def test_reconcile_requires_signpost(self):
        cf = build_action_counterfactual(
            exposure_ledger=self.ledger,
            scenario={"scenarioId": "wait", "action": "RECONCILE"},
        )
        incomplete = evaluate_constraint_gate(
            counterfactual=cf,
            risk_budget_evaluation={"standing": "SATISFIED"},
        )
        self.assertIn("RECONCILIATION_SIGNPOST", incomplete["incompleteChecks"])
        passed = evaluate_constraint_gate(
            counterfactual=cf,
            risk_budget_evaluation={"standing": "SATISFIED"},
            evidence={"reconciliationSignpost": {"defined": True}},
        )
        self.assertEqual(passed["standing"], "PASS")

    def test_counterfactual_set_contains_no_ranking_surface(self):
        cfs = build_counterfactual_set(
            exposure_ledger=self.ledger,
            scenarios=[
                {"scenarioId": "hold", "action": "HOLD"},
                {
                    "scenarioId": "d25",
                    "action": "DE_RISK",
                    "instrumentId": "SNDK",
                    "reductionFraction": "0.25",
                },
            ],
        )
        self.assertNotIn("rankingProduced", cfs)
        self.assertNotIn("winnerSelected", cfs)
        gates = build_counterfactual_gate_set(counterfactual_set=cfs)
        self.assertNotIn("rankingProduced", gates)
        self.assertNotIn("winnerSelected", gates)


if __name__ == "__main__":
    unittest.main()
