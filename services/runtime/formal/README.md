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
