---
schema_version: 1
id: runtime.operator-guide
title: Runtime Operator Guide
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-runtime
audience:
  - operator
  - user
updated: 2026-11-07
summary: Human-operated Runtime discovery, fault diagnosis, cleanup, and storage-cutover guidance.
evidence_status: observed
readiness: READY
applies_to:
  - ordivon-runtime
related:
  - runtime.operations
  - runtime.recovery
---
# Runtime Operator Guide (Human)

## Know which Runtime you are operating

Record: node name, OS, installed binary digest, exact Git commit, service identity, Registry backend, active Job count, Workspace count, and configured consumer endpoint. Do not treat a repo checkout, candidate service, or green test as proof that the installed production path changed.

Observed on 2026-11-07: both active Linux `ordivon-runtime.service` and `ordivon-runtime-pg-candidate.service` execute a PG-native binary with `ORDIVON_PG_DSN` and `ORDIVON_PG_SCHEMA` present. The legacy SQLite database, four obsolete trace files, 428,509 retired Attempt directories and the remaining two orphaned marker files were removed after explicit consumer verification. The old Linux `/var/lib/ordivon/registry/` directory itself was also removed. Other Owner roots and current PG stores were not touched. This is a completed **Linux legacy Registry data-root** retirement, not proof that Windows Runtime or all legacy SQLite source code has been retired. Windows has running `OrdivonRuntimeR6Candidate`, `OrdivonRuntimePrivilegedBroker`, and `OrdivonRuntimePostgreSQL18` services; a running PostgreSQL server alone does not confirm that Windows Runtime is PG-backed. A separate Windows inspection found a 251,088,896-byte SQLite Registry file under `C:\ProgramData\Ordivon\RuntimeCandidateR6\registry\`; qualify its native PG replacement before deleting it. These are time-scoped observations.

## Ordinary safe operations

1. Use `runtime.describe` on each connected node. Compare only native targets and configured authority, not inferred access.
2. Use `workspace.list` and `job.list` to inventory current consumers; use `workspace.get` and `job.get` for an exact identity.
3. Check `job.observe` for the particular Job rather than restarting or resubmitting an ambiguous external effect.
4. Inspect source differences with `workspace.diff` and recorded terminal artifacts before concluding success.
5. Use the documented operator `status`, `doctor`, `repair`, `deploy`, or lifecycle commands for the installed backend only after checking they are actually supported by that release.

## Storage and cleanup

Cleanup eligibility is established by **consumer reachability**, not naming, age, or the mere presence of a `cache`, `archive`, `sqlite`, or `r6` substring.

- **Keep**: current service executables/configuration, live PG schema and WAL, active/held Job or Workspace state, dirty Workspace source, Git objects used by worktrees, and OS service files.
- **Reclaim through native owners**: closed/verified Workspaces, owner-tagged disposable test output, expired bounded caches, and transient files with no ongoing reference. Use `workspace.close`, Git worktree commands, systemd directory lifecycle, or existing lifecycle utilities; do not substitute blind `rm -rf`.
- **SQLite retirement**: first establish exactly which running service/binary/client still opens the old Registry, switch those consumers to one qualified PG writer, prove new admission/readback/reconciliation and restart recovery, then stop the retired writer and delete only the verified old state. Old run history need not be migrated merely to preserve it; live consumers are a different question.
- **System paths**: never recursively erase `/var/lib`, `/run`, `/etc`, Windows ProgramData, or deployment roots using guessed patterns. A Runtime-owned subpath can be retired only after its owner, reader set, and final service activation are known.

For ordinary Linux service directory management, prefer systemd `StateDirectory=`, `CacheDirectory=`, `RuntimeDirectory=`, and an explicit `tmpfiles.d` policy with the correct retention meaning. Do not make an active store 'temporary' to facilitate cleanup.

## Native cancellation and stuck capacity (Linux)

The kernel and systemd already manage process lifetime. Use the installed Runtime's exact Job and native Unit identity rather than `ps | grep` PID-tree scripts. Human diagnosis: inspect `job.get`, `systemctl show <exact-unit>`, `systemctl status <exact-unit>`, the recorded cgroup's `cgroup.events` `populated` value, and (where supported) `systemctl kill --kill-whom=cgroup --signal=SIGKILL <exact-unit>`. The native Unit must be tied to the admitted Attempt before any physical signal. Never kill a broad `ordivon-*` wildcard or the PG server service itself. `cgroup.kill` is the Linux kernel's native recursive process termination primitive.

`systemctl --no-block stop` only queues a stop; it is not terminal evidence. If the Unit is no longer active and a committed `runner-start.json` binds Job/Attempt/launch token and kernel cgroup population has reached zero, an absent Runner result permits an honest *lost execution result*, not a fabricated successful cancellation. If Runner start is missing, a not-found Unit can race with pending launch; preserve UNKNOWN and investigate native dispatch admission. The application-level effect remains unproven even if the kernel confirms there are no processes.

Linux references: https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html and https://www.freedesktop.org/software/systemd/man/latest/systemctl.html. Windows counterpart: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects (TerminateJobObject / kill-on-close with identity-bound handle). Do not manually mutate live PostgreSQL reservations or treat a source-only change as installed service behavior.

## Changes and acceptance

Use an isolated Git Workspace, validate the smallest affected contract, then use the **existing** release/receipt path. Acceptance evidence includes code diff, selected Rust tests, MCP tool discovery, native Linux and Windows execution where applicable, PG restart/recovery, and installed binary/endpoint confirmation. A source change without deployment remains source-only.

Read [Agent Execution Guide](agent-runtime.md), [Operations](../operations.md), [Recovery](../recovery.md), and [Owner Audit](../audits/2026-11-07-runtime-owner-audit.md).


### PG cancellation recovery without an execution slot

The installed PG binary accepts `--reconcile-cancelled` as an operator-only native
invocation. Load the same private EnvironmentFiles as the installed service; run
it through systemd or the operator shell, not through `workspace.exec`. It only
reconciles already committed cancelled Jobs, up to 100 per invocation, and does
not admit a command, change request identity or consume execution capacity.
The service also runs a bounded cancellation recovery pass every two seconds;
clients can disconnect without leaving cancellation dependent on later polling.
Failed observations remain pending and retry. Neither mode blindly releases a
reservation, fabricates an execution Result, nor claims an external effect failed.
Observe waits use inotify and cgroup.events wakeups with a bounded fallback;
notifications are hints and never authority to commit terminal state.

Cancellation before dispatch has a separate PG fact boundary: an `accepted`
Attempt with committed stop intent cannot pass the dispatch admission CAS. It
therefore commits `cancelled` with `admission_cancel_evidence`, without inventing
Runner or cgroup evidence. Its Result availability remains false. A real
PostgreSQL/MCP test admits such an Attempt through PgAdmissionStore, cancels it,
and verifies zero DISPATCH_ISSUED events. This is distinct from an already
launched Attempt with missing Result, whose external outcome remains LOST.


The periodic worker also reconciles already-issued nonterminal Attempts, including
natural completion after a disconnected client. It never dispatches a natural
`accepted` Attempt. The native `--reconcile-cancelled` CLI remains restricted to
committed cancellation intent. A disposable PG/systemd test restarts only the MCP
control process while a native Unit runs, then verifies automatic terminal
readback and exactly one DISPATCH_ISSUED event. This permits control-plane recovery
without treating Runtime service restart as native Job termination.


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

### Native execution Slice accounting and real pressure

The Linux launch path pins transient workload Units to `system.slice`, so the scheduling supply observer reads **the Slice and its cgroup v2 ancestors**. A Runtime management service's private service cgroup can have different `TasksMax` and other limits; it must not be mistaken for the sibling workload's capacity. Effective CPU quota, `memory.max/current`, and `pids.max/current` are intersected across both layers. `max` never overrides a stricter ancestor limit; unreadable controller values fail the scheduling observation instead of supplying fictitious headroom.

A real source verification of a Cargo build briefly coincided with node PSI `memory full avg10=49.82%` and `io full avg10=63.94%`. The exact test Job was cancelled through Runtime and converged `lost/released`, after which PSI observations were `0.55%` and `3.88%`. The before/after correlation does not prove sole causality. Treat the default 100m CPU / 128MiB memory values as placeholders for unknown workloads, **not safe size estimates for builds**. Declare realistic resource requests for heavy work and inspect pressure before launching multiple native builds; do not increase a global Job-count limit to mask a resource bottleneck.

The canonical `scripts/tla-formal check` includes `RuntimeResourceQueueR1`; `falsify-resource` verifies the `Capacity` predicate catches a deliberately removed CPU-admission guard. Neither TLC nor unit tests replace real PG/systemd, fresh-node install and recovery receipts.
