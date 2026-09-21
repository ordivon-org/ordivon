# Ordivon Capital Architecture

## Core rule

Ordivon Capital is a composition/control plane, not a new financial framework. External standards define semantics and providers own authoritative external reality. Mature implementations are candidates for mechanics until they pass current language, semantic, executable and comparative qualification gates. Ordivon keeps local mechanisms when no external candidate is admitted, while minimizing them to the exact bounded contract.

The currently instantiated domains are:

- `ordivon_capital.market`: Market-domain provider, research-binding, risk, execution, and reconciliation glue;
- `ordivon_capital.accounting`: bounded provider-neutral accounting semantics composed onto SQLite WAL/FULL mechanics; TigerBeetle is retained only as a distributed-accounting challenger.

Market is a child domain of Ordivon Capital. No empty Treasury/Compute/Human/etc. packages are created merely to mirror a conceptual taxonomy. `config/external_owner_census.json` is the machine-readable ownership audit.

Canonical flow:

`Provider/Data Evidence -> Frozen Decision -> Standard Execution Intent -> Bounded Policy Decision -> Provider Effect -> Authoritative Venue Reality -> Reconciliation -> Accounting`

Engine-local fills, protocol acknowledgements, workflow success and passing tests never replace authoritative venue/account/custody/settlement reality.

## 1. Evidence and research

External mature systems provide the active evidence mechanics:

- market/account providers own current external reality;
- NumPy 2.5.3, SciPy 1.18.1 and scikit-learn 1.9.1 own only their admitted numerical/statistical/estimator mechanics;
- jsonschema 4.26.0 owns Draft 2020-12 schema evaluation for the two active domain schemas;
- PyArrow 25.0.1 / Apache Parquet owns typed columnar materialization and DuckDB 1.5.5 supplies independent readback;
- the single monitoring-row contract is validated locally after a 400-case zero-mismatch Pandera differential; MLflow, Pandera and pandas are not current Market runtime dependencies.

The historical Wave-A GLEIF/SEC/Cboe/equal-weight generation pipeline is retired. Its frozen target-portfolio fixture remains only as a bound Wave-B regression/execution-mechanics input. Capital does not retain a duplicate research platform or lineage graph.

Model-risk governance follows Federal Reserve SR 26-2 proportionately as a reference framework: quantitative models require purpose, limitations, validation standing, use restrictions, inventory, and ongoing monitoring. Simple arithmetic calculations and deterministic controls are not promoted into models merely because they participate in a financial workflow.

Risk-data architecture uses BCBS 239 principles as the reference for source identity, accuracy, completeness, timeliness, aggregation, lineage, and compensating controls. This is a sound-practice reference, not a claim of bank-regulatory applicability.


## Composition-first rule

The Ordivon Capital Market domain adopts a mechanism only after contract-equivalent qualification. Venue APIs own market/account/order reality. The current bounded US-equity feasibility contract is owned by the small local fee-aware sizer after zero-mismatch differential qualification against current LEAN; LEAN remains an isolated historical/general trading-engine challenger because its latest candidate is functionally green but supply-chain blocked. NautilusTrader is likewise a challenger rather than a canonical core owner. FIX Latest / FIX Orchestra remains the order-semantic reference. The current legacy FIX 4.4 mechanics projection is a bounded local sessionless TagValue projector after 120/120 byte-exact QuickFIX/n comparisons; QuickFIX/n is retained only as a differential oracle and future real-session candidate. SQLite owns the admitted single-host ACID/WAL accounting primitive; TigerBeetle is a future distributed-accounting challenger. Prometheus 3.14.0 is a Market-domain candidate rather than a current owner: the only active Prometheus service is Network v2 and it has no Market target, loaded Market rule group, or Market metric series. Grafana/OpenTelemetry/OpenLineage likewise remain candidates until an active contract exists. See docs/COMPOSITION_FIRST_2026-09-14.md.

### Capital accounting substrate

SQLite 3.53.1 through canonical Python 3.14.7 owns the current single-host ACID/WAL transaction primitive. Ordivon retains only the bounded reservation/post/void schema, deterministic identity binding, and fail-closed durable reconciliation seam. SQLite state is not settlement finality, legal ownership, withdrawability, deployability, venue execution truth, or external-write policy. Authoritative reconciliation maps unresolved effects to NO_MUTATION, proven no-effect to VOID_PENDING_TRANSFER, and positive execution to POST_PENDING_TRANSFER. Intact database restarts preserve exact local accounting history; missing or contradictory state requires no automatic repair and cannot reopen terminal reservation history. TigerBeetle 0.17.9 remains a challenger if replication, consensus, cluster recovery, or materially higher transaction throughput becomes an active contract.

## 2. Decision

Portfolio construction produces an immutable decision artifact with a frozen decision boundary. Prospective evaluation uses only strictly post-decision aligned holdout observations. Post-decision timing prevents leakage; it does not establish causality. Future market data must not silently rewrite a frozen decision or precommit.

## 3. Execution intent

The current execution-feasibility contract is deliberately narrow: empty USD portfolio, positive long US equities, one-share lot, explicit free-portfolio buffer, and the frozen default LEAN/Interactive-Brokers-style equity fee mechanics. `src/ordivon_capital/market/execution_feasibility.py` owns that bounded calculation after 57 fee-aware differential comparisons against LEAN 985ef30 produced zero mismatches; unsupported mechanics fail closed. LEAN remains a historical/general backtest, fill, slippage, calendar, and broader buying-power challenger rather than a current core owner. FIX Latest / FIX Orchestra supplies the semantic reference for order intent. The current FIX 4.4 compatibility projection is local, sessionless and explicitly incomplete as a network wire frame: it does not claim BodyLength/CheckSum or FIX session mechanics. QuickFIX/n 1.14.1 remains the oracle/future session-engine candidate.

## 4. External ownership and policy boundaries

The former custom semantic core is retired. Current boundaries are owned by provider reality, FIX lifecycle vocabulary, admitted accounting mechanics, bounded local deterministic policy decisions, and narrow reconciliation mappings.

Retained local seams are:

- provider-native observation normalization and BCBS-239-style quality/lineage checks;
- frozen-decision to standard execution-intent mapping;
- bounded local deterministic policy input normalization and fail-closed enforcement;
- venue-native order/fill state to FIX lifecycle normalization;
- authoritative reconciliation to bounded accounting reservation resolution on the admitted SQLite substrate;
- provider restart/recovery identity bindings required by the composition.

The Market-domain execution-policy enforcement point is src/ordivon_capital/market/policy_decision.py plus config/execution_policy.json. The current contract is a bounded deterministic rule set evaluated directly in canonical Python 3.14.7. OPA 1.20.2 is retained only as historical differential evidence under tools/opa_1_20_2.

Current runners that cross the effect boundary pass the bounded local policy-decision point. The current policy input yields `allowExternalWrite=false`; no live external-write execution path is implemented. LEAN is not a prerequisite for canonical current runners.

## 5. External financial infrastructure

Future broker/custodian/venue integration should use mature broker APIs, LEAN brokerage adapters or FIX sessions only where they are actually required. External systems remain authoritative for account, cash, positions, order lifecycle, executions, custody and settlement evidence.

Read-only account reality precedes write authority.

## 6. Reality and reconciliation

Completion is not `send()` or an HTTP/FIX acknowledgement. The operational boundary is:

`intent -> authorized effect -> broker receipt/execution -> authoritative account reality -> reconciliation`.

Expected and authoritative state must reconcile; otherwise the pending accounting state remains unchanged and recovery/reconciliation is required.

PFMI and ISO 20022 remain reference semantics for external post-trade infrastructure. The Market domain does not implement a private clearing or settlement system absent a demonstrated substitution failure.


## 7. Crypto venue lane

The active future venue qualification path is OKX + Binance Spot through an asymmetric composition: each venue's authoritative APIs own market/account/order reality; NautilusTrader remains an execution/OMS/reconciliation challenger and has no canonical core dependency until a current candidate passes all gates; Binance public data remains on its official credential-free REST/WebSocket boundary where that is the qualified path. The lane is continuous 24/7 crypto and does not inherit the historical U.S.-equity opening-auction assumptions. Public market data is admitted without credentials; private account data, demo execution and live execution remain blocked until separately graduated.

Initial common universe: BTC/USDT and ETH/USDT. OKX Demo and Binance Demo/Testnet are the first future execution environments. Direct local exchange HTTP requires workstation scoped VPN transport. Singapore OpenVPN-TCP has passed point-in-time public-data qualification for both OKX and Binance; future sessions must rediscover/revalidate a fresh path.

## Current progression

- Historical Wave A: generator retired; frozen target-portfolio fixture retained for Wave-B regression/execution-mechanics compatibility.
- Historical Wave B M1-M4: LEAN mechanics, provider-origin historical data and FIX semantics remain reproducible evidence. Current sizing/feasibility ownership has moved to the bounded local fee-aware sizer after LEAN 985ef30 differential qualification; LEAN is not a canonical core gate.
- Wave B M5: prospective post-decision holdout validation implemented; no causal inference is claimed.
- Historical Wave B M6: pre-decision LEAN shadow-order precommit remains frozen evidence. The current `shadow_precommit` sizing owner is the local bounded sizer; the historical LEAN runner remains a challenger reproduction path.
- Wave B M6.1: semantic/authority core migrated directly into the canonical repository; temporary cross-repo architecture removed.
- Wave B M6.2: NautilusTrader `2.0.0rc4` admitted only as a non-live candidate; OMS/Risk controls passed, but simulated `AT_THE_OPEN` execution is blocked as unsupported.
- Historical equity M7 remains a valid independent validation experiment, but the active future venue qualification path is now the separate OKX + Binance continuous crypto lane. The frozen equity experiment is not rewritten into crypto semantics.
- Crypto Public Shadow R1: concurrent OKX/Binance public REST capture is bound to exact Network v2 authorities. Whole capture rounds retry coherently on transient transport failure so only one contemporaneous round enters analysis. The latest rerun remained PARTIAL because venue-clock agreement exceeded the frozen 250 ms research gate; private/demo/live writes are independently NOT_ADMITTED.
- Crypto Shadow Mechanics R1: accepted public quote/metadata evidence now drives a local Nautilus multi-currency Spot simulation; four mechanics-only IOC intents pass venue precision/lot rules and OMS fill lifecycle with no broker connection.
- Crypto Native Adapter R1: OKX native Nautilus public data is admitted; Binance rc4 native data startup is blocked, so Binance public data stays on its official credential-free REST/WebSocket boundary and is normalized before use.
- Clock Quality Gate: fresh multi-source audits show the host/WSL clock is outside the 1000 ms gate and the error direction is unstable (previously ~2.65–2.68 s ahead, now ~2.90–2.92 s behind). Windows Time inspection is available and shows an unsynchronized Local CMOS fallback; safe remediation requires an administrator-authorized Windows path.
- Crypto Public Shadow R2: persistent public WebSocket observation uses websockets 17.1 for protocol/client mechanics and Network v2 for route authority. A transient 2026-09-21 dual-venue failure was traced to Network v2/sing-box DNS lookup failures, not the WebSocket library. After DNS recovery, fresh R2 passed one warm-up plus three measured snapshots under the unchanged 1200 ms source/receive gates.
- Remaining non-live admissions are qualification/composition work: minimal decision → FIX-aligned intent binding; read-only authoritative account/order/trade reality; compare current execution-engine candidates against the bounded local baseline; venue reconciliation; and repeated paper/recovery evidence. NautilusTrader may be used only after a current latest-language candidate passes the exact contract. Live authorization remains a separate later admission.
- Crypto Stream Resilience R3: missing, stale, and time-diverged public feeds fail closed. Fresh 2026-09-21 injected-disconnect qualification passes both venues through exact Network v2 WS authorities: OKX reconnect 689.3 ms, Binance 5826.4 ms, both generation 2, recovery qualified, three measured rounds each, zero final-run connection errors, under hardened transport binding sha256:f7b0cea.... The R3 runner now uses the canonical Python capability runner and always preserves both venue results instead of collapsing first-venue failure into NO_SESSION_RESULT. Application code does not select VPN node/protocol/ingress.
- Crypto FIX Projection R4: the already-qualified four historical mechanics-only Spot intents are projected through the local bounded sessionless FIX 4.4 NewOrderSingle TagValue projector. It matched QuickFIX/n 1.14.1 byte-for-byte in 120/120 differential cases. ClientOrderId remains ClOrdID, venue remains ExDestination, and no network FIX session, credential, private account state or financial write is introduced.
- OKX provider-capability audit: the live-trade credential is queried only through a local Python 3.14 stdlib GET-only client restricted to account config, trading-account balance and open Spot orders. It matched @okx_ai/okx-trade-cli 1.4.7 on 120/120 HMAC vectors and 3/3 live structural reads, while structurally exposing no client write method. The credential nevertheless has provider Trade permission, so this lane is evidence about provider capability and is not the canonical private-Reality observer. The dedicated OKX observer lane remains pending fresh provider-permission verification; Binance Spot/USD-M private USER_DATA contracts are also not admitted.
Clock timing qualification now passes: Windows w32time is synchronized to qualified public NTP peers and WSL CLOCK_REALTIME follows the Windows host through `/dev/ptp_hyperv` using `phc2sys`; fresh external validation observed <=47.1 ms absolute error versus the frozen 1000 ms gate. Overall private/demo/live execution remains blocked by the separate NON_LIVE execution authority.

- Private Reality R5 offline normalization: venue-native observer envelopes are normalized by a pure no-network/no-credential function into balances, positions, open orders, order history and fills. Observer credential bindings are external; Binance executor credentials are excluded; fresh permission verification is still required before private account data is admitted.
- Binance USD-M Equity Perp Provider R1: TradFi Equity Perpetuals are a separate provider scope from the historical Binance Spot lane. The official Binance USD-M SDK 17.4.0 owns /fapi REST/WebSocket mechanics; Network v2 owns fapi.binance.com / fstream.binance.com transport; exchangeInfo filters own tick/step/min-notional rules; Position V3/leverageBracket/USER_DATA streams will own private risk truth once credentials are freshly qualified. Public SNDKUSDT consequence passed; private USER_DATA/product eligibility remain pending; TradFi agreement, leverage/margin mutations and all TRADE surfaces remain non-admitted.

- Execution Reconciliation R6: venue reality remains authoritative and FIX lifecycle vocabulary normalizes order state. Absence from a broad snapshot yields UNKNOWN with NO_MUTATION; explicit authoritative no-effect proof maps to VOID_PENDING_TRANSFER; positive execution maps to POST_PENDING_TRANSFER.

- Demo/Testnet execution R7 preflight: the historical rc4 candidate exposed OKX DEMO and Binance Spot TESTNET configuration without local client reimplementation. This proves candidate component readiness only; it does not admit Nautilus under the current Python 3.14.7 / Rust 1.98.1 baseline, and demo/live external writes remain NOT_ADMITTED.

- Live test-account admission: user-designated LIVE accounts may serve as qualification accounts without being relabeled Demo/Testnet. A pure admission evaluator requires fresh authoritative near-zero account reality, no positions/open orders/nonquote balances, <=1 quote unit, trade permission, no withdraw/transfer authority, clock PASS and reconciliation health. Production trading remains false.
