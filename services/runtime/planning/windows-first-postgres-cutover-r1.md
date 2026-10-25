# Runtime: Windows-first PostgreSQL cutover (2026-10-26)

**Decision:** migrate the Windows Runtime Registry first, then use ordinary
Windows Runtime active_user Jobs to stop/restart only the Linux Runtime service
via wsl.exe. Reuse the existing Runtime operator, release and Registry owners.
No dual Runtime leader election, shadow dual-writer or new scheduler.

## Evidence and actual blockers

- Windows native Runtime service is RUNNING under the limited identity
  NT SERVICE/OrdivonRuntimeR6Candidate; its installed Registry is still SQLite.
  No PostgreSQL storage backend is configured. Windows service-limited identity
  can open a TCP connection to 127.0.0.1:14550.
- The Windows Runtime active_user identity can invoke archlinux WSL as Linux
  root and inspect active ordivon-runtime.service. The service-limited identity
  cannot see that per-user WSL distro (WSL_E_DISTRO_NOT_FOUND). Only explicit
  active_user Jobs can be considered for WSL operations. Do not widen the
  service token or mistake WSL access for automatic permission to mutate state.
- PostgreSQL currently runs inside the WSL environment, listening on
  loopback TCP 14550; Windows can reach it. Stop only Linux Runtime service,
  NOT the whole WSL distro or its PostgreSQL process. Windows independence
  from shutting down WSL is neither required here nor proven.
- Existing Runtime Registry R06 uses Rust rusqlite and SQLite schema v6.
  Existing formal/RuntimePgCutoverR1.tla proves scoped bounded properties
  of copied identity/content, single installed writer and rollback conditions;
  it does NOT prove source/PG row correspondence or installed effects.

## One-way state representation

Apply to Windows first, then Linux:

 LEGACY_LIVE -> QUIESCED -> PG_IMPORTED -> PG_VERIFIED -> PG_LIVE -> LEGACY_RETIRED

A failed import/verification returns to QUIESCED for investigation, not an
unqualified old-writer restart. Before any independent PG commit, an explicitly
validated rollback is possible. After the first accepted PG write, only
PG-forward recovery is allowed; do not resurrect the old SQLite writer.

Obligations, to be refined to real Rust/PG/installed-state checks:

- single_writer(node): no simultaneous SQLite and PG effective writer.
- promotion(node): exact PG row identity/content and recovery/effect parity;
  the old writer must already be fenced.
- WindowsPGReady requires physical Windows service restart and replay evidence,
  not just DB connectivity or a passing abstract model.
- LinuxQuiesce requires WindowsPGReady and an observed active_user WSL command.
- LinuxPGReady requires Linux Runtime stopped/quiesced, PostgreSQL accessible,
  exact migrated data proof and legacy-writer fence.
- ambiguous_or_committed_effect forbids automatic duplicate redispatch.
- after_pg_write forbids SQLite rollback or a second legacy authority.

## Minimum capability LEGO and acceptance

| Stage | Existing owner | Admission / proof |
| --- | --- | --- |
| Inventory | Git/Runtime and R06 | Fresh upstream SHA and installed binary digests; Windows and Linux service users; exact table/schema shape, Job/Attempt/reservation/unknown-effect populations; PG role/endpoint; storage and held jobs; no secret content in reports |
| Windows PG storage | Rust Runtime R06 | Replace Registry storage with native PG under existing Tool interfaces; schema with unique principal/client_request_id, row-version, Job/Attempt/effect/reservation constraints; no repaired SQLite |
| Windows import | Runtime R06 and operator R15 | Freeze admissions; reconcile active/unknown/held attempts; consistent source snapshot; PG import; read back every identity and semantic dependency (not counts alone); backup witness and duplicate-identity negative cases |
| Windows activation | Existing structured release | Quiesce, fence legacy writes, install candidate from source-qualified digest, restart Windows Runtime and prove old Job replay, no duplicate effects, recovery and newly admitted PG Job |
| Linux quiesce | Windows Runtime active_user | One explicit Windows Job invokes wsl.exe -d archlinux -u root systemctl stop ordivon-runtime.service; verify service stopped, PG still online; do not shut down WSL |
| Linux import/activation | R06/R15 plus native Linux Runtime | Perform same exact source-to-PG import, fence, restore evidence; Windows invokes service start; check PG-based Job replay and Linux active/held/unknown recovery |
| Retirement | Existing R15 Git/Workspace operators | No real consumer of old DB or compatibility writer; safe delete after installed and semantic PG acceptance; no second controller; move next to Host/Harness/Network and domains |

**Stop conditions** (native CEGAR): mismatch of any Job/Attempt identity or
effect, PG unreachable under the real Windows service, non-reconcilable
UNKNOWN_DISPATCH, duplicate physical effect, old SQLite writer still alive,
Windows active_user WSL unavailable, incorrect candidate binary digest, or
PG going offline during Linux Runtime stop. For each, refuse promotion and
retain recoverable evidence; do not claim success from a green TLC run.

This is a Windows-first orchestration PLAN, not implementation or deployment
of PostgreSQL Runtime Registry. Backend migration needs its own real Rust PG
implementation and source-bound Windows and Linux recovery acceptance.

## Prohibited complexity

No dual Runtime leader selection, generic failover fabric, new runtime agent,
new database migration framework, two active writers, SQLite feature patches,
PG server relocation solely to restart Linux Runtime, or speculative
domain-level optimization before the core cutover is verified.
