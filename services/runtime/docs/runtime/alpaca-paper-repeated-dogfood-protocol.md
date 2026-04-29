# Alpaca Paper Repeated Dogfood Protocol

Status: **DOCUMENTED** (Phase 7P-R)
Date: 2026-04-29
Phase: 7P-R
Tags: `alpaca`, `paper`, `dogfood`, `protocol`, `repeated`, `governance`

## 1. Purpose

Repeated Alpaca Paper dogfood tests Ordivon's governance **durability**, not
trading profitability. The question is: can the intake → receipt → execution →
outcome → review pipeline handle multiple trades without degrading, bypassing
boundaries, or accumulating unresolved issues?

The first paper trade (AAPL, +$1.52, 22 minutes) validated the pipeline once.
Repeated trades validate whether the pipeline holds under repetition.

## 2. Entry Criteria for Next Paper Trade

A new paper trade may only be initiated when ALL of these are true:

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Previous trade review is COMPLETE | Required |
| 2 | No open paper position (flat) | Required |
| 3 | Outcome captured for previous trade | Required |
| 4 | All CandidateRules from previous trade handled as advisory | Required |
| 5 | No unresolved boundary issue | Required |
| 6 | Market data freshness is CURRENT or STALE (< 15 min) | Required |
| 7 | Human GO explicitly declared for THIS paper trade only | Required |
| 8 | Readiness gate (9 checks) re-executed | Required |

**Rule**: No next trade without completed previous review. This is enforced by
process, not by code — the PaperExecutionAdapter does not block sequential orders,
but Ordivon governance requires review-before-next-trade as a constitutional rule.

## 3. Frequency Limits

| Limit | Value |
|-------|-------|
| Max paper trades per day | 3 |
| Max paper trades per week | 10 |
| Max concurrent open positions | 1 |
| Automated / looped trading | ❌ FORBIDDEN |
| Cooldown after loss | 1 hour minimum |
| Cooldown after review failure | 24 hours or until review completed |
| Cooldown after ambiguous outcome | Until resolved |

**Rule**: If the adapter is called in a loop, the operator must stop immediately.
The paper execution adapter has no loop prevention — governance is the loop
prevention.

## 4. Required Receipt Chain Per Trade

Every paper trade must produce a COMPLETE document trail:

```
1. Intake (with readiness gate)
2. Plan Receipt
3. Execution Receipt
4. Fill Reconciliation
5. Outcome
6. Formal Review
7. Lesson Candidate (at least one per trade)
```

Missing any link in the chain blocks the next trade.

## 5. Paper PnL Interpretation

| PnL | Meaning | Action |
|-----|---------|--------|
| Positive | Paper simulation artifact | Do NOT treat as strategy validation |
| Negative | Paper simulation artifact | Do NOT treat as strategy failure |
| Zero | Paper simulation artifact | Do NOT treat as breakeven proof |

**Rule**: Paper PnL across any number of trades is a **simulation artifact**.
It does not prove edge, does not disprove edge, and must never be used to
justify live trading, position sizing increases, or strategy changes.

After N paper trades, the governance question is:
- "Did the pipeline hold across N trades?" — NOT "Was the cumulative PnL positive?"

## 6. CandidateRule Handling

| Rule | Value |
|------|-------|
| CR-7P-001 (market-hours gate) | Advisory only. Not Policy. |
| Future paper CandidateRules | Advisory only. Not Policy. |
| Escalation threshold | ≥2 weeks observation + ≥3 real interceptions (doctrine §3.6) |
| Auto-activation | ❌ FORBIDDEN |
| Live trading implication | ❌ FORBIDDEN |

Paper trades may generate CandidateRules more freely than live trades because
the risk of false positives is zero (no real money). But paper-only rules must
not be promoted to Policy without live evidence.

See `docs/runtime/alpaca-paper-candidate-rule-handling.md` for full procedure.

## 7. Stop / HOLD Conditions

The repeated dogfood must HALT if any of these occur:

| Condition | Action |
|-----------|--------|
| Missing fill reconciliation | HALT — resolve before next trade |
| Stale market data (> 15 min) | HALT — wait for fresh data |
| Incomplete outcome (> 24 hours) | HALT — complete before next trade |
| Missed review (> 48 hours) | HALT — catch up on reviews |
| Repeated deviation from plan (3+ trades) | HALT — review process |
| Paper/live wording ambiguity in any doc | HALT — fix wording |
| AI suggests automated / algorithmic trading | HALT — governance review |
| Paper PnL used as profit proof | HALT — re-education |
| ReadOnlyAdapterCapability modified | HALT — security incident |
| Live Alpaca URL appears in any path | HALT — security incident |

## 8. Phase 8 Readiness Criteria

Phase 8 ($100 live manual micro-capital) may be reconsidered only when:

- [ ] ≥5 completed paper round trips with full document trails
- [ ] Zero live boundary violations across all paper trades
- [ ] All reviews complete, no backlog
- [ ] No unresolved CandidateRules
- [ ] No pressure to automate or increase frequency
- [ ] Explicit human Stage Summit declaration
- [ ] Live broker selection finalized (Futu or IB)
- [ ] $100 funded and ready in chosen live account
- [ ] Live paper/live boundary documents updated

**Phase 8 is NOT automatic.** The paper dogfood protocol continues until
the operator explicitly declares readiness. There is no paper-trade-count
threshold that triggers live trading.

## 9. Protocol Governance

This protocol is a governance document, not code. It is enforced by:
- Human operator discipline
- Document trail completeness checks
- AI context (AGENTS.md) clarity
- CandidateRule observability

It does NOT:
- Block orders in the adapter (the adapter has no trade-count awareness)
- Activate any RiskEngine policy
- Create any active Policy
