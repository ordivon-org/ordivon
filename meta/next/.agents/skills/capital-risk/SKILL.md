---
name: capital-risk
description: "Route Ordivon Capital portfolio exposure, descriptive risk, and explicit counterfactual analysis through registered read-only LEGO circuits. Preserve UNSET risk-budget state, model-use restrictions, and the distinction between measurement/scenario evidence and investment recommendation."
compatibility: Requires the Ordivon Capital registry, risk/portfolio owner implementations, and read-only circuit contracts.
metadata:
  source-authority: ordivon-capital-registered-lego-router
---

# Capital Risk

This Skill selects bounded analysis circuits; it does not infer the owner's risk tolerance or choose investments.

## Procedure

1. For exposure/risk measurement use `PORTFOLIO_RISK_R1`.
2. For an explicit caller-supplied what-if action use `COUNTERFACTUAL_ANALYSIS_R1`.
3. Read `domains/capital/config/portfolio_risk_budget.json`. Preserve `UNSET` exactly; never synthesize limits from portfolio size, volatility, age, preferences, or model output.
4. Preserve model inventory/validation standing and prohibited-use restrictions from the Capital LEGO Registry.
5. Counterfactual scenarios must remain caller-supplied. Do not rank scenarios, select a winner, convert an incomplete evidence gate into approval, or emit an order.
6. Treat the circuit receipt as mechanical evidence only.

## Non-claims

- Risk measurement is not investment advice or authorization.
- Counterfactual improvement is not a recommendation.
- PASS/INCOMPLETE on an evidence gate is not production-write admission.

## Stop condition

Stop with the bounded report/counterfactual plus unresolved obligations; do not cross into Effect.
