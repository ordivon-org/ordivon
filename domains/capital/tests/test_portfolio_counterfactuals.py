import unittest

from ordivon_capital.market.portfolio_counterfactuals import (
    PortfolioCounterfactualError,
    build_action_counterfactual,
    build_counterfactual_gate_set,
    build_counterfactual_set,
    evaluate_constraint_gate,
)
from ordivon_capital.market.portfolio_risk import build_exposure_ledger


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
            {"RISK_BUDGET", "MARGIN_DELTA", "LIQUIDITY_COST", "FUNDING_BASIS_CARRY", "DEPENDENCE_EVIDENCE"},
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
