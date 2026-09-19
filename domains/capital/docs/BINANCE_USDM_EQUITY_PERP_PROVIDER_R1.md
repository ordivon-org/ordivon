# Binance USDⓈ-M Equity Perp Provider R1

Date: 2026-09-19
Status: PUBLIC_AND_CLIENT_SURFACES_QUALIFIED_PRIVATE_USER_DATA_PENDING

## Purpose

Treat Binance USDⓈ-M TradFi Equity Perpetuals as an independent authoritative provider rather than translating OKX semantics into Binance-shaped local objects.

The provider stack is:

Binance documented product/API semantics
-> Binance Official USDⓈ-M Futures Python SDK
-> Network v2 exact scoped transport
-> thin Market Capital normalization
-> OPA execution policy
-> no external write authority

## Mature owner boundaries

### Binance owns

- contract status and dynamic symbol filters;
- mark price and price-index methodology;
- funding rate, funding interval and funding history;
- TradFi trading-session schedule;
- leverage/notional brackets and maintenance margin;
- position amount, mark, PnL, liquidation price, initial/maintenance margin and ADL rank;
- account mode, position mode and Multi-Assets mode;
- order lifecycle, user data streams, ADL and insurance-fund reality;
- TradFi agreement and product eligibility.

### Official SDK owns

The isolated provider is binance-sdk-derivatives-trading-usds-futures 17.4.0.

It exposes official /fapi REST, WebSocket API and WebSocket Streams. Market Capital must not implement its own signing, retrying or endpoint client while this mature provider is available.

### Network v2 owns

- fapi.binance.com REST egress through localhost:19287;
- fstream.binance.com stream egress through localhost:19289;
- provider selection/failover;
- fail-closed no-direct-fallback routing.

### Market Capital owns only

- normalization into cross-venue observation/account structures;
- explicit data-quality/provenance checks;
- policy input construction and fail-closed OPA enforcement;
- reconciliation mapping after authoritative provider truth is observed.

## SNDKUSDT launch contract

The Binance notice for SNDKUSDT specifies:

- underlying: Sandisk Corporation Common Stock, Nasdaq SNDK;
- settlement: USDT;
- tick size: 0.01;
- minimum trade amount: 0.01 SNDK;
- minimum notional: 5 USDT;
- funding settlement: every eight hours;
- funding cap: plus/minus 2 percent per interval;
- funding interest component: 0 percent;
- maximum leverage at launch: 10x;
- trading hours: 24/7;
- Multi-Assets Mode: supported.

These are launch specifications, not immutable runtime truth. Current exchangeInfo, fundingInfo and USER_DATA leverageBracket win when parameters change.

This distinction is already material: Binance announced revised SNDKUSDT leverage/margin tiers effective 2026-08-11, including a 51-75x smallest-notional tier. That does not mean a particular account currently has 75x available. User-specific leverage/notional brackets remain USER_DATA provider truth.

## Exchange-info rules

Binance explicitly says pricePrecision must not be used as tickSize and quantityPrecision must not be used as stepSize.

Therefore:

- PRICE_FILTER.tickSize owns price increments;
- LOT_SIZE / MARKET_LOT_SIZE own quantity increments;
- MIN_NOTIONAL owns minimum notional;
- symbol status/order types/TIF are provider truth.

The local normalizer fails closed if required filters are absent.

## TradFi pricing is not crypto-perp pricing

During normal underlying sessions Binance aggregates vendor/reference data.

For equity TradFi perps, Orderbook EWMA index mode is active during daily maintenance, weekends and holidays. Binance changed TradFi Mark Price Price-2 basis from a 30-second basis to a one-minute basis effective 2026-08-31 08:15 UTC.

Therefore a weekend SNDKUSDT price is not treated as a direct live Nasdaq cash quote.

The tradingSchedule endpoint is authoritative for PRE_MARKET, REGULAR, AFTER_MARKET, OVERNIGHT and NO_TRADING boundaries.

## Dividend/corporate-action semantics

Equity perps have a provider-native dividend adjustment workflow.

For U.S. equity perps, Binance can temporarily:

- shorten funding to one hour;
- put the contract into reduce-only mode;
- tighten mark/index deviation limits;
- execute a special dividend funding payment from shorts to longs;
- restore ordinary mode after the event.

Market Capital must consume provider state/announcements. It must not reimplement dividend adjustment arithmetic as execution truth.

## Margin hierarchy

Binance exposes several distinct layers which must not be conflated:

1. One-Way vs Hedge position mode.
2. Cross vs Isolated margin mode.
3. Single-Asset vs Multi-Assets mode.
4. Portfolio Margin / Portfolio Margin Pro.

Multi-Assets Mode uses Cross Margin. Portfolio Margin is a different account-level risk system and must be qualified separately.

A user choosing 10x leverage does not create a Market Capital risk budget. Current risk limits remain explicit policy inputs.

## Liquidation and ADL

Position Information V3 exposes authoritative current fields including position amount, entry/break-even/mark price, PnL, liquidation price, initial margin, maintenance margin and ADL rank.

Current user-specific leverage/notional brackets come from USER_DATA leverageBracket.

Public symbol ADL risk and insurance-fund endpoints are additional provider observations.

Market Capital does not own a competing liquidation formula.

## Private USER_DATA

The required read-only surface is:

- Account Information V3
- Futures Account Balance V3
- Futures Account Configuration
- current Multi-Assets mode
- current Position mode
- user leverage/notional brackets
- Position ADL quantile
- Position Information V3
- current open orders
- account trades

For timeliness Binance recommends Position Information V3 together with USER_DATA ACCOUNT_UPDATE.

Current standing remains PENDING_CREDENTIAL_CLIENT_BINDING because the existing observer credential has not yet been freshly verified for USDⓈ-M USER_DATA through the official SDK boundary.

## TradFi agreement / eligibility

POST /fapi/v1/stock/contract signs the TradFi-Perps agreement.

That endpoint is never an automated Market Capital action.

Product agreement and regional/account eligibility require explicit user/provider action and must be verified at Binance before any execution lane can graduate.

## Execution

The official SDK exposes new_order and related TRADE surfaces, but their existence does not imply admission.

Current state:

- public market reads: structurally qualified;
- SDK client surface: qualified;
- private USDⓈ-M USER_DATA: pending;
- account/product eligibility: pending provider verification;
- TradFi agreement automation: forbidden;
- live execution: not admitted;
- external financial writes: not admitted.

## Current public SNDK consequence

A fresh credential-free capture through the official SDK and exact Network v2 USD-M REST authority observed:

- contract type: TRADIFI_PERPETUAL;
- status: TRADING;
- tick size: 0.01;
- limit and market quantity step: 0.01;
- minimum notional: 5 USDT;
- trigger protection: 3%;
- liquidation fee field: 1.5%;
- market take bound: 3%;
- funding interval: eight hours;
- current ordinary funding rate: 0%;
- public symbol ADL risk: LOW;
- current underlying-equity schedule state at the capture: NO_TRADING;
- next schedule state: OVERNIGHT;
- all six reported index-constituent price fields were hidden as -1.

The same exchangeInfo payload reported pricePrecision=5 and quantityPrecision=2 while tick/step were 0.01. This is direct runtime evidence that precision fields are metadata, not trading-rule authority.

Canonical public evidence: evidence/acceptance/binance-sndk-usdm-public-canary-r1.json.

## Failure and reconciliation semantics

Binance USD-M documentation distinguishes several server-error cases. In particular, an HTTP 503 response whose message says execution status is unknown must not be treated as an immediate failed order. Binance directs clients to verify through WebSocket updates or order-id queries before retrying to avoid duplicate execution.

Market Capital therefore does not own a generic retry-on-5xx policy. Any future execution lane must preserve provider-specific unknown-execution reconciliation and remain idempotency-aware.
