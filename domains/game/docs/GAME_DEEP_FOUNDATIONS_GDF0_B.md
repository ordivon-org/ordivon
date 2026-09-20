---
schema_version: 1
id: game.deep-foundations.gdf0-b
title: Ordivon Game Deep Foundations — GDF0-B Competing Models of Play and Game
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Competing-model tournament for Play and Game. Separates target level from claim type, tests classical philosophical, ethological, developmental, functional and agency models against a shared boundary corpus, attacks GDF0-A C0/C1/C2, and derives stronger Game-specific research coordinates without reopening F1–F9.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf0-a
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF0-B

## 0. Question

GDF0-A found that `play` and `game` discourse mixes several target objects:

```text
PlayBehavior
PlayExperience / PlayMode
PlayFrame
PlayPractice
GameStructure / GameArtifact
Gameplay / GameInstance
GameCategory
```

GDF0-B therefore does not ask which famous theory is "the definition".

It asks:

> Which theories actually compete, which are complementary because they target different levels, what does each predict, and what survives a shared adversarial test set?

R1–R29 / F1–F9 remain frozen unless an R29 FoundationReopenCondition appears.

---

# 1. Model-competition protocol

A theory is represented as:

```text
Theory =
TargetLevel
× ClaimType
× Scope
× CoreClaim
× Mechanism
× PositivePredictions
× ExclusionPredictions
× Falsifiers
```

## 1.1 Target levels

```text
T0 Lexical / cultural category
T1 Observable behavior / episode identification
T2 Participant experience / motivation / valuation
T3 Social frame / practice / recognition
T4 Game/task structure / constitutive constraints
T5 Enactment / agency / interaction dynamics
T6 Function / developmental or evolutionary outcome
T7 Design/value mechanism
```

## 1.2 Claim types

```text
C  constitutive / definition claim
I  identification criterion
M  proximate mechanism
F  function / adaptive outcome
V  value / phenomenology claim
X  taxonomy / continuum
R  rhetoric / meta-theory
```

## 1.3 Real-conflict test

Two theories genuinely compete only when:

```text
Scope overlaps
+ TargetLevel overlaps
+ ClaimType overlaps
+ predictions are incompatible
```

Otherwise apparent disagreement may be level mismatch.

This immediately changes the literature map:

```text
Suits          → mainly T4/T5 + C
Burghardt      → mainly T1 + I
Špinka et al.  → mainly T6 + F, with T1/T5 predictions
Nguyen         → mainly T5/T7 + V/M
Zosh et al.    → mainly T2/T3 + X, pedagogic scope
Sutton-Smith   → T0/T6 + R/meta-theory
```

Thus "Suits vs Burghardt" is mostly not a direct definition fight. They identify different objects.

Novelty status:

```text
C3 ModelConflictProtocol = N1 synthesis candidate
```

---

# 2. Shared adversarial corpus

Every model is pressured against the same boundary set:

```text
B01 animal rough-and-tumble play
B02 animal locomotor/object play
B03 child free pretend play
B04 child guided play
B05 casual chess
B06 professional chess/esport for income/status
B07 coerced classroom game
B08 gambling with material loss
B09 dangerous sport / climbing
B10 open-ended creative sandbox
B11 puzzle solved for leisure
B12 puzzle solved as paid work
B13 scientific exploration
B14 artistic improvisation
B15 religious/civic ritual
B16 training drill / simulator
B17 idle/incremental game
B18 AI policy playing chess
B19 spectator engagement
B20 negotiated folk/playground game
```

The objective is not to force ordinary-language consensus on each label. The objective is to expose what each theory actually predicts.

---

# 3. M1 — Suits: goal + constitutive inefficiency + lusory acceptance

## Target

```text
T4 GameStructure / T5 game-playing
ClaimType: C
```

## Core strength

Suits' account explains a genuinely strange feature of games:

```text
participants accept constraints that rule out more efficient means
because those constraints make the game activity possible.
```

This is much stronger than "games have rules". It identifies **constitutive obstacle creation**.

## Strong predictions

The account predicts high fit where:

```text
- a prelusory/local goal is identifiable;
- permissible means are deliberately restricted;
- the restriction is constitutive of the activity;
- participants treat achievement under those restrictions as the local problem.
```

Strong cases:

```text
chess
football
golf
speedrun categories
climbing problems
many puzzles/challenge games
```

## Pressure / exclusion error

It is not a theory of all PlayBehavior:

```text
animal play
free object play
unstructured pretend
```

need not contain fixed prelusory goals.

Open-ended sandbox and creative play also pressure the requirement that one specific state of affairs be the goal; local/player-authored goals may change during play.

## GDF0-B verdict

```text
RETAIN strongly for constitutive challenge-game structure.
REJECT as universal Play theory.
NARROW universal Game-definition authority.
```

Important retained mechanism:

```text
constitutive constraints can create an activity rather than merely limit one.
```

---

# 4. M2 — Huizinga / Caillois: frame, separation, freedom, uncertainty and special order

## Target

```text
T2 PlayMode
T3 PlayFrame / PlayPractice
partly T4
ClaimType: C/X/V
```

## Core strengths

This family notices that play commonly changes the interpretation of action:

```text
ordinary meanings/rules
→ suspended, transformed or supplemented
→ local play meanings/rules
```

Caillois further distinguishes broad modes around competition, chance, simulation and vertigo and a continuum from improvisatory `paidia` toward rule-disciplined `ludus`.

## What survives strongly

```text
Play often has frame semantics.
Local rules/meanings can differ from ambient ones.
Uncertainty / latitude for participant response often matters.
Improvisation ↔ formalized constraint is a useful dimension.
```

## What fails as universal necessity

Strong versions of:

```text
free
separate
unproductive
outside ordinary life
```

fail or need major qualification under:

```text
professional sport/esport
gambling
streaming/content production
serious games/training
social reputation
physical injury
persistent online economies
```

The better model is not a sealed magic circle but a frame with selective boundary permeability.

## GDF0-B verdict

```text
RETAIN PlayFrame / special-order insight.
REJECT binary separation from ordinary reality.
REJECT unproductivity as universal.
```

A's `ExternalInstrumentality` and `ConsequenceCoupling` are preferable to a play/work or inside/outside binary.

---

# 5. M3 — Wittgensteinian family resemblance

## Target

```text
T0 lexical/category structure
ClaimType: R / anti-essentialist pressure
```

## Core strength

The model warns that the ordinary word `game` may cover overlapping similarities rather than one necessary-and-sufficient essence.

This is strongly compatible with the observed diversity of:

```text
sports
puzzles
chance games
pretend
sandboxes
role-play
idle games
social games
```

## Weakness

Family resemblance supplies little mechanism for why a particular structure is playable, enjoyable, learnable or agency-shaping.

Therefore:

```text
No lexical essence
!=
No causal regularities
```

## Verdict

```text
RETAIN as category-level anti-overfit guard.
REJECT as sufficient mechanistic theory.
```

---

# 6. M4 — Sutton-Smith: rhetoric / ambiguity of Play

## Target

```text
T0/T6 meta-theory
ClaimType: R
```

## Core strength

Sutton-Smith shows that play theories repeatedly foreground different rhetorics and values: progress/development, fate, power, communal identity, imaginary, self and frivolity.

The important GDF0 lesson is epistemic:

```text
A theory can partly reveal the researcher's cultural/value interests
rather than a neutral essence of Play.
```

This explains why "play develops skills", "play expresses freedom", "play is competition", and "play is imagination" can each look obvious from one disciplinary vantage.

## Weakness

Meta-ambiguity alone does not identify episode mechanisms.

## Verdict

```text
RETAIN as theory-bias guard.
Use to prevent one function/value rhetoric from swallowing the domain.
```

---

# 7. M5 — Burghardt: ethological operational criteria

## Target

```text
T1 PlayBehavior identification
ClaimType: I
```

## Core strength

The five-criteria family makes play research possible without human language or formal GameStructure. It emphasizes:

```text
limited immediate function
endogenous/rewarding or spontaneous character
structural/temporal modification relative to serious behavior
repetition without rigid stereotype
relaxed field / reduced acute pressure
```

This strongly falsifies:

```text
Play requires rules/goals/fiction/human symbolism.
```

## Pressure

The criteria are best understood as a conjunctive operational identification strategy, not a complete phenomenology or evolutionary explanation.

Human cases with mixed external incentives and high stakes also pressure simple transplantation of `relaxed field` or endogenous motivation to all gameplay.

## Verdict

```text
RETAIN strongly for PlayBehavior.
Do not promote to GameStructure theory.
Do not infer subjective PlayExperience directly from behavior alone.
```

---

# 8. M6 — Practice / developmental rehearsal

## Target

```text
T6 developmental function
ClaimType: F
```

## Prediction

If Play exists primarily to rehearse useful adult/species-typical competence, play form should systematically anticipate later required motor/social/cognitive abilities and produce transferable gains.

## Strength

Explains many juvenile cases and why play recombines fragments of serious behavior.

## Failure as universal theory

Poor coverage of:

```text
adult symbolic play
chance games
mature repeated games
abstract board games
fictional world building
play whose skills are intentionally arbitrary
```

Even where later skill transfer occurs, that does not identify the current episode as play.

## Verdict

```text
RETAIN as one functional family.
REJECT Function = Definition.
```

---

# 9. M7 — Training for the Unexpected

## Target

```text
T6 adaptive function
with T1/T5 structural predictions
ClaimType: F/M
```

## Distinguishing claim

Play actively creates manageable perturbation and transient loss of control so the organism can learn flexible motor/emotional recovery.

This is stronger than generic practice because it predicts:

```text
self-handicapping
novel/unpredictable perturbation
switching between control and loss-of-control
recovery versatility
```

## Strong domains

```text
rough-and-tumble
locomotor play
some risky physical play
some action/game situations built around recovery
```

## Weak domains

It cannot plausibly explain all:

```text
chess
idle games
creative sandbox
story role-play
pure chance
many puzzle forms
```

## Verdict

```text
RETAIN as high-quality narrow mechanistic/function theory.
REJECT universal Play/Game expansion.
```

Important consequence: self-imposed difficulty is not uniquely human/game-cultural; play-like systems may actively generate perturbations for their own downstream value.

---

# 10. M8 — Exploration / causal learning / counterfactual possibility

## Target

```text
T5 exploration dynamics
T6 learning function
ClaimType: M/F
```

## Strength

Developmental causal-learning work links extended childhood, pretend/counterfactual reasoning and exploration of possible causal structures. This provides a strong account of why low-immediate-utility action can improve later world-model structure.

Predictions include:

```text
novel interventions
information-seeking action
counterfactual variation
hypothesis revision
broader sampling under uncertainty
```

## Failure as universal Play theory

Play and exploration are distinguishable. Repeated mastery play can remain valuable after major novelty/information gain has collapsed.

Examples:

```text
rhythm mastery
familiar sport
speedrunning
social banter
ritualized competitive play
```

## Verdict

```text
RETAIN exploration as one Play mechanism/value mode.
REJECT Play = information gain.
```

A stronger hypothesis is:

```text
Play can make possibility sampling desirable and sustainable,
but sampling is not the only form of play.
```

---

# 11. M9 — Intrinsic / autotelic / process-valued activity

## Target

```text
T2 PlayMode
ClaimType: V/M/I
```

## Strength

Explains a widespread experiential feature:

```text
means/process can be valued independently of external output.
```

It also separates PlayMode from ordinary instrumental optimization.

## Boundary failure

Strict forms fail as a definition of Gameplay because motives can be mixed:

```text
professional play → income/status
esport → competition + identity + pay
gambling → material payoff
training game → learning/assessment
coerced game → obligation
```

A participant can still instantiate the same GameStructure and action dynamics.

## Verdict

```text
RETAIN as PlayMode dimension.
REJECT as universal Game participation condition.
```

This result strongly supports separating:

```text
GameGoal
ParticipationPurpose
PlayerValue
ExternalStake
```

---

# 12. M10 — Nguyen: agency as art / striving play

## Target

```text
T5 enactment/agency
T7 designed value
ClaimType: V/M
```

## Core strengths

Two distinctions are especially strong:

```text
1. Games can specify a form of agency:
   goals + abilities + constraints + practical attention.

2. In striving play:
   local goal != higher-order purpose.
   A player can temporarily care about winning
   for the sake of the valuable struggle.
```

This explains the apparent paradox of games:

```text
constraints narrow raw freedom
while making a specific kind of agency available.
```

It also explains why intentional failure does not substitute for genuine failed striving in some experiences: the local agency must be sincerely enacted enough for the failure to be the relevant kind of failure.

## Boundaries

Nguyen explicitly distinguishes striving play from achievement play; therefore striving is not a universal account of why every person plays.

The model also has weak direct coverage of animal/free object play.

## Verdict

```text
RETAIN strongly as Game-specific agency/value mechanism.
REJECT as universal Play ontology.
```

This is currently the strongest external support for GDF0's `AgencySculpting` direction.

---

# 13. M11 — Play-as-spectrum / guided-play model

## Target

```text
T2/T3 developmental/pedagogical practice
ClaimType: X
```

## Core strength

A free-play ↔ guided-play ↔ games ↔ playful-instruction spectrum avoids a binary in which any adult structure or learning goal instantly destroys play. It explicitly preserves child agency while varying who initiates/directs activity and whether an external learning goal is present.

## Pressure

One continuum is not enough for the full Game domain.

Adult/cross-cultural cases vary independently in:

```text
rule authority
stakes
external instrumentality
fiction
competition
social recognition
constraint mutability
participant control
```

Thus:

```text
Play spectrum is useful locally,
but global Play/Game space is multidimensional.
```

## Verdict

```text
RETAIN spectrum logic.
GENERALIZE from scalar continuum to coordinate space.
```

---

# 14. Tournament matrix

Legend:

```text
++ strong explanatory fit
+  useful partial fit
~  compatible but not explanatory
-  notable failure/out-of-scope
```

| Model | Animal free play | Pretend | Formal game | Pro/high-stakes | Sandbox | Learning function | Game design mechanism |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Suits | - | -/~ | ++ | ++/~ | -/~ | ~ | + |
| Huizinga/Caillois | + | ++ | + | -/~ | + | ~ | + |
| Family resemblance | + | + | + | + | + | - | - |
| Sutton-Smith | + | + | + | + | + | + meta | - |
| Burghardt | ++ | + | -/~ | -/~ | ~ | ~ | - |
| Practice | + | + | ~ | ~ | ~ | ++ | - |
| Unexpected training | ++ | -/~ | -/~ | ~ physical | - | ++ narrow | + narrow |
| Exploration/causal | + | ++ | + epistemic | ~ | + | ++ | + |
| Intrinsic/process | + inferred | ++ | + | -/~ | ++ | + | + value |
| Nguyen agency/striving | - | -/~ | ++ | + | ~ | ~ | ++ |
| Spectrum | + child | ++ | + | - | + child | ++ pedagogic | + pedagogic |

Main result:

```text
No model dominates because most do not target the same explanandum.
```

---

# 15. Strongest cross-model deductions

## 15.1 Definition, identification, mechanism and function must never be collapsed

```text
What episode is play?
!=
Why does play exist?
!=
What does play feel like?
!=
What structure is a game?
!=
Why is that structure valuable?
```

This is the strongest GDF0-B methodological law.

## 15.2 Goal must be split from purpose

The following are independent enough to model separately:

```text
GameGoal
= local target/evaluation criterion inside the activity.

ParticipationPurpose
= why this participant entered/continues the activity.

PlayerValue
= what aspects of the experience are valued.

ExternalStake
= real-world consequences coupled to local outcomes.
```

Examples:

```text
professional chess:
GameGoal = win
ParticipationPurpose = career / competition / identity
PlayerValue = mastery/striving/etc may vary
ExternalStake = rating / money / status

gambling:
GameGoal = local game outcome
ParticipationPurpose = entertainment and/or profit
ExternalStake = money

striving play:
GameGoal = win
ParticipationPurpose = valuable struggle
```

This removes major confusion from intrinsic-vs-extrinsic debates.

Novelty status:

```text
C4 EvaluationLayering = N1 synthesis
```

## 15.3 Frame boundary is permeable, not binary

A play/game frame can locally change rules/meaning while remaining strongly coupled to external reality.

Therefore track:

```text
ConsequenceCoupling =
material
bodily
economic
social
identity/reputation
institutional/legal
knowledge/skill
```

independently.

```text
LocalFrame != ConsequenceIsolation
```

This supports the GDF0-A supplement rather than a sealed `magic circle` ontology.

## 15.4 Game structure is not sufficient for GameCategory

Ritual, exams, markets, scientific contests and training protocols can contain:

```text
goals
constraints
roles
information
success criteria
strategy
```

without ordinary-language categorization as games.

Thus:

```text
NormativeActionProblem
is broader than
GameCategory.
```

GameCategory depends partly on cultural/practice recognition and historical lineage.

---

# 16. Self-attack of C0 — layered target ontology

GDF0-A proposed:

```text
PlayBehavior
PlayMode
PlayFrame
PlayPractice
GameStructure
Gameplay
```

The competing-model tournament mostly supports the separations, but **rejects a simple vertical stack**.

Why?

```text
- social practice can constitute effective rules;
- participant commitments can create goals/constraints;
- frame changes the meaning of the same physical action;
- artifact affordances constrain practice;
- repeated practice can modify the GameStructure;
- experience influences rule negotiation and continuation.
```

Therefore C0 is reconstructed as a coupled factorization:

```text
LudicConfiguration =
Behavior
× ParticipantMode
× Frame
× Practice
× EffectiveRuleTopology
× Artifact/Affordances
× Enactment
× ExternalCoupling
× CulturalCategory
```

No factor is assumed universally necessary at maximum strength.

Evidence status:

```text
C0 survives as N1 synthesis,
but StackForm is REJECTED.
CoupledFactorForm retained.
```

---

# 17. Self-attack of C1 — CounterfactualSlack

C1 proposed that play recruits behavioral/interpretive possibility not completely dictated by immediate external necessity.

## Positive evidence

It fits:

```text
relaxed-field animal play
self-handicapping
pretend reinterpretation
exploration
creative variation
self-imposed challenge
```

## Strong counterexamples / non-specificity

High CounterfactualSlack also appears in:

```text
science
engineering design
artistic creation
strategy work
policy research
```

without necessarily being play.

Meanwhile some gameplay occurs under very strong external obligation/stakes.

Therefore:

```text
CounterfactualSlack is neither sufficient for Play
nor necessary for GameExecution.
```

It may remain an enabling ecological/behavioral condition for some PlayMode/PlayBehavior.

Disposition:

```text
C1 DEMOTED from N1/N2 boundary to N1 analytical lens.
Do not pursue as candidate universal Play foundation unless GDF0-C finds a discriminator.
```

---

# 18. Self-attack of C2 — ConstraintTransformation

C2 proposed that play/game transforms ambient possibility through locally binding constraints.

## What survives

Strongly survives the observation that rules can have both:

```text
restrictive effect
and
constitutive effect.
```

The same physical action can become:

```text
legal move
foul
goal
capture
turn
role action
```

only under local rule/authority semantics.

## What fails

Constraint transformation is not Game-specific:

```text
ritual
law
training drills
scientific protocols
art forms
work procedures
```

also transform possibility through constraints.

Therefore C2 is not a Game definition.

## Reconstruction

The Game-relevant mechanism is narrower:

```text
AgencySculpting =
constraints / goals / abilities / information / feedback
transform a broad ambient action space
into a structured field of differentiable participant policies
whose enactment/learning/evaluation can itself carry value.
```

This is compatible with Suits and strongly aligned with Nguyen, while remaining applicable to games without assuming all play is rule-governed.

Disposition:

```text
C2 as definition → REJECTED.
C5 AgencySculpting mechanism → N1/N2 candidate, UNFROZEN.
```

Falsifier for C5:

> Construct cases classified robustly as games where changing constitutive constraints/goals/information leaves no meaningful difference in participant policy, skill, interpretation or evaluation yet game value remains unchanged for reasons not representable as presentation/fiction/sociality.

---

# 19. New synthesis — Local Evaluation Layering

The tournament reveals a recurring structure deeper than intrinsic/extrinsic motivation:

```text
Enduring / external values
        ↓ participant enters frame/practice
Local evaluation structure
        ↓
local goals / scores / success / failure / roles
        ↓
participant enacts a policy
        ↓
experience and external consequences feed back upward
```

The local evaluation can be:

```text
adopted voluntarily
accepted professionally
imposed pedagogically
socially negotiated
encoded by artifact
```

and its coupling to enduring values can vary.

This explains:

```text
why losing a game can be locally bad but globally enjoyable;
why professional loss can be both local and genuinely costly;
why pretending can temporarily revalue objects/actions;
why a player can pursue winning for the sake of struggle;
why gamification can become dangerous when a simplified local score
is promoted into an externally authoritative value metric.
```

Candidate:

```text
EvaluationLayering =
LocalEvaluationAuthority
+ ParticipationPurpose
+ PlayerValue
+ ExternalStake / ConsequenceCoupling
```

Novelty status:

```text
C4 = N1 synthesis candidate
```

This is not claimed as a universal Play definition.

---

# 20. New synthesis — Game as Agency Scaffold, not unique ontological substance

Cross-model pressure suggests a useful possibility:

```text
GameStructure may be one family of stabilized NormativeActionProblems,
not a metaphysically unique substance.
```

A broad action problem can specify:

```text
roles
state
possible actions
constraints
information
evaluation
resolution
feedback
```

Training drills, rituals, exams and games can share these structural coordinates.

What differentiates `Game` may therefore be distributed across:

```text
structure
+ mode/frame
+ practice/category
+ designed/recognized experiential purpose
```

rather than one hidden Game atom.

A stronger Game-specific design view is:

```text
Game as Agency Scaffold:
a stabilized structure that offers/assigns a local form of agency
through selected capabilities, constraints, information,
goals/evaluations and consequence semantics.
```

Whether that scaffold is *played playfully*, professionally, coercively or instrumentally is a separate participant-level question.

Evidence status:

```text
C6 AgencyScaffold = N1 synthesis candidate
```

Relation:

```text
C6 describes GameStructure function/form.
C5 AgencySculpting describes one mechanism by which scaffold design creates value.
```

---

# 21. Which theories actually conflict?

After target alignment, fewer conflicts remain than expected.

## Real conflict A — strict intrinsic definition vs mixed-motive gameplay

Strict:

```text
Play requires activity for its own sake / no extrinsic purpose.
```

Counterevidence class:

```text
professional play
gambling
serious/training games
mixed motive play
```

Result:

```text
Intrinsic/process value is dimensional, not universal Game criterion.
```

## Real conflict B — sealed/separate/unproductive play vs porous consequence

Strong separation theories conflict with professional/economic/social/physical coupling.

Result:

```text
Frame semantics survive;
sealing does not.
```

## Real conflict C — all-play-as-learning/practice vs stable mature/repetitive play

If information/skill acquisition goes near zero while valued play continues, learning cannot be the universal proximate essence.

Result:

```text
Learning is one outcome/loop, not Play identity.
```

## Real conflict D — fixed-goal universal Game definition vs open-ended/player-authored forms

This remains unresolved rather than decisively rejected because open-ended games may contain continually generated local goals/evaluation structures.

GDF0-C must distinguish:

```text
No fixed global goal
from
No local evaluation/commitment structure at all.
```

---

# 22. Strongest GDF0-B laws

```text
1. Definition != Identification != Mechanism != Function != Value.
2. Target-level mismatch creates false theoretical conflict.
3. Play and Game remain partially orthogonal.
4. PlayMode is participant-relative; GameStructure is not.
5. GameGoal != ParticipationPurpose != PlayerValue != ExternalStake.
6. PlayFrame != ConsequenceIsolation.
7. ExternalInstrumentality does not automatically erase Gameplay or PlayMode.
8. Rules can be constitutive as well as restrictive.
9. ConstraintTransformation is not Game-specific; AgencySculpting is the more useful Game mechanism candidate.
10. CounterfactualSlack is too broad to define Play.
11. Learning/practice/exploration/unexpected-training are functions/mechanisms of important subsets, not universal definitions.
12. A lexical family-resemblance result does not imply absence of mechanistic regularity.
13. GameStructure may be a stabilized AgencyScaffold within a broader NormativeActionProblem family.
14. GameCategory is partly cultural/historical recognition, not reducible to structural similarity.
```

---

# 23. Revised discovery ledger

## N0 — rediscovery / established pressure

```text
- Suitsian constitutive constraints explain many goal/challenge games.
- Ethological play identification does not require formal GameStructure.
- Training-for-unexpected gives discriminating self-handicap/recovery predictions.
- Causal-learning/exploration explains important developmental play functions but not all play.
- Intrinsic/process value is common but mixed motives exist.
- Nguyen's striving play separates local goal from higher-order purpose.
- Play-as-spectrum usefully rejects strict free-play vs instructed-play binaries.
- Play categories/theories are culturally/rhetorically ambiguous.
```

## N1 — Ordivon synthesis candidates

```text
C0 Coupled LudicConfiguration
C3 ModelConflictProtocol
C4 EvaluationLayering
C6 AgencyScaffold
```

## N1/N2 boundary

```text
C5 AgencySculpting
```

It becomes N2 only if GDF0-C derives discriminating predictions beyond the already known general fact that constraints shape action.

## Demoted

```text
C1 CounterfactualSlack
→ useful analytical lens, not universal foundation candidate.
```

## Rejected as definition

```text
C2 ConstraintTransformation
→ absorbed into C5 mechanism and general F4/F9 semantics.
```

## N3

```text
None.
```

---

# 24. GDF0-C exact frontier

Next round:

```text
GDF0-C — Minimal Mechanisms of Play / Game
```

The task is no longer "find another famous definition".

Construct competing minimal generative models able to reproduce different regions of the boundary corpus.

Priority candidates:

```text
P-model: PlayMode / process-valued enactment
F-model: Frame + EvaluationLayering
S-model: AgencyScaffold / EffectiveRuleTopology
E-model: exploration / possibility sampling
R-model: perturbation / self-handicap / recovery
A-model: AgencySculpting under constraints
```

For each ask:

```text
What variables are minimally required?
What transitions distinguish it from Work/Ritual/Training/Art?
What changes when one variable is removed?
Which observations would make the model false?
Can we construct a cheap executable or behavioral falsifier?
```

Special unresolved target:

```text
Does open-ended GameStructure require at least a dynamic/local evaluation structure,
or can genuine Gameplay exist with no goal/evaluation commitment at any scale?
```

---

# 25. FoundationReopenCondition audit

Nothing in GDF0-B forces a new F1–F9 coordinate.

Current synthesis uses:

```text
F2 State
F3 Relation
F4 Transition / Constraint
F5 Time
F6 Authority / Provenance
F7 Observation / Representation
F8 Evaluation / Motivation
F9 Action / Capability / Policy / Control
```

`Frame`, `EvaluationLayering`, `EffectiveRuleTopology`, `AgencyScaffold`, `ExternalStake` and `AgencySculpting` are derived Game-science models.

```text
FoundationReopenCondition = NOT TRIGGERED
```

---

# References / pressure anchors

- Bernard Suits (1967), *What Is a Game?*, Philosophy of Science 34(2), 148–156. DOI 10.1086/288138.
- Roger Caillois (1958/1961), *Man, Play and Games*.
- Johan Huizinga (1938/1950), *Homo Ludens*.
- Ludwig Wittgenstein (1953), *Philosophical Investigations*, §§65–71.
- Brian Sutton-Smith (1997), *The Ambiguity of Play*.
- Gordon M. Burghardt (2005), *The Genesis of Animal Play* and associated five-criteria literature.
- Špinka, Newberry & Bekoff (2001), *Mammalian Play: Training for the Unexpected*, DOI 10.1086/393866.
- Buchsbaum, Bridgers, Weisberg & Gopnik (2012), *The power of possibility: causal learning, counterfactual reasoning, and pretend play*, DOI 10.1098/rstb.2012.0122.
- Zosh et al. (2018), *Accessing the Inaccessible: Redefining Play as a Spectrum*, DOI 10.3389/fpsyg.2018.01124.
- C. Thi Nguyen (2020), *Games: Agency as Art*, Oxford University Press.
- Jesper Juul (2005/2011), *Half-Real*, MIT Press.
- Jaakko Stenros (2012/2014), work separating psychological, social and cultural boundaries of play.
