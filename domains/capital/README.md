# Ordivon Capital — Composition First

Ordivon Capital is the capital composition and control plane of Ordivon. It does not define a new accounting, risk, trading, settlement, identity, observability, lineage, or cloud-cost framework. It composes authoritative standards, mature implementations, provider reality, and the minimum Ordivon glue required to bind evidence, authority, execution, and reconciliation.

**Market Capital is one implemented domain inside Ordivon Capital, not the parent system.** The current repository contains the Market domain plus a cross-domain TigerBeetle accounting integration. Treasury, Compute, Enterprise, Human, Distribution, and other capital domains are not instantiated until a real use case requires them and an external-owner census has been completed.

Current Market-domain business backbone: CFA investment-management process.
Trading semantics: FIX.
Trading runtime: pinned QuantConnect LEAN (installed and admitted for bounded non-live Wave B execution).
Post-trade reference semantics: PFMI + ISO 20022; broker/custodian infrastructure remains authoritative.
Research/data persistence: Pandera + Parquet/PyArrow + DuckDB + MLflow, with MLflow tracking configuration owned by the caller/environment.
Historical issuer/reference inputs (GLEIF/SEC/Arelle) belong to the retired Wave-A generation slice and are not active Capital capabilities.
Capital accounting mechanics: TigerBeetle `0.17.9`; venue/custody/settlement systems remain authoritative for their own external state.

## Current standing

The historical Wave-A generation pipeline is retired. Its frozen `wave_b/fixtures/wave_a_target_portfolio.json` remains an immutable regression/execution-mechanics input for Wave B; Capital no longer carries the GLEIF/SEC/Cboe/equal-weight generator that produced it.

Wave B / M1 admits bounded historical execution through pinned QuantConnect LEAN. M2 adds LEAN-native pre-trade feasibility. M3 uses provenance-recorded Nasdaq historical OHLCV only for execution-mechanics/data-plumbing validation. M4 projects order intent through a legacy FIX 4.4 wire profile under the FIX Latest semantic reference. M5 is prospective validation: a frozen decision may be evaluated only against strictly post-decision aligned holdout sessions; this is not causal evidence. M6 freezes a pre-market shadow plan. Every current execution runner crosses the OPA-governed execution-policy enforcement point before LEAN starts. No live financial-write path is implemented. NautilusTrader `2.0.0rc4` remains qualification-only.

This repository does not import legacy Ordivon finance/Market Capital code or schemas.

The active public-data venue qualification path is **OKX + Binance Spot** through exact Network v2 authorities. Network v2/sing-box owns provider A/B transport and failover; the Ordivon Capital Market domain consumes only destination-fenced loopback authorities. The lane remains public-data-only and credential-free, separate from the historical equity M6/M7 experiment.

Crypto Public Shadow R1 now binds concurrent OKX/Binance public REST capture to exact Network v2 authorities. The latest migration rerun completed one coherent capture round, but the scientific standing remained `PARTIAL_PUBLIC_CAPTURE_NO_CROSS_VENUE_CLAIM` because venue-clock agreement was ~294.6 ms against the frozen 250 ms gate; the gate was not relaxed. Private/demo/live writes remain independently blocked by NON_LIVE execution authority.

Crypto Shadow Mechanics R1 also passes local multi-currency Spot OMS mechanics for OKX/Binance using venue-owned tick/step precision; it remains explicitly non-economic and non-live.

Crypto data transport is now venue-specific: OKX uses the qualified Nautilus native public client, while Binance uses its official credential-free REST/WebSocket boundary because Nautilus 2.0.0rc4 still times out during native data-client startup.

**Public-data adapter policy LEGO** (capital.markets.crypto-public-data-admission):
Capital owns one responsibility—reject nonpublic or execution-capable adapter
configuration. Input: config/crypto_data_adapters.json; output: a successful
bounded public-data policy receipt or nonzero rejection. Contract: PUBLIC_DATA_ONLY,
credential-free OKX/Binance primary paths, no venue execution client, and no Binance
SBE credential workaround. Actual consumers: scripts/run-crypto-public-shadow-r2
and scripts/run-crypto-stream-resilience-r3. Acceptance:
tests/test_crypto_data_adapters.py injects forbidden credential/execution flags
into an isolated configuration and requires rejection under ordinary and optimized
Python, then mise run verify checks the owner suite. This does not authorize
private account access, trading or external financial effects.

**Crypto Public Shadow Product Acceptance LEGO** (`capital.market.crypto-public-shadow-consumer`):
The natural owner is `scripts/consume_crypto_public_shadow_product_r1.py`.
Input: frozen ODPS product, SHA-256-bound public observation and ODRL rights policy.
Output: read-only decision/feedback receipt plus OpenLineage events, **only after**
all twelve source, privacy, execution, timing and rights conditions hold.
A false condition must emit no PASS receipt under normal or `python -O` execution.
The existing consumer acceptance test
`tests/test_data_product_consumption_crypto_public_shadow.py`
falsifies source-digest, broker-credential, private-account, financial-write and
rights-policy mutations in an isolated temp fixture. The gate never grants
execution authority, trading rights, redistribution or financial effects.

Crypto Public Shadow R2 now passes repeated persistent public streaming through exact Network v2 WS authorities using the mature `websockets` client proxy support. OKX `bbo-tbt` plus Binance market-data-only `@ticker` produced one warm-up and three measured coherent snapshots; all measured source/receive spans remained below the frozen 1200 ms limits. Provider selection is owned by Network v2 `provider-auto`, not by an application-level node/protocol matrix.

Crypto Stream Resilience R3 keeps fail-closed missing/stale/time-divergence semantics and the dual-venue reconnect harness on exact Network v2 WS authorities. Current injected-disconnect qualification passes for both OKX and Binance; observed reconnect latencies were ~16.0 s and ~26.3 s respectively and remain evidence rather than a hidden transport claim. The state is exported through the existing Prometheus/Grafana stack without enabling private/demo/live execution.
Clock timing qualification now passes: Windows w32time is synchronized to qualified public NTP peers and WSL CLOCK_REALTIME follows the Windows host through `/dev/ptp_hyperv` using `phc2sys`; fresh external validation observed <=47.1 ms absolute error versus the frozen 1000 ms gate. Overall private/demo/live execution remains blocked by the separate NON_LIVE execution authority.

Composition policy: prefer authoritative standards, mature implementations, and provider-native truth over local mechanisms. ISO/FIX/ISO 20022 and workload-applicable external identity/reporting standards define semantics where needed; LEAN/Nautilus/venue APIs/TigerBeetle/OPA/MLflow/Pandera/Parquet/DuckDB/OpenLineage/OTel/Prometheus own their respective mechanics. Ordivon Capital retains only narrow composition, policy-input/enforcement, evidence, data-quality, and reconciliation seams that no natural owner can establish alone. Custom mechanisms require a demonstrated substitution failure. Machine-readable ownership is tracked in `config/external_owner_census.json`; see `docs/COMPOSITION_FIRST_2026-09-14.md`.

**CAP-DB-TYPE-01 — PostgreSQL-first type/representation contract.**
The database-neutral Accounting Substrate owns exactly one identity for
LedgerApplyStatus, AccountState and TransferState, consumed by the
PostgreSQL-first ledger and by legacy historical import tests. The PostgreSQL
runtime must import successfully when importing sqlite_ledger is forbidden.
The existing native negative test
tests/test_accounting_substrate_type_authority.py proves both this isolation
and identical enum/data type identities across consumers. These types are
an existing Thought LEGO (domain law) used by a Capability LEGO (native
PostgreSQL accounting). The old SQLite data path gains no new features and
remains a retirement target once real migration/replay consumers are qualified.

**Typed accounting-operation LEGO** (capital.accounting.typed-operation): existing
AccountingInstruction and resolution_instruction own the enum boundary.
Inputs must use AccountingOperation members, never raw strings or unknown values;
a raw VOID cannot bypass its zero-amount invariant. Consumers are the existing
reservation/POST/VOID construction paths, with executable negative evidence in
tests/test_accounting_substrate.py and owner acceptance via mise run verify.
This is a local accounting contract, not a live financial-write authority.

TigerBeetle Capital Substrate R1 passes the base mechanical integration and R3.1 composes Reservation -> PENDING, RETAIN -> no mutation, RELEASE -> VOID_PENDING_TRANSFER, and CONSUME -> POST_PENDING_TRANSFER. R3.2 now passes durable restart/reconciliation on one intact data file: a pending reservation survived the first process restart, a consumed reservation survived the second, exact replay returned `EXISTS` without reopening pending state, and exact terminal semantic history reconciled `MATCH`. If provider terminal history is missing or stale, the result is retain/recovery (`PROVIDER_INCOMPLETE_RETAIN` / `CONTRADICTION_RETAIN`) with provider repair forbidden; terminal Capital accounting history is never resurrected from provider state. The bounded harness deletes its data file afterward, so no long-running canonical ledger or external financial write is admitted.

**CAP-PG-SOURCE-TYPE-01 — PostgreSQL migration source fidelity:** SQLite
INTEGER affinity is not a proof that stored source cells are integers. Before
producing a migration digest or admitting a PostgreSQL write, the PG importer
requires an exact integer type for every account balance and transfer amount,
and an exact {0,1} integer for the overdraft flag; it rejects REAL, TEXT,
boolean aliases and out-of-range values rather than silently truncating or
coercing them. Consumer acceptance is a real PostgreSQL 18 native negative
test with malformed disposable source rows and an empty PG target after
failure. This is a PostgreSQL-import contract, not a new SQLite repair or a
claim that source-writer retirement has been completed.

**CAP-DB-MW-01 (TYPE + NATURAL_KEY + SERIALIZATION):** before the
PostgreSQL-first accounting cutover, two independent SQLite callers must not
treat an absent-ID read as exclusive admission. The narrow interim ledger
uses SQL INSERT ON CONFLICT DO NOTHING RETURNING for Account admission,
and places Transfer replay/readback inside BEGIN IMMEDIATE together with
the only permitted balance effects. Native two-connection interleaving
tests force same-ID replay and conflicting amounts and assert typed
CREATED/EXISTS/ID_CONFLICT with a single balance mutation; the original
implementation failed with a raw sqlite3.IntegrityError for both Account
and Transfer creation. This protects existing non-live consumers, not
a justification for retaining SQLite after PostgreSQL achieves parity.
The PostgreSQL cutover still requires exact u128 account identity,
atomic concurrent no-overdraft / pending POST or VOID, restart/replay
equivalence, live data inventory and an independently verified migration
and rollback SourceCut. No external funds or trading authority is implied.

**SQLite accounting smoke verification LEGO**: the existing disposable
SQLite scripts run-sqlite-accounting-durable-restart-smoke-r1 and
run-nonlive-capital-effect-matrix own one responsibility: prove local
state transitions, durable reopen, reconciliation and exact replay before
issuing a PASS receipt. Inputs are synthetic accounting instructions and
a disposable SQLite file; outputs are the existing JSON receipts.
Consumers are scripts/run-r0-r5-closure and
scripts/run-capital-trading-fullpath-closure respectively.
Necessary writes and checks execute identically with ordinary Python
and python -O. The native tests/test_accounting_smoke_optimizer_contract.py
verifies actual entrypoint equivalence and distinct pending/consume
observables. No live funds or provider write authority is used.

Crypto FIX Projection R4 now passes: the four already-qualified Nautilus mechanics-only Spot orders project through sessionless QuickFIX/n FIX 4.4 `NewOrderSingle` semantics with ClientOrderId→ClOrdID identity continuity, venue `ExDestination`, Market order type and IOC TIF. No credential, FIX session, private account read or external financial write is admitted.

Private Reality read-only preflight now passes without credentials: OKX will use the installed NautilusTrader `OKXHttpClient`; Binance will use the first-party `binance-sdk-spot 11.3.0`. Required account/order/trade query surfaces are present, but credential use remains `NOT_ADMITTED`, secret discovery is forbidden, and TRADE/Withdraw remain blocked.

Private Reality R5 offline normalization now passes: authoritative OKX/Binance observer envelopes map through a pure no-network/no-credential normalizer into a minimal balances/positions/orders/fills read model. Existing observer credential locations are bound externally, Binance executor credentials are explicitly excluded, and private account data remains blocked pending fresh permission verification.

Execution Reconciliation R6 now passes offline: authoritative normalized venue reality is mapped into FIX 4.4 execution lifecycle vocabulary, and reconciled directly to TigerBeetle accounting-resolution instructions. Broad snapshot absence is never treated as no-effect; voiding a pending transfer requires terminal zero-fill with complete fill coverage or an exact authoritative negative lookup.

Demo/Testnet Execution R7 preflight is prepared but not admitted: the installed NautilusTrader execution configs construct successfully for OKX DEMO and Binance Spot TESTNET without credentials or network access. Demo/live write authority remains false.

Live endpoint test-account policy is now explicit: the user authorizes the existing OKX/Binance LIVE endpoints for non-production qualification, but they remain semantically LIVE. Fresh authoritative account reality must prove an effectively empty account (no positions/open orders/nonquote balances and <=1 quote unit), trade-only authority, clock health and reconciliation health before order submission can be enabled.

## Finance factor LEGO — current consumer boundary

The current Market Capital research/risk consumer is **descriptive**, not a new
factor-model framework. A factor label, factor exposure, proxy correlation, alpha
forecast, strategy target and broker order are **different responsibilities**.

| Existing LEGO consumer | Actual implementation | Contract |
| --- | --- | --- |
| Factor proxy measurement | `risk/portfolio_risk.py::build_factor_observatory` | Explicit market-proxy histories; dependence evidence is not causal alpha |
| Portfolio factor exposure | `risk/portfolio_risk.py::build_exposure_ledger` | Caller-supplied loadings; overlapping exposure is not additive risk contribution |
| Risk budget and report | `risk/portfolio_risk.py::build_portfolio_risk_report` | `UNSET` stays incomplete, never inferred |
| Portfolio alternatives | `portfolio/portfolio_counterfactuals.py` | Explicit what-if mechanics, not trade ranking or authorization |
| Execution | Current Capital Governance / Trading authorities | `NON_LIVE`; no financial-write effect from factor observations |

An older experimental decision-state/atlas circuit exists in historical branches
but **is not a protected-main consumer**. Do not resurrect it merely to satisfy
a factor test. Use an external academic factor definition or qualified LEAN
implementation when a real strategy consumer demands it; qualify its data cut,
source, signal meaning, costs and forward evidence before promoting it.

Golden Path (no provider account, synthetic data, no order):
`mise run //domains/capital:verify`, including
`tests/test_factor_lego_consumer_contract.py`. This only demonstrates current
mechanical consumer boundaries; it is not evidence of positive investment Edge.

## Non-live and private-read admission LEGO

The existing Capital policy-checker LEGO uses these three Owner scripts:
- scripts/check-demo-execution-preflight
- scripts/check-nonlive-credential-provisioning
- scripts/check-private-reality-readonly-preflight

Their actual consumers are scripts/run-capital-trading-fullpath-closure
and scripts/run-r0-r5-closure. Their contracts are unchanged: no
live/external writes, unauthorized demo/testnet order submission or
private-account access, and no group/world-readable credential files.
An invalid policy or file permission must produce a nonzero exit under
both normal Python and optimized Python. The native falsifier is
tests/test_nonlive_policy_optimized_contract.py with isolated synthetic
JSON and dummy files. This mechanical boundary does not authorize live
financial effects or prove external provider behavior.

The same Owner contract also covers scripts/check-nonlive-effect-authority,
scripts/check-private-reality-credential-bindings, and
scripts/check-clock-quality-gate. Consumers include non-live effect
reconciliation, R0-R5 private-read binding, and public shadow/stream
resilience clock qualification. In addition to optimization independence,
the bindings checker must reject forbidden private-account, trading or
external-write flags even in ordinary Python; credential file modes and
clock-forgery declarations are negative-tested with synthetic fixtures.
No provider resources or live effects are admitted by this proof.

## Verification boundary

Required repository CI is hermetic and authority-free. The capital:verify task runs the
Capital source suite with provider_qualification tests excluded. Tests carrying that
marker require node-local external-owner runtimes, exact candidate binaries, or
credential bindings and therefore are not evidence that a clean GitHub runner can or
should reproduce provider reality.

Run those separately on a qualified local node with:

    mise run //domains/capital:verify:provider

The split does not weaken the provider gates: provider-bound tests remain tracked and
must pass in the environment that actually owns the required external evidence. It
prevents local credentials, /root candidate environments, or /opt provider binaries
from becoming hidden prerequisites of repository CI.


**PostgreSQL-first accounting capability (native consumer transition)**.
The bounded accounting API can now use PostgresAccountingLedger with an
explicit PostgreSQL DSN; no SQLite fallback is permitted if a PG DSN was
selected. scripts/run-nonlive-capital-effect-matrix selects this backend
when ORDIVON_CAPITAL_PG_DSN is supplied. Without a PG DSN it FAILS CLOSED;
historical disposable SQLite regression tests require the explicit
ORDIVON_CAPITAL_LEGACY_OFFLINE_SMOKE=1 test-only opt-in. The PG implementation
uses a transaction-scoped schema-admission lock, PostgreSQL SERIALIZABLE
transactions with whole-transaction retry, unique account/transfer identities,
atomic no-overdraft and pending POST/VOID effects, and native restart/replay
readback. Physical PostgreSQL consumer tests are in tests/test_postgres_ledger.py;
they require ORDIVON_CAPITAL_PG_TEST_DSN pointing at a disposable
database, with no production-credential defaults. Existing SQLite is an
historical migration-source/debt item and must not be extended.

PostgresAccountingLedger.import_quiesced_sqlite performs a read-only
snapshot and pre-commit exact PG readback into an empty target. It refuses to
start without explicit independent legacy-producer quiescence; it never edits,
locks out, or silently deletes the old authority. The receipt says
VERIFIED_COPY_NOT_CONSUMER_CUTOVER. Installed worker shutdown, deployed PG
DSN, rollback and final retirement are separate unsatisfied gates; passing
a disposable test is not production migration. No external financial write
authority follows from PG accounting.
