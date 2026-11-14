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

## Preserve consumer-valued output before Workspace release

Git-clean is **not** equivalent to disposable. Git ignores build caches and
potentially valuable outputs in paths such as target/ and __pycache__/.
Even **workspace.close(force=false)** may remove ignored files. The
**consumerReleased=true** flag is a caller assertion, not identity proof,
consumer consent, delivery evidence, or proof that external readers are gone.

Use the **existing** carrier appropriate to the real consumer:

1. For source changes, integrate the required Git commit and independently
   read back its reachable contents before releasing the Workspace.
2. For **bounded execution evidence**, inspect the registered Job/Attempt
   Artifact with **artifact.read** or **artifact.content** before close. Check
   its actual bytes, meaning, and **truncated=false**; if missing or truncated,
   or the output must outlive the owning Runtime Registry, use step 3 instead.
   Job Artifacts are retained only with that Registry, not a general file
   publishing service or an indefinite archive. A successful process exit or
   an Artifact's presence does not prove domain semantic success.
3. For **consumer-valued** ignored files, large/binary outputs, or longer
   retention, publish using the existing Artifact capability or the
   destination's mature native API, then **read back the destination object**
   and verify it is usable. Classify an ignored path by the actual consumer:
   if acceptance or another actor still references it, or it is costly or
   impossible to regenerate, treat it as a deliverable until handed off.
   Cache-shaped path names alone are not evidence that output can be deleted.
   If the consumer or preservation requirement is unknown, do not assert
   release; resolve that uncertainty rather than blocking every cache.
4. Confirm known readers/writers, external consumers, dependent Workspaces,
   and active/held Jobs are finished. Runtime's Job/lease checks cannot
   prove the absence of arbitrary foreign processes or open file handles;
   if a known consumer is unresolved, **do not release**. Then request
   **workspace.close(force=false, consumerReleased=true)** with the
   **expectedSourceStateDigest** from **workspace.get**. Verify the reported
   closure disposition and, for bounded Job evidence, read the same Artifact
   again **after close**. Post-close readback detects retention failure;
   it does **not** replace the pre-close durable handoff when that is needed.
   **removed** means the worktree was retired, not that all external file
   handles or cached disk blocks disappeared immediately.

Delete disposable build caches through the established Workspace lifecycle;
preserve actual deliverables through their natural Git/Artifact consumers.
Do not add a second GC, publication registry, or evidence serializer.

## Operating boundaries

- Linux and Windows are independently native Runtime providers. Do not use a Linux node as an implicit Windows runner, or guess an elevated token.
- PostgreSQL is the target Registry backend. The 2026-11-07 `/proc/<pid>/exe` inspection verified that **both** active Linux Runtime service processes execute `ordivon-runtime-pg` with PG environment keys, despite one legacy-named systemd unit. That does not prove both instances share one PostgreSQL schema or that Windows has switched. Inspect each node and epoch independently.
- Never promote a test database, edit PG writer qualification rows, or remove SQLite data while a live consumer is unresolved.
- Use existing Git, systemd, SCM, PostgreSQL, Cargo, and OS utilities instead of inventing equivalent custom tools.
- Prefer focused, evidence-bearing verification of changed contracts. Rust unit/property tests and TLA+ exploration are different evidence classes; passing one does not prove the other.
- Run cleanup only against explicitly owned roots and use Runtime Workspace lifecycle APIs rather than raw directory deletion. Protect dirty workspaces, running/held Jobs, linked worktrees, deployment assets, and system paths.

## PG ReleaseEffect as an autonomous outcome

The Linux PG release.apply interface is only catalogued after exact
out-of-band Operator qualification, its systemd timer and live PostgreSQL
release stage are all present. It atomically admits an immutable effect,
not a claim that an installation has finished. The independent host
Operator performs the replacement and verifies the restarted MCP catalog.
After any lost release.apply response, reuse release.get with the ORIGINAL
clientRequestId. Never create a second release request due to transport
uncertainty.

## Native PG operator vs Agent authority

The PG ReleaseEffect is admitted under the source/epoch writer and a
separate operator-owned release qualification. The independent host
operator performs the physical systemd replacement; generic Workspace
execution cannot impersonate this release, even when operating with
administrator privileges. A committed dispatch event with no receipt
means reconcile the original effect, NOT reissue it. When a service
restarts, independently query release.get for the same authenticated
principal and clientRequestId and confirm the installed binary/catalog.
Until the connected node actually exposes qualified release.apply,
structuredReleaseConfigured remains false. Do not claim production
installation based only on successful disposable PG/systemd tests.

## PG release readback is not deployment

On the PG-native node, release.get provides a read-only identity-scoped
effect/receipt projection. It cannot install, retry or repair a release.
runtime.describe.structuredReleaseConfigured=false still means the PG writer
is unavailable. Do not infer from release.get that release.apply exists.
Missing/mismatched receipts require reconciliation, not success claims.
A normal Job success is not a Runtime installation receipt.

## Kernel-native stop / Agent decision

For a Job with cancellation already committed, use the exact Job/Attempt identity and `job.observe` rather than dispatching a replacement attempt. A successful `systemctl stop` request alone does not prove cgroup quiescence. Never enumerate PIDs and kill by broad process name; use systemd/cgroup identity on Linux and the installed Job Object owner on Windows. If the exact native group has stopped but the Runner produced no terminal evidence, preserve `lost`/UNKNOWN effect semantics. If no valid Runner start evidence exists, do not infer termination merely from an absent transient Unit because dispatch may still be in flight. `CONCURRENCY_LIMIT` is not proof of actual kernel resource exhaustion. See [Runtime LEGO Guide](runtime-legos.md) and [Operator Guide](operator-runtime.md).

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

See [Runtime LEGO Guide](runtime-legos.md) for capability and thinking LEGOs, [Operator Guide](operator-runtime.md), [Execution Model](../runtime.md), and [Owner Audit](../audits/2026-11-07-runtime-owner-audit.md).


## PostgreSQL resource scheduler (2026-11-08)

The Linux PG execution path persists every valid request before scheduling. `globalExecutionLimit` is null: neither global Job counts nor per-Workspace Job counts govern dispatch. `concurrency_reservations` retains durable lifecycle/idempotency ownership; `job_allocations` records physical resource and Workspace-access reservations. Pending work has no physical allocation. Terminal commit releases both atomically with its evidence and Artifacts. Cancellation and native reconciliation operate independently of ordinary resource admission.

`execution.budget.scheduling` accepts this optional contract:

```json
{"resources":{"cpuMillis":100,"memoryBytes":134217728,"pids":16,"ioIntensive":false},"workspaceAccess":{"readOnly":true},"owner":"build","priority":0}
```

The example resources are defaults, not hard limits or measured requirements. Existing CPU quota, memory maximum, PID maximum and timeout fields remain native hard budgets. Explicit resource requests must fit supplied hard budgets. `memoryHighBytes` and `ioWeight` optionally configure native soft controls. CPU request zero is suitable for wait-dominated work and receives low native CPU weight. Operators must choose realistic estimates; observations alone cannot predict a future compiler's peak memory.

Dispatch atomically checks observed CPU supply, available memory/PIDs, unspent active requests and Linux PSI. Memory keeps 5% of total (at least 64 MiB) headroom; PID headroom is 64. Current pressure targets are CPU some avg10 <70%, memory full avg10 <5%, I/O full avg10 <40% for I/O-intensive work. These explicit resource policies are exposed by describe; they are not Job-count limits. Pending tasks wake on PostgreSQL LISTEN/NOTIFY and a one-second pressure-observation fallback. Running observations use inotify/cgroup.events. Priority precedes equal-weight dominant-resource-share selection; an owner may borrow all idle supply. Owner is a trusted accounting label, not an authentication identity. No priority preemption is implemented.

Workspace concurrency depends on access conflicts. Default mutable work keeps an exclusive lease. `readOnly:true` jobs may share. Scoped mutable jobs declare existing `writePaths` directories and explicit `readPaths`; intersecting writes/reads wait, independent scopes share. Missing readPaths means the whole tree. Normal Workspace mutations use the same path conflict contract. Native read-only mounts protect the Workspace and shared Git metadata, with write exceptions for declared directories. Scoped source commitments bind HEAD and streamed contents/types/modes of the declared read set; symlink and hardlink aliases are rejected. This remains trusted-local execution: declarations do not establish arbitrary code's external effects or prove it only read its declared paths.

A daemon schedules pending work and reconciles issued native work without client polling. Restart retains the queue, committed allocation, native unit identity and immutable Runner bundle. An accepted request cannot launch without an active allocation and the dispatch CAS. Older issued Jobs retain their old immutable Runner; migrations backfill conservative resource/exclusive leases. A schema/source upgrade requires an independently installed writer seal so the older count-based binary cannot resume newly queued work. Never roll back that binary over outstanding resource-queued Jobs.

`formal/RuntimeResourceQueueR1.tla` checks finite CPU/memory, conflicts, pending allocation, restart and single-dispatch safety; it does not prove unbounded liveness. `resource_fit.rs` is checked against an independent widened-integer Kani specification. Physical SQL and systemd tests establish the executable refinement, including six simultaneous readers in one Workspace, restart, pending cancellation, disjoint writers, conflicting mutations and owner idle borrowing. Windows legacy execution remains a separate backend; this release does not qualify Windows PG cutover.

### Agent recipe: resource-aware, not count-based

For CPU/memory-intensive build, model, or media jobs, explicitly set `execution.budget.scheduling.resources` from known workload evidence; do not assume that the default 128MiB request covers Cargo compilation. Use `runtime.describe.scheduling` to observe PSI and effective node headroom, and prefer work that can share idle capacity without forcing another Owner into thrash. The workload's physical systemd Unit is in `system.slice`; do not read the Runtime manager's separate service cgroup as if it were the workload's capacity. The Slice and ancestor restrictions are the physical inputs to admission.

When cancelling, use the exact Job identity and then verify `job.get` reports terminal Attempt and released allocation; `lost` does not mean the external effect succeeded. If a heavy test materially raises PSI, cancel **that test only** and record its outcome as UNRUN/INCOMPLETE for the native test phase. For a scheduler patch, run `scripts/tla-formal check-resource` and `falsify-resource`, then obtain a real PostgreSQL/systemd consumer receipt; a parsed model alone is insufficient.


## Read-only evidence admission before running repeated verification (2026-11-14)

An Agent should not re-run a previously successful owner check just because
its prior chat cannot recall it. Use existing GitHub Actions check-runs at the
original **exact commit**, the repo's native SourceCut/Owner closure
(`convergence_plan.py`), and the existing Harness evidence checker:

```bash
# Query PR #2177's original GitHub CI at its exact proof SourceCut.
# Do not call Runtime Job replay, TLC, or a physical canary as a substitute.
python3 services/runtime/scripts/agent_evidence_admission.py --pr 2177 --owner runtime --target cc294b72700c9aa02c067f9962fab47359836af6

# A squash/Merge Queue may change commit identity. Query the new main
# commit's OWN CI instead of transferring the old pull-request HEAD status.
python3 services/runtime/scripts/agent_evidence_admission.py --commit cc294b72700c9aa02c067f9962fab47359836af6 --owner runtime --target cc294b72700c9aa02c067f9962fab47359836af6

# The Agent/Harness consumer queries the independent Harness authority.
# Runtime must not execute or import the higher-level Harness implementation.
python3 services/harness/scripts/check_evidence.py --query-claim harness.runtime-correlation.h2
```

Commit and PR queries use the same original CI identity checks.
The commit mode does not invent the missing PR base/Owner task selection,
and never inherits PASS across different Git cuts merely because they
result from a squash merge; the new commit needs its own official receipt.

The Runtime query calls `gh api` read-only, requires official GitHub
`root-verification` and exact-commit successful checks, then delegates
SourceCut/consumer selection to the **existing** Owner planner. A missing,
pending, ambiguous, failed, foreign or nonmatching receipt is UNKNOWN or
not passed; it must not make a stale proof current. The Agent composes
this Runtime source-CI query with the independently owned Harness claim
read. It never promotes archived historical evidence into current verified
evidence or makes Runtime depend on Harness. Different Git cuts remain separate.

`EXACT_CUT_CI_OBSERVED` means **one source commit's CI passed**.
It does NOT establish a production-installation receipt, closed dynamic
dependency graph, Rust/TLA refinement proof or a live process effect
(`proofReuseAdmissible=false`). `SCOPED_SOURCE_NO_OWNER_RECHECK`
is only a source-level Owner policy projection.
`UNKNOWN_SOURCE_RELATION` means investigate missing source relation,
**not** blanket re-run unrelated historic experiments.

This is on-demand Agent-consumable capability, **not yet wired automatically**
into the Harness Run scheduling lifecycle. No second evidence registry,
verifier service, or background monitoring job is introduced.
