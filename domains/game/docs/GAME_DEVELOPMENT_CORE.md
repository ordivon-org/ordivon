---
schema_version: 1
id: game.development-core
title: Ordivon Game — Development Core Responsibility Model
profile: product
lifecycle: active
source_role: canonical-supporting-model
visibility: public
owners:
  - ordivon-game
updated: 2026-08-27
summary: Current responsibility-and-evidence model underneath Ordivon Game's canonical G0-G8 stage projection. It does not create new Game Foundations or product stages; it exposes the concurrent design, player-learning, evidence, content, expression, realization and ecology responsibilities that stage labels alone cannot represent.
evidence_status: derived
readiness: CURRENT
applies_to:
  - ordivon-game
related:
  - game.development-paradigm-research
  - game.development-model
  - game.core-research.reset
---
# Ordivon Game — Development Core Responsibility Model

## 0. Authority boundary

This document does **not** redefine G0–G8.

`DEVELOPMENT_MODEL.md` remains the sole authority for product-stage identities.

This document answers a different question:

> What development responsibilities and evidence states actually have to evolve underneath those stage labels?

It is a practical responsibility projection over existing Game research, not a new Foundation registry and not eight new services.

```text
DevelopmentCore != FoundationOntology
DevelopmentCore != RepositoryArchitecture
DevelopmentCore != StageProjection
```

## 1. The model

Use eight concurrent responsibility views:

```text
D1 Intent / Audience Context
D2 Play Causality
D3 Player Learning / Legibility
D4 Evidence / Prototyping
D5 Content / Progression Architecture
D6 Expression / Feel
D7 Production Realization
D8 Product Ecology / Evolution
```

They are deliberately not numbered as GDFs and do not own semantic truth already frozen elsewhere.

Development is a coupled graph rather than a one-way pipeline:

```text
                 D1 Intent / Audience
                    ↕
D5 Content ↔ D2 Play Causality ↔ D3 Player Learning
     ↕               ↕                 ↕
D6 Expression ↔ D4 Evidence / Prototyping
     ↕               ↕
D7 Production Realization
     ↕
D8 Product Ecology / Evolution
     ↺ evidence may reopen any earlier assumption
```

G0–G8 project this graph into coarse commitment/coordination states.

## 2. D1 — Intent / Audience Context

Question:

> For whom, in what context, and toward what experience/fantasy/value hypothesis are we designing?

Minimum useful view:

```text
PlayerRole / Fantasy
TargetExperience
CentralValueHypothesis
Audience / Context assumptions
Session / device / social constraints
Product constraint / purpose
Explicit non-goals
```

Important law:

```text
MarketSegment != HumanEssence
TargetAudienceAssumption != observed audience truth
```

Audience research may change this view before any mechanic is implemented.

## 3. D2 — Play Causality

Question:

> What player/world interaction is expected to cause the target experience?

Use a bidirectional design bridge:

```text
ExperienceTarget
↔ ExpectedDynamics
↔ Mechanics / Rules / Verbs / State / Information / Evaluation
```

The frozen GDFs remain the semantic source for Action, Control, Challenge, Failure and Determination boundaries.

A development claim should be able to answer:

```text
If mechanism X changes,
which dynamic Y should change,
and why should that alter player-relevant experience Z?
```

Do not promote one “core loop” sentence into a universal causal model. Preserve loop topology when needed:

```text
micro loop
core/repeated loop
session loop
progression/meta loop
persistent/open loop
```

## 4. D3 — Player Learning / Legibility

Question:

> What must a player learn, notice, predict, practice or reinterpret for the game to become playable and deepen over time?

Practical view:

```text
LearningTarget
Prerequisites
Action / decision opportunity
Feedback / evidence
Mental-model expectation
Practice / variation
Challenge progression
Transfer expectation
Observed misunderstanding / skill failure
```

Strong boundary:

```text
DesignedLearnability != ActualHumanLearning
```

Game may own intended cues, practice structure and observed local evidence. Human-specific learning/experience claims require appropriate Human/player evidence.

This responsibility is continuous. It is not only tutorial/onboarding work.

## 5. D4 — Evidence / Prototyping

Question:

> What is the cheapest **valid** evidence carrier for the current decision?

Every material prototype should be representable as:

```text
PrototypeEvidenceContract =
TargetQuestion
+ ClaimToChange
+ EvidenceHorizon
+ Medium
+ RepresentedDimensions
+ OmittedDimensions
+ FalsePositiveRisks
+ FalseNegativeRisks
+ Baseline / Comparison
+ ObservationMethod
+ DecisionRule
+ ReuseIntent
```

`EvidenceHorizon` records how long the relevant consequence takes to become observable:

```text
interaction | encounter | session | run | campaign | cross-session | population/time-window
```

Fast evidence is not automatically more decision-relevant. High-frequency micro-loop evidence can otherwise crowd out slower macro/progression evidence.

Prototype media may include:

```text
paper / tabletop
formal rules / spreadsheet
simulation
interactive mock
mechanic toy
graybox
level blockout
technical spike
experience prototype
production-pipeline trial
representative slice
```

Rules:

```text
CheapestPrototype != CheapestValidPrototype
PrototypePassed != ProductValidated
TechnicalFeasibility != PlayerValue
MachineTrajectory != HumanExperience
```

Ordivon's existing cheap-falsifier and exact-counterfactual machinery is one strong implementation of this responsibility, not its universal form.

## 6. D5 — Content / Progression Architecture

Question:

> How does a finite set of mechanics become sufficient breadth, variety, pacing, challenge and progression without replacing depth with one-off content?

Practical view:

```text
ContentProgressionArchitecture =
ContentGrammar
Mechanic introduction order
Parameter / modifier space
Combination / interaction space
Difficulty / pressure progression
Player-skill progression assumptions
Macro structure
Variety budget
Reuse / transformation rules
Generator / template boundaries
Content validation
```

Distinguish:

```text
MacroArchitecture != MicroContent
ContentGrammar != ContentList
Breadth != Depth
Generation != Authorship
```

A procedural or Agent generator may participate here, but the game still owns constraints, validation, selection and gameplay consequence.

Cross-case pressure now shows this responsibility is richer than a content-class list. Current practical construction is defined in [`GAME_CONTENT_PROGRESSION_ARCHITECTURE.md`](GAME_CONTENT_PROGRESSION_ARCHITECTURE.md), which separates Possibility, Player Capability/Model, Exposure/Content and Production graphs; progression carriers; mechanic-depth construction; macro topology; and content-production economics. It remains a derived development view rather than a new Foundation or runtime schema.

## 7. D6 — Expression / Feel

Question:

> What must be perceived, heard, controlled, timed and emotionally legible for the mechanics to become the intended experience?

Expression is not always late polish.

For some forms:

```text
input latency
camera
animation timing
hit feedback
audio cueing
visual hierarchy
spatial readability
character performance
```

are part of the causal mechanism being tested.

Record:

```text
ExpressionCriticality = low | medium | constitutive
```

When constitutive, pull the required Studio/engine medium into the prototype early enough to avoid false positives from an invalid low-fidelity carrier.

Game still owns gameplay meaning; Studio owns medium-specific editable expression and production.

## 8. D7 — Production Realization

Question:

> Can the intended game be repeatedly created, integrated, tested and changed at the required quality, cost and throughput?

Practical view:

```text
Engine / platform fit
Tool / editor fit
Asset/content pipelines
Build / integration path
Performance budgets
Authoring throughput
Iteration latency
Cross-discipline handoffs
Agent production leverage
Provenance / rights
QA / regression
Cost / schedule uncertainty
```

A production pipeline is a capability, not background plumbing.

Agent-era production primarily changes this responsibility by reducing:

```text
intent → inspect → mutate → test → observe → revise
```

latency and cost.

It does not inherit design or Player Value authority.

## 9. D8 — Product Ecology / Evolution

Question:

> What external environment must the game survive or learn from after it meets real players?

This responsibility is conditional in scope but can constrain early design for multiplayer, UGC, platform-dependent or live products.

Possible concerns:

```text
distribution / discovery
platform constraints
community / social topology
safety / moderation
network population
telemetry
retention / churn
population experiments
economy / monetization when applicable
update / LiveOps cadence
support / incident recovery
modding / UGC ecosystem
```

Strong distinctions:

```text
TelemetryCorrelation != CausalEffect
PopulationExperiment != MachineCounterfactual
Retention != Fun by identity
Monetization != PlayerValue by identity
Popularity != DesignAuthority
```

A finite offline game may keep D8 small. A live social game may need it from preproduction.

## 10. Development standing is a vector

Do not use one stage label as a substitute for current evidence.

A useful bounded standing may project:

```text
ExperienceEvidence
PlayCausalityEvidence
LearningLegibilityEvidence
PrototypeValidity
ContentScalability
ExpressionFidelity
ProductionRepeatability
TechnicalStability
AudienceEvidence
OperationalReadiness
```

Each value must retain source, scope and currentness where material.

Example:

```text
G4
+ strong PipelineProof
+ strong QualityBar
+ weak HumanExperienceEvidence
```

is coherent.

The stage does not magically upgrade the weak dimension.

## 11. Vertical Slice is a compound evidence bundle

Do not treat `Vertical Slice passed` as one indivisible truth.

A representative slice may carry separate claims:

```text
ExperienceRepresentativeness
QualityBar
IntegrationProof
PipelineProof
ThroughputEstimate
PerformanceEnvelope
```

Optional, separately evidenced:

```text
AudienceResonance
Market / distribution assumptions
```

Therefore:

```text
BeautifulSlice != RepeatableProduction
RepeatableProduction != HumanPlayerValue
HumanPlayerValue != MarketDemand
```

G4 remains a stage. Its exit decision consumes this evidence bundle rather than replacing it.

## 12. Player Evidence Programme

Human/player evidence should be operation-relative rather than one generic gate.

```text
PlayerEvidenceRecord =
DecisionToInform
+ ClaimType
+ TargetPopulation / Context
+ Method
+ SampleScope
+ Observations / Measures
+ Bias / Limitation
+ ResultStanding
+ ReopenCondition
```

Different questions justify different methods:

```text
context / motivation       → interviews / contextual research
comprehension / usability  → observed play
experience / resonance     → observed play + careful interview
balance / pacing           → broader quantitative samples
population causal effect   → controlled field experiment
post-launch why            → telemetry + qualitative follow-up
```

No method is universal.

## 13. Product stages as projection

Keep canonical G0–G8 meanings, but interpret them as coarse projections over this Core:

| Stage | Dominant commitment change | Development Core still active |
| --- | --- | --- |
| G0 Define | enough D1/D2 clarity to name the candidate | all may remain uncertain |
| G1 Preproduction | remove highest design/production unknowns | D1–D7 iterate aggressively |
| G2 Kernel/graybox | valid evidence for central play causality | D2–D6 dominate |
| G3 Playable | independent end-to-end play becomes possible | D3/D4/D6/D7 intensify |
| G4 Vertical Slice | representative quality + integration + production evidence | bundle dimensions remain separate |
| G5 Production | scale proven content/realization architecture | D5/D7 dominate; D2 can still reopen under evidence |
| G6 Alpha | whole-game coherence/content validation | broad D3–D7 evidence |
| G7 Beta | release-quality convergence | D6–D8 + stability |
| G8 Release/operate/learn | real ecology becomes available | D8 can reopen any earlier assumption |

This is not waterfall:

```text
stage progress is monotonic only as a coordination commitment
underlying assumptions may be revised or reopened by evidence
```

## 14. Agent use under the Development Core

### Production Agents

Can operate across D1–D8 as researchers, designers, builders, editor operators, synthetic players, QA/falsifiers, analysts, producers, localization/accessibility assistants and operations analysts.

### Runtime Agents

Remain a D2/D7 product realization choice admitted only when a cheaper baseline cannot preserve a player-relevant causal distinction.

### Synthetic players

Are D4 evidence instruments. They can establish mechanics, reachability, strategy, robustness and some behavioral differences, but not Human experience by identity.

### Analytics / experiment Agents

Are D8 operators. They can retrieve and propose analyses/experiments without owning metric interpretation, experiment validity or product authority.

## 15. Current consequences for Ordivon Game

1. Use [`GAME_DEVELOPMENT_CASE_PRESSURE_TESTS.md`](GAME_DEVELOPMENT_CASE_PRESSURE_TESTS.md) as the current real-history falsification set for D1-D8; do not build another treatment merely to fill a GameForm matrix.
2. Existing Station Zero / Casefile / Concept Lab / Pre-G0 implementations remain regression and experiment apparatus.
3. Use external mature games and existing apparatus until a specific unresolved claim requires a new carrier.
4. Replace `prototype count` with `decision-relevant uncertainty removed` as the search-progress measure.
5. Treat Human evidence as a typed programme, not a generic C0 ritual.
6. Treat content/progression architecture as a first-class positive construction capability.
7. Treat G0–G8 as stage projection, never as proof that all evidence dimensions have equal standing.
8. Keep Product/Runtime/Studio/Host/World authority boundaries unchanged.
