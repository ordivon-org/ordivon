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
summary: Exact continuity handoff for resuming the Game foundations programme after R1–R21 without depending on the originating conversation context.
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
  - game.foundations-research.map
  - game.core-research.reset
---
# Ordivon Game Foundations Research Continuation Handoff

## Read first

1. [`GAME_FOUNDATIONS_RESEARCH_R21.md`](GAME_FOUNDATIONS_RESEARCH_R21.md) — canonical R21 decomposition of embodiment, control, input, skill, affordance, game feel, presence and shared/delegated control.
2. [`GAME_FOUNDATIONS_RESEARCH_MAP.md`](GAME_FOUNDATIONS_RESEARCH_MAP.md) — compact R1–R21 conceptual map and cross-round abstractions.
3. [`GAME_FOUNDATIONS_RESEARCH_R20.md`](GAME_FOUNDATIONS_RESEARCH_R20.md) — creation/authorship layer that R21 extends through Action Causality.
4. [`GAME_FOUNDATIONS_RESEARCH_R19.md`](GAME_FOUNDATIONS_RESEARCH_R19.md) — strategic-interdependence layer used by command/delegation/shared control.
5. [`GAME_FOUNDATIONS_RESEARCH_R18.md`](GAME_FOUNDATIONS_RESEARCH_R18.md) — motivation/goal/commitment layer used by Intent and delegated goals.
6. [`GAME_FOUNDATIONS_RESEARCH_R1_R17.md`](GAME_FOUNDATIONS_RESEARCH_R1_R17.md) — canonical snapshot of the first seventeen foundation rounds.
7. [`GAME_CORE_RESEARCH_RESET.md`](GAME_CORE_RESEARCH_RESET.md) — protects canonical G0–G8 semantics and prevents premature product selection.
8. [`DEVELOPMENT_MODEL.md`](DEVELOPMENT_MODEL.md) — only authority for G0–G8 product-development meanings.

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
```

Exact next round:

```text
R22 — Uncertainty, Probability, Randomness, Risk, Luck, Variance, Determinism and Fairness
```

## R18–R20 results to preserve

```text
Need != Desire
Desire != Goal
Goal != Intention
Preference != Utility
Scalarize late.
Goal proposal != Goal adoption.
```

```text
StrategicRelevance(j → i)
=
changing i's belief about j's policy
can change i's preferred response
```

```text
Many moving Actors != Strategic interaction.
Statement != Commitment.
Equilibrium != Product Value.
```

```text
Creation != Creativity
Generation != Player Creation
Authorship != Ownership
More options != More expression
```

R20's main authorship test:

```text
AuthorialCausality =
important artifact properties counterfactually depend
on meaningful participant decisions
```

## R21 durable result

R21's minimal control chain is:

```text
Intent
→ Control Expression
→ Input / Command
→ Mapping / Interpretation
→ Candidate Action
→ Capability / Affordance / Legality / World Resolution
→ Executed Action
→ Consequence
→ Feedback / Perception
→ Attribution / Sense of Agency
→ Learning / Updated Intent
↺
```

Core separation:

```text
Intent != Input != Command != Action != Outcome
Control != SenseOfAgency
Avatar != Body
BodyOwnership != Agency
Embodiment != Presence
Affordance != Capability != Legality
Latency != Responsiveness
DirectManipulation != Agency
Automation != AgencyLoss
```

### Action Causality

```text
ActionCausality =
important action/outcome properties counterfactually depend
on participant intent/control.
```

This is the action analogue of R20 Authorial Causality.

### Control Locus

```text
ControlLocus =
the entity/state/surface through which participant control
enters authoritative system change,
without assuming an avatar/body.
```

Possible control loci include:

```text
body
vehicle
cursor
unit/team
camera
organization
text persona
creative tool
world-level policy
```

Use `Embodiment` only when a self-relevant Body participates in self-location, body ownership and/or agency. Do not call every controlled entity a body.

### Body

```text
Body =
a self-relevant action–perception substrate whose state
constrains sensing, capability, vulnerability and reference frame.
```

Bodies therefore alter reachable futures, affordances, risk and information.

### Embodiment profile

```text
EmbodimentProfile = {
  SelfLocation,
  BodyOwnership,
  MotorAgency,
  SensoryContingency,
  Vulnerability / Stakes,
  MorphologicalIdentification
}
```

No one scalar is sufficient.

### Objective Control versus Sense of Agency

```text
ObjectiveControl = actual causal influence
SenseOfAgency   = experienced attribution that “I caused this”
```

They are related but not identical. Body Ownership is another separate dimension.

Agency can live at different layers:

```text
Strategic agency
Tactical agency
Motor agency
Outcome agency
```

Automation may reduce one and preserve another.

### Intent Fidelity

```text
IntentFidelity =
degree to which value-bearing distinctions in participant intent
survive interpretation, planning and execution.
```

Useful components:

```text
Goal fidelity
Constraint fidelity
Style/manner fidelity
Timing fidelity
Target fidelity
Risk-tolerance fidelity
Stop/revoke fidelity
```

For AI/Agent control this is usually more informative than exact low-level command matching.

### Control Contribution Topology

```text
ControlContributionTopology =
who controls which intent/action layer,
variable, time interval or correction path.
```

This replaces crude “percent player control” reasoning.

Example:

```text
Player: goal + target + broad direction
AI: collision avoidance / stabilization
World: physics / opponent resolution
```

### Direct manipulation / command / delegation / automation

Keep separate:

```text
Direct manipulation = participant directly steers visible/local state
Command             = participant specifies semantic action
Delegation          = participant specifies goal/constraints; executor chooses means
Autonomous execution= system chooses more of goal and/or means
Supervision         = system acts; participant monitors/intervenes
Shared control      = multiple controllers influence overlapping trajectory/scope
```

None is a maturity ladder.

### Control granularity and horizon

```text
Fine      → trajectory / exact placement
Medium    → action / target / formation
Coarse    → goal / policy / constraint
```

```text
Immediate → frame/second/move
Tactical  → local sequence
Strategic → longer policy/trajectory
```

Control should be exposed at the layer where player value resides.

### Affordance

```text
Affordance(actor, environment) =
action possibility arising from
actor capability × environment structure/state
```

Preserve:

```text
Capability       = what actor can execute
Affordance       = what actor–environment relation makes possible
PerceivedAffordance = what player/actor believes possible
Legality         = what authoritative rules currently permit
Cue              = information about possibility, not the possibility itself
```

### Responsiveness

```text
Responsiveness =
promptness + predictability + proportionality + feedback coherence
```

not latency alone.

Intentional/legible wind-up, inertia or command delay can support fantasy and skill; hidden/variable unexplained delay usually harms learnability.

### Game Feel

```text
GameFeel =
Control Mapping
+ Dynamics / Resistance
+ Timing / Responsiveness
+ Feedback
+ Sensory Expression
+ Consequence / Stakes
```

Game Feel is causal action–response phenomenology, not merely animation/particles/audio polish.

### Skill

Keep distinct:

```text
Perceptual skill
Predictive/model skill
Decision skill
Motor/execution skill
Coordination skill
Meta-control skill
```

```text
Difficulty != SkillDepth
MotorSkill != AllGameSkill
```

### Friction

Separate:

```text
Material friction
Execution friction
Cognitive friction
Interface friction
Coordination friction
Administrative friction
```

Core rule:

```text
Preserve resistance that carries intended skill/fantasy/question.
Remove resistance that only obstructs access to it.
```

### Automation/shared control

R21 does not assume agency is proportional to raw motor authority.

```text
Low-level correction can reduce exact command matching
while improving higher-level intent success and sometimes agency.
```

But opaque/misaligned/uninterruptible automation can weaken agency.

Therefore:

```text
Automate low-value control work.
Preserve the value-bearing intent distinctions.
```

### Playable Control / Embodiment

```text
PlayableControl =
a control relation whose mappings, constraints,
assistance and consequences can be learned/predicted,
and whose meaningful outcome differences remain sensitive
to participant intent.
```

```text
PlayableEmbodiment =
body/self-location/agency relations that materially alter
perception, capability, risk, identity or action choices
and remain experientially legible.
```

## Research boundary that must survive the context switch

Do **not** assume Game requires action combat, humanoid avatars, VR, direct input or autonomous Agents.

The search space remains broad:

```text
traditional authored games
action / sensorimotor games
strategy / command games
systemic simulations
social worlds
creative sandboxes / UGC tools
procedural games
SillyTavern-like AI roleplay / co-creation
generative narrative / character experiences
persistent Agent worlds
hybrids among the above
```

Preserve:

```text
AI Game != Agent World
Agent != LLM
Generation != gameplay
Freedom != Agency
More buttons != More control
Direct input != More agency
Control != Sense of Agency
Avatar != Body
Embodiment != Presence
Affordance != UI cue
Lower latency != Always better
Automation != Agency loss
TechnicalCreativePower != PlayerCreativeAgency
```

No product winner currently exists. Foundation rounds do not redefine G0–G8.

## How to continue R22

Start from uncertainty as a property of information/outcomes/models, not from “RNG systems” or loot tables.

The core problem is:

> What changes when future states, action consequences or hidden facts cannot be known or controlled exactly, and how do probability, risk, luck and fairness differ?

Distinguish at least:

```text
Uncertainty
Ignorance
Probability
Randomness
Stochasticity
Determinism
Unpredictability
Risk
Ambiguity
Variance
Luck
Chance
Expected Value
Distribution
Fairness
Procedural Fairness
Perceived Fairness
Control
Skill Attribution
```

Questions worth attacking:

1. What distinguishes uncertainty from randomness and from ignorance?
2. How do epistemic uncertainty and aleatory uncertainty differ for play?
3. Can deterministic systems still produce uncertainty through hidden state or computational complexity?
4. What is Risk relative to uncertainty, stakes, probability and controllability?
5. What is Luck as an experienced attribution rather than merely random sampling?
6. How do random input, random transition, random information and random reward differ?
7. How do distribution shape and variance matter beyond expected value?
8. When does randomness create replayability/tension versus destroy skill/agency attribution?
9. How should players learn uncertainty when exact numeric probabilities are hidden?
10. How do fairness, symmetry, procedural fairness and outcome equality differ?
11. When is bad luck acceptable because the process is legible/anticipated?
12. How does uncertainty interact with R21 Action Causality — did I fail, or did chance dominate?
13. How should risk-sensitive Subjects differ from scalar expected-utility maximizers?
14. How should generative systems communicate uncertainty instead of presenting one sample as confident truth?

## Expected R22 output shape

```text
1. separate uncertainty/randomness/risk/luck/fairness terms;
2. derive minimal uncertainty structure;
3. separate epistemic vs aleatory sources;
4. test deterministic hidden-information games and stochastic games;
5. test action/strategy/economy/social/generative forms;
6. analyze skill/chance attribution and fairness;
7. identify distribution/variance effects beyond expected value;
8. identify collapse/failure modes;
9. reconnect tension, belief, utility, strategy and control;
10. end with the next foundational question rather than product selection.
```

## Stable abstractions already available

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
ActionCausality =
important outcome properties counterfactually depend
on participant intent/control
```

```text
IntentFidelity =
value-bearing intent distinctions survive interpretation/planning/execution
```

```text
Playable X =
X that players can observe, model, influence/test,
and use to improve future decisions or expression
```

## High-priority warnings

Do not regress into:

```text
“Random = unpredictable.”
“Uncertain = random.”
“More variance = more tension.”
“Expected value is enough.”
“Fair means equal outcome.”
“Bad luck means bad design.”
“More control means less uncertainty.”
“Exact percentages are required for legibility.”
“Generative output is truth rather than a sample/inference.”
```

## Product-selection stop condition

Do not begin intentional new-product G0 merely because the corpus is large.

Before narrowing, the programme should still:

- finish remaining obvious foundational dimensions;
- synthesize independent vs redundant dimensions;
- identify a smaller set of candidate causal laws;
- compare materially different authored, systemic, social, creative and generative families;
- design high-information falsifiers;
- state what remains unknown.

Only then ask whether evidence is mature enough to select an actual product form.
