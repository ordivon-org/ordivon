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
summary: Exact continuity handoff for resuming the Game foundations programme after R1–R22 without depending on the originating conversation context.
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
  - game.foundations-research.map
  - game.core-research.reset
---
# Ordivon Game Foundations Research Continuation Handoff

## Read first

1. [`GAME_FOUNDATIONS_RESEARCH_R22.md`](GAME_FOUNDATIONS_RESEARCH_R22.md) — canonical R22 decomposition of uncertainty, probability, randomness, risk, luck, variance, determinism, predictability and fairness.
2. [`GAME_FOUNDATIONS_RESEARCH_MAP.md`](GAME_FOUNDATIONS_RESEARCH_MAP.md) — compact R1–R22 conceptual map and cross-round abstractions.
3. [`GAME_FOUNDATIONS_RESEARCH_R21.md`](GAME_FOUNDATIONS_RESEARCH_R21.md) — control/action-causality layer that R22 extends into Distributional Agency.
4. [`GAME_FOUNDATIONS_RESEARCH_R20.md`](GAME_FOUNDATIONS_RESEARCH_R20.md) — creation/authorship layer.
5. [`GAME_FOUNDATIONS_RESEARCH_R19.md`](GAME_FOUNDATIONS_RESEARCH_R19.md) — strategic-interdependence layer.
6. [`GAME_FOUNDATIONS_RESEARCH_R18.md`](GAME_FOUNDATIONS_RESEARCH_R18.md) — motivation/goal/utility layer.
7. [`GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](GAME_FOUNDATIONS_RESEARCH_R1_R17.md) — canonical snapshot of the first seventeen foundation rounds.
8. [`DEVELOPMENT_MODEL.md`](DEVELOPMENT_MODEL.md) — sole authority for G0–G8 product-development meanings.

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
R18 Need / Want / Desire / Goal / Preference / Utility / Value / Commitment
R19 Strategic Interdependence / Conflict / Competition / Cooperation / Coordination / Bargaining / Strategy / Equilibrium
R20 Creation / Creativity / Construction / Expression / Authorship / Customization / Style / Co-creation
R21 Embodiment / Control / Input / Skill / Affordance / Game Feel / Presence
R22 Uncertainty / Probability / Randomness / Risk / Luck / Variance / Determinism / Fairness
```

Exact next round:

```text
R23 — Time, Sequence, Simultaneity, Duration, Timing, Rhythm, Turn, Cooldown, Deadline and Temporal Agency
```

## Stable pre-R22 boundaries

```text
AI Game != Agent World
Agent != LLM
Generation != gameplay
Freedom != Agency
Memory != History
Need != Desire
Desire != Goal
Goal != Intention
Preference != Utility
Communication != Commitment
Equilibrium != Product Value
Creation != Creativity
Authorship != Ownership
Control != SenseOfAgency
Avatar != Body
Embodiment != Presence
```

R20:

```text
AuthorialCausality =
important artifact properties counterfactually depend
on meaningful participant decisions
```

R21:

```text
ActionCausality =
important action/outcome properties counterfactually depend
on participant intent/control
```

```text
IntentFidelity =
value-bearing intent distinctions survive
interpretation, planning and execution
```

## R22 durable result

Core separations:

```text
Uncertainty != Randomness != Unpredictability
Probability != Uncertainty itself
Risk != Variance != ExpectedValue
Luck != Randomness
Fairness != Symmetry != OutcomeEquality != Balance
DecisionQuality != OutcomeQuality
```

### Uncertainty

```text
Uncertainty(subject/model, X, t) =
multiple materially plausible states/models/outcomes of X
remain open under accessible evidence/model at time t
```

Uncertainty requires specifying:

```text
bearer
object
time
information boundary
model boundary
```

### World branching versus epistemic spread

```text
WorldBranching =
same conditioning state/action can resolve to multiple next states
under the chosen authoritative model
```

```text
EpistemicSpread =
participant/model does not know which state/model/outcome is true,
even if authoritative reality is fixed
```

Randomness is only one uncertainty source.

### Uncertainty Topology

```text
UncertaintyTopology = {
  Bearer,
  Object,
  Source,
  ModelBoundary,
  Reducibility,
  RealizationTime,
  Observability,
  Controllability,
  Stakes,
  UpdatePath
}
```

Sources can include:

```text
hidden information
stochastic transition
other Subject policy
computational complexity
chaotic sensitivity
model ambiguity
semantic ambiguity
generative sampling
```

### Epistemic / aleatory

```text
EpistemicUncertainty =
missing knowledge/state/parameter/model uncertainty
at the current boundary
```

```text
AleatoryUncertainty =
variation represented as irreducible random realization
within the current model boundary
```

The distinction is model-relative. A PRNG system can be deterministic under complete seed/state and stochastic at the player-facing abstraction.

### Determinism / predictability

```text
Determinism = full state + rules uniquely determine next state
Predictability = bounded predictor can forecast relevant future accurately enough
```

Therefore:

```text
Determinism != Predictability
```

Hidden state, computation, chaos and strategic opponents can make deterministic systems unpredictable.

### Probability / ambiguity

```text
Probability =
quantitative distribution/measure assigned to alternatives
under a specified model/belief state
```

Probability needs provenance. `30%` is incomplete without model/conditioning/source.

```text
Ambiguity =
uncertainty about distribution/model/parameters,
not merely which outcome realizes
```

### Randomness placement

```text
before decision
→ adaptation problem

after commitment
→ risk-bearing resolution

hidden pre-existing state
→ inference/scouting problem

continuous disturbance
→ control/robustness problem
```

Where randomness enters is more important than an undifferentiated “RNG amount.”

### Risk

R7's early heuristic:

```text
Risk ≈ ProbabilityOfLoss × SubjectiveValueOfLoss
```

is superseded as a general definition by:

```text
Risk =
exposure to materially valued consequence distributions
under uncertainty,
especially where adverse outcomes matter
```

Relevant structure may include:

```text
probabilities
loss/gain magnitudes
variance
skew
tails
ruin thresholds
reversibility
correlation
path dependence
controllability
ambiguity
```

### Expected value / variance

```text
ExpectedValue = probability-weighted mean
Variance = one dispersion measure
```

Neither is the full distribution or universal risk measure.

```text
ExpectedValue != Distribution
Variance != Risk
```

### Luck

```text
Luck =
retrospective attribution that a valued realized outcome
depended materially on factors outside the relevant participant's
control, skill or available knowledge
```

Luck can arise without literal random mechanics.

### Outcome Contribution Topology

```text
OutcomeContributionTopology =
which factors materially shaped the realized outcome:
player policy / execution / opponent / hidden state /
stochastic realization / environment / information / AI interpretation
```

Do not replace this with one arbitrary “skill vs luck percentage.”

### Decision Quality / Outcome Quality

```text
DecisionQuality =
quality of choice given information/model/objectives/constraints
available at decision time
```

```text
OutcomeQuality =
value of realized consequence
```

Thus:

```text
GoodDecision + BadLuck → BadOutcome
BadDecision + GoodLuck → GoodOutcome
```

### Skill under uncertainty

```text
SkillUnderUncertainty =
learned ability to improve outcome distributions
or decision quality under uncertainty,
not guarantee every sample
```

Skill may include:

```text
hedging
information acquisition
variance management
robust policy
reserve management
adaptation
```

### Distributional Agency

```text
DistributionalAgency =
ability to intentionally change the distribution/set
of meaningful future outcomes
without selecting the exact realization
```

This is how R21 ActionCausality survives chance.

### Fairness

```text
Fairness =
judgment that rules, procedures, opportunities, information,
uncertainty and outcomes are acceptably justified
relative to the relevant game/social contract
```

Keep distinct:

```text
Procedural Fairness
Opportunity / ex-ante Fairness
Informational Fairness
Causal / Skill Fairness
Distributive Fairness
Perceived Fairness
```

Preserve:

```text
Fairness != OutcomeEquality
Fairness != Symmetry
Fairness != Balance
```

A fair lottery can generate unequal outcomes; an equal outcome can come from an unfair process.

### Uncertainty Contract

```text
UncertaintyContract =
what is random?
what is hidden?
what can be learned?
what can be controlled?
when is chance resolved?
how severe can outcomes be?
are odds stable?
can exposure be mitigated?
```

A bad beat can be painful, unlucky and still fair when the process/uncertainty contract is sufficiently clear.

### Playable Uncertainty / Risk

```text
PlayableUncertainty =
uncertainty whose relevant alternatives/sources can be
partially modeled, investigated, anticipated or acted around,
and whose resolution provides useful causal evidence
```

```text
PlayableRisk =
valued uncertain consequence exposure
that players can understand enough to choose,
mitigate, hedge, accept, reject or increase
```

### Generative systems

Keep distinct:

```text
Sampling variation
Knowledge/model uncertainty
Instruction ambiguity
Unknown external state
```

Their remedies differ:

```text
sampling variation → constrain/resample if useful
knowledge uncertainty → seek evidence / represent epistemic status
instruction ambiguity → interpret cautiously / expose consequential interpretation
external state uncertainty → observe authoritative source
```

Preserve:

```text
SampledOutput != WorldTruth
```

## Research boundary that must survive the context switch

Do not assume uncertainty means casino mechanics or explicit probabilities.

Search space remains broad:

```text
deterministic authored games
hidden-information games
stochastic/systemic games
action games
strategy/command games
social deduction / bargaining
creative sandboxes
procedural/generative worlds
SillyTavern-like roleplay
persistent Agent worlds
hybrids
```

No product winner exists. Foundation rounds do not redefine G0–G8.

## How to continue R23

Start from **temporal ordering and temporal possibility**, not from animation timing or current Station Zero turn code.

Core question:

> How are actions, opportunities and consequences ordered through time, and how does temporal structure itself create choice, skill, coordination, commitment and meaning?

Distinguish at least:

```text
Game Time
Real Time
Simulation Time
Subjective / Player Time
Sequence
Order
Simultaneity
Concurrency
Turn
Phase
Tick
Duration
Timing
Tempo
Rhythm
Cooldown
Wind-up
Recovery
Deadline
Waiting
Delay
Commitment Window
Initiative
Asynchrony
Persistence
Reversibility
Pause
Rewind
Save/Load
Temporal Agency
```

Questions worth attacking:

1. What kinds of Time exist in a game, and which are authoritative?
2. When does ordering itself change causality/strategy?
3. How do simultaneity, turns, phases, ticks and asynchronous action differ?
4. How do Duration, Timing, Tempo and Rhythm differ?
5. What are wind-up/recovery/cooldown as temporal constraints rather than UI timers?
6. When does waiting become strategic commitment rather than dead time?
7. How do deadlines/time pressure transform preference and risk?
8. What is initiative/turn-order advantage?
9. How should concurrent conflicting actions resolve fairly?
10. How do pause, rewind, undo and save/load alter consequence/commitment?
11. How do persistent/offline/asynchronous worlds change agency and social coordination?
12. How should Agent systems act over continuous, turn-based and long-horizon asynchronous time?
13. How does R21 responsiveness differ from Game-world time?
14. How does R22 risk evolve with time, decay, hazard and information arrival?

## Expected R23 output shape

```text
1. separate time/sequence/timing/tempo/rhythm/turn concepts;
2. derive minimal temporal state-transition structure;
3. compare turn-based, real-time, phased, ticked, paused and asynchronous forms;
4. study simultaneity/concurrency/initiative;
5. study duration/windows/cooldowns/deadlines/waiting;
6. study reversibility/pause/save-load;
7. test action, strategy, social, creative and generative forms;
8. identify temporal failure modes;
9. reconnect loops/pacing/history/control/risk;
10. end with next foundation frontier, not product selection.
```

## Stable cross-round abstractions

```text
Question
→ Choice
→ Consequence
→ Learning
→ ChangedState
→ NewQuestion
```

```text
Truth != Signal != Observation != Belief != Statement
```

```text
AuthorialCausality
ActionCausality
DistributionalAgency
```

```text
Playable X =
X that players can observe, model, influence/test,
and use to improve future decisions or expression
```

## High-priority warnings

Do not regress into:

```text
“Uncertain means random.”
“Random means unfair.”
“Higher EV means better decision.”
“Bad outcome means bad play.”
“More variance means more tension.”
“Exact percentages are required for legibility.”
“More buttons means more control.”
“Generation means creativity.”
“More simulation means more depth.”
```

## Product-selection stop condition

Do not begin intentional new-product G0 merely because the corpus is large.

Before narrowing, continue to:

- finish remaining obvious foundational dimensions;
- synthesize independent versus redundant dimensions;
- identify a smaller set of candidate causal laws;
- compare materially different authored, systemic, social, creative and generative families;
- design high-information falsifiers;
- state what remains unknown.
