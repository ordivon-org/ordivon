# Runtime formal specifications

This directory contains small TLA+ models for concurrency/recovery properties that are
more important than prose-only architecture claims.

## RuntimeDispatchR1

Scope:

- durable admission precedes physical dispatch;
- one Attempt crosses the physical dispatch boundary at most once;
- ambiguous dispatch blocks redispatch until reconciliation proves absence;
- a retry is an explicit new Attempt;
- terminal evidence belongs to an already-dispatched Attempt.

Non-scope:

- business workflow orchestration;
- Temporal Workflow semantics;
- provider-domain compensation;
- semantic Task completion;
- exact implementation data structures.

The model follows the standard TLA+ Init / Next / invariant style and is intended for
TLC model checking. TLA+ is used here because the Runtime boundary is a concurrent state
machine with safety properties; this is not a new Ordivon formalism.

Traceability:
- docs/runtime.md: irreducible Runtime invariants;
- docs/effect-kernel.md: at-most-once physical dispatch and ambiguity preservation;
- docs/recovery.md: reconcile before a new operation identity;
- docs/STANDARDS_FIRST_W2_BOUNDARY_R1.md: workflow ownership boundary.

Expected model-check command once the standard TLA+ tools are available:

    java -cp tla2tools.jar tlc2.TLC -config RuntimeDispatchR1.cfg RuntimeDispatchR1.tla

A passing finite model is evidence about this abstraction, not proof that Rust code
implements it. Implementation tests must remain separately traced to these invariants.

Static review note (2026-09-19): `dispatchCount` intentionally permits `0..2` in `TypeOK` so `AtMostOnceDispatchPerAttempt` remains an independently falsifiable safety invariant rather than being true by construction. TLC execution is still required before this model is accepted as checked evidence.

- across distinct Attempt identities, no two Attempts may simultaneously be
  admitted/running/ambiguous; an explicitly reconciled **lost** predecessor may
  coexist with an independently admitted retry.

## R2.1 compositional state obligation

Use the existing TLA+ relational/transition-system math kernel. For the
finite set of Attempts, define Live(a) when an Attempt is admitted, running or
ambiguous. NoCompetingLiveAttempts requires
forall a,b: a != b => not (Live(a) and Live(b).
The existing ReconcileProvenAbsent transition marks an ambiguous predecessor
lost *before* AdmitExplicitRetry admits a fresh Attempt. Its physical-absence
assumption requires Runtime owner evidence; the model cannot certify it.

An actual TLC violation caused by adding a blind-retry transition is a
bounded falsification witness. Two physical Runtime tests are **opt-in** (root,
systemd, cgroup); they must never be represented as executed always-on CI
proof. This invariant supplements, and must not replace, the independent
TerminalEvidenceIsCommitted property and its always-on Rust test. Passing TLC
does not establish Rust-to-TLA refinement, external effect idempotency, or
semantic Work acceptance.

## Scoped progress obligation

TLC additionally checks the temporal property ProgressToFirstDecision under
FairSpec. Under weak fairness for admission, dispatch, and either terminal
observation or explicit ambiguity, the model eventually exposes a first
decision. An ambiguous dispatch counts as an explicit block, NOT success.
Without fairness, the stuttering model cannot guarantee this liveness.

CHECK_DEADLOCK FALSE remains intentional because terminal states stutter.
The finite Attempts model is not an actual Runtime retry quota. The model
does not prove real-world deadlock freedom, reconciliation progress, bound on
completion time, external effect idempotency, or Rust-to-TLA refinement.

## CEGAR-inspired negative control: prove this invariant is falsifiable

The Runtime Owner's existing `mise run formal:verify` also executes
`scripts/tla-formal falsify` on an ephemeral **copy** of the same TLA+ model.
It introduces exactly one forbidden transition: admit a replacement Attempt
while an earlier physical dispatch is still ambiguous. The pinned upstream
TLC must return a **named** `NoCompetingLiveAttempts` counterexample.
Successful Java exit, model syntax errors, unrelated failed invariants,
an unknown outcome or an absent counterexample all **fail closed**.

This is a model-level negative control, not proof that the Rust implementation
has such a transition and not a complete CEGAR abstraction-refinement cycle.
A real Runtime defect must be shown feasible in its concrete state/authority
boundary before using the trace as implementation evidence. An abstraction
refinement is justified only after proving the abstract trace spurious and
preserving concrete behaviors. No new solver, model, registry or state is added.

## Reproducible toolchain gate

The command-line checker is pinned in `formal/toolchain.lock.json`. The repository does
not commit the upstream JAR.

Bootstrap is the only networked step:

    scripts/tla-formal bootstrap

Model checking is then offline/repeatable from the digest-verified cache:

    scripts/tla-formal check

An isolated Runtime Workspace can use a previously materialized trusted JAR without
duplicating or downloading it into every Workspace:

    ORDIVON_TLA_TOOLS_JAR=/absolute/path/to/tla2tools-v1.7.4.jar scripts/tla-formal verify
    ORDIVON_TLA_TOOLS_JAR=/absolute/path/to/tla2tools-v1.7.4.jar scripts/tla-formal check

The override must be an absolute regular non-symlink file, and both upstream-locked
digests are checked before execution. Runtime callers should additionally bind the
same path and locked SHA-256 through `execution.hostDependencies` to fence admission
and runtime-host-namespace path continuity. The wrapper's digest checks alone do
not establish a race-free immutable input or prove Java consumed the committed bytes.
`bootstrap` still writes only to the project's ignored local cache, regardless of
the override; a fresh checkout does not require bootstrap if an external pinned JAR
is available.

The lock records the upstream release URL, the SHA-1 published on the official v1.7.4
release page, and the SHA-256 measured only after that upstream digest matched. The
cached JAR lives under ignored `target/` state.

First accepted finite-model result (2026-09-19):

- TLC 2.19 / TLA+ tools v1.7.4;
- Attempts = {A1, A2};
- 25 states generated;
- 20 distinct states;
- complete state graph depth 9;
- zero invariant violations.

This result is evidence for the bounded abstraction only. It is not a proof that the Rust
implementation refines the model; refinement/traceability remains a separate gate.

Current expanded native verification (2026-10-25): the **same** TLA+ model
with Attempts = {A1, A2, A3} explores two consecutive explicit retries,
generating 73 states (56 distinct) and finds no safety/liveness violation.
The Runtime source-bound trace gate now refuses a future configuration
silently shrunk below three distinct Attempt identities, even if its SHA-256
is refreshed. No new formal DSL, extra checker or provider is involved.

The three-Attempt exploration is still bounded abstraction evidence, not an
unbounded induction proof, a retry quota, external effect exactly-once proof,
or machine-checked Rust refinement. The historical two-Attempt acceptance
above is preserved as a dated receipt rather than overwritten.

## LEGO R2.1: evidence is typed by execution boundary

Reuse the current upstream TLA+/TLC transition-system checker for the **finite
model**; use Rust Registry CAS and orphan-state tests as **always-on owner
implementation witnesses**. Do not treat either as a mechanized refinement of
Rust into TLA+.

The two root/systemd/cgroup integration tests remain present and executable
with explicit opt-in, but carry **physical-opt-in** evidence status because
Rust ignores them in normal CI. The source-bound trace gate now rejects an
ignored test as an always-on proving reference. Its PASS establishes that
the expected named obligations and test identities exist, not that conditional
physical tests were executed or that a deployment accepted the behavior.

Mathematical substrate: TLA+ state transitions and invariants, Rust
versioned CAS semantics, and an assume/guarantee obligation at the
ExecutionProvider boundary; no new Ordivon DSL, interpreter, global LEGO
registry, or second test runner is introduced. Model safety, unit-test
acceptance, optional physical acceptance and domain completion remain separate
facts.

## R2.1 consumer-slice: terminal evidence provenance (TLA+ + Rust)

The mature transition-system kernel supplies states, steps, invariants, weak
fairness and finite-state counterexamples; no new Ordivon algebra or verifier
is created. The added `TerminalEvidenceIsCommitted` is an explicit
safety obligation:

```tla
jobState = "terminal" =>
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "terminal"
    /\ reconcileState = "committed"
```

The invariant is deliberately separate from `TerminalAttemptWasDispatched`:
physical dispatch and committed terminal evidence are different predicates.
The exact Runtime Owner's
`terminal_evidence_requires_result_finish_matching_resolution_and_no_current_attempt`
test supplies an implementation-level negative-control witness. The
existing trace gate binds the invariant and test symbol by current source
identity; neither it nor the bounded TLC result proves Rust-to-TLA+
refinement. Actual provider completion and semantic Work acceptance are
outside this model. Consumers of terminal standing must still enforce their
domain acceptance predicate.

## LEGO R2.1: selected-live and held-orphan identity semantics

The bounded Runtime dispatch model now distinguishes selected live Attempt
(admitted/running/ambiguous with currentAttempt identity) from a physically
orphaned and held Attempt (orphanedHeld, no current pointer, reconciliation
still required). These are distinct legal safety representations. The
NoDetachedLiveAttempt safety condition forbids an unfenced detached live
Attempt; HeldOrphanIsFenced prevents a held orphan from becoming a new
dispatch-eligible Job state without explicit reconciliation. The actual Rust
owner tests confirm both current identity after initial admission and the
legal Orphaned pattern of current_attempt_id=None plus HeldOrphaned reservation.

A prepatch negative-control mutation left a detached ambiguous Attempt, with
no retry enabled. The previous TLC invariant set PASSed (11 distinct states).
The new selected-live invariant rejected it (TLC exit 12). A separate held
orphan state is needed because native Rust demonstrated that an orphan can
legally have no current pointer while retaining its capacity reservation.
Actual Orphaned terminal evidence may occur before confirmed physical
dispatch. Therefore the revised model permits orphanedHeld from admitted
or running, and deliberately does not demand dispatchCount=1 for all
orphaned states. A minimal separate heldReservation Boolean represents the
physical capacity fence (not a new general ledger or scheduler).
HeldOrphanIsFenced enforces equivalence between the held bit and the
abstract orphaned state, while preventing admission/retry until explicit
reconciliation. The Boolean models one Job and cannot certify global
capacity accounting.

Independent upstream TLC negative control: an orphan transition sets
orphanedHeld but incorrectly omits the heldReservation write. The same
mutated model PASSes with the original invariant set (67 generated,
45 distinct states; exit 0); selecting HeldOrphanIsFenced produces an
invariant violation at state 5 (exit 12). This catches missing recovery
fencing as a state invariant rather than waiting for a subsequent bad
retry. The admission-originated Orphaned test remains a necessary
physical witness because modeling a dispatchCount of exactly one
for every Orphaned state would be incorrect.

The official SHA-256-locked upstream TLC checks abstract rules only, not
Rust/SQLite/Windows/Linux refinement, global concurrency capacity or actual
domain outcomes. Preserve always-on Rust witnesses and conditional physical
acceptance rather than replacing them with synthetic model claims.

## Foreign result observation / exact matching recovery (2026-10-25, CEGAR)

**Typed problem**: `RUNTIME-RESULT-FOREIGN-RECOVERY-01`, class `EVIDENCE_IDENTITY / ABSTRACTION_RECOVERY`, natural Owner `services/runtime/formal`. The previous `ObserveResultEvidence` action admitted `none → foreign` and `none → matching` but no `foreign → matching` for one unresolved Attempt. Consequently, a foreign result observation became an irreversible fact in the *abstract model*, even if a subsequently available authoritative matching result should qualify the Attempt. This is not by itself evidence of a real Runtime bug.

**Refinement**: The native TLA+ model now provides `CorrectForeignResultEvidence` for an unresolved selected Attempt in `running` or `ambiguous` standing, preserving the distinct dispatch/Job/reconciliation state while changing only the result evidence from `foreign` to `matching`. The independent invariant `ForeignResultDoesNotDisableMatchingRecovery` checks that this local transition remains ENABLED under the specified preconditions. `ObserveTerminalEvidence` continues to require a matching result, preserving `MatchingResultRequiredForTerminal` and `NoForeignResultIsTerminal`.

**Actual counterexample / negative controls**: Existing Runtime `scripts/tla-formal falsify` also runs a standalone false reachability probe `ForeignResultIsUnreachable` and demands a concrete `foreign` result. Then it intentionally weakens the recovery step in a temporary source copy; TLC must report a named `ForeignResultDoesNotDisableMatchingRecovery` violation with a foreign-result witness. Parser errors or merely nonzero exit do not count. The ordinary three-Attempt TLC model checks the normal safety/progress obligations on its complete finite state space, not just the selected probe state. `verify_formal_trace.py` now requires this new TLC invariant and exact source SHA-256s; source digest refresh alone cannot remove the actual checked invariant.

**Proof boundary**: `ENABLED` proves a legal abstract choice, not fairness, that the environment will eventually deliver valid evidence, or a concrete SQLite/Rust recovery implementation. The existing native Rust `terminal_evidence_requires_result_finish_matching_resolution_and_no_current_attempt` tests the narrower terminal evidence predicate; it is **not** a mechanized refinement proof for `CorrectForeignResultEvidence`. Correctness of consumer-visible recovery remains UNKNOWN pending an exact Rust transition/consumer bridge. Reuse TLA+/TLC rather than adding a new registry, custom solver or speculative Skill. The mature alternative [Apalache](https://github.com/apalache-mc/apalache) uses SMT/Z3/CVC5; no reason to install it for this small bounded model unless a concrete performance/proof limitation arises.

## PostgreSQL R06 live-consumer admission (independent qualification)

A copied source revision, source/target content parity, and a single installed
writer still do **not** imply that actual consumers may safely use PostgreSQL.
The existing cutover TLA+ model now distinguishes copying/verifying from
QualifyConsumers, which is required before Promote. Commits to the legacy
source, subsequent copies, and rollback invalidate the qualification. The
normal TLC config checks PgWriterRequiresQualifiedConsumers, and the
existing ephemeral negative-control runner deletes just that guard and
requires a named counterexample state trace.

QualifyConsumers is deliberately an UNVERIFIED external oracle in this
abstract model. TLC PASS **does not** authenticate a live consumer receipt,
prove its source seal, demonstrate readback on a real PG instance, or prove
Rust/Harness application refinement. Actual cutover remains NOT_CUT_OVER
until the real consumer and effect owner evidence discharges those obligations.
This is one additional scoped contract in the existing formal owner, not a
new custom solver or a global LEGO registry.

## PostgreSQL R06 installed-writer overlap (CEGAR refinement)

The one-owner enum alone makes dual-writer overlap unrepresentable, even if
two physical processes exist. RuntimePgCutoverR1 now tracks independent
SQLite and PostgreSQL writer-activity bits and checks
NoConcurrentInstalledWriters. Its third ephemeral mutation starts PostgreSQL
while incorrectly leaving SQLite active and requires the exact named TLC
state trace. This models two independent writer authorities, but it does
not attest actual systemd processes, immutable SQLite snapshot bytes,
PostgreSQL connection identity, application commit parity, or Rust refinement.
Cutover remains PROPOSED until real native process/source witnesses bind
these model variables to physical behavior.

## WorkspaceConsumerCloseR1 — bounded continuation guard (2026-10-26)

The existing Runtime WorkspaceLeaseTable is a per-operation mutex, not a
consumer lease across completed Jobs. A real cross-Job failure occurred:
open Workspace, finish command, another caller closes clean/idle Workspace,
then the next valid command receives "workspace is closed". PR #793 proposes
a consumer-release guard. This model verifies the proposed abstract contract,
not the current installed Runtime.

The existing upstream-locked TLA+/TLC owner tool is reused by
mise run formal:verify. Scoped properties:

- FreshActiveConsumerCannotBeClosed: inside the 24h fresh-state abstraction,
  close requires an honest finished-and-released consumer.
- ClosedHasNoLiveJob and ClosedHasNoGitDependent: existing native close
  exclusions remain independent of any release.
- ReleasedAssumesConsumerFinished: an EXTERNAL ASSUMPTION about caller
  truthfulness, not a cryptographically authenticated capability.
- ClosedUnreachable is an intentionally false reachability control:
  an actual named TLC trace proves legitimate closure remains possible.
- Independent ephemeral mutations remove the fresh-release guard or forge
  release by an active consumer; each must violate the named fresh-active
  invariant, or verification fails closed.

Finite model checking does NOT prove Rust-to-TLA refinement, actual
consumer-completion semantics, multi-consumer authorization, persistent
claim/recovery/expiry atomicity, clock trust, Windows permissions, or
the behavior of expired workspaces. PR #793 consumerReleased=true is a
caller assertion. The spoofed-release counterexample demonstrates that
the stronger guarantee remains UNKNOWN without authenticated owner state,
implementation witness, and negative replay. Age expiry is explicitly
allowed to reclaim without release, preserving bounded liveness.

**Concrete Rust recovery-boundary qualification.** The normal
`consumerReleased` guard previously sat after Git metadata recovery
branches that can physically remove an open Workspace. The current
Runtime close-recovery implementation reuses the same guarded predicate
before normal close, corrupt Git metadata force recovery, and unborn-HEAD
force removal; separate native negative CDCs verify the unreleased
consumer's unique residual files survive. This is implementation-level
test evidence for specific paths, *not* a general Rust-to-TLA refinement
proof or an authenticated consumer claim. The previously proposed
`WorkspaceContinuationR1` abstract model is retired here because the
currently checked `WorkspaceConsumerCloseR1` already represents
fresh idle consumer continuity, live Job/Git dependencies, and stronger
spoofed-release negative controls. Maintain one present-day model for
this Owner safety obligation, not duplicate finite proof registries.

No second solver, custom formal DSL, new scheduler or global registry is added.

## PostgreSQL R06 failed-cutover abort before PG authority (CEGAR)

**Problem**: freezing the last SQLite writer is not proof that PostgreSQL
can be promoted. A failed import, parity check, or consumer qualification can
leave the design in the paused state with no executable escape route. Retrying
the source writer must not retain copied PG parity/certification evidence.

**Scoped refinement**: RuntimePgCutoverR1 now admits AbortPaused only
while both installed writer indicators are false and no PG commit exists.
It returns authority to the same SQLite source and clears copied,
parityVerified, and consumersQualified before enabling the old writer.
InstalledWriterMatchesAuthority, NoRetainedQualificationOnSqlite, and
PrecommitAbortEnabled check writer identity, certification invalidation,
and a legally enabled abort. These are abstract safety and enabledness
obligations, not fairness, replay/protocol liveness, or a deployed operation.

**Falsification**: the existing tla-formal falsify gate now admits a
malicious paused-to-SQLite return which preserves PG consumer qualification,
and requires TLC to return a concrete named violation. An independent
reachability probe proves that a certification-free paused state can actually
return to SQLite before a PG writer starts; a permanently paused model
must not be accepted as a safe recovery implementation.

**Physical STOP**: No active Rust Registry PG adapter, durable fence,
installed-process quiescence receipt, current source-final parity, or
consumer-owned replay proof is supplied by this abstract action. The live
PG18 staging import remains VERIFIED_NON_AUTHORITY with promotion_allowed
false. A real service cutover is not authorized by this model and must not
run before independently authenticated downstream obligations are satisfied.
