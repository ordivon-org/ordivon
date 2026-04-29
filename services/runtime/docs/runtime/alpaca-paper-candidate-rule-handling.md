# Alpaca Paper CandidateRule Handling

Status: **DOCUMENTED** (Phase 7P-R)
Date: 2026-04-29
Phase: 7P-R
Tags: `alpaca`, `paper`, `candidate-rule`, `advisory`, `policy`

## 1. Purpose

This document defines how CandidateRules generated from Alpaca Paper dogfood
are handled. Paper CandidateRules are valuable governance observations, but
they are NOT Policies, NOT activated in RiskEngine, and NOT evidence for
live trading decisions.

## 2. Current CandidateRules

### CR-7P-001: Market-Hours Awareness Gate

| Field | Value |
|-------|-------|
| Source | 7P-3 first paper trade (after-hours submission, +$11.78 gap) |
| Observation | After-hours paper trade intake resulted in fill at market open with large price gap vs after-hours reference |
| Proposal | Paper trade intake should include a market-hours check to set fill-timing expectations |
| Status | **Advisory only** |
| Not Policy | Cannot block trades |
| Not activated | No RiskEngine integration |
| Escalation criteria | ≥2 weeks observation, ≥3 interceptions across paper AND live trades, documented bypass conditions |
| Last reviewed | 7P-Z formal review |

### CR-7P-002: Pre-Trade Review Completion Gate

| Field | Value |
|-------|-------|
| Source | 7P-R repeated dogfood protocol |
| Observation | Without a review-before-next-trade rule, paper dogfood risks accumulating unreviewed trades |
| Proposal | No next paper trade until previous trade review is complete |
| Status | **Advisory only** |
| Enforced by | Protocol (this document), not code |
| Not Policy | Adapter does not block sequential orders |

## 3. CandidateRule Lifecycle

```
Paper Trade → Review → Lesson Observation → CandidateRule (advisory)
                                                   ↓
                                          ≥2 weeks observation
                                          ≥3 real interceptions
                                          documented bypass conditions
                                          stakeholder sign-off
                                                   ↓
                                          PolicyProposal → EvidenceGate
                                          → ShadowEvaluator → ApprovalGate
                                          → PolicyRecord (still not active_enforced)
```

**Critical**: Paper-only observations NEVER reach the evidence gate for live
Policy promotion. Paper evidence is insufficient for Policy. Live trading
evidence (Phase 8+) is required for Policy consideration.

## 4. Paper vs Live CandidateRule

| Property | Paper CandidateRule | Live CandidateRule |
|----------|-------------------|-------------------|
| Evidence source | Simulated paper trades | Real trades with real money |
| Financial risk | Zero | Real capital at risk |
| Policy eligibility | ❌ NO (insufficient) | ⏳ After ≥3 real interceptions |
| Review value | Process observation only | Process + financial outcome |
| Recommendation weight | Advisory, low confidence | Advisory, higher confidence |

## 5. Handling Rules

| Rule | Value |
|------|-------|
| Paper CR can be proposed | ✅ At any time |
| Paper CR can be advisory | ✅ Always |
| Paper CR can become Policy | ❌ NOT without live evidence |
| Paper CR can activate RiskEngine | ❌ NEVER (Phase 5 closure) |
| Paper CR can block live trading | ❌ NEVER |
| Paper CR must reference specific trade | ✅ Required |
| Paper CR must be re-evaluated after live trades | ✅ When Phase 8 begins |

## 6. What To Do With a Paper CandidateRule

1. **Record it** — in the trade review document
2. **Reference the evidence** — specific trade ID, date, observation
3. **Mark as advisory** — "CandidateRule only, not Policy"
4. **Re-evaluate later** — when Phase 8 provides live evidence
5. **Do NOT activate** — no RiskEngine, no Policy record, no enforcement

## 7. Example: Proper Handling

```
❌ WRONG: "CR-7P-001 says after-hours trades should be blocked. Add to RiskEngine."
✅ RIGHT: "CR-7P-001 observes that after-hours intake produces large fill gaps.
   This is advisory. Re-evaluate after Phase 8 live trades. Do not activate."
```
