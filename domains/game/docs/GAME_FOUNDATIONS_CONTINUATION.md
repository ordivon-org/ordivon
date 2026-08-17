---
schema_version: 1
id: game.foundations-research.continuation
title: Ordivon Game Foundations Research Continuation Handoff
type: handoff
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - researcher
  - builder
  - agent
updated: 2026-08-17
summary: Exact continuity handoff for resuming the Game foundations programme after R1–R17 without depending on the originating conversation context.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.map
  - game.core-research.reset
---
# Ordivon Game Foundations Research Continuation Handoff

## Read first

1. [`GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](GAME_FOUNDATIONS_RESEARCH_R1_R17.md) — full canonical snapshot of the seventeen completed foundation rounds.
2. [`GAME_FOUNDATIONS_RESEARCH_MAP.md`](GAME_FOUNDATIONS_RESEARCH_MAP.md) — compact conceptual map and cross-round abstractions.
3. [`GAME_CORE_RESEARCH_RESET.md`](GAME_CORE_RESEARCH_RESET.md) — protects canonical G0–G8 semantics and prevents premature product selection.
4. [`DEVELOPMENT_MODEL.md`](DEVELOPMENT_MODEL.md) — only authority for G0–G8 product-development meanings.

## Current research status

Completed:

```text
R1  Game classification / multidimensional form space
R2  Player-value families
R3  Atomic mechanics
R4  Game loops
R5  Motivation / reward / emotion / fantasy
R6  Fun / engagement / satisfaction / compulsion / meaning
R7  Tension / uncertainty / difficulty / pacing
R8  Story / narrative / emergence / simulation
R9  World / rules / state / dynamics / simulation / emergence
R10 Object / Actor / Subject / NPC / Agent / Player
R11 Action / Choice / Agency / Freedom / Control / Consequence
R12 Feedback / Legibility / Mental Model / Learning
R13 Progression / Persistence / Memory / History / Learning
R14 Resource / Scarcity / Ownership / Production / Exchange / Economy
R15 Group / Organization / Institution / Norm / Law / Collective Agency
R16 Space / Topology / Distance / Territory / Exploration
R17 Information / Knowledge / Belief / Secrets / Communication / Deception
```

Exact next round:

```text
R18 — Goals, Utility, Needs, Values and Desire
```

## Research boundary that must survive the context switch

Do **not** assume the answer is an authoritative Agent World.

The search space remains deliberately broad, including:

```text
traditional authored games
systemic simulations
social worlds
creative sandboxes
procedural games
SillyTavern-like AI roleplay / co-creation
generative narrative / character experiences
persistent Agent worlds
hybrids among the above
```

In particular:

```text
AI Game != Agent World
Agent != LLM
NPC != Agent
Generation != gameplay
World != Map
Freedom != Agency
Memory != History
```

Do not promote any research direction into canonical G0–G8. No product winner currently exists.

## How to continue R18

Start from the concepts, not from current implementation.

The core problem is:

> Why does a Subject choose one future over another, and how much motivational structure is actually required for different game forms?

Distinguish at least:

```text
Need
Want
Desire
Goal
Preference
Utility
Value
Drive
Constraint
Identity commitment
```

Questions worth attacking:

1. Is `Need` a state deficit, a desired setpoint, or only one source of preference?
2. How is a temporary `Goal` generated from slower `Preferences` / `Values`?
3. When is one scalar utility function a harmful compression of genuinely incommensurable values?
4. When do multiple incompatible needs create interesting trade-offs rather than arbitrary behavior?
5. How do resource scarcity, information and time change goal selection?
6. How should relationships, identity, norms and institutions modify preferences?
7. Can goals themselves be generated dynamically from World state rather than pre-authored?
8. What is the minimum motivational model for an enemy, companion, economic actor, citizen, organization or roleplay Persona?
9. Which forms need autonomous desire at all? A generative Persona may primarily serve player fantasy/expression rather than pursue independent world goals.
10. How do compatible/incompatible value structures generate cooperation, conflict, bargaining and sacrifice?
11. How do Subject goals differ from Human player motivation and designer-authored objectives?
12. Which motivational commitments should be structured/hard, and which may remain soft/generated?

## Expected R18 output shape

Continue the same style used in R1–R17:

```text
1. define and separate overloaded terms;
2. derive the smallest useful formal structure;
3. test it against multiple traditional game families;
4. test it against social/systemic worlds;
5. test it against generative/SillyTavern-like interaction;
6. identify collapse/failure modes;
7. connect back to prior rounds;
8. preserve provisional equations as hypotheses, not final laws;
9. end with the next foundational question rather than product selection.
```

## Stable abstractions already available

Reuse these where useful, but challenge them if R18 reveals a contradiction:

```text
GameForm =
Interaction × Control × World × Time × Space
× ContentSource × GoalStructure × SocialStructure × Value
```

```text
Question
→ Choice
→ Consequence
→ Learning
→ ChangedState
→ NewQuestion
```

```text
World = StructuredState + RulesOfPossibleChange
```

```text
Subject =
SituatedPerspective
+ InternalState
+ Policy
+ ConsequentialAction
```

```text
Agency =
ability to select among meaningfully distinct future trajectories
```

```text
Truth != Signal != Observation != Belief != Statement
```

```text
History becomes valuable when past becomes present/future structure
```

```text
Resource ≈ StoredOptionality
```

```text
Topology = structure of reachability and influence
```

```text
Playable X =
X that the player can observe, model, influence/test,
and use to improve future decisions or expression
```

## High-priority warnings

Do not regress into any of these shortcuts:

```text
“LLM is smarter, therefore NPC is better.”
“More memory means deeper character.”
“More agents means richer society.”
“More map means more exploration.”
“More events means more story.”
“More choices means more agency.”
“More simulation means more depth.”
“More generation means more content value.”
“More time spent means more engagement value.”
```

The entire programme exists partly to replace those surface metrics with causal, player-facing structure.

## Product-selection stop condition

Do not begin intentional new-product G0 merely because the research corpus is large.

Before narrowing, the research should at least:

- finish the remaining obvious foundational dimensions;
- synthesize which dimensions are independent vs redundant;
- identify a smaller set of candidate causal laws;
- compare several materially different experience families;
- distinguish requirements of authored, systemic and generative forms;
- design high-information falsifiers rather than simply more prototypes;
- state what remains unknown.

Only then ask whether evidence is mature enough to select an actual product form.
