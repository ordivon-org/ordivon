# LEGO Theory Wave 2 R1

Date: 2026-09-18
Status: ACTIVE / PROSPECTIVELY VALIDATED R1 / FOLLOW-UPS OPEN

## Purpose

Wave 2 adds four optional analytical lenses that fill gaps left after Wave 1:

1. compositional contracts — when parts must compose or remain replaceable;
2. causal intervention — when a decision depends on what actually causes an outcome;
3. FMEA / FTA — when explicit failure propagation and recovery matter;
4. information flow — when information must or must not cross a boundary.

These are lenses, not mandatory project-plan fields.

## Admission rule inherited from Wave 1

A theory is retained only when it produces at least one of:

- corrected boundary;
- corrected edge;
- falsifiable experiment;
- newly exposed hazard/failure path;
- justified no-change decision.

Vocabulary richness is not evidence of usefulness.

## W2-1 Compositional Contracts

Primary mature foundations:
- assume-guarantee reasoning in compositional verification;
- contract-based subsystem verification;
- refinement/substitutability;
- optional applied-category-theory composition laws.

Core model:

`Component + Environment Assumption -> Guarantee`

Composition is valid only when assumptions are discharged by the environment/other components and the composed guarantees establish the desired property.

Category-theoretic ideas are subordinate:
- use composition/associativity/wiring abstractions when they reduce ambiguity;
- do not create category-theory vocabulary for ordinary modules that already have clear native contracts.

## W2-2 Causal Intervention

Primary mature foundation:
- structural causal models and intervention/identifiability reasoning.

Hard distinction:

`P(Y | X) != P(Y | do(X))`

The lens asks:
- what is being intervened on?
- which causal assumptions are required?
- is the effect identified?
- what controlled experiment would falsify the mechanism?
- where does the result transport?

It must be allowed to return NOT IDENTIFIED.

## W2-3 FMEA / FTA

Primary mature foundations:
- IEC 60812:2018 for FMEA/FMECA;
- NASA fault-tree analysis practice/definitions.

Two directions must remain distinct:

`FMEA: component/function -> failure mode -> local/system effects`

`FTA: top undesired event -> deductive cause paths`

Use STPA alongside these methods when loss can arise from unsafe control/interactions without component failure.

## W2-4 Information Flow

Primary mature foundation:
- information-flow security / noninterference.

Core question:

`Can protected information influence an observation that an unauthorized observer can see?`

The lens traces:
- source;
- transform;
- store;
- channel;
- sink/observer;
- declassification.

Information flow is not authority. A component may see information without being authorized to act, or may have effect authority without receiving unrelated secrets.

## Source boundary

Wave 2 draws from mature external disciplines rather than claiming Ordivon invention.

Canonical authorities recorded for R1:
- NASA CoCoSim / assume-guarantee compositional verification;
- CMU compositional model checking;
- Fong & Spivak, Seven Sketches in Compositionality / MIT Applied Category Theory;
- Judea Pearl, structural causal models / interventions / identifiability;
- IEC 60812:2018 FMEA/FMECA;
- NASA fault-tree-analysis definitions/practice;
- information-flow security / noninterference literature and Cornell systems-security teaching.

## Prospective validation standing

Detailed evidence:
- `knowledge/lessons/lego-wave2-prospective-validation-r1.md`
- `evidence/acceptance/lego-theory-wave2-prospective-r1.json`

Observed first-wave results:

- **Compositional Contracts — PROSPECTIVELY_VALIDATED_REPLACEMENT_LENS.** Harness H05 replacement acceptance was strengthened from happy-path compatibility to assume-guarantee substitutability.
- **Causal Intervention — PROSPECTIVELY_VALIDATED_CAUSAL_BOUNDARY_LENS.** Browser/provider-security evidence supports bounded local attribution while the protected-provider challenge effect remains explicitly NOT IDENTIFIED.
- **FMEA / FTA — PROSPECTIVELY_VALIDATED_RELIABILITY_LENS.** Continuation UNKNOWN is safely non-repeatable but lacks an explicit turn-level convergence owner.
- **Information Flow — PROSPECTIVELY_VALIDATED_INFORMATION_BOUNDARY_LENS.** the historical Agent Service R14 "secret-free locator" wording was corrected: opaque credential locators may themselves be sensitive even though resolved credential/header material remains external.

No finding enters LEGO Core from one case, and Wave 2 introduced no common schema field.


## Relationship to Agent Security LEGO cross-domain validation

Agent Security LEGO consumes this Wave 2 Information Flow lens rather than duplicating it.

Cross-domain validation adds adjacent control/effect questions that Information Flow alone does not own:
- exact operating-regime identity;
- policy binding event/time;
- authority propagation across composed actors/providers;
- persistence-class separation;
- effect commit point/reversibility;
- effect reconciliation oracle.

Reference:
- `knowledge/lessons/agent-security-cross-domain-destroyer-r1.md`

These are promoted as optional shared analytical laws, not Wave 2 replacement lenses and not common schema fields.
