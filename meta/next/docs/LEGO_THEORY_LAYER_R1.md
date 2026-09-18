# LEGO Theory Layer R1

Date: 2026-09-18
Status: ACTIVE / WAVE 1 PROSPECTIVELY VALIDATED R1

## Purpose

LEGO Theory Layer connects the existing evidence-bound LEGO planning method to mature external disciplines without turning those disciplines into a new mandatory ontology.

The project remains authoritative. Theory lenses are analytical aids.

## Core law

Keep the LEGO planning kernel thin.

A mature discipline may contribute:
- data structures;
- analysis operators;
- derived evidence;
- failure tests;
- stop conditions.

It does not automatically add required fields to project-lego-plan-r1.json.

Promote a concept into the shared core only after repeated cross-domain evidence shows that omitting it causes systematic loss.

## Lens contract

Every theory lens must state:

1. Activation — when the lens is useful.
2. Inputs — what project evidence it consumes.
3. Model — what derived representation it builds.
4. Operators — what transformations or analyses it performs.
5. Outputs — what claims/evidence it produces.
6. Non-claims — what it cannot establish.
7. Promotion law — which findings may update the LEGO plan.
8. Stop condition — when further use adds little value.
9. Sources — mature external authorities on which the procedure is based.

## Cross-cutting analysis operator

### LEGO Question Compiler

Use before or between theory lenses when the target question is vague, overloaded, prematurely solution-shaped, or insufficiently falsifiable.

It does not add another ontology. It compiles a small decision-relevant question set from existing evidence, routes questions to the natural mature lens/domain owner, prunes low-value breadth, and binds retained questions to evidence or bounded experiments.

Canonical references:
- docs/LEGO_QUESTION_COMPILER_R1.md
- .agents/skills/lego-question-compiler/SKILL.md

Question Compiler output is derived analysis. A generated question cannot update project truth or the LEGO plan by itself.

### LEGO Lens Router

Use after the question/decision is sufficiently bound and multiple methods could apply.

It selects a **Minimum Sufficient Theory Set** rather than maximizing theory coverage.

Canonical references:
- docs/LEGO_LENS_ROUTER_R1.md
- .agents/skills/lego-lens-router/SKILL.md
- knowledge/registries/lego-lens-registry-r1.json

The router may return:
- one or more lenses;
- a validated composite profile;
- DOMAIN_METHOD;
- NO_LENS.

Question Compiler asks better questions; Lens Router chooses the smallest useful method set; Project Planning begins only after enough uncertainty is resolved.

### LEGO Lens Compiler

Use only when Lens Router returns `NO_LENS` (or an explicitly bounded uncovered method residue remains) and the decision still lacks a natural rigorous owner.

Lens Compiler does **not** select among active lenses and does not own the lens registry. It searches mature external disciplines for the missing operator, type-checks target-to-discipline mappings, rejects metaphor-only analogies, compiles a thin temporary lens card, and produces shadow/prospective evidence for later registry admission.

Canonical references:
- docs/LEGO_LENS_COMPILER_R1.md
- .agents/skills/lego-lens-compiler/SKILL.md
- templates/LEGO_LENS_CARD_R1.md

The candidate theory space may be large; the active registry remains sparse. There is no automatic Wave 4 merely because more disciplines exist.

Question Compiler -> Lens Router -> existing lens / DOMAIN_METHOD / NO_LENS -> Lens Compiler only for a material missing-method gap -> shadow/prospective evidence -> registry admission/merge/retirement.

Lens Compiler output is derived analysis. It cannot grant itself project/domain authority or self-promote a candidate into the active lens registry.

## Wave 1 lenses

### Systems Engineering

Use for:
- system boundary and environment;
- stakeholder/outcome framing;
- lifecycle;
- interfaces;
- whole-system versus local optimization;
- decomposition at the correct abstraction level.

Produces:
- system-of-interest statement;
- context/boundary map;
- external interfaces;
- lifecycle concerns;
- unresolved boundary questions.

### DSM

Use when:
- dependency density is high;
- decomposition may be wrong;
- cycles/rework/change propagation matter;
- module boundaries are unclear.

Produces:
- typed element-interaction matrix;
- clusters/modules;
- cycles;
- hubs/integrative elements;
- candidate boundary changes.

### Feedback Control

Use when:
- state changes over time;
- observation is partial;
- feedback, delay, disturbance, recovery, robustness, or regulation matters.

Produces:
- state variables;
- observations/sensors;
- controllers;
- actuators/effects;
- reference/goal signals;
- feedback loops;
- delays/disturbances;
- stability/robustness questions.

### STPA / STAMP

Use when:
- safety/security loss can emerge from correct components interacting badly;
- control actions can be unsafe;
- loss propagation cannot be understood as component failure alone.

Produces:
- unacceptable losses;
- system hazards;
- control structure;
- unsafe control actions;
- causal scenarios;
- candidate system constraints.

## Promotion law

A lens finding may change the project LEGO plan only when it establishes an architecture-relevant fact, for example:
- a hidden authority boundary;
- an interface that must be explicit;
- a dependency cluster that invalidates a claimed replacement seam;
- a feedback/control responsibility that requires a separate owner;
- an unsafe interaction that requires a new constraint or split.

Derived clusters, hazards, state models, and control diagrams remain analysis evidence unless promoted by source-grounded review.

## Reflexive use

The LEGO method itself may be treated as a target system.

When LEGO analyzes LEGO:
- distinguish the target method version from the analyzing method version;
- preserve evidence and provenance;
- do not let a lens validate its own correctness merely because it produced a coherent model;
- compare before/after behavior on real projects;
- preserve rollback to the previous method.

This makes self-application an engineering feedback loop rather than unrestricted self-reference.

## Non-goals

- no universal complex-systems ontology;
- no requirement to run every lens on every project;
- no replacement for domain standards;
- no claim that a diagram proves truth;
- no schema expansion merely because a theory has additional vocabulary.

## Planned later waves

Wave 2 candidates:
- compositionality/contracts/category-theoretic ideas;
- causal inference and intervention;
- reliability/FMEA/FTA;
- information-flow/information-theoretic analysis.

Wave 3 candidates:
- exploration/exploitation and bandits;
- C-K design theory;
- evolutionary search;
- organizational cybernetics / viable-systems ideas.

Adoption is evidence-driven, not chronology-driven.


## Recorded LEGO cases

### Poker AI / imperfect-information strategy

Recorded pilot:
- knowledge/lessons/poker-ai-lego-question-compiler-pilot-r1.md

This pilot tests the Question Compiler against the Libratus/Pluribus narrative. It converts a broad "math versus psychology" story into bounded state/observability, action-space, exploitability, information-flow, emergence/control, and counterfactual questions with explicit evidence or experiment routes.

It is a method pilot, not a promotion of game-theoretic vocabulary into the common LEGO schema.


### AI as Miracle Material / Infinite Minds article

Recorded case:
- knowledge/lessons/ai-miracle-material-lego-case-r1.md
- knowledge/graphs/ai-miracle-material-lego-case-r1.json

This case exercises kernel extraction, primitive decomposition, typed relations, metaphor separation, missing-node discovery, failure probing, recomposition, Ordivon transfer, and falsification hooks.

It introduces only promotion candidates, not new mandatory core fields. Repeated cross-domain evidence is required before any candidate is promoted into the shared LEGO kernel.


## Active experimental lens: Regime Shift & Deep-Uncertainty Decision

Canonical references:
- docs/LEGO_REGIME_SHIFT_DECISION_R1.md
- .agents/skills/lego-regime-shift/SKILL.md
- evidence/acceptance/lego-regime-shift-lens-r1.json

Use when observed outputs may lag upstream structural change, when buffers/delays hide state, or when decisions are partly irreversible under deep uncertainty.

Core sequence:

State -> Flow/Derivative -> Buffer -> Delay -> Threshold -> Feedback -> Regime Hypothesis -> Falsifier -> Robust Action

Hard non-equivalences:
- warning signal != forecast
- forecast != decision
- current level != marginal direction
- coherent narrative != causal mechanism
- regime hypothesis != project truth

This lens remains an overlay. It adds no mandatory field to project-lego-plan-r1.json. Promotion requires prospective cross-domain evidence.

## Wave 1 prospective validation

Cross-domain prospective validation is recorded in:

- `knowledge/lessons/lego-wave1-prospective-validation-r1.md`
- `evidence/acceptance/lego-theory-wave1-prospective-r1.json`

Observed results:

- **Systems Engineering — KEEP_OPTIONAL_FOUNDATION.** It consistently protected system boundaries, external authority, and whole-system framing. Its Wave 1 value was mostly confirmatory rather than architecture-changing.
- **DSM — KEEP_CONDITIONAL.** The Runtime trial did not justify a re-cut of its intentionally sparse graph. DSM remains useful for dense/cyclic systems, but broader Ordivon standing requires a genuinely dense dependency case.
- **Feedback Control — PROSPECTIVELY_VALIDATED_OPTIONAL_LENS.** It exposed missing feedback edges in two unrelated domains: Runtime reconciliation back into execution control, and Game player evidence back into composition hypotheses.
- **STAMP/STPA — PROSPECTIVELY_VALIDATED_HIGH_CONSEQUENCE_LENS.** It exposed an Agent Service authority-lifetime/revocation question even after the R14 implementation's focused and full repository tests passed, while also confirming existing Browser Security fail-closed control constraints.

Concrete evidence:

- Runtime feedback-loop correction integrated at `cf0e0adf118d4f143fd7117d6a9592343261d8e0`.
- Game feedback-loop correction validated at detached commit `3138d9157e3c933287be1cc3b1879aea7eef3593`; it was not integrated during the trial because the existing Game main already had branch divergence.
- Agent Service R14 characterization showed that an already-created Binding can still deliver after its SemanticSession is closed. This is recorded as an unresolved authority-lifetime contract, not automatically classified as a bug.
- Browser/provider-security analysis was confirmatory: challenge state remains observation rather than root-cause truth, and consequential effects remain behind fail-closed boundaries.

### Wave 1 promotion verdict

No theory-specific field is promoted into the shared LEGO Core or `project-lego-plan-r1` schema.

Useful findings fit existing graph/evidence mechanisms:

- feedback can be represented with existing CONTROL / OBSERVATION edges;
- hazards remain derived evidence until a domain owner adopts a constraint;
- DSM matrices remain derived projections;
- boundary/context maps remain optional analyses;
- authority lifetime remains a domain/system-contract question until repeated evidence justifies a shared primitive.

The stronger admission rule for later lenses is:

`theory usefulness != vocabulary richness`

A lens earns retention when it produces at least one of:

- a corrected boundary;
- a corrected edge;
- a falsifiable experiment;
- a newly exposed hazard;
- a justified no-change decision.

Otherwise stop the lens rather than generate more analysis.

## Active Wave 2 experimental lenses

Canonical package:
- `docs/LEGO_THEORY_WAVE2_R1.md`
- `evidence/acceptance/lego-theory-wave2-r1.json`

Wave 2 currently adds four optional lenses:
- `lego-compositional-contracts`;
- `lego-causal-intervention`;
- `lego-fmea-fta`;
- `lego-information-flow`.

Wave 2 has now passed its first prospective cross-domain validation with follow-ups. None adds mandatory fields to the common LEGO schema.

Standing:
- `lego-compositional-contracts` — PROSPECTIVELY_VALIDATED_REPLACEMENT_LENS;
- `lego-causal-intervention` — PROSPECTIVELY_VALIDATED_CAUSAL_BOUNDARY_LENS;
- `lego-fmea-fta` — PROSPECTIVELY_VALIDATED_RELIABILITY_LENS;
- `lego-information-flow` — PROSPECTIVELY_VALIDATED_INFORMATION_BOUNDARY_LENS.

Evidence:
- `knowledge/lessons/lego-wave2-prospective-validation-r1.md`
- `evidence/acceptance/lego-theory-wave2-prospective-r1.json`

## Active Wave 3 experimental lenses

Canonical package:
- `docs/LEGO_THEORY_WAVE3_R1.md`
- `evidence/acceptance/lego-theory-wave3-r1.json`

Wave 3 adds four optional lenses for generative/adaptive work:
- `lego-exploration-policy`;
- `lego-ck-design`;
- `lego-evolutionary-search`;
- `lego-organizational-cybernetics`.

Wave 3 has passed its first prospective validation with conditional algorithmic adoption. None adds mandatory fields to the common LEGO schema. Search reward, design concepts, evolutionary fitness, and organizational-model coordinates remain derived evidence rather than project truth.

Standing:
- `lego-exploration-policy` — PROSPECTIVELY_VALIDATED_SCOPE_GUARD; algorithmic adoption remains conditional on repeated comparable feedback;
- `lego-ck-design` — PROSPECTIVELY_VALIDATED_GENERATIVE_DESIGN_LENS;
- `lego-evolutionary-search` — PROSPECTIVELY_VALIDATED_EVALUATOR_GUARD; algorithmic adoption remains conditional on a trustworthy evaluator;
- `lego-organizational-cybernetics` — PROSPECTIVELY_VALIDATED_ORGANIZATIONAL_BOUNDARY_LENS.

Evidence:
- `knowledge/lessons/lego-wave3-prospective-validation-r1.md`;
- `evidence/acceptance/lego-theory-wave3-prospective-r1.json`;
- `knowledge/lessons/lego-wave23-self-audit-r1.md`.

Wave 3 routing is phase-specific: C-K expands unknown concepts, Exploration Policy allocates repeated trials among known comparable options, Evolutionary Search varies populations only after representation/evaluator validity exists, and Organizational Cybernetics diagnoses organizational control rather than candidate search.


## Agent Security LEGO — cross-domain validated composite profile

Canonical lens:
- `knowledge/lessons/agent-security-lego-r1.md`

Validation chain:
- ZCode reference case: `knowledge/lessons/zcode-workspace-snapshot-security-lego-r1.md`
- coding-agent destroyer: `knowledge/lessons/agent-security-cross-system-destroyer-r1.md`
- unrelated-domain destroyer: `knowledge/lessons/agent-security-cross-domain-destroyer-r1.md`
- machine graph: `knowledge/graphs/agent-security-cross-domain-destroyer-r1.json`

The lens was first pressure-tested across ZCode, Codex, Claude Code, Cursor, OpenCode and OpenClaw, then across browser automation/Agent Birth, Artifact Build & Delivery, Market Capital, Game/Station Zero, and Gmail/Google Calendar connected-app action surfaces.

The cross-domain round deliberately reuses Wave 2 Information Flow for source/transform/store/channel/sink reasoning rather than inventing a competing information-flow ontology.

Repeated cross-domain evidence promotes six **analytical laws** into the shared LEGO Theory layer:

1. **REGIME_BOUND_CLAIMS** — capability/security claims bind to an exact operating regime, not a product/system name alone.
2. **POLICY_BINDING_EVENT** — a control must state when it becomes effective; policy applied after commit cannot retroactively constrain the committed effect.
3. **EXPLICIT_AUTHORITY_PROPAGATION** — composed actors/components must state how authority is delegated, attenuated, clamped, independent, or escalatable.
4. **PERSISTENCE_CLASS_SEPARATION** — persistence/retention/deletion is object-class specific rather than one system-wide boolean or duration.
5. **EFFECT_COMMIT_POINT** — distinguish proposal/intent/preview/draft from the operation that crosses into consequential effect.
6. **EFFECT_RECONCILIATION_ORACLE** — consequential or ambiguous effects require owner-native read-back/reconciliation rather than process-success inference or blind retry.

These laws reinforce existing Ordivon laws including `intent_not_authority`, `attempt_before_effect_when_durable`, `observation_not_semantic_success`, and `unknown_external_outcome_is_first_class`.

No mandatory project-plan field is added. `schemas/project-lego-plan-r1.schema.json` remains unchanged.

## Lens-library growth law

Almost any mature discipline may become an Ordivon lens candidate, but usefulness as a discipline is not sufficient for registry admission.

A candidate must establish a distinct decision question, mature substrate, activation/prerequisite/contraindication boundary, overlap audit, stop condition, prospective case, and retention evidence.

The theory library is therefore open-ended while the Core remains deliberately closed.

The current optimization target is not "more disciplines"; it is:

`minimum sufficient theory for the current decision`.

No Wave 4 is implied by discovering another useful academic field.
- docs/LEGO_LENS_UNIVERSE_R1.md
