# Causal Lag R4 — Core Breadth / Content Grammar

Status: **CONTENT GRAMMAR MECHANICALLY GREEN / FIRST BREADTH ARC PLAYABLE / HUMAN VALUE UNOBSERVED**

R4 is the first Causal Lag development wave executed explicitly with the current Ordivon LEGO theory stack rather than by adding a new mechanic.

Method provenance used for this wave was inspected from local Ordivon Next revision `4ec87fee31135995f096339b2598e0b925ca9729`. That reference supplies analysis methods only; Game remains authority for the product experiment.

## One-sentence kernel

> R4 turns the fixed R3 session into authored, composable context-transition content while keeping the same diagnosis → forecast → delayed commitment → consequence loop.

It is **not** a new level framework, procedural-generation service, progression system or Game ontology.

## Question Compiler

Target:

```text
R3 already has a mechanically complete stateful session.
How can it gain breadth without adding feature soup?
```

Decision:

```text
Prefer composition of existing mechanics
if existing variation already creates different policies
and can be authored through explicit contracts.
```

Primary questions retained:

1. Do existing context transitions already change optimal policy?
2. Can a content unit remain smaller than the session/reward rules it composes?
3. Can independently authored units compose through an exact seam?
4. Can R3 consume a compiled content path without forking the session engine?
5. Can one representative longer arc preserve meaningful SUCCESS / FAILURE?
6. What remains unproved after mechanical breadth? Human learning, fun, pacing quality and product value.

Questions about crafting, loot, companions, XP and base building were pruned from this wave because they do not control the current decision.

## C-K Design

### K-space

Established knowledge entering R4:

- three existing PC01 operating contexts;
- three causes and three architecture modes;
- exact diagnostic semantics and costs;
- one-context delayed commitment;
- hidden persistence regime;
- R2 history/model relevance;
- R3 architecture/cause continuity and contract terminal states;
- content/progression guidance that depth should first expand existing mechanic relations.

### C0

```text
A broader Causal Lag game
without adding new player primitives.
```

### Selected C branch

```text
existing context transitions
× previous architecture
× persistence
→ authored breadth
```

A throwaway exhaustive probe, then the retained verifier, evaluates:

```text
3 source contexts
× 3 execution contexts
× 3 previous architectures
× 3 persistence values
= 81 decision states
```

Result:

- **9** context-transition types;
- **7 distinct policy signatures**;
- **9 / 9** transition types produce at least two policy signatures across the tested state grid;
- **0 new player verbs**.

This is mechanical policy diversity, not Human fun or perceived difficulty.

### Deferred C branches

R4 deliberately defers:

- unreliable diagnostics;
- degraded/partial forecasts;
- additional architecture families;
- new resource/economy layers;
- crafting/loot/companions;
- meta progression.

They remain valid future concepts if the existing composition space saturates or a real content failure requires them.

## Compositional Contracts

### ContentUnit contract

```text
ASSUME
- role is one of the authored R4 role vocabulary
- sourceCycleIndex resolves to an existing PC01 context
- executionCycleIndex resolves to an existing PC01 context

GUARANTEE
- exactly one source-context → execution-context relation
- no reward table
- no diagnostic rule
- no switch rule
- no session state
- no product authority
```

Current role vocabulary:

```text
INTRODUCE
PRACTICE
VARY
COMBINE
STRESS
RECONTEXTUALIZE
CONCLUDE
```

These labels describe author intent only. They do not establish what a Human actually learns or feels.

### RunRecipe contract

Adjacent units compose only when:

```text
executionCycleIndex(N)
==
sourceCycleIndex(N+1)
```

The compiler also requires a valid initial architecture and a target that does not exceed the theoretical no-cost base maximum.

Its guarantee is deliberately small:

```text
valid content recipe
→ R3-compatible sessionRules
```

### Session-kernel substitution

R3 now accepts an optional `sessionRules` input. With no override, its historical default remains:

```text
roundCount = 4
targetTotal = 320
context chain = 0→1, 1→2, 2→0, 0→1
```

R4 therefore extends content through a replacement seam rather than cloning the session engine.

## Feedback Control view

R4 preserves the existing dynamic loop:

```text
reference
  contract target

state
  latent cause
  built architecture
  round index
  accumulated net
  resolved history

observations
  current symptom
  future context forecast
  history
  contract margin

controller
  player

effects
  inspect
  select architecture
  commit

disturbance
  hidden cause transition

delay
  one context shift

feedback
  consequence + history + contract margin
  → next decision
```

R4 changes the **context path**, not the controller vocabulary.

## First breadth arc

The first composed arc is seven beats:

| Beat | Role | Transition |
|---|---|---|
| 1 | INTRODUCE | 0 → 0 |
| 2 | PRACTICE | 0 → 1 |
| 3 | VARY | 1 → 1 |
| 4 | COMBINE | 1 → 2 |
| 5 | STRESS | 2 → 2 |
| 6 | RECONTEXTUALIZE | 2 → 0 |
| 7 | CONCLUDE | 0 → 1 |

Contract:

```text
7 rounds
target = 560
initial architecture = ROUTE
```

Deterministic witnesses:

- route-aligned path: `700` → **CONTRACT SECURED**;
- persistent ROUTE cause + repeated wrong SOURCE commitments: after beat 4, total `238`, maximum recoverable `538 < 560` → **CONTRACT LOST**.

## Run

Mechanical acceptance:

```bash
pnpm eval:causal-lag:r4
```

Browser E2E:

```bash
pnpm e2e:causal-lag:r4
```

Manual play:

```bash
python -m http.server 8000
```

Open:

```text
http://127.0.0.1:8000/experiments/product-composition-r1/causal-lag-content-r4/web/
```

## Evidence boundary

R4 establishes:

- a thin content-unit contract;
- exact run-recipe seam validation;
- backward-compatible R3 session-rule substitution;
- policy diversity over the tested existing transition space;
- one mechanically valid seven-beat content arc;
- browser execution of that arc.

It does **not** establish:

```text
Human learning
Human difficulty
Human enjoyment
retention
market value
product selection
G0 admission
Game Core law
```

Current machine boundary remains:

```text
productSelected=false
G0=false
humanOutcomeEstablished=false
gameCoreChanged=false
```
