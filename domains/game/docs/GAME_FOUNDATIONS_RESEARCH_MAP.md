---
schema_version: 1
id: game.foundations-research.map
title: Ordivon Game Foundations Research Map — R1–R18
type: research
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
summary: Compact navigation map for the R1–R18 Game foundations corpus, including core distinctions, cross-domain abstractions, motivational structure, open boundaries and the exact continuation point.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.r18
  - game.core-research.reset
  - game.development-model
---
# Ordivon Game Foundations Research Map

This is the compact navigation surface for [`GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](GAME_FOUNDATIONS_RESEARCH_R1_R17.md) plus [`GAME_FOUNDATIONS_RESEARCH_R18.md`](GAME_FOUNDATIONS_RESEARCH_R18.md). It is intentionally much shorter than the full research records.

## Boundary

```text
Research != product selection
Research rounds != G0–G8
AI Game != Agent World
Agent != LLM
Generation != gameplay by itself
```

No new product has been selected.

## R1–R18 index

| Round | Main subject | Durable distinction / result |
| --- | --- | --- |
| R1 | Game classification | Game forms occupy a multidimensional space; generative/open-ended interaction remains a first-class family. |
| R2 | Player-value families | Ability, Decision, World and Meaning are useful coarse consumption modes. |
| R3 | Atomic mechanics | Mechanics combine constraint, action, state change and feedback; recurring operations are Know, Act, Choose, Acquire/Transform, Relate, Create. |
| R4 | Loops | Healthy loops convert Question → Choice → Consequence → Learning → Changed State → New Question. |
| R5 | Motivation / fantasy | Design should start from desired experience/fantasy and motivation rather than available AI capability. |
| R6 | Fun / engagement / meaning | Player Value != Playtime; compulsion must be tracked separately from fun, satisfaction and meaning. |
| R7 | Tension / pacing | Tension comes from valued unresolved possibility; generation needs restraint, contrast and closure. |
| R8 | Story / narrative | Event != Story != Narrative != Meaning; generative narrative needs governance, not only generation. |
| R9 | World / simulation | World != Map/Lore/Simulation; preserve the causality needed by the experience rather than maximize realism. |
| R10 | Subject / Agent | NPC != Agent != LLM; richer cognition matters only when it changes meaningful play. |
| R11 | Agency / consequence | Freedom and button count are not agency; open intent can coexist with structured consequences. |
| R12 | Feedback / learning | Actual causality must become perceived/learnable causality; complexity and intelligence must be playable. |
| R13 | Time / history | Progression, persistence, memory, history and learning are separate; history becomes valuable when past becomes present structure. |
| R14 | Economy | Resource ≈ stored optionality; scarcity creates trade-off; economy is multi-subject coordination under constrained resources/claims. |
| R15 | Society / institutions | Organization != Institution; institutions can be history compressed into future rules. |
| R16 | Space / topology | Topology = structure of reachability/influence; distance is transition cost; exploration grows a usable world model. |
| R17 | Information / belief | Truth != Signal != Observation != Belief != Statement; bounded knowledge and information topology generate play. |
| R18 | Motivation / goals | Need, Value and Desire are distinct motive sources; Preference is contextual comparison; Goal is selected pursuit; Commitment stabilizes it; Utility is optional representation/arbitration. |

## Current multidimensional GameForm model

```text
GameForm =
Interaction
× Control
× World
× Time
× Space
× ContentSource
× GoalStructure
× SocialStructure
× Value
```

Historical genres are stable clusters, not the fundamental ontology.

## Current player–world loop

```text
WORLD
State / Rules / Subjects / Resources / Topology / Information
        ↓ Evidence
PLAYER
Perception
→ Mental Model
→ Desire
→ Choice
→ Action
        ↓
WORLD CONSEQUENCE
        ↓
Feedback
→ Attribution
→ Learning / Feeling
→ Changed Possibility
        ↺
```

## World stack

```text
State
→ Rules
→ Transitions
→ Dynamics
→ Subjects / Policies
→ Interactions
→ Persistent Traces
→ History
→ Emergent Structure
```

The world may be physical, social, epistemic, economic, institutional, narrative/contextual or hybrid. A strong simulation is not mandatory for every game form.

## Subject stack

```text
Identity
→ Situated Observation
→ Belief / Internal State
→ Motive Structure / Commitments
→ Policy
→ Action
→ World Consequence
→ Feedback
→ Memory / Learning
```

R18 refines the motive layer:

```text
MotiveStructure =
RegulatoryPressure
+ EvaluativeStructure
+ CurrentSalience

Need    = requirement pressure
Value   = evaluative structure
Desire  = current motivational salience
Preference = contextual comparison
Goal       = selected future/trajectory to pursue
Intention  = Goal + persistence/reconsideration
Utility    = optional numerical representation/arbitration
```

Use the lowest motivational complexity that creates a new playable causal distinction. `Want` is normally a surface-language term rather than a mandatory primitive.

Implementation options for policy include scripts, FSMs, behavior trees, utility systems, planners, search, RL, models, humans and hybrids.

## Temporal stack

```text
Momentary State
→ Event
→ Persistent Trace
→ Memory
→ History
→ Development
→ Identity / Institution / Culture
→ Future Policy
```

Core distinction:

```text
StoredPast != FunctionalMemory
History != EventLog
```

## Narrative stack

```text
World Events
→ Persistent History
→ Causal Structure
→ Salience Selection
→ Narrative Framing
→ Player Interpretation
→ Personal Meaning
```

Generation may enter at several points; it is not synonymous with narrative authority or world authority.

## Agency profile

Agency should not be reduced to one score. Analyze at least:

```text
Domain
Scale
Freedom
Control
Influence
Consequence
Persistence
Legibility
Commitment
```

Useful relationship:

```text
AgencyValue ≈
ValuedAlternatives × Influence × Consequence × Legibility
```

For natural-language interaction distinguish:

```text
Expressive Agency
Narrative Agency
World/Causal Agency
Meta-Authorial Agency
```

A useful generative pattern:

```text
OpenIntentSpace + StructuredConsequenceSpace
```

## The Playable-X family

Internal sophistication is not enough. Across domains the common criterion is player-accessible causal structure.

```text
PlayableComplexity
PlayableIntelligence
PlayableEconomy
PlayableSociety
PlayableTopology
PlayableInformation
PlayableMotivation
```

Generalized:

```text
Playable X =
X that players can observe,
model,
test/influence,
and use to improve future decisions or expression.
```

## Possibility-space translation

A cross-round language that repeatedly worked:

| Concept | Possibility interpretation |
| --- | --- |
| Resource | Stored optionality. |
| Power | Ability to alter/reach more futures. |
| Agency | Selection among meaningful future trajectories. |
| Progression | Transformation of future play. |
| Movement | Exchange current position for a different reachable future set. |
| Creation | Add new artifacts/possibilities. |
| Institution | Structure others' permitted/expected future interaction. |
| Information | Improve prediction/action over future possibilities. |
| History | Past choices constrain present/future possibilities. |

Do not treat this as a proven final ontology; retain it as a high-yield abstraction.

## Recurring high-value hybrid patterns

### Stable semantics + variable realization

```text
Stable rules / grammar / causal meaning
+
procedural or generated content / expression
```

Supports novelty without destroying learnability.

### Hard fact + soft interpretation

```text
Hard event / state
+
soft belief / narrative / emotion / expression
```

Supports rich generative behavior without making prose authoritative truth.

### Structured freedom

```text
Many meaningful options
+
constraints / costs / commitment
```

is often richer than arbitrary wish fulfillment.

### Local closure + persistent possibility

Open-ended systems can retain satisfaction by closing local arcs while the world continues.

## Generative-system liabilities to remember

Generative capability reduces content-production cost but increases governance burdens.

```text
Generated setup     → payoff debt
Generated character → continuity debt
Generated world fact → causal-state debt
Generated place      → topological debt
Generated relationship claim → future-behavior debt
```

Potential scarce resources therefore shift toward:

```text
selection
commitment
integration
continuity
closure
forgetting
```

## Information model

```text
WorldTruth
→ Signal
→ Observation
→ Interpretation
→ Belief
→ Communication Intent
→ Statement
→ Other Subject Belief
```

Key consequences:

- Subjects should not automatically share omniscient truth.
- False belief can create real world consequence.
- Secrets matter when distribution matters.
- Deception is action on another subject's belief.
- UI defines the player's observation function.
- Generated dialogue can express a character's belief without becoming world truth.

## Social model

```text
Individual Action
→ Relation
→ Group Pattern
→ Norm
→ Organization
→ Institution
→ Future Individual Action
```

Organization coordinates subjects; institution structures repeated interaction. Laws, norms, preferences and physical rules should remain distinct.

## Economy model

```text
Need
→ Acquire
→ Produce
→ Allocate
→ Consume / Invest
→ New Need
```

With multiple subjects:

```text
Production
→ Exchange
→ Specialization
→ Interdependence
→ Coordination / Institutions
```

Do not let a universal economy/currency consume all other value dimensions.

## Topology model

Topology is not limited to physical maps.

```text
Physical topology
Social topology
Information topology
Economic/logistics topology
Narrative topology
Capability topology
Organizational topology
```

For any topology ask:

```text
What are the nodes?
What are the edges?
What is edge cost/capacity/direction?
Who can see/control the edge?
Can the topology change?
Does changing it alter future possibilities?
```

## Player-value guardrails

```text
PlayerValue != PlayTime
Complexity != Depth
Difficulty != Complexity
ContentDiversity != InteractionDiversity
AgentCount != SocialDepth
MemoryAmount != MemoryQuality
WorldSize != SpatialDepth
```

A practical test remains:

> If extrinsic rewards, AI novelty and technical spectacle were removed, what core behavior would still be worth doing?

## Exact frontier

R18 is complete. Continue with:

```text
R19 — Conflict, Cooperation, Competition, Coordination, Bargaining, Strategy and Equilibrium
```

Primary transition:

```text
R18: Why does one Subject select one future over another?
→
R19: What happens when multiple Subjects can alter one another's reachable futures?
```

Do not select a product before R19 and the remaining adjacent foundational dimensions have been examined and then synthesized.
