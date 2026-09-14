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
- ProductionAuthorization.

The execution gate is `src/market_capital/authority.py` plus `config/execution_authority.json` and the contracts under `contracts/`.

All current runners must pass this in-repository gate before LEAN starts. Production authorization is `BLOCK_NOT_GRANTED`; external financial writes are not admitted and the live verifier is not implemented.

## 5. External financial infrastructure

Future broker/custodian/venue integration should use mature broker APIs, LEAN brokerage adapters or FIX sessions only where they are actually required. External systems remain authoritative for account, cash, positions, order lifecycle, executions, custody and settlement evidence.

Read-only account reality precedes write authority.

## 6. Reality and reconciliation

Completion is not `send()` or an HTTP/FIX acknowledgement. The operational boundary is:

`intent -> authorized effect -> broker receipt/execution -> authoritative account reality -> reconciliation`.

Expected and authoritative state must reconcile; otherwise the effect remains pending/retained and recovery is required.

PFMI and ISO 20022 remain reference semantics for external post-trade infrastructure. Market Capital does not implement a private clearing or settlement system absent a demonstrated substitution failure.


## 7. Crypto venue lane

The active future venue qualification path is OKX + Binance Spot through the native NautilusTrader adapters. The lane is continuous 24/7 crypto and does not inherit the historical U.S.-equity opening-auction assumptions. Public market data is admitted without credentials; private account data, demo execution and live execution remain blocked until separately graduated.

Initial common universe: BTC/USDT and ETH/USDT. OKX Demo and Binance Demo/Testnet are the first future execution environments. Direct local exchange HTTP requires workstation scoped VPN transport. Singapore OpenVPN-TCP has passed point-in-time public-data qualification for both OKX and Binance; future sessions must rediscover/revalidate a fresh path.

## Current progression

- Wave A: investment/research loop closed.
- Wave B M1-M4: LEAN mechanics, feasibility, provider-origin historical data and FIX semantics admitted in bounded non-live lanes.
- Wave B M5: causal post-decision gate implemented.
- Wave B M6: pre-decision shadow order precommit frozen.
- Wave B M6.1: semantic/authority core migrated directly into the canonical repository; temporary cross-repo architecture removed.
- Wave B M6.2: NautilusTrader `2.0.0rc4` admitted only as a non-live candidate; OMS/Risk controls passed, but simulated `AT_THE_OPEN` execution is blocked as unsupported.
- Historical equity M7 remains a valid independent validation experiment, but the active future venue qualification path is now the separate OKX + Binance continuous crypto lane. The frozen equity experiment is not rewritten into crypto semantics.
- Crypto Public Shadow R1: fresh dual-target Surfshark discovery + one scoped VPN session + concurrent OKX/Binance public capture is admitted for bounded contemporaneous observation; private/demo/live execution remains blocked until host clock offset is <= 1000 ms on a fresh measurement.
- Crypto Shadow Mechanics R1: accepted public quote/metadata evidence now drives a local Nautilus multi-currency Spot simulation; four mechanics-only IOC intents pass venue precision/lot rules and OMS fill lifecycle with no broker connection.
- Crypto Native Adapter R1: OKX native Nautilus public data is admitted; Binance rc4 native data startup is blocked, so Binance public data stays on its official credential-free REST/WebSocket boundary and is normalized before use.
- Clock Quality Gate: fresh multi-source audits show the host/WSL clock is outside the 1000 ms gate and the error direction is unstable (previously ~2.65–2.68 s ahead, now ~2.90–2.92 s behind). Windows Time inspection is available and shows an unsynchronized Local CMOS fallback; safe remediation requires an administrator-authorized Windows path.
- Crypto Public Shadow R2: persistent public WebSocket observation is qualified on a fresh HK OpenVPN-UDP/native-a path. One warm-up plus three measured snapshots used exchange source timestamps and local monotonic receive timestamps; measured 3/3 passed the frozen 1200 ms source/receive span gates. Host wall clock was not used, and private/demo/live remain blocked by the independent clock-quality gate.
- Paper brokerage, real account reality, reconciliation and live authorization remain future admissions.
- Crypto Stream Resilience R3: missing, stale, and time-diverged public feeds fail closed; dual-venue reconnect qualification passes real injected disconnect/reconnect tests for both OKX and Binance on a fresh qualified HK/UDP/native-a path. Canonical evidence is exported through the existing node_exporter → Prometheus → Grafana stack.
Clock timing qualification now passes: Windows w32time is synchronized to qualified public NTP peers and WSL CLOCK_REALTIME follows the Windows host through `/dev/ptp_hyperv` using `phc2sys`; fresh external validation observed <=47.1 ms absolute error versus the frozen 1000 ms gate. Overall private/demo/live execution remains blocked by the separate NON_LIVE execution authority.
