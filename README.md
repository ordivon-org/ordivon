# Ordivon Capital — Composition First

Ordivon Capital is the capital composition and control plane of Ordivon. It does not define a new accounting, risk, trading, settlement, identity, observability, lineage, or cloud-cost framework. It composes authoritative standards, mature implementations, provider reality, and the minimum Ordivon glue required to bind evidence, authority, execution, and reconciliation.

**Market Capital is one implemented domain inside Ordivon Capital, not the parent system.** The current repository contains the Market domain plus a cross-domain TigerBeetle accounting integration. Treasury, Compute, Enterprise, Human, Distribution, and other capital domains are not instantiated until a real use case requires them and an external-owner census has been completed.

Current Market-domain business backbone: CFA investment-management process.
Trading semantics: FIX.
Trading runtime: pinned QuantConnect LEAN (installed and admitted for bounded non-live Wave B execution).
Post-trade reference semantics: PFMI + ISO 20022; broker/custodian infrastructure remains authoritative.
Issuer reporting: XBRL/iXBRL + Arelle.
Research: existing Ordivon Research E2E / MLflow.
Capital accounting mechanics: TigerBeetle `0.17.9`; venue/custody/settlement systems remain authoritative for their own external state.

## Current standing

Wave A is closed on the investment side:

`Mandate / IPS -> authoritative data -> research artifact -> portfolio construction -> target portfolio`

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. M2 adds LEAN-native pre-trade feasibility. M3 uses provenance-recorded Nasdaq historical OHLCV only for execution-mechanics/data-plumbing validation. M4 projects order intent through a legacy FIX 4.4 wire profile under the FIX Latest semantic reference. M5 is prospective validation: a frozen decision may be evaluated only against strictly post-decision aligned holdout sessions; this is not causal evidence. M6 freezes a pre-market shadow plan. Every current execution runner crosses the OPA-governed execution-policy enforcement point before LEAN starts. No live financial-write path is implemented. NautilusTrader `2.0.0rc4` remains qualification-only.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.

The active public-data venue qualification path is **OKX + Binance Spot** through exact Network v2 authorities. Network v2/sing-box owns provider A/B transport and failover; Market Capital consumes only destination-fenced loopback authorities. The lane remains public-data-only and credential-free, separate from the historical equity M6/M7 experiment.

Crypto Public Shadow R1 now binds concurrent OKX/Binance public REST capture to exact Network v2 authorities. The latest migration rerun completed one coherent capture round, but the scientific standing remained `PARTIAL_PUBLIC_CAPTURE_NO_CROSS_VENUE_CLAIM` because venue-clock agreement was ~294.6 ms against the frozen 250 ms gate; the gate was not relaxed. Private/demo/live writes remain independently blocked by NON_LIVE execution authority.

Crypto Shadow Mechanics R1 also passes local multi-currency Spot OMS mechanics for OKX/Binance using venue-owned tick/step precision; it remains explicitly non-economic and non-live.

Crypto data transport is now venue-specific: OKX uses the qualified Nautilus native public client, while Binance uses its official credential-free REST/WebSocket boundary because Nautilus 2.0.0rc4 still times out during native data-client startup.

Crypto Public Shadow R2 now passes repeated persistent public streaming through exact Network v2 WS authorities using the mature `websockets` client proxy support. OKX `bbo-tbt` plus Binance market-data-only `@ticker` produced one warm-up and three measured coherent snapshots; all measured source/receive spans remained below the frozen 1200 ms limits. Provider selection is owned by Network v2 `provider-auto`, not by an application-level node/protocol matrix.

Crypto Stream Resilience R3 keeps fail-closed missing/stale/time-divergence semantics and the dual-venue reconnect harness on exact Network v2 WS authorities. Current injected-disconnect qualification passes for both OKX and Binance; observed reconnect latencies were ~16.0 s and ~26.3 s respectively and remain evidence rather than a hidden transport claim. The state is exported through the existing Prometheus/Grafana stack without enabling private/demo/live execution.
Clock timing qualification now passes: Windows w32time is synchronized to qualified public NTP peers and WSL CLOCK_REALTIME follows the Windows host through `/dev/ptp_hyperv` using `phc2sys`; fresh external validation observed <=47.1 ms absolute error versus the frozen 1000 ms gate. Overall private/demo/live execution remains blocked by the separate NON_LIVE execution authority.

Composition policy: prefer authoritative standards, mature implementations, and provider-native truth over local mechanisms. ISO/FIX/ISO 20022/GLEIF define external semantics where applicable; LEAN/Nautilus/venue APIs/TigerBeetle/OPA/MLflow/Pandera/OpenLineage/OTel/Prometheus own their respective mechanics. Ordivon Capital retains only narrow composition, policy-input/enforcement, evidence, data-quality, and reconciliation seams that no natural owner can establish alone. Custom mechanisms require a demonstrated substitution failure. Machine-readable ownership is tracked in `config/external_owner_census.json`; see `docs/COMPOSITION_FIRST_2026-09-14.md`.

TigerBeetle Capital Substrate R1 passes the base mechanical integration and R3.1 composes Reservation -> PENDING, RETAIN -> no mutation, RELEASE -> VOID_PENDING_TRANSFER, and CONSUME -> POST_PENDING_TRANSFER. R3.2 now passes durable restart/reconciliation on one intact data file: a pending reservation survived the first process restart, a consumed reservation survived the second, exact replay returned `EXISTS` without reopening pending state, and exact terminal semantic history reconciled `MATCH`. If provider terminal history is missing or stale, the result is retain/recovery (`PROVIDER_INCOMPLETE_RETAIN` / `CONTRADICTION_RETAIN`) with provider repair forbidden; terminal Market Capital history is never resurrected from provider state. The bounded harness deletes its data file afterward, so no long-running canonical ledger or external financial write is admitted.

Crypto FIX Projection R4 now passes: the four already-qualified Nautilus mechanics-only Spot orders project through sessionless QuickFIX/n FIX 4.4 `NewOrderSingle` semantics with ClientOrderId→ClOrdID identity continuity, venue `ExDestination`, Market order type and IOC TIF. No credential, FIX session, private account read or external financial write is admitted.

Private Reality read-only preflight now passes without credentials: OKX will use the installed NautilusTrader `OKXHttpClient`; Binance will use the first-party `binance-sdk-spot 11.3.0`. Required account/order/trade query surfaces are present, but credential use remains `NOT_ADMITTED`, secret discovery is forbidden, and TRADE/Withdraw remain blocked.

Private Reality R5 offline normalization now passes: authoritative OKX/Binance observer envelopes map through a pure no-network/no-credential normalizer into a minimal balances/positions/orders/fills read model. Existing observer credential locations are bound externally, Binance executor credentials are explicitly excluded, and private account data remains blocked pending fresh permission verification.

Execution Reconciliation R6 now passes offline: authoritative normalized venue reality is mapped into FIX 4.4 execution lifecycle vocabulary, and reconciled directly to TigerBeetle accounting-resolution instructions. Broad snapshot absence is never treated as no-effect; voiding a pending transfer requires terminal zero-fill with complete fill coverage or an exact authoritative negative lookup.

Demo/Testnet Execution R7 preflight is prepared but not admitted: the installed NautilusTrader execution configs construct successfully for OKX DEMO and Binance Spot TESTNET without credentials or network access. Demo/live write authority remains false.

Live endpoint test-account policy is now explicit: the user authorizes the existing OKX/Binance LIVE endpoints for non-production qualification, but they remain semantically LIVE. Fresh authoritative account reality must prove an effectively empty account (no positions/open orders/nonquote balances and <=1 quote unit), trade-only authority, clock health and reconciliation health before order submission can be enabled.
