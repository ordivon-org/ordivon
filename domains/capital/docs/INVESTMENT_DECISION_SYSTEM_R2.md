# Ordivon Capital Investment Decision System R2

Date: 2026-09-27
Standing: PASS_R2_EVIDENCE_TO_STATE_TO_RECORD
Truth role: decision-support and learning substrate, not investment truth, recommendation authority, owner risk appetite, or external financial effect authority.

## Closed seam

Explicit evidence claims -> Decision State Claim Registry -> Decision State Projection -> External Model Atlas + Owner Risk Budget -> Decision Router -> Frozen Decision Record -> strictly later Outcome Observation -> Ex-post Measurement.

R2 removes caller-authored state tags from the read circuit. State tags are projected only from explicit, time-bounded evidence claims that bind producer identity/class, evidence kind, SHA-256 evidence digest, observation time, validity deadline and ACTIVE standing. Unknown, expired, future, duplicate or contract-mismatched claims are rejected.

RISK_BUDGET_SET is deliberately absent from the state-claim registry. The read circuit derives owner risk-budget standing from config/portfolio_risk_budget.json, so caller evidence cannot mint owner risk appetite.

## Frozen decision record

build_decision_record content-addresses the decision-support episode and freezes decision identity/timestamp/objective/horizon, accepted/rejected claims, projected state tags, model routes and authority digests for the model atlas, risk budget and state-claim registry. persist_decision_record provides content-addressed LOCAL_STATE persistence with readback equality and collision rejection.

## Outcome boundary

attribute_decision_outcome accepts only strictly post-decision observations. It can measure realized and benchmark-relative returns while explicitly claiming neither causality nor skill and never treating one outcome as model validation.

## Live canary

Runtime Job job-01a0df43-e386-7a32-95fd-d21934abd6ff projected MACRO_STATE_AVAILABLE and VALUATION_SIGNAL_AVAILABLE, returned RESEARCH_ONLY_RISK_BUDGET_UNSET, produced record sha256:afbb395318488f040469967be159b8d531e9dcfbd2a114f1225d02a6fb6c65b1, measured later excess return 0.03, and reported causalAttribution=false, skillClaimed=false and externalFinancialWritesAttempted=false.

## Verification

Owner-native Capital verification passed in Runtime Job job-01a0df57-94a9-7fa0-abcb-20784ff9bf47: ruff PASS; pytest 401 passed; 11 provider-bound tests deselected; 0 failed. Current-state readback reports 13 external models, 13 evidence-claim routes, manual state tags disabled in the read circuit, 47 registry entries (42 canonical), risk budget UNSET, execution NON_LIVE and external financial effects disabled.

## Next frontier

R2 does not manufacture model outputs. The next frontier is provider/model-specific evidence production for mature valuation, quality, momentum, trend, macro, volatility and execution-cost components, each with prospective validation and explicit currentness.
