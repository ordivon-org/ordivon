---
name: lego-causal-intervention
description: "Apply structural causal and intervention reasoning to a LEGO problem that asks what causes an outcome, what would happen if one variable were changed, or whether an observed association justifies an intervention. Separate observation from intervention, state causal assumptions, identify confounding/selection/mediators, test identifiability, and design the smallest valid experiment or intervention. Use for ablations, mechanism claims, policy/design changes, regressions, and empirical architecture decisions. Do not convert correlation or temporal order into causation."
compatibility: Cross-platform. Produces causal hypotheses and identification/experiment plans; it does not infer causal truth from observational data automatically.
metadata:
  source-authority: Judea Pearl structural causal models / intervention and identifiability
  lego-theory-layer: docs/LEGO_THEORY_LAYER_R1.md
  wave: "2"
---

# LEGO Causal Intervention Lens

Use this lens when the decision depends on "what changes what" rather than merely "what co-occurs with what."

## Procedure

1. State the causal question in intervention form:
   - outcome Y;
   - candidate cause/intervention X;
   - target population/system state;
   - relevant time horizon.
2. Separate:
   - observation P(Y|X);
   - intervention P(Y|do(X));
   - counterfactual questions about alternate states of the same unit/system.
3. Draw the smallest causal graph needed for the claim.
4. Mark:
   - candidate confounders;
   - mediators;
   - colliders/selection variables;
   - common causes;
   - feedback/time-order relations;
   - variables that are measured versus latent.
5. State the structural assumptions that make the graph meaningful.
6. Ask identifiability:
   - can the intervention effect be identified from current observations under the assumptions?
   - if yes, name the adjustment/identification strategy;
   - if no, say NOT IDENTIFIED rather than inventing an estimate.
7. Prefer randomized or controlled intervention when feasible and appropriate.
8. For engineering systems, use one-variable ablation/differential tests only when the manipulated variable is isolated enough to support the causal claim.
9. Check transport/external validity before generalizing a causal result to another environment, population, provider, version, or scale.
10. Define falsifiers and alternative causal graphs that could explain the same observations.

## Output

Produce:
- causal question/estimand;
- minimal causal graph;
- explicit assumptions;
- observation versus intervention distinction;
- identification standing;
- confounding/selection risks;
- smallest useful experiment or intervention;
- falsifiers and transport limits.

## Promotion law

A causal edge or mechanism claim may influence shared architecture only when supported by a valid intervention, a justified identification argument, or repeated evidence that rules out relevant alternatives.

## Non-claims

- A DAG is an assumption-bearing model, not ground truth.
- Temporal precedence alone is not causation.
- Correlation, feature importance, attribution, or prediction accuracy do not establish intervention effects.
- An intervention in a simulator or test double does not automatically transport to production or Human behavior.
- Do-calculus does not rescue a causal effect that is not identifiable under the available assumptions/data.

## Stop condition

Stop when the causal claim is either identified and testable, experimentally answered within scope, or explicitly classified as not identified with the missing evidence named.

Canonical external foundation:
- Judea Pearl, structural causal models, do-interventions, causal effect identifiability.

Canonical local reference:
- docs/LEGO_THEORY_LAYER_R1.md
- docs/LEGO_THEORY_WAVE2_R1.md
