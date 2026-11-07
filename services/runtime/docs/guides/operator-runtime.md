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

Observed on 2026-11-07: both active Linux `ordivon-runtime.service` and `ordivon-runtime-pg-candidate.service` execute a PG-native binary with `ORDIVON_PG_DSN` and `ORDIVON_PG_SCHEMA` present. The old SQLite file measured 6,166,085,632 bytes at first inspection; neither active PG process held it open. Subsequently it was removed after verifying no file opener, no active SQLite-referencing timers, and no PG Store Root within the old Registry tree; the Registry parent and other files remained intact. This is a completed **Linux file-only** retirement, not proof that Windows or all legacy SQLite source code has been retired. Windows has running `OrdivonRuntimeR6Candidate`, `OrdivonRuntimePrivilegedBroker`, and `OrdivonRuntimePostgreSQL18` services; a running PostgreSQL server alone does not confirm that Windows Runtime is PG-backed. A separate Windows inspection found a 251,088,896-byte SQLite Registry file under `C:\ProgramData\Ordivon\RuntimeCandidateR6\registry\`; qualify its native PG replacement before deleting it. These are time-scoped observations.

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

## Changes and acceptance

Use an isolated Git Workspace, validate the smallest affected contract, then use the **existing** release/receipt path. Acceptance evidence includes code diff, selected Rust tests, MCP tool discovery, native Linux and Windows execution where applicable, PG restart/recovery, and installed binary/endpoint confirmation. A source change without deployment remains source-only.

Read [Agent Execution Guide](agent-runtime.md), [Operations](../operations.md), [Recovery](../recovery.md), and [Owner Audit](../audits/2026-11-07-runtime-owner-audit.md).
