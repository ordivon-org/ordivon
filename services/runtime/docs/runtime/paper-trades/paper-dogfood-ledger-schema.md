# Paper Dogfood Ledger — JSONL Schema

Status: **ACTIVE** | Date: 2026-04-29 | Phase: 7P-D1

**⚠ JSONL ledger is evidence, not execution authority.**

## 1. Purpose

Machine-readable evidence for Phase 7P Alpaca Paper dogfood. Not an execution source.
Checker validates consistency; does NOT authorize trades.

## 2. Event Model

Required fields: event_id, trade_id, event_type, phase, timestamp, environment,
live_order, paper_only, evidence_refs, candidate_rule_refs, boundary_violation, notes.

Optional: symbol, order_id_masked, decision, status, simulated_pnl.

## 3. Event Types

- TRADE_INTAKE_ACCEPTED / TRADE_REJECTED / TRADE_HELD / TRADE_NO_GO
- ORDER_SUBMITTED / ORDER_PENDING / ORDER_FILLED / ORDER_CLOSED
- ORDER_EXPIRED / ORDER_REJECTED
- OUTCOME_CAPTURED / REVIEW_COMPLETED
- CANDIDATE_RULE_OBSERVED / LEDGER_STATUS

## 4. Invariants (16 total)

| # | Invariant |
|---|-----------|
| 1 | All lines valid JSON |
| 2 | Unique event_id |
| 3 | environment = "paper" |
| 4 | live_order = false |
| 5 | paper_only = true |
| 6 | HOLD/REJECT/NO-GO have no order_id_masked |
| 7 | Completed trade requires ORDER_SUBMITTED + FILLED + CLOSED + OUTCOME + REVIEW |
| 8 | Pending does not count as completed |
| 9 | Pending trade blocks next trade |
| 10 | CandidateRule status = "advisory" |
| 11 | No CandidateRule marked Policy or RiskEngine-active |
| 12 | Paper PnL notes contain "simulated" |
| 13 | boundary_violation is boolean |
| 14 | Phase 8 readiness does not auto-advance |
| 15 | No live execution authority exists |
| 16 | Duplicate IDs rejected |

## 5. Current Ledger Summary

- 28 events
- 3 completed round trips (PT-001/002/003)
- 1 pending (PT-004 NFLX limit $90)
- 1 HOLD, 2 REJECT, 2 NO-GO
- 0 boundary violations
- $+1.54 cumulative simulated PnL
- Phase 8: 3/10 DEFERRED
- **PT-005 BLOCKED**

## 6. Usage

```
uv run python scripts/check_paper_dogfood_ledger.py
```

Exit 0 = all invariants pass. Non-zero = violations found.

## 7. New AI Warning

Fresh AI reading this ledger must NOT treat it as permission to trade.
The checker says whether evidence is consistent; it does NOT authorize execution.
PT-005 requires explicit human GO, protocol criteria, and ledger status = no blocking.
