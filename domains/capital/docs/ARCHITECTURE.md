# Ordivon Capital Architecture

## Finance investment program — source boundary (2026-11-06)

The Finance economic program **reuses** Capital's seven real source owners.
The existing `strategic_contribution.py` and `passive_benchmark.py` are the
current Investment Mode mechanics. No second passive-index simulator is added.
The current `investment_candidate.py` owns byte-bound economic candidate
evaluation; no second economic performance calculator is added.

`research/experiment_protocol.py` owns only a **pre-experiment** plan
commitment and subsequent readiness assessment using declared source
availability, disjoint train/validation/prospective holdout and identity
digests. Temporal instants are normalized to UTC before calendar-day
partition comparison; the frozen plan and result are strict versioned JSON
shapes, and an undeclared authority or extra economic claim cannot promote
a review standing. It complements, but does not replace, existing provider byte-binding
and return-path evaluation. UNKNOWN is not REJECTED; REVIEW_REQUIRED is
not independent research validation, broker permission or an allocation grant.

**Finance research composition** calls existing
`investment_candidate.py` for source-to-return arithmetic rather than
repeating the economics. Pre-holdout `fingerprint-policy` binds only
candidate identity, frozen instant, strategy asset weight, benchmark expense,
currency, trial count and cost categories into the plan's `configDigest`.
Source and holdout byte digests are *postfreeze* evidence, not preregistered
historical features. After observation, `review-candidate` checks exact
policy identity before delegating byte-verified source replay and the
prospective evidence gate. Complete local arithmetic without independently
attested timestamp, provider authenticity, multiple-testing correction and
independent reproduction remains `UNKNOWN`; incomplete holdout is `UNKNOWN`.
The protocol's `sha256:<hex>` prefix and the candidate's raw lowercase
64-character source/holdout digests remain their existing native contracts.

`scripts/run-finance-lego` calls the existing Capital Python toolchain
for all four research operations. An optional Agent consults
`.agents/skills/finance-experiment-review/SKILL.md`; no new Agent
registry, workflow platform, brokerage engine or source-owner tree exists.
R2.1 contract CA10 is explicitly source-qualified, and real historic
timestamp attestation remains UNKNOWN. The native acceptance uses
`mise run //domains/capital:verify`.

## Core rule

Ordivon Capital is a composition/control plane, not a new financial framework. External standards define semantics and providers own authoritative external reality. Mature implementations are candidates for mechanics until they pass current language, semantic, executable and comparative qualification gates. Ordivon keeps local mechanisms when no external candidate is admitted, while minimizing them to the exact bounded contract.

The currently instantiated Python source-owner packages are Markets, Trading, Portfolio, Risk, Research, Governance, and Accounting. The former monolithic ordivon_capital.market package is retired with no compatibility shim.

Ordivon Capital is the umbrella. The currently instantiated source-owner domains are `markets/`, `trading/`, `portfolio/`, `risk/`, `research/`, `governance/`, and `accounting/`. No empty Treasury/Compute/Human/etc. packages are created merely to mirror a conceptual taxonomy. `config/capital_domain_taxonomy.json` defines the source-owner taxonomy and `config/external_owner_census.json` is the machine-readable implementation-ownership audit.

`Markets` owns observable public market/reference facts, microstructure and streaming qualification. `Trading` owns provider/private reality, order intent, execution feasibility, FIX projection and reconciliation. `Portfolio` owns caller-supplied portfolio counterfactuals and deterministic contribution-only strategic allocation; `Risk` owns exposure and risk measurement; `Research` owns model/evidence validation; `Governance` owns authorization/policy gates; `Accounting` owns durable ledger mechanics. `Execution` is therefore a capability inside Trading rather than a synonym for Capital or Markets.

Canonical flow:

`Provider/Data Evidence -> Frozen Decision -> Standard Execution Intent -> Bounded Policy Decision -> Provider Effect -> Authoritative Venue Reality -> Reconciliation -> Accounting`

Engine-local fills, protocol acknowledgements, workflow success and passing tests never replace authoritative venue/account/custody/settlement reality.

## 1. Evidence and research

External mature systems provide the active evidence mechanics:

- market/account providers own current external reality;
- NumPy 2.5.3, SciPy 1.18.1 and scikit-learn 1.9.1 own only their admitted numerical/statistical/estimator mechanics;
- the two current fixed Risk/Research document contracts are validated by domain-local fail-closed validators bound to exact schema SHA-256 identities; jsonschema 4.26.0 is retained only as the isolated R18 differential oracle/future broader-schema candidate after 6000 mutation cases produced zero mismatches;
- Apache Parquet/PyArrow and DuckDB are qualified only for bounded typed materialization and independent read-back contracts actually consumed by current workflows; past R16/R17 version-specific qualification is historical and is not evidence of an installed binary or an active universal research-data platform;
- the single monitoring-row contract is validated locally after a 400-case zero-mismatch Pandera differential; MLflow, Pandera and pandas are not current Capital Research runtime dependencies.

The historical Wave-A GLEIF/SEC/Cboe/equal-weight generation pipeline is retired. Its frozen target-portfolio fixture remains only as a bound Wave-B regression/execution-mechanics input. Capital does not retain a duplicate research platform or lineage graph.

Model-risk governance follows Federal Reserve SR 26-2 proportionately as a reference framework: quantitative models require purpose, limitations, validation standing, use restrictions, inventory, and ongoing monitoring. Simple arithmetic calculations and deterministic controls are not promoted into models merely because they participate in a financial workflow.

Risk-data architecture uses BCBS 239 principles as the reference for source identity, accuracy, completeness, timeliness, aggregation, lineage, and compensating controls. This is a sound-practice reference, not a claim of bank-regulatory applicability.


## Composition-first rule

Ordivon Capital owner domains adopt a mechanism only after contract-equivalent qualification. Venue APIs own market/account/order reality. The current bounded US-equity feasibility contract is owned by the small local fee-aware sizer after zero-mismatch differential qualification against current LEAN; LEAN remains an isolated historical/general trading-engine challenger because its latest candidate is functionally green but supply-chain blocked. NautilusTrader is likewise a challenger rather than a canonical core owner. Its rc4 executable qualification tools are isolated under tools/nautilus_rc4; canonical public-data, private-read preflight, and OKX provider-audit gates do not execute rc4. Nautilus-specific episode normalization/effect-matrix adapters are likewise candidate tools; the current non-live effect admission contract is provider-neutral and retains rc4 only as historical qualification evidence. FIX Latest / FIX Orchestra remains the order-semantic reference. The current legacy FIX 4.4 mechanics projection is a bounded local sessionless TagValue projector after 120/120 byte-exact QuickFIX/n comparisons; QuickFIX/n is retained only as a differential oracle and future real-session candidate. PostgreSQL 18.6 through psycopg 3 is the current **native-qualified Accounting implementation owner** in the source census, while installed-service cutover remains a distinct observed fact; legacy SQLite is confined to disposable historical regression consumers, and TigerBeetle remains a separately qualified distributed-accounting challenger. Prometheus 3.14.0 is a Capital observability candidate rather than a current owner. A 2026-09-21 live census found the old Market-Capital node-exporter/shared-Prometheus island inactive and the active Network v2 Prometheus had zero Capital series; the stale renderer/rules/textfile/drop-in were therefore retired instead of preserved as compatibility debt. Grafana/OpenTelemetry/OpenLineage likewise remain candidates until an active contract exists. See docs/COMPOSITION_FIRST_2026-09-14.md.

### Capital accounting substrate
### Capital accounting substrate

The canonical source authority is
`src/ordivon_capital/accounting/postgres_ledger.py` with exact
`config/external_owner_census.json` current qualifications. Native
PostgreSQL SERIALIZABLE/uniqueness/advisory-transaction evidence belongs to
the Accounting owner; do not reinterpret that test PASS as an automatic
production install/cutover. The one-time SQLite source importer is retired:
no historical SQLite row backfill is required. Capital's old SQLite ledger,
its differential-only tests and historical smoke are retired. Current
physical Accounting tests run against disposable PostgreSQL and check the
same domain contract directly. TigerBeetle remains a candidate, not
canonical Capital Accounting.

Neither internal accounting substrate proves exchange settlement, legal
ownership, withdrawability or venue trade reality. Reconciliation still
distinguishes unknown effect (`NO_MUTATION`), authoritative proven no-effect
(`VOID_PENDING_TRANSFER`) and **fully reconciled exact-quantity execution**
(`POST_PENDING_TRANSFER`) without resurrecting terminal history. A positive
**partial** execution is PARTIAL_EXECUTION_UNSETTLED -> NO_MUTATION, including
partial-fill-then-cancel: it must not post an entire pending reservation or
void a reservation whose venue effect is positive. Trading retains the
authoritative fill/remaining-quantity evidence until a separately qualified,
amount-aware Accounting consumer exists. Venue trade IDs are deduplicated and
an ambiguous reused client order ID never selects an arbitrary order.
**One-time amount-aware terminal resolution (TigerBeetle two-phase contract).**
The current Accounting PostgreSQL owner accepts a POST_PENDING_TRANSFER with
an exact integer posted_amount in (0, reserved] and atomically removes the
*entire reserved amount* from pending while posting only the observed amount.
The difference becomes available headroom, not an independent phantom credit.
POSTED is terminal even when the posted amount is smaller than reserved:
another POST, VOID, or amount-changing replay cannot post again.
DurableReservationHistory(CONSUMED, posted_amount=...) must match the exact
read-back amount; absent explicit amount means the historical full-post case.
Independent Z3 model obligations and disposable PostgreSQL concurrency
tests cover this bounded invariant, not venue or source authenticity.

Trading still returns PARTIAL_EXECUTION_UNSETTLED / NO_MUTATION for an
incomplete or unauthenticated partial fill. Neither venue qty * price nor
Accounting's accepted numeric posted_amount is financial truth by itself:
only after Trading qualifies terminal fill/fee/currency evidence may an
external effect consumer request a one-time amount-aware resolution. Live
and Demo providers are **not automatically connected to this new authority**.

For installed truth, inspect the actual Accounting owner/Runtime release
and live service rather than inferring it from this architecture page.

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
- authoritative reconciliation to the current qualified Accounting owner, without a SQLite importer or fallback;
- provider restart/recovery identity bindings required by the composition.

The Governance-domain execution-policy enforcement point is src/ordivon_capital/governance/policy_decision.py plus config/execution_policy.json. The source contract is a bounded deterministic policy rule set evaluated by the current owner-native Python toolchain. OPA 1.20.2 is retained only as historical differential evidence under tools/opa_1_20_2.

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

Initial common universe: BTC/USDT and ETH/USDT. OKX Demo and Binance Demo/Testnet are the first future execution environments. Actual live transport is qualified by Network owner observations; a September 2026 VPN exit-path sample is not a standing claim about current provider reachability.

## Source-currentness versus historical experiments

Historical Wave-A generation, Wave-B LEAN mechanics and Nasdaq experiments,
September crypto public/private qualification episodes, and October
Python/SQLite/Parquet rebuild/backup rehearsals were specific executed
SourceCuts. Their original claims and digests remain in Git history, but
they are **not a durable installed-state inventory**. Previously recorded
clock offsets, VPN exits, dependency versions, local registry sizes and
vendor connection results should not be called `CURRENT` without fresh
owner observation.

Current source and consumer entrypoints, in priority order:

- `config/capital_domain_taxonomy.json`: actual seven Python owner packages
  and their exact source patterns, not a proposed `finance/` superpackage.
- `config/external_owner_census.json`: local/external mechanism owner,
  comparative qualifications and retained migration consumers.
- `src/ordivon_capital/` and `scripts/`: importable and executable
  source, not proof of a running customer service.
- `mise run verify` in `domains/capital`: current owner-native software
  acceptance, explicitly separate from effect-provider readback.
- The owner Runtime/Host/Network and actual external providers: exact
  current installed version, live health, source time and external reality.

The current Finance investment/research workflow reuses Portfolio's
no-sale contribution projection and matched-cash-flow passive baseline,
Research's precommitted prospective protocol and byte/source replay,
Markets' source-bearing observations, Risk's measured exposure/tail-risk
calculations and Accounting's exact qualification boundary. The
[Capital owner README](../README.md) routes Human and Agent readers
to the existing first-run task and native Skill guidance.

The continuing constraints are substantive: historical provider truth,
time-of-availability, multiple trials, selection bias, capital suitability,
authoritative broker effects and custody/settlement are not established
by a retrospective paper replay or by this repository.

**Retirement decision:** these superseded progress narratives were
unreferenced as execution/acceptance contracts; retain current source
contracts and observed consumers instead of updating long historical
status paragraphs every time one vendor version or network route changes.
