---
name: lego-fmea-fta
description: "Apply FMEA/FMECA and Fault Tree Analysis to a LEGO system when the main question is how component/process failure modes propagate into local or system effects, or how a specified top failure can arise. Use FMEA bottom-up from functions/items and FTA top-down from an undesired event. Use for reliability, operations, recovery, deployment, data pipelines, and other failure-sensitive systems. Use STPA instead or alongside this lens when unsafe interactions can occur without component failure."
compatibility: Cross-platform. Produces reliability/failure analysis evidence; quantitative probabilities require justified data and independence/dependence assumptions.
metadata:
  source-authority: IEC 60812:2018 FMEA/FMECA; NASA fault-tree analysis
  lego-theory-layer: docs/LEGO_THEORY_LAYER_R1.md
  wave: "2"
---

# LEGO FMEA / FTA Lens

Use this lens to analyze explicit failure propagation from both directions.

## FMEA procedure — bottom-up

1. Define the item/process/function and required function.
2. Enumerate credible failure modes for that function.
3. For each failure mode record:
   - initiating causes/conditions;
   - local effect;
   - next-level/system effect;
   - existing prevention/control;
   - detection/observation;
   - recovery/containment;
   - severity or criticality when justified.
4. Separate failure mode from cause and from effect.
5. Identify common-cause and interface-dependent failures.
6. Do not rank mechanically when ordinal scoring would hide uncertainty.
7. Derive treatments/tests only for the failure modes relevant to the current decision.

## FTA procedure — top-down

1. Define one precise top undesired event.
2. Decompose credible causes with explicit AND/OR logic.
3. Continue until reaching actionable/basic events or evidence limits.
4. Identify single points, common causes, minimal cut sets when the model supports them, and missing detection/recovery barriers.
5. If using probabilities:
   - state data source;
   - state dependence/independence assumptions;
   - do not multiply probabilities that are not independent.
6. Turn important paths into fault-injection, recovery, or monitoring tests.

## Output

Produce:
- scoped FMEA table;
- top-event fault tree where useful;
- common-cause/interface failures;
- detection/recovery gaps;
- candidate fault-injection tests;
- treatment priorities with uncertainty.

## Promotion law

Promote only durable reliability responsibilities, barriers, recovery requirements, or observability requirements that are supported by a credible failure path and have a verification strategy.

## Non-claims

- FMEA completeness is not guaranteed.
- RPN or criticality rankings are decision aids, not objective truth.
- A fault tree is only as complete as its top event, model boundary, and credible-cause search.
- Quantitative FTA is invalid when probabilities/dependencies are fabricated.
- Component-failure analysis does not replace STPA for unsafe interactions where components may behave correctly.

## Stop condition

Stop when decision-relevant failure paths have explicit detection, containment/recovery, and tests, or when further analysis requires unavailable reliability evidence.

Canonical external foundations:
- IEC 60812:2018, Failure modes and effects analysis (FMEA and FMECA).
- NASA fault-tree-analysis definitions and aerospace FTA practice.

Canonical local reference:
- docs/LEGO_THEORY_LAYER_R1.md
- docs/LEGO_THEORY_WAVE2_R1.md
