# Ordivon Market Capital — Clean Room

Clean-room composition of mature external standards and implementations.

Business backbone: CFA investment-management process.
Trading semantics: FIX.
Trading runtime: pinned QuantConnect LEAN (installed and admitted for bounded non-live Wave B execution).
Post-trade reference semantics: PFMI + ISO 20022; broker/custodian infrastructure remains authoritative.
Issuer reporting: XBRL/iXBRL + Arelle.
Research: existing Ordivon Research E2E / MLflow.
Capital accounting mechanics: TigerBeetle `0.17.9` (mechanical-only provider; no capital truth or write authority).

## Current standing

Wave A is closed on the investment side:

`Mandate / IPS -> authoritative data -> research artifact -> portfolio construction -> target portfolio`

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. M2 adds LEAN-native pre-trade feasibility, M3 admits provenance-recorded Nasdaq historical OHLCV while remaining non-causal, M4 inserts QuickFIX/n FIX 4.4 `NewOrderSingle` semantics, M5 adds a fail-closed causal-shadow gate, M6 freezes a pre-market shadow order plan from the last pre-decision provider-origin close, and M6.1 migrates the proven semantic/authority core directly into this canonical repository so every current trading runner crosses the in-repository authority gate before LEAN starts. M5 is currently `WAITING_FOR_POST_DECISION_DATA`; M6 has emitted no LEAN orders or external effects. No FIX session, broker credential, venue write, or external financial write is admitted. External financial write admission remains `NOT_ADMITTED`; no provider/executor write capability is implemented and bound; there is no active runtime dependency on the retired `market-capital-v2` repository. NautilusTrader `2.0.0rc4` is installed only as a shadow qualification candidate: its OMS/Risk controls pass local controls, but its simulated venue rejects the frozen M6 `AT_THE_OPEN` orders, so it is not admitted as an M6/M7 replacement or live engine. See the Wave B documents under `docs/`.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.

The active public-data venue qualification path is **OKX + Binance Spot** through exact Network v2 authorities. Network v2/sing-box owns provider A/B transport and failover; Market Capital consumes only destination-fenced loopback authorities. The lane remains public-data-only and credential-free, separate from the historical equity M6/M7 experiment.

Crypto Public Shadow R1 now binds concurrent OKX/Binance public REST capture to exact Network v2 authorities. The latest migration rerun completed one coherent capture round, but the scientific standing remained `PARTIAL_PUBLIC_CAPTURE_NO_CROSS_VENUE_CLAIM` because venue-clock agreement was ~294.6 ms against the frozen 250 ms gate; the gate was not relaxed. Private/demo/live writes remain independently blocked by NON_LIVE execution authority.

Crypto Shadow Mechanics R1 also passes local multi-currency Spot OMS mechanics for OKX/Binance using venue-owned tick/step precision; it remains explicitly non-economic and non-live.

Crypto data transport is now venue-specific: OKX uses the qualified Nautilus native public client, while Binance uses its official credential-free REST/WebSocket boundary because Nautilus 2.0.0rc4 still times out during native data-client startup.

Crypto Public Shadow R2 now passes repeated persistent public streaming through exact Network v2 WS authorities using the mature `websockets` client proxy support. OKX `bbo-tbt` plus Binance market-data-only `@ticker` produced one warm-up and three measured coherent snapshots; all measured source/receive spans remained below the frozen 1200 ms limits. Provider selection is owned by Network v2 `provider-auto`, not by an application-level node/protocol matrix.

Crypto Stream Resilience R3 keeps fail-closed missing/stale/time-divergence semantics and the dual-venue reconnect harness on exact Network v2 WS authorities. Current injected-disconnect qualification passes for both OKX and Binance; observed reconnect latencies were ~16.0 s and ~26.3 s respectively and remain evidence rather than a hidden transport claim. The state is exported through the existing Prometheus/Grafana stack without enabling private/demo/live execution.
Clock timing qualification now passes: Windows w32time is synchronized to qualified public NTP peers and WSL CLOCK_REALTIME follows the Windows host through `/dev/ptp_hyperv` using `phc2sys`; fresh external validation observed <=47.1 ms absolute error versus the frozen 1000 ms gate. Overall private/demo/live execution remains blocked by the separate NON_LIVE execution authority.

Composition policy: prefer authoritative venue APIs and mature components over local mechanisms. LEAN/Nautilus/FIX/venue APIs/TigerBeetle/Prometheus own their respective mechanics; Market Capital retains only thin decision, proof, authority and reconciliation seams. Custom mechanisms require a demonstrated substitution failure. See `docs/COMPOSITION_FIRST_2026-09-14.md`.

TigerBeetle Capital Substrate R1 passes an ephemeral mechanical integration. R3.1 now additionally composes Market Capital reservation resolution onto provider pending-transfer mechanics: Reservation -> PENDING, RETAIN -> no provider mutation, RELEASE -> VOID_PENDING_TRANSFER, and CONSUME -> POST_PENDING_TRANSFER. A 700-unit pending reservation prevented a second 400-unit reservation against 1000 units of mechanical credit (`EXCEEDS_CREDITS`); RELEASE removed the encumbrance, a later 600-unit CONSUME posted exactly once, replay returned `EXISTS`, and a late RELEASE after consume failed with `PENDING_TRANSFER_ALREADY_POSTED`. These are mechanical conservation/monotonicity results only. Canonical false-green semantics still reject `TigerBeetle balance -> deployable capital`; no persistent ledger or external financial write is admitted.

Crypto FIX Projection R4 now passes: the four already-qualified Nautilus mechanics-only Spot orders project through sessionless QuickFIX/n FIX 4.4 `NewOrderSingle` semantics with ClientOrderId→ClOrdID identity continuity, venue `ExDestination`, Market order type and IOC TIF. No credential, FIX session, private account read or external financial write is admitted.

Private Reality read-only preflight now passes without credentials: OKX will use the installed NautilusTrader `OKXHttpClient`; Binance will use the first-party `binance-sdk-spot 11.3.0`. Required account/order/trade query surfaces are present, but credential use remains `NOT_ADMITTED`, secret discovery is forbidden, and TRADE/Withdraw remain blocked.

Private Reality R5 offline normalization now passes: authoritative OKX/Binance observer envelopes map through a pure no-network/no-credential normalizer into a minimal balances/positions/orders/fills read model. Existing observer credential locations are bound externally, Binance executor credentials are explicitly excluded, and private account data remains blocked pending fresh permission verification.

Execution Reconciliation R6 now passes offline: authoritative normalized venue reality is mapped into FIX 4.4 execution lifecycle vocabulary, while Market Capital retains only EffectAuthority disposition. Broad snapshot absence is never treated as no-effect; release requires terminal zero-fill with complete fill coverage or an exact authoritative negative lookup.

Demo/Testnet Execution R7 preflight is prepared but not admitted: the installed NautilusTrader execution configs construct successfully for OKX DEMO and Binance Spot TESTNET without credentials or network access. Demo/live write authority remains false.

Live endpoint test-account policy is now explicit: the user authorizes the existing OKX/Binance LIVE endpoints for non-production qualification, but they remain semantically LIVE. Fresh authoritative account reality must prove an effectively empty account (no positions/open orders/nonquote balances and <=1 quote unit), trade-only authority, clock health and reconciliation health before order submission can be enabled.
