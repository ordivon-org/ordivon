# Meta-Improvement Measurement R1

Date: 2026-09-22
Status: **RESEARCH PROFILE / NOT A UNIVERSAL COMPOSITION METRIC**

## Question

A system may improve one benchmark while becoming worse at producing future improvements.
RSI therefore needs a separate claim:

> Did the successor improve the process that produces later improvements?

Successor Contract R1 can bind a recursive-mechanism change. It does not answer this
question. Meta-improvement is an empirical study obligation.

## Improvement episode

Define one improvement episode:

```text
E =
(
  predecessor,
  improvement-process,
  evidence/input regime,
  candidate attempts,
  verifier outcomes,
  promoted successor or abstention,
  resource costs,
  held-out outcomes
)
```

The episode must preserve exact identities for predecessor, process, evaluation anchors, and
the final candidate/successor.

## Improvement-process evaluation

For improvement process `I`, task family `B`, budget `H`, and frozen evaluation anchor
`A`:

```text
E(I ; B, H, A)
```

denotes the distribution of improvement outcomes, not one scalar score.

A useful measurement vector is:

```text
Π(I) = (
  valid_target_yield,
  admitted_candidate_yield,
  heldout_gain_distribution,
  regression_rate,
  abstention_calibration,
  observation_cost,
  model_call_cost,
  token_cost,
  wall_clock_cost,
  compute_cost,
  human_intervention_cost,
  recovery_or_rollback_rate
)
```

No universal weights are defined here.

## Meta-improvement claim

Let `I_t` be the predecessor improvement mechanism and `I_{t+1}` the candidate mechanism.

A strong bounded meta-improvement claim requires all of:

1. **Mechanism change** — the exact improvement mechanism is inside the successor change set.
2. **Lineage** — the candidate mechanism is bound to the exact predecessor mechanism.
3. **Frozen evaluation anchor** — the standard used to compare mechanisms does not silently
   move with the candidate.
4. **Held-out transfer** — evaluation tasks/data are disjoint from the evidence used to
   design the candidate where the domain permits this.
5. **Comparable budgets** — time/compute/token/human budgets are fixed or explicitly
   normalized.
6. **Repeated evidence** — stochastic mechanisms require repeated runs or an uncertainty
   model; one lucky trajectory is not a distributional claim.
7. **Regression accounting** — gains cannot erase failures on required invariants or named
   negative controls.
8. **Authority continuity** — evaluator/promotion owners remain independently identified.
9. **No forced mutation** — a calibrated abstention/no-change outcome remains admissible.
10. **Exact provenance** — all outcome claims bind exact code/config/model/evaluator versions.

## Pareto rule before scalarization

Because Goodhart pressure is severe, compare the vector `Π` before introducing a scalar.

A candidate mechanism may be called a Pareto improvement only if:

```text
no required dimension becomes materially worse
and
at least one required dimension becomes materially better
```

with the materiality thresholds frozen by the study owner.

If a scalar utility is required:

```text
U(Π)
```

the utility function, thresholds, and metric orientations must be frozen outside the
candidate mechanism before evaluation.

Then a bounded meta-gain may be reported as:

```text
G_meta = U(Π(I_{t+1})) - U(Π(I_t))
```

This value is meaningful only inside that exact study contract.

## Recursion depth

Use descriptive depth, not hype:

```text
R0  output refinement only; no persistent system update
R1  persistent component update
R2  persistent scaffold/harness/circuit update
R3  improvement mechanism itself is updated
R4  evaluator/improvement co-evolution under external anchors
R5  long-horizon repeated successor production with transfer evidence
```

R3+ indicates recursive structure. It does not imply runaway growth, general intelligence, or
open-ended improvement.

## Current Ordivon mapping

Historical Harness evidence maps approximately as:

```text
P0/P1 -> R1-R2 adaptation of attempt strategy / evidence use
P2    -> R2 source/harness self-modification
P3    -> R3 bounded improvement-of-improvement
P4    -> R3 discovery composition + lawful abstention
P5    -> R3 improvement-process efficiency evidence
```

The P5 observation reduction is not by itself a meta-improvement verdict because provider
calls/tokens remained costly. It is one coordinate of `Π`.

## Benchmark implications

A credible Ordivon RSI study should prefer:

- benchmark-disjoint development/evaluation;
- sealed or owner-controlled held-out evaluation where feasible;
- multiple domain families rather than one repository-only task;
- replay from a fresh environment;
- exact predecessor/candidate artifact identity;
- cost and failure accounting;
- transfer across at least one changed model/domain/regime when making a generalization claim.

## Non-claims

This document does not define:

- a universal intelligence score;
- an Ordivon-wide reward function;
- a global RSI grade;
- an automatic promotion threshold;
- a production safety standard;
- an evaluator service.

Meta-improvement remains study/domain evidence until repeated evidence justifies a narrower
reusable mechanism.
