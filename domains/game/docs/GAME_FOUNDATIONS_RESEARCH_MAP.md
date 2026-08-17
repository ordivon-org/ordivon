---
schema_version: 1
id: game.foundations-research.map
title: Ordivon Game Foundations Research Map — R1–R21
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
summary: Compact navigation map for the R1–R21 Game foundations corpus, including core distinctions, cross-domain abstractions, motivational, strategic, creative and control/embodiment structure, open boundaries and the exact continuation point.
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
  - game.core-research.reset
  - game.development-model
---
# Ordivon Game Foundations Research Map

This is the compact navigation surface for [`GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](GAME_FOUNDATIONS_RESEARCH_R1_R17.md), [`GAME_FOUNDATIONS_RESEARCH_R18.md`](GAME_FOUNDATIONS_RESEARCH_R18.md), [`GAME_FOUNDATIONS_RESEARCH_R19.md`](GAME_FOUNDATIONS_RESEARCH_R19.md), [`GAME_FOUNDATIONS_RESEARCH_R20.md`](GAME_FOUNDATIONS_RESEARCH_R20.md), and [`GAME_FOUNDATIONS_RESEARCH_R21.md`](GAME_FOUNDATIONS_RESEARCH_R21.md). It is intentionally much shorter than the full research records.

## Boundary

```text
Research != product selection
Research rounds != G0–G8
AI Game != Agent World
Agent != LLM
Generation != gameplay by itself
```

No new product has been selected.

## R1–R21 index

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
| R19 | Strategic interdependence | Strategic relevance depends on policy-contingent mutual consequence; conflict/competition/cooperation/coordination differ; bargaining needs outside options and commitment; equilibrium is an incentive diagnostic; strategy must be playable. |
| R20 | Creation / authorship | Creation, Creativity, Expression and Authorship are distinct; creative possibility is structured by material/tool/grammar/constraint; authorship follows meaningful decision locus rather than raw output share; generation is only one mechanism. |
| R21 | Embodiment / control | Intent, Input, Command, Action and Outcome are distinct; Control Locus is broader than Avatar/Body; agency, body ownership and presence separate; affordance is relational; shared/delegated control must preserve intent; control must be playable. |

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

R19 adds the strategic layer:

```text
StrategicRelevance(j → i)
= changing i's belief about j's policy can change i's preferred response

StrategicInterdependence(i, j) =
MutualConsequenceCoupling
+ PolicyContingency
+ Belief / Anticipation

StrategicTopology =
who can alter whose reachable valued futures
through policy/consequence influence edges
```

Key R19 separations:

```text
Conflict     = incompatible preferred futures
Competition  = rivalry over scarce/relative outcomes
Cooperation  = intentional joint strategic benefit
Coordination = compatible action/convention selection
Bargaining   = selection among acceptable joint outcomes under disagreement
Negotiation  = strategic communication around information/proposals/commitments
Strategy     = policy conditioned on anticipated other-policy
Equilibrium  = stability under a specified deviation model
```

R19 discipline:

```text
Do not maximize opponent intelligence.
Expose meaningful conditional response.
Use equilibrium to debug incentives, not to define fun.
Keep strategic information bounded.
Soft negotiation + structured strategic transition where persistence matters.
```

R20 adds the creative layer:

```text
Creation = deliberate organization/transformation into Form
Creativity = meaningful novelty + contextual value/appropriateness
Expression = legible identity / stance / taste / meaning
Authorship = meaningful causal responsibility for form/meaning
Customization = bounded personalization
Generation = candidate production mechanism
```

```text
CreativePossibilitySpace =
Materials × Tools × Grammar × Constraints × Skills × Time
```

R20 discipline:

```text
Track decision locus, not token/pixel share.
Authorial causality asks which artifact properties change when player decisions change.
Constraints can create semantic contrast and mastery.
Curation can carry authorship when selection/framing is consequential.
Automate unwanted realization friction, not the intended creative question.
Generation != Creativity != Player Authorship.
```

R20 also adds `CreativeContributionTopology`: who contributes to framing, constraints, structure, realization, selection, evaluation, revision, integration and commitment.

R21 adds the control/embodiment layer:

```text
Intent
→ Control Expression
→ Input / Command
→ Mapping / Interpretation
→ Candidate Action
→ Capability + Affordance + Legality + World Resolution
→ Consequence
→ Feedback
→ Attribution / Sense of Agency
→ Learning
```

Key R21 separations:

```text
Input != Intent != Action != Outcome
Control != SenseOfAgency
Avatar != Body
BodyOwnership != Agency
Embodiment != Presence
Affordance != Capability != Legality
Latency != Responsiveness
DirectManipulation != Agency
Automation != AgencyLoss
```

R21 adds:

```text
ActionCausality =
important action/outcome properties counterfactually depend on participant intent/control

ControlLocus =
where participant control enters authoritative state change
without assuming a body/avatar

IntentFidelity =
value-bearing distinctions in participant intent survive
interpretation, planning and execution

ControlContributionTopology =
who controls which action layer / variable / time interval / correction path
```

R21 discipline:

```text
Preserve the player-value layer of Intent.
Do not confuse directness with agency.
Do not confuse automation with agency loss.
Do not hide assistance/control authority when attribution matters.
Preserve resistance that carries intended skill/fantasy; remove access overhead.
```

Implementation options for policy include scripts, FSMs, behavior trees, utility systems, planners, search, regret minimization, RL, models, humans and hybrids.

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
PlayableStrategy
PlayableCreation
PlayableExpression
PlayableControl
PlayableEmbodiment
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

R21 is complete. Continue with:

```text
R22 — Uncertainty, Probability, Randomness, Risk, Luck, Variance, Determinism and Fairness
```

Primary transition:

```text
R21: How does intent become controlled and attributable action?
→
R22: What changes when action outcomes, information or future states cannot be known or controlled exactly?
```

Do not select a product before R22 and the remaining adjacent foundational dimensions have been examined and then synthesized.
