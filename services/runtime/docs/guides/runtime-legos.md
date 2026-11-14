---
schema_version: 1
id: runtime.lego-guide
title: Runtime LEGO Capability and Reasoning Guide
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-runtime
audience:
  - user
  - builder
  - operator
  - agent
updated: 2026-11-07
summary: Owner-native index of Runtime capability and reasoning LEGOs, with Human and Agent consumption paths.
evidence_status: observed
readiness: READY
applies_to:
  - ordivon-runtime
related:
  - runtime.model
  - runtime.operations
---
# Runtime LEGOs — Capability and Reasoning Guide

## Scope

This guide is a **consumer index**, not a second tool catalog or a new execution framework. Authoritative tools are discovered from the connected Runtime node, source truth comes from the specific Git revision, and physical results come from a Job/Attempt and provider evidence. The existing planning graph is [planning/lego-plan-r1.json](../../planning/lego-plan-r1.json); conceptual foundations are [Runtime Research](../../research/README.md).

A LEGO is described by `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`: inputs/outputs, owned state, pre/postconditions, invariant, possible effects, cost/capacity, uncertainty, provenance, and decomposition. Each entry must distinguish **specification**, **model/validator**, and **installed implementation**. The implementation and physical model are not proven equivalent merely because they share a name.

## Workspace lifecycle and current stock audit

The existing WorkspaceConsumerCloseR1 TLA models and native Runtime provider
remain unchanged. Current stock-only source audit, refactor decisions and
recorded evidence are in the repository-root path `docs/architecture/audits/2026-11-10-brownfield/AUDIT_SCOPE.md`.
Earlier consumer-expansion plans are historical and do not authorize new
runtime features, tests or interfaces.

## Capability LEGOs — current native consumers

| Capability | Source / actual owner | Preconditions and observable postcondition | Mature substrate / evidence |
| --- | --- | --- | --- |
| Git Workspace identity | `universal/workspace/`, `runtime/pg_runtime/workspace.rs` | Exact source revision and workspace identity → observed source-state digest and a fenced working tree; close must reject active/held consumers | Git worktree, source-state readback |
| PG Job admission / replay | `pg_admission.rs`, `pg_dispatch.rs`, `runtime/pg_runtime/job.rs` | Qualified PG writer epoch, authenticated principal, exact operation identity → committed Job or exact replay; never create a duplicate because reply delivery was lost | PostgreSQL transaction and durable query |
| Native physical execution | `universal/runner.rs`, `execution_provider.rs`, `platform/windows/` | Admitted Job, committed provider identity → observed Attempt or explicit ambiguity | systemd/cgroup (Linux), SCM/Job Object (Windows) |
| Reconciliation / cancellation | `runtime/pg_runtime.rs`, `runtime/supervisor.rs` | Persisted Job plus live provider evidence → justified terminal state or UNKNOWN; cancellation intent is not proof the process stopped | identity-bound process evidence |
| Artifact observation | `runtime/pg_runtime/artifact.rs`, `universal/resource_receipt.rs` | Existing registered Artifact/digest → bounded verified read; target success is not task completion | SHA-256, owned receipt |
| Runtime release | `runtime/engine/release.rs`, release tools when configured | Qualified candidate manifest and deploy authority → external deployment receipt, not inferred binary exit | existing receipted release path |
| Operator retention | `scripts/ordivon-runtime-lifecycle`, `scripts/ordivon-runtime-reclaim` | Complete ownership and absence of current/held consumers → selective Workspace/cache retirement | Git worktree removal, systemd native directory lifetime |

### Source layout of the PG implementation

`runtime/pg_runtime.rs` owns PG configuration and writer qualification. Its submodules separate `node_query.rs` (discovery/list), `workspace.rs` (Workspace operations), `job.rs` (admission/observe/cancel/get), `reconciliation.rs` (Attempt readback, OS reconciliation and result projection), `native_stop.rs` (pure kernel-evidence admission classifier with Kani proof harness), and `artifact.rs` (Artifact projection). Runtime errors use `runtime/error/universal.rs` for executor-to-domain mapping, while `runtime/error/sqlite.rs` is a gated **legacy** Registry adapter. PostgreSQL clients must use the neutral error mapper rather than importing the legacy Engine. These are source-level structure improvements, **not a PG-only Cargo dependency graph**: `postgres-runtime` still transitively enables `rusqlite`, and Windows PG-native execution is not yet qualified.

## Reasoning LEGOs — reusable human/agent decisions

| Thought LEGO | Invariant or falsifier | Avoid |
| --- | --- | --- |
| Truth-owner decomposition | Each mutable fact has one responsible writer; projections never silently become writers | Two state ledgers for one Job |
| Effect ambiguity | A lost response or missing Result cannot prove failure, absence, or successful external effects | Blind retry with a new ID |
| Representation refinement | New models/contracts must preserve externally observed behavior and error standing; counterexample closes the claim | Calling a structural rename a verified equivalence |
| Source identity vs environment | Git commit and dirty-tree digest do not prove frozen clock, network responses, target mount view, or all host dependencies | Claiming a complete execution snapshot |
| Capacity and resource evidence | Use observed bounded execution limits and receipts; treat missing measurement as unknown | Invented resource accounting |
| Consumer-reachable retirement | Delete only exact owner state for which current and scheduled consumers have been checked | Deleting by age, glob, name, or repository history alone |

## Agent execution consumer bridge (source candidate 2026-11-13)

The direct Runtime consumer is an Agent/Harness physical execution terminal;
Research, Finance, and publication are downstream payloads, never Runtime
semantic lifecycle authorities. The complete path is Agent Run -> fixed
Workspace grant -> Gateway execution.submit/get -> Runtime PG Job/Attempt
-> owner-confirmed Artifact -> Harness result -> separately verified
consumer relinquishment -> Runtime fenced close.

A Runtime Job reaching a terminal state is not proof of Agent Run completion.
Gateway execution.resolve already returns an exact Runtime job.list
clientRequestId / jobId / workspaceId binding. Harness now reuses this
existing projection after each terminal execution.get: wrong Workspace
rejects, absent request binding remains reconciliation_required instead
of resultAvailable=true. The frozen public Gateway MCP schema stays intact.
No new public tool, duplicate Run Registry, or GC was introduced.
The source-only bounded GatewayAgentWorkspaceBindingR1 finite model lives
under services/gateway/formal; exact source tests and a live PG owner observation
are evidence for this narrow consumer link, NOT deployed refinement.

**Physical negative consumer (2026-11-14).** A disposable, same-Workspace
two-logical-Agent Gateway/PG trial showed both Job results can finish while
one Agent still intends another command. A single consumerReleased=true
assertion removes the clean idle Workspace and the second Agent's subsequent
command fails. This is the explicitly admitted single-caller assumption of
Runtime Close, not a broken PG lock or evidence that another real Agent was
affected. The separate formal WorkspaceMultiAgentReleaseR1.tla models the
multi-consumer requirement; model status only. A safe implementation needs
a durable owner-registered consumer set or provably exclusive scope and
bounded revoked/expired claims, without a transaction spanning model thinking.

Still unimplemented P0: a real Agent Run's long-lived Workspace ownership,
durable outcome handoff, exact relinquishment evidence, and Gateway-issued
native Workspace close. The current Runtime consumerReleased flag is only a
caller assertion and the four-hour hold cannot prove an active Agent finished.

## Human usage

For normal operator work, identify the endpoint and actual installed backend, inspect `runtime.describe`, `workspace.list`, `job.list`, and read the installed service/receipt. For physical execution use the established tool and then inspect its Job and Artifact. For maintenance, classify the exact state root as *active*, *quarantined/unknown*, or *consumer-free*. Prefer `git worktree remove` for worktree lifecycle and native systemd directory policy for service-managed directories. Use the existing release and rollback mechanism; never rename a live service to make the architecture diagram cleaner.

For code changes, use `cargo fmt`, `cargo check`, focused Rust tests, the repository's physical PG qualification tasks, and standard CI. The 2026-11-07 PG module extraction compiled and passed 7 explicitly enabled native PG/MCP/Runner integration tests; those tests are Linux-only and do not qualify a Windows backend.

## Verification-validity LEGO: make existing evidence reusable

The hardest missing **Agent consumer** seam is not another Workspace GC
or model checker: it is the join between *a claim already verified*,
*the exact assumptions/readset under which it was verified*,
*a new Git/installed/environment delta*, and *the consumer decision*.
Current project truth boundaries make this a partial capability:

| Existing native capability | What is established | What it does not establish |
| --- | --- | --- |
| `tools/repo/source_history_legos.py` | Exact immutable Git membership/value delta | Model/code equivalence or dynamic readset |
| `tools/repo/convergence_plan.py` and `affected_owners.py` | Current policy-selected verification Owner tasks | Whether a historical proof is still valid |
| `tools/repo/check_architecture_docs.py` | Declared LEGO source/edge impact | Complete actual Agent/Runtime consumer graph |
| `scripts/verify_formal_trace.py` | Positive Rust formal-test source edges and task impact | Closed compiler/runtime inputs; proof reuse remains false |
| Harness `scripts/check_evidence.py` | Revision/dependency-scoped evidence currentness for qualifying `verified` entries | Runtime installed effects or unregistered claims |
| GitHub CI and Runtime receipts | Exact commit test PASS and observed provider effect | Automatic transfer across revisions or environments |

**Observed baseline (2026-11-14):** Harness evidence index contained
94 `historical` records and **zero** records with
`status=verified`. The selector treated a changed root
`mise.toml` as `CROSS_CUTTING`,
selecting 21 Owners for the inspected PR. These are empirical blockers,
not authorizations to promote history to current proof.

The target composition is:
`Claim/Consumer -> existing evidence + SourceCut + assumption/readset ->
delta closure -> impact verdict -> reuse qualified receipt OR run the
smallest actually affected native task -> bind new receipt`.
Use the existing CI/Artifact/Host/Git stores. A second Evidence DB,
global Verifier service or repeated replay mechanism is not required.

Only `EXACT_CUT_ACCEPTED` may inherit an existing qualified PASS
at its specific cut and environment. `SCOPED_SOURCE_UNCHANGED`
preserves source-only equality while all non-Git dimensions retain their
old independent standing. `IMPACTED_RECHECK` selects the
original affected test; `UNKNOWN_DEPENDENCY` identifies a
missing edge and requires targeted consumer investigation, **not**
automatic whole-system retesting. `NOT_RELEVANT` returns to
the Agent's actual productive work.

Thought LEGOs: assumption-guarantee compositional contracts (discharge
premises across modules), incremental build action inputs (Bazel/Nx),
typed evidence currentness, and value-of-information (stop checking
when the expected decision delta is zero). Logic LEGOs: claim identity,
dependency closure, change propagation, original receipt qualification,
consumer admission, and selective execution. Capability LEGOs: existing
Git SourceCut, Owner graph, Harness evidence checker, CI status, original
Runtime formal toolchain, PG Job/Artifact receipt.
See `services/runtime/AGENTS.md` for the operational rule.

### Qualified Harness issuer and environment preservation

Caller-supplied `foreignReferences` are metadata, never execution authority.
A Harness dispatch-fence hint may suppress Runtime's private Cargo default
**only when a same-PG Harness issuer verifier is operator-configured**.
The issuer guard still validates the original exact Tool intent inside the new
PG admission transaction. Without that verifier, forged/unrelated references
cannot alter the Runtime Cargo default. Neither a source patch nor the hint
establishes that the issuer guard is installed or configured on a live node.

## Agent usage

1. Discover node capabilities before choosing commands; never guess permissions or backend by the endpoint name.
2. Reuse exact Workspace and `clientRequestId`; bind source and provider identity before executing.
3. Call one supported Runtime execution surface and observe the same Job; preserve UNKNOWN when actual effects cannot be reconstructed.
4. Use the native domain/toolchain acceptance for semantic correctness, independent from process exit and Runtime transport success.
5. Make a module replacement only when a consumer and invariant show why the new seam matters. Reuse mature Git, PostgreSQL, systemd, Windows Job Objects, Cargo, and OpenTelemetry instead of a custom duplicate control plane.
6. Never present a source-only change, a passing Linux-only test, or an empty-epoch PG candidate as Windows production cutover or fleet-wide truth.

## Existing Skill reuse (do not duplicate)

The installed Ordivon Skills catalog currently exposes the approved advisory Skill `ecc-native/enterprise-agent-ops` (operational lifecycle, observability, release/rollback, incident response and owner metrics). Human operators can consult it for established incident practice; Agents should resolve its current binding before reading and treat its instructions as **advisory**, never as execution authority. Apply native Runtime Job/Attempt and PG evidence for all changes. No new overlapping Runtime operations Skill needs to be registered just to restate those practices.

## Relevant external authorities (use their native mechanisms)

- [Rust API Guidelines — naming](https://rust-lang.github.io/api-guidelines/naming.html)
- [Rust module filesystem layout](https://doc.rust-lang.org/reference/items/modules.html)
- [Git worktree](https://git-scm.com/docs/git-worktree)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html)
- [systemd.exec directories and resource boundary](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
- [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
- [OpenTelemetry semantic convention naming](https://opentelemetry.io/docs/specs/semconv/general/naming/)
- [cargo-nextest](https://nexte.st/)

### Kernel-owned process-group cancellation LEGO

This capability is composed from existing native APIs, **not a custom process-tree algorithm**. Precondition: exact Job→Attempt→Unit identity, committed cancel intent, and authoritative systemd service state. Linux action: request Unit stop; the existing systemd transient Unit already enforces `KillMode=control-group`, `TimeoutStopSec=2s` and `SendSIGKILL=yes`, so no additional per-PID or immediate-SIGKILL wrapper is justified. Windows action: use the already-owned Job Object handle rather than enumerating child PIDs. Postcondition: kernel process group absent or unpopulated, independently observed and retained as an immutable digest-bound `native-stop-evidence.json` Artifact within the existing PG terminal transaction; no claim of semantic task completion. Uncertainty: an unloaded Unit without bound Runner start evidence can race with dispatch. Implementation target: `runtime/platform/linux.rs`, `runtime/pg_runtime/job.rs`, and `runtime/pg_runtime/reconciliation.rs`. Source changes are **not deployed or physically qualified** until native tests and release receipt pass.

### Kernel-native liveness vs durable reservation

`globalExecutionLimit` is currently a product/PG admission cap, **not a Linux kernel process limit**. A pool blocked by stale `stopping` reservations is a control-plane reconciliation failure; adding an arbitrary timeout, artificially increasing a counter, or deleting PG rows is not kernel-based resolution. Prefer systemd `TasksMax`, `MemoryMax`, `CPUQuota`, cgroup v2 `pids.max`, and actual provider observations for physical resource control; retain only justified transaction-level admission/backpressure invariants. Do not conflate kernel process absence with the business outcome of arbitrary executed commands.

## Capacity and reconciliation: Human / Agent instructions

Human: inspect the node's `runtime.describe` capacity, then `job.list` and `job.get`. If a Job has durable cancellation intent but its Attempt still shows `stopping`, use `job.observe` to obtain the installed provider's current evidence. Do not manually delete a Job reservation, kill an unrelated process by name, or treat an operator UI timeout as proof of process termination. Follow the installed supervisor/recovery contract when the state cannot converge.

Agent: on `CONCURRENCY_LIMIT` with `commitState=not_started`, preserve the original operation identity; do **not** invent a new `clientRequestId` or claim a Job was accepted. Inspect other live work only if its identity is relevant. For an already committed Job, observe that exact identity. When process state is unknown, emit UNKNOWN and cite its actual Job/Attempt evidence; capacity must not be reclaimed by guessing a terminal outcome.

## Retirement and evidence standing

The Linux Runtime has a PG-native installed process, but the PG Cargo feature still transitively includes the legacy SQLite Core. Windows still has a live, growing SQLite Registry as of the 2026-11-07 audit. Neither fact can be erased by editing this guide. See [Operator Guide](operator-runtime.md), [Agent Guide](agent-runtime.md), and the [live audit](../audits/2026-11-07-runtime-owner-audit.md).
