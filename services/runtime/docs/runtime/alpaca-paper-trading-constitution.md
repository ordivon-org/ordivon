# Alpaca Paper Trading Constitution

Status: **DOCUMENTED** (Phase 7P-1)
Date: 2026-04-29
Phase: 7P-1
Tags: `alpaca`, `paper`, `trading`, `constitution`, `dogfood`, `paper-only`

## 1. Purpose

Alpaca Paper Trading is the **next dogfood stage** for Ordivon's finance governance loop.
It is a controlled, zero-risk environment for testing the full governance lifecycle:

```
Observe → Intake → Plan Receipt → Paper Order → Fill Capture → Outcome → Review → Lesson → CandidateRule
```

This constitution defines what is and is not allowed within Alpaca Paper dogfood.
Paper execution is NOT live trading. Paper PnL is NOT real profitability.

## 2. Paper vs Live Boundary

| Property | Alpaca Paper (Phase 7P) | Live Trading (Phase 8) |
|----------|------------------------|------------------------|
| Money | Simulated ($100,000 default) | Real ($100) |
| Risk | Zero financial risk | Real capital at risk |
| Broker endpoint | `paper-api.alpaca.markets` | TBD (Futu or IB) |
| Order execution | Paper API (simulated fills) | Real broker |
| PnL | Simulated — not real | Real — actual gain/loss |
| Evidence value | Governance process validation | Real financial evidence |
| Current status | Constitution defined (7P-1) | **DEFERRED** |

**Critical**: Paper execution adapter (Phase 7P-2) must be **separate** from
`ReadOnlyAdapterCapability`. The read-only adapter must remain read-only.
A paper execution adapter may have `can_place_paper_order = True` but
`can_place_live_order` must remain `False`.

## 3. Allowed Actions (Phase 7P)

| Action | Allowed? | Phase |
|--------|----------|-------|
| Read-only Alpaca Paper observation | ✅ | 6G–6L (complete) |
| Health endpoint queries | ✅ | 6K (complete) |
| Paper trade intake | ✅ | 7P-1 (defined here) |
| Paper governance check | ✅ | 7P-1 |
| Paper plan receipt | ✅ | 7P-1 |
| **Paper order placement (via API)** | ⏭ | 7P-2 (after adapter implemented + reviewed) |
| Paper fill capture | ⏭ | 7P-3 |
| Paper outcome capture | ⏭ | 7P-3 |
| Paper post-trade review | ⏭ | 7P-3 |
| Paper lesson → CandidateRule | ⏭ | 7P-Z |
| Real-money trading | ❌ | Phase 8 (DEFERRED) |

## 4. Forbidden Actions

| Action | Status |
|--------|--------|
| Live broker order placement | ❌ NO-GO |
| Live broker write keys | ❌ NO-GO |
| Live account API access | ❌ NO-GO |
| Withdraw / transfer | ❌ NO-GO |
| Margin / leverage / derivatives | ❌ NO-GO |
| Auto trading / algorithmic execution | ❌ NO-GO |
| Repeated autonomous AI paper trading | ❌ NO-GO |
| AI placing paper orders without human review | ❌ NO-GO |
| Treating paper PnL as real profitability | ❌ NO-GO |
| Promoting paper-only lesson directly to Policy | ❌ NO-GO |
| Pointing paper adapter to live Alpaca URL | ❌ NO-GO |
| Mixing read-only adapter with paper execution | ❌ NO-GO (must be separate) |

## 5. Paper Execution Lifecycle

```
1. OBSERVE
   - Health endpoint shows provider status
   - Market data freshness verified
   - Paper account state checked

2. INTAKE (pre-trade)
   - All required fields completed
   - Must include "reason NOT to trade"

3. GOVERNANCE CHECK
   - Risk budget check
   - Stop conditions check
   - Paper account state confirmed

4. PLAN RECEIPT
   - Decision: PAPER_INTAKE_ACCEPTED / HOLD / REJECTED
   - Allowed: Alpaca Paper order only
   - Forbidden: live order

5. PAPER ORDER (Phase 7P-2+)
   - Via PaperExecutionAdapter (separate from ReadOnlyAdapterCapability)
   - Paper endpoint only
   - Human authorization required

6. FILL CAPTURE
   - Order ID, fill price, quantity, timestamp
   - Simulated fees if available

7. OUTCOME CAPTURE
   - Entry, exit, quantity, fees, slippage
   - Paper PnL (explicitly labeled as simulated)
   - Plan followed? Deviation?

8. REVIEW
   - Mandatory post-trade review
   - Lesson extraction (advisory only)

9. LESSON → CandidateRule
   - CandidateRule only, not Policy
   - No automatic activation
```

## 6. Required Pre-Paper-Trade Intake

| Field | Required | Notes |
|-------|----------|-------|
| symbol | Yes | Ticker |
| asset class | Yes | US equity only for paper |
| paper account state | Yes | Equity, cash from /health/finance-observation |
| market snapshot freshness | Yes | CURRENT/STALE/DEGRADED/MISSING |
| thesis | Yes | Why this trade? |
| setup | Yes | Technical/fundamental description |
| entry plan | Yes | Price, order type, timing |
| invalidation | Yes | What proves thesis wrong? |
| stop condition | Yes | Exit trigger |
| max paper risk | Yes | In simulated dollars |
| reason NOT to trade | Yes | At least one |
| expected fee/slippage | Yes | Alpaca is commission-free but slippage exists |
| evidence refs | Yes | Charts, data, observation snapshots |

## 7. Paper Plan Receipt

Generated after intake governance check:

| Field | Description |
|-------|-------------|
| decision | PAPER_INTAKE_ACCEPTED / HOLD / REJECTED |
| allowed action | Alpaca Paper order only |
| forbidden action | Live order — NO-GO |
| max paper quantity | Shares |
| max paper risk | Simulated $ |
| order type | Market / limit |
| stop / exit plan | Exit conditions |
| evidence refs | Link to intake |
| **⚠ PAPER ONLY — NOT LIVE TRADING** | Mandatory disclaimer |
| **⚠ Paper PnL is simulated, not real** | Mandatory disclaimer |

## 8. Paper Outcome Capture

| Field | Required | Notes |
|-------|----------|-------|
| paper order ID | Yes | From Alpaca Paper API |
| fill ID / fill time | Yes | Timestamp |
| fill price | Yes | Actual fill |
| quantity | Yes | Shares |
| simulated fees | If available | Alpaca is commission-free |
| slippage estimate | Yes | Expected vs actual |
| paper PnL | Yes | **Labeled as simulated** |
| plan followed? | Yes | Y/N |
| deviation? | Yes | Describe if any |
| review required? | Yes | Mandatory |

## 9. Review Rules

| Rule | Value |
|------|-------|
| Review required | Every paper trade |
| Review window | ≤ 48 hours after outcome |
| Lesson extraction | One per trade minimum |
| Lesson status | Advisory only |
| CandidateRule | Not Policy |
| Policy activation | ❌ |
| Auto-promotion | ❌ |
| Evidence for CR | Must reference specific paper trade |

## 10. Risk Red-Team

| # | Vector | Mitigation | Status |
|---|--------|-----------|--------|
| R1 | Paper trading creates false confidence for live | Constitution §2: explicit paper vs live boundary table | ✅ |
| R2 | Paper liquidity/slippage differs from live | Documented as known limitation in outcome capture | ✅ |
| R3 | Paper PnL mistaken as real | "⚠ Paper PnL is simulated" on every receipt + outcome | ✅ |
| R4 | Paper adapter accidentally points to live URL | Phase 7P-2 must enforce paper-api only; check at init | 📋 7P-2 |
| R5 | Read-only adapter polluted with write methods | Constitution §2: adapters must be SEPARATE | ✅ |
| R6 | AI loops paper trades repeatedly | Forbidden §4: "Repeated autonomous AI paper trading — NO-GO" | ✅ |
| R7 | Paper success used to justify early live trading | Phase 8 requires separate authorization; paper≠live | ✅ |
| R8 | Future AI misunderstands 7P as live trading | AGENTS.md updated; constitution header states PAPER ONLY | ✅ |

## 11. Phase 7P-2 Readiness Criteria

Phase 7P-2 (PaperExecutionAdapter implementation) may begin when:

- [ ] This constitution is reviewed and accepted by human operator
- [ ] Paper vs Live boundary is documented and understood
- [ ] PaperExecutionAdapter design is separated from ReadOnlyAdapterCapability
- [ ] Paper endpoint (`paper-api.alpaca.markets`) is the only allowed URL
- [ ] No live Alpaca endpoint in any code path
- [ ] Order methods explicitly labeled as paper-only
- [ ] write_capabilities for paper adapter: `can_place_paper_order = True`, all live writes = False
- [ ] ReadOnlyAdapterCapability remains unchanged (write=False)
- [ ] Tests required before any paper order execution
- [ ] No live API keys used
- [ ] No secrets exposed
- [ ] AI context (AGENTS.md) updated to reflect 7P-2 as active

## 12. Phase 7P-2 Preview (Not Yet Started)

Phase 7P-2 will implement:
- `adapters/finance/paper_execution.py` — PaperExecutionAdapter (separate class)
- Paper-only capability: `can_place_paper_order = True`, all live = False
- Paper endpoint enforcement at init
- Tests: paper order lifecycle, no live URL, no live keys
- Updated `/finance-prep` with paper execution status

It will NOT:
- Point to live Alpaca
- Reuse ReadOnlyAdapterCapability
- Enable live trading
- Place orders without tests
