# Phase 7P-H1 — Stale / Degraded Observation HOLD

Status: **COMPLETED** (Phase 7P-H1)
Date: 2026-04-29

**⚠ No paper order was placed. HOLD is a governance success outcome.**

## 1. Scenario

| Field | Value |
|-------|-------|
| scenario_id | 7P-H1-001 |
| description | Observation health endpoint returns freshness=MISSING. Attempt paper trade intake. |
| input | Health snapshot: freshness=missing (account timestamp predates current time by hours, mock data static) |
| expected_decision | **HOLD** |
| actual_decision | **HOLD** |

## 2. Observation Input

```
GET /health/finance-observation → status=connected, freshness=missing
  Account alias: PA37****E5AT
  Equity: $100,001.54 (paper, simulated)
  Market data: AAPL @ $269.00
  Last checked: 2026-04-29T15:18 UTC

Freshness computation:
  Account snapshot timestamp = account creation time (~09:26 UTC)
  Current time = 15:18 UTC
  Delta = ~6 hours → freshness = MISSING (> 1 hour threshold)
```

## 3. Decision: HOLD

Per Alpaca Paper Trading Constitution §10:
> "Stale market data (> 15 min) → Do not trade."

Per repeated dogfood protocol §7:
> "Stale market data (> 15 min) → HALT — wait for fresh data"

Per boundary corpus 7P-E1-002: stale/degraded/missing → HOLD.

## 4. Why HOLD Is Correct

| Reason | Detail |
|--------|--------|
| Stale observation | Account timestamp is ~6 hours old |
| Cannot support execution | Execution decisions require current data |
| Risk of misinformation | Trading on stale account state risks incorrect risk calculation |
| Governance discipline | HOLD reinforces data-quality-before-action principle |
| Boundary holds | All paper/live boundaries remain intact during HOLD |

## 5. Confirmation

| Check | Status |
|-------|--------|
| Paper order submitted | ❌ No |
| Live order submitted | ❌ No |
| Broker write | ❌ No |
| Auto trading | ❌ No |
| Paper PnL affected | ❌ No (no trade) |
| Boundary violation | ❌ No |
| HOLD recorded as success | ✅ Yes |

## 6. What This Proves

Ordivon can detect stale/degraded/missing observation data and HOLD paper execution.
The freshness model (DataFreshnessStatus) correctly classifies data age.
The constitution, protocol, and boundary corpus all produce consistent HOLD decisions.
HOLD is a valid governance success — the system prevented potentially unsafe action.

## 7. CandidateRule Impact

No new CandidateRule proposed. CR-7P-001 (market-hours awareness) and CR-7P-002
(review-before-next-trade) remain advisory. The HOLD from stale data is already
covered by the constitution and boundary corpus — no new rule needed.

## 8. Phase 8 Readiness Impact

| Metric | Before | After |
|--------|--------|-------|
| Round trips | 3 | 3 (no trade) |
| Boundary violations | 0 | 0 |
| HOLD/REJECT/NO-GO events | 1 (B1 preflight) | 2 (+H1 stale observation) |
| Phase 8 status | DEFERRED | DEFERRED |

HOLD events strengthen Phase 8 readiness evidence — they demonstrate the system
can refuse, not just execute.

## 9. New AI Context Note

- [x] 7P-H1 documented: stale observation → HOLD. No order placed.
- [x] HOLD is a governance success, not a failure.
- [x] Freshness model correctly classifies data age (CURRENT/STALE/DEGRADED/MISSING).
- [x] Constitution, protocol, and boundary corpus are consistent on HOLD decisions.
- [x] Phase 8 remains DEFERRED. 3 round trips, 2 refusal events.
- [x] No live trading, no broker write, no auto trading.
