# Causal Lag R6 — Horizon Contract Oracle

Status: **MECHANICALLY GREEN / HORIZON RELATION ESTABLISHED / PLAYER STRATEGY UNOBSERVED**

R6 does not add another mechanic. It uses the updated Ordivon LEGO Question Compiler + **Lens Router** to decide between two competing next questions:

1. has the existing `Context × Information Pressure` composition space begun to saturate?
2. does adding a finite contract horizon create a genuinely new relation where future consequences change the current best policy?

Method provenance is bound to Ordivon Next revision `2231438e8f293742c1f5f1a2622b3e567003f5e0`. These methods remain analysis provenance rather than Game authority.

## Question Compiler

The branch decision was reduced to two discriminating questions.

### Q1 — Saturation

If more R5 composition merely repeats the same policy topology, a new pressure/mechanic may be justified.

### Q2 — Horizon

If the same local state changes policy only because the remaining contract requirement changes, then time coupling itself is a new design relation and should be tested before adding another mechanic.

## Lens Router

The updated router intentionally selected a very small method set.

```text
LEGO lens
  C-K Design
    compare the two concept branches

DOMAIN_METHOD
  exact combinatorial enumeration
    saturation/equivalence measurement

DOMAIN_METHOD
  finite-horizon dynamic programming
    contract-success policy
```

Not selected:

- Exploration Policy — the search is deterministic, cheap, exhaustive, and exactly attributable.
- Feedback Control — useful as an interpretation lens, but R6 introduces no new runtime controller or durable control contract.
- Information Flow — oracle visibility remains bounded, but no new architecture-level information-flow decision is required.

This is the newer LEGO rule in practice: **a domain-native mature method wins when it already owns the exact question**.

## Branch A — composition saturation

Each local content unit is:

```text
source context
× execution context
× pressure profile
```

There are:

```text
3 × 3 × 3 = 27 units
```

Each unit is fingerprinted by its optimal local policy across:

```text
previous architecture ∈ {SOURCE, PROCESS, ROUTE}
persistence ∈ {0.2, 0.9}
```

Result:

```text
27 local units
20 policy-equivalence classes
7 redundant units

unique fraction = 20 / 27 = 74.07%
```

Baseline-only transitions had 7 classes across 9 transitions. Information pressure expanded the bounded local policy vocabulary to 20 classes.

More importantly, valid chained sequences do not show worsening collapse:

| Length | Valid sequences | Distinct equivalence words | Unique fraction |
|---:|---:|---:|---:|
| 1 | 27 | 20 | 74.07% |
| 2 | 243 | 180 | 74.07% |
| 3 | 2,187 | 1,620 | 74.07% |
| 4 | 19,683 | 14,580 | 74.07% |
| 5 | 177,147 | 131,220 | 74.07% |

Therefore:

```text
local equivalence exists
≠
composition saturation established
```

R6 does not admit a new pressure axis from saturation evidence.

## Branch B — horizon-aware contract planning

R6 defines a bounded exact oracle:

```text
horizon ∈ {1,2,3 beats}
objective:
  maximize P(contract target reached)
  then maximize expected total net as tie-breaker
```

It is intentionally **not** a generic MDP/POMDP framework.

It reuses only:

- existing PC01 reward tables;
- existing diagnostics;
- existing architectures;
- existing R5 pressure profiles;
- existing R3 carryover semantics where resolved execution cause becomes the next current cause and committed architecture persists.

No R3 runtime code is changed.

## Full bounded R5-window screen

R6 re-evaluates every existing R5 two- and three-beat window under:

```text
persistence ∈ {0.2, 0.9}
previousArchitecture ∈ {SOURCE, PROCESS, ROUTE}
remainingTarget = 40,45,...,(100 × horizon)
```

The exact receipt finds:

```text
96 target-sensitive window states
625 adjacent-target current-policy transitions
```

So contract margin is not just a terminal score check.

It can alter the action chosen **now**.

## Volatile witness — locally useless information becomes strategically useful

Use existing R5 beats 2–3:

```text
0 → 1   SCAN_CHEAP
1 → 1   BASELINE

persistence = 0.2
previous architecture = ROUTE
```

### Myopic objective

Maximize immediate expected net:

```text
NO SCAN
→ PROCESS

immediate expected net = 78.8
```

### Horizon objective, remaining target = 155

```text
PROCESS SCAN
FAULT → PROCESS
OK    → ROUTE

P(contract success) = 0.68704
expected total net  = 157.808
immediate expected net = 76.7
```

This policy deliberately gives up immediate expected value:

```text
76.7 < 78.8
```

because the information-conditioned architecture state improves the finite-horizon contract objective.

### Same state, remaining target = 160

```text
NO SCAN
→ ROUTE

P(contract success) = 0.636
expected total net  = 158.52
```

Everything except the contract requirement is unchanged.

Therefore:

```text
same local state
+ different remaining contract margin
→ different optimal current policy
```

That is the new R6 relation.

## Stable witness

The effect is not restricted to volatile worlds.

Existing R5 beats 4–5:

```text
1 → 2   BASELINE
2 → 2   SCAN_EXPENSIVE

persistence = 0.9
previous architecture = PROCESS
```

At remaining target 185:

```text
ROUTE SCAN
FAULT → ROUTE
OK    → SOURCE

P(success) = 0.70846
```

At remaining target 190:

```text
NO SCAN
→ ROUTE

P(success) = 0.549
```

Again, the local state is otherwise fixed.

## Why there is no browser carrier

R6 deliberately creates **no browser carrier**.

The oracle consumes:

- exact persistence;
- explicit success probability;
- complete transition/reward model.

Those are falsification/evaluation variables, not current player observations.

Rendering them as a normal player surface would blur:

```text
oracle knowledge
≠
player-visible knowledge
```

So R6 remains an evaluator.

## Why there is no G09

R6 introduces no durable new project responsibility.

The existing graph already owns the needed boundaries:

```text
G06 StatefulSessionKernel
  defines carryover semantics

G07 ContentGrammarCompiler
  owns existing authored context/pressure units

G08 BreadthVerifier
  owns bounded mechanical policy-diversity and strategy-sensitivity evidence
```

The horizon solver is an experimental verifier under G08, not a production planning service.

## Run

```bash
pnpm eval:causal-lag:r6
```

## Evidence boundary

R6 establishes only that, inside the exact bounded model:

- current optimal policy can depend on remaining contract target;
- horizon planning can prefer lower immediate expected net;
- information with no local advantage can gain strategic value through future-state coupling;
- the effect occurs in both tested persistence regimes;
- current R5 composition is not yet mechanically shown to be saturated.

R6 does **not** establish:

```text
Human strategic reasoning
Human comprehension
Human pacing quality
fun
difficulty
retention
market value
product selection
G0
Game Core law
```

Authority remains:

```text
runtimeKernelChanged=false
projectNodeAdded=false
newPlayerVerbsAdded=0
productSelected=false
g0Entered=false
humanOutcomeEstablished=false
gameCoreChanged=false
```
