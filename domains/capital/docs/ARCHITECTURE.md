# Ordivon Capital Architecture

## Core rule

Ordivon Capital is a composition/control plane, not a new financial framework. External standards define semantics, mature implementations own mechanics, and providers own external reality. Ordivon keeps only the evidence/authority/reconciliation seams that cannot be established by one external owner alone.

The currently instantiated domains are:

- `ordivon_capital.market`: Market-domain provider, research-binding, risk, execution, and reconciliation glue;
- `ordivon_capital.accounting`: TigerBeetle integration only; TigerBeetle remains the accounting-mechanics owner.

Market is a child domain of Ordivon Capital. No empty Treasury/Compute/Human/etc. packages are created merely to mirror a conceptual taxonomy. `config/external_owner_census.json` is the machine-readable ownership audit.

Canonical flow:

`Provider/Data Evidence -> Frozen Decision -> Standard Execution Intent -> OPA Policy Decision -> Provider Effect -> Authoritative Venue Reality -> Reconciliation -> Accounting`

Engine-local fills, protocol acknowledgements, workflow success and passing tests never replace authoritative venue/account/custody/settlement reality.

## 1. Evidence and research

External mature systems provide the active evidence mechanics:

- market/account providers own current external reality;
- NumPy/SciPy/scikit-learn own admitted numerical/model mechanics;
- Pandera owns dataframe contracts, Parquet/PyArrow owns columnar materialization, DuckDB supplies independent readback, and MLflow owns run/artifact tracking configuration and storage semantics.

The historical Wave-A GLEIF/SEC/Cboe/equal-weight generation pipeline is retired. Its frozen target-portfolio fixture remains only as a bound Wave-B regression/execution-mechanics input. Capital does not retain a duplicate research platform or lineage graph.

Model-risk governance follows Federal Reserve SR 26-2 proportionately as a reference framework: quantitative models require purpose, limitations, validation standing, use restrictions, inventory, and ongoing monitoring. Simple arithmetic calculations and deterministic controls are not promoted into models merely because they participate in a financial workflow.

Risk-data architecture uses BCBS 239 principles as the reference for source identity, accuracy, completeness, timeliness, aggregation, lineage, and compensating controls. This is a sound-practice reference, not a claim of bank-regulatory applicability.


## Composition-first rule

The Ordivon Capital Market domain does not own mechanisms already provided by authoritative venues or mature components. Venue APIs own market/account/order reality; QuantConnect LEAN and NautilusTrader own admitted trading-engine mechanics; FIX Latest / FIX Orchestra is the order-semantic reference while QuickFIX/n and explicit legacy FIX profiles provide wire compatibility where required; TigerBeetle owns admitted double-entry accounting conservation and atomic transfer mechanics; PFMI and ISO 20022 remain post-trade reference semantics; Prometheus/Grafana own monitoring mechanics. The Market domain retains only narrow mappings, policy enforcement, data-quality checks, and reconciliation seams. Custom mechanisms require a documented substitution failure. See `docs/COMPOSITION_FIRST_2026-09-14.md`.

### Capital accounting substrate

TigerBeetle owns accounting conservation, pending-transfer encumbrance, and POST/VOID mechanics. A TigerBeetle balance is not settlement finality, legal ownership, withdrawability, deployability, venue execution truth, or external-write policy. Authoritative reconciliation maps unresolved effects to NO_MUTATION, proven no-effect to VOID_PENDING_TRANSFER, and positive execution to POST_PENDING_TRANSFER. Intact-data restarts preserve exact provider history; missing or contradictory provider state requires no automatic repair and cannot reopen terminal reservation history.

## 2. Decision

Portfolio construction produces an immutable decision artifact with a frozen decision boundary. Prospective evaluation uses only strictly post-decision aligned holdout observations. Post-decision timing prevents leakage; it does not establish causality. Future market data must not silently rewrite a frozen decision or precommit.

## 3. Execution intent

QuantConnect LEAN owns mature trading-engine mechanics such as buying-power modeling, sizing, calendars and bounded execution simulation. FIX Latest / FIX Orchestra supplies the semantic reference for order intent. QuickFIX/n may project an explicitly required legacy FIX 4.4 wire profile, but FIX 4.4 is not treated as the current semantic standard. The Market domain owns only the mapping from an admitted decision into an `ExecutionIntent`.

## 4. External ownership and policy boundaries

The former custom semantic core is retired. Current boundaries are owned by provider reality, FIX lifecycle vocabulary, TigerBeetle accounting mechanics, OPA policy, and narrow reconciliation mappings.

Retained local seams are:

- provider-native observation normalization and BCBS-239-style quality/lineage checks;
- frozen-decision to standard execution-intent mapping;
- OPA policy input construction and fail-closed policy enforcement;
- venue-native order/fill state to FIX lifecycle normalization;
- authoritative reconciliation to TigerBeetle pending-transfer resolution;
- provider restart/recovery identity bindings required by the composition.

The Market-domain execution-policy enforcement point is `src/ordivon_capital/market/opa_policy.py` plus `config/execution_policy.json`. OPA is the policy decision point; Python only supplies facts, requests decisions, and fails closed.

All current runners must pass the OPA-governed execution-policy enforcement point before LEAN starts. The current policy input yields `allowExternalWrite=false`; no live external-write execution path is implemented.

## 5. External financial infrastructure

Future broker/custodian/venue integration should use mature broker APIs, LEAN brokerage adapters or FIX sessions only where they are actually required. External systems remain authoritative for account, cash, positions, order lifecycle, executions, custody and settlement evidence.

Read-only account reality precedes write authority.

## 6. Reality and reconciliation

Completion is not `send()` or an HTTP/FIX acknowledgement. The operational boundary is:

`intent -> authorized effect -> broker receipt/execution -> authoritative account reality -> reconciliation`.

Expected and authoritative state must reconcile; otherwise the pending accounting state remains unchanged and recovery/reconciliation is required.

PFMI and ISO 20022 remain reference semantics for external post-trade infrastructure. The Market domain does not implement a private clearing or settlement system absent a demonstrated substitution failure.


## 7. Crypto venue lane

The active future venue qualification path is OKX + Binance Spot through an asymmetric mature-component composition: Nautilus owns admitted OMS/Risk and available execution-client mechanics; each venue's authoritative APIs own market/account/order reality; Binance public data remains on its official credential-free REST/WebSocket boundary where that is the qualified path. The lane is continuous 24/7 crypto and does not inherit the historical U.S.-equity opening-auction assumptions. Public market data is admitted without credentials; private account data, demo execution and live execution remain blocked until separately graduated.

Initial common universe: BTC/USDT and ETH/USDT. OKX Demo and Binance Demo/Testnet are the first future execution environments. Direct local exchange HTTP requires workstation scoped VPN transport. Singapore OpenVPN-TCP has passed point-in-time public-data qualification for both OKX and Binance; future sessions must rediscover/revalidate a fresh path.

## Current progression

- Historical Wave A: generator retired; frozen target-portfolio fixture retained for Wave-B regression/execution-mechanics compatibility.
- Wave B M1-M4: LEAN mechanics, feasibility, provider-origin historical data and FIX semantics admitted in bounded non-live lanes.
- Wave B M5: prospective post-decision holdout validation implemented; no causal inference is claimed.
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
- Binance USD-M Equity Perp Provider R1: TradFi Equity Perpetuals are a separate provider scope from the historical Binance Spot lane. The official Binance USD-M SDK 17.4.0 owns /fapi REST/WebSocket mechanics; Network v2 owns fapi.binance.com / fstream.binance.com transport; exchangeInfo filters own tick/step/min-notional rules; Position V3/leverageBracket/USER_DATA streams will own private risk truth once credentials are freshly qualified. Public SNDKUSDT consequence passed; private USER_DATA/product eligibility remain pending; TradFi agreement, leverage/margin mutations and all TRADE surfaces remain non-admitted.

- Execution Reconciliation R6: venue reality remains authoritative and FIX lifecycle vocabulary normalizes order state. Absence from a broad snapshot yields UNKNOWN with NO_MUTATION; explicit authoritative no-effect proof maps to VOID_PENDING_TRANSFER; positive execution maps to POST_PENDING_TRANSFER.

- Demo/Testnet execution R7 preflight: installed Nautilus execution components support OKX DEMO and Binance Spot TESTNET configuration without local client reimplementation. This is component readiness only; demo/live external writes remain NOT_ADMITTED.

- Live test-account admission: user-designated LIVE accounts may serve as qualification accounts without being relabeled Demo/Testnet. A pure admission evaluator requires fresh authoritative near-zero account reality, no positions/open orders/nonquote balances, <=1 quote unit, trade permission, no withdraw/transfer authority, clock PASS and reconciliation health. Production trading remains false.
