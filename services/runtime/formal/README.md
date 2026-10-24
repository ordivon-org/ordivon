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
