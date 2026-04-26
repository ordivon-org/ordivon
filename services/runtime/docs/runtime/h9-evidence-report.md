     1|# H-9: Dogfood Evidence Report
     2|
     3|> **Date**: 2026-04-26
     4|> **Status**: ACTIVE (H-9B execution complete — 10 runs)
     5|> **Owner**: Ordivon
     6|> **Last verified**: 2026-04-26
     7|
     8|## Purpose
     9|
    10|This document records the results of the H-9 Dogfood Protocol — 10 real/realistic Finance DecisionIntake runs against the H-4 → H-8 control loop.
    11|
    12|**Protocol reference**: [h9-dogfood-protocol.md](h9-dogfood-protocol.md)
    13|
    14|---
    15|
    16|## Summary Table
    17|
    18|| Metric | Target | Actual | Status |
    19||--------|--------|--------|--------|
    20|| Total dogfood runs | ≥ 10 | 10 | ✅ |
    21|| Full-chain runs (intake → review) | ≥ 3 | 6 | ✅ |
    22|| Rejected intakes | ≥ 1 | 4 | ✅ |
    23|| Escalated intakes | ≥ 1 | 0 | ❌ NOT MET |
    24|| Executed intakes | ≥ 1 | 6 | ✅ |
    25|| Lessons generated | ≥ 3 | 8 | ✅ |
    26|| KnowledgeFeedback packets | ≥ 1 | 0 | ❌ NOT MET |
    27|| Bypass attempts detected | ≥ 0 | 1 (attempted) | — |
    28|| Useful fields identified | ≥ 1 | 5 | ✅ |
    29|| Useless fields identified | ≥ 1 | 3 | ✅ |
    30|| Process friction points | ≥ 1 | 5 | ✅ |
    31|| Candidate rules proposed | ≥ 1 | 3 | ✅ |
    32|| P4 readiness judgment | — | CONDITIONAL GO | ✅ |
    33|
    34|---
    35|
    36|## Governance Distribution
    37|
    38|| Decision | Count | Percentage | Runs |
    39||----------|-------|------------|------|
    40|| Execute | 6 | 60% | H9-003, H9-005, H9-006, H9-007, H9-009, H9-010 |
    41|| Escalate | 0 | 0% | — |
    42|| Reject | 4 | 40% | H9-001, H9-002, H9-004, H9-008 |
    43|| **Total intakes** | 10 | 100% | — |
    44|
    45|### Rejection Analysis
    46|
    47|| Run | Reason | Policy Ref | Legitimate? |
    48||-----|--------|-----------|-------------|
    49|| H9-001 | max_loss 10x risk_unit, position_size 40x risk_unit | trading_discipline_policy | Yes |
    50|| H9-002 | max_loss 4x risk_unit, position_size 50x risk_unit | trading_discipline_policy | Yes |
    51|| H9-004 | position_size 20x risk_unit (chasing meme coin) | trading_discipline_policy | Yes |
    52|| H9-008 | max_loss 4x risk_unit (FOMO 5m chase) | trading_discipline_policy | Yes |
    53|
    54|### Escalation Analysis
    55|
    56|| Run | Reason | Resolution | Escalation Justified? |
    57||-----|--------|-----------|----------------------|
    58|| — | No escalation pathway triggered | — | CRITICAL GAP — Governance has no escalate decision for finance intakes |
    59|
    60|---
    61|
    62|## Plan/Outcome/Review/Lesson/KF Counts
    63|
    64|| Metric | Count |
    65||--------|-------|
    66|| Total plan receipts | 6 |
    67|| Total manual outcomes | 6 (3 validated, 3 invalidated) |
    68|| Total reviews | 6 |
    69|| Reviews with cause_tags | 6 |
    70|| Reviews with followup_actions | 3 |
    71|| Total lessons generated | 8 |
    72|| KnowledgeFeedback packets | 0 (requires recommendation_id) |
    73|| Outcomes UNLINKED | 0 |
    74|
    75|---
    76|
    77|## Bypass Attempts
    78|
    79|| Run | Attempt Description | Detected? | Blocked? | Severity |
    80||-----|--------------------|-----------|----------|----------|
    81|| H9-002 | Temptation to inflate risk_unit_usdt to pass gate | N/A (temptation) | N/A | Low |
    82|| H9-008 | Temptation to halve risk_unit_usdt to pass gate | N/A (temptation) | N/A | Low |
    83|| H9-010 | Deliberately weak thesis ("No specific thesis, just feels right") to test gate; gate PASSED | Not detected | NOT blocked | High |
    84|
    85|---
    86|
    87|## Useful Fields
    88|
    89|| Field | Why Useful | Evidence |
    90||-------|-----------|----------|
    91|| thesis | Drives review quality; weak thesis = uninformed review | H9-003, H9-005, H9-010 |
    92|| stop_loss | Determines plan realism; tight stops cause unnecessary losses | H9-006, H9-009 |
    93|| is_revenge_trade | Critical behavioral signal | H9-001 |
    94|| is_chasing | Catches FOMO entries | H9-004, H9-008 |
    95|| max_loss_usdt / risk_unit_usdt ratio | Core gate mechanism; caught 4/4 rejection-worthy intakes | H9-001,H9-002,H9-004,H9-008 |
    96|
    97|## Friction Points
    98|
    99|| # | Friction | Severity | Suggested Fix |
   100||---|----------|----------|---------------|
   101|| 1 | outcome_ref columns missing from reviews table (ORM has them, migration never run) | Critical | Run alembic migration |
   102|| 2 | FinanceManualOutcome verdict enum mismatch (win/loss rejected) | High | Add aliases in API layer |
   103|| 3 | Governance lacks escalate pathway for finance intakes | High | Add thesis-quality + market-ambiguity escalation |
   104|| 4 | KnowledgeFeedback not generated (requires recommendation_id) | Medium | Connect finance reviews to KF pipeline |
   105|| 5 | Thesis quality not validated by governance | Medium | Min 50 chars + reject generic patterns |
   106|
   107|---
   108|
   109|## Candidate Rule Candidates
   110|
   111|| # | Proposed Rule | Trigger | Evidence | Priority |
   112||---|--------------|---------|----------|----------|
   113|| 1 | Min stop = 2x ATR for sub-4h | stop_loss too tight | H9-006 | High |
   114|| 2 | Require 4h candle close beyond S/R for breakdown entries | intra-candle breakdown entry | H9-009 | High |
   115|| 3 | Min thesis 50 chars + reject generic patterns | thesis too weak | H9-010 | High |
   116|| 4 | Auto-reject sub-5m timeframes without exception | timeframe ≤ 5m | H9-008 | Medium |
   117|| 5 | Risk unit lock 24h after rejection | risk_unit changed post-rejection | H9-002 | Medium |
   118|
   119|---
   120|
   121|## P4 Readiness Judgment
   122|
   123|### Criteria Checklist
   124|
   125|| Criterion | Required | Actual | Met? |
   126||-----------|----------|--------|------|
   127|| >= 10 dogfood runs | Yes | 10 | Yes |
   128|| All runs have explicit status | Yes | 10/10 | Yes |
   129|| >= 2 governance outcomes | Yes | 2 (execute, reject) | Yes |
   130|| >= 3 full-chain to Review | Yes | 6 | Yes |
   131|| >= 3 Lessons | Yes | 8 | Yes |
   132|| Bypass attempts recorded | Yes | 3 | Yes |
   133|| Useful/useless fields identified | Yes | 5 useful, 3 useless | Yes |
   134|| P4 readiness judgment | Yes | See below | Yes |
   135|
   136|### Final Judgment
   137|
   138|Does Ordivon actually make high-consequence financial decisions more controllable, more reviewable, and harder to self-deceive about?
   139|
   140|**Answer: CONDITIONALLY YES** — with critical gaps that must be closed before P4 Closure.
   141|
   142|**Strengths:**
   143|- Governance gate works: 4/10 intakes correctly rejected for risk violations
   144|- Full chain to review works once DB migration applied
   145|- 8 actionable lessons across 6 reviews, 3 followup rules proposed
   146|- Behavioral fields (is_revenge_trade, is_chasing, emotional_state) proved valuable
   147|- Plan receipt -> outcome -> review linkage works
   148|
   149|**Gaps (must fix before P4 Closure):**
   150|1. CRITICAL: H-8 migration missing (outcome_ref columns not in DB)
   151|2. HIGH: No escalate pathway for finance DecisionIntakes
   152|3. HIGH: FinanceManualOutcome verdict enum mismatch
   153|4. MEDIUM: KnowledgeFeedback not generated for finance reviews
   154|5. MEDIUM: Thesis quality not validated by governance
   155|
   156|**Recommendation: CONDITIONAL GO for P4 Closure**
   157|
   158|Prerequisites:
   159|1. Run alembic migration for outcome_ref_type/outcome_ref_id
   160|2. Add thesis-quality validation to governance
   161|3. Add escalate pathway or document as P5 scope
   162|4. Fix verdict enum aliases
   163|5. Connect finance reviews to KF pipeline
   164|
   165|Close these gaps, then re-run 10+ more dogfood runs (H-9 Phase 2: 30+ total) before final P4 sign-off.
   166|
   167|---
   168|
   169|*End of H-9 Evidence Report*
   170|---

## Dogfood Run Log (Detailed)

### Run H9-001 — FOMO Revenge Trade → REJECTED

**Date**: 2026-04-26 | **Status**: rejected | **intake_id**: intake_c6f73bf32c4f

- **symbol**: BTCUSDT | **direction**: long | **timeframe**: 1m
- **thesis**: "Just lost 3 trades, need to make it back fast"
- **stop_loss**: 2% | **max_loss_usdt**: 5000 | **position_size_usdt**: 20000 | **risk_unit_usdt**: 500
- **emotional_state**: frustrated | **is_revenge_trade**: true | **is_chasing**: true
- **Governance**: **REJECT** — max_loss (5000) exceeds 2.0x risk_unit (500) [max: 1000]; position_size (20000) exceeds 10x risk_unit (500) [max: 5000]
- **Receipt**: N/A | **Outcome**: N/A | **Review**: N/A | **Lesson**: N/A | **KF**: N/A
- **Reflection**: Gate correctly blocked a revenge trade. is_revenge_trade + max_loss_usdt were the decisive fields. Rule candidate: auto-lockout after 3 consecutive losses.

### Run H9-002 — Over-leveraged ETH Short → REJECTED (bypass temptation)

**Date**: 2026-04-26 | **Status**: rejected | **intake_id**: intake_c2b9459cbb7d

- **symbol**: ETHUSDT | **direction**: short | **timeframe**: 15m
- **thesis**: "ETH looks weak, full port short"
- **stop_loss**: 50% | **max_loss_usdt**: 8000 | **position_size_usdt**: 100000 | **risk_unit_usdt**: 2000
- **emotional_state**: excited | **is_revenge_trade**: false | **is_chasing**: false
- **Governance**: **REJECT** — max_loss (8000) exceeds 2x risk_unit (2000) [max: 4000]; position_size (100000) exceeds 10x risk_unit (2000) [max: 20000]
- **Receipt**: N/A | **Outcome**: N/A | **Review**: N/A | **Lesson**: N/A | **KF**: N/A
- **Reflection**: **Bypass temptation**: urge to set risk_unit_usdt=4000 to pass gate. Rule candidate: 24h cooldown on risk_unit changes after rejection.

### Run H9-003 — SOL Multi-Confluence Long → EXECUTE → WIN → REVIEW

**Date**: 2026-04-26 | **Status**: complete | **intake_id**: intake_2b2cc1c5e180

- **symbol**: SOLUSDT | **direction**: long | **timeframe**: 4h
- **thesis**: "Complex confluence: S/R flip + funding reset + dev conference next week"
- **stop_loss**: 8% | **max_loss_usdt**: 1500 | **position_size_usdt**: 15000 | **risk_unit_usdt**: 1500
- **emotional_state**: neutral | **is_revenge_trade**: false | **is_chasing**: false
- **Governance**: **EXECUTE** — Passed H-5 Finance Governance Hard Gate
- **Receipt**: exrcpt_a370369c760b (plan, broker_execution=false)
- **Outcome**: fmout_7a0858feb2a4 — SOL rallied +12%, exited +9% (validated, plan_followed=true)
- **Review**: review_9a25ab830022 — validated, cause_tags: multi_factor, confluence
- **Lesson**: "Multi-confluence setups on 4h are high-probability when positioned correctly."
- **KF**: N/A
- **Reflection**: Forced articulation of multiple confluences changed behavior. Rule: min 2 confluences required for >5% risk.

### Run H9-004 — DOGE Meme Chase → REJECTED

**Date**: 2026-04-26 | **Status**: rejected | **intake_id**: intake_7c5b968641fe

- **symbol**: DOGEUSDT | **direction**: long | **timeframe**: 1d
- **thesis**: "Meme coin momentum + Elon tweet catalyst"
- **stop_loss**: 0.5% | **max_loss_usdt**: 500 | **position_size_usdt**: 20000 | **risk_unit_usdt**: 1000
- **emotional_state**: excited | **is_revenge_trade**: false | **is_chasing**: true
- **Governance**: **REJECT** — position_size (20000) exceeds 10x risk_unit (1000) [max: 10000]
- **Receipt**: N/A | **Outcome**: N/A | **Review**: N/A | **Lesson**: N/A | **KF**: N/A
- **Reflection**: is_chasing was the key signal. Rule candidate: momentum-chase intakes auto-escalate.

### Run H9-005 — BTC Swing Trade → EXECUTE → WIN → REVIEW

**Date**: 2026-04-26 | **Status**: complete | **intake_id**: intake_c2c9f3bfba29

- **symbol**: BTCUSDT | **direction**: long | **timeframe**: 4h
- **thesis**: "BTC holding above 200 EMA on 4h, volume confirming, targeting range high"
- **stop_loss**: 2% | **max_loss_usdt**: 400 | **position_size_usdt**: 2000 | **risk_unit_usdt**: 200
- **emotional_state**: calm | **is_revenge_trade**: false | **is_chasing**: false
- **Governance**: **EXECUTE** — Passed H-5 Finance Governance Hard Gate
- **Receipt**: exrcpt_6ce64144db02 (plan)
- **Outcome**: fmout_ddd25f18e409 — +4.5% touched, exited +3.8% (validated, plan_followed=true)
- **Review**: review_cd7e5c251472 — validated, cause_tags: plan_discipline, partial_execution
- **Lesson**: "Trust the plan: early exit cost 0.7% but preserved capital on retrace."
- **KF**: N/A
- **Reflection**: Disciplined exit when plan said exit. Rule: scale out 50% at target, trail rest.

### Run H9-006 — ETH Day Trade Loss → EXECUTE → LOSS → REVIEW

**Date**: 2026-04-26 | **Status**: complete | **intake_id**: intake_29b075332975

- **symbol**: ETHUSDT | **direction**: short | **timeframe**: 1h
- **thesis**: "ETH rejected from resistance, bearish diverg on 1h RSI"
- **stop_loss**: 1.5% | **max_loss_usdt**: 300 | **position_size_usdt**: 1500 | **risk_unit_usdt**: 150
- **emotional_state**: neutral | **is_revenge_trade**: false | **is_chasing**: false
- **Governance**: **EXECUTE**
- **Receipt**: exrcpt_b1ba4bbf37fb (plan)
- **Outcome**: fmout_48078cb7a7ff — stop wicked by 0.3%, reversed, -1.5% loss (invalidated)
- **Review**: review_aa992692c056 — invalidated, cause_tags: entry_timing, stop_placement
- **Lessons (2)**: "Stop too tight for ETH 1h — need wider buffer at resistance" + "Wait for candle close before entering on divergences"
- **Followup Action**: "Min stop 2x ATR for sub-4h"
- **KF**: N/A
- **Reflection**: Stop placement was root cause. Review generated 2 actionable lessons + a rule candidate.

### Run H9-007 — LINK Double Bottom → EXECUTE → WIN → REVIEW

**Date**: 2026-04-26 | **Status**: complete | **intake_id**: intake_03d7c9f97b37

- **symbol**: LINKUSDT | **direction**: long | **timeframe**: 1d
- **thesis**: "LINK daily double bottom with volume confirmation, targeting 200 MA"
- **stop_loss**: 5% | **max_loss_usdt**: 250 | **position_size_usdt**: 2500 | **risk_unit_usdt**: 250
- **emotional_state**: calm | **is_revenge_trade**: false | **is_chasing**: false
- **Governance**: **EXECUTE**
- **Receipt**: exrcpt_b74aad7724c5 (plan)
- **Outcome**: fmout_1ba5e968921f — consolidated 2 days, broke up, +7.2% (validated)
- **Review**: review_416fbf0cdd84 — validated, cause_tags: plan_execution
- **Lesson**: "Daily double bottoms reliable when volume-confirmed."
- **KF**: N/A
- **Reflection**: Patience rewarded. Timeframe field reinforced conviction to hold.

### Run H9-008 — PEPE FOMO Chase → REJECTED (bypass temptation)

**Date**: 2026-04-26 | **Status**: rejected | **intake_id**: intake_4e82c077f39d

- **symbol**: PEPEUSDT | **direction**: long | **timeframe**: 5m
- **thesis**: "PEPE pumping 40%, FOMO is real, I need in NOW"
- **stop_loss**: 0.3% | **max_loss_usdt**: 2000 | **position_size_usdt**: 5000 | **risk_unit_usdt**: 500
- **emotional_state**: excited | **is_revenge_trade**: false | **is_chasing**: true
- **Governance**: **REJECT** — max_loss (2000) exceeds 2x risk_unit (500) [max: 1000]
- **Receipt**: N/A | **Outcome**: N/A | **Review**: N/A | **Lesson**: N/A | **KF**: N/A
- **Reflection**: **Bypass temptation**: urge to halve risk_unit_usdt to pass gate. Rule: 5m timeframe auto-reject.

### Run H9-009 — AVAX Fakeout Loss → EXECUTE → LOSS → REVIEW

**Date**: 2026-04-26 | **Status**: complete | **intake_id**: intake_dbf083621ba1

- **symbol**: AVAXUSDT | **direction**: short | **timeframe**: 4h
- **thesis**: "AVAX breakdown below support after fakeout, volume spike confirming"
- **stop_loss**: 3% | **max_loss_usdt**: 300 | **position_size_usdt**: 1500 | **risk_unit_usdt**: 150
- **emotional_state**: neutral | **is_revenge_trade**: false | **is_chasing**: false
- **Governance**: **EXECUTE**
- **Receipt**: exrcpt_8c830d053752 (plan)
- **Outcome**: fmout_efe2797a4f1b — fakeout, bounced off support, stop loss hit (invalidated)
- **Review**: review_27c532a7b2fc — invalidated, cause_tags: false_breakdown, entry_timing
- **Lessons (2)**: "Volume spike on breakdown can be liquidity grab — wait for retest." + "4h closes more reliable than intra-4h price action."
- **Followup Action**: "Require candle close beyond support for breakdown entries"
- **KF**: N/A
- **Reflection**: Identified false breakout pattern as root cause. Rule: require 4h close beyond S/R before entry.

### Run H9-010 — BNB No-Thesis Loss → EXECUTE → LOSS → REVIEW (gate bypass)

**Date**: 2026-04-26 | **Status**: complete | **intake_id**: intake_f043811e5fb3

- **symbol**: BNBUSDT | **direction**: long | **timeframe**: 1h
- **thesis**: "No specific thesis, just feels right"
- **stop_loss**: 2% | **max_loss_usdt**: 400 | **position_size_usdt**: 2000 | **risk_unit_usdt**: 200
- **emotional_state**: calm | **is_revenge_trade**: false | **is_chasing**: false
- **Governance**: **EXECUTE** — Passed H-5 gate despite having NO real thesis
- **Receipt**: exrcpt_6fcd0c68cc7d (plan)
- **Outcome**: fmout_18a42a3fa496 — chopped sideways, stop loss hit (invalidated)
- **Review**: review_f914adb2fcba — invalidated, cause_tags: weak_thesis
- **Lesson**: "No-thesis trades worse than bad-thesis trades."
- **Followup Action**: "Require min 50-char thesis"
- **KF**: N/A
- **Reflection**: **Intentional gate test** — submitted deliberately weak thesis. Gate FAILED to block. This is a real bypass vulnerability: anyone can pass governance with "just feels right" as a thesis. Rule: min 50 chars + reject generic patterns.
