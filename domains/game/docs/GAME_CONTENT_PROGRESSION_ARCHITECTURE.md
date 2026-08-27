---
schema_version: 1
id: game.content-progression-architecture
title: Ordivon Game — Content / Progression Architecture
profile: product
lifecycle: active
source_role: canonical-supporting-model
visibility: public
owners:
  - ordivon-game
updated: 2026-08-28
summary: Practical D5 construction model for turning a bounded game kernel into learnable depth, content breadth, pacing, progression and sustainable production. It is derived from frozen Game semantics and cross-case development evidence; it creates no new Foundation, product stage, engine or content service.
evidence_status: derived
readiness: CURRENT
applies_to:
  - ordivon-game
related:
  - game.development-core
  - game.development-case-pressure-tests
  - game.development-model
---
# Ordivon Game — Content / Progression Architecture

## 0. Boundary

This is a **development construction model**, not a new semantic ontology.

```text
ContentProgressionArchitecture
!= GDF
!= Runtime schema
!= universal level format
!= content database
```

It exists because real game development repeatedly forces one question that `ContentGrammar` alone cannot answer:

> How does a bounded mechanic/rule set become a coherent sequence or field of learnable, replayable and producible player possibilities?

## 1. The central correction

The naive pipeline is:

```text
make mechanics
→ make content
→ add progression
```

Cross-case evidence rejects this as a universal process.

A stronger model is:

```text
Kernel Possibilities
↔ Player Learning / Capability
↔ Content Exposure / Composition
↔ Progression State / Meaning
↔ Expression
↔ Production Capacity
↔ Evidence
```

Content and progression can change the meaning and viability of the kernel itself.

## 2. Four graphs that must not be collapsed

### 2.1 Possibility Graph

What the game rules currently make possible.

```text
node = relevant game-state / strategic possibility class
edge = legal meaningful transformation
```

Examples:

- Celeste: movement/obstacle combinations;
- Factorio: production/logistics constructions;
- Into the Breach: tactical counterplay states;
- Hades: build/tool combinations;
- Outer Wilds: actions/locations enabled by current knowledge.

### 2.2 Player Capability / Model Graph

What the target player is expected to understand, execute or reason about.

```text
node = learning / skill / mental-model capability
edge = practical prerequisite or transfer relation
```

This is a **design hypothesis**, not direct access to Human cognition.

### 2.3 Exposure / Content Graph

What situations the product presents and in what relationship.

```text
node = level / encounter / quest / event / room / scenario / authored beat / generated class
edge = sequence, prerequisite, branch, recurrence, conditional availability or recombination relation
```

### 2.4 Production Graph

What the development environment can repeatedly create and validate.

```text
node = content class / source / tool / pipeline / review capability
edge = dependency / transformation / validation / integration relation
```

A design can be theoretically deep and still fail because the Production Graph cannot realize enough valid content at sustainable cost.

## 3. D5 is graph alignment, not one progression curve

A robust content architecture continuously asks whether these graphs align.

Examples of failure:

```text
Exposure ahead of Capability
→ confusion / opaque difficulty

Capability ahead of Exposure
→ boredom / underuse of learned depth

Possibility ahead of Production
→ rich design space that cannot be authored/tested at scale

Production ahead of Possibility
→ high content volume with shallow systemic variation

Reward ahead of meaningful possibility
→ number growth without new play
```

Therefore:

```text
D5Quality ≈ useful alignment among
Possibility × Capability × Exposure × Production
```

not one scalar content count.

## 4. Progression carriers

Progression means a change that materially alters later play/interpretation; it does not imply XP or persistent account state.

Use the smallest relevant carrier set:

### P1 Skill progression

The Human becomes better at execution, timing, planning or interpretation.

Game can structure practice and observe performance; it does not own the Human capability state as truth.

### P2 Knowledge progression

The player learns causal/world information that changes later decisions.

Outer Wilds is the strong case.

### P3 Possibility / access progression

New verbs, tools, spaces, actions, recipes, build components or social options become reachable.

### P4 Power / resource progression

Capacity, efficiency, survivability or economic leverage changes.

### P5 Complexity progression

Previously independent systems become coupled or combinatorial.

Factorio frequently uses this carrier.

### P6 Relationship / identity progression

Future actions/interpretations change because characters, roles, reputation, commitments or history changed.

### P7 World transformation progression

The environment itself becomes a new problem/possibility space because prior actions changed it.

### P8 Content / narrative exposure progression

New authored/generated material becomes meaningful or available based on prior play.

### P9 Social / institutional progression

Population, guild, faction, economy or institution standing changes future opportunity.

No product needs all nine.

## 5. Content unit roles

A content unit is not defined only by medium.

A room, encounter, mission, card set, dialogue event, planet, puzzle, quest or generated configuration may serve one or more roles:

```text
Introduce
Practice
Vary
Combine
Stress
Contrast
Recover
Reward
Reveal
Recontextualize
TestTransfer
Express
Branch
Conclude
```

This role view is more reusable than assuming:

```text
Level 1 = easy
Level 2 = harder
Level 3 = harder again
```

## 6. Mechanic-depth construction

For each durable mechanic family, expose its transformation space rather than immediately inventing another mechanic.

```text
MechanicDepthSpace =
ParameterVariation
× ContextVariation
× CombinationWithOtherMechanics
× Resource / information pressure
× Temporal pressure
× Spatial/topological pressure
× Goal/evaluation change
× Opponent/environment response
× Player-control constraint
```

Depth pressure asks:

> Can existing mechanics produce a materially new decision/skill/interpretation under a changed context?

Only when the answer repeatedly becomes no should a new mechanic receive content budget by default.

This is not a prohibition on novelty. It is a defense against one-shot mechanic sprawl.

```text
Breadth != Depth
MoreContent != MorePossibility by identity
```

## 7. Learning / challenge progression

Use GDF1/GDF2 boundaries but add a constructive sequence view.

A candidate learning chain can be:

```text
Expose distinction
→ safe recognition
→ bounded action
→ feedback
→ repeated variation
→ interference / combination
→ reduced scaffolding
→ transfer
→ novel composition
```

A challenge increase can come from different pressure dimensions:

```text
execution precision
reaction/time
state-space size
information uncertainty
resource scarcity
planning horizon
opponent adaptation
coordination
recovery cost
simultaneous goals
```

Therefore:

```text
Harder != BiggerNumber
```

and:

```text
DifficultyProgression
must name which pressure changed.
```

## 8. Reward / option topology

A progression reward should be represented by what later possibility it changes.

```text
RewardEffect =
new verb
| new combination
| greater efficiency
| new information
| new location
| new expressive option
| new relationship/status
| reduced friction
| altered risk profile
| purely extrinsic signal
```

A reward that only changes an external number may still be useful, but should not be mistaken for increased game depth.

Factorio's science progression is a strong example where unlocks also guide the player toward production structures and new system couplings.

## 9. Macro architecture

Macro structure is the long-horizon organization of content and progression.

Possible forms include:

```text
linear chapters
branching campaign
hub-and-spoke
run-based recombination
open knowledge graph
technology tree
world regions
mission network
season/live cadence
UGC/social feed
persistent systemic world
```

Do not select one by genre convention alone.

A useful macro architecture answers:

```text
What can the player choose next?
What are they expected to understand by then?
What changes if they choose a different route/order?
What recurs, escalates or transforms?
How does the structure end, loop or remain open?
```

## 10. Content grammar

A content grammar should describe how valid content is produced, not only list types.

```text
ContentGrammar != ContentList
```

```text
ContentGrammar =
UnitTypes
+ Required semantic roles
+ Allowed combinations
+ Constraints / invariants
+ Variation dimensions
+ Difficulty/pressure dimensions
+ Prerequisite assumptions
+ Reward/consequence forms
+ Expression requirements
+ Validation rules
```

Optional realization mechanisms:

```text
hand authorship
systemic recombination
procedural generation
search/optimization
UGC
Agent/generative production
hybrid workflows
```

Mechanism choice does not change Game's ownership of gameplay validity.

## 11. Generators and production tools

External modern engines reinforce a durable distinction:

```text
Generator != ContentAuthority
```

Unreal Engine 5.8 PCG, for example, provides editable/extensible procedural graphs, shape grammars, runtime/editor generation and integration with traditional world-building pipelines.

A production Agent or generator can own:

```text
proposal / draft / transformation / search
```

while Game retains:

```text
constraints
validation
selection
integration
consequence
```

The important D5 question is not “can AI generate more levels?” It is:

> Can the production system generate or assist content that occupies the intended Possibility/Capability/Exposure region without making validation and curation cost explode?

## 12. Content-production economics

Track at least:

```text
UnitCost
IterationLatency
ValidationCost
ReuseFactor
VariationYield
DefectRate
ExpressionCost
IntegrationCost
CurationCost
```

A generator that produces ten times more candidates but requires twenty times more review is negative leverage.

Likewise, one highly reusable mechanic that creates many valid compositions may dominate many bespoke content units.

## 13. Evidence horizon and content horizon

Content architecture spans multiple causal horizons:

```text
interaction
encounter
session
run
campaign
cross-session
live population window
```

Every major content/progression claim should name its horizon.

Examples:

```text
Celeste room teaches dash timing     → interaction/encounter
ITB island choice affects campaign   → run/campaign
Hades dialogue recurrence            → run/cross-run
Factorio tech branch                 → long session/campaign
Roblox onboarding change             → session + D1/D7 population windows
```

This prevents high-frequency micro evidence from silently dominating low-frequency macro decisions.

## 14. Content Unit Evidence View

Do not persist this universally. Use it when a real production/research decision needs the structure.

```text
ContentUnitEvidenceView =
Purpose / target dynamic
ProgressionCarrier(s)
Prerequisite capability/model assumptions
Mechanics introduced / varied / combined
Pressure dimensions
Reward / future-option effect
Expression criticality
Evidence horizon
Expected observation
Production class / cost
Validation method
Reuse / transformation role
Known omissions
```

This is a positive Agent affordance: an Agent can ask what a content unit is *for* instead of inferring purpose from filenames or level numbers.

## 15. Macro Content Standing

Before scaling production, a bounded product should be able to answer:

```text
MechanicDepth:      where does repeated depth come from?
LearningStructure:  how does player capability/model grow?
ProgressionCarrier: what actually changes future play?
MacroTopology:      how are content units related over time?
VariationSystem:    why is repeated content not equivalent?
ProductionModel:    how are valid units repeatedly created?
ValidationModel:    how do we detect shallow/broken/redundant units?
EvidenceHorizon:    when can important effects be observed?
```

This is not a release gate by itself. It is D5 standing.

## 16. Agent-first implications

Production Agents are especially valuable in D5 for:

```text
searching mechanic combinations
proposing content variants
building grayboxes
simulating trajectories
finding degenerate strategies
measuring parameter sensitivity
generating draft assets/data
operating editors
checking grammar/invariants
clustering play traces
identifying underused mechanics
```

But Agent output must be evaluated against two different objectives:

```text
SearchLeverage
and
ProductionLeverage
```

A weird disposable level that discovers a new mechanic interaction may have high SearchLeverage and zero ProductionLeverage.

A reliable generator that fills a proven grammar may have high ProductionLeverage and little SearchLeverage.

Do not collapse them.

## 17. Current Ordivon consequence

No new content needs to be built for Station Zero, Casefile or existing playables.

Use them only when an unresolved D5 claim happens to match their evidence capabilities.

For future products, the first D5 work should not be “make content.” It should be:

```text
identify progression carrier
→ expose mechanic depth space
→ model player-learning assumptions
→ select macro topology
→ establish content grammar
→ choose valid content evidence carriers
→ measure production/validation burden
→ only then scale breadth
```

## 18. Reopen conditions

Revisit this model if a materially different real development case shows that:

1. a necessary content/progression responsibility cannot be represented by the four-graph alignment plus current carriers;
2. a new carrier changes future play but cannot be reduced to existing Game semantic relations/state/action/evaluation views;
3. production repeatedly needs an executable shared schema rather than an operation-relative view;
4. Agent retrieval/routing is materially harmed by document-only representation.

Until then, do not create a content service, universal level schema, or new Foundation.
