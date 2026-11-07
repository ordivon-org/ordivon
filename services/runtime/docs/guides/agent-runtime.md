---
schema_version: 1
id: runtime.agent-execution-guide
title: Runtime Agent Execution Guide
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-runtime
audience:
  - agent
updated: 2026-11-07
summary: Agent execution and evidence interpretation guidance for the independently deployed Runtime nodes.
evidence_status: observed
readiness: READY
applies_to:
  - ordivon-runtime
related:
  - runtime.model
  - runtime.operations
---
# Runtime Agent Execution Guide

## Purpose and truth boundary

Runtime owns Workspace, admitted operation identity, Job and physical Attempt, executor observation, Registry lifecycle, and bounded result evidence. The Agent or domain owns goal interpretation and semantic completion. A process exit code of zero is not proof that a requested external-world effect happened.

At the beginning of an operation, call `runtime.describe` on the **specific node** to discover the supported OS target, provider identity, limits, and execution profile. Never infer Windows privileges or Linux capabilities from documentation alone. Do not assume that all Runtime nodes use the same Registry backend: inspect the service actually connected.

## Minimal execution cycle

1. Inspect exact Workspace identity with `workspace.get`; open a Workspace at an exact commit only if no suitable existing one exists.
2. Inspect source and any active/held Jobs; do not mutate a Workspace consumed by an active Job.
3. Compute a stable `clientRequestId` before admission. Keep it unchanged across a lost reply.
4. Submit `workspace.exec`, `workspace.execPlan`, or an appropriate immutable-input variant using an absolute executable and a bounded execution plan.
5. Observe the **same** `jobId` through `job.get` / `job.observe`. Never create a second Job merely because the transport timed out.
6. Read `artifact.read` and verify the retained output and evidence standing. If outcome is `lost`, `orphaned`, `unknown`, or delivery uncertain, do not translate it into `failed` or silently redispatch an effect-opaque operation.
7. Check `workspace.diff`, `workspace.get`, and domain-specific acceptance. Close via `workspace.close` only when no consumer remains.

## Operating boundaries

- Linux and Windows are independently native Runtime providers. Do not use a Linux node as an implicit Windows runner, or guess an elevated token.
- PostgreSQL is the target Registry backend. The 2026-11-07 `/proc/<pid>/exe` inspection verified that **both** active Linux Runtime service processes execute `ordivon-runtime-pg` with PG environment keys, despite one legacy-named systemd unit. That does not prove both instances share one PostgreSQL schema or that Windows has switched. Inspect each node and epoch independently.
- Never promote a test database, edit PG writer qualification rows, or remove SQLite data while a live consumer is unresolved.
- Use existing Git, systemd, SCM, PostgreSQL, Cargo, and OS utilities instead of inventing equivalent custom tools.
- Prefer focused, evidence-bearing verification of changed contracts. Rust unit/property tests and TLA+ exploration are different evidence classes; passing one does not prove the other.
- Run cleanup only against explicitly owned roots and use Runtime Workspace lifecycle APIs rather than raw directory deletion. Protect dirty workspaces, running/held Jobs, linked worktrees, deployment assets, and system paths.

## Useful conceptual LEGOs

| LEGO | Preconditions | Observable postcondition | Evidence |
| --- | --- | --- | --- |
| Workspace identity | exact Git revision and owned root | isolated recorded working copy | Workspace source revision/digest |
| Job admission | valid proposal, capacity, authenticated principal | durable operation ID or exact replay | Registry projection |
| Physical Attempt | committed Job and provider commitment | launched/terminal/unknown Attempt | Runner/SCM/systemd evidence |
| Reconciliation | existing committed state and observed executor | justified convergence or explicit unknown | observation / terminal artifacts |
| Close/reclaim | no active/held consumer and accepted source state | owned Workspace retired | close disposition / Git state |
| Release | candidate digest and operator-qualified release authority | receipted deployment state | release.get and installation receipt |

These are capability/contract descriptions, not newly registered executable Tools. Design extensions using `(input, output, state, precondition, postcondition, invariant, effects, cost, uncertainty, provenance, decomposition)`. An unknown postcondition must remain UNKNOWN.

See [Operator Guide](operator-runtime.md), [Execution Model](../runtime.md), and [Owner Audit](../audits/2026-11-07-runtime-owner-audit.md).
