# Agent-native Measurement Improvement Loop R1

Date: 2026-09-24
Status: **CURRENT-MAIN COMPILED ARCHITECTURE PROFILE / REUSE EXISTING ORDIVON WAISTS**

## Purpose

Compile the reusable engineering pattern exposed by Anthropic's September 2026 claude.ai performance sprint into Ordivon-native composition without creating a new controller, optimizer, evidence database, verifier runtime, scheduler, or data platform.

The external pattern is:

```text
user journey
  -> observation
  -> measurement contract
  -> deterministic proxy / benchmark
  -> proxy qualification against field outcome
  -> bounded search cell
  -> candidate change
  -> natural-verifier obligations
  -> controlled effect/release
  -> field observation
  -> adjudication
  -> regression ratchet
  -> new instrument when blind spots remain
  -> optional analytical episode / learning feedback
```

The key architectural fact is that this is not a new durable state machine. It is a task-local composition profile over existing Ordivon owners.

## Reused Ordivon substrate

- Cognitive Circuit / Composition: scoped objective, stages, task-local gates.
- Improvement Circuit Profile R1: predecessor, candidate, frozen evaluation, successor closure, promotion separation.
- Verification Obligation R1: exact gate-to-natural-verifier binding.
- Cross-domain Verification R3: seam-specific adapters; no universal verifier.
- Runtime: Job/Attempt physical execution, exact digests, terminal evidence, recovery semantics.
- Artifact Verification: byte/profile/object-contract verification and bounded non-claims.
- Security: policy and consequence verification where effects require admission.
- Experimental Episode R1: non-authoritative analytical projection from exact owner-native evidence.
- Data lifecycle: ODCS/ODPS/DCAT/OpenLineage/PROV-O projections; Parquet/DuckDB/PyArrow where data artifacts require them.
- Existing provider-native telemetry: e.g. GitHub Merge Queue / Actions observation.

## Separation laws

```text
user outcome != proxy metric
observation != evidence
measurement != diagnosis
lab benchmark != field outcome
verification resolution != verifier execution
verifier execution != obligation discharge
mechanical closure != domain acceptance
successor closure != promotion authority
promotion decision != physical release/deployment effect
telemetry != task label
analytical episode != owner truth
formal model check != implementation refinement proof
regression ratchet != universal fitness function
```

## LEGO DAG

### M00 — Outcome Contract
Owner: caller/domain.

Defines the user/domain outcome, population, scope, success/failure boundary, and non-goals. The objective must be meaningful without reference to a local implementation detail.

### M01 — Journey / Scenario Contract
Owner: domain/product owner.

Defines reproducible start/end states for one bounded journey or scenario. A journey may be decomposed, but component metrics cannot silently replace the end-to-end outcome.

### M02 — Observation Source
Owner: natural system/provider owner.

Binds exact observers, methods, scope, time/currentness, and limitations. Provider-native truth remains provider-native.

### M03 — Measurement Contract
Owner: task-local evaluator plus natural metric owner.

Defines one or more measurable quantities, units, aggregation, population, percentile/window, noise assumptions, and expected failure modes.

### M04 — Proxy Candidate
Owner: task-local study.

Introduces a cheap/deterministic surrogate only when direct outcome measurement is too noisy, slow, expensive, or non-repeatable.

### M05 — Proxy Qualification
Owner: evaluation boundary / study owner.

Requires prospective or otherwise bounded evidence that changes in the proxy track the intended field outcome strongly enough for the declared use. A proxy that cannot survive negative controls is not admitted as an optimization target.

### M06 — Deterministic Replay / Benchmark
Owner: natural verifier or benchmark owner.

Creates a reproducible laboratory surface for fast iteration. Exact inputs, versions, configuration, environment assumptions, and result identity must be bound. Benchmark PASS is laboratory evidence only.

### M07 — Search Cell
Owner: task-local Cognitive Circuit / Harness.

One bounded search unit owns a narrow objective, metric/proxy, hypothesis set, experiment loop, evidence references, and stop/done condition. Parallel cells must be isolated enough that attribution remains possible.

### M08 — Candidate Materialization
Owner: Runtime/Harness/domain implementation owner.

Produces the candidate through existing execution owners. Candidate identity must be exact; proposal and materialization remain distinct.

### M09 — Verification Obligations
Owner: packages/composition plus natural verifiers.

Compile task-local gates into `VerificationObligationSet`, bind exact verifier identities, and preserve support scope/non-claims. Reuse owner-native, policy, TLA+/TLC, Pacti, Artifact, empirical, or reality verifiers as appropriate.

### M10 — Controlled Effect / Release
Owner: external effect/promotion authority.

Feature flag, staged rollout, Git integration, deployment, or other physical mutation remains outside the improvement profile. Reversibility and admission are explicit properties, not assumed consequences of a PASS.

### M11 — Field Observation
Owner: natural field/provider owner.

Collect real-user/real-system evidence under the original outcome contract. Lab wins do not auto-promote to field truth.

### M12 — Adjudication
Owner: domain/evaluation owner.

Compare lab evidence, field evidence, correctness/safety constraints, and maintenance/risk costs. The result may accept, reject, hold, or require new instrumentation.

### M13 — Regression Ratchet
Owner: the system that naturally owns the invariant or CI/release gate.

When an improvement is accepted, encode the bounded non-regression property in the natural owner. Ratchets must be scoped and falsifiable; they are architecture memory, not a universal score.

### M14 — Instrument Gap Discovery
Owner: task-local study plus observation owner.

If Human/reality observation conflicts with current metrics, preserve the conflict and create a new instrument rather than optimizing the wrong proxy harder.

### M15 — Analytical Episode / Learning Feedback
Owner: analytical consumer.

Optionally bind exact owner-native evidence into `experimental-episode-binding-r1`, derived features, decision/outcome feedback, or federated data-product lineage. This layer may learn from prior attempts but never becomes Runtime, Harness, domain, provider, or effect truth.

## Minimum admission profile

A task is ready for agent-native optimization only when it has at least:

```text
M00 outcome contract
M01 bounded journey/scenario
M02 observation source
M03 measurement contract
M06 reproducible benchmark OR justified direct field measurement
M09 verifier obligations
M10 explicit effect/promotion authority
M11 field observation path for any claimed real-world improvement
```

M04/M05 are required when a surrogate is used. M13 is required before calling an accepted local improvement durable architecture knowledge. M15 is optional and demand-driven.

## Anti-growth laws

Do not create:

- a universal optimizer;
- a universal fitness/evaluation score;
- a global metric registry with semantic authority;
- a new evidence truth store;
- a second experimental database;
- a universal verifier or proof language;
- a new scheduler/workflow engine;
- an automatic promotion authority;
- a data lake/catalog service without measured consumer pressure.

## Current Ordivon mapping

Base canonical cut surveyed for this profile: `e66aaa1eabcb21b02b58e139b687162dac0e930f`.

The deep substrate is already present. Current resolution after direct repository census and owner-native qualification is:

1. **M03 Measurement Contract** reuses `META_IMPROVEMENT_MEASUREMENT_R1` plus the task/domain measurement owner; no global metric schema is admitted.
2. **M04/M05 Proxy Candidate / Qualification** reuse the existing Evaluation Boundary, negative controls, held-out evidence and natural study owner.
3. **M09 Verification Obligations** reuse `VerificationObligationSet` plus natural verifiers. Runtime V07 now has a bounded `PARTIAL_EXPLICIT_TRACEABILITY_GATE`; this remains trace/currentness evidence, not a mechanized Rust-to-TLA+ refinement proof.
4. **M13 Regression Ratchet** remains owned by the natural invariant / CI / release owner. A scoped ratchet is created only after accepted field evidence; there is no global fitness authority.
5. **M15 Analytical Episode / Learning Feedback** reuses Experimental Episode + OpenLineage/PROV/data-product feedback. The current Finance witness legitimately returns `NO_CHANGE_REQUIRED`; a real non-trivial outcome-driven change remains D16 `OPEN_EMPIRICAL`.
6. **M14 Instrument Gap Discovery** remains event-driven: add an instrument only after a demonstrated observation blind spot or proxy/field conflict.

The remaining challenge is therefore empirical workload pressure and field outcome, not missing generic substrate.

## Source trigger

This profile was compiled after reviewing Anthropic's claude.dev engineering series, especially `How we made claude.ai 3x faster in two weeks`, together with their articles on dynamic workflows, skills, agent tooling, prompt caching, context engineering, and long-running agent verification.
