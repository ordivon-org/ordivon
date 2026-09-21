# Ordivon Capital — Composition First

## Rule

Ordivon Capital first discovers authoritative standards, provider reality, and mature external mechanisms, but discovery does not imply adoption. Market is one domain inside this composition.

External existence, age, star count, or community size makes a mechanism a candidate only. A replaceable external mechanism must win a contract-equivalent comparative qualification against the smallest credible local baseline before substitution. The local baseline is allowed to be a small multi-Agent implementation; reimplementation cost is therefore measured rather than assumed to be large.

Candidate-discovery preference:

1. authoritative venue/broker/custodian API for facts that only the provider can authoritatively establish;
2. international or industry-standard semantic model;
3. mature external implementation for non-authoritative mechanics;
4. smallest credible local implementation built from mature primitives;
5. thin cross-owner mapping, proof binding, and authority seam.

For non-authoritative mechanics, items 3 and 4 compete. Neither wins by default.

The goal is not a uniform framework. Asymmetric composition is preferred when different components demonstrably own different responsibilities better. See docs/EXTERNAL_IMPLEMENTATION_QUALIFICATION_R1.md.

## Current component ownership

| Responsibility | Primary owner | Local Ordivon Capital / Market-domain responsibility |
|---|---|---|
| Public OKX market data | OKX public API + Network v2 exact authority | evidence binding and common observation projection |
| Public Binance market data | Binance official public REST/WebSocket + Network v2 exact authority | thin normalization into the common observation projection |
| Market-data resilience | venue WebSocket protocols + `websockets` + Network v2/sing-box | qualification harness and fail-closed health evidence; no local VPN/path selector |
| Current bounded US-equity feasibility | local fee-aware sizer; LEAN 985ef30 as differential reference | exact bounded calculation only; broader mechanics fail closed |
| Historical/general trading-engine mechanics | QuantConnect LEAN candidate | isolated qualification evidence only; not a canonical core dependency while supply-chain blocked |
| Order intent semantics | FIX Latest / FIX Orchestra | local bounded sessionless FIX 4.4 TagValue projection; QuickFIX/n 1.14.1 retained only as 120/120 differential oracle/future session candidate |
| Trading OMS/Risk mechanics | NautilusTrader candidate | historical qualification evidence only until a current candidate passes all gates |
| OKX execution transport | Nautilus candidate adapter | candidate configuration/qualification only; venue remains authoritative |
| Binance execution transport | Nautilus candidate adapter | candidate configuration/qualification only; venue remains authoritative |
| OKX non-live venue | OKX Demo | qualification only; venue remains authoritative |
| Binance non-live venue | Binance Demo/Testnet | qualification only; venue remains authoritative |
| Account/order/fill reality | venue private/account APIs | OKX live-trade provider-capability audit uses a local GET-only stdlib client but does not grant private-Reality observer admission; dedicated OKX observer and Binance private lanes remain pending |
| Execution lifecycle vocabulary | FIX ExecutionReport semantics where applicable | venue-to-standard state mapping |
| Post-trade/finality boundary | venue/custodian reality, PFMI reference semantics | no private settlement implementation |
| Securities/post-trade vocabulary | ISO 20022 reference semantics where applicable | mapping only, not protocol emulation |
| Clock authority | Windows w32time → Hyper-V PTP → linuxptp phc2sys | qualification gate only |
| Model-risk governance | Federal Reserve SR 26-2 reference framework | inventory, validation standing, limitations and monitoring bindings |
| Risk-data aggregation/governance | BCBS 239 reference principles | source identity, lineage, quality, timeliness and reconciliation controls |
| Market metrics/alerting candidate | Prometheus 3.14.0 + node exporter configuration | current repo emits Prometheus text format and retains validated rule files, but no active Market scrape/TSDB/rule-evaluation consumer is observed; Grafana remains a candidate |
| Durable workflow outside hot path | existing n8n / Temporal when actually needed | orchestration only |

## Thin seams retained locally

Ordivon Capital may retain only the semantics that external components cannot establish for the composition as a whole:

- decision evidence/currentness binding;
- decision → standard execution-intent mapping;
- provider and artifact identity binding across component boundaries;
- fail-closed reconciliation mapping from authoritative venue state to bounded accounting reservation resolution;
- bounded local external-write policy inputs, capability attenuation, revocation, and reconciliation boundaries;
- reconciliation result over authoritative venue reality.

These are seams, not replacement trading/account/settlement systems.

## Explicit non-goals

Do not build a local replacement for:

- venue market-data protocols;
- order state machines already expressible by FIX Latest / venue semantics;
- broker/exchange account protocols;
- general OMS/Risk/backtest engines unless a candidate wins the exact active contract; bounded local mechanisms must not silently grow into a general engine;
- Demo/Testnet venues;
- clearing, custody, settlement or legal-ownership systems;
- time synchronization;
- monitoring stacks;
- generic workflow engines.

Do not repair a component merely to make the architecture visually uniform. Example: Binance native Nautilus public-data startup is currently blocked, but Binance official credential-free WebSocket already satisfies the public-data boundary; therefore that native startup defect is not an Ordivon Capital blocker.

## Next composition sequence

The remaining non-live path is composition work, not subsystem construction:

1. **Decision → FIX-aligned intent**: use the local bounded sessionless FIX 4.4 TagValue projector; QuickFIX/n is not a canonical runtime dependency unless a future real FIX session contract is activated.
2. **Read-only venue reality**: the OKX three-GET implementation is qualified for provider-capability auditing, but the exercised live-trade credential is not the private-Reality observer. Fresh provider permission verification of the dedicated OKX observer remains required; Binance private reads likewise remain unadmitted.
3. **Demo/Testnet execution**: qualify a latest-language current execution-client candidate against OKX Demo and/or Binance Demo/Testnet; do not adopt or replace the bounded local path until the candidate wins the same contract.
4. **Reconciliation**: map authoritative venue order/trade/account state to standard execution lifecycle semantics, retaining only the thin fail-closed mapping from venue reconciliation to accounting resolution.
5. **Repeated paper evidence**: exercise reconnect, reject, cancel, partial-fill, timeout/unknown-effect and restart recovery across repeated sessions.
6. **Stop and review**: production/live authorization is a separate admission problem and is not obtained by changing configuration booleans.

No private credentials or external financial writes are admitted by this document.
