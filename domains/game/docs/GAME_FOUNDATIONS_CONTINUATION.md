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
summary: Exact continuity handoff for resuming the Game foundations programme after R1–R23 without depending on the originating conversation context.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.r18
  - game.foundations-research.r19
  - game.foundations-research.r20
  - game.foundations-research.r21
  - game.foundations-research.r22
  - game.foundations-research.r23
  - game.foundations-research.map
  - game.core-research.reset
---
# Ordivon Game Foundations Research Continuation Handoff

## Read first

1. [`GAME_FOUNDATIONS_RESEARCH_R23.md`](GAME_FOUNDATIONS_RESEARCH_R23.md) — canonical R23 decomposition of temporal frames, order, concurrency, duration, timing, rhythm, turns, windows, waiting, reversibility, persistence and temporal agency.
2. [`GAME_FOUNDATIONS_RESEARCH_MAP.md`](GAME_FOUNDATIONS_RESEARCH_MAP.md) — compact R1–R23 conceptual map.
3. [`GAME_FOUNDATIONS_RESEARCH_R22.md`](GAME_FOUNDATIONS_RESEARCH_R22.md) — uncertainty/risk layer that R23 extends through realization timing, deadlines and temporal exposure.
4. [`GAME_FOUNDATIONS_RESEARCH_R21.md`](GAME_FOUNDATIONS_RESEARCH_R21.md) — control/action-causality layer that R23 temporalizes.
5. [`GAME_FOUNDATIONS_RESEARCH_R20.md`](GAME_FOUNDATIONS_RESEARCH_R20.md) — creation/authorship layer.
6. [`GAME_FOUNDATIONS_RESEARCH_R19.md`](GAME_FOUNDATIONS_RESEARCH_R19.md) — strategic-interdependence layer.
7. [`GAME_FOUNDATIONS_RESEARCH_R18.md`](GAME_FOUNDATIONS_RESEARCH_R18.md) — motivation/goal/commitment layer.
8. [`GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](GAME_FOUNDATIONS_RESEARCH_R1_R17.md) — canonical first seventeen rounds.
9. [`DEVELOPMENT_MODEL.md`](DEVELOPMENT_MODEL.md) — sole authority for G0–G8 product-stage meanings.

## Current research status

Completed through R23. Exact next round:

```text
R24 — Identity, Character, Role, Persona, Self, Status, Reputation, Continuity and Transformation
```

## Stable pre-R23 boundaries

```text
AI Game != Agent World
Agent != LLM
Generation != gameplay
Freedom != Agency
Memory != History
Need != Desire != Goal
Communication != Commitment
Creation != Creativity
Authorship != Ownership
Control != SenseOfAgency
Avatar != Body
Embodiment != Presence
Uncertainty != Randomness
Determinism != Predictability
Risk != Variance != ExpectedValue
DecisionQuality != OutcomeQuality
Fairness != Symmetry != OutcomeEquality != Balance
```

## R23 durable result

```text
Time != Clock
Sequence != Duration
ClockOrder != CausalOrder
Simultaneity != Concurrency
Turn != Tick != Phase
Duration != Timing
Tempo != Rhythm != Pacing
Deadline != Timer
Cooldown != Recovery
Latency != GameWorldTime
Waiting != DeadTime
Persistence != ContinuousSimulation
Replay != Undo != StateRestore != InWorldRewind
ClockDuration != ExperiencedDuration != RememberedDuration
```

### Temporal Frame / Mapping

```text
TemporalFrame =
Events / Processes
+ TemporalRelations
+ optional Metric / Clock
+ ProgressionRule
```

Useful frames include wall, gameworld/simulation, coordination, fictive/narrative, subjective/experienced and authority time where rules need an exact reference.

```text
TemporalMapping(F_a → F_b)
```

may be 1:1, scaled, paused, discontinuous, compressed or action-triggered.

### Ordering / concurrency

```text
ClockOrder != CausalOrder
NetworkArrivalOrder != SemanticPriority
Simultaneity != Concurrency
SimultaneousResolution != ArbitrarySequentialization
```

For actions `a,b`, compare `T_a(T_b(s))` and `T_b(T_a(s))`; if unequal, explicit joint/priority/conflict/allocation semantics are required.

### Duration / timing / tempo / rhythm / pacing

```text
Duration = interval extent
Timing   = placement relative to event/window/reference
Tempo    = event/action/decision rate
Rhythm   = patterned interval/accent/phase relation
Pacing   = macro distribution of tension/decisions/feedback/recovery
```

```text
WorldSpeed != DecisionDensity
ReactionSpeed != AllTemporalSkill
```

### Turn / round / phase / tick

```text
Turn  = bounded opportunity/authority to commit action/decision
Round = recurring grouping/synchronization cycle
Phase = regime with different legality/information/resolution rules
Tick  = simulation/update quantum
```

### Temporalized action

```text
Opportunity
→ Intent
→ Commit
→ Wind-up / Preparation
→ Effect / Active interval
→ Completion
→ Recovery
→ Next availability
```

```text
WindUp != ActiveInterval != Recovery != Cooldown
```

### Windows / deadlines / pressure

```text
TemporalAffordance =
action possibility whose legality/effectiveness depends on temporal relation/window
```

Useful windows include availability, reaction, vulnerability, cancellation, commitment and information windows.

```text
Deadline = boundary after which legality/value/options change
Timeout  = consequence of noncompletion/nonresponse at boundary
Timer UI = representation only
```

```text
TemporalScarcity =
limited temporal opportunity relative to desired action/deliberation/coordination
```

### Waiting

Decompose:

```text
Access/dead
Process/maturation
Information
Strategic
Synchronization
Recovery/cooldown
Anticipatory/aesthetic
Asynchronous dependency
```

Meaningful waiting normally changes at least one of state, information, options, value/cost, strategy, synchronization or experience.

### Temporal Causality / Agency

```text
TemporalCausality =
important future properties counterfactually depend on
when, order, duration or synchronization
```

```text
TemporalAgency =
meaningful influence over
schedule / order / duration / rate / synchronization /
interruption / commitment / reversal
```

```text
TemporalAgency != ActingFaster
```

### Persistence / asynchrony

```text
Asynchronous != TurnBased
Persistence != ContinuousComputation
PersistentAgent != ThinkEveryTick
```

Event schedules, elapsed-time materialization and wake-on-relevance are valid when they preserve equivalent player-facing causality.

### Pause / reversal

```text
Pause = suspend selected temporal frames while others may continue
```

```text
Replay       = observe/reconstruct past
Undo         = cancel/compensate prior change
StateRestore = restore retained state
InWorldRewind= represented temporal-reversal mechanic
```

Crucial:

```text
WorldStateReversal != PlayerKnowledgeReversal
SameWorldState != SamePlayHistory
```

### Temporal Contract

```text
TemporalContract =
what advances / pauses / resolves first / expires / persists /
locks / can be reversed / which clock-order is authoritative
```

### Agent temporal fit

```text
Match Agent decision timescale to player-value timescale.
```

Potential temporal intent fields:

```text
EarliestStart
Deadline
DurationLimit
Cadence
Priority
Interruptibility
CancellationCondition
RetryWindow
SynchronizationCondition
```

### Playable Temporality

```text
PlayableTemporality =
temporal relations/windows/rates/orderings/mappings
that participants can perceive/model enough to anticipate,
influence or coordinate around,
and whose temporal differences alter meaningful futures
```

## Research boundary

Do not assume Game requires real-time action, metric seconds, global clocks, cooldowns or persistent simulation. Keep authored, turn-based, real-time, simultaneous, async, persistent, social, creative, narrative and generative forms open. No product winner exists; foundation rounds do not redefine G0–G8.

## How to continue R24

Start from continuity criteria, not character sheets or persona prompts.

Core question:

> What makes a Subject, character or collective count as the same entity through time, transformation, role change and social recognition?

Distinguish at least:

```text
Identity
Self
Character
Persona
Role
Avatar
Body
Name / Identifier
Continuity
Memory
History
Values / Commitments
Social Recognition
Status
Rank
Reputation
Alias
Disguise
Ownership
Provenance
Transformation
Replacement
Clone / Copy
Collective Identity
```

Questions:

1. Identity relative to memory/body/values/history/persistent state?
2. Character vs Subject vs Persona vs Avatar?
3. Role as capability/social expectation/institution position/narrative function?
4. Sameness across memory loss, body swap, rewind or reconstruction?
5. Self-identity vs observer-assigned identity?
6. Status vs Rank vs Reputation vs Power?
7. Development versus identity break?
8. Aliases/disguises/secret identities as playable uncertainty?
9. Identity constraints on goals/commitments/relationships/institutions?
10. Player identification vs R21 embodiment/body ownership?
11. Repeated expression/authorship becoming style/identity?
12. Generative Persona continuity without freezing variation?
13. Provenance across model/session/runtime boundaries?
14. Collective identity vs organization?

## High-priority warnings

```text
Identity != name/id
Character != Agent
Persona != prompt
Role != class
Memory != identity
Body != self
Reputation != identity
Continuity != continuous computation
More backstory != more character depth
```

## Product-selection stop condition

Do not begin intentional new-product G0 merely because the corpus is large. Finish remaining obvious foundations and later synthesize independent/redundant dimensions, candidate causal laws and high-information falsifiers before narrowing.
