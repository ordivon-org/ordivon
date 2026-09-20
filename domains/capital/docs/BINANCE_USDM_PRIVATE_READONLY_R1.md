# Binance USDⓈ-M Private Read-Only Qualification R1

Date: 2026-09-19
Status: INPUT_AUTHORITY_ACTIVE_EXPECTED_DIGEST_COMMITMENT_MISSING

## Objective

Qualify one Binance observer credential for USDⓈ-M Futures private reality without admitting any trade, account-mode mutation, leverage mutation, transfer, withdrawal, or TradFi agreement effect.

The process is permission-first. Merely proving that a credential can read a Futures endpoint is insufficient because it may also be order-capable.

## Mature owner composition

The credential path uses:

1. Runtime digest-bound InputAuthority for immutable credential presentation.
2. Binance Official Wallet Python SDK 13.4.0 for GET /sapi/v1/account/apiRestrictions.
3. Binance Official USDⓈ-M Futures Python SDK 17.4.0 for FAPI USER_DATA GET surfaces.
4. Network v2 exact egress authorities:
   - api.binance.com through localhost:19290;
   - fapi.binance.com through localhost:19287.
5. Market Capital pure normalization only after provider truth is captured.

No local signer, request authenticator, retry engine, margin calculator or permission classifier substitutes for the official provider mechanisms.

## Permission gate

Before any USDⓈ-M private account read, API-key permission truth must show:

- enableReading = true;
- enableWithdrawals = false;
- enableInternalTransfer = false;
- enableMargin = false;
- enableFutures = false;
- permitsUniversalTransfer = false;
- enableVanillaOptions = false;
- enableFixApiTrade = false;
- enableSpotAndMarginTrading = false;
- enablePortfolioMarginTrading = false.

This gate is deliberately strict. If Binance requires enableFutures=true even for a Futures read-only credential, the current observer cannot be admitted under this policy merely because the intended request is GET. A separate provider-supported read-only credential design would be required.

## Private GET surface after permission admission

Only after the permission gate passes may the observer call:

- Account Information V3
- Futures Account Balance V3
- Futures Account Configuration
- Current Multi-Assets Mode
- Current Position Mode
- Notional and Leverage Brackets
- Position ADL Quantile
- Position Information V3
- Current All Open Orders
- Account Trade List

The capture code contains no new-order, cancel, modify, leverage-change, margin-mode-change, position-mode-change, Multi-Assets-mode-change or TradFi-contract-signing call.

## Output minimization

The live qualification command uses summary-only output. It reports only:

- permission standing;
- per-call success/failure;
- account configuration mode booleans;
- whether leverage bracket and ADL surfaces were observed;
- counts / presence booleans for SNDK private state;
- explicit no-write guards.

It does not emit balances, position prices, liquidation price, order IDs or trade prices into acceptance evidence.

## TradFi agreement

The official USDⓈ-M interface exposes POST /fapi/v1/stock/contract to sign the TradFi-Perps agreement. No authoritative read-only status endpoint is currently bound in this implementation.

Therefore:

tradFiAgreementStanding = UNKNOWN_NO_READ_ONLY_STATUS_API

Private-read success must never be upgraded into a claim that the account is eligible to open SNDKUSDT or that the agreement has been signed.

## Runtime authority state

The operator Runtime has a separate active named authority:

finance-binance-observer-materials

rooted at the explicitly authorized Binance observer credential directory.

The authority was activated only after Runtime reported zero active Jobs. A delayed service restart loaded the authority without interrupting unrelated work, and runtime_describe now reports the authority.

The remaining input-bound admission requirement is the caller-held expected SHA-256 commitment for each object. No prior canonical commitment exists, and platform execution policy prevents the current agent from deriving hashes directly from the secret host paths.

This is treated as a Runtime operator-interface gap. Market Capital does not recover the digest by deliberately causing a mismatch, does not use ambient secret discovery, and does not fall back to executor credentials.

## Network state

Network v2 has an exact Binance Wallet/SAPI authority:

- profile: finance-binance-wallet
- host: api.binance.com
- proxy: localhost:19290
- direct fallback: false

A public Binance server-time request through this path succeeded.

## Graduation rule

The private provider may advance from PENDING_CREDENTIAL_CLIENT_BINDING only when all of the following are true:

1. Runtime reports finance-binance-observer-materials as an active input authority. PASS.
2. Exact caller-held SHA-256 commitments exist for api_key and private.pem.
3. Credential bytes are presented through the authority rather than ambient discovery.
4. Wallet API permission query passes the strict read-only gate.
5. Required USDⓈ-M USER_DATA GET calls succeed.
6. No external financial write is attempted.
7. TradFi agreement and trade eligibility remain separately unknown unless independently proven.

Until then live execution remains non-admitted and the existing OKX SNDK position is not migrated.
