# Finance Observation Provider Plan

Status: **DOCUMENTED** (Phase 6H)
Date: 2026-04-29
Phase: 6H
Tags: `finance`, `observation`, `provider`, `read-only`, `adapter`, `plan`, `alpaca`, `china`, `futu`, `polygon`

## 1. Purpose

This document evaluates real market data and read-only account providers for the
Ordivon Finance Observation Layer. The selected provider will be the first real
external data source connected to the `ObservationProvider` Protocol defined in
Phase 6G. This phase does NOT enable order placement, broker write, or live trading.

**Important**: The operator is based in Mainland China. This significantly constrains
brokerage selection for Phase 7 live trading. Phase 6I-6J (paper observation) is
unaffected — paper trading is available globally without KYC.

## 2. Strategy: Two-Phase Provider Selection

We separate the problem into two distinct phases with different constraints:

| Phase | Stage | Constraint | Provider |
|-------|-------|-----------|----------|
| Phase 6I-6J | Paper observation (read-only) | Global access, no KYC | Alpaca Paper Trading |
| Phase 7 | Live $100 micro-capital trading | China-accessible brokerage | TBD (Futu or IB) |

Phase 6I-6J uses Alpaca Paper Trading to validate the **entire observation +
governance pipeline** without needing a real brokerage account. The data model,
Protocol, adapter, freshness checks, and UI integration are identical for paper vs live.

Phase 7 selects a China-accessible brokerage for the actual $100 trading dogfood.

## 3. Provider Evaluation Matrix

### 3.1 Market Data + Observation Providers (Phase 6I-6J)

Each provider is scored against 14 criteria on a 1–5 scale (5 = best fit).
These providers only need read-only access.

| # | Criterion | Alpaca Paper | Polygon.io | yfinance | Finnhub |
|---|-----------|-------------|------------|----------|---------|
| 1 | Public market data | 5 | 5 | 3 | 4 |
| 2 | Read-only account | 5 | 0 | 0 | 0 |
| 3 | Read-only API key | 5 | 5 | N/A | 5 |
| 4 | Disable trading/withdraw/transfer | 5 | N/A | N/A | N/A |
| 5 | Account balance | 5 | 0 | 0 | 0 |
| 6 | Position visibility | 5 | 0 | 0 | 0 |
| 7 | Fill/order history | 5 | 0 | 0 | 0 |
| 8 | Fee visibility | 5 (via fills) | 0 | 0 | 0 |
| 9 | Rate limits | 4 (200/min free) | 4 (free tier) | 2 (unofficial) | 4 (60/min) |
| 10 | Region (China) | 5 (paper global) | 5 (global) | 5 (global) | 5 (global) |
| 11 | Sandbox / paper | 5 (full paper env) | N/A | N/A | N/A |
| 12 | API stability | 5 | 4 | 2 | 4 |
| 13 | Cost | 5 (free) | 4 (free tier) | 5 (free) | 4 (free tier) |
| 14 | $100 micro-capital fit | 5 | 3 | 4 | 3 |
| **TOTAL** | | **69** | **25** | **16** | **24** |

### 3.2 Live Brokerage Candidates (Phase 7, China Operator)

For Phase 7 live trading, the operator needs a brokerage that:
- Accepts Mainland China residents
- Supports US stock trading
- Has API access for data observation
- Has commission structure viable for $100 micro-capital

| # | Criterion | Futu/moomo (富途) | Interactive Brokers (盈透) | Tiger Brokers (老虎) |
|---|-----------|-------------------|---------------------------|---------------------|
| 1 | China resident OK | 5 (native) | 4 (available) | 5 (native) |
| 2 | US stocks | 5 | 5 | 5 |
| 3 | API access | 4 (FutuOpenD) | 5 (TWS API + REST) | 2 (limited) |
| 4 | Read-only API | 4 | 5 | 2 |
| 5 | Account/position data | 5 | 5 | 3 |
| 6 | Fill history | 5 | 5 | 3 |
| 7 | Fee visibility | 5 | 5 | 3 |
| 8 | Commission | 4 ($0.99/trade) | 3 ($1/trade min) | 4 ($0.99/trade) |
| 9 | $100 viability | 4 (1% per trade) | 3 (1% per trade) | 4 (1% per trade) |
| 10 | API docs quality | 3 (Chinese primarily) | 4 (English) | 2 (limited) |
| 11 | Python SDK | 3 (community) | 5 (official ib_insync) | 1 |
| 12 | Paper trading | 4 (HK paper) | 5 (full paper) | 2 (limited) |
| **TOTAL** | | **51** | **54** | **36** |

## 4. Provider Profiles

### 4.1 Alpaca Paper Trading (Phase 6I-6J Primary)

**What it is**: US commission-free stock brokerage with paper trading environment.

**China operator status**: ✅ Paper trading available globally without KYC or SSN.
Register at app.alpaca.markets with email only. Paper API keys work immediately.

**Why Alpaca for observation validation**:
- Paper trading has **full API parity** with live — same endpoints, same data model
- The `ObservationProvider` Protocol doesn't care if the data source is paper or live
- Validating the governance pipeline on paper before committing real capital is
  the correct approach regardless of operator location
- Read-only API key is enforced server-side

**Live trading limitation**: ❌ Alpaca Live requires US residency (SSN, FINRA).
Not available for China-based operators.

### 4.2 Polygon.io (Market Data Backup)

**What it is**: Market data provider only. No brokerage, no account.

Use case: Supplement Alpaca paper data with real market data if paper data quality
is insufficient. Does not replace account/position/fill observation.

### 4.3 Interactive Brokers / 盈透证券 (Phase 7 Candidate)

**What it is**: Full-featured international brokerage. Available to Mainland China
residents through 盈透证券 (Interactive Brokers Hong Kong or IB LLC).

**API**: 
- TWS API (mature, complex, requires running TWS/IB Gateway)
- IBKR Client Portal REST API (simpler, read-only capable)
- `ib_insync` Python library (well-maintained, async, simplifies TWS API)

**Commission**: $0.005/share, $1 minimum per trade.
For $100 capital buying 1 share of AAPL (~$195): $1 commission = ~0.5% of trade.
Acceptable for micro-capital governance dogfood.

**Paper trading**: IB has a full paper trading account with the same API.

**Python SDK**: `ib_insync` (community, well-maintained, type-hinted).

**Region**: Available to Mainland China residents. Account opening requires
identity verification but accepts Chinese citizens.

### 4.4 Futu / moomoo / 富途牛牛 (Phase 7 Candidate)

**What it is**: Hong Kong-listed brokerage, very popular in China.
FutuOpenD is the gateway API for programmatic access.

**API (FutuOpenD)**:
- Free download, connects to Futu trading account
- Market data: US, HK, China A-shares
- Account: balance, positions, orders
- Read-only operations available
- Can disable trading permissions

**Commission**: ~$0.99/trade for US stocks. 
For $100 capital buying AAPL: $0.99 = ~0.5% of trade.

**Paper trading**: Futu supports paper trading (HK market primarily, US paper limited).

**Python SDK**: `futu-api` (official pip package). Chinese-language docs primarily.

**Region**: Native support for Mainland China residents. Chinese ID accepted.

### 4.5 Tiger Brokers / 老虎证券 (Phase 7 Backup)

Similar to Futu with a smaller API surface and weaker developer ecosystem.
Not recommended as primary unless Futu and IB are both unavailable.

## 5. Recommendation

### 5.1 Phase 6I-6J: Alpaca Paper Trading

- **What**: Implement `AlpacaObservationProvider` against Alpaca Paper Trading API
- **Why**: Available globally (no KYC), full API parity with live, validates governance pipeline
- **Risk**: None — paper money, read-only key, zero financial exposure
- **Outcome**: Proven `ObservationProvider` implementation ready for any brokerage backend

### 5.2 Phase 7 Live: TBD (Futu or Interactive Brokers)

Decision deferred to Phase 7. Recommendation criteria:
- If the operator has an existing Futu account → use FutuOpenD (simpler onboarding)
- If the operator wants English docs + mature API → use IB + ib_insync
- If neither works → defer live trading, continue with paper observation only

**Both providers are viable**. The key insight is that **Phase 6I-6J does not depend
on this decision** — the `ObservationProvider` Protocol abstracts the data source.
Switching from Alpaca Paper to Futu/IB Live requires only a new adapter class
implementing the same Protocol, with zero changes to the domain models, tests, or UI.

### 5.3 Market Data Backup

Polygon.io as fallback for pure market data. Useful if:
- Alpaca paper data has quality issues
- Need real-time data during paper trading
- Future need for data beyond US equities

## 6. First Data to Integrate (Phase 6I)

Priority order using Alpaca Paper Trading:

| Priority | Data | Endpoint | Maps to Model |
|----------|------|----------|---------------|
| P0 | Account balance + equity | GET /v2/account | `AccountSnapshot` |
| P0 | Market data (quote) | GET /v2/stocks/{symbol}/quotes/latest | `MarketDataSnapshot` |
| P1 | Positions | GET /v2/positions | `PositionSnapshot` |
| P1 | Order/fill history | GET /v2/orders | `FillRecord` |
| P2 | Portfolio history | GET /v2/account/portfolio/history | (new model if needed) |

## 7. What Remains Forbidden

All capabilities remain permanently blocked in all observation providers:

| Capability | Status | Enforcement |
|-----------|--------|-------------|
| Place order | BLOCKED | `ReadOnlyAdapterCapability.can_place_order = False` (frozen) |
| Cancel order | BLOCKED | `ReadOnlyAdapterCapability.can_cancel_order = False` |
| Withdraw | BLOCKED | `ReadOnlyAdapterCapability.can_withdraw = False` |
| Transfer | BLOCKED | `ReadOnlyAdapterCapability.can_transfer = False` |
| API key with write | BLOCKED | Read-only key enforced server-side |
| Auto trading | BLOCKED | No scheduling, no event-driven execution |
| Margin | BLOCKED | Cash account only |
| Leverage | BLOCKED | Cash account only |
| Derivatives | BLOCKED | Equities only |

## 8. Security Boundary

### 8.1 API Key Management

```
.env (never committed):
  ALPACA_API_KEY=PK...        # Read-only paper trading key
  ALPACA_SECRET_KEY=...       # Read-only paper trading secret
  ALPACA_PAPER=true           # Paper trading flag

Adapter (adapters/finance/alpaca_provider.py):
  - API keys loaded from env vars only
  - Keys never logged, never serialized, never exposed in UI
  - Read-only capability enforced at construction (frozen dataclass)
  - Adapter refuses to initialize if key has write permissions
```

### 8.2 Three-Layer Defense

| Layer | Mechanism | What It Blocks |
|-------|-----------|---------------|
| Code | `ReadOnlyAdapterCapability` frozen dataclass, write=False, post_init guard | Any code path trying to enable writes |
| Protocol | `ObservationProvider` Protocol — no write methods exist | Any caller trying to place orders |
| Server | Alpaca read-only API key — POST/DELETE rejected by Alpaca | Compromised key still can't trade |

### 8.3 Data Freshness

All data from Alpaca carries server-side timestamps. Freshness computed client-side:

| Timeliness | Status | Action |
|-----------|--------|--------|
| ≤ 60s | CURRENT | Trust |
| 1–15 min | STALE | Downgrade confidence |
| > 15 min | DEGRADED | Unreliable, warn |
| Missing | MISSING | No data available |

## 9. Phase 6I Implementation Plan

### 9.1 Scope

**Add**:
- `adapters/finance/__init__.py`
- `adapters/finance/alpaca_provider.py` — `AlpacaObservationProvider` implementing Protocol
- `tests/unit/finance/test_alpaca_provider.py` — unit tests with mocked Alpaca API
- `adapters/finance/README.md` — security notes

**New dependency**:
- `alpaca-py` (official Alpaca SDK) or raw REST with `httpx` if SDK is too heavy

**Modify**:
- `apps/web/src/app/finance-prep/page.tsx` — update observation panel source
- `domains/finance/read_only_adapter.py` — no changes needed (Protocol already defined)

**Do NOT modify**:
- RiskEngine, governance, state, ORM, DB schema
- CI workflows, Dependabot config
- Policy platform
- Any existing domain models outside `domains/finance/`

### 9.2 Implementation Order

| Step | Description | Risk |
|------|-------------|------|
| 1 | Add `alpaca-py` to dependencies | Low |
| 2 | Create `AlpacaObservationProvider` implementing Protocol | Low |
| 3 | Implement `get_account_snapshot()` | Low |
| 4 | Implement `get_market_snapshot(symbol)` | Low |
| 5 | Implement `get_positions()` | Low |
| 6 | Implement `get_fills()` | Low |
| 7 | Add error handling (timeout, rate limit, unavailable) | Medium |
| 8 | Add unit tests with mocked Alpaca responses | Low |
| 9 | Update `/finance-prep` to show Alpaca source | Low |
| 10 | Update `ObservationSource.PROVIDER` | Low |

### 9.3 Out of Scope (Phase 7 or Later)

- Alpaca real API key registration
- Live $100 capital deposit (requires Phase 7 brokerage selection)
- Order placement or broker write
- Futu/IB adapter implementation
- WebSocket streaming
- Historical data pipeline

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Alpaca paper API downtime | Low | Medium | Graceful degradation — show STALE, not crash |
| Rate limit exceeded | Low (200/min) | Low | Cache results, respect Retry-After |
| Read-only key misconfiguration | Low | High | Adapter validates key at init |
| SDK dependency breakage | Low | Medium | Pin exact version |
| **Phase 7: China operator cannot open US brokerage** | **Medium** | **High** | Two viable alternatives: Futu (native China support) and IB (盈透, accepts Chinese residents). Decision in Phase 7. |
| $100 capital too small for commissions | Medium | Low | Acceptable — governance validation is the goal, not profit |
| Live $100 deposit blocked (capital controls) | Low | Low | Paper-only is still valuable as governance validation |

## 11. Decision Record

| Decision | Rationale |
|----------|-----------|
| Alpaca Paper is Phase 6I-6J provider | Only provider with full observation API + paper trading + global access (no KYC). Score 69/70. Validates governance pipeline at zero risk. |
| Polygon.io is market data backup | Pure market data. Global access. Useful if Alpaca paper data is insufficient. |
| Phase 7 live provider deferred | Futu or IB, depending on operator preference. The `ObservationProvider` Protocol abstracts the backend — switching requires only a new adapter class. |
| Paper trading first, regardless of region | Validates the entire governance loop (observation → freshness → UI → decision intake → manual execution → outcome capture → review) before any real money is involved. This is correct architecture regardless of brokerage availability. |
| Read-only enforced at three layers | Code (frozen dataclass) + Protocol (no write methods) + Server (read-only key). Three independent guarantees. |
| No SDK trading modules imported | Adapter imports only market data and account-read endpoints. Never imports order placement APIs. |

## 12. China Operator Notes

### Phase 6I-6J (Paper, No Issue)
- Alpaca Paper Trading: register at app.alpaca.markets with email. No SSN, no KYC.
- Paper API key: generated immediately, works globally.
- Zero cost, zero risk, zero region constraint.

### Phase 7 (Live, Two Options)
1. **Futu/富途牛牛**: Native China support. Chinese ID accepted. FutuOpenD API.
   Commission ~$0.99/trade. Good fit for $100 micro-capital.
2. **Interactive Brokers/盈透证券**: International broker. Chinese residents accepted.
   TWS API + ib_insync. Commission $1/trade minimum. More mature API, English docs.

### Capital Controls Note
$100 is well within personal foreign exchange limits ($50,000/year).
Depositing $100 to a US stock brokerage from China is legally straightforward.
