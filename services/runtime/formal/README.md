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


## WorkspaceContinuationR1 (2026-10-26)

This separate small bounded TLC model captures the **actual observed**
cross-command race: a first Runtime Job reaches terminal status, an Agent
intends to submit a subsequent Job, and a cleaner mistakes idle for released.
`Close` is permitted only when no Job is running and either (1) the consumer
asserted release or (2) the bounded hold expired. It preserves two safety
obligations: no close while a running Job remains, and no close of an
unreleased fresh Workspace. A deliberately unsafe idle-only close transition
must produce a named `NoUnreleasedFreshClose` counterexample.

The owner Rust test
`workspace_continuation_requires_explicit_release_inside_retention_window`
provides one concrete counterpart to the abstract trace. Mapping
`age = fresh` to `now < createdUnixMs + 24h`, and `released` to
`WorkspaceCloseRequest.consumerReleased`, is scoped evidence only,
**not a mechanized Rust-to-TLA simulation**. The release declaration does
not authenticate the consumer, prove absence of persistent systemd/Research
consumers, or guarantee that future Jobs will not be requested. Expiry is a
bounded operational policy, not a safety theorem about external tasks.
Existing source-state CAS, dirty guards, Git dependencies, external effect
recovery, and cross-node lifetime assumptions are outside this small model.
These bridge and authority obligations remain UNKNOWN.
