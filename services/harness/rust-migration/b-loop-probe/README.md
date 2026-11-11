# Harness Rust B: source-qualified Loop, Provider, and Tool Surface

## Exact source boundary

This is a **non-production, read-only/pure Rust consumer candidate** on the
single `services/harness/Cargo.toml` workspace. Its starting integration
SourceCut is `6d97f2a08265152a2771addb87877f85e2338c40`, rebased on
protected main `485fbcdc`. A retains the **single** sealed Canonical Core,
PostgreSQL CAS/Journal Reader and eventual PG Writer/Lease/Dispatch Fence.
This crate does not clone their parsers or own physical effects.

Production Python sources used as oracles:

- `ordivon/turn_projection.py`, `ordivon/run_recovery.py`,
  `ordivon/loop.py`: tool selection, evidence and budget-gate decisions
- `ordivon/continuity_records.py`: exact Provider Call Record V4
  validation; `protocol.py`: Provider statuses and failure semantics
- `domain_tools.py`: `DomainToolCatalog.to_dict`, `_select`,
  `_granted_digest`, plus `ordivon/model.py` `AgentToolDefinition`

## Implemented capabilities and verified bounds

- B pure Tool Working Set selector, Evidence state transition, path
  subsumption, progress counters and RunBudget gates. Python 400 selection/
  gate cases + 640 stateful evidence transitions; UNKNOWN cannot create
  observed progress or trigger blind effects.
- `provider_head.rs`: **read-only** Provider v4 record validation and
  recovery posture. Reuses A's borrowed `CanonicalRef`; checks exact 28
  fields, identity/digest/status and result/failure reference constraints.
  `claimed` is not a dispatch grant; `dispatching` and `unknown`
  require authoritative reconciliation, never automatic resend. Result
  digest remains even when result content is privacy-redacted.
- `pg_domain_read.rs::inspect_pg_provider_head`: a real **PG-backed Provider
  record head observation**, strictly through A's existing
  `read_run_readonly` and the new A-owner-reviewed-candidate
  `VerifiedProviderReference` / `VerifiedReferenceLink` read-only getters.
  The same A transaction authenticates CAS bytes, immutable Event/Reference
  edges and the v1/v2 semantic Run Contract. B applies its existing Python
  V4 exact 28-field parser and compares the current Provider Event's record
  digest/status, Run/Adapter/Model identity, timestamp and the exact State,
  Request, Result, Failure CAS edge set. Follows the Python source's
  `_heads` clearing semantics. A syntactically valid v3 record returns
  `UnsupportedV3ProviderRecord`, not a fabricated V4 or corruption.
  `dispatching` and `unknown` retain Provider-owner reconciliation,
  `completed` retains a result SHA even if content is privacy-redacted.
  No Provider FailureReceipt body, AgentTurnResult body, or RunState is yet
  semantically rehydrated; do not claim this is full Provider recovery.
  A test-only Python Store constructs **11** genuine CAS-linked Provider
  Event scenario records in the existing ephemeral PG18 database (no real
  model request): claimed/unknown/redacted completed/cleared and deliberate
  invalid digest/kind/record-vs-event refs/extra edges/status/CAS tampering.
  The Rust readonly consumer must accept the appropriate bounded heads,
  reject bad references and preserve unsupported historical V3 distinct from
  corruption. No second database/PG Writer/Execution Fence.
- Provider v4 numeric identities and timestamps retain Python-valid
  arbitrary-precision canonical decimal text. Numeric comparison is exact,
  not `u64`-bounded. `python_text.rs` captures Python `str.strip()`
  including C0 0x1c–0x1f; this was a verified Rust/Python RED→GREEN case.
  525 native Python v4 source examples (54 accepted, 471 rejected) pass.
- `tool_surface.rs`: immutable Domain-owned Tool Catalog + Grant projection
  into `catalog_digest`, `grant_digest`, **catalog-ordered** model-visible
  definitions. Reuses B's original Tool selection and A's Canonical builder;
  unknown/duplicate/empty grants, mutated catalog or Contract digest
  mismatch fail closed. 224 native Python DomainToolCatalog/Grant source
  examples (128 accepted, 96 rejected) pass. This does not create a global
  Tool registry or authorize tool execution.
- `tool_call.rs`: Model-produced Tool Calls are decoded using the current
  Python `AgentToolCall.from_dict` source grammar, not a new Tool protocol.
  Exact ID/name UTF-8 bounds, arguments object, optional Provider parse
  diagnostics, and Python-normalized Call digest (including all-null
  `providerArguments` omission) are retained. The pure preflight checks
  the frozen Catalog/Grant identity, duplicate ToolCall identity, locally
  rejected malformed Provider arguments, and visibility of the proposed
  Tool; the only positive standing is
  `NeedsAuthenticatedContractAndDurableAdmission` **NOT** dispatch.
  Source oracle invokes Python `AgentToolCall.from_dict` and the actual
  `_GrantedDomainToolBridge` name gate with a no-effect fake executor.
  1,152 source vectors (336 Python-valid, 816 invalid) pass; the four
  distinct standing outcomes all appear.
- `pg_domain_read.rs`: the first real B-native PG consumer of A's verified
  `read_run_readonly` API. From one REPEATABLE READ / READ ONLY snapshot,
  consumes A's versioned semantic `HarnessRunContract` plus Journal/CAS,
  checks independent Provider/Adapter/Model identities, and binds the exact
  `toolCatalogDigest` + `toolGrantDigest` to a caller-provided immutable
  custom `DomainToolCatalog` and approved Tool-name subset. It returns a
  privately constructed `ObservedDomainRun` with a source-bound **observation**
  and pure ToolCall preflight; NOT a fresh Lease, Writer Fence, Effect Intent,
  Tool execution grant, Provider availability result, or capability token.
  This custom mode **does not** qualify the separate no-Tool or Runtime
  Search Run modes.
- The same `pg_domain_read.rs` also supports a distinct **Provider-only,
  zero-Tool Run** via `inspect_pg_no_tool_run`. It reuses exactly the same
  A-owned PG reader, v1/v2 Contract gate and Provider/Adapter/Model identity
  checker. It recreates the fixed Python `NO_TOOL_AGENT_SURFACE` and
  `NO_TOOL_AGENT_GRANT` hashes using A's sealed Canonical builder; no opaque
  hardcoded digest and no new registry. The returned private
  `ObservedNoToolRun` has zero model-visible Tool entries and **no Tool
  preflight or execution method**. A mixed no-Tool/Domain Grant, custom Run
  or built-in Runtime Search Run fails closed. This is still only a
  snapshot observation, not an authorized Provider request.
- An opt-in extension to A's existing disposable PG18 runner reuses the same
  private database and Python `PostgresHarnessStore` to create a true
  Contract-bound Domain Tool Run, then invokes Rust `pg_domain_readback`
  through the read-only role. Tests fail closed for mismatched Provider,
  Adapter, Model, tool Catalog/Grant, mutated Catalog, missing Run,
  rejected/duplicate/unavailable model Tool Calls. The source-authoritative
  Python `AgentToolCall.to_dict()/digest` in this same actual PG fixture
  replaces hand-authored Rust Tool Call JSON (independent reviewer patch
  `0bb43f` reused by cherry-pick). Three additional real Python Contracts
  exercise no-Tool, mixed Grant and built-in Runtime Search surfaces;
  Rust accepts only the exact no-Tool pair and still rejects all 24
  independent CAS-consistent but semantically invalid Run Contracts in
  both custom and no-Tool consumer paths. No second PG bootstrap script,
  no raw database writer in B, and no physical Tool effects.
- Whole-root Cargo fmt/test/clippy -D warnings pass. The A PG Reader's
  separate disposable PostgreSQL 18.6 integration verifies Python-writer
  → Rust SELECT-only readback and five real normal/corruption/legacy cases.
  That **does not** mean this B crate has a PG writer.

## Commands

Run from `services/harness`:

```sh
cargo fmt --all --check
cargo test --locked --offline --workspace --all-targets
cargo clippy --locked --offline --workspace --all-targets -- -D warnings
bash crates/harness-pg/tests/run_isolated_pg18.sh
# Extended actual PostgreSQL consumer boundary and Contract adversarial cases:
cd ../..
HARNESS_B_BOUND_PG_DOMAIN=1 HARNESS_CONSUMER_FALSIFY_CONTRACT=1 \
  bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh
```

The Python source-oracle tests use `uv run --offline --locked python` from
this Harness tree. Do not replace them with hand-copied expected behavior.

## What remains unproven

- This is **not** an installed Rust Agent Run, PG writer, Provider transport,
  Runtime Tool executor, or independently accepted production cutover.
- PG-bound custom Tool inspection does not check dynamic capability permissions,
  adapter availability, Provider model response, RunBudget composition, or
  external Effect admission; those require separate owner-native consumer gates.
- Actual Context→Model, persistent Model→Tool Intent→Runtime and Receipt/UNKNOWN→
  WorkingView consumers, cancellation, recovery of old Run v3, authorized
  privacy handling and live Writer/Lease/Fence are separate gates.
- The B pure progress-gate `u64` representation still rejects overflow
  explicitly; its Contract budget range is not equivalent to arbitrary
  Python integers. Provider-v4 large-int parity does not cure this separate
  Contract boundary.
- A's legacy PG Reader may classify hash-verified, Python-legal deep CAS as
  UnsupportedLegacyRepresentation; this must never be treated as proven
  corruption, false effect or a safe replay.
- **Historical P0 Contract semantic counterexample is now regression-guarded**:
  on the older Rust Reader a CAS-consistent, Python-invalid Contract was
  incorrectly accepted. A's newer full versioned v1/v2 Contract semantic
  validator now rejects all 24 independent negative PG cases and accepts
  10 true Python-valid Run Contracts, including from both B custom/no-Tool
  consumers in this opt-in scratch-PG test. This bounded corpus is **not**
  proof of all historical domain representations or executable standing.
- The model preflight returns only `NeedsAuthenticatedContractAndDurableAdmission`.
  It cannot create a durable ToolStepIntent, validate a complete Run Contract,
  send a Runtime tool, or reconcile an uncertain physical effect.
- The Python DomainToolCatalog is for **custom domain bridges** only;
  Provider-only no-Tool is separately qualified for read-only observation;
  built-in Runtime Search remains a distinct composition requiring the
  real HarnessExecutionBinding and Runtime Client. Neither path gains
  physical Provider/Tool admission from these read-only consumers.

Independent C consumer adversarial review is still required before PR/main
promotion. Keep the one Host Space/Topic/Work and one A PG authority.

## One authoritative PG Journal / Provider recovery SourceCut (integration)

The A PG Writer/Lease contribution and B Provider/Tool/Agent-loop consumers
are integrated **in one three-crate Cargo workspace** without changing the
Python v1 PostgreSQL schema or introducing a second Store. A's single
`read_run_readonly` owns Contract/CAS/Journal verification; the shared
`VerifiedReferenceLink {event_id,digest,kind,byte_length}` and the narrowly
exposed `VerifiedProviderReference` project already verified CAS references.
A's `append_events` owns the atomic Journal transaction and exact Run Lease
fence; B derives only read-only Provider/Model/Tool observations.

Test the **same scratch PG18 database** with all known consumers enabled,
from repository root:

```sh
HARNESS_CONSUMER_FALSIFY_CONTRACT=1 \
HARNESS_PG_NATIVE_LEASE=1 \
HARNESS_PG_NATIVE_WRITER=1 \
HARNESS_B_BOUND_PG_DOMAIN=1 \
bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh
```

New cross-language test in `pg_provider_head`:

1. Python `PostgresHarnessStore` creates a legitimate no-Tool Contract and
   Provider V4 Claimed/Dispatching/UNKNOWN CAS objects and FailureReceipt,
   **without appending the three Provider events**.
2. A's native Rust `acquire_run_lease` / `append_events` atomically records
   three Event payloads, reference edges, Run revision and lease consumption
   in one real PG18 transaction. No actual Provider HTTP request occurs.
3. The writer connection is closed. The SELECT-only `observe_exact_batch`
   and `read_run_readonly` confirm the same three events and Run revision 4.
   B `inspect_pg_provider_head` recovers the identical Python V4 UNKNOWN head
   with `RetainUnknownAndReconcile` and exact Provider record SHA digest.
4. A's exact replay returns `Admission::Existing` without duplicate Events;
   altered payload is rejected, and Python `validate_run_history` plus
   `list_run_events` verify the same Run after Rust writes.

The source fixture is in `pg_provider_v4_python_store.py` and reuses the
same existing disposable PG18 test runner. No second cluster, codec, schema
or global Tool catalog is introduced.

**Limits:** `dispatching`/`unknown` Journal states do not prove an external
Provider request was sent. `ExactCommitted` proves only the specific Journal
batch exists. Run snapshot, Run Lease and Journal append are **not** a
durable physical-effect/dispatch permit; they cannot by themselves establish
at-most-once physical effects or replace downstream Receipt/UNKNOWN
reconciliation. A owner and original C-seat must review before production
Rust takeover. Native `create_run`, Provider HTTP and old v3 compatibility
remain open separate gates.

## Source-qualified Tool Intent/Fence/Receipt recovery — R17 (source-only)

Current pg_tool_head is the read-only semantic consumer of A's ONE
read_run_readonly PostgreSQL Run/Contract/Event/CAS snapshot. It is not
a Tool executor and cannot construct an Owner Dispatch Permit.

Python's production EventSourcedRunContinuity.prepare_tool_step stores
Intent V1, Fence V2, Snapshot, State and Event references. The narrow A PG
projection exposes only already SHA/kind-validated typed Intent/Fence/Receipt
CAS values plus a whitelist of Snapshot authority identity fields and an
exact source-field-set witness. Raw State, private Snapshot fields, Tool
Observation and result contents are not exposed. B reuses mature Serde typed
decoding with source-exact schemas and validates RunContract/assignment,
full Event edge set, active Intent in Snapshot, Run/Fence revisions, and
Receipt provenance/status.

Returned standings are deliberately non-executable: PreparedNeedsOwnerAdmission,
UnknownRequiresOwnerReconciliation, PendingCancellationRequiresOwnerReconciliation,
ReceiptObservedNoRedispatch. prepared_revision_is_current() is only a
historical readback comparison; it never grants physical dispatch.
Runtime currentness, idempotent Owner admission, actual receipts and
external UNKNOWN reconciliation are not yet source-qualified in Rust.

Real Python Producer => disposable PostgreSQL18 => A Rust PG reader =>
B typed Tool Head, same existing A/B test runner:

    HARNESS_CONSUMER_FALSIFY_CONTRACT=1 \
    HARNESS_WRITER_CONTRACT_FALSIFY=1 \
    HARNESS_PG_NATIVE_LEASE=1 \
    HARNESS_PG_NATIVE_WRITER=1 \
    HARNESS_B_BOUND_PG_DOMAIN=1 \
    HARNESS_B_TYPED_TOOL_HEAD=1 \
    bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh

Nine source cases: prepared; privacy-redacted UNKNOWN; stale Run revision;
generic Event with no Intent; stolen cross-Run CAS; forged Fence digest;
extra CAS edge; UNKNOWN Receipt disguised as recorded Event; and a
digest-valid but semantically invalid Snapshot that lacks the active Intent.
The last failed before the Snapshot active-binding fix (real RED), then
passed (real GREEN). No Provider HTTP or physical Runtime Tool request.

Original C, A PG Owner and B Tool Owner must review before promoting source.
