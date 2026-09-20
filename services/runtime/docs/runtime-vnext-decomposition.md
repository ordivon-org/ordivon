# Runtime vNext decomposition and reassembly

## Goal

Rebuild Runtime from independently justified parts. A part remains only if removing or externalizing it breaks a measured workload, a physical execution invariant, recovery, or evidence quality.

The core ownership boundary remains narrow:

> admitted operation -> controlled physical execution -> durable evidence -> reconciliation

Runtime does not own task semantics, workflow policy, project management, or domain reasoning.

## Reality baseline

The current production trace contains 288,604 observed tool calls in the counted sample. The dominant loop is:

`workspace.open -> workspace.read/mutate -> workspace.exec/execPlan -> job.observe/get -> workspace.close`

| Tool | Calls | Share |
|---|---:|---:|
| workspace.exec | 140,792 | 48.78% |
| job.observe | 37,162 | 12.88% |
| workspace.read | 29,484 | 10.22% |
| workspace.mutate | 15,284 | 5.30% |
| workspace.close | 12,373 | 4.29% |
| workspace.execPlan | 11,740 | 4.07% |
| workspace.get | 11,457 | 3.97% |
| workspace.open | 9,723 | 3.37% |

Those eight operations account for 92.87% of counted calls. Advanced surfaces are real but secondary.

## Parts inventory

| Part | Truth owned | Standing | Direction |
|---|---|---|---|
| Workspace mechanics | Git workspace identity, bounded file mutation/read/diff | KEEP | make independently buildable |
| Runner | physical process execution and bounded output | KEEP | thin physical executor |
| Durable Job/Attempt kernel | admission, reservation, event, terminal state | KEEP | irreducible execution truth |
| Supervisor | process-tree ownership, systemd/cgroup evidence | KEEP | provider-owned mechanism |
| Reconciliation/recovery | ambiguous execution convergence | KEEP | irreducible safety property |
| Provider binding | Linux/Windows/input/host-dependency commitments | KEEP | isolate behind provider boundary |
| MCP transport | authentication, schema, request adaptation | KEEP | thin adapter; no domain truth |
| Structured effects | durable intent + effect-specific receipt + reconciliation | KEEP/EXTEND | generalize carefully from release/patch |
| Doctor/repair | exceptional operator diagnosis and repair | MOVE | operator-tools feature, not production MCP dependency |
| Inspect/experience summaries | operator projections | MOVE/SPLIT | retain job.get core projection; externalize broad analytics |
| lifecycle/status/cache/deploy/reclaim scripts | operator automation | MOVE/REDUCE | stop duplicating Registry semantics/SQL |
| direct Registry SQL in shell/Python helpers | duplicate truth interpretation | REMOVE-CANDIDATE | replace with stable Runtime query/admin API |
| workspace_is_dirty wrapper | duplicate weaker dirty probe | REMOVE | deleted; coverage merged into stronger probe |
| monolithic runtime/tests.rs | test-only coupling across core/operator concerns | SPLIT | core tests vs operator tests |

## Phase 1 changes

1. Corrected the `universal-executor` feature boundary. It previously claimed to be independently buildable but `lib.rs` exported functions only compiled with `transactional-runtime`. The universal-only feature now compiles independently.
2. Added `operator-tools` feature. `doctor` and `repair` are no longer required by the MCP production dependency graph. Default developer builds retain them.
3. Gated Registry administrative repair transaction paths behind `operator-tools` while retaining historical migration compatibility.
4. Physically decomposed the 7,952-line `engine.rs` implementation into responsibility slices without changing the Rust module/privacy boundary:
   - `engine/construction.rs`
   - `engine/admission.rs`
   - `engine/release.rs`
   - `engine/workspace.rs`
   - `engine/execution.rs`
   - `engine/reconciliation.rs`
   - `engine/control_query.rs`
5. Deleted the unused public `workspace_is_dirty` wrapper and its duplicate Git status implementation. Its ignore semantics are now covered by the stronger `workspace_head_and_dirty_at` test.

## Phase 2 changes

1. Physically decomposed `registry.rs` while preserving one SQLite authority and one Rust module/privacy boundary:
   - `registry/storage.rs`
   - `registry/admission.rs`
   - `registry/lifecycle.rs`
   - `registry/query.rs`
   - `registry/reconciliation.rs`
   - `registry/recovery.rs`
2. Physically decomposed inspection into `inspection/job.rs` for the exact Job projection and `inspection/operator.rs` for operator-only read models; cold-history eligibility is further isolated in `inspection/operator/archive.rs`.
3. Added narrow operator projections rather than a second generic Registry API:
   - `registry` for active/held ownership;
   - `registry-workspace` for one Workspace fence;
   - `registry-activity` for batched latest durable activity;
   - `registry-markers` for cache TOCTOU identity;
   - `registry-status` for bounded health/dashboard rows;
   - `registry-archive` for cold-history classification and closure accounting.
4. Removed direct Runtime-Registry SQL from `ordivon-runtime-reclaim`, `deploy`, `lifecycle`, `cache`, `status`, and repository-only `archive`. Their Python remains policy, orchestration, filesystem work, and report presentation rather than a second Registry interpreter.
5. Repository-wide non-test census now leaves SQLite imports only in `scripts/backup.py` and `scripts/restore.py`, where SQLite backup and integrity verification are the physical operation itself. No non-test Python script contains direct semantic queries over Runtime Job/Attempt/reservation/event tables.
6. Corrected test feature boundaries: doctor/repair/broad operator-inspection tests are gated by `operator-tools`, so the lean `transactional-runtime` test target compiles and runs instead of accidentally importing operator-only types.

## Reliability closure after decomposition

1. Current main independently gained fail-closed stale/launch-identity cancellation recovery: cancellation may converge only after the exact target state proves the identity-bound unit, recorded PID identity, and cgroup process tree absent. The operator repair path is scoped to the exact stale target rather than global Registry quiescence.
2. Post-result terminal process-tree evidence is now cgroup-first. When an Attempt has a committed cgroup identity, Runtime checks the recorded PID identity and recursive cgroup-v2 `populated` state directly; a transient `systemctl show` timeout can no longer downgrade a proven-clean terminal process tree to `unknown`.
3. The cgroup-first rule is deliberately limited to terminal evidence after a Runner result. Live execution, cancellation safety, and reconciliation keep the stricter systemd/PID/cgroup identity checks and remain fail-closed.
4. The combined current-main state was exercised through both the complete all-feature Core suite and the explicit privileged local transactional acceptance suite.
5. Post-release `--diagnose` exposed a separate operator-path bound: five sequential `du -sb` storage probes each had an independent 20-second timeout, allowing maintenance diagnostics to exceed a one-minute caller deadline. Storage probes now share a 10-second total budget and each individual probe is capped at 2 seconds; unavailable measurements remain explicit `null` values and raise `STORAGE_MEASUREMENT_UNAVAILABLE` rather than fabricating size truth. On the live store with 375 open Workspaces, the source-matched diagnose path completed in about 26.2 seconds with `health=healthy` and maintenance attention for the intentionally bounded Workspace/storage observations.

## Current evidence

### Operator/Universal cleanup follow-up

- The earlier REMOVE-CANDIDATE for operator scripts directly interpreting Runtime SQLite schema is now **closed as already migrated**: `ordivon-runtime-{archive,cache,deploy,lifecycle,reclaim,status}` contain no direct SQLite/SQL interpretation and use the stable `ordivon-runtime-inspect` projections instead. Remaining non-test SQLite use is storage-native backup/restore integrity work, not Runtime schema semantics.
- `universal-executor` is **retained**. It is the physical Workspace/Runner substrate used by `transactional-runtime`, not a competing execution stack; MCP Workspace and execution tools ultimately depend on it, while the standalone runner intentionally needs only this layer.
- `operator-tools` is no longer part of the Core default feature set. Default Core now means the transactional application core; doctor/inspect/repair remain explicit operator capabilities, while canonical release builds continue to use `--all-features`. Production MCP was already explicitly transactional-only, so this removes build-time/default-surface coupling without changing the MCP contract.
- The MCP adapter's remaining 1,970-line `server/mod.rs` was physically decomposed, without introducing new Rust module/privacy semantics, into same-module include units for tool contract schemas, execution binding, input ingress, server state/configuration, structured tool errors, and tracing. The root file is now 66 lines; existing `handler.rs`, `tools.rs`, and `tests.rs` remain the transport/tool-registration/test owners. MCP 55/55, all-features Core 245/245 (known heavy Registry property skipped), workspace warnings-denied check, Runtime binary tests, and documentation contract all pass after reassembly.
- The 2,681-line physical Workspace substrate was likewise decomposed without changing module/privacy semantics. `universal/workspace.rs` is now a 99-line assembly root plus bounded same-module units for records/lifecycle, file I/O, change/diff projection, source-state identity, close/recovery, and path/Git helpers. Reassembly validation passes universal-only 63/63, default transactional Core 223/223, all-features Core 245/245 (known heavy Registry property skipped), MCP 55/55, Runtime binary/auth tests 4/4, and the warnings-denied workspace check. No new full-build dead-code signal appeared, so this cut is structural decomposition rather than semantic deletion.
- Nine internal helper functions that had no production, binary, integration-test, script, or documentation consumer are no longer re-exported from the crate root. Their implementations remain private implementation detail where transactional Runtime still uses them.
- The obsolete record-first `list_workspace_records` / `list_workspace_record_inventory` path was deleted. Production already uses the stronger current-physical `list_open_workspace_record_inventory` projection; its stale-Workspace unit-test semantics were migrated to that stronger primitive.
- Validation after the cleanup: full workspace check with warnings denied PASS; MCP unit tests 55/55 PASS; default transactional Core unit tests 223/223 PASS; all-features Core unit tests 245/245 PASS; both Core lanes skip only the known heavy Registry property test; universal-only feature still compiles independently.


- `universal-executor` standalone compile: PASS.
- lean `transactional-runtime` compile: PASS.
- lean `transactional-runtime` unit suite: **223/223 PASS**.
- production MCP against lean transactional core compile: PASS.
- default Core smoke excluding the intentionally long reference-model property: **243/243 PASS**.
- complete all-feature Core unit suite, including the long reference-model property: **246/246 PASS**.
- MCP unit suite: **55/55 PASS**.
- Runtime server/auth suite in the all-target workspace run: **4/4 PASS**.
- Python operational suite: **138/138 PASS**, including archive, cache, lifecycle, deploy/reclaim, status, backup/restore, acceptance helpers, and the bounded storage-diagnostics budget law.
- explicit privileged/local transactional Runtime acceptance: **39/39 PASS**, including contained-local isolation, fast success/failure races, interactive close/reconciliation, cancellation reconstruction, provider binding, cgroup budgets, Windows-native execution, and WSL restart recovery.
- source-only archive behavior suite: **7/7 PASS**, including v4/v5 recovery representation, latest-Attempt fallback, fail-closed capability checks, and byte-identical Registry observation.
- non-test Runtime Registry semantic SQL in Python/shell scripts: **0 matches**.
- remaining direct SQLite script owners: `backup.py` and `restore.py` only, for physical backup/integrity operations.

The ordinary all-target run still keeps privileged/systemd/WSL fixtures ignored by default. For this closure, their explicit local opt-in was supplied separately and all 39 privileged transactional fixtures passed; the two evidence classes remain distinct.

## Reassembly target

```text
Agent / caller
    |
    v
Thin MCP adapter
    |
    v
Runtime application core
    |-- Workspace service
    |-- Execution admission
    |-- Observation / cancellation
    |-- Reconciliation
    |-- Structured effect coordinator
    |
    +--> Registry (single durable state authority)
    +--> Runner / Supervisor providers
    +--> OS / Windows / external effect providers

Operator package (separate)
    |-- doctor
    |-- repair
    |-- broad inspection / analytics
    `-- deployment and maintenance automation
```

## Acceptance rule for every later deletion

A component can be deleted only when all are true:

1. no production caller needs its unique semantic contract;
2. its invariant is already owned by another stronger primitive, or it is outside Runtime's ownership boundary;
3. public MCP behavior or an explicitly approved replacement remains available;
4. compile/tests and at least one real workload path pass after removal;
5. recovery/evidence quality is not weakened.

## Next cuts

1. Review the still-large `inspection/operator.rs` by measured responsibility, not file size alone. Split only if status/activity/marker/workspace projections have independent change pressure or compilation ownership; do not manufacture service boundaries for aesthetic symmetry.
2. Keep the repeated `runtime_inspect_binary()`/JSON subprocess adapters in the operator scripts until a shared support artifact is justified by real maintenance cost. Centralizing them today would change the receipt-bound production release set from 12 artifacts to 13, so line-count reduction alone is insufficient evidence.
3. Investigate recurring control-plane `REGISTRY_BUSY` during runner-bind observation and one-second `systemctl show` timeouts as a separate Runtime reliability/performance problem. Terminal evidence no longer depends on the latter when cgroup identity exists, but live supervision/reconciliation still does; these observations must not be conflated with Registry read-model semantics.
4. Revisit compact projection wrappers after MCP DTO ownership is explicit; do not delete them while MCP still consumes them.
5. Before production replacement, run the exact release candidate through the normal deployment/rollback acceptance path and at least one real agent execution workflow. Source-level decomposition success is not deployment truth.
