---
schema_version: 1
id: runtime.r3-owner-architecture-2026-11-16
title: Runtime R3 Architecture and Consumer Safety Decision Review
type: architecture
profile: engineering
lifecycle: active
source_role: canonical
visibility: internal
owners:
  - ordivon-runtime
audience:
  - builder
  - operator
  - agent
updated: 2026-11-16
summary: Source-grounded Runtime R3 owner decision candidate for external consumer reachability, PG/native execution truth, and release currentness.
evidence_status: observed
readiness: REVIEW
applies_to:
  - ordivon-runtime
related:
  - runtime.model
  - runtime.operations
  - runtime.effect-kernel
---

# Runtime R3 — execution kernel and consumer lifecycle (decision candidate)

**Review status:** owner-authored, source-backed architecture proposal. It is not a completed formal proof, a replacement MCP schema, a production update, or independent A/B/C/D/E acceptance. This review preserves existing natural owner APIs and should be revised after cross-owner falsification.

## Actual product and usage

Runtime exists to turn an authorized Agent action into an identifiable, bounded, observable native execution with retrievable outputs and safe resource disposition. Host and Harness own task and Run continuity; Domain owners judge business value. A normal Agent consumer follows Workspace → Exec → Observe → Artifact → handoff → Close. Runtime must not grow another Agent workflow engine.

The historical 2026-11-07 Runtime decomposition record (`docs/runtime-decomposition-history.md`) reported a bounded 288,604-Tool-call sample, in which `workspace.exec`, `job.observe`, `workspace.read`, `workspace.mutate`, `workspace.close`, `workspace.execPlan`, `workspace.get`, and `workspace.open` represented 92.87% of counted calls. This is a historical sample, **not** a fresh installed workload census. It supports prioritizing the common short, source-bound execution-and-observation path over a hypothetical new cluster scheduler.

## Exact evidence boundary

- Git origin/main and this worktree were observed at a4f264dcc91c7a26d62335ee76154979f8182df7 after 2026-11-16 18:12 Asia/Shanghai. Revalidate before source edits or deployments; a fixed SourceCut is not a claim of latest HEAD forever.
- At that observation, PR #2339 native durable CLOSING was MERGED at f69344e2ebc1d14a0b59595fe7a6d70891d10c4f, and PR #2367 stable WorkspaceId was MERGED at a4f264dcc91c7a26d62335ee76154979f8182df7. An independent **installed HTTP MCP** read-only `server/discover` + `tools/list` at 2026-11-16 19:10+08 (native PG Job `job-01a1e40d-bd81-70fe-9d8c-12040b4bcf93`, Host message #28434) returned 21 tools, catalog digest `sha256:83535e7a6abbc9bb7c7ec6aa6406ce680029b64bb1c931db98058f0ed94b2493`, and `workspace.open` required fields `[sourceRepo, sourceRevision]` while `workspaceId` remained optional and nullable. Current `main` source requires caller-supplied `workspaceId: String`. No effectful tool was invoked. This is a direct SOURCE→INSTALLED HTTP schema mismatch, not just a possibly stale connector declaration; a future release must recheck the actual server catalog and downstream connector currentness.
- PR #2354 triple-artifact PG release was OPEN and Ready, #2371 Windows PG readback reuse OPEN Draft, #2333 cross-DB workspace pin OPEN Draft with blocker, and #2251 competing Harness-local cross-DB lock OPEN Draft/Dirty. These are time-scoped observations.
- Linux runtime.describe observed PG native resource-aware queue, no fixed global Job-count ceiling, dynamic resources; Windows runtime.describe observed R6 native provider, global execution limit 12. Windows PG writer cutover was NOT proven.
- Prior independent real PostgreSQL 18 Harness PAUSED Run plus native Workspace.close showed the original workspace could be removed while the durable Harness Run still reopened; no Tool effect was emitted. This disproves external consumer reachability by native job vacancy, not all execution safety.
- An isolated PG18/MCP/systemd Runner/Artifact test established healthy Job completion after a corrupted candidate was skipped; source and installed fixes were not established by that scratch result.

## Architecture: six responsibilities, two existing Rust crates

| Responsibility (candidate, not a new standalone LEGO declaration) | Natural truth owner | Existing native carrier | Prohibited replacement |
| --- | --- | --- | --- |
| Contract / authority | Runtime public DTO + authenticated principal; Harness Run outside | core runtime/types.rs, authority_contract.rs, MCP contract.rs | A second public workflow/run state |
| Admission / scheduling | PostgreSQL Job/Attempt/Reservation CAS | pg_admission.rs, pg_dispatch.rs, resource_scheduling.rs, pg_runtime/job.rs + scheduling.rs | Separate scheduler, Registry, or arbitrary command replay |
| Native execution | Kernel and OS process-supervisor facts | systemd/cgroup + universal Runner; Windows SCM/JobObject | Duplicate PID walker or inferred stop |
| Observation / reconciliation | Qualified PG snapshot plus native identity-bound evidence | pg_readback.rs, pg_runtime/reconciliation.rs, native_stop.rs | Guessing Running/Terminal/Success from issued intent |
| Artifact / delivery | Digest-bound output bytes; domain acceptance remains external | pg_runtime/artifact.rs, Result/Artifact tools | Treating exit-code 0 as business completion |
| Lifecycle / release | Git workspace source; Runtime PG held resources; trusted consumer finalization; installed service & release receipts | universal/workspace/, pg_runtime/workspace.rs, native Close, ReleaseEffect/systemd operator | TTL-only workspace deletion, caller bool as consumer proof, bare copy deployment |

Six responsibilities are *logic boundaries*, not six processes, six new directories, six Crates, or a new registry. Keep the current core + MCP workspace while source and consumers are refined; retain legacy Windows SQLite only until Windows PG native writer and its consumer acceptance have actually cut over.

## Hardest kernel: external consumer reachability across PostgreSQL databases

External Harness Run records and Runtime Job/Workspace records live in distinct authoritative domains. A PostgreSQL advisory lock in one database does not serialize a separate database's transaction. Git worktree state, PG job state, and a caller's consumerReleased=true are individually insufficient evidence that all external long-lived consumers have finished.

**Design obligation, not an implemented claim:** a Run must not become tool-ready with a frozen Workspace reference until a Runtime-owned, durably observable hold has been established under the actual Runtime PG close fence. The binding should carry exact Run/grant/Workspace identity and version or equivalent natural-owner proof. A crashed preparation may leave a retained hold; safe recovery requires positive independent owner evidence, not a guessed expiry.

**Release obligation:** the natural Harness owner must supply an independently qualified terminal + output disposition/finalization observation. A trustless arbitrary Tool caller must not discharge another Run's hold by asserting consumerReleased or supplying the same principal/request ID. The complete obligation must be verified with two different PostgreSQL databases, real Git worktrees, and negative PAUSED/needs_input cases before automatic GC assumes safety.

**Close protocol candidate:** qualified external release AND no Runtime active/held Job/Attempt or unknown physical effects AND valid exact Git/source/evidence preconditions → same PG admission/close fence → durable CLOSING intent → native Git removal → CLOSED record/tombstone. A crash after Git removal but before CLOSED must be discoverable by the existing inventory even if the physical directory is absent. No second Registry, Lease Service, or cross-DB advisory-lock illusion.

SameRun resume must preserve the original FrozenGrant and Workspace identity; a replacement Workspace creates an explicit successor Run and may not replay any UNKNOWN external effect.

## Typed failure principles

- READY/STARTING/ISSUED is not proof of a running native process. RUNNING requires a positive identity-bound OS witness.
- A missing Runner result with uncertain process identity yields UNKNOWN/orphaned or reconciliation required, never an invented failure/success or automatic re-dispatch.
- A malformed individual scheduling candidate must not block other independently eligible Jobs; provider faults must become observable reasoned conditions rather than ordinary resource pending.
- Windows JobObject PID absent or failed OpenJobObject does not prove every descendant quiescent; check Breakaway flags, exact identity and inherited provider scope.
- A successfully merged SourceCut is not proof that the installed HTTP MCP, Runner, Reclaimer helper, Windows writer, or lifecycle timer is current.
- Keep runtime execution success, artifact delivery, and Host/Harness/domain semantic success orthogonal.

## Evidence-rooted decomposition (DSM diagnostic, not architecture authority)

At a4f264d, a bounded source scan found 134 Rust files, 92,097 Rust lines including tests, 74 lexical matches for use super::* and 50 include! occurrences. Highest gross bundling points: old engine.rs (20 include!), MCP server/mod.rs (9 include!), PG reconciliation.rs (7 wildcard imports), and Workspace convenience modules. These are *candidate* implicit coupling sites, not a true typed dependency matrix or proof that moving them reduces total cost.

Plan a directed typed DSM from existing Rust imports/exports, PG SQL ownership, native OS effects, and actual MCP/Harness/Gateway consumers. For each high-coupling edge decide KEEP intentional seam, MOVE responsibility, INVERT dependency, DELETE duplication or leave UNKNOWN. First reduce live PG/Native/Workspace consumer authority coupling; only after Windows PG acceptance remove old SQLite engine/registry. Do not migrate entire trees for visual symmetry.

## Priority, ownership, negative tests, and prerequisites

| Order | Decision-critical work | Responsible participants | Must be demonstrated |
| --- | --- | --- | --- |
| P0-1 | Cross-DB Run→Workspace hold/finalizer, safe and live close | A consumer contract + D Workspace/GC + B PG, Owner integrates | Real two-DB PAUSED hold prevents native close; terminal+delivered finalization eventually permits close |
| P0-2 | Broken candidate isolation and provider diagnostic conditions | B + C native witness | Bad candidate no HOL; good native Job PG terminal and artifact.read; independent provider error categorized |
| P0-3 | Crash after physical Git close and record-only CLOSING discovery | D; E validates installed GC | Recoverable from durable record without original physical worktree; unknown authorization holds |
| P0-4 | Three-artifact source-to-installed ReleaseEffect | E; Owner checks exact manifest | Server, Runner, Reclaimer bytes/MainPID/HTTP MCP/source receipt match and rollback tested |
| P0-5 | Windows qualified PG readback and native writer cutover | C native + B PG + A contract | Windows writer real SQL CAS, JobObject, process stop, Artifact, restart and only then SQLite retirement |
| P1-1 | Types, PG reconciliation and MCP implicit coupling | A/B/C per natural source files | Real consumer graph and tightly scoped refactor tests |
| P1-2 | GC No-Job, storage reclamation, performance and diagnostics | D/E | No accidental delete, bounded discovery, real before/after resource evidence |
| P1-3 | Formal TLA+/Kani and native refinement / Docs | Each owner, independently falsified | Exact model→source→installed→native consumer chain; no unrun PASS |

## Acceptance and method

Apply existing user-agents/recursive-lego-calculus and design-structure-matrix Skills, mature Parnas information hiding, assume–guarantee contracts, FMEA and CEGAR when an actual counterexample needs refinement. A LEGO declaration requiring formal status must include all 11 R2.1 coordinates; this document only identifies candidate responsibility boundaries, not freshly admitted LEGOs. Preferred action order: DELETE obsolete responsibility → REUSE internal PG/Git/OS/Runner → COMPOSE thin current API → custom implementation only if a real consumer counterexample remains.

Every proposed fix has separate evidence grades: ARCHITECTURE, MODEL, SOURCE, INSTALLED, PHYSICAL_CONSUMER. Include exact Job/Attempt/PR/SourceCut and negative controls. A native executable test can satisfy a scoped physical check without demonstrating a production binary update. Never force-close another owner's dirty or actively consumed Workspace.

## Team and review

New R3 team: Owner integration; A Contract/Consumer Graph; B PG admission/scheduling/reconciliation; C Native Linux/Windows; D Workspace/long Run/GC; E Source-to-installed release and operations. Old team actor standing does not carry new write authorization; one actual current writer per source file and PR. The Host kickoff is message #28412 and Owner ADR-0 proposal #28415 in topic:ordivon-runtime:team-reboot-architecture-r3:20261116. This file remains REVIEW until all five independent role reports and their concrete counterexamples are considered.

## Operational non-claims

No new production configuration, SQL schema, Windows PG writer, or native service was changed by preparing this review. This document must not be used as authorization to close or retire any source, PR, Job, Workspace, Artifact, or installed binary.

## New R3 cross-falsification accepted into architectural review

Fresh independent A/B/C/D/E reviews were posted to the same Host Topic as #28417, #28416, #28421, #28419, and #28418; Owner #28426 froze the six logical seams and assigned distinct source writers. They do not establish deployed success, and the exact implementation write permissions remain constrained to their source families.

**A/B schema gate:** main PG pendingReason currently emits only cause_unobserved and the MCP pg_output_contract.rs enum admits that same value. A new scheduler-specific diagnostic is an *interface change*: B may implement internal per-candidate isolation, but external enum/value and tools/list/job.get/observe/list/Gateway consumption must be jointly qualified by A before source merge. The historical scratch experiment with reconciliation_error was not a current-main implementation.

**C Windows build and native evidence gate:** main runtime/platform/mod.rs unconditionally exposes a Linux-only module using libc statfs/cgroup/inotify primitives; a Windows PG writer cannot be claimed buildable merely by adding a preflight binary. C owns the platform cfg and Windows native source seam, B owns PG terminal CAS. The existing Windows C# launcher DescribeProcessOwner uses GetExitCodeProcess == STILL_ACTIVE(259) to infer liveness; Windows may also legitimately exit with status 259, so this is a source-level ambiguity. Reuse the already present native WaitForSingleObject mechanism with an appropriately authorized SYNCHRONIZE handle, exact PID and process-birth identity, and an isolated exit-259 negative control. Do not treat this source hypothesis as an installed failure before the physical Windows experiment.

**D post-merge native recoverability:** #2339 already persists CLOSING and supports exact-id recovery, but list_open_workspace_record_inventory currently enumerates physical worktrees and omits records_root-only CLOSING once Git removal has completed. The new D owns that existing inventory/record discovery patch; the old implementation is not absent. Consumer certification and record-only liveness are separate independent invariants, not grounds to create another general GC service.

**E installed release observation:** independent current systemd readback found installed PG Server SHA 3c098091..., Runner SHA 1f09ef4d..., helper SHA a5fa3c8e..., while main helper SHA is 20f179e6... and the Root configuration still enumerates two binaries with no includePgReclaimer flag. #2354 at head 72d8d8c had nine successful checks in E's latest live readback but remained OPEN. The exact protected merge, Root effective installer path, three-file candidate prepare, ReleaseEffect, live /proc MainPID and helper/Runner readbacks remain the real source→installed gates.

**P0 order after the first independent reviews:** (1) external Run hold-before-effective-Grant and authenticated finalizer/Delivered; (2) independent record-only CLOSING inventory/liveness repair and precise GC HOLD; (3) scheduler per-candidate fault isolation plus A/B public-schema parity; (4) release triple-manifest plus installed Tool Schema parity; (5) Windows native build/witness and PG writer cutover. When separate write sets are available these proceed concurrently, with source and physical acceptance independently qualified.

Review owner decision reference: Host message #28426. The original SourceCut, package count and test results retain their stated scope; this file is a review artifact and does not silently promote any pending P0 to complete.
