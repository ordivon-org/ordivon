# LEGO Theory Layer R1

Date: 2026-09-18
Status: ACTIVE EXPERIMENTAL OVERLAY R1

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
