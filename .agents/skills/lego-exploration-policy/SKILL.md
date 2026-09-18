---
name: lego-exploration-policy
description: "Apply exploration-exploitation and bandit-style sequential decision reasoning when Ordivon repeatedly chooses among uncertain candidate actions, experiments, mechanisms, providers, or designs and receives feedback over time. Define arms/options, reward or information objectives, feedback model, stationarity/context assumptions, budget, regret/information trade-off, stopping and reset rules. Use for experiment portfolios, adaptive routing, search budget allocation, and repeated trials. Do not use a bandit metaphor for one-shot irreversible choices or when feedback cannot be attributed to the chosen action."
compatibility: Cross-platform. Produces exploration-policy evidence and experiment allocation plans; it does not grant production authority or define domain value.
metadata:
  source-authority: Lattimore-Szepesvari Bandit Algorithms / sequential decision theory
  lego-theory-layer: docs/LEGO_THEORY_LAYER_R1.md
  wave: "3"
---

# LEGO Exploration Policy Lens

Use this lens when choices repeat and information gained from one choice can improve later choices.

## Procedure

1. Define the decision horizon and candidate options/arms.
2. Define the actual objective:
   - cumulative reward/performance;
   - pure exploration / best-option identification;
   - information gain / uncertainty reduction;
   - constrained multi-objective outcome.
3. Name feedback:
   - what is observed after choosing an option?
   - how noisy/delayed/censored is it?
   - can the observation be causally attributed to the chosen option?
4. State assumptions:
   - stationary or changing environment;
   - independent/contextual outcomes;
   - known/unknown constraints;
   - cost per trial;
   - reversible versus irreversible action.
5. Distinguish exploration from exploitation explicitly.
6. Choose only the minimum policy family justified by the problem:
   - fixed explore-then-commit;
   - confidence-bound style;
   - posterior/Thompson-style;
   - pure-exploration allocation;
   - adversarial/non-stationary treatment when evidence requires it.
7. Preserve safety/authority constraints outside reward optimization.
8. Track uncertainty and evidence per option; do not convert one lucky outcome into winner truth.
9. Define stopping/reset conditions:
   - confidence/evidence threshold;
   - budget exhausted;
   - environment drift detected;
   - value of information too low;
   - candidate set changed materially.
10. Compare against cheap baselines such as uniform allocation or fixed policy.

## Output

Produce:
- option/arm set;
- objective and horizon;
- feedback model;
- assumptions and non-stationarity risks;
- exploration policy;
- budget/allocation;
- baseline;
- stopping/reset rule;
- evidence needed to update the policy.

## Promotion law

Promote only stable experiment-allocation or adaptive-routing responsibilities that survive prospective comparison against a simpler baseline.

## Non-claims

- Reward is not automatically domain value.
- Regret minimization is not semantic correctness.
- A bandit policy does not solve causal attribution by itself.
- Historical arm performance does not transport across changed contexts/providers/versions automatically.
- Exploration never overrides safety, authorization, or irreversible-effect constraints.

## Stop condition

Stop when the next allocation decision is explicit and further policy sophistication would not change the bounded experiment portfolio.

Canonical external foundation:
- Tor Lattimore and Csaba Szepesvári, Bandit Algorithms.

Canonical local reference:
- docs/LEGO_THEORY_LAYER_R1.md
- docs/LEGO_THEORY_WAVE3_R1.md
