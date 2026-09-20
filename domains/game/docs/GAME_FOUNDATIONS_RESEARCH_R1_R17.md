---
schema_version: 1
id: game.foundations-research.r1-r17
title: Ordivon Game Foundations Research — R1–R17
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
summary: Canonical research snapshot of the first seventeen foundation rounds that decompose conventional, systemic, social and generative game forms before any new Ordivon Game product selection.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.core-research.reset
  - game.core-research.direction-space
  - game.development-model
  - game.vision
---
# Ordivon Game Foundations Research — R1–R17

## 0. Status and boundary

This document preserves the foundation research completed across seventeen conceptual rounds so the work does not depend on one long conversation context.

It is a **research record**, not a product specification and not a product-stage promotion.

The canonical G0–G8 meanings remain exclusively those in `docs/DEVELOPMENT_MODEL.md`:

```text
G0 Define
G1 Preproduction / core design
G2 Kernel / graybox prototype
G3 Playable prototype
G4 Vertical Slice
G5 Production / content expansion
G6 Alpha / content-complete validation
G7 Beta / polish / release candidate
G8 Release / operate / learn
```

A research round is a search method. It is not a product phase.

No new Ordivon Game product has been selected by R1–R17. Station Zero, Casefile, Last Light and Echo Hunt remain treatments/reference experiments. The research space intentionally remains open to conventional games, systemic worlds, social simulations, creative sandboxes, and **SillyTavern-like generative interaction / co-creation**.

Two guardrails are especially important:

```text
AI Game != Agent World
LLM output != gameplay by itself
```

A future product may use a strong authoritative simulation, a lightweight narrative/context world, generated characters, generated narrative, authored structure, direct player control, co-authoring, or a hybrid. R1–R17 deliberately avoid selecting among them prematurely.

---

# 1. Research method

The research changed the unit of analysis from historical genres such as `RPG`, `FPS`, `RTS`, and `Simulation` to the lower-dimensional structures that repeatedly reappear across games.

The working method is:

```text
surface genre
→ interaction structure
→ state and rules
→ player/world coupling
→ temporal and information structure
→ player value
```

The main discipline is to separate concepts that are often collapsed into one word:

```text
Genre != Mechanics != Loop
Action != Choice != Agency
World != Map != Lore != Content
NPC != Agent != LLM
Event != Story != Narrative != Meaning
Progression != Persistence != Memory != History != Learning
Group != Organization != Institution
Truth != Observation != Belief != Statement
```

The purpose is not ontological perfection. The purpose is to produce a sufficiently precise model to:

1. compare very different game forms without category confusion;
2. identify which causal structures create actual player value;
3. know what must be simulated and what may remain authored/generated/soft;
4. recognize when added AI/model complexity changes play and when it merely adds prose, latency, or hidden entropy;
5. defer product selection until the search space is understood well enough to make a deliberate choice.

---

# 2. Cross-round working model

A broad current representation of a game form is:

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

Genres are historical stable clusters in this high-dimensional space, not fundamental ontology boundaries.

A more causal representation now emerging from the research is:

```text
WORLD
State / Rules / Time / Subjects / Resources / Topology / Information
            ↓ observable evidence
PLAYER / PARTICIPANT
Perception → Mental Model → Desire → Choice → Action
            ↓
WORLD CONSEQUENCE
            ↓
Feedback → Attribution → Learning → Meaning
            ↺
```

For persistent multi-subject systems the temporal form becomes:

```text
Player_t × Subjects_t × World_t
            ↓ interaction
Player_t+1 × Subjects_t+1 × World_t+1
```

The three sides may all change through time:

```text
Player: learning / skill / preference / identity
Subject: memory / belief / policy / development
World: state / structure / institutions / history
```

No single formula here is promoted as the final Game Core law. They are working compressions that survived multiple rounds and should continue to be attacked.

---

# 3. R1 — Traditional game classification as a multidimensional space

## Problem

Historical labels such as RPG, FPS, RTS, Adventure and Simulation mix several different questions: player verb, camera/control, progression, world representation, content source, social form and value proposition.

## Main result

Classify games across multiple axes rather than forcing them into one genre tree.

Important axes identified:

- **Primary interaction:** action, adventure, roleplay, strategy, tactics, simulation, management, puzzle, sports, racing, survival, stealth, sandbox, creative, social, narrative, card/board, rhythm, idle, party/casual.
- **Player–world relationship:** direct control, party control, command, management, god-game intervention, observation, negotiation, investigation, creation, roleplay, co-creation.
- **What is modeled:** physics, combat, economy, ecology, society, politics, relationships, psychology, knowledge/investigation, creation, history, organization, culture.
- **Time:** real-time, turn-based, real-time-with-pause, tick, phase, asynchronous, idle/persistent.
- **Space:** none, graph/node, grid, continuous 2D, isometric, 3D level, open world, persistent simulated world.
- **Content source:** authored, procedural, randomized, systemic/emergent, UGC, live ops, AI-generated, hybrid.
- **Goal structure:** fixed victory, scenario goals, progression goals, self-directed, expression, social, experience goals, no terminal goal.
- **Value source:** mastery, challenge, discovery, curiosity, power, progression, expression, fantasy, attachment, sociality, competition, cooperation, collection, optimization, emergence, narrative, aesthetics, chaos/humor, creation.

A useful coarse compression is eight superfamilies:

```text
1. Action / Skill
2. Strategy / Decision
3. Simulation / Systems
4. Roleplay / Character
5. Narrative / Discovery
6. Social / Relationship
7. Creative / Sandbox
8. Generative / Open-ended
```

The eighth family is intentionally retained. Generative/open-ended interaction is not treated as an inferior or incomplete Agent World. A SillyTavern-like loop can itself be a valid interactive form:

```text
Player expression
→ AI continuation
→ Player reinterpretation
→ AI continuation
```

The important conclusion is:

```text
AI Game != Agent World
```

AI may generate narrative, character expression, worlds, scenes, quests, art, audio, mechanics, or co-created content without becoming the authority over a simulated world.

---

# 4. R2 — What players actually consume

The eight broad families persist because they repeatedly expose a small number of different player-value structures.

A general loop was identified:

```text
Perception → Decision → Action → Consequence → Evaluation → Next Desire
```

Representative family structures:

### Action / Skill

```text
Skill ≈ Perception × Prediction × MotorExecution
```

The human policy is a large part of progression. Fast, causal, legible feedback is central.

### Strategy / Decision

The player chooses among futures with trade-offs, delayed consequences, and opponent/system uncertainty:

```text
choice → changes future option set
```

Strategy becomes shallow when all values can be simultaneously maximized.

### Simulation / Systems

```text
observe system
→ intervene
→ system evolves
→ unexpected interaction
→ diagnose
→ intervene
```

A useful approximation:

```text
Fun_systemic ≈ Understanding + Intervention + Emergence
```

The system can ask “what happens if?” rather than only “how do I win?”.

### Roleplay / Character

Roleplay can operate across mechanical identity, build/strategic identity and narrative identity. Strong roleplay changes how the player exists in the game, not just numeric stats.

### Narrative / Discovery

Curiosity comes from a structured information gap. Mystery is stronger when players construct hypotheses from evidence rather than passively receive reveals.

### Social / Relationship

Another subject becomes part of the game object. Trust, interpretation, debt, reputation, exclusion and expectation can become state. Interaction among participants can produce complex experience even when mechanics are simple.

### Creative / Sandbox

```text
player defines goal → creates solution
```

The player can generate objectives rather than merely traverse authored goals.

### Generative / Open-ended

Generative systems may support narrative generation, character generation, world generation, mechanical generation or human–AI co-creation. Generation is a content/state production mechanism; it becomes gameplay only when integrated with a meaningful interaction loop.

A useful compression from R2:

```text
Games often primarily consume:
Ability
Decision
World
Meaning
```

These are not mutually exclusive.

---

# 5. R3 — Atomic mechanics

A minimal mechanic was represented as:

```text
Mechanic = Constraint + Player Action + State Change + Feedback
```

or:

```text
State --Action→ State'
```

modulated by information, uncertainty, cost, risk, time, other actors and persistence.

Important mechanic families included:

- information: observe, reveal, search, infer, predict, track, hide, deceive, scout, identify;
- position/movement: change which actions are available;
- execution: intent → execution quality → outcome;
- choice/commitment: a real choice excludes alternatives;
- resources: acquire, store, spend, convert, produce, transfer, trade, invest, protect, steal, destroy, regenerate;
- scarcity: creates trade-offs and planning;
- risk/reward: creates stakes, anticipation, regret and relief;
- conflict: competing agency over incompatible futures;
- cooperation: combined capability through differentiated information/resources/actions;
- uncertainty: randomness, hidden state and another subject's policy are different sources;
- progression/unlock: changes capability or action space;
- exploration: reduces uncertainty and discovers possibilities;
- creation: adds new artifacts or possibilities;
- relationship: history changes later policy;
- loss/permanence: raises choice weight;
- reset/replay: world may reset while human knowledge persists;
- generation: produces content/state but does not by itself constitute a game.

A useful compression was six fundamental operations:

```text
Know
Act
Choose
Acquire / Transform
Relate
Create
```

with four cross-cutting modulators:

```text
Uncertainty
Scarcity
Risk
Time
```

and three temporal structures:

```text
Progression
Persistence
Reset
```

---

# 6. R4 — Game loops

A mechanic is not yet a game. A strong loop is closer to:

```text
Observe
→ Model
→ Choose
→ Act
→ Resolve
→ Feedback
→ Update
→ New Question
```

A loop should repeat with meaningful state change rather than merely repeat an animation or chore.

Working approximation:

```text
LoopQuality ∝ MeaningfulStateChange × Feedback × RenewedUncertainty
```

Nested timescales were separated:

```text
Micro Loop
→ Core Loop
→ Session Loop
→ Meta Loop
→ Persistent / Open Loop
```

A useful minimal Core Loop requires some combination of:

```text
Goal + Constraint + ActionSpace + Consequence
```

Higher loops explain why the player wants to repeat it.

## Loop coupling

Strong games often consist of simple loops whose outputs feed other loops:

```text
combat → loot → build → new strategies → exploration → narrative/resources
```

Open-ended forms can replace a final win condition with **goal generation** and self-propagating loops.

## Loop currency

Different loops transform different “currencies”:

```text
Combat: health / position / advantage
Exploration: unknown → known
Strategy: options / resources / position
Progression: capability
Narrative: questions / information
Relationship: trust / history / interpretation
Social: reputation / information / coordination
Creative: possibilities / artifacts
Generative: context / novelty / meaning
Optimization: efficiency / bottlenecks
Survival: scarcity / safety
```

A loop tends to die when its currency stops changing meaningfully.

## Loop regeneration

Long-term loops can regenerate through:

```text
skill depth
system complexity
new authored content
procedural generation
other players
AI generation
```

AI is only a useful regeneration engine if it produces new meaningful problems/possibilities rather than differently-worded noise.

A compact durable loop form from R4:

```text
Question
→ Choice
→ Consequence
→ Learning
→ Changed State
→ New Question
```

---

# 7. R5 — Motivation, reward, emotion and fantasy

These concepts were separated:

```text
Motivation = why continue
Reward = what signals/creates value
Emotion = what is felt
Fantasy = what identity/situation the player inhabits
```

Major motivation families identified:

```text
Mastery
Challenge / Achievement
Curiosity / Discovery
Power / Growth
Autonomy / Agency
Expression / Creation
Identity / Fantasy
Attachment / Relationship
Social / Status
Meaning / Narrative
```

Important conclusions:

- Mastery requires the player to attribute improved results to learning.
- Curiosity works best with partial understanding: total ignorance becomes confusion; total knowledge becomes boredom.
- Power is deeper when it expands reachable future space rather than only numbers.
- Autonomy requires choices with meaningfully different consequences, not just many buttons.
- Expression depends on ownership and distinctiveness.
- Identity can form a loop: `Choice → Identity → Future Choice`.
- Fantasy must be supported by mechanics; a “genius detective” fantasy is undermined if the actual mechanic is clicking every glowing object.
- Attachment can come from shared history, specificity, dependency and recognition.
- Relationship only becomes structural when past interaction changes later interaction.
- Cooperation is strongest with interdependence, complementary capability, communication and trust.
- Completion can drive behavior even when core play is weak.
- Stewardship adds responsibility/care toward a city, community, pet, ecology, team or other persistent object.
- Surprise is valuable when unexpected **and interpretable**; random weirdness is entropy.
- Regret requires choice, irreversibility and counterfactual imagination.

Five compressed player questions:

```text
Can I?                  → mastery / challenge
What is there?          → curiosity / discovery
What can I become/change? → power / autonomy / creation
Who are we?             → identity / relationship / sociality
What does this mean?    → narrative / history / regret / meaning
```

A design stack emerged:

```text
Desired Experience / Fantasy
→ Motivation
→ Desired Emotion
→ Loop
→ Mechanics
→ Production Form
```

This is deliberately preferable to “we have AI, therefore make an AI game”.

## Generative-system risk discovered in R5

More model capability can make **constraint, continuity, scarcity and commitment** more important, not less:

- infinite answers can collapse curiosity if no answer is real;
- identity drift can collapse attachment;
- AI solving the hard part can collapse achievement;
- unlimited rewrite can collapse meaning;
- incoherent response can collapse fantasy.

---

# 8. R6 — Fun, engagement, satisfaction, compulsion and meaning

The central separation:

```text
PlayerValue != PlayTime
```

Five dimensions were separated:

- **Fun:** the activity itself is immediately valuable.
- **Engagement:** attention continues to be allocated.
- **Satisfaction:** retrospective feeling that the effort/time was worthwhile.
- **Compulsion:** behavior continues because of behavioral pressure even when value may be low.
- **Meaning:** durable personal significance and memory.

A useful diagnostic is to remove extrinsic rewards mentally:

> If XP, loot, streaks and achievements disappear, would the core behavior still be worth doing?

Engagement can be driven by unresolved relevant questions:

```text
Engagement ∝ RelevantUnresolvedQuestions
```

Fun and engagement are separable. Low-fun/high-engagement systems may be driven by FOMO, checklist pressure or compulsion rather than strong play.

Satisfaction often uses local closure:

```text
Tension → Resolution
```

Open-ended worlds can still create satisfaction through many local closures while preserving future possibility.

Compulsion mechanisms such as streaks, FOMO, variable reward, daily resets, sunk cost and social obligation must be evaluated separately from player value.

A useful value vector was:

```text
V = F + E + S + M
```

where F=fun, E=engagement, S=satisfaction, M=meaning, while **C=compulsion remains separate**. Increasing C does not prove V increased.

## Comprehension–Expansion loop

A deeper long-term source of play is compression:

```text
Complexity → MentalModel → Compression
```

Then the game regenerates complexity:

```text
Complexity
→ Understanding
→ New Complexity
```

This is the **Comprehension–Expansion Loop**.

## Breadth vs depth

```text
Breadth = number of distinct situations
Depth = number of meaningful policies within situations
```

AI naturally expands breadth. It does not automatically expand depth.

A strong target is often:

```text
Generative breadth + Systemic depth
```

rather than infinite breadth + shallow interaction.

A provisional healthy-play form was:

```text
MeaningfulTension
→ Agency
→ LegibleConsequence
→ Learning/Feeling
→ ChangedPossibility
```

This is not yet promoted as a final core law.

---

# 9. R7 — Tension, uncertainty, difficulty and pacing

Tension was broadened beyond “stress”. A useful definition is:

```text
Tension = valued unresolved instability
```

or approximately:

```text
DesiredState - PerceivedCurrentState
```

Examples include danger, curiosity, anticipation, social uncertainty and creative incompletion.

## Sources of tension

- uncertainty;
- risk;
- scarcity;
- time pressure;
- commitment;
- conflict;
- information asymmetry;
- expectation/anticipation.

Uncertainty types included:

```text
outcome uncertainty
state uncertainty
rule uncertainty
opponent-policy uncertainty
capability uncertainty
meaning uncertainty
```

Randomness is only one subset of uncertainty.

Strong uncertainty is often **learnable uncertainty**:

```text
Unknown + Evidence + Learnability
```

Risk was represented as:

```text
Risk ≈ ProbabilityOfLoss × SubjectiveValueOfLoss
```

Scarcity creates opportunity cost. Time pressure is a special scarcity. Commitment makes choices heavier by making no-cost reversal harder.

Difficulty is not complexity. A working definition:

```text
Difficulty = RequiredCapability - CurrentCapability
```

with execution, cognitive, strategic, resource and social forms.

Depth is also not difficulty. A hard problem may have only one correct policy; a relatively accessible system may support many good policies.

## Pacing

Pacing is not clock speed. It is the distribution of tension, decision density, novelty, feedback, recovery and closure through time.

A basic rhythm:

```text
Build → Tension → Peak → Release
```

Good pacing depends on contrast. Constant climax produces habituation.

Different pace channels can vary independently:

```text
Action pace
Decision pace
Information pace
Reward pace
Narrative pace
Emotional pace
Progression pace
```

Escalation is stronger when it introduces new problem structure rather than only larger numbers.

## Generative pacing

AI may dynamically adapt pacing, but “player bored → generate crisis” can create soap-opera flatness. Generation requires restraint.

A key principle emerged:

```text
GenerateMore is not the same as ChooseWhatNotToGenerate
```

Silence, normality, waiting, scarcity and repetition can all be design resources.

Generative systems can also destroy anticipation if every desired thing can be instantly requested.

A provisional play model from R7:

```text
Play =
ValuedPossibility
+ Uncertainty
+ Agency
+ Constraint
+ Resolution
```

with resolution opening new possibilities.

---

# 10. R8 — Story, narrative, emergence and simulation

Four concepts were separated:

```text
Event != Story != Narrative != Meaning
```

- **Event:** state change that occurred.
- **Story:** interpretable temporal/causal/subject structure among events.
- **Narrative:** how events are selected, ordered, framed and presented.
- **Meaning:** why those events matter to the player/subject.

Simulation primarily produces events. Many events do not automatically create story.

Story potential increases with causal connection, continuity, subject specificity, stakes and transformation.

A useful distinction:

```text
History = stored/causally retained past
Story = interpretable past
```

Narrative performs compression:

```text
HugeEventSpace → SalientStructure
```

## Story-production modes

The research retained multiple legitimate modes:

```text
Authored Story
Branching Narrative
Environmental Storytelling
Systemic Narrative
Emergent Narrative
Procedural Narrative
Generative Narrative
Player-authored Story
Social Narrative
```

Two independent questions matter:

```text
Who generates events?
Who constructs meaning?
```

## Generative narrative

A major generative limitation is long-range structure:

```text
LocalCoherence >> LongRangeStructure
```

Models can produce interesting next responses without maintaining setup, delayed payoff, transformation and closure.

This led to **Narrative Governance** as a more important problem than raw generation:

```text
When should nothing new be added?
Which setup should now pay off?
Which arc should close?
Which character should leave?
Which mystery should remain unresolved?
```

Three forms of continuity debt were identified:

```text
Setup Debt
Character Debt
World Debt
```

Every generated claim creates future coherence obligations.

A useful Narrative Stack:

```text
World Events
→ Persistent History
→ Causal Structure
→ Salience Selection
→ Narrative Framing
→ Player Interpretation
→ Personal Meaning
```

AI can intervene at several different layers: event proposal, character expression, salience detection, retrospective narration, interpretation and co-authoring. These are not the same architecture.

A useful working statement:

```text
Story = meaningful transformation structured across time
```

and:

```text
Emergence = interacting rules/policies → unplanned but explainable pattern
```

---

# 11. R9 — World, rules, state, dynamics, simulation and emergence

The key separation:

```text
World != Map != Content != Lore != Simulation
```

A minimal working world:

```text
World = StructuredState + RulesOfPossibleChange
```

Chess already qualifies: board, pieces, turn, rules and history form a complete world without an open 3D map.

## State and transition

```text
W_t --Action→ W_t+1
```

State may be spatial, physical, resource, character, social, epistemic, institutional, narrative, creative or temporal.

Rules determine legal possibilities, resolution, costs, time, information exposure and persistence.

Dynamics arise from:

```text
Rules × State × Time
```

Simulation is those dynamics actually unfolded over time.

## Simulation detail is not gameplay depth

A system is worth simulating when it participates in player-relevant causality:

```text
observe → model → decide → consequence
```

A useful relevance approximation:

```text
Relevance(s) ∝ Observability × Actionability × Consequence
```

World depth is not the number of variables. **Systemic leverage** matters: how many meaningful interactions a rule/state participates in.

Good emergence was described as:

```text
Unexpected + CausallyLegible
```

Otherwise high complexity may feel random.

## World as compression

Game worlds are selective models of reality:

```text
Reality → SelectedStateVariables
```

The target is not maximum realism but preservation of the causality needed for the intended experience.

Three useful fidelity distinctions:

```text
Physical fidelity
Causal fidelity
Fantasy fidelity
```

Consistency is more basic than realism because consistency supports prediction, strategy and agency.

## Hard and soft state

Generative systems introduced an important design axis:

```text
Hard State ↔ Soft State
```

Hard state is exact, persistent and authority-bearing. Soft state supports ambiguity, expression and interpretation.

A strong hybrid pattern is:

```text
Hard facts + Soft interpretations
```

A world can be lightweight and narrative/contextual without being invalid. Strong authoritative simulation is only required when the experience requires reliable causal inference across world actions.

---

# 12. R10 — Object, actor, subject, NPC, agent and player

The research separated several concepts that AI-game discourse often merges.

```text
Object = Identity + State
Actor = Object + ActionCapability
Subject = Actor + SituatedPerspective / InternalState
Policy = mechanism selecting action
NPC = a character not directly controlled by the current player
Agent = comparatively autonomous selector among consequential alternatives
Persona = identity/expression surface
Generator = context → content producer
```

The central corrections:

```text
Agent != LLM
NPC != Agent
Intelligence != Agency != Autonomy
```

An LLM call producing text is a generator/function unless it participates in a loop such as:

```text
Observe → Decide → Act → Consequence → Observe
```

## Subjecthood

A subject has a situated perspective. World truth and local observation differ:

```text
Reality != Observation_i
```

Internal beliefs may be false yet consequential. Stealth works precisely because opponents act on beliefs rather than omniscient truth.

Policy may be implemented by:

```text
script
FSM
behavior tree
utility system
GOAP / planner
search
RL policy
LLM
human
hierarchy / hybrid
```

The semantic role and implementation mechanism are separate.

## Cognition complexity

A provisional non-maturity taxonomy was used:

```text
C0 Reactive
C1 Stateful
C2 Goal-directed
C3 Social / epistemic
C4 Reflective / long-horizon
```

Higher is not better. A bullet-hell enemy may be best at C0 because pattern readability is the game.

## Character continuum

```text
Portrait
→ Persona
→ Responsive Character
→ Stateful Character
→ Goal-directed Subject
→ Autonomous Agent
→ Long-horizon Social Agent
```

Added complexity is justified only when it produces added player value.

## Agent Value Test

When replacing a cheap deterministic policy with an expensive model agent, evaluate whether richer cognition produces meaningful changes in:

```text
trajectory
player strategy
relationship
surprise
legibility
fantasy
attachment
```

If not, use the cheaper mechanism.

---

# 13. R11 — Action, choice, agency, freedom, control and consequence

The central correction:

```text
ManyActions != MeaningfulChoice
Freedom != Agency
Control != Agency
Power != Agency
```

Action is simply an available operation. Choice means selecting among alternatives. Decision is the internal selection process. Control measures how directly the player commands state change. Freedom measures size of allowed action space. Agency concerns whether choices can select among **meaningfully distinct future trajectories**.

A useful working definition:

```text
Agency = ability to select among meaningfully distinct future trajectories
```

with value approximately affected by:

```text
AgencyValue ≈
ValuedAlternatives
× Influence
× Consequence
× Legibility
```

and modulated by constraint, commitment and persistence.

## Different agency domains

```text
Instrumental
Causal
Expressive
Interpretive
Authorial
Physical
Spatial
Tactical
Economic
Social
Narrative
Creative
Institutional
Epistemic
```

Therefore “this game has high agency” is incomplete unless scale and domain are specified.

## Generative-language agency

SillyTavern-like systems may have extremely high **expressive freedom** and **authorial potential** without necessarily possessing strong causal world agency.

A useful separation:

```text
Expressive Agency: I can express almost any intent.
Narrative Agency: the story responds to that expression.
World Agency: resulting changes become persistent reality constraining the future.
Meta-Authorial Agency: I directly edit/direct the experience generator.
```

Participant, director and author are different control roles.

Natural language also introduces an authority ambiguity:

```text
“I open the safe”
```

might be interpreted as claim, attempt or desire. Strong language-based game systems may need:

```text
PlayerUtterance
→ Intent
→ AuthorityCheck
→ Resolution
```

A powerful hybrid principle:

```text
OpenIntentSpace + StructuredConsequenceSpace
```

Expression can remain broad while world consequences remain governed by capability, rules, resources, relationships and history.

## Resistance and automation

World resistance can make impact meaningful. An always-agreeing world may increase apparent freedom while reducing tension and significance.

AI automation has a critical boundary:

```text
Automate bad friction,
not the intended decision problem.
```

If AI solves the strategic inference, creative judgment, relationship decision or mastery task that constitutes play, tool capability rises while game value may fall.

---

# 14. R12 — Feedback, legibility, mental models and learning

The causal loop is incomplete until the player can perceive and attribute consequence:

```text
Action
→ WorldChange
→ Perception
→ Attribution
→ MentalModelUpdate
→ BetterPrediction
```

Feedback is broader than effects/juice. Important forms include:

```text
Sensory feedback
State feedback
Causal feedback
Strategic feedback
Social feedback
Narrative feedback
```

## Legibility

Legibility means the player can form a sufficiently useful model from evidence. It does **not** require explicit numeric transparency.

```text
Legibility != RevealAllState
```

Relationship systems, mystery and social play often need behavioral evidence rather than direct meters.

## Learning loop

A general mastery/learning loop:

```text
Observe
→ Hypothesize
→ Predict
→ Act
→ Observe Outcome
→ Attribute
→ Update Model
```

Failure is productive when it yields usable prediction error. Unattributable failure yields frustration.

A strong surprise obeys:

```text
GoodSurprise = PredictionViolation without WorldModelCollapse
```

The player may be wrong, while the world remains coherent.

## Playable Complexity / Intelligence

Two useful concepts were introduced:

```text
PlayableComplexity =
complexity that can be observed, modeled, tested and exploited
```

and:

```text
PlayableIntelligence =
cognition that creates legible, consequential, learnable behavior
```

Internal sophistication invisible to player reasoning may be merely hidden entropy.

## Generative stability

AI character/world novelty should distinguish:

```text
State-conditioned novelty
vs
Sampling novelty
```

Behavior changing because the world/history changed can be learned. Critical policy changing merely because sampling changed can destroy learnability.

A useful hybrid pattern is:

```text
Semantic determinism + Surface variation
```

or more generally:

```text
Stable semantics / grammar + Variable realization
```

This allows generative breadth while preserving player learning.

---

# 15. R13 — Progression, persistence, memory, history and learning

The central separation:

```text
Progression != Persistence != Memory != History != Learning
```

- **Progression:** directional state transformation.
- **Persistence:** which changes survive across time boundaries.
- **Memory:** past information available to future cognition.
- **History:** past events whose causal traces remain in the present.
- **Learning:** experience changes future policy/model.

Progression is not necessarily monotonic power growth. Development may involve specialization, maturity, decline, obligation or identity transformation.

## Progression forms

```text
Numeric growth
Capability growth
Knowledge growth
Relationship development
Identity development
World development
Player skill / mental-model development
```

Capability progression is especially structural when it expands reachable possibility space.

Strong progression can also recontextualize old content:

```text
OldWorld + NewCapability → NewPossibility
OldHistory + NewKnowledge → NewMeaning
```

## Persistence horizon

Persistence can exist at multiple layers:

```text
instant
encounter
mission
run
session
campaign
character lifetime
world lifetime
cross-generation
```

This produced **Layered Persistence** rather than a simple permanent/reset binary.

Roguelikes demonstrate that world state may reset while player knowledge persists.

## Memory pipeline

Infinite context/store-everything is not equivalent to good memory.

A stronger pipeline is:

```text
Experience
→ Salience
→ Memory
→ Interpretation
→ Internalization
→ Policy
```

Old episodes may decay after being compressed into dispositions, relationship state or identity.

```text
StoredPast != FunctionalMemory
```

Memory quality is better approximated as:

```text
RightPast → RightPresentDifference
```

## History and legacy

```text
History != EventLog
```

History becomes valuable when past events remain as present structure: ruins, ownership, institutions, relationships, knowledge, identity, culture or boundaries.

A useful principle:

```text
History becomes structure
```

Legacy describes effects that outlive their source. Death can transform a world through inheritance, organization change, cultural memory and relation networks rather than merely remove an NPC.

Long-lived systems need decay, forgetting and historical compression, not infinite accumulation.

An important long-term value concept is **CoHistory**: the player and world become mutually specific because both have changed through their shared history.

---

# 16. R14 — Resource, scarcity, ownership, production, exchange and economy

A useful resource definition:

```text
Resource = a state/capability whose availability changes reachable valued futures
```

leading to the compression:

```text
Resource ≈ StoredOptionality
```

Not every valuable state should be treated as a currency/resource; doing so can erase relational, narrative or identity structure.

## Scarcity and allocation

```text
DesiredUses(R) > Available(R)
```

creates:

```text
Scarcity → OpportunityCost → Choice
```

Scarcity can arise from quantity, flow, capacity, time, position/access or information.

Stock and flow were separated:

```text
Stock = current quantity
Flow = change per unit time
```

Capital introduces investment:

```text
PresentConsumption ↔ FutureCapability
```

## Ownership

```text
Ownership != Possession != Access != Control
```

Ownership is a structured distribution of future use/transfer/exclusion rights. It redistributes agency over resources.

## Production and economy

```text
Production = Inputs + Capability + Time → Outputs
```

Capabilities such as tools, technology, knowledge, institutions and organization may be more important than raw stock.

Exchange becomes possible when subjects value resources differently. Repeated exchange can create specialization, dependence, trade networks and institutions.

Prices can act as compressed signals of distributed scarcity and preference, but dynamic price is only playable when causal evidence allows the player to understand/influence it.

A useful definition:

```text
PlayableEconomy =
economic dynamics that players can observe, model, influence and exploit
```

## Future claims

Debt, credit, promise and contract extend resource structure through time:

```text
Debt: future resource → present optionality
Contract: structured future obligation
Ownership: persistent claim over future use
```

Natural-language agents become more consequential when statements can establish real promises/commitments rather than only prose.

## Boundary

A universal currency can collapse multiple values into profit optimization. Therefore:

```text
NotEverythingValuableShouldBecomeACurrency
```

Economic utility and player meaning must be allowed to diverge.

---

# 17. R15 — Group, organization, institution, norm, law and collective agency

The research moved from individual subjects to persistent social coordination.

```text
ManySubjects != Organization
Faction != Organization
Organization != Institution
Rule != Law != Norm
CollectiveAgency != LeaderAgency
```

A working organization definition:

```text
Organization =
RepeatedCoordination
+ PersistentRoles
+ SharedResources
```

Roles distribute rights, responsibilities and expected behavior, thereby redistributing individual action spaces.

Organization capability is not the simple sum of member capability. Coordination structure can amplify or destroy collective capability.

Hierarchies and networks are different coordination topologies with different information, authority and failure modes.

## Collective agency

Collective action can arise from:

```text
ManySubjects
+ DecisionProcedure
+ InstitutionalAuthority
→ OneRecognizedAction
```

The resulting policy may differ from any single member's desired policy.

## Institution

A working definition:

```text
Institution =
persistent rules and shared expectations structuring repeated interaction
```

Institutions lower uncertainty and coordination cost by creating stable expectations about ownership, contract, authority, membership and enforcement.

Laws differ from physical rules because violation can be physically possible while triggering institutional consequence.

Norms are softer:

```text
Norm = SharedExpectation + DistributedEnforcement
```

They can arise from repeated behavior and collective response without a central authority.

## Institutions as compressed history

A major temporal insight:

```text
Repeated historical problems
→ coordination responses
→ stable organization/rules
→ institution
```

Thus institutions can be **history compressed into future rules**.

Rules themselves may become game objects:

```text
Rules_t → collective/player action → Rules_t+1
```

This creates meta-agency: acting on other subjects' future action spaces.

## Playable society

```text
PlayableSociety =
social structures whose rules, conflicts, histories and consequences
players can observe, model and influence
```

Five deeply interacting subjects can produce more social gameplay than thousands of autonomous chatters if the latter lack legible organizations, norms, conflicts and history.

---

# 18. R16 — Space, topology, distance, territory and exploration

The key separation:

```text
Space != Map != Geometry
```

A minimal space is:

```text
Locations + Adjacency + Reachability
```

Topology is more fundamental than geometry for many game questions:

```text
Who connects to whom?
What is reachable?
Through which paths?
At what transition cost?
```

## Position and movement

Position matters when it changes available actions, observation, risk or access.

```text
Movement = trading current position for different future possibilities
```

Distance is better represented as transition cost than meters:

```text
Distance ≈ CostOfTransition
```

Fast travel is therefore a topology rewrite, not merely a QoL feature. It can remove travel play if travel friction was part of the intended problem.

## Territory

```text
Territory = Space + PersistentControl/AccessRights
```

Control may be physical, legal, military, economic or cultural and need not collapse into one owner field.

## Flow and logistics

Space becomes systemically rich when people, resources, armies, information, fire, disease, water, electricity or influence flow through constrained networks.

```text
Logistics = ResourceFlow × SpatialTopology
```

Chokepoints, redundancy, capacity and access rules can have high systemic leverage.

## Exploration

A stronger definition than map coverage:

```text
Exploration = growth of a usable world model
```

It can discover places, connections, affordances, resources or underlying rules.

```text
Coverage != Understanding
```

## Topology beyond geography

The same language applies to:

```text
skill trees
narrative branches
social networks
supply chains
communication networks
organizational hierarchy
```

A useful general definition:

```text
Topology = structure of reachability and influence
```

and:

```text
PlayableTopology =
reachability structure players can discover, reason about, exploit and change
```

## Place and generative worlds

```text
Place = Space + Identity/History/Meaning
```

Infinite generated space does not imply infinite exploration value. A major generative risk is **Space Without Place**: many interchangeable locations with little persistent history, network role or future consequence.

Every generated place also creates topological consistency obligations: where it is, what connects to it, who controls it and whether it remains reachable later.

---

# 19. R17 — Information, knowledge, belief, secrets, communication and deception

This round established a dedicated epistemic world layer.

The core chain:

```text
WorldTruth
→ Signal
→ Observation
→ Interpretation
→ Belief
→ Policy
→ Action
```

and the central separation:

```text
Truth != Signal != Observation != Belief != Statement
```

Subjects act on beliefs, not necessarily truth. False beliefs can therefore cause real world consequences.

## Information asymmetry

Different subjects observe different projections:

```text
O_A(W) != O_B(W)
```

This asymmetry directly generates stealth, scouting, bluffing, deduction, negotiation, social inference and many strategy mechanics.

Poker and Chess demonstrate that uncertainty may come from hidden state, hidden intent/policy or unknown future even without randomness.

## Secrets and information value

A strong secret is:

```text
Secret = information whose distribution matters
```

Information can behave like stored optionality, but unlike physical inventory it can often be replicated without being surrendered.

Information value depends on factors such as:

```text
Accuracy × Timeliness × Exclusivity × Actionability
```

Truth alone does not guarantee usefulness.

## Evidence and provenance

Mystery is stronger when it exposes evidence rather than answers:

```text
Evidence acquisition
→ model construction
→ hypothesis testing
```

Information provenance matters: source, timestamp, evidence, confidence and incentives affect whether a claim should update belief.

## Statement and deception

A statement is a communication action, not a direct view into belief.

Intentional divergence between internal belief and external statement can create deception. Bluffing is broader belief manipulation through behavior.

Stealth can therefore be understood as management of opponent epistemic state rather than simply avoiding visibility.

## Communication topology

Communication edges have cost, speed, capacity, privacy, reliability and direction. Physical, social and information topology may differ substantially.

Rumor provides a canonical chain:

```text
Event
→ Observation
→ Belief
→ Statement
→ Other Belief
→ New Statement
```

Information can distort across propagation. This can create politics, reputation, collective memory and culture.

## UI as information policy

Interface determines the player's observation function:

```text
O_player(W)
```

HUDs, maps, markers, diegetic feedback and journals therefore alter gameplay, not merely presentation.

## Generative character stack

A useful separation for generated characters is:

```text
World Truth
Character Belief
Character Communication Intent
Generated Utterance
```

This allows rich language without making every utterance authoritative reality.

A strong hybrid may use AI at expression and interpretation while retaining exact world/epistemic state where the experience requires consistency.

## Playable information

```text
PlayableInformation =
information structure players can acquire, evaluate, infer,
conceal, transmit, distort and act upon
```

This unifies mystery, stealth, social deduction, poker, diplomacy, narrative reveal, strategy and AI relationship play at a deeper level.

---

# 20. Cross-cutting structures discovered across R1–R17

## 20.1 The “Playable X” test

Across many domains, internal sophistication is not enough. A system becomes game-relevant when players can meaningfully interact with it.

The research repeatedly converged on variants of:

```text
Playable X =
X that players can
observe
model
influence / test
and use to change future decisions
```

Examples now include:

```text
Playable Complexity
Playable Intelligence
Playable Economy
Playable Society
Playable Topology
Playable Information
```

This is a strong general diagnostic against technology-first overbuilding.

## 20.2 Possibility space as a common language

Many previously separate concepts can be restated as changes to reachable futures:

```text
Resource      → stores optionality
Power         → expands influence over reachable futures
Agency        → selects among meaningful future trajectories
Progression   → changes future play/possibilities
Movement      → changes spatially reachable possibilities
Creation      → adds new possibilities
Institution   → constrains/enables subjects' future action spaces
Information   → changes which futures can be predicted/selected
History       → past decisions constrain current possibilities
```

This does not prove possibility space is the final ontology, but it is a highly reusable research language.

## 20.3 Stable structure + variable realization

Procedural and generative forms repeatedly suggest a powerful combination:

```text
Stable grammar / semantics / causality
+
Variable content / expression / instances
```

This supports both novelty and learnability.

## 20.4 Hard fact + soft interpretation

A second recurrent hybrid is:

```text
Hard event / state
+
Soft beliefs / narratives / expression
```

Example:

```text
Hard: Alice did not attend the meeting.
Soft: why Alice did not attend; how Bob interprets it; what rumor spreads.
```

This creates generative richness without abandoning world coherence.

## 20.5 Constraint is productive

Across agency, economy, pacing, generation and social systems the research repeatedly found:

```text
Infinite arbitrary possibility
can reduce meaning.
```

Scarcity, commitment, travel cost, limited information, social resistance, institutional constraints and irreversible history can all create decision structure.

This does not mean “more friction is better”. It means meaningful constraints differ from interface friction.

## 20.6 Generation creates debt

Every generated claim may create future obligations:

```text
Narrative claim → setup/payoff debt
Character claim → continuity debt
World claim → causal state debt
Place claim → topological debt
Relationship claim → future behavior debt
```

The future bottleneck of AI games may therefore be less “can we generate content?” and more:

```text
What should exist?
What should persist?
What should be integrated?
What should close?
What should be forgotten?
```

## 20.7 Complexity requires legibility

A recurring failure mode is:

```text
Actual sophistication ↑
Player-understandable causality ↓
```

When the player cannot build a useful mental model, sophisticated systems become perceived randomness.

The valuable target is not maximum complexity but **modelable / playable complexity**.

## 20.8 More AI is not automatically more game

For every model insertion, ask:

```text
Which responsibility is AI performing?
Generator?
Interpreter?
Policy?
Planner?
Narrator?
Expression layer?
World authority?
Salience selector?
Memory compressor?
```

Then ask whether the richer mechanism creates measurable experience value compared with a cheaper control.

---

# 21. Current unified layers

The research now contains several interacting layers rather than one “game engine” concept.

## World layer

```text
State
Rules
Transitions
Time
Dynamics
Space / Topology
Resources / Flows
Information / Observation
History
```

## Subject layer

```text
Identity
Situated observation
Belief / internal state
Need / preference / goal        [not yet fully decomposed]
Policy
Action
Relationship
Memory / learning
```

## Social layer

```text
Relations
Exchange
Groups
Organizations
Roles
Institutions
Norms
Culture
Collective agency
```

## Player layer

```text
Perception
Mental model
Desire / motivation
Choice
Agency
Feedback
Learning
Emotion
Meaning
```

## Narrative layer

```text
Event
History
Causal structure
Salience
Narrative framing
Interpretation
Meaning
```

## Production / content layer

```text
Authored
Procedural
Systemic
UGC
Generated
Hybrid
```

A future product can select a thin subset. No research result says every game should implement every layer.

---

# 22. Explicit non-conclusions

R1–R17 do **not** establish that:

- the first new Ordivon Game should be Station Zero, Casefile, an Agent society, a simulation, or a SillyTavern-like experience;
- authoritative World simulation is mandatory for every AI game;
- language freedom is equivalent to causal agency;
- LLM cognition is required for believable characters;
- more NPCs/Agents create a better society;
- more memory creates a better relationship;
- more simulation variables create deeper play;
- more content or generation creates more gameplay depth;
- every meaningful state should be turned into a resource/currency;
- all history should persist permanently;
- all uncertainty should be eliminated through UI;
- every world should have complex economy, institutions, topology or culture;
- the provisional formulas in these notes are final Game Core laws.

The research currently supports **conditional causal claims**, not a universal product architecture.

---

# 23. Research invariants to preserve in later rounds

When continuing the programme:

1. Start from the concept under investigation, not the current codebase.
2. Keep conventional, systemic, social, creative and generative forms in the search space.
3. Do not promote a research round to G0–G8.
4. Do not let installed tools/model capabilities vote on product direction.
5. Separate semantic game responsibilities from implementation technologies.
6. Distinguish actual causality from player-perceived causality.
7. Prefer the cheapest mechanism that preserves player value.
8. Treat negative experiment results as local to the tested treatment.
9. Distinguish breadth, depth, complexity, difficulty and content quantity.
10. Preserve the possibility that a lightweight narrative/generative interaction is the correct form for some future product.
11. Treat player value, not technical sophistication or raw duration, as the eventual product criterion.
12. Keep asking what changes future possibilities and why the player should care.

---

# 24. Exact continuation point

The next planned foundation round is:

```text
R18 — Goals, Utility, Needs, Values and Desire
```

The unresolved distinctions are:

```text
Need != Want != Desire != Goal != Preference != Utility != Value
```

Questions to attack next:

- Why does a Subject choose one future over another?
- What is the smallest motivational structure needed for a convincing game Subject?
- When is a simple utility function enough?
- When do multiple competing needs create interesting behavior?
- How are short-term goals generated from longer-term preferences?
- How can identity, norms, relationships and institutions alter preference/goal formation?
- How do conflict and cooperation emerge from incompatible/compatible value structures?
- How should player desire be modeled differently from NPC/Agent desire?
- What does a generative Persona need if its purpose is roleplay rather than autonomous world agency?
- Which motivational state should be hard/structured and which may remain soft/generative?

After R18, likely neighboring foundational areas include cooperation/conflict/game theory, creativity/expression, embodiment/control/game feel, social identity/status, and eventually a full synthesis before any product narrowing.

---

# 25. One-page compression

If only the minimal state of the research can be carried forward, preserve this:

```text
1. Games are a high-dimensional space, not a genre tree.
2. AI Game is not synonymous with Agent World.
3. Generation is a mechanism; it becomes play only through meaningful interaction structure.
4. World = structured state + possible transitions; simulate only causality needed by experience.
5. Subject = situated perspective + internal state + policy + consequential action; Agent != LLM.
6. Agency is about meaningful future divergence, not button count or free text.
7. Feedback/legibility turn real causality into learnable player causality.
8. History matters when past becomes present/future structure; memory is not store-everything.
9. Resources create optionality; scarcity creates trade-offs; not every value should become currency.
10. Organizations/institutions coordinate subjects and can be history compressed into future rules.
11. Topology is structure of reachability/influence; space is only one instance.
12. Information is a World layer: Truth != Observation != Belief != Statement.
13. Strong systems expose Playable Complexity, Playable Intelligence, Playable Economy, Playable Society, Playable Topology and Playable Information rather than hidden sophistication.
14. Stable semantics + variable realization and hard facts + soft interpretation are promising hybrid patterns.
15. Infinite generation creates continuity/governance debt; selection, commitment, integration, closure and forgetting may become scarcer than content.
16. Player value != playtime, technical sophistication, content quantity or Agent count.
17. No product has been selected. Continue foundation research at R18 before narrowing.
```
