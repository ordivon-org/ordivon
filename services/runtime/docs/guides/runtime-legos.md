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
updated: 2026-11-19
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

## First-principles architecture: thought -> logic -> capability (2026-11-19)

Runtime is the physical effect-and-evidence kernel, not another Agent,
Host, approval authority, domain judge, or shadow process manager.

**Goal:** Given one identified, admitted operation in a source-bound Workspace,
execute under an actual OS process owner and return qualified bounded evidence;
when PostgreSQL, filesystem, and OS effects are inconsistent, preserve the
exact UNKNOWN instead of inventing completion, absence, or safe retry.

**Observed architecture:** The Core crate owns contracts, the PostgreSQL writer,
use-case logic and OS adapters; the MCP crate owns network/protocol presentation;
Git, PostgreSQL, native OS and retained file bytes own different kinds of
truth. The still-installed Windows R6 writer is not equivalent to Linux PG.
A PostgreSQL transaction cannot atomically commit with OS process launch,
Windows Job Objects, Git worktrees or arbitrary external effects.

**Change:** Remove hidden dependencies between contract validation, writer
authority, transactional decisions and physical effects. Avoid a big-bang
directory rename or a parallel framework.

### Three LEGO categories, two reasoning directions

| Category | Role | Concrete Runtime instance |
| --- | --- | --- |
| Positive Thought | Work forward from goal to necessary invariants and sufficient observable conditions | A result needs committed operation identity, kernel ownership, terminal evidence, Artifact readback |
| Reverse Thought | Start with a failed inference/counterexample, then derive missing requirements | Starting != running; cancel requested != stopped; no Result != no effect; terminal Job != every Run consumer finished |
| Logic | Reframe failure/requirements as a decision: inputs, state, rules, outputs, UNKNOWN and counterexamples | Admission/replay, scheduling, dispatch, reconciliation, consumer ownership, safe retirement |
| Capability | Carry the decision on a mature concrete substrate, with explicit interface and truth owner | PostgreSQL tx/CAS, Git worktree, systemd/cgroup, Windows Job Object, native Runner, SHA-256 files, MCP |

A LEGO is a contractable responsibility, not automatically one function,
Tool, file, Agent, Skill or proof document. Use the existing typed R2.1
fields only for a formally declared/admitted LEGO; do not duplicate registries.

### Essential questions and current implementation

| Question | Logic LEGO and output | Capability carrier (actual source path) |
| --- | --- | --- |
| Which exact source and Workspace? | Identity, snapshot/host dependency, consumer grant/close fence | universal/workspace/, runtime/pg_runtime/workspace.rs, claim.rs, Git |
| Who submitted what, and is it a replay? | Transport auth -> request normalization -> issuer and writer qualification -> idempotent admission | MCP access_auth.rs/pg_auth.rs; runtime/admission_validation.rs; pg_admission/input_contract.rs, writer_authority.rs, pg_issuer_guard.rs and pg_admission.rs |
| Can execution be placed? | Resource-fit, owner fairness, actual reservation vs UNKNOWN | resource_fit.rs, resource_scheduling.rs, pg_runtime/scheduling.rs, PG and kernel counters |
| Did execution physically start? | Dispatch generation, native process identity, exact immutable Runner binding | pg_dispatch.rs, pg_runtime/job.rs, universal/runner.rs, runtime/platform/linux.rs; runtime/windows.rs and Windows launcher |
| Has stop or terminal happened? | Stop intent != stop evidence; terminal transition/CAS; reconcile ambiguous state | pg_runtime/job/cancellation.rs, pg_runtime/native_stop.rs, pg_runtime/reconciliation.rs, pg_admission/terminal_contract.rs and cancel_contract.rs |
| Can a caller consume output? | Result identity, bounded Artifact manifest and digest-verified readback | pg_readback.rs, pg_runtime/artifact.rs, universal/resource_receipt.rs, artifact files |
| Can a Workspace/resource be removed? | Current Job and logical Run consumers all released, exact native close/retention | pg_runtime/workspace.rs and claim.rs, workspace_headroom.rs, Git worktree |
| Is a released binary installed and usable? | Source/manifest -> ReleaseEffect -> actual file/process -> consumer result | pg_runtime/release.rs, release scripts, systemd/SCM, actual Runtime Job and Artifact |

### Cross-database Run Claim release: source contract, not Installed proof

A Runtime workspace.claim.reserve protects the physical Git Workspace even
after its last Job exits. Its principal + clientRequestId is a **recovery
coordinate**, not a trustworthy statement that an external Harness Run or a
recipient finished consuming the output. An authenticated caller with the
original Claim owner identity can otherwise call workspace.claim.release
before Harness Run terminal/recipient Byte ACK; ordinary workspace.close
can then remove unique material. This happened in a real disposable Run +
installed Runtime native test, not just in the formal model.

The separately authenticated /harness/mcp route exists in source, not
automatically in the installed service. Ordinary /mcp **always denies**
workspace.claim.release, including when dedicated credentials are not
configured; both tools/list and the actual raw tools/call enforce the boundary.
A caller-supplied key or Agent actor label is never a release credential.
The source change is staged on the protected ordinary-default-deny PR and
must be verified against the exact installed service before claims about
production safety.

**Two different capabilities must not be coupled:** a Claim finalizer
requires original Runtime PostgreSQL Workspace owner state, whereas a Harness
Job issuer requires the optional same-database source-currentness SQL function.
Runtime PG and Harness PG may reside in the same physical PostgreSQL cluster
while remaining separate databases. The dedicated route requires
ORDIVON_PG_HARNESS_TOKEN_FILE and ORDIVON_PG_HARNESS_PRINCIPAL
(operator-owned, mutually distinct from ordinary authentication). With no
ORDIVON_PG_HARNESS_ISSUER_SCHEMA it enters Claim-only mode, allowing exactly
workspace.get and workspace.claim.reserve/get/release. The route cannot open,
close or execute Workspaces, cancel Jobs, or apply releases, even via raw
tools/call. When the issuer schema is present, the original same-PG Harness
Job issuance/dispatch fencing mode remains unchanged. Do not copy Harness
tables into Runtime merely to issue or release a physical Workspace Claim.

**Cutover requires consumer migration:** Claims created under the old ordinary
principal are not automatically transferable to the new dedicated principal.
A correctly installed trusted Harness coordinator must use the dedicated
identity from original Run birth, restore the same key on restart, and only
release after independently verifying original Run terminal, delivered
recipient bytes and Native OS effects drained. A dedicated bearer by itself
does not prove any of these conditions. In particular, ordinary trusted_local
Jobs currently execute as host root and may read root-only credential files:
two distinct root-owned Bearer files do not protect against untrusted root code.
Normal Agent compute must use a genuine separate native OS principal or
capability boundary before treating a separate finalizer token as a hard
inter-Agent security guarantee. Keep automatic destructive GC on HOLD until
that real control and original Domain evidence are qualified. A human-initiated
explicit abandon flow must not be mislabeled as successful delivery.

### PostgreSQL ordinary Agent execution: opt-in Native contained profile

The original PG Runtime uses the SAME PostgreSQL Job/Attempt and Linux
systemd Runner for both execution profiles. Default remains trusted_local,
which is intended only for explicitly authorized high-control operation.
On this source branch, local_linux also accepts explicitly selected
contained_local, and runtime.describe advertises the source capability.
This is NOT proof of an installed or granted production capability.

Reuse the existing systemd ProtectSystem=strict, private mounts/network,
NoNewPrivileges, zero capabilities, inaccessible /etc/ordivon and the
existing original PostgreSQL Job/Attempt/Artifact journal. Runtime creates
Workspace-owned private HOME, temp, build and package caches BEFORE durable
PG dispatch, because systemd BindPaths cannot mount nonexistent sources.
Cache subdirectories themselves are resolved through the existing
no-follow native directory handles, preventing an original Agent from
planting a symbolic link and turning a later root-owned bind into host
path access. Caller-supplied cache mount roots (HOME/CARGO_TARGET_DIR/etc.)
fail closed
before any new Job admission, rather than re-exposing arbitrary host paths.

The original Git Common Directory is bound READ-ONLY even for default-scope
contained requests, so the actual worktree Git identity can be read, and
a nested Workspace-owned Git repository can be created/committed. Direct
commit into the shared original worktree is NOT qualified; its metadata is
deliberately not made writable to a normal contained Agent. Original
source commits require a separate consumer-qualified ownership effect.

The opt-in true PostgreSQL18/native MCP E2E tests original Job launch and
terminal Artifact bytes, checks boolean inability to read installed
control-plane credentials and proc-root escape paths, and rejects hostile
caller-selected cache mounts without any PG Job/Attempt side effect.
Contained source uses UID0 within an isolated OS namespace: it is an
accidental-access barrier, not malicious host-root isolation. Existing
trusted_local remains an administrator-equivalent grant; a normal
Coding/Research agent cannot be claimed isolated until original grants
select contained_local and OS/native consumers are actually installed.
Domain Run Completed/recipient ByteACK/native effect drain are distinct.

### Actual PG Admission module ownership (current source)

This is an incremental reorganization inside the existing owner, not a
second runtime or a completed fleet migration.

| Source directory or module | Stable responsibility | Forbidden dependency |
| --- | --- | --- |
| crates/ordivon-runtime-core/src/pg_admission/input_contract.rs | Pure JSON/field contract; unambiguous object keys | Database connection, OS process execution |
| pg_admission/writer_authority.rs | PostgreSQL schema identification, physical epoch and qualified relational constraints | Job admission business transaction or a new approval system |
| pg_admission/terminal_contract.rs | Pure Attempt terminal state decision, Artifact manifest; original Kani proof stays adjacent | PG commit, OS stop |
| pg_admission/cancel_contract.rs | Cancellation immutable identity and DTO | Process termination |
| pg_admission.rs | Small public facade: stable DTO exports and owner module composition | New Authorization DB, SQL transaction implementations |
| pg_admission/admission.rs | Atomic new Job admission, idempotency and shared transaction linearization | Runtime OS launch, user-authentication parsing |
| pg_admission/release.rs | Runtime ReleaseEffect binding/qualification, reusing the original admission transaction | A second Release store or process publisher |
| pg_admission/readback.rs | Read-only PG admission confirmation after uncertain reply | Reissuing a physical Job |
| pg_admission/terminal.rs | One PG Attempt terminal/registered Artifact commit | Domain task completion |
| pg_admission/cancellation.rs | Cancel intent and exact PG readback | Assuming OS Process has stopped |
| pg_admission/retry.rs | Bounded retry of definitely aborted PostgreSQL transactions | Retrying systemd/JobObject effects |
| pg_admission/contract_tests.rs, live_pg_tests/*_cases.rs | Pure contracts and domain-scoped PG18 behavioral tests | Positional source files, public authority declarations |
| runtime/pg_runtime/ | PG-bound Job/Workspace/scheduling/reconciliation use-case composition | Harness goal/Run semantics |
| runtime/pg_runtime/job/cancellation.rs | Existing PG Job cancel use-case: authorize -> persist intent -> native stop request -> reconciliation/readback | HTTP principal decoding, invented native stop implementation, semantic task completion |
| runtime/platform/ and universal/ | Native Linux/Windows execution and generic Git/Runner/FS capabilities | Upstream Agent reasoning or policy hierarchy |
| ordivon-runtime-mcp/src/ | Protocol presentation and existing authenticated principal mapping | Reimplement PG Job state machine |
| runtime/engine/, runtime/registry/ | Gated SQLite legacy path; retain only while installed Windows needs it | Linux PG production writer |

**Concrete code move (PG Admission R10):** The former 3,816-line
pg_admission.rs contained four distinct PostgreSQL effects, readback/retry,
and over 2,700 lines of colocated physical tests. Its 71-line facade now
delegates the original SQL transactions to separate admission, release,
readback, terminal, cancellation, and retry modules; 25 native PG18 tests are grouped
by behavioral domain with a common disposable fixture. Public Rust DTOs,
method signatures, transaction boundaries, event schema, and OS ownership
remain unchanged; source-only modularization is not an installed release.

**Test quality:** Use the native Cargo harness, disposable PostgreSQL 18,
and explicit fail-closed missing-DSN behavior to validate admission,
cancellation, artifact terminal, issuer currentness and Windows evidence.
Never require a named test to remain in a specific Rust source file or use
a fully qualified implementation-module path as an execution identity.
The Windows witness remains mandatory: exactly one matching business
test must run and pass. Existing historical planning snapshots are not
runtime authority or proof of today's installed backend.

### Dependency and retirement rules

1. MCP authenticates and decodes a request; Runtime logical contracts decide
   identity, admission and resolution; PostgreSQL persists; the native provider
   launches/stops; evidence projection reports what can really be established.
   Pure contracts may not connect to PostgreSQL or invoke an OS subprocess.
2. Cloudflare Zero Trust covers upstream ingress, not PG writer-epoch or
   local OS file/process authority. Preserve existing real authentication and
   authorization boundaries, without inventing another AuthZEN or Owner veto.
   The Windows policy / legacy MCP request-auth split is in source PR #2457,
   OPEN at this audit, not assumed merged or installed.
3. Evidence is owned at its origin: Git (source), PG (Job/Attempt/cancel/CAS),
   systemd or Job Object (process), files (Artifact bytes), Harness (Run
   continuation). A missing OS result does not justify a new physical attempt.
4. Do not erase legacy SQLite solely on source-level PG compilation.
   The key unresolved Windows positive consumer is trusted pre-close
   JobObject drain -> current PG Attempt terminal -> accessible Artifact.
   OpenJobObject=NotFound after closing is not a positive drain witness.
5. Separate SOURCE, MODEL, CODE, INSTALLED and PHYSICAL standing.
   Prefer removing superseded code over adding wrappers, checks, ledgers or
   redundant tool aliases. An additional module must replace a known
   coupling and have an identified real consumer.

## Workspace lifecycle and current stock audit

The existing WorkspaceConsumerCloseR1 TLA models and native Runtime provider
remain unchanged. Current stock-only source audit, refactor decisions and
recorded evidence are in the repository-root path `docs/architecture/audits/2026-11-10-brownfield/AUDIT_SCOPE.md`.
Earlier consumer-expansion plans are historical and do not authorize new
runtime features, tests or interfaces.

**Installed-state check (2026-11-17, UTC+08):** the live Linux `ordivon-runtime.service` is PostgreSQL-native, but its running Server bytes must be identified separately from `origin/main`. The installed `ordivon-runtime-lifecycle.timer` was `disabled` and `inactive` at this check; the four-hour minimum quiet period does **not** imply an enabled collector or safe automatic close. The connected Linux PG Runtime exposes `release.get` but not `release.apply`; the source PG `release.rs` is read-only and the root-owned operator is a separate physical deployment authority. Windows R6 remains a distinct installed execution stack, not an authenticated PG Writer cutover. Recheck these facts at the actual node before operational decisions.

## Capability LEGOs — current native consumers

| Capability | Source / actual owner | Preconditions and observable postcondition | Mature substrate / evidence |
| --- | --- | --- | --- |
| Git Workspace identity | `universal/workspace/`, `runtime/pg_runtime/workspace.rs` | Exact source revision and workspace identity → observed source-state digest and a fenced working tree; close must reject active/held consumers | Git worktree, source-state readback |
| PG Job admission / replay | `runtime/admission_validation.rs` (storage-neutral request validation), `pg_admission.rs`, `pg_dispatch.rs`, `runtime/pg_runtime/job.rs` | Qualified PG writer epoch, authenticated principal, exact operation identity → committed Job or exact replay; never create a duplicate because reply delivery was lost | PostgreSQL transaction and durable query |
| Native physical execution | `runtime/build_target_contract.rs` (shared Cargo presentation choice), `universal/runner.rs`, `runtime/execution_provider.rs`, `runtime/platform/linux.rs`, `runtime/windows.rs` | Admitted Job, committed provider identity → observed Attempt or explicit ambiguity | systemd/cgroup (Linux), SCM/Job Object (Windows) |
| Reconciliation / cancellation | `runtime/pg_runtime.rs`, `runtime/supervisor.rs` | Persisted Job plus live provider evidence → justified terminal state or UNKNOWN; cancellation intent is not proof the process stopped | identity-bound process evidence |
| Artifact observation | `runtime/inspection_contract.rs` (storage-neutral Job/Attempt readback types), `runtime/pg_runtime/artifact.rs`, `universal/resource_receipt.rs` | Existing registered Artifact/digest → bounded verified read; target success is not task completion | SHA-256, owned receipt |
| Runtime release | `runtime/pg_runtime/release.rs` (PG ReleaseEffect read-only projection), `scripts/ordivon_runtime_pg_operator.py` (native install operator); `runtime/engine/release.rs` is legacy | Qualified candidate manifest and deploy authority → external deployment receipt, not inferred binary exit | existing receipted release path |
| Operator retention | `scripts/ordivon-runtime-pg-reclaim` (installed helper; the systemd timer can be disabled), `runtime/workspace_headroom.rs`; legacy SQLite operator scripts remain separate until retired | Complete ownership and absence of current/held consumers → selective Workspace/cache retirement | Git worktree removal, systemd native directory lifetime |

### Source layout of the PG implementation

`runtime/admission_validation.rs` owns shared request-shape validation for PG and legacy Engine. `runtime/inspection_contract.rs` now carries shared Job/Attempt evidence projection shapes; SQLite-only inspection queries remain under `runtime/inspection.rs` and are not PostgreSQL execution authority. `runtime/build_target_contract.rs` owns the shared Linux Cargo presentation selection, and `runtime/workspace_headroom.rs` owns the shared filesystem capacity gate. The `runtime-contract` Core Cargo feature now separates shared execution contracts from the legacy SQLite Registry. A source-only Core build using `cargo check --locked -p ordivon-runtime-core --no-default-features --features postgres-registry-admission` compiles `PgRuntime` without linking `rusqlite` (verify with Cargo's dependency graph). The MCP Cargo dependency uses Core `default-features = false` and `features = ["runtime-contract"]`; enabling `postgres-runtime` selects Core `postgres-registry-admission` without selecting the legacy `transactional-runtime`/`rusqlite` path. This is a **source Cargo-feature claim**, not proof that the current Linux installed binary has the same SourceCut or that Windows has a native PostgreSQL Writer. Qualify installed bytes, effective settings, and actual consumers separately. `runtime/pg_runtime.rs` owns PG configuration and writer qualification. Its submodules separate `node_query.rs` (discovery/list), `workspace.rs` (Workspace operations), `job.rs` (admission/observe/cancel/get), `reconciliation.rs` (Attempt readback, OS reconciliation and result projection), `native_stop.rs` (pure kernel-evidence admission classifier with Kani proof harness), and `artifact.rs` (Artifact projection). Runtime errors use `runtime/error/universal.rs` for executor-to-domain mapping, while `runtime/error/sqlite.rs` is a gated **legacy** Registry adapter. PostgreSQL clients must use the neutral error mapper rather than importing the legacy Engine. The PG-only MCP source feature boundary is separate from the legacy SQLite-backed MCP feature; use `cargo tree --no-default-features --features postgres-runtime` for a new exact dependency-graph verification if relevant inputs change. Windows PG-native Writer qualification and installed-process source parity remain independent requirements.

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

### Windows PostgreSQL Attempt witness (source-only, no cutover)

The existing native Windows Launcher/Job Object and the PostgreSQL Job/Attempt
schema are composed through `pg_windows_evidence.rs`. The **PG-only** Core
binary `ordivon-runtime-windows-pg-preflight` can inspect one exact qualified
Writer/Job/Attempt/Bundle identity without starting a service, allocating a Job
or changing PostgreSQL. It is intentionally separate from the legacy
SQLite-enabled MCP binary.

The explicit phase is `no_launcher_witness`, `launcher_witness`,
`target_witness`, or `result_witness_pending_os_reconciliation`. A
target-writable `result.json`, a stale/reused PID, a matching process birth
FILETIME or a signalled launcher handle **cannot individually prove** that the
whole Windows Job Object has terminated, that PG terminal CAS was committed,
or that another consumer has accepted the result.
`terminalProven=false` remains mandatory for this source-only reader;
missing/ambiguous native owner evidence must remain UNKNOWN. For an unresolved
PG Job, the read-only witness must bind to its exact `current_attempt_id`,
not merely `ORDER BY attempt_number DESC`. Resolved Jobs may inspect historical
Attempts only when their live current-Attempt pointer has been cleared.
An inconsistent snapshot is a failed qualification, never an execution grant.
The same PG-admitted Attempt name also drives a **read-only Win32 Job Object**
`OpenJobObjectW(JOB_OBJECT_QUERY)` / `QueryInformationJobObject` observation.
`populated`, `empty`, `not_found` and `unknown` remain separate:
an empty object is only a momentary process-count observation; missing object
handles or unavailable Session/ACL truth are **not** terminal evidence.
The explicit PE `--self-test` checks this native kernel readback on Windows
using a unique empty disposable Job Object and closes its handle; it does not
connect PostgreSQL, dispatch a Job or qualify the installed Windows PG Writer.
When invoked as an already owned Windows Runtime target, it also reports the
calling process's immediate enclosing Job Object population through the same
kernel accounting primitive. This diagnostic is **not** evidence of PG ownership
or a service-account qualification.

Verification: `cargo test -p ordivon-runtime-core --no-default-features
--features postgres-registry-admission pg_windows` checks bounded pure cases;
`python3 scripts/pg_disposable_physical.py` runs the complete native PG18 test inventory plus
the independent Windows PG reader against a disposable PostgreSQL 18 schema;
`scripts/tla-formal check-windows-pg-attempt` and
`falsify-windows-pg-attempt` check the finite owner/exit model and required
counterexamples. Cross-target `cargo check` qualifies only Windows PE
compilability, **not** Windows-native execution. Actual Windows PG Writer,
native launcher, process recovery, Gateway consumers and installed release
remain separate OPEN obligations; do not switch or delete the live SQLite
Registry on the strength of these checks.

The three PostgreSQL verification tasks reuse the same native Cargo library-test
selection and exact execution-witness comparison:
`mise run test:postgres-registry:disposable` creates an isolated fixture;
`mise run test:postgres-registry:physical` requires an explicit isolated
`ORDIVON_PG_TEST_DSN`; `mise run test:postgres-registry:stage` requires the
separate historical-stage test DSN `ORDIVON_PG_STAGE_TEST_DSN`.
Empty or wrong inventories, zero executed tests, mismatched test identities,
duplicate execution, and nonzero native exits cannot qualify. The fresh PG
lanes additionally require every named PG physical-opt-in witness from
`formal/RuntimeDispatchR1.trace-r1.json` to occur in the native inventory
and execute successfully; a nonempty remainder cannot hide a missing required
obligation. The stage lane
must select exactly its one named witness; its passing result is not a
fresh-epoch or Windows production acceptance. An operator DSN is not supplied
by default and is never inherited by the disposable fixture.

For source-level formal trace evidence, `mise run formal:verify` executes the
existing Legacy trace and the explicit PG-only profile. Query the current
implementation with
`python3 scripts/verify_formal_trace.py --native-profile pg --native-witnesses`.
The PG profile separately names always-on native code witnesses, shared typed
contracts, and compiled-but-not-executed physical PostgreSQL witnesses. Do not
substitute one profile for the other. For incremental source impact, use the
same profile plus `--impact-base <ancestor-commit> --impact-head <checkout-commit>`
and optionally `--impact-compiler`. The compiler's exact tracked PG SQL inputs,
package-directory dependency and qualified absolute/relative spellings are
bound to its source receipt. Composition consumes the positive path readsets;
external/build/dynamic closure, whole-model implementation refinement,
installed currentness, and domain acceptance remain UNKNOWN.

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

### Native Runner start versus PG dispatch intent (2026-11-15 source candidate)

For Agent progress, `DISPATCH_ISSUED` commits the at-most-once physical **intent** and means `starting`; it is not proof that a process started. The existing PG reconciler may advance the exact current Attempt to `running` and append one `RUNNER_BOUND` event only after matching the Runner-produced start identity with qualified PostgreSQL source/epoch, live systemd `InvocationID`, `ControlGroup`, `MainPID`, observed Linux `/proc/PID/stat` process birth, and committed provider digest. The same Job/Attempt CAS and held allocation reject stale versions, cancellation, replaced native processes, or terminal Jobs. Short commands can finish directly from `starting` before a positive running observation; absence of `RUNNER_BOUND` is UNKNOWN, not proof the command never ran. Partial stdout alone is not native ownership proof.

**Source-only verification (2026-11-15):** original disposable PG18 suite 19/19 including new cancellation/terminal tests, original PostgreSQL→MCP→systemd physical success/cancel consumer 1/1, full Core 514, MCP 80, strict Clippy PASS. The new scoped `formal/RuntimeRunnerBoundR1.tla` checks the positive native-witness gate over 80 reachable states and has two named negative controls (legitimate binding is reachable; removing the native proof guard violates the running invariant). The earlier `RuntimeDispatchR1.tla` uses a coarser post-dispatch `running` abstraction; neither model proves systemd or Rust/PG implementation equivalence. Installed-node acceptance and Agent consumer refresh remain independent. Consumers should observe the **same** Job via `job.observe`, never redispatch on a `starting` snapshot.

### Kernel-native liveness vs durable reservation

`globalExecutionLimit` is an **owner-reported capability**, not a kernel capacity measurement. As observed on 2026-11-15, Linux `linux-pg` reports `null` and uses an existing resource-aware persistent queue, cgroup/PSI observations, and per-Workspace access leases; Windows R6 still reports 12. Do not repeat the historical claim that installed Linux is blocked by a fixed four-slot counter. Stale `stopping` reservations, if observed, are control-plane reconciliation defects: do not impose arbitrary timeouts, inflate counters, or edit PG rows to conceal them. Reuse systemd `TasksMax`, `MemoryMax`, `CPUQuota`, cgroup v2 `pids.max`, and native process evidence for physical control. Kernel process absence is distinct from arbitrary-command business results.

## Capacity and reconciliation: Human / Agent instructions

Human: inspect the node's `runtime.describe` capacity, then `job.list` and `job.get`. If a Job has durable cancellation intent but its Attempt still shows `stopping`, use `job.observe` to obtain the installed provider's current evidence. Do not manually delete a Job reservation, kill an unrelated process by name, or treat an operator UI timeout as proof of process termination. Follow the installed supervisor/recovery contract when the state cannot converge.

Agent: on `CONCURRENCY_LIMIT` with `commitState=not_started`, preserve the original operation identity; do **not** invent a new `clientRequestId` or claim a Job was accepted. Inspect other live work only if its identity is relevant. For an already committed Job, observe that exact identity. When process state is unknown, emit UNKNOWN and cite its actual Job/Attempt evidence; capacity must not be reclaimed by guessing a terminal outcome.

## Retirement and evidence standing

The Linux Runtime has a PG-native installed process, but the PG Cargo feature still transitively includes the legacy SQLite Core. Windows still has a live, growing SQLite Registry as of the 2026-11-07 audit. Neither fact can be erased by editing this guide. See [Operator Guide](operator-runtime.md), [Agent Guide](agent-runtime.md), and the [live audit](../audits/2026-11-07-runtime-owner-audit.md).
