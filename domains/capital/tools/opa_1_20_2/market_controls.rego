package ordivon.capital.market.execution

default allow_non_live := false
default allow_external_write := false

allow_non_live if {
    input.currentLane == "NON_LIVE"
    input.writePolicy.state == "NOT_ADMITTED"
    input.writePolicy.externalFinancialWriteAllowed == false
    input.writePolicy.providerWriteCapabilityBound == false
    input.writePolicy.effectVerifier != "IMPLEMENTED_BOUND_CURRENT"
}

allow_external_write if {
    input.currentLane == "EXTERNAL_WRITE"
    input.writePolicy.state == "ADMITTED"
    input.writePolicy.externalFinancialWriteAllowed == true
    input.writePolicy.providerWriteCapabilityBound == true
    input.writePolicy.effectVerifier == "IMPLEMENTED_BOUND_CURRENT"
}

# Live-endpoint qualification policy. Python normalizes provider reality into facts;
# OPA owns the admission decision and blocking reason vocabulary.

live_test_blocking_reasons contains "unsupported-venue" if {
    input.liveTest.venue != "OKX"
    input.liveTest.venue != "BINANCE"
}

live_test_blocking_reasons contains "readonly-reality-not-verified" if {
    input.liveTest.permissionStanding != "READ_ONLY_VERIFIED"
}

live_test_blocking_reasons contains "reality-not-readonly" if {
    input.liveTest.externalFinancialWriteAttempted != false
}

live_test_blocking_reasons contains "clock-gate-not-passed" if {
    input.liveTest.clockPassed != true
}

live_test_blocking_reasons contains "reconciliation-not-healthy" if {
    input.liveTest.reconciliationHealthy != true
}

live_test_blocking_reasons contains "trade-permission-missing" if {
    input.liveTest.tradePermission != true
}

live_test_blocking_reasons contains "withdraw-permission-not-proven-absent" if {
    input.liveTest.withdrawPermission != false
}

live_test_blocking_reasons contains "transfer-permission-not-proven-absent" if {
    input.liveTest.transferPermission != false
    input.liveTest.transferPermission != null
}

live_test_blocking_reasons contains "nonzero-position-present" if {
    input.liveTest.hasNonzeroPosition == true
}

live_test_blocking_reasons contains "open-order-present" if {
    input.liveTest.hasOpenOrders == true
}

live_test_blocking_reasons contains reason if {
    count(input.liveTest.nonquoteNonzeroAssets) > 0
    reason := sprintf("nonquote-balance-present:%s", [concat(",", input.liveTest.nonquoteNonzeroAssets)])
}

live_test_blocking_reasons contains "quote-balance-exceeds-test-threshold" if {
    input.liveTest.quoteBalanceExceedsThreshold == true
}

live_test_account_decision := {
    "admitted": count(live_test_blocking_reasons) == 0,
    "blockingReasons": sort(live_test_blocking_reasons),
}


# Portfolio risk-limit control. Numeric observations are normalized by Python;
# OPA owns whether each explicit caller/policy limit is satisfied.
risk_budget_decision := {
    "standing": "INCOMPLETE",
    "missingBudgetInputs": input.riskBudget.missingBudgetInputs,
    "statuses": {},
} if {
    input.riskBudget.complete == false
}

risk_budget_decision := {
    "standing": standing,
    "missingBudgetInputs": [],
    "statuses": statuses,
} if {
    input.riskBudget.complete == true
    statuses := {
        "MAX_GROSS_TO_EQUITY": risk_max_gross_status,
        "MAX_LARGEST_POSITION_GROSS_SHARE": risk_max_concentration_status,
        "MIN_AVAILABLE_EQUITY_RATIO": risk_min_available_status,
        "MAX_EQUITY_LOSS_AT_NAMED_SHOCK": risk_shock_loss_status,
    }
    standing := risk_budget_standing
}

risk_budget_standing := "SATISFIED" if {
    risk_max_gross_status == "PASS"
    risk_max_concentration_status == "PASS"
    risk_min_available_status == "PASS"
    risk_shock_loss_status == "PASS"
} else := "BREACHED"

risk_max_gross_status := "PASS" if {
    input.riskBudget.grossToEquity <= input.riskBudget.maxGrossToEquity
} else := "FAIL"

risk_max_concentration_status := "PASS" if {
    input.riskBudget.largestPositionGrossShare <= input.riskBudget.maxLargestPositionGrossShare
} else := "FAIL"

risk_min_available_status := "PASS" if {
    input.riskBudget.availableEquityRatio >= input.riskBudget.minAvailableEquityRatio
} else := "FAIL"

risk_shock_loss_status := "PASS" if {
    input.riskBudget.shockLossPct <= input.riskBudget.maxEquityLossPctAtShock
} else := "FAIL"

# Pre-trade evidence control. Mechanical scenario projection stays in Python;
# OPA owns whether the supplied evidence is sufficient/compatible.
counterfactual_gate_statuses := {
    "RISK_BUDGET": counterfactual_risk_budget_status,
    "GROSS_DIRECTION": counterfactual_gross_direction_status,
    "MARGIN_DELTA": counterfactual_margin_status,
    "FUNDING_BASIS_CARRY": counterfactual_carry_status,
    "LIQUIDITY_COST": counterfactual_liquidity_status,
    "TARGET_FACTOR_MECHANICS": counterfactual_target_factor_status,
    "DEPENDENCE_EVIDENCE": counterfactual_dependence_status,
    "DIVERSIFICATION_EVIDENCE": counterfactual_diversification_status,
    "RECONCILIATION_SIGNPOST": counterfactual_reconciliation_status,
}

counterfactual_risk_budget_status := "PASS" if {
    input.counterfactual.riskBudgetStanding == "SATISFIED"
} else := "FAIL" if {
    input.counterfactual.riskBudgetStanding == "BREACHED"
} else := "INCOMPLETE"

counterfactual_gross_direction_status := "PASS" if {
    input.counterfactual.action == "DE_RISK"
    input.counterfactual.projectedGrossToEquity < input.counterfactual.baselineGrossToEquity
} else := "FAIL" if {
    input.counterfactual.action == "DE_RISK"
} else := "PASS" if {
    input.counterfactual.action == "HOLD"
    input.counterfactual.projectedGrossToEquity == input.counterfactual.baselineGrossToEquity
} else := "FAIL" if {
    input.counterfactual.action == "HOLD"
} else := "PASS" if {
    input.counterfactual.action == "RECONCILE"
    input.counterfactual.projectedGrossToEquity == input.counterfactual.baselineGrossToEquity
} else := "FAIL" if {
    input.counterfactual.action == "RECONCILE"
} else := "PASS"

counterfactual_margin_status := "PASS" if {
    input.counterfactual.needsNewPositionEvidence == true
    input.counterfactual.marginMeasured == true
} else := "INCOMPLETE" if {
    input.counterfactual.needsNewPositionEvidence == true
} else := "NOT_REQUIRED"

counterfactual_carry_status := "PASS" if {
    input.counterfactual.needsNewPositionEvidence == true
    input.counterfactual.carryMeasured == true
} else := "INCOMPLETE" if {
    input.counterfactual.needsNewPositionEvidence == true
} else := "NOT_REQUIRED"

counterfactual_liquidity_status := "PASS" if {
    input.counterfactual.changesPosition == true
    input.counterfactual.liquidityMeasured == true
} else := "INCOMPLETE" if {
    input.counterfactual.changesPosition == true
} else := "NOT_REQUIRED"

counterfactual_target_factor_status := "PASS" if {
    input.counterfactual.action == "HEDGE"
    input.counterfactual.targetFactorStanding == "TARGET_FACTOR_ABSOLUTE_EXPOSURE_REDUCED"
} else := "FAIL" if {
    input.counterfactual.action == "HEDGE"
    input.counterfactual.targetFactorStanding == "TARGET_FACTOR_ABSOLUTE_EXPOSURE_INCREASED"
} else := "FAIL" if {
    input.counterfactual.action == "HEDGE"
    input.counterfactual.targetFactorStanding == "TARGET_FACTOR_ABSOLUTE_EXPOSURE_UNCHANGED"
} else := "INCOMPLETE" if {
    input.counterfactual.action == "HEDGE"
} else := "NOT_REQUIRED"

counterfactual_dependence_status := "PASS" if {
    input.counterfactual.action == "HEDGE"
    input.counterfactual.dependenceComponentId == "portfolio-dependence-analysis"
    input.counterfactual.dependenceSampleCountPresent == true
} else := "FAIL" if {
    input.counterfactual.action == "HEDGE"
    input.counterfactual.dependencePresent == true
    input.counterfactual.dependenceComponentId != "portfolio-dependence-analysis"
} else := "INCOMPLETE" if {
    input.counterfactual.action == "HEDGE"
} else := "NOT_REQUIRED"

counterfactual_diversification_status := "PASS" if {
    input.counterfactual.action == "DIVERSIFY"
    input.counterfactual.diversificationComponentId == "portfolio-dependence-analysis"
} else := "FAIL" if {
    input.counterfactual.action == "DIVERSIFY"
    input.counterfactual.diversificationPresent == true
    input.counterfactual.diversificationComponentId != "portfolio-dependence-analysis"
} else := "INCOMPLETE" if {
    input.counterfactual.action == "DIVERSIFY"
} else := "NOT_REQUIRED"

counterfactual_reconciliation_status := "PASS" if {
    input.counterfactual.action == "RECONCILE"
    input.counterfactual.reconciliationSignpostDefined == true
} else := "INCOMPLETE" if {
    input.counterfactual.action == "RECONCILE"
} else := "NOT_REQUIRED"
