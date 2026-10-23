---
name: evolutionary-search
description: "Apply evolutionary-computation reasoning when the system has a large, discrete, non-differentiable, combinatorial, or open-ended candidate space that can be evaluated repeatedly. Define representation/genotype, phenotype/evaluation, population, variation, selection, diversity, archive, constraints, evaluation noise, and termination. Use for architecture/design search, mechanic combinations, prompt/workflow variants, or parameter/configuration populations. Do not equate fitness with real value or deploy evolved candidates without independent verification."
compatibility: Cross-platform. Produces search-protocol evidence; it does not authorize autonomous production mutation.
metadata:
  source-authority: Eiben-Smith Introduction to Evolutionary Computing
---

# Evolutionary Search

Use this method when maintaining and transforming a population of candidates is more appropriate than optimizing one current design.

## Procedure

1. Define candidate representation:
   - what may mutate/recombine;
   - what must remain invariant.
2. Define phenotype/evaluation:
   - how candidate behavior is materialized;
   - which evaluator observes it.
3. Define population and initialization:
   - seeded versus random;
   - diversity requirements;
   - known baselines.
4. Define variation operators:
   - mutation;
   - recombination;
   - structural edits;
   - domain-specific transformations.
5. Define selection:
   - fitness/objective;
   - constraints;
   - Pareto/multi-objective handling;
   - elitism/archive when justified.
6. Prevent Goodhart collapse:
   - keep fitness local/scoped;
   - use holdout/independent evaluation;
   - detect degenerate shortcuts;
   - preserve behavioral diversity.
7. Handle noisy/stochastic evaluation with repeated trials or confidence where necessary.
8. Track lineage/provenance and exact candidate identity.
9. Separate search environment from production authority.
10. Define termination/restart:
   - no meaningful improvement;
   - diversity collapse;
   - budget;
   - objective/constraint change;
   - evaluator drift.

## Output

Produce:
- representation;
- population;
- variation operators;
- selection/evaluation;
- diversity/novelty policy;
- archive/lineage;
- anti-Goodhart checks;
- termination/restart;
- verification boundary before promotion.

## Promotion law

A candidate leaves the search population only through independent domain acceptance. Fitness alone never promotes a production architecture, research claim, or product direction.

## Non-claims

- Fitness is not ground truth.
- More generations do not guarantee useful innovation.
- Evolutionary search is not automatically better than random/grid/Bayesian/local search.
- Diversity metrics do not prove semantic diversity.
- Search mutation does not grant permission to mutate production state.

## Stop condition

Stop when search representation/evaluation are no longer trustworthy, a simpler search dominates, or a candidate has reached the independent domain-verification gate.

Canonical external foundation:
- A. E. Eiben and J. E. Smith, Introduction to Evolutionary Computing.

Canonical local reference:
- docs/LEGO_THEORY_WAVE3_R1.md
