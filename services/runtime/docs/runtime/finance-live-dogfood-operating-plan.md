# Finance Live Dogfood Operating Plan

Status: **DRAFT — DEFERRED TO PHASE 8** (Phase 7A, reclassified 7A-R)
Date: 2026-04-29
Phase: 7A-R
Tags: `finance`, `dogfood`, `operating-plan`, `manual`, `deferred`

> **⚠ DEFERRED LIVE DRAFT**: See constitution header. This operating plan
> is a future live-stage draft. The next stage is Alpaca Paper Trading (Phase 7P).

## 1. Purpose

This document defines the day-to-day operating procedures for the $100 manual
live micro-capital dogfood. It complements the constitution by specifying
**how** to execute each step, not just what is required.

## 2. Daily Workflow

### 2.1 Pre-Market (Before Trading)

```
1. Open /finance-prep in browser
2. Verify observation health status:
   - Provider status: CONNECTED or CONFIGURED
   - Freshness: CURRENT for market data
   - No STALE DATA warning
3. Review account state:
   - Current equity
   - Available cash
   - Any open positions?
4. Review market conditions:
   - Check Alpaca Paper quote for symbols of interest
   - Note any significant news or events
5. Review open reviews:
   - Any pending post-trade reviews?
   - Any missing outcome captures?
6. Set daily intentions:
   - Max trades today
   - Risk budget remaining
   - Symbols to watch
```

### 2.2 Pre-Trade (For Each Trade)

```
1. Complete pre-trade intake form:
   - Fill ALL required fields (Section 6 of constitution)
   - Must include at least one reason NOT to trade
   - Record market data freshness timestamp
2. Risk check:
   - Is per-trade risk ≤ $5.00 (5%)?
   - Is daily loss ≤ $15.00?
   - Is weekly loss ≤ $25.00?
   - Any stop conditions active?
3. Generate plan receipt:
   - Intake accepted? → continue
   - Intake rejected? → stop, document reason
4. Record plan receipt timestamp
```

### 2.3 Trade Execution (MANUAL ONLY)

```
1. Open brokerage app/portal (NOT Ordivon)
2. Place manual order based on plan receipt
3. Record actual fill price immediately
4. Do NOT modify the order based on real-time price movement
5. If fill is significantly different from plan (> 1% slippage):
   - Record the deviation
   - Decide: accept or cancel remaining?
```

### 2.4 Post-Trade (After Exit)

```
1. Fill outcome capture form:
   - Entry, exit, quantity, fees, slippage, PnL
   - Plan followed? Rule violated?
   - Emotional state note (optional)
2. Submit outcome capture
3. Trigger post-trade review
4. If loss:
   - Observe cooldown period (1 hour minimum)
   - Review what went wrong BEFORE next trade
5. If win:
   - Review what went right
   - Do not increase position size
```

### 2.5 End-of-Day

```
1. Verify all trades have outcome captures
2. Verify all outcomes have reviews
3. Close /finance-prep
4. Note: daily PnL, trades taken, rules followed, lessons
5. Check for generated CandidateRules
```

## 3. Weekly Review

| Day | Activity |
|-----|----------|
| Monday | Set weekly intentions, review last week's lessons |
| Friday | Weekly PnL summary, check loss limits, review all CandidateRules |
| Saturday | Deep review: patterns, discipline, constitution adherence |

## 4. Roles and Responsibilities

| Role | Who | What |
|------|-----|------|
| Trader | Human operator | Manual execution, intake, outcome capture |
| Reviewer | Human operator (can be same) | Post-trade review, lesson extraction |
| Governance | Ordivon | Risk check, plan receipt, observation, freshness |
| Observer | Alpaca Paper (Phase 6) | Market data, account reference (paper only) |
| Auditor | Future human or Phase 7+ | Constitution compliance audit |

## 5. Tools and Surfaces

| Tool | Purpose | URL |
|------|---------|-----|
| `/finance-prep` | Observation health, constitution, intake preview | localhost:3000/finance-prep |
| `/reviews` | Post-trade review queue, CandidateRule review | localhost:3000/reviews |
| `/policy-shadow` | Shadow policy evaluation (advisory) | localhost:3000/policy-shadow |
| Alpaca Paper | Market data + paper account reference | paper-api.alpaca.markets |
| Live Broker (TBD) | Manual order execution | Broker app/portal |

## 6. Failure Modes and Responses

| Failure | Response |
|---------|----------|
| Observation health returns DEGRADED | Do not open new trades. Fix connectivity. |
| Observation health returns UNAVAILABLE | Stop all trading. Use last-known account state. |
| Market data is STALE (> 1 min) | Refresh. If persists, do not trade. |
| Pre-trade intake incomplete | REJECT — cannot trade |
| Plan receipt missing | Cannot trade — intake not processed |
| Outcome capture missing after 24 hours | Flagged. Cannot open new trades. |
| Review missing after 48 hours | Flagged. Suspend until current. |
| Loss streak (3 consecutive) | Automatic 24-hour cooldown |
| Daily loss limit hit | Stop for the day |
| Total loss limit hit ($50) | HARD STOP — dogfood ends |
| Broker app unavailable | Do not trade. Document. |
| Emotional / impulsive trade detected | Stop 24 hours. Document in review. |
| Constitution rule violated | Stop. Document. Review before resuming. |

## 7. Evidence Chain

Every trade must produce a complete evidence chain:

```
Pre-Trade Intake
  → Plan Receipt
    → Manual Order Execution (outside Ordivon)
      → Outcome Capture (entry, exit, fees, slippage, PnL)
        → Post-Trade Review
          → Lesson → CandidateRule (advisory only)
```

Missing any link in the chain blocks the next trade.

## 8. Phase 7B Trigger

Phase 7B may begin when ALL of these are true:

- [ ] Constitution reviewed and accepted by human operator
- [ ] Live brokerage account exists and is funded ($100)
- [ ] Operator has placed at least one manual trade before (any venue)
- [ ] Alpaca Paper observation confirmed working
- [ ] Intake template tested with at least one simulated trade
- [ ] Outcome capture template tested with at least one simulated trade
- [ ] Review template tested
- [ ] All Phase 6 verification gates pass (pr-fast baseline)
- [ ] Human operator explicitly declares "Phase 7B: GO"

Phase 7B is the first supervised manual trade protocol — still no API orders,
still no auto-trading, still constitution-bound.

## 9. Phase 7B Preview (Not Yet Started)

Phase 7B will define:
- First trade pre-authorization checklist
- Supervisor / reviewer assignment
- Live trade documentation template
- Real-time observation dashboard requirements
- Post-first-trade retrospective format

It will NOT enable:
- Broker API integration
- Automated order execution
- Algorithmic trading
- Policy activation
