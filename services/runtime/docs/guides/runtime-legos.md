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

`runtime/pg_runtime.rs` owns configuration, PG persistence access and internal reconciliation. Its submodules separate `node_query.rs` (discovery/list), `workspace.rs` (Workspace operations), `job.rs` (admission/observe/cancel/get), and `artifact.rs` (Artifact projection). The split preserves the public API and is not yet a PG-only Cargo dependency graph: the current feature tree still builds `rusqlite`.

## Reasoning LEGOs — reusable human/agent decisions

| Thought LEGO | Invariant or falsifier | Avoid |
| --- | --- | --- |
| Truth-owner decomposition | Each mutable fact has one responsible writer; projections never silently become writers | Two state ledgers for one Job |
| Effect ambiguity | A lost response or missing Result cannot prove failure, absence, or successful external effects | Blind retry with a new ID |
| Representation refinement | New models/contracts must preserve externally observed behavior and error standing; counterexample closes the claim | Calling a structural rename a verified equivalence |
| Source identity vs environment | Git commit and dirty-tree digest do not prove frozen clock, network responses, target mount view, or all host dependencies | Claiming a complete execution snapshot |
| Capacity and resource evidence | Use observed bounded execution limits and receipts; treat missing measurement as unknown | Invented resource accounting |
| Consumer-reachable retirement | Delete only exact owner state for which current and scheduled consumers have been checked | Deleting by age, glob, name, or repository history alone |

## Human usage

For normal operator work, identify the endpoint and actual installed backend, inspect `runtime.describe`, `workspace.list`, `job.list`, and read the installed service/receipt. For physical execution use the established tool and then inspect its Job and Artifact. For maintenance, classify the exact state root as *active*, *quarantined/unknown*, or *consumer-free*. Prefer `git worktree remove` for worktree lifecycle and native systemd directory policy for service-managed directories. Use the existing release and rollback mechanism; never rename a live service to make the architecture diagram cleaner.

For code changes, use `cargo fmt`, `cargo check`, focused Rust tests, the repository's physical PG qualification tasks, and standard CI. The 2026-11-07 PG module extraction compiled and passed 7 explicitly enabled native PG/MCP/Runner integration tests; those tests are Linux-only and do not qualify a Windows backend.

## Agent usage

1. Discover node capabilities before choosing commands; never guess permissions or backend by the endpoint name.
2. Reuse exact Workspace and `clientRequestId`; bind source and provider identity before executing.
3. Call one supported Runtime execution surface and observe the same Job; preserve UNKNOWN when actual effects cannot be reconstructed.
4. Use the native domain/toolchain acceptance for semantic correctness, independent from process exit and Runtime transport success.
5. Make a module replacement only when a consumer and invariant show why the new seam matters. Reuse mature Git, PostgreSQL, systemd, Windows Job Objects, Cargo, and OpenTelemetry instead of a custom duplicate control plane.
6. Never present a source-only change, a passing Linux-only test, or an empty-epoch PG candidate as Windows production cutover or fleet-wide truth.

## Relevant external authorities (use their native mechanisms)

- [Rust API Guidelines — naming](https://rust-lang.github.io/api-guidelines/naming.html)
- [Rust module filesystem layout](https://doc.rust-lang.org/reference/items/modules.html)
- [Git worktree](https://git-scm.com/docs/git-worktree)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html)
- [systemd.exec directories and resource boundary](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
- [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
- [OpenTelemetry semantic convention naming](https://opentelemetry.io/docs/specs/semconv/general/naming/)
- [cargo-nextest](https://nexte.st/)

## Retirement and evidence standing

The Linux Runtime has a PG-native installed process, but the PG Cargo feature still transitively includes the legacy SQLite Core. Windows still has a live, growing SQLite Registry as of the 2026-11-07 audit. Neither fact can be erased by editing this guide. See [Operator Guide](operator-runtime.md), [Agent Guide](agent-runtime.md), and the [live audit](../audits/2026-11-07-runtime-owner-audit.md).
