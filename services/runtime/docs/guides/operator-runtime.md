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
