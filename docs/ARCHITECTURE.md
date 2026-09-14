# Architecture

## Core rule

Market Capital is one canonical composition, not a federation of Ordivon finance subsystems. Use mature external financial/research infrastructure wherever it already exists; keep only the irreducible Market Capital domain semantics, mappings, decisions, authority rules and reconciliation logic in this repository.

Canonical flow:

`Evidence -> Decision -> ExecutionIntent -> Authority -> External Effect -> Reality -> Reconciliation -> Evidence`

Engine-local fills, protocol acknowledgements, workflow success and passing tests never establish capital truth or production authority by themselves.

## 1. Evidence and research

External mature sources/capabilities provide most evidence mechanics:

- CFA-informed IPS/mandate structure;
- GLEIF legal-entity identity;
- SEC/XBRL issuer disclosure;
- Research Capability for dataframe validation, Parquet, DuckDB and MLflow lineage;
- market-data providers for historical and future market reality.

Market Capital owns the mappings from admitted evidence into its domain decisions, not duplicate research infrastructure.


## Composition-first rule

Market Capital does not own mechanisms already provided by authoritative venues or mature components. Venue APIs own market/account/order reality; QuantConnect LEAN and NautilusTrader own admitted trading-engine mechanics; FIX 4.4/QuickFIX-n owns standard order-intent/execution vocabulary where applicable; TigerBeetle owns admitted double-entry accounting conservation and atomic transfer mechanics; PFMI and ISO 20022 remain post-trade reference semantics; Prometheus/Grafana own monitoring mechanics. Market Capital retains only thin decision/proof/authority/reconciliation seams. Custom mechanisms require a documented substitution failure. See `docs/COMPOSITION_FIRST_2026-09-14.md`.

### Capital accounting substrate

TigerBeetle is the mature accounting-mechanics provider. Its account and transfer state is mechanical evidence only: a TigerBeetle balance is not settlement, legal ownership, withdrawability, deployable capital, external-effect admission, or `EffectAuthority`. Market Capital keeps those domain semantics outside the provider. The server binary and official Python client are pinned to the same `0.17.9` release in an isolated external capability environment; Market Capital does not duplicate that dependency stack. R3.1 maps an exact Market Capital Reservation to a provider PENDING transfer; domain-owned RETAIN emits no provider mutation, RELEASE maps to VOID_PENDING_TRANSFER, and CONSUME maps to POST_PENDING_TRANSFER. TigerBeetle balance constraints may enforce mechanical scarcity but never mint `ScarcityAuthority`, and provider state never derives the disposition.

## 2. Decision

Portfolio construction produces an immutable decision artifact with a causal decision boundary. Decision-time inputs and future execution-time observations are kept distinct. Future market data must not silently rewrite a frozen decision or precommit.

## 3. Execution intent

QuantConnect LEAN owns mature trading-engine mechanics such as buying-power modeling, sizing, calendars and bounded execution simulation. FIX 4.4 / QuickFIX/n supplies standard order-intent semantics where appropriate. Market Capital owns the mapping from an admitted decision into an `ExecutionIntent`.

## 4. Canonical semantic and authority core

The semantic core is now implemented directly in this repository under `src/market_capital/semantic.py`; there is no active `market-capital-v2` dependency.

Canonical retained semantics are:

- observation/same-cut;
- proof binding/currentness;
- Scientific Truth != Economic Truth != Capital Truth;
- registry/parcel/scarcity identity;
- Reservation != Grant;
- EffectAuthority RETAIN/RELEASE/CONSUME;
- revocation/recovery boundaries;
- ExternalFinancialWriteAdmission (effect-surface admission, not generic product approval).

The execution boundary is `src/market_capital/authority.py` plus `config/execution_authority.json` and the contracts under `contracts/`. It expresses whether a concrete provider/executor external-effect surface is implemented, bound and current; it is not a Human/product approval gate.

All current runners must pass this in-repository effect boundary before LEAN starts. External financial write admission is `NOT_ADMITTED`; no provider write capability is bound and the external-write verifier is `NOT_IMPLEMENTED`.

## 5. External financial infrastructure

Future broker/custodian/venue integration should use mature broker APIs, LEAN brokerage adapters or FIX sessions only where they are actually required. External systems remain authoritative for account, cash, positions, order lifecycle, executions, custody and settlement evidence.

Read-only account reality precedes write authority.

## 6. Reality and reconciliation

Completion is not `send()` or an HTTP/FIX acknowledgement. The operational boundary is:

`intent -> authorized effect -> broker receipt/execution -> authoritative account reality -> reconciliation`.

Expected and authoritative state must reconcile; otherwise the effect remains pending/retained and recovery is required.

PFMI and ISO 20022 remain reference semantics for external post-trade infrastructure. Market Capital does not implement a private clearing or settlement system absent a demonstrated substitution failure.


## 7. Crypto venue lane

The active future venue qualification path is OKX + Binance Spot through an asymmetric mature-component composition: Nautilus owns admitted OMS/Risk and available execution-client mechanics; each venue's authoritative APIs own market/account/order reality; Binance public data remains on its official credential-free REST/WebSocket boundary where that is the qualified path. The lane is continuous 24/7 crypto and does not inherit the historical U.S.-equity opening-auction assumptions. Public market data is admitted without credentials; private account data, demo execution and live execution remain blocked until separately graduated.

Initial common universe: BTC/USDT and ETH/USDT. OKX Demo and Binance Demo/Testnet are the first future execution environments. Direct local exchange HTTP requires workstation scoped VPN transport. Singapore OpenVPN-TCP has passed point-in-time public-data qualification for both OKX and Binance; future sessions must rediscover/revalidate a fresh path.

## Current progression

- Wave A: investment/research loop closed.
- Wave B M1-M4: LEAN mechanics, feasibility, provider-origin historical data and FIX semantics admitted in bounded non-live lanes.
- Wave B M5: causal post-decision gate implemented.
- Wave B M6: pre-decision shadow order precommit frozen.
- Wave B M6.1: semantic/authority core migrated directly into the canonical repository; temporary cross-repo architecture removed.
- Wave B M6.2: NautilusTrader `2.0.0rc4` admitted only as a non-live candidate; OMS/Risk controls passed, but simulated `AT_THE_OPEN` execution is blocked as unsupported.
- Historical equity M7 remains a valid independent validation experiment, but the active future venue qualification path is now the separate OKX + Binance continuous crypto lane. The frozen equity experiment is not rewritten into crypto semantics.
- Crypto Public Shadow R1: concurrent OKX/Binance public REST capture is bound to exact Network v2 authorities. Whole capture rounds retry coherently on transient transport failure so only one contemporaneous round enters analysis. The latest rerun remained PARTIAL because venue-clock agreement exceeded the frozen 250 ms research gate; private/demo/live writes are independently NOT_ADMITTED.
- Crypto Shadow Mechanics R1: accepted public quote/metadata evidence now drives a local Nautilus multi-currency Spot simulation; four mechanics-only IOC intents pass venue precision/lot rules and OMS fill lifecycle with no broker connection.
- Crypto Native Adapter R1: OKX native Nautilus public data is admitted; Binance rc4 native data startup is blocked, so Binance public data stays on its official credential-free REST/WebSocket boundary and is normalized before use.
- Clock Quality Gate: fresh multi-source audits show the host/WSL clock is outside the 1000 ms gate and the error direction is unstable (previously ~2.65–2.68 s ahead, now ~2.90–2.92 s behind). Windows Time inspection is available and shows an unsynchronized Local CMOS fallback; safe remediation requires an administrator-authorized Windows path.
- Crypto Public Shadow R2: persistent public WebSocket observation consumes exact Network v2 OKX/Binance Spot WS authorities. The `websockets` client owns WebSocket/proxy mechanics; Network v2/sing-box owns provider A/B failover. One warm-up plus three measured snapshots passed the unchanged 1200 ms source/receive span gates.
- Remaining non-live admissions are composition work: minimal decision → FIX-aligned intent binding; read-only authoritative account/order/trade reality; Nautilus → OKX Demo/Binance Demo-Testnet execution; venue reconciliation; and repeated paper/recovery evidence. Live authorization remains a separate later admission.
- Crypto Stream Resilience R3: missing, stale, and time-diverged public feeds fail closed; dual-venue reconnect qualification passes real injected disconnect/reconnect tests for both OKX and Binance through exact Network v2 WS authorities. Application code no longer selects VPN node/protocol/ingress. Canonical evidence is exported through the existing node_exporter → Prometheus → Grafana stack.
- Crypto FIX Projection R4: the already-qualified four Nautilus mechanics-only Spot orders are projected through sessionless QuickFIX/n FIX 4.4 `NewOrderSingle` semantics. ClientOrderId is preserved as ClOrdID, venue is carried as ExDestination, and no network FIX session, credential, private account state or financial write is introduced.
- Private Reality read-only preflight: mature read surfaces are selected without loading credentials. OKX uses NautilusTrader `OKXHttpClient`; Binance uses first-party `binance-sdk-spot 11.3.0`. Credential use, private account reads, TRADE/Withdraw and all order submission remain NOT_ADMITTED pending separate explicit authorization.
Clock timing qualification now passes: Windows w32time is synchronized to qualified public NTP peers and WSL CLOCK_REALTIME follows the Windows host through `/dev/ptp_hyperv` using `phc2sys`; fresh external validation observed <=47.1 ms absolute error versus the frozen 1000 ms gate. Overall private/demo/live execution remains blocked by the separate NON_LIVE execution authority.

- Private Reality R5 offline normalization: venue-native observer envelopes are normalized by a pure no-network/no-credential function into balances, positions, open orders, order history and fills. Observer credential bindings are external; Binance executor credentials are excluded; fresh permission verification is still required before private account data is admitted.

- Execution Reconciliation R6: venue reality remains authoritative, FIX 4.4 supplies execution lifecycle vocabulary, and the only local semantic is EffectAuthority RETAIN/RELEASE/CONSUME. Absence from a broad snapshot is UNKNOWN/RETAIN; no-effect release requires explicit authoritative proof.

- Demo/Testnet execution R7 preflight: installed Nautilus execution components support OKX DEMO and Binance Spot TESTNET configuration without local client reimplementation. This is component readiness only; demo/live external writes remain NOT_ADMITTED.

- Live test-account admission: user-designated LIVE accounts may serve as qualification accounts without being relabeled Demo/Testnet. A pure admission evaluator requires fresh authoritative near-zero account reality, no positions/open orders/nonquote balances, <=1 quote unit, trade permission, no withdraw/transfer authority, clock PASS and reconciliation health. Production trading remains false.
