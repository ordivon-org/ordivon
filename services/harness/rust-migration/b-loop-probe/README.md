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
```

The Python source-oracle tests use `uv run --offline --locked python` from
this Harness tree. Do not replace them with hand-copied expected behavior.

## What remains unproven

- This is **not** an installed Rust Agent Run, PG writer, Provider transport,
  Runtime Tool executor, or independently accepted production cutover.
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
- **P0 independent semantic counterexample**: the current Rust
  `harness-pg.read_run_readonly` can accept a digest-consistent Run with a
  Python-invalid `HarnessRunContract` (e.g. empty `providerId`).
  A complete versioned Contract validator, including Python-valid historical
  cases, must pass before any of B's digest/Tool/Provider projections become
  consumer authority. Independent reviewer supplied 24 invalid / 10 valid
  scratch-PG tests; normal PG and CI green do not waive this block.
- The model preflight returns only `NeedsAuthenticatedContractAndDurableAdmission`.
  It cannot create a durable ToolStepIntent, validate a complete Run Contract,
  send a Runtime tool, or reconcile an uncertain physical effect.
- The Python DomainToolCatalog is for **custom domain bridges** only;
  no-Tool and built-in Runtime-search surfaces retain their separate Python
  Run Contract composition rules and are not implicitly granted here.

Independent C consumer adversarial review is still required before PR/main
promotion. Keep the one Host Space/Topic/Work and one A PG authority.
