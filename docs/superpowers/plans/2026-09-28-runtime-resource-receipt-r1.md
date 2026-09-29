# Runtime Resource Receipt R1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or an equivalent task-by-task TDD executor. Steps use checkbox syntax for tracking.

**Goal:** Persist truthful Attempt-scoped CPU, memory, and I/O observations as an optional immutable Runtime Artifact and expose a bounded read-side workload profile path.

**Architecture:** Linux Runner observes its already-owned cgroup-v2 tree and writes a separate `resource-receipt.json`; Runtime validates identity and registers it during normal terminal evidence commit. Analytics remain outside authoritative execution state and consume immutable receipts.

**Tech Stack:** Rust, systemd/cgroup v2, serde JSON, existing Runtime Artifact Registry, Python only for optional read-side aggregation.

**Spec:** `services/runtime/docs/RESOURCE_RECEIPT_R1.md`

## Global Constraints

- Do not extend `RunnerResult` with resource fields.
- Do not create a second scheduler, Job store, Registry, telemetry warehouse, or pricing authority.
- Receipt absence must remain backward-compatible and must not change execution state.
- Receipt presence must be identity-validated and fail closed when malformed or mismatched.
- R1 scope is a terminal pre-result snapshot of the Attempt cgroup, including Runner overhead and descendants observed up to sampling; it does not claim post-sampling Runner teardown accounting.
- GPU, Windows Job Object, energy, and provider pricing are out of the R1 physical receipt.
- Production behavior follows RED 鈫?GREEN 鈫?refactor TDD.

---

### Task 1: Resource receipt value contract and cgroup parsers

**Files:**
- Create: `services/runtime/crates/ordivon-runtime-core/src/universal/resource_receipt.rs`
- Modify: `services/runtime/crates/ordivon-runtime-core/src/universal/mod.rs`
- Test: `services/runtime/crates/ordivon-runtime-core/src/universal/tests.rs`

**Interfaces:**
- Produces `RunnerResourceReceipt`, CPU/memory-event/IO aggregate value structs, and pure parsers for cgroup-v2 text.
- Later Runner collection consumes these parsers and value types.

- [ ] Add literal parser tests for `cpu.stat`, `memory.events(.local)`, and multi-device `io.stat`; include malformed required counters and optional discard counters.
- [ ] Run the focused universal test target and verify RED because receipt parsers/types do not yet exist.
- [ ] Implement the minimal strict parsers and serializable receipt types.
- [ ] Re-run focused tests and verify GREEN.
- [ ] Refactor only after green.

### Task 2: Linux Runner observation and optional receipt emission

**Files:**
- Modify: `services/runtime/crates/ordivon-runtime-core/src/universal/resource_receipt.rs`
- Modify: `services/runtime/crates/ordivon-runtime-core/src/universal/runner.rs`
- Test: `services/runtime/crates/ordivon-runtime-core/src/universal/tests.rs`

**Interfaces:**
- Produces `resource-receipt.json` in the Attempt bundle when cgroup-v2 accounting can be observed.
- Does not alter `RunnerResult` or execution terminal semantics.

- [ ] Add a failing test using a controlled fake cgroup directory to prove aggregation and exact receipt identity/scope.
- [ ] Verify RED.
- [ ] Implement collection from `cpu.stat`, `memory.peak`, optional `memory.swap.peak`, `memory.events.local` with `memory.events` fallback, and `io.stat`.
- [ ] Wire best-effort receipt emission after terminal execution construction and before result commit; collection failure must not replace the execution result.
- [ ] Verify GREEN and mutation-check identity/scope behavior.

### Task 3: Runtime terminal evidence registration

**Files:**
- Modify: `services/runtime/crates/ordivon-runtime-core/src/runtime/evidence.rs`
- Test: `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs`

**Interfaces:**
- Consumes optional `resource-receipt.json`.
- Produces ordinary Artifact registration with `kind=resource_receipt` and `application/json`.

- [ ] Add a failing test proving historical bundles without receipt still prepare terminal evidence.
- [ ] Add a failing test proving a valid receipt is registered.
- [ ] Add failing cases for wrong Job/Attempt/launch-token identity and malformed receipt.
- [ ] Implement optional read, strict deserialize/identity check, digest/length registration.
- [ ] Verify focused tests GREEN.

### Task 4: Real Linux cgroup-v2 acceptance

**Files:**
- Modify: `services/runtime/crates/ordivon-runtime-core/src/runtime/integration_tests.rs`
- Modify if needed: `services/runtime/scripts/local-acceptance`

**Interfaces:**
- Proves the production systemd/cgroup carrier rather than only parser behavior.

- [ ] Add ignored owner-local test that executes CPU work, allocates memory, and performs file I/O.
- [ ] Verify it fails before the Runner emission implementation on the real system path.
- [ ] Run after implementation and assert `resource_receipt` exists, identity matches, CPU usage > 0, memory peak > 0, and I/O counters are physically plausible.
- [ ] Run existing local acceptance to ensure supervision/reconciliation behavior is unchanged.

### Task 5: Bounded WorkloadProfile projection

**Files:**
- Create: `services/runtime/scripts/resource_workload_profile.py`
- Create: `services/runtime/scripts/tests/test_resource_workload_profile.py`
- Modify: `services/runtime/docs/operations.md`

**Interfaces:**
- Consumes a caller-supplied bounded set of receipt JSON files or Artifact export directory.
- Produces deterministic JSON with coverage, count, and P50/P95/P99 for CPU use, memory peak, and I/O totals.
- Does not mutate Registry and does not rank hardware/providers.

- [ ] Write literal-fixture tests first for percentiles, missing optional fields, and deterministic output.
- [ ] Verify RED.
- [ ] Implement minimal standard-library-only aggregator.
- [ ] Verify GREEN.

### Task 6: Documentation, regression and currentness fence

**Files:**
- Modify: `services/runtime/README.md`
- Modify: `services/runtime/CHANGELOG.md`
- Modify: `services/runtime/docs/operations.md`

**Interfaces:**
- Documents receipt scope, non-authority semantics, compatibility behavior, and the boundary to later GPU/Windows/TCO enrichment.

- [ ] Run formatting and focused Rust/Python tests.
- [ ] Run the Runtime portable owner checks available in the current environment.
- [ ] Run real Linux acceptance when the Linux execution owner is available.
- [ ] Inspect exact diff for accidental scope expansion.
- [ ] Recheck canonical main movement before integration; reconcile rather than overwriting concurrent work.