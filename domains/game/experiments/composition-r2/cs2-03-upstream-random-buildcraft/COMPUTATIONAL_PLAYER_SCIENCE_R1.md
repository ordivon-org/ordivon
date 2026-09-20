# CS2-03 Computational Player Science — R1

Status: **COMPUTATIONAL LOOP ACTIVE / HUMAN GATE NOT REQUIRED**
Date: 2026-09-14

## Purpose

Replace the historical `structural apparatus -> mandatory Human C0/C1` progression with a claim-relative computational evaluation loop.

```text
Mechanism intervention
  -> procedural player population
  -> paired counterfactual simulation
  -> explicit causal estimand
  -> statistics / uncertainty
  -> surrogate model
  -> active experiment selection
  -> direct follow-up simulation
  -> model update / replacement
  -> next experiment
```

Human-specific observations remain admissible when a concrete claim actually requires them, but they are not a workflow terminal and do not block mechanism research.

## R1 estimand

Treatment:

```text
UPSTREAM = current encounter information available before choice
```

Control:

```text
DOWNSTREAM = the same current encounter is revealed only after choice
```

Primary estimand:

```text
persona-balanced paired average treatment effect
= E[total score under UPSTREAM - total score under DOWNSTREAM]
```

The modeled population is an equal-weighted set of ten declared procedural persona families. All 625 four-encounter sequences are enumerated. Stochastic policy draws use common random numbers across treatment/control so the comparison is paired rather than two unrelated Monte Carlo samples.

## Synthetic player population

R1 includes:

- adaptive planner;
- myopic adapter;
- cautious generalist;
- combo builder;
- habitual specialist;
- noisy novice;
- low-attention player;
- expected-value planner;
- opportunist;
- random baseline.

The parameterized behavior envelope varies:

```text
information use
foresight
risk aversion
synergy bias
balance bias
habit bias
decision temperature/noise
```

These are **procedural models**, not a calibrated Human population.

## Primary result

The first population result rejects the earlier simple story that upstream information is uniformly valuable.

```text
persona-balanced score ATE      +0.282
95% two-stage bootstrap CI      [-0.600, +1.179]
persona positive-effect share    50%
worst persona effect             -2.040
best persona effect              +2.977
paired random-baseline effect     0.000
```

Standing:

```text
MIXED_OR_INCONCLUSIVE_IN_DECLARED_SYNTHETIC_PLAYER_ENVELOPE
```

This is a useful negative/heterogeneity result, not a failed experiment.

### Selected persona effects

| Persona | UPSTREAM - DOWNSTREAM score ATE | Interpretation inside model only |
| --- | ---: | --- |
| noisy-novice | +2.977 | information partly counteracts noisy choice |
| expected-value-planner | +1.500 | information helps a future-aware policy |
| cautious-generalist | +0.948 | information helps under robust/generalist weighting |
| combo-builder | +0.665 | modest positive effect |
| low-attention | +0.539 | small but stable benefit |
| adaptive-planner | -0.034 | near-zero aggregate effect despite large action changes |
| habitual-specialist | -0.057 | little information use / little treatment responsiveness |
| opportunist | -1.682 | current-context chasing damages longer-run structure |
| myopic-adapter | -2.040 | current-context chasing strongly damages longer-run structure |
| random-baseline | 0.000 | required treatment-invariant falsifier |

The mechanistic implication is therefore closer to:

```text
information timing
× information use
× planning horizon
× bounded-rational noise
-> outcome
```

rather than:

```text
more upstream information -> more value
```

## Measurement model

R1 refuses a universal `fun` scalar. It separates computationally identified constructs from Human-specific claims.

### Computationally addressable

- strategic adaptation;
- meaningful-choice potential;
- robustness across player models;
- score/regret effects;
- context-responsive choices;
- path/choice diversity.

### Not directly identified by R1

- Human felt agency;
- Human enjoyment;
- Human replay desire.

Those unknowns do **not** create a mandatory Human gate. They remain unknown until a decision actually depends on them or a calibrated surrogate is available.

## Uncertainty

R1 records distinct uncertainty views instead of collapsing them into one number:

```text
between-persona effect variance     2.105
mean between-sequence variance     90.379
mean within-sequence aleatory var  20.034
Human-population calibration        HIGH / unquantified
model-form uncertainty              partially probed only
```

These are diagnostics, not claimed additive variance components.

## Surrogate R1 — polynomial

A Bayesian polynomial surrogate over the continuous seven-parameter player-model envelope was trained on 100 profiles and tested on 28 frozen independent profiles.

```text
R2    0.625
MAE   0.457
standing = WEAK_LOCAL_SURROGATE
```

Permutation sensitivity:

```text
infoUse      44.6%
temperature  36.1%
foresight      8.5%
habitBias      5.3%
others         smaller in this experiment
```

The weak surrogate was retained rather than promoted.

## Active-learning falsifier

The polynomial surrogate selected eight high-expected-information-gain player-model points. Direct paired simulation then tested them using all 625 encounter sequences and 12 stochastic replicates per sequence.

Result:

```text
mean absolute prediction error   1.216
max absolute prediction error    2.244
sign mismatches                  3 / 8
```

Therefore active learning did its job: it found regions where the current model was weak.

## Surrogate R2 — Gaussian process

The weak polynomial was replaced with a Gaussian-process emulator using an ARD RBF kernel. Hyperparameters are selected by bounded coordinate descent on exact marginal likelihood. The eight active-followup observations are added to training while the original 28-profile independent test set remains frozen.

```text
R2                         0.819
MAE                        0.295
approx 95% predictive coverage   89.3%
standing                   PASS_LOCAL_GP_SURROGATE
```

R2 improves test R2 by about `+0.194` and reduces MAE by about `0.162` versus the polynomial model.

ARD length scales again identify the same dominant geometry:

```text
infoUse      0.32   <- fastest variation
temperature  0.50
foresight    1.20
risk         1.20
synergy      1.80
balance      1.80
habit        1.80
```

Shorter length scale means the modeled treatment effect changes more rapidly along that parameter dimension.

## Active experiment selection

The current GP selects the next player-model evaluations by one-observation Gaussian expected information gain:

```text
EIG(x) = 0.5 * log(1 + epistemicVariance(x) / observationNoiseVariance)
```

This is currently **player-model-space active learning**, not yet the final cross-mechanism candidate selector. Once two or more Composition Search candidates share this measurement stack, the acquisition layer can move up one level and compare which mechanism experiment most changes the current decision.

## Current evidence files

```text
model/player-population-r1.json
model/player-value-measurement-r1.json

evidence/computational-player-science-r1.json
evidence/player-effect-surrogate-r1.json
evidence/active-player-model-followup-r1.json
evidence/gp-player-effect-surrogate-r2.json

scripts/computational_player_science_r1.py
scripts/active_followup_r1.py
scripts/gp_surrogate_r2.py
```

## Current conclusion

CS2-03 is **not** promoted as a universally positive mechanism. The stronger result is:

> Upstream encounter information creates a large change in decision geometry, but its value is conditional on player-model properties. Some bounded policies use the information productively; some chase local context and perform worse; treatment response is particularly sensitive to information-use propensity and decision noise.

The next work is therefore computational model refinement / mechanism interaction research, not a mandatory Human canary.

## Claim boundary

This work supports causal statements only inside the declared synthetic player-model envelope and experiment scoring model. It does not establish Human enjoyment, preference, felt agency, retention, population prevalence, or commercial outcome. Absence of those claims is not a workflow blocker.
