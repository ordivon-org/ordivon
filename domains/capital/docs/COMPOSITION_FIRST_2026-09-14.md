# Market Capital — Composition First

## Rule

Market Capital composes mature external mechanisms before implementing local mechanisms.

A local implementation is admitted only when a concrete substitution failure has been demonstrated against the selected mature component. Preference order:

1. authoritative venue/broker/custodian API;
2. mature trading/runtime/protocol implementation;
3. international or industry-standard semantic model;
4. thin local mapping, proof binding, and authority seam;
5. custom mechanism only after documented substitution failure.

The goal is not a uniform framework. Asymmetric composition is preferred when different mature components own different responsibilities better.

## Current component ownership

| Responsibility | Primary owner | Local Market Capital responsibility |
|---|---|---|
| Public OKX market data | OKX public API + Network v2 exact authority | evidence binding and common observation projection |
| Public Binance market data | Binance official public REST/WebSocket + Network v2 exact authority | thin normalization into the common observation projection |
| Market-data resilience | venue WebSocket protocols + `websockets` + Network v2/sing-box | qualification harness and fail-closed health evidence; no local VPN/path selector |
| Historical execution mechanics | QuantConnect LEAN | decision-to-engine mapping and evidence |
| Order intent semantics | FIX Latest / FIX Orchestra; QuickFIX/n for explicit wire profiles | semantic mapping, compatibility-profile binding and proof identity |
| Crypto OMS/Risk mechanics | NautilusTrader | admitted configuration and evidence |
| OKX execution transport | Nautilus `OKXExecutionClientConfig` / factory | configuration, qualification and authority boundary |
| Binance execution transport | Nautilus `BinanceExecutionClientConfig` / factory | configuration, qualification and authority boundary |
| OKX non-live venue | OKX Demo | qualification only; venue remains authoritative |
| Binance non-live venue | Binance Demo/Testnet | qualification only; venue remains authoritative |
| Account/order/fill reality | venue private/account APIs | read model and reconciliation mapping |
| Execution lifecycle vocabulary | FIX ExecutionReport semantics where applicable | venue-to-standard state mapping |
| Post-trade/finality boundary | venue/custodian reality, PFMI reference semantics | no private settlement implementation |
| Securities/post-trade vocabulary | ISO 20022 reference semantics where applicable | mapping only, not protocol emulation |
| Clock authority | Windows w32time → Hyper-V PTP → linuxptp phc2sys | qualification gate only |
| Model-risk governance | Federal Reserve SR 26-2 reference framework | inventory, validation standing, limitations and monitoring bindings |
| Risk-data aggregation/governance | BCBS 239 reference principles | source identity, lineage, quality, timeliness and reconciliation controls |
| Metrics and alerting | node_exporter / Prometheus / Grafana | textfile projection and domain alerts |
| Durable workflow outside hot path | existing n8n / Temporal when actually needed | orchestration only |

## Thin seams retained locally

Market Capital may retain only the semantics that external components cannot establish for the composition as a whole:

- decision evidence/currentness binding;
- decision → standard execution-intent mapping;
- proof identity/currentness across component boundaries;
- Reservation != Grant;
- fail-closed reconciliation mapping from authoritative venue state to TigerBeetle pending-transfer resolution;
- OPA external-write policy inputs, capability attenuation, revocation, and reconciliation boundaries;
- reconciliation result over authoritative venue reality.

These are seams, not replacement trading/account/settlement systems.

## Explicit non-goals

Do not build a local replacement for:

- venue market-data protocols;
- order state machines already expressible by FIX Latest / venue semantics;
- broker/exchange account protocols;
- OMS/Risk engines when LEAN/Nautilus provides the required mechanism;
- Demo/Testnet venues;
- clearing, custody, settlement or legal-ownership systems;
- time synchronization;
- monitoring stacks;
- generic workflow engines.

Do not repair a component merely to make the architecture visually uniform. Example: Binance native Nautilus public-data startup is currently blocked, but Binance official credential-free WebSocket already satisfies the public-data boundary; therefore that native startup defect is not a Market Capital blocker.

## Next composition sequence

The remaining non-live path is composition work, not subsystem construction:

1. **Decision → FIX-aligned intent**: reuse the existing QuickFIX/n FIX 4.4 projection and keep only a minimal crypto decision binding.
2. **Read-only venue reality**: qualify official OKX/Binance private account/order/trade reads before any order-capable credential is admitted.
3. **Demo/Testnet execution**: use Nautilus execution clients against OKX Demo and/or Binance Demo/Testnet; do not write a new exchange client.
4. **Reconciliation**: map authoritative venue order/trade/account state to standard execution lifecycle semantics, retaining only the thin fail-closed mapping from venue reconciliation to accounting resolution.
5. **Repeated paper evidence**: exercise reconnect, reject, cancel, partial-fill, timeout/unknown-effect and restart recovery across repeated sessions.
6. **Stop and review**: production/live authorization is a separate admission problem and is not obtained by changing configuration booleans.

No private credentials or external financial writes are admitted by this document.
