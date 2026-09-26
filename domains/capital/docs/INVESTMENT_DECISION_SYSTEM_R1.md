# Ordivon Capital Investment Decision System R1

Date: 2026-09-27
Standing: **PASS_R1_ACTIVE_DECISION_SUPPORT**
Truth role: decision-support architecture, not investment truth, owner mandate, trade approval, or external financial effect authority.

## Objective

R1 turns the existing Capital observation/risk/research substrate into a bounded investment decision-support system without building a local investment doctrine. Mature external models are registered with their assumptions, applicable conditions, invalidators, evidence identities, and permitted decision roles. The router chooses which models are relevant to the current decision context; it does not choose securities or submit orders.

## Architecture

```text
Life / objective / horizon
        ↓
Current portfolio + explicit constraints
        ↓
External Investment Model Atlas
        ↓
Decision Router
        ├─ CORE models → required baseline context
        ├─ MATURE_CONDITIONAL → eligible when routing tags are satisfied
        ├─ CONTESTED_CONDITIONAL → research-only by default
        └─ STATE_MODEL → context/risk interpretation, not direct trade oracle
        ↓
Risk Governor
        ├─ UNSET risk budget → no sizing proposal
        ├─ liquidity/funding stress → risk review before sizing
        └─ model conflict → no sizing escalation
        ↓
Counterfactual / risk / execution-planning surfaces
        ↓
Attribution / prospective monitoring / learning
```

## Current external model atlas

The canonical R1 atlas is `config/investment_model_atlas.json`. It currently registers:

- lifecycle / human-capital framing;
- diversified strategic baseline;
- performance-attribution governance;
- value / valuation;
- quality / profitability;
- cross-sectional momentum;
- time-series trend;
- Black-Litterman view blending;
- fractional Kelly sizing reference;
- macro state context;
- volatility risk scaling (contested conditional);
- factor timing (contested conditional);
- dynamic cost-aware trading.

The atlas stores stable evidence identities such as DOI, NBER working-paper identity, PII, or canonical professional-learning URL. The atlas is an external model library, not an assertion that every registered model is currently true or appropriate.

## Routing contract

`src/ordivon_capital/portfolio/decision_router.py::route_investment_decision` consumes only an explicit context:

- `decisionId`
- `asOf`
- `objective`
- `horizon`
- `riskBudgetStatus` (`SET` or `UNSET`)
- `stateTags`

It emits model routes with one of:

- `REQUIRED`
- `ELIGIBLE`
- `RESEARCH_ONLY`
- `INACTIVE`
- `BLOCKED_BY_STATE`

and a bounded decision standing:

- `RESEARCH_ONLY_RISK_BUDGET_UNSET`
- `RISK_REVIEW_REQUIRED`
- `MODEL_CONFLICT_REVIEW`
- `CONDITIONAL_OVERLAY_REVIEW`
- `BASELINE_ONLY`

The router never emits order-generation or external-write authority.

## Authority hierarchy

```text
Life objective / owner mandate
        >
Risk Governor / explicit risk budget
        >
Strategic portfolio baseline
        >
Conditional active models
        >
Execution planning
```

Lower layers may not silently rewrite higher-layer objectives or limits.

## R1 principles

1. **DELETE-CUSTOM-BY-DEFAULT** — mature external investment theory is registered and routed, not reimplemented as local doctrine.
2. **Conditional, not religious** — value, momentum, macro, volatility and factor models may coexist because they answer different questions and horizons.
3. **Conflict reduces authority** — contested models remain research-only; explicit `MODEL_CONFLICT` prevents sizing escalation.
4. **Risk appetite is owner truth** — the current repository authority remains `config/portfolio_risk_budget.json`; `UNSET` stays `UNSET`.
5. **State is not action** — macro and risk observations may alter model applicability without directly generating a trade.
6. **Target is not execution** — cost-aware execution can plan movement toward a frozen target but cannot change the thesis.
7. **Outcome is not process quality** — performance attribution and prospective monitoring remain part of the learning loop.

## Current authority standing

R1 does not alter the existing external-effect boundary:

```text
execution lane                 NON_LIVE
production external write      BLOCK_NOT_GRANTED
private account data           NOT_ADMITTED
portfolio risk budget          UNSET (until owner explicitly sets it)
```

Accordingly, the current system can route models, analyze scenarios, build counterfactuals and support research. It cannot infer a personal risk budget, autonomously size a live portfolio, or submit a real-money order.

## Verification

Owner-native verification passed in Runtime Job `job-01a0dee3-39ce-7fc1-bf40-9e3c5b52d4dd`:

```text
ruff               PASS
pytest              396 passed
provider-bound      11 deselected
failed              0
```

The decision-router plus read-only decision-support circuit suite independently passed 15/15 targeted tests. Current-state generation/readback reports 13 registered external decision models, 43 Capital registry entries (38 canonical), `portfolio risk budget=UNSET`, `execution lane=NON_LIVE`, and `externalFinancialEffectAllowed=false`.

## Read-only decision-support circuit

`INVESTMENT_DECISION_SUPPORT_R1` is now implemented through `circuits/investment-decision-support-r2.json` and the existing Capital read-circuit compiler/runner. It binds the current registered model atlas and derives risk-budget standing from `config/portfolio_risk_budget.json`; a caller cannot upgrade an `UNSET` owner budget to `SET` through decision context. The circuit remains effect-free and its canary returned `RESEARCH_ONLY_RISK_BUDGET_UNSET`, `externalFinancialEffectAllowed=false`, and 13 registered models.

## Next integration seam

The next bounded step is decision-time evidence/state projection: replace manually supplied state tags with explicit observation-to-state contracts where mature external definitions exist, persist the frozen decision context for later attribution, and continue to keep execution authority separate.
