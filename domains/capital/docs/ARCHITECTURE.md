# Ordivon Capital Architecture

## Core rule

Ordivon Capital is a composition/control plane, not a new financial framework. External standards define semantics and providers own authoritative external reality. Mature implementations are candidates for mechanics until they pass current language, semantic, executable and comparative qualification gates. Ordivon keeps local mechanisms when no external candidate is admitted, while minimizing them to the exact bounded contract.

The currently instantiated Python source-owner packages are Markets, Trading, Portfolio, Risk, Research, Governance, and Accounting. The former monolithic ordivon_capital.market package is retired with no compatibility shim.

Ordivon Capital is the umbrella. The currently instantiated source-owner domains are `markets/`, `trading/`, `portfolio/`, `risk/`, `research/`, `governance/`, and `accounting/`. No empty Treasury/Compute/Human/etc. packages are created merely to mirror a conceptual taxonomy. `config/capital_domain_taxonomy.json` defines the source-owner taxonomy and `config/external_owner_census.json` is the machine-readable implementation-ownership audit.

`Markets` owns observable public market/reference facts, microstructure and streaming qualification. `Trading` owns provider/private reality, order intent, execution feasibility, FIX projection and reconciliation. `Portfolio` owns caller-supplied portfolio counterfactuals; `Risk` owns exposure and risk measurement; `Research` owns model/evidence validation; `Governance` owns authorization/policy gates; `Accounting` owns durable ledger mechanics. `Execution` is therefore a capability inside Trading rather than a synonym for Capital or Markets.

Canonical flow:

`Provider/Data Evidence -> Frozen Decision -> Standard Execution Intent -> Bounded Policy Decision -> Provider Effect -> Authoritative Venue Reality -> Reconciliation -> Accounting`

Engine-local fills, protocol acknowledgements, workflow success and passing tests never replace authoritative venue/account/custody/settlement reality.

## 1. Evidence and research

External mature systems provide the active evidence mechanics:

- market/account providers own current external reality;
- NumPy 2.5.3, SciPy 1.18.1 and scikit-learn 1.9.1 own only their admitted numerical/statistical/estimator mechanics;
- the two current fixed Risk/Research document contracts are validated by domain-local fail-closed validators bound to exact schema SHA-256 identities; jsonschema 4.26.0 is retained only as the isolated R18 differential oracle/future broader-schema candidate after 6000 mutation cases produced zero mismatches;
- PyArrow 25.0.1 / Apache Parquet owns only the bounded typed-Parquet materialization contract, while DuckDB 1.5.5 owns only independent Parquet parsing/readback plus bounded SQL assertions. R16 requalification passed Python 3.14.7, bidirectional cross-engine round-trip, Unicode/int64/nullability cases, explicit type rejection, and truncated/garbage Parquet rejection; same-engine PyArrow self-readback is deliberately not treated as an independent baseline;
- the single monitoring-row contract is validated locally after a 400-case zero-mismatch Pandera differential; MLflow, Pandera and pandas are not current Capital Research runtime dependencies.

The historical Wave-A GLEIF/SEC/Cboe/equal-weight generation pipeline is retired. Its frozen target-portfolio fixture remains only as a bound Wave-B regression/execution-mechanics input. Capital does not retain a duplicate research platform or lineage graph.

Model-risk governance follows Federal Reserve SR 26-2 proportionately as a reference framework: quantitative models require purpose, limitations, validation standing, use restrictions, inventory, and ongoing monitoring. Simple arithmetic calculations and deterministic controls are not promoted into models merely because they participate in a financial workflow.

Risk-data architecture uses BCBS 239 principles as the reference for source identity, accuracy, completeness, timeliness, aggregation, lineage, and compensating controls. This is a sound-practice reference, not a claim of bank-regulatory applicability.


## Composition-first rule

Ordivon Capital owner domains adopt a mechanism only after contract-equivalent qualification. Venue APIs own market/account/order reality. The current bounded US-equity feasibility contract is owned by the small local fee-aware sizer after zero-mismatch differential qualification against current LEAN; LEAN remains an isolated historical/general trading-engine challenger because its latest candidate is functionally green but supply-chain blocked. NautilusTrader is likewise a challenger rather than a canonical core owner. Its rc4 executable qualification tools are isolated under tools/nautilus_rc4; canonical public-data, private-read preflight, and OKX provider-audit gates do not execute rc4. Nautilus-specific episode normalization/effect-matrix adapters are likewise candidate tools; the current non-live effect admission contract is provider-neutral and retains rc4 only as historical qualification evidence. FIX Latest / FIX Orchestra remains the order-semantic reference. The current legacy FIX 4.4 mechanics projection is a bounded local sessionless TagValue projector after 120/120 byte-exact QuickFIX/n comparisons; QuickFIX/n is retained only as a differential oracle and future real-session candidate. SQLite owns the admitted single-host ACID/WAL accounting primitive; TigerBeetle is a future distributed-accounting challenger. Prometheus 3.14.0 is a Capital observability candidate rather than a current owner. A 2026-09-21 live census found the old Market-Capital node-exporter/shared-Prometheus island inactive and the active Network v2 Prometheus had zero Capital series; the stale renderer/rules/textfile/drop-in were therefore retired instead of preserved as compatibility debt. Grafana/OpenTelemetry/OpenLineage likewise remain candidates until an active contract exists. See docs/COMPOSITION_FIRST_2026-09-14.md.

### Capital accounting substrate

SQLite 3.53.1 through canonical Python 3.14.7 owns the current single-host ACID/WAL transaction primitive. Ordivon retains only the bounded reservation/post/void schema, deterministic identity binding, and fail-closed durable reconciliation seam. SQLite state is not settlement finality, legal ownership, withdrawability, deployability, venue execution truth, or external-write policy. Authoritative reconciliation maps unresolved effects to NO_MUTATION, proven no-effect to VOID_PENDING_TRANSFER, and positive execution to POST_PENDING_TRANSFER. Intact database restarts preserve exact local accounting history; missing or contradictory state requires no automatic repair and cannot reopen terminal reservation history. TigerBeetle 0.17.9 remains a challenger if replication, consensus, cluster recovery, or materially higher transaction throughput becomes an active contract.

## 2. Decision

Portfolio construction produces an immutable decision artifact with a frozen decision boundary. Prospective evaluation uses only strictly post-decision aligned holdout observations. Post-decision timing prevents leakage; it does not establish causality. Future market data must not silently rewrite a frozen decision or precommit.

## 3. Execution intent

The current execution-feasibility contract is deliberately narrow: empty USD portfolio, positive long US equities, one-share lot, explicit free-portfolio buffer, and the frozen default LEAN/Interactive-Brokers-style equity fee mechanics. `src/ordivon_capital/trading/execution_feasibility.py` owns that bounded calculation after 57 fee-aware differential comparisons against LEAN 985ef30 produced zero mismatches; unsupported mechanics fail closed. LEAN remains a historical/general backtest, fill, slippage, calendar, and broader buying-power challenger rather than a current core owner. FIX Latest / FIX Orchestra supplies the semantic reference for order intent. The current FIX 4.4 compatibility projection is local, sessionless and explicitly incomplete as a network wire frame: it does not claim BodyLength/CheckSum or FIX session mechanics. QuickFIX/n 1.14.1 remains the oracle/future session-engine candidate.

## 4. External ownership and policy boundaries

The former custom semantic core is retired. Current boundaries are owned by provider reality, FIX lifecycle vocabulary, admitted accounting mechanics, bounded local deterministic policy decisions, and narrow reconciliation mappings.

Retained local seams are:

- provider-native observation normalization and BCBS-239-style quality/lineage checks;
- frozen-decision to standard execution-intent mapping;
- bounded local deterministic policy input normalization and fail-closed enforcement;
- venue-native order/fill state to FIX lifecycle normalization;
- authoritative reconciliation to bounded accounting reservation resolution on the admitted SQLite substrate;
- provider restart/recovery identity bindings required by the composition.

The Governance-domain execution-policy enforcement point is src/ordivon_capital/governance/policy_decision.py plus config/execution_policy.json. The current contract is a bounded deterministic rule set evaluated directly in canonical Python 3.14.7. OPA 1.20.2 is retained only as historical differential evidence under tools/opa_1_20_2.

Current runners that cross the effect boundary pass the bounded local policy-decision point. The current policy input yields `allowExternalWrite=false`; no live external-write execution path is implemented. LEAN is not a prerequisite for canonical current runners.

## 5. External financial infrastructure

Future broker/custodian/venue integration should use mature broker APIs, LEAN brokerage adapters or FIX sessions only where they are actually required. External systems remain authoritative for account, cash, positions, order lifecycle, executions, custody and settlement evidence.

Read-only account reality precedes write authority.

## 6. Reality and reconciliation

Completion is not `send()` or an HTTP/FIX acknowledgement. The operational boundary is:

`intent -> authorized effect -> broker receipt/execution -> authoritative account reality -> reconciliation`.

Expected and authoritative state must reconcile; otherwise the pending accounting state remains unchanged and recovery/reconciliation is required.

PFMI and ISO 20022 remain reference semantics for external post-trade infrastructure. The Trading/Accounting domains do not implement a private clearing or settlement system absent a demonstrated substitution failure. Historical LEAN Wave-B runners and their algorithm build payload, plus TigerBeetle/Nautilus qualification runners, are isolated under tools as replay/candidate surfaces; their legacy class names and stable provider IDs are preserved for reproducibility but are not current scripts or runtime owners. The frozen wave_b/fixtures/wave_a_target_portfolio.json path remains intentionally retained as a provenance/regression identity.


## 7. Crypto venue lane

The active future venue qualification path is OKX + Binance Spot through an asymmetric composition: each venue's authoritative APIs own market/account/order reality; NautilusTrader remains an execution/OMS/reconciliation challenger and has no canonical core dependency until a current candidate passes all gates; Binance public data remains on its official credential-free REST/WebSocket boundary where that is the qualified path. The lane is continuous 24/7 crypto and does not inherit the historical U.S.-equity opening-auction assumptions. Public market data is admitted without credentials; private account data, demo execution and live execution remain blocked until separately graduated.

Initial common universe: BTC/USDT and ETH/USDT. OKX Demo and Binance Demo/Testnet are the first future execution environments. Direct local exchange HTTP requires workstation scoped VPN transport. Singapore OpenVPN-TCP has passed point-in-time public-data qualification for both OKX and Binance; future sessions must rediscover/revalidate a fresh path.

## Current standing projection

Current source/authority standing is maintained in docs/CURRENT_STATE.md and mechanically projected in planning/current-truth-r1.json. Historical Wave A/B, clock, provider, qualification and migration observations are retained in docs/history/ARCHITECTURE_PROGRESSION_THROUGH_20260921.md; they are provenance, not present-tense authority.

The current architectural invariants remain:

- the execution lane is NON_LIVE;
- production external financial writes are BLOCK_NOT_GRANTED;
- portfolio risk budget is UNSET until supplied by OWNER_PRINCIPAL;
- private account data remains NOT_ADMITTED pending fresh provider-permission verification;
- provider reality outranks engine/workflow/local-ledger claims for external financial truth;
- Execution remains a capability under Trading;
- current local single-host accounting mechanics are SQLite-backed and do not establish settlement, ownership, venue execution or write authorization.
