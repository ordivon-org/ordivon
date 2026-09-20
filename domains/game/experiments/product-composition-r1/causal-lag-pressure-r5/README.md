# Causal Lag R5 — Pressure Topology

Status: **MECHANICALLY GREEN / TEN-BEAT PRESSURE RUN PLAYABLE / HUMAN PACING UNOBSERVED**

R5 applies the current Ordivon LEGO theory stack to a narrower question than “what feature comes next?”:

> Which existing pressure variable can change Causal Lag decisions strongly enough to create a longer run topology without adding player verbs?

Method provenance was inspected from local Ordivon Next revision `0032108f2fa9ce019e3735623e5b37fed23fc3a8`. Those Skills are analysis methods only; Game remains owner of the experiment.

## Question Compiler

The initial candidate set was:

- run-level persistence;
- diagnostic / information cost;
- architecture switch cost;
- contract target pressure.

The decision criterion was not “which number makes the game harder?” It was:

```text
Does varying this axis change optimal policy
over otherwise identical local decision states?
```

The deterministic screen uses all:

```text
3 source contexts
× 3 execution contexts
× 3 previous architectures
=
27 local states
```

Results across bounded level sets:

| Axis | Tested levels | Local states whose policy changes |
|---|---|---:|
| Persistence | 0, .2, .55, .9, 1 | 19 / 27 |
| Diagnostic cost | 0, 3, 6, 9, 12, 18, 30 | **27 / 27** |
| Switch cost | 0, 4, 8, 12, 20, 32 | 18 / 27 |
| Contract target | 200, 320, 560, 690 | **0 / 27** under the current myopic local objective |

The diagnostic-cost sweep changes policy in **27/27** local states across its tested levels.\n\nThe last result matters: raising the target can make terminal failure more likely, but the current local policy solver does not consume targetTotal. R5 therefore rejects “bigger target = pacing” as a fake local-strategy claim.

## C-K Design

### C0

```text
A longer Causal Lag run
with non-fake pacing
generated from existing mechanics.
```

### Selected branch

```text
visible information-acquisition pressure
×
existing hidden run stability
```

R5 retains the historical hidden regimes:

```text
STABLE   persistence = 0.9
VOLATILE persistence = 0.2
```

It changes only the visible current cost of a scan.

Kernel-owned profiles:

```text
SCAN_CHEAP     diagnosticCost = 3
BASELINE       diagnosticCost = 6
SCAN_EXPENSIVE diagnosticCost = 12

switchCost = 8 in all three
```

Content stores only the profile identity. It cannot embed numeric diagnosticCost or switchCost.

## Regime-conditioned information value

This is the key R5 result.

For diagnostic cost levels `3 / 6 / 12`:

| Persistence | States with a policy flip |
|---:|---:|
| 0.2 | **0 / 27** |
| 0.55 | **16 / 27** |
| 0.9 | **27 / 27** |

At persistence `0.9`:

```text
cost = 3  → all 27 tested states use a scan
cost = 12 → all 27 tested states use no scan
```

At persistence `0.2`, the same cost intervention changes no tested policy.

So the mechanically interesting object is not “cheap scan” in isolation:

```text
Information Value
≈
Information Price × World Stability × Context × Built Architecture
```

This is a bounded decision-model result, not a Human pacing or fun claim.

## Feedback Control view

R5 preserves the R3/R4 controller:

```text
reference
  contract target

state
  current cause
  built architecture
  total net
  run history

visible observations
  current symptom
  future context forecast
  current scan cost
  current switch cost
  contract margin

hidden disturbance
  run-level persistence regime

controller
  player

effects
  inspect
  choose architecture
  commit
```

The player action set is unchanged.

## Exploration Policy: deliberately not used

The R5 candidate grid is:

- deterministic;
- exactly attributable;
- tiny enough to enumerate;
- cheap to evaluate.

Therefore adaptive experiment allocation, UCB, Thompson sampling or other bandit machinery would not improve the current decision. Exhaustive screening is the cheaper baseline and wins.

This is an explicit LEGO no-change result, not a missing feature.

## Compositional contract

R5 refines rather than replaces R4:

```text
R5 PressureUnit
=
R4 ContentUnit
+
pressureProfileId
```

The R5 compiler:

1. rejects any numeric pressure fields smuggled into content;
2. validates the pressureProfileId;
3. strips back to a legal R4 ContentUnit;
4. lets the R4 compiler validate context seams and target reachability;
5. emits an R3-compatible `pressureChain` of resolved kernel costs.

R3 accepts the optional chain. When it is absent, historical behavior remains:

```text
profileId      = DESIGN_DEFAULT
diagnosticCost = 6
switchCost     = 8
```

## First ten-beat pressure run

The first R5 schedule is:

```text
CHEAP
CHEAP
BASELINE
BASELINE
EXPENSIVE
EXPENSIVE
EXPENSIVE
BASELINE
CHEAP
CHEAP
```

Its context chain is:

```text
0→0
0→1
1→1
1→2
2→2
2→0
0→0
0→1
1→2
2→0
```

Contract:

```text
10 rounds
target = 780
initial architecture = ROUTE
```

Deterministic witnesses:

- persistent ROUTE cause + ROUTE architecture → `1000` → **CONTRACT SECURED**;
- persistent ROUTE cause + repeated SOURCE architecture → after round 6, total `374`, maximum recoverable `774 < 780` → **CONTRACT LOST**.

## Run

```bash
pnpm eval:causal-lag:r5
pnpm e2e:causal-lag:r5
```

Manual browser:

```text
http://127.0.0.1:8000/experiments/product-composition-r1/causal-lag-pressure-r5/web/
```

## Evidence boundary

R5 establishes:

- one exact pressure-profile substitution seam;
- per-round visible information cost in the existing session kernel;
- deterministic policy sensitivity to information cost;
- strong interaction between information cost and the existing hidden stability regime;
- one ten-beat playable pressure schedule;
- explicit R4 no-pressure compatibility.

R5 does **not** establish:

```text
Human pacing quality
Human comprehension
Human learning
fun
retention
market value
product selection
G0
Game Core law
```

Current authority remains:

```text
newPlayerVerbsAdded=0
productSelected=false
g0Entered=false
humanOutcomeEstablished=false
gameCoreChanged=false
```
