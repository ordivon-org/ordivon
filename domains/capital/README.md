# Ordivon Market Capital — Clean Room

Clean-room composition of mature external standards and implementations.

Business backbone: CFA investment-management process.
Trading semantics: FIX.
Trading runtime: pinned QuantConnect LEAN (installed and admitted for bounded non-live Wave B execution).
Post-trade reference semantics: PFMI + ISO 20022; broker/custodian infrastructure remains authoritative.
Issuer reporting: XBRL/iXBRL + Arelle.
Research: existing Ordivon Research E2E / MLflow.

## Current standing

Wave A is closed on the investment side:

`Mandate / IPS -> authoritative data -> research artifact -> portfolio construction -> target portfolio`

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. M2 adds LEAN-native pre-trade feasibility, M3 admits provenance-recorded Nasdaq historical OHLCV while remaining non-causal, M4 inserts QuickFIX/n FIX 4.4 `NewOrderSingle` semantics, M5 adds a fail-closed causal-shadow gate, M6 freezes a pre-market shadow order plan from the last pre-decision provider-origin close, and M6.1 migrates the proven semantic/authority core directly into this canonical repository so every current trading runner crosses the in-repository authority gate before LEAN starts. M5 is currently `WAITING_FOR_POST_DECISION_DATA`; M6 has emitted no LEAN orders or external effects. No FIX session, broker credential, venue write, or external financial write is admitted. Production/live authorization remains `BLOCK_NOT_GRANTED`; there is no active runtime dependency on the retired `market-capital-v2` repository. NautilusTrader `2.0.0rc4` is installed only as a shadow qualification candidate: its OMS/Risk controls pass local controls, but its simulated venue rejects the frozen M6 `AT_THE_OPEN` orders, so it is not admitted as an M6/M7 replacement or live engine. See the Wave B documents under `docs/`.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.

The active future venue qualification path is now **OKX + Binance Spot** through NautilusTrader native adapters. It is currently public-data-only and credential-free; crypto uses a separate continuous-market lane rather than rewriting the historical equity M6/M7 experiment.

Crypto Public Shadow R1 now passes dual-venue bounded public observation through fresh scoped VPN discovery, while a ~2.2 s host/exchange clock offset blocks private/demo/live execution qualification.

Crypto Shadow Mechanics R1 also passes local multi-currency Spot OMS mechanics for OKX/Binance using venue-owned tick/step precision; it remains explicitly non-economic and non-live.

Crypto data transport is now venue-specific: OKX uses the qualified Nautilus native public client, while Binance uses its official credential-free REST/WebSocket boundary because Nautilus 2.0.0rc4 still times out during native data-client startup.

Crypto Public Shadow R2 now passes repeated persistent public streaming: OKX `bbo-tbt` plus Binance market-data-only `@ticker` streams produced one warm-up and three measured coherent snapshots on a fresh HK/UDP path, with all measured source/receive spans below the frozen 1200 ms limits. This does not relax the failed private-execution clock gate.
