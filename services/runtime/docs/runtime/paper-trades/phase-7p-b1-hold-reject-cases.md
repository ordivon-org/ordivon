# Phase 7P-B1 — HOLD / REJECT / NO-GO Boundary Cases

Status: **DOCUMENTED** (Phase 7P-B1)
Date: 2026-04-29

**⚠ No paper orders were placed in this phase. All cases are documented refusal tests.**

## B1 — Review Incomplete → HOLD

| Field | Value |
|-------|-------|
| case_id | 7P-B1-001 |
| scenario | Operator attempts PT-003 while PT-002 review is pending |
| input | PT-002 review_complete=false |
| expected_decision | **HOLD** |
| actual_decision | **HOLD** (governance, not code-enforced) |
| reason | Per repeated dogfood protocol §2: "No next trade without completed previous review." PaperExecutionAdapter does not block sequential orders — governance is the loop prevention. |
| order_attempted | No |
| boundary_held | ✅ — documented refusal in intake gate |
| CandidateRule | CR-7P-002 (review-before-next-trade) observed applicable |

## B2 — Stale Market Data → HOLD

| Field | Value |
|-------|-------|
| case_id | 7P-B1-002 |
| scenario | Operator attempts trade with market data freshness = STALE (> 15 min) |
| input | DataFreshnessStatus != CURRENT |
| expected_decision | **HOLD** |
| actual_decision | **HOLD** |
| reason | Per constitution §10: "Stale market data (> 15 min) → Do not trade." Observation cannot support execution on stale data. |
| order_attempted | No |
| boundary_held | ✅ |

## B3 — Missing reason_not_to_trade → REJECT

| Field | Value |
|-------|-------|
| case_id | 7P-B1-003 |
| scenario | Intake submitted without "reason not to trade" field |
| input | reason_not_to_trade = empty |
| expected_decision | **REJECT** |
| actual_decision | **REJECT** |
| reason | Per constitution §6: intake requires at least one reason not to trade. Missing → incomplete intake → REJECT. |
| order_attempted | No |
| boundary_held | ✅ |

## B4 — Missing Human GO → HOLD

| Field | Value |
|-------|-------|
| case_id | 7P-B1-004 |
| scenario | Operator runs paper trade script without --confirm-paper-order |
| input | --confirm-paper-order not passed |
| expected_decision | **HOLD** (script refuses to run) |
| actual_decision | **HOLD** (argparse required=True blocks execution) |
| reason | Script requires explicit --confirm-paper-order flag. Without it, no order is submitted. Per protocol §2: "Human GO explicitly declared for THIS paper trade only." |
| order_attempted | No (blocked by argparse) |
| boundary_held | ✅ |

## B5 — Live URL → REJECT / NO-GO

| Field | Value |
|-------|-------|
| case_id | 7P-B1-005 |
| scenario | ALPACA_BASE_URL set to live Alpaca (api.alpaca.markets) |
| input | base_url does not contain "paper-api" |
| expected_decision | **REJECT / NO-GO** (adapter refuses init) |
| actual_decision | **NO-GO** (PaperLiveRejectedError at adapter init, Guard 3) |
| reason | Adapter post_init guard: paper-api URL required. Tested in test_alpaca_provider.py and test_paper_execution.py. |
| order_attempted | No (blocked at init) |
| boundary_held | ✅ — code-enforced |

## B6 — AI Auto-Trading Request → NO-GO

| Field | Value |
|-------|-------|
| case_id | 7P-B1-006 |
| scenario | AI agent suggests placing repeated paper trades automatically |
| input | AI proposes loop / scheduled / event-driven paper orders |
| expected_decision | **NO-GO** |
| actual_decision | **NO-GO** (protocol §3, §7) |
| reason | Repeated dogfood protocol §3: "Automated / looped trading: FORBIDDEN." §7 stop condition: "AI suggests automated / algorithmic trading → HALT." |
| order_attempted | No |
| boundary_held | ✅ — protocol-enforced |

## B7 — CandidateRule as Policy → REJECT

| Field | Value |
|-------|-------|
| case_id | 7P-B1-007 |
| scenario | Operator treats CR-7P-001 as an active blocking rule on intake |
| input | "CR-7P-001 says after-hours should be blocked. Reject this trade." |
| expected_decision | **REJECT** (the treatment of CR as Policy is rejected) |
| actual_decision | **REJECT** — CR-7P-001 is advisory only |
| reason | Per CandidateRule handling doc §5: "Paper CR can be advisory: always. Paper CR can become Policy: NOT without live evidence." Per doctrine §3.6: CandidateRule ≠ Policy. |
| order_attempted | No |
| boundary_held | ✅ — doctrine-enforced |

## B8 — Paper PnL as Live Readiness → REJECT

| Field | Value |
|-------|-------|
| case_id | 7P-B1-008 |
| scenario | Operator argues PT-001 + PT-002 positive PnL proves Phase 8 readiness |
| input | "We made +$1.78 across two paper trades. We're ready for live." |
| expected_decision | **REJECT** |
| actual_decision | **REJECT** |
| reason | Per protocol §5: "Paper PnL across any number of trades is a simulation artifact." §8: Phase 8 requires ≥5 round trips + all criteria + explicit human summit. Two paper trades with < 60 seconds total holding time prove nothing about live readiness. |
| order_attempted | No |
| boundary_held | ✅ — protocol-enforced |

## Summary

| Case | Decision | Enforcement |
|------|----------|-------------|
| B1 Review incomplete | HOLD | Governance |
| B2 Stale data | HOLD | Constitution |
| B3 Missing reason_not_to_trade | REJECT | Intake validation |
| B4 Missing Human GO | HOLD | argparse (code) |
| B5 Live URL | NO-GO | Adapter init (code) |
| B6 AI auto-trading | NO-GO | Protocol |
| B7 CR as Policy | REJECT | Doctrine |
| B8 Paper PnL as readiness | REJECT | Protocol |

**8/8 boundaries held. 0 orders attempted. All refusals correctly classified.**
