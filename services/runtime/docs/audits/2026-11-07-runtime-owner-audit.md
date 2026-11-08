---
schema_version: 1
id: runtime.owner-audit-2026-11-07
title: Runtime Owner Audit 2026-11-07
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: internal
owners:
  - ordivon-runtime
audience:
  - operator
  - builder
  - agent
updated: 2026-11-07
summary: Observed Runtime directory inventory, current/legacy backend distinction, cleanup classification, and LEGO convergence plan.
evidence_status: observed
readiness: REVIEW
applies_to:
  - ordivon-runtime
related:
  - runtime.model
  - runtime.operations
---
# Runtime Owner Audit — 2026-11-07

## Scope and evidence standing

Audited the source tree at Linux commit `f52091fb1c8f920b7114c813142d1e7795ae8664` in isolated Workspace `ws-gpt6-runtime-owner-audit-20261107-r1`. Windows read-only comparison used commit `73196dc2bc076f148e905b688fafa34d40486a9c`. Findings are **time-scoped source and service observations**, not installed release acceptance. The initial census was read-only; later exact-path legacy SQLite/trace retirement is recorded below.

Linux tracked directory census: `crates` 125 files (~3.10 MB), `research` 132 (~1.53 MB), `scripts` 62 (~1.53 MB), `docs` 24 (~0.39 MB), `planning` 8 (~0.15 MB), `formal` 14 (~0.07 MB), `platform` 3 (~0.18 MB), `packaging` 11 (~0.03 MB). File counts exclude untracked/ignored working data. Code scans found 24 tracked files referencing `registry.sqlite3` and 15 referencing `rusqlite` (scans included docs/tests where indicated).

Linux service inspection found both `ordivon-runtime.service` (PID 133847, port 8897) and `ordivon-runtime-pg-candidate.service` (PID 6026, port 28795) active. Crucially, `/proc/<pid>/exe` and process configuration showed **both were PG-native executables** with `ORDIVON_PG_DSN` and `ORDIVON_PG_SCHEMA` set, despite the first unit's historical name. Neither process held a file descriptor to `registry.sqlite3`. Windows showed `OrdivonRuntimeR6Candidate`, `OrdivonRuntimePrivilegedBroker`, and `OrdivonRuntimePostgreSQL18` active; this alone does not prove the Windows Runtime Registry uses PG. The old file `/var/lib/ordivon/registry/registry.sqlite3` measured exactly 6,166,085,632 bytes (last modified 2026-11-07 07:40:03 UTC). `fuser` reported no current opener at inspection, but this alone cannot rule out scheduled consumers. The `/var/lib/ordivon` root is shared across other Owners. Subsequent exact-path retirement was **completed** through Job `job-01a1b62d-29d9-7740-b0b2-fe5ae6510095`: both live Linux service binaries and PG configuration were reverified, their PG Store Roots were confirmed outside the old Registry tree, the SQLite-referencing lifecycle/storage-pressure timers were inactive and disabled, `fuser` found no opener, and the file identity (inode/size/mtime) was compared immediately before unlink. The command returned `file_now_absent=True`; the Registry parent directory and all its other contents were preserved. The deletion did not change installed Runtime binaries, unrelated Owner state, or the Windows Registry.

## Directory-by-directory disposition

| Directory | Current role | Decision / next proof |
| --- | --- | --- |
| `crates/ordivon-runtime-core/src/runtime/engine/` | admission, execution, reconciliation, terminal commit | KEEP; inspect cross-module state dependencies before additional extraction |
| `crates/ordivon-runtime-core/src/runtime/registry/` | SQLite-oriented durable lifecycle | RETIRE-CANDIDATE after complete PG consumer cutover; do not keep dual truth |
| `crates/ordivon-runtime-core/src/pg_*.rs`, `runtime/pg_runtime.rs` | PG admission/readback/native execution vertical | PROMOTE-CANDIDATE; verify installed writer, restart, recovery, cancellation, evidence |
| `crates/ordivon-runtime-core/src/universal/` | reusable runner, source state, filesystem and workspace operations | KEEP; identify reusable independent seams, avoid name-only crate splits |
| `crates/ordivon-runtime-core/src/bin/` | runner, doctor, inspect, repair, Windows deploy and fixtures | AUDIT every binary's build/packaging consumer; keep only qualified owner paths |
| `crates/ordivon-runtime-mcp/src/server/` | transport, schemas, auth, tool adapter | KEEP; thin transport, no second execution state |
| `platform/windows/` | native Windows launcher/broker/fixture | KEEP; tests and installed launcher identities are release consumers |
| `packaging/systemd/`, `packaging/windows/` | managed services and policies | KEEP; compare current installed service units before retiring configurations |
| `scripts/` | owner operation wrappers, tests, deployment, backup | KEEP selectively; find duplicate backends and dead scripts by exact call sites |
| `tests/` | real-system/Windows/contract verification | KEEP if they falsify active contracts; do not judge by rarity of failure |
| `formal/` | TLA+ state models and trace checks | KEEP verified consumers; label model version and scope; UNKNOWN is not PASS |
| `standards/` | owner-native standard representation | KEEP as candidate until generator/consumer and freshness validation |
| `research/` | formal foundations, owner roles, provenance | KEEP canonical entry + referenced historical proof; distinguish history from active authority |
| `planning/` | LEGO plans, inventories, prior release stages | CLASSIFY as active/closed/superseded; do not treat roadmap as source of current binary truth |
| `docs/` | operational and user-facing contract | FIX stale backend truth, remove ambiguous current-status claims |
| `evidence/` | previous integration receipts | KEEP when actual tests/docs reference them; otherwise prefer verified Git history |
| `examples/` | finite demo | KEEP only if demo acceptance still consumes it |
| `.github/`, `.ordivon/` | automation, ownership and publication | KEEP while release and CI consumers remain |
| root Cargo, Python, toolchain configs | build and pinning | KEEP while build consumers remain |

## Observed specific candidates

1. **P0**: `AGENTS.md` asserted “SQLite owns durable ... state” without distinguishing PG. Corrected its truth boundary; live Linux inspection now shows two PG-native services. The remaining SQLite file and all scheduled consumers must be separately classified before deletion.
2. **P0**: `docs/quickstart.md` used an undefined `$repo` variable in its deploy snippet. Correct the command.
3. **P1**: Renamed `docs/runtime-vnext-decomposition.md` to [`docs/runtime-decomposition-history.md`](../runtime-decomposition-history.md) after finding zero literal filename references in tracked source; updated the document heading and marked it as historical implementation evidence, not live PG authority. The content was preserved.
4. **P1**: `runtime/registry.rs`, `runtime/inspection.rs` and supporting scripts still refer to the former SQLite store. Removal requires a verified absence of live consumers, not solely a grep result.
5. **P2**: `research/core/HISTORICAL-EF27.md` is referenced by 9 tracked files including provenance; do **not** delete by its historical title.
6. **P2**: `evidence/harness-h2-runtime-r2-live-d50f609-20260731.json` has 3 tracked consumers; keep until its acceptance contract is intentionally replaced.
7. **P2**: `standards/runtime_standard_native_r3_report.json` is referenced by its validation script and TOML; do not classify as disposable generated garbage.
8. **P2**: `planning/lego-plan-r1.json` is still referenced by verification material; do not remove before replacements are identified.

## Target minimal composition

Keep **one runtime execution kernel**, **one durable writer per node/epoch**, native **Linux/Windows providers**, a **thin MCP boundary**, and an **operator projection**. Keep Git Workspace and Artifact state distinct from Registry state. Route external long-running workflows to the existing Host/Harness/Temporal owner, not an invented Runtime business scheduler. Do not create a new crate merely because a source file is long; split only where a self-contained invariant can be tested and its dependencies narrowed.

Boundary contracts for capability/idea LEGOs:

- Workspace source identity (Git exact revision/digest) and Workspace close consumer fence.
- Durable Job/Attempt admission and exact replay (PG row truth).
- Native execution provider (systemd/cgroup or SCM/Job Object, with provider-identity commitment).
- Reconciliation (preserve unknown when execution outcome cannot be established).
- Evidence (bounded artifacts, digests, provenance, semantic-completion boundary).
- Resource/lifecycle policy (known owner, capacity, source validity, consumer reachability).
- Structured release (deployment receipt, not process exit as release proof).

Each LEGO definition should record `I, O, S, pre, post, inv, eff, c, epsilon, prov, unfold`, link the *actual consuming* implementation, and distinguish specification, model/validator, implementation. An unproved equivalence is not a migration permission.

## Mature implementation and theory references

- Rust API Guidelines: https://rust-lang.github.io/api-guidelines/naming.html — snake_case modules, clear conversion and feature names.
- Cargo/Rust module structure: https://doc.rust-lang.org/stable/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html
- Git worktree: https://git-scm.com/docs/git-worktree — lifecycle and safe removal.
- systemd directory ownership: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html — StateDirectory, CacheDirectory, RuntimeDirectory.
- systemd tmpfiles: https://www.freedesktop.org/software/systemd/man/latest/tmpfiles.d.html — age-scoped transient cleanup, not blanket state removal.
- Temporal idempotent Activity design: https://docs.temporal.io/ — outside Runtime physical Job/Attempt semantics.
- OpenTelemetry semantic conventions: https://opentelemetry.io/docs/specs/semconv/ — consistent trace attributes, not an alternative state ledger.
- TLA+ and TLC: https://docs.tlapl.us/ — concurrency model checking, bounded to modeled assumptions.
- cargo-nextest: https://www.nexte.st/ — standard Rust test execution.

## Acceptance and completion gates

- **Source P0**: stale AGENTS/quickstart fixed; current Git diff reviewed; affected docs contract passes.
- **Backend P0**: identify each live service binary, Registry backend, PG writer epoch, and caller endpoints; every current Job consumer reads and writes the same target PG source. No SQLite fallback remains in the deployed execution path.
- **PG functional**: real fresh admission, exact replay, Job observation, cancellation, terminal evidence, restart recovery, Workspace close, and concurrency correctness.
- **Windows**: confirm native target and PG backend independently; native provider tests cannot be replaced by Linux tests.
- **Cleanup**: only after absence of active and scheduled consumers, classify each candidate as remove/keep/unknown. Delete old SQLite operational data without historical migration once its consumer set is closed. Both observed Linux services already execute PG-native binaries; confirm auxiliary jobs, scripts, and Windows separately rather than treating the old service name as SQLite proof.
- **Formal/LEGO**: each replacement declares pre/post/invariants, evidence standing, and falsification. No new test for a claim already discharged by an existing stronger proof.
- **Deployment**: release receipt and installed source/binary equality; unmerged Workspace source changes do not count as installed.

## Next audited steps

1. Read service startup identity and Registry backend without exposing secrets.
2. Trace the caller graph from Gateway/Harness/Host to every Runtime endpoint.
3. Qualify a single PG writer and physical Linux/Windows acceptance.
4. Remove obsolete SQLite source and associated scripts/migrations only after exact consumer graph closure.
5. Recount tracked, ignored, and owner-managed data separately and reclaim only closure-proven candidates.

## Verified PG-only source blocker

The active Linux process uses the PG-native binary, but the **source dependency graph is not PG-only**:

- `crates/ordivon-runtime-core/Cargo.toml` sets `default = ["transactional-runtime"]`, and that feature includes `dep:rusqlite`.
- `crates/ordivon-runtime-mcp/Cargo.toml` depends on Core with `features = ["transactional-runtime"]` unconditionally; `postgres-runtime` only adds `postgres-registry-admission`.
- `src/lib.rs` exports `PgRuntime` only when both `transactional-runtime` and `postgres-registry-admission` are enabled on Linux; `runtime/mod.rs` still declares `registry` and related SQLite modules.
- Thus an installed PG executable need not open a SQLite database, but the source/build may still compile and link the legacy SQLite implementation. The file deletion alone is **not** a source-code deprecation.

The next safe decomposition is to separate storage-neutral Job/Attempt/Workspace contracts and provider/evidence interfaces from the SQLite Runtime implementation, make PG admission/reconciliation the only production backend, retire the legacy MCP entry point and operator-only SQLite repair/tools after verifying consumers, and finally remove `rusqlite`, SQLite migrations, and obsolete tests. Preserve real native Windows execution and process recovery during this refactor. Accept the change only with a PG-only Cargo dependency tree, PG real-system tests, native Windows verification, and installed release receipts. Do **not** just remove the `transactional-runtime` feature: PG currently imports types under it, so that would cause broken builds rather than achieving modularity.

## Windows Registry P0 evidence (2026-11-07)

The running Windows service `OrdivonRuntimeR6Candidate` (PID 7276 at inspection) belongs to an older source tree (`73196dc...`) that lacks the Linux PG-native entry point and still contains SQLite Registry implementation. A bounded file inspection found `C:\ProgramData\Ordivon\RuntimeCandidateR6\registry\registry.sqlite3` with **251,088,896 bytes**, last modified **2026-11-07 13:25:53 UTC**. That first file-enumeration Job finished with exit code 1 after producing those file facts, so this is a partial, not comprehensive Windows storage survey.

The independent `OrdivonRuntimePostgreSQL18` service is running, but there is no observed Windows Runtime PG-admission/readback/reconciliation cutover. Do not delete the Windows SQLite file on this evidence. P0 path: port the PG-only storage contract while preserving the native Windows SCM/Job Object supervisor; qualify one writer, execution-replay, cancel, terminal readback and crash recovery; switch endpoint consumers; then retire the R6 candidate name/path and old SQLite files. Do not change Windows service identity ahead of the approved native PG release.

### Windows live SQLite write correlation

A second `windows_native` Runtime execution (`job-01a1b631-dfc2-7e71-80d7-550c4914eda0`) succeeded and re-read the same Registry file. It now measured **251,170,816 bytes** with mtime **2026-11-07 13:28:04.4129877 UTC**, a growth of **81,920 bytes** since the preceding observation, during new native Runtime Job activity. This materially strengthens the conclusion that the Windows Runtime remains SQLite-backed. The observation is correlated evidence, not an independent SQL transaction trace. Do not retire the Windows file until native PG writer and readback are proved in production.

## Legacy trace retirement and remaining large subtree

An additional exact-path cleanup Job `job-01a1b634-0b11-72d7-942e-cd2e06020f40` deleted four unreferenced legacy trace files after checking both PG process file-descriptor sets, inactive legacy timers, immutable file identities, and absent file openers: `runtime-trace.jsonl` (59,341,977 bytes), `runtime-trace.jsonl.1` (67,108,711), `runtime-trace.jsonl.http.jsonl` (43,598,344), and `runtime-trace.jsonl.http.jsonl.1` (67,108,641). Total additional logical removal: **237,157,673 bytes**. Together with the earlier SQLite file, exact removed file byte lengths total **6,403,243,305**; this is not a measured disk-space delta.

The initial 8-second bounded `du` inventory timed out. Subsequent complete top-level census established **428,509** uniformly named `attempt-*` directories; no nested mountpoints and no open-file-descriptor consumers were observed. Both active Linux Runtime processes used native PG and external Store Roots; legacy SQLite lifecycle/storage-pressure timers were inactive. After exact root/consumer checks, Job `job-01a1b659-24d0-725d-b957-8d62a77f934c` atomically renamed only the old `attempts/` subtree to `/var/lib/ordivon/retired/runtime-registry-attempts-20261107`, then three bounded removal Jobs deleted all 428,509 historical Attempt directories (500 + 30,000 + 398,009; final Job `job-01a1b65c-54e7-70ea-9f7c-962e2a0a7ae4`), using `rm --one-file-system` on explicit batch paths. The retired root was then removed. Independent readback Job `job-01a1b660-816f-701f-92ba-480dd1ceae20` confirmed both old and retired Attempt paths absent and both PG Runtime services active. The latter two large batches measured roughly 20.8 GB additional available filesystem space in their respective snapshots, not a globally exact recovered-byte guarantee. After a further installed-service/configuration literal-reference scan and `fuser`-negative readback, exact-path Job `job-01a1b666-f003-76c1-a129-be9f258b85f2` deleted the two final obsolete files `admission.lock` (0 bytes) and `dogfood-latest.json` (1,461 bytes), then removed the empty `/var/lib/ordivon/registry/` root. A subsequent fresh `runtime.describe`, `job.list`, and `workspace.get` succeeded on the current Linux PG Runtime. The Windows active SQLite Registry was not touched.

## Second-pass PG modularization (source-only, 2026-11-07)

The 1,504-line `crates/ordivon-runtime-core/src/runtime/pg_runtime.rs` mixed durable PG coordination with Workspace methods, public Job APIs, Artifact projection, and node discovery. The code was **physically split without public API or SQL contract changes**, keeping the root `PgRuntime` as the single implementation:

- `runtime/pg_runtime.rs` — PG configuration, writer qualification, internal attempt/reconciliation/project logic; 600 lines after extraction.
- `runtime/pg_runtime/node_query.rs` — public discovery and scoped Job listing (134 lines).
- `runtime/pg_runtime/workspace.rs` — source-bound Workspace operations (210 lines).
- `runtime/pg_runtime/job.rs` — Job admission/observation/cancellation/get (466 lines).
- `runtime/pg_runtime/artifact.rs` — digest/length bounded Artifact reads (119 lines).

The 7 native `pg_vertical` tests are **ignored by default**. This pass explicitly enabled them in a disposable local PostgreSQL cluster with `cargo test -p ordivon-runtime-mcp --features postgres-runtime --test pg_vertical -- --ignored --nocapture --test-threads=1`: 7 passed / 0 failed / 0 ignored. The PG MCP binary also passed `cargo check --locked`, scoped Rust PG unit tests 2/2 and `cargo clippy ... -D warnings`. Passing Linux PG acceptance does not prove Windows PG implementation or production deployment. Current Cargo still transitively compiles `rusqlite`.

Human/Agent capability vs reasoning LEGO instructions are linked in [Runtime LEGO Guide](../guides/runtime-legos.md). The source module move is intentional **structure-only** refinement; `PostgresOnlyCargoDependencyGraph` remains NOT SATISFIED, and `WindowsNativePgWriter` remains NOT QUALIFIED. Future changes must not bundle these unresolved obligations into this source-only commit.

## Third-pass dependency and naming audit (2026-11-07)

A new isolated source worktree `ws-gpt6-runtime-pg-boundary-20261107-r1` was opened at commit `6de375a567a6`; the source branch is `refactor/runtime-pg-error-boundaries-20261107`. The PG-native implementation was further decomposed: `runtime/pg_runtime/reconciliation.rs` owns Attempt readback, native reconciliation and read-only Job result projection. Runtime's former `engine::map_universal_error` was extracted to storage-neutral `runtime/error/universal.rs`, shared by Engine, execution provider, host dependency and PG Workspace/Job, removing the PG error-mapping import from legacy Engine. The `rusqlite`-specific `RuntimeError::from_sql` adapter moved into `runtime/error/sqlite.rs`, conditionally compiled only for `transactional-runtime`. This preserves Runtime error codes and avoids inventing a new error taxonomy. No live production binary was replaced.

The installed Windows `OrdivonRuntimeR6Candidate` remained active and the file `C:\\ProgramData\\Ordivon\\RuntimeCandidateR6\\registry\\registry.sqlite3` continued growing (observed 255,766,528 bytes; modified 2026-11-07 14:44:06 UTC). Native Windows PG remains a P0 **unqualified** consumer; its file is not garbage. Linux remains PG-native but Cargo's current `postgres-runtime` feature still activates legacy `transactional-runtime` / `rusqlite`, so `PG_ONLY_DEPENDENCIES=FALSE`. Both are explicit unfinished obligations; source extraction must not be confused with actual storage cutover.

Directory dispositions remain consumer-driven: `runtime/error/` is now grouped by transport-neutral and SQLite-only adapters; `runtime/pg_runtime/` is grouped by one lifecycle/projection responsibility; `platform/windows/` and `packaging/` remain native operating-system boundaries. Do not rename systemd units or Windows R6 services until the installed release and caller graphs support it. Preserve the shared `/var/lib/ordivon` owner root; the legacy **Linux** Registry data root was verified removed in the preceding retirement pass, but the current **Windows** Registry remains active.

### Live Linux capacity / recovery observation

The connected Linux PG Runtime advertises `globalExecutionLimit=4`. The 2026-11-07 workspace inventory showed four active Jobs, including three older Jobs whose durable `desiredState=cancelled` but Attempt state remained `stopping` with `mechanicallyConverged=false`, one in Security and two in Finance Workspaces. Read-only `job.get` and targeted native `job.observe` verified their continued stopping state; no new Job was created by those inspections. Subsequently, the fourth active Data Owner Job (`job-01a1b678-3665-7756-b27c-fbffc66c7a74`) also entered `stopping`, leaving **four of four** Linux PG slots occupied by Attempts without observed terminal convergence. The Data Job had produced positive test output, but process exit/effect standing remains unconfirmed. Repeated `job.cancel` on the previously cancelled three Jobs returned `stopping` for two and `REGISTRY_UNAVAILABLE: native stop not confirmed` for one. These observations are **not** sufficient to declare processes dead, release their reservations manually, label them failed, or remove their workspaces. This is a **P0 Runtime control-plane liveness/recovery defect**: a full execution pool must not prevent owner-native administrative diagnosis of stuck cancellation. Investigate systemd/cgroup provider identities and PG reservation reconciliation through an owner-approved native administrative path, without inventing terminal truth. Source changes in this branch were formatted and passed PG Cargo check/strict Clippy, but new Job admission for the full physical suite and Git commit was refused with `CONCURRENCY_LIMIT` and `commitState=not_started`. Preserve `UNKNOWN` versus `FAILED` and do not manually rewrite PostgreSQL state.

## Fourth-pass OS-native process termination and capacity diagnosis (2026-11-07)

The installed Linux PG node still advertised a four-Job admission limit. Four previously committed Jobs remained nonterminal `stopping` with durable cancellation intent. A new `workspace.exec` was rejected with `CONCURRENCY_LIMIT` / `commitState=not_started`; this is a PostgreSQL admission/reservation ceiling, **not evidence that Linux cgroup CPU, memory or pids are exhausted**. The earlier `job.cancel` and `job.observe` paths had persisted/observed cancellation intent but were unable to verify native process termination.

Source analysis isolated the real owner gap: `PgRuntime::cancel` previously submitted `systemctl --no-block stop` and `PgRuntime::reconcile` normally required a Runner `result.json` before terminalizing. If the supervisor killed the Runner before it wrote a terminal file, the process could be gone while the reservation stayed active.

**Unreleased implementation in isolated Workspace `ws-gpt6-runtime-pg-boundary-20261107-r1`:**

1. `runtime/platform/linux.rs`: **reuse its existing** `systemd-run` properties `KillMode=control-group`, `TimeoutStopSec=2s`, and `SendSIGKILL=yes`. A proposed extra immediate-SIGKILL wrapper was examined and deliberately **deleted as redundant**. No custom PID recursion or additional native stop layer remains.
2. `runtime/pg_runtime/job.rs`: verify deterministic Job/Attempt→Unit ownership, persist cancel intent, and use the existing `systemctl --no-block stop` native Unit operation. When a transient Unit has already been collected, treat failed stop submission as uncertain and defer to native reconciliation, rather than concluding the process must still be alive.
3. `runtime/pg_runtime/reconciliation.rs`: when no Runner terminal result exists, require matching `runner-start.json`, systemd Unit no longer active/no pending job, matching invocation identity (when the Unit retains it), and an unpopulated **recorded cgroup**. Retain an immutable `native-stop-evidence.json` Artifact containing the observed native identity and quiescence evidence, and commit the `lost` execution state, capacity release and Artifact metadata through the **existing PostgreSQL atomic terminal transaction**. A missing Runner terminal result is explicitly not success, and a missing transient Unit without bound Runner start is never enough to terminalize. This does **not** claim that arbitrary external effects were rolled back or that the Job succeeded. An absent Unit without Runner start evidence is insufficient: dispatch could still race.
4. Human/Agent guides: distinguish kernel process-group limits (systemd/cgroup v2, Windows Job Objects) from the current arbitrary product admission count. The kernel already owns termination; Runtime owns durable idempotency, exact evidence, and PG readback.
5. Windows launcher source audit: `platform/windows/Ordivon.WindowsJobLauncher.cs` **already** calls `CreateJobObject`, `AssignProcessToJobObject`, `TerminateJobObject`, and uses `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. Preserve this native implementation; only the **Windows Registry PG migration** remains P0. The broker's independent `Process.Kill` calls concern its pinned short-lived launcher, not a new user-process-tree manager.

Official OS authority: https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html ; https://www.freedesktop.org/software/systemd/man/latest/systemctl.html ; https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects .

**Evidence standing:** source edits are staged only in the isolated dirty Workspace, not committed, not released, and not qualified by the physical PG integration suite. The installed node continued rejecting new physical Jobs at admission; `workspace.mutate` was able to update only source files and guidance. The earlier PG check/Clippy result precedes this fourth-pass kernel source change and must not be reused as validation for it. Do not change production service binaries or PostgreSQL reservations without actual native verification. Existing installed live Jobs stay `stopping` until reconciled by the installed owner.

## 2026-11-08 follow-up — formal-first native stop refinement

- Fresh `runtime.describe`, `job.list`, exact `job.get`, and `job.observe` calls still found **four** previously cancelled Linux PG Attempts in `stopping` with `active` reservations. New Linux `workspace.exec` was rejected as `CONCURRENCY_LIMIT`, `commitState=not_started`. The current connector exposes ordinary Runtime Job execution and read-only projection but no independently usable root/systemd administrative shell. Do not confuse the user's explicit authorization with an already working OS control-plane route.
- Reused systemd's existing `KillMode=control-group`, `TimeoutStopSec=2s`, `SendSIGKILL=yes`; removed an unnecessary proposed immediate SIGKILL wrapper. No custom PID/process-tree manager remains.
- Extracted production `runtime/pg_runtime/native_stop.rs::decide_native_stop` to encode the exact four-way kernel/identity evidence guard. It returns `CommitLost` **only** if the native Unit is inactive, no systemd Job is pending, Runner start identity is independently bound, and the recorded cgroup is observed unpopulated. The implementation uses the actual pure function in PG reconciliation, not a separate shadow-model function.
- Added Kani `#[cfg(kani)]` proof harness `no_lost_resolution_without_complete_native_evidence`, quantifying the complete finite Boolean/Option state space, checking equivalence to an independent propositional contract and using `kani::cover!` anti-vacuity witnesses. **UNRUN**: Kani's actual solver result has not been obtained; do not claim the proof has succeeded.
- For a no-Runner-result `lost` outcome, `native-stop-evidence.json` is written immutably and digest-registered via the **existing PostgreSQL terminal-with-artifacts transaction**; the same transaction resolves the Job and releases its reservation. The normal terminal-result projection is preserved; only the new `native_stop_evidence` variant reports `resultAvailable=false`. This is an effect-unknown execution outcome, not a proof of business completion.
- Strengthened the existing physical `pg_vertical.rs::fresh_pg_mcp_native_runner_success_and_cancel` test rather than creating redundant new test fixtures: wait for bound Runner-start identity, submit native cancellation, require terminal convergence and released PG capacity, and if outcome is `lost` require exact native stop Artifact while disallowing fake Runner result availability. The older test accepted `stopping` indefinitely and therefore could not detect the observed real-world liveness defect. This replacement is a necessary real-system consumer verification supplement to Kani, not a substitute for it.
- Formal evidence linkage is documented in `formal/README.md`; agent consumption contract updated in `AGENTS.md`, `docs/guides/runtime-legos.md`. Historical SQLite data-parity and Windows-first rollout TLA+ models remain referenced but are explicitly not active release prerequisites.
- **Release standing:** source-only changes in dirty isolated `ws-gpt6-runtime-pg-boundary-20261107-r1`, HEAD still `6de375a567a6`. No new Git commit, pull request, installed binary, Kani proof PASS, Rust compile/Clippy PASS, or physical PG test PASS can be claimed for the 2026-11-08 changes. All execution attempts this pass were refused before admission. Do not delete needed native integration tests or Windows's live SQLite Registry to make the checklist appear green.
