# Finance Live Micro-Capital Constitution

Status: **DRAFT — DEFERRED TO PHASE 8** (Phase 7A, reclassified 7A-R)
Date: 2026-04-29
Phase: 7A-R
Tags: `finance`, `constitution`, `micro-capital`, `manual`, `live`, `deferred`

> **⚠ DEFERRED LIVE DRAFT**: This constitution is a future live-stage draft.
> It is NOT active execution authorization. The next dogfood stage is
> **Alpaca Paper Trading** (Phase 7P), not real-money live trading.
> Live broker write / API order placement remains NO-GO.
> See `AGENTS.md` for the corrected roadmap.

## 1. Purpose

This constitution governs Ordivon's first manual live finance dogfood.
It is a **$100 micro-capital experiment** designed to test:

- Trading discipline under real market pressure
- Governance workflow completeness (intake → receipt → outcome → review)
- Evidence quality and freshness in live observation
- Human decision quality with Ordivon governance support
- CandidateRule generation from real trading experience

It is **not** a profit-maximization experiment. A financial loss that follows
this constitution is acceptable. A financial loss without governance is not.

## 2. Capital

| Rule | Value |
|------|-------|
| Initial capital | **$100.00 USD** (or equivalent) |
| Max total loss | **$50.00 USD** (hard stop — dogfood ends) |
| Additional capital | **FORBIDDEN** without new Stage Review |
| Profit reinvestment | Allowed within the same phase |
| Account type | Cash only — no margin |

## 3. Execution Model

### 3.1 Manual Execution Only

All trades are placed **manually by a human** outside Ordivon.
Ordivon does not place orders. Ordivon provides:

| Ordivon Provides | Human Does |
|-----------------|------------|
| Pre-trade intake form | Reads intake and decides |
| Risk budget check | Chooses execution venue |
| Market data freshness check | Places manual order |
| Plan receipt (governance decision) | Records actual fill |
| Outcome capture form | Enters outcome data |
| Post-trade review queue | Conducts self-review |
| CandidateRule extraction | Reviews candidate lessons |

### 3.2 Forbidden Execution

| Action | Status |
|--------|--------|
| Broker API order placement | ❌ NO-GO |
| Order cancellation via Ordivon | ❌ NO-GO |
| Order modification via Ordivon | ❌ NO-GO |
| Automated / algorithmic trading | ❌ NO-GO |
| Copy-trading / signal-following | ❌ NO-GO |
| Trading while outcome from prior trade is missing | ❌ NO-GO |

### 3.3 Observation Only

Alpaca Paper Trading remains the **observation and paper reference** only.
Live brokerage selection for actual execution is a separate Phase 7 decision
(Futu or Interactive Brokers — see `docs/runtime/finance-observation-provider-plan.md`).

The observation layer may continue to read Alpaca Paper data for market
reference, but paper fills are not real and must not be used for outcome
capture.

## 4. Instrument Scope

| Rule | Value |
|------|-------|
| Asset class | **US equities (common stock only)** |
| Excluded | Options, futures, forex, crypto, ETFs, leveraged products, penny stocks |
| Broker | To be selected (Futu or IB — Phase 7B) |
| Symbol limit | Max 3 symbols under active observation |
| Minimum price | $5.00/share (no penny stocks) |
| Maximum price | No single position > 50% of capital |

## 5. Risk Rules

| Rule | Value |
|------|-------|
| Max per-trade risk | **$5.00 USD (5% of capital)** |
| Max daily loss | **$15.00 USD (15% of capital)** |
| Max weekly loss | **$25.00 USD (25% of capital)** |
| Loss-streak stop | **3 consecutive losing trades → stop for 24 hours** |
| Cooldown after loss | Minimum 1 hour between trades after a loss |
| Max trades per day | 3 |
| Max trades per week | 10 |
| Max concurrent positions | 1 |
| Fee/slippage tracking | Mandatory — must be recorded in outcome capture |
| Invalidation before entry | Mandatory — "what would prove this trade wrong?" |

## 6. Pre-Trade Intake (Mandatory)

Every trade must have a completed intake before execution.
Intake must be timestamped and cannot be backfilled.

| Field | Required | Description |
|-------|----------|-------------|
| symbol | Yes | Ticker symbol |
| thesis | Yes | Why this trade? What edge? |
| setup | Yes | Technical/fundamental setup description |
| entry plan | Yes | Price, order type, timing |
| invalidation | Yes | What would prove the thesis wrong? |
| stop condition | Yes | Price or condition to exit |
| max risk | Yes | In dollars and % of capital |
| evidence refs | Yes | Links to charts, news, data |
| market data freshness | Yes | When was price data last checked? |
| account state | Yes | Current equity, available cash |
| reason NOT to trade | Yes | Write at least one reason to skip this trade |

## 7. Plan Receipt (Mandatory)

After intake is reviewed, a plan receipt is generated before execution.

| Field | Value |
|-------|-------|
| governance decision | INTAKE_ACCEPTED (manual only) or INTAKE_REJECTED |
| allowed action | Manual market order only |
| forbidden action | Automated / broker API order |
| risk budget check | Within limits? Y/N |
| exit plan | Trailing stop, time stop, or invalidation-based |
| rollback plan | Immediate close if loss exceeds $3 |
| evidence refs | Link to intake |

## 8. Outcome Capture (Mandatory)

After every trade, outcome must be captured within 24 hours.

| Field | Required | Description |
|-------|----------|-------------|
| entry price | Yes | Actual fill price |
| exit price | Yes | Actual exit price |
| quantity | Yes | Number of shares |
| fees | Yes | Commission + regulatory fees |
| slippage | Yes | Expected vs actual entry |
| PnL | Yes | Gross and net |
| plan followed? | Yes | Y/N — if N, describe deviation |
| rule violation? | Yes | Any constitution rule broken? |
| emotional state | Optional | Relevant discipline note |
| lesson candidate | Yes | What was learned? |

## 9. Post-Trade Review (Mandatory)

Every completed outcome must be reviewed. Reviews may generate CandidateRules.

| Rule | Value |
|------|-------|
| Review required | Within 48 hours of outcome capture |
| Lesson candidate | One lesson per trade minimum |
| CandidateRule | Only advisory, not Policy |
| Policy activation | ❌ NO-GO (Phase 5 closure) |
| Auto-promotion | ❌ NO-GO |
| Evidence for CR | Must reference specific trade and outcome |

## 10. Stop Conditions

The dogfood must stop if any of these occur:

| Condition | Action |
|-----------|--------|
| Total loss ≥ $50.00 | **HARD STOP** — dogfood ends, Phase 7B review required |
| Daily loss ≥ $15.00 | Stop for the day |
| Weekly loss ≥ $25.00 | Stop for the week |
| 3 consecutive losing trades | Stop for 24 hours |
| Stale market data (> 15 min) | Do not trade |
| Missing outcome capture | Do not open new trade |
| Missed review (> 48 hours) | Suspend until reviews are current |
| Emotional / impulsive trading | Stop for 24 hours, document |
| Constitution rule violation | Stop, document, review |
| Broker account uncertainty | Stop until account state is verified |

## 11. Evidence Requirements

| Evidence Type | Freshness | Source |
|---------------|-----------|--------|
| Market data | ≤ 1 min for CURRENT | Alpaca Paper or live broker |
| Account state | ≤ 5 min | Broker portal or API |
| Intake | Timestamped before trade | Manual entry |
| Plan receipt | Timestamped before trade | Generated |
| Outcome capture | ≤ 24 hours after exit | Manual entry |
| Review | ≤ 48 hours after outcome | Manual |
| CandidateRule | Generated from review | Advisory only |

## 12. AI / Agent Boundaries

| Action | Allowed? |
|--------|----------|
| Assist pre-trade analysis | ✅ |
| Check risk budget | ✅ |
| Generate plan receipt | ✅ |
| Display market data freshness | ✅ |
| Suggest lessons / CandidateRules | ✅ (advisory only) |
| Review outcome data | ✅ |
| Authorize a live trade | ❌ |
| Place an order | ❌ |
| Cancel / modify an order | ❌ |
| Bypass intake | ❌ |
| Convert CandidateRule to Policy | ❌ |
| Increase risk limits | ❌ |

## 13. Phase 7B Readiness Criteria

Phase 7B may begin when:

- [ ] This constitution has been reviewed by a human
- [ ] A live brokerage account exists (Futu or IB)
- [ ] The account is funded with $100 (or equivalent)
- [ ] The operator has placed at least one manual trade before (any venue)
- [ ] Alpaca Paper observation is confirmed working
- [ ] Intake / receipt / outcome / review templates are ready
- [ ] No outstanding Phase 6 issues

Phase 7B is **not** automatic. It requires explicit human declaration.
