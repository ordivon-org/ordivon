---
schema_version: 1
id: game.deep-foundations.gdf2-a
title: Ordivon Game Deep Foundations — GDF2-A Challenge / Difficulty / Failure / Mastery Term & Target Separation
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Opens GDF2 from frozen Action/Control/Skill Foundations v1. Rejects Difficulty as one scalar by separating nominal setting, structural demand, participant-relative functional difficulty and Human experienced difficulty; separates skill challenge from outcome risk and infeasibility; decomposes failure/error/punishment/loss/setback/recovery/retry; separates capability mastery, demonstrated mastery, subjective competence and social mastery; and establishes cross-GameForm boundary cases plus executable falsifiers. No frozen foundation reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.action-control-skill-foundations.v1
  - game.play-game-deep-foundations.v1
---
# Ordivon Game Deep Foundations — GDF2-A

## 0. Why GDF2 begins with deletion, not a difficulty formula

GDF1 froze a non-scalar `SkillProfile` and explicitly refused to freeze `difficulty`, `skill floor`, or `skill ceiling` as intrinsic Game properties.

GDF2 now asks:

> Given an attribution target with a SkillProfile, what does it mean for a situation to challenge it, to be difficult for it, to produce failure, and eventually to support a defensible mastery claim?

The common vocabulary is immediately dangerous:

```text
Hard level
high challenge
high fail rate
punishing
frustrating
mastery game
flow state
```

These can refer to different targets.

A's first law is therefore:

```text
DifficultyWord != OneExplanandum.
```

Canonical evidence/probes:

```text
evidence/gdf2-a/term-target-matrix.json
evidence/gdf2-a/challenge-falsifiers.json
scripts/gdf2-a/challenge-falsifiers.mjs
scripts/gdf2-a/audit-gdf2-a.mjs
```

---

# 1. Four different things are routinely called `difficulty`

## 1.1 NominalDifficultySetting

Examples:

```text
Easy / Normal / Hard
Enemy Level 50
speed multiplier 1.4×
ranked category
NG+7
```

This is a declared configuration/label.

It can be useful, but:

```text
NominalDifficultySetting != actual functional difficulty.
```

Two participants can play the same `Hard` setting and face radically different capability relations.

---

## 1.2 StructuralDemandProfile

This is Game/Practice-side structure before a participant-specific difficulty claim.

Candidate dimensions may include:

```text
constraints / legal action structure
information limits
required timing / precision
opposition/adversary configuration
resource scarcity
stochasticity
current evaluation threshold
consequence and recovery topology
```

A does **not** freeze this vector yet.

The important separation is:

```text
StructuralDemandProfile != SkillProfile.
```

---

## 1.3 FunctionalDifficultyRelation

This is participant/controller-relative.

Research sketch:

```text
FunctionalDifficulty
=
relation(
  StructuralDemandProfile,
  attribution-target SkillProfile,
  ControlMapping / ControlLocus / access,
  observation/information,
  current evaluation commitment,
  opponent/other-agent distribution,
  stochasticity,
  history,
  horizon/recovery topology
)
```

It is generally **not one number**.

The same chess puzzle, rhythm chart, boss or traversal route can be easy for one profile and hard for another.

The same participant can also face a changed functional difficulty after remapping/accessibility assistance without the underlying content changing.

---

## 1.4 ExperiencedDifficulty

This is Human-side judged/felt difficulty.

It may depend on:

```text
perception
confidence/self-efficacy
fatigue
frustration
attention
prior expectation
meaning/stakes
```

among many Human variables.

Therefore:

```text
ExperiencedDifficulty != FunctionalDifficulty by identity.
```

Game can provide structural conditions and collect reports, but Human owns the subjective mechanism.

---

# 2. First strong GDF2-A law

```text
NominalDifficultySetting
!= StructuralDemandProfile
!= FunctionalDifficultyRelation
!= ExperiencedDifficulty
```

This already eliminates a large class of weak game-design statements such as:

```text
"Hard mode increased difficulty by 20%."
```

unless the speaker says which target changed and how it was measured.

---

# 3. Low success probability is not automatically Skill Challenge

A's strongest executable falsifier is deliberately simple.

Consider a lottery-like action:

```text
P(success) = 0.10
```

and player skill has no influence on it.

The outcome is difficult to obtain and the adverse-outcome risk is high.

But increasing the player's SkillProfile does nothing.

Therefore:

```text
LowSuccessProbability != SkillChallenge.
```

This means Game needs at least to distinguish:

# **OutcomeRisk**

from

# **SkillChallengeRelation**.

---

# 4. An impossible task is not `maximum skill challenge`

Now take:

```text
P(success) = 0
```

because the necessary action/path does not exist.

If changing participant capability still leaves success at zero, the structure is **infeasible** under the declared horizon/action space.

It is not informative to call it infinitely skill-challenging.

Therefore:

```text
Infeasibility != MaximumSkillChallenge.
```

This distinction will later matter for:

```text
unwinnable encounters
hard locks
missing information
impossible timing windows
content gates
soft locks
forced narrative loss
```

because an impossible situation has different Player/learning consequences from a difficult-but-controllable one.

---

# 5. Candidate: SkillChallengeRelation

A introduces one deliberately narrow candidate:

> The part of a functional challenge for which evaluation-relevant outcome distinctions are sensitive to changes in the attribution target's SkillProfile/policy over the current SRVS, under a declared ProbeTransformation.

It is **not** proposed as the final definition of all challenge.

The executable probe uses local outcome sensitivity only as a falsifier:

```text
lottery
→ low success, zero local skill sensitivity

impossible
→ zero success, zero local skill sensitivity

matched capability frontier
→ moderate success, high local skill sensitivity
```

Thus:

```text
FailRate ranking != SkillChallenge ranking.
```

A retains `SkillChallengeRelation` as a candidate for B, not a frozen foundation.

---

# 6. Challenge also is not Effort, Uncertainty or Risk

All can contribute to a challenging situation.

None is identity.

## High effort, low challenge

Grinding a completely mastered action for 30 minutes may be effortful/fatiguing but minimally skill-discriminative.

## High uncertainty, low skill challenge

A random roulette outcome can be maximally uncertain while unaffected by player capability.

## High risk, low skill challenge

A one-button random death event may carry severe consequences without testing participant capability.

## High skill challenge, low consequence

A rhythm practice sandbox with instant retry and no score persistence can strongly differentiate timing capability while carrying little external consequence.

Therefore:

```text
Challenge != Effort
Challenge != Uncertainty
Challenge != OutcomeRisk
Challenge != ConsequenceSeverity
```

---

# 7. Challenge Point theory is useful because it is relational

Guadagnoli & Lee's Challenge Point Framework explicitly models motor-learning conditions through interaction between performer skill and task difficulty, and proposes that different practice conditions can be optimal for different skill levels.

GDF2 consumes this as **N0 external pressure** for relational difficulty.

It does **not** universalize the motor-learning framework into:

```text
GameDifficulty = ChallengePoint
```

because Game also includes:

```text
strategy
puzzle/search
social opposition
self-authored goals
stochastic risk
narrative/forced loss
creative practice
```

outside that framework's primary scope.

---

# 8. Failure itself is also overloaded

The common chain:

```text
error -> punishment -> loss -> death -> failure -> retry
```

is not a semantic identity chain.

A separates at least:

```text
ErrorEvent
PunishmentConsequence
Loss
Setback
FailureEvent
RecoveryTopology
Retry
```

---

# 9. FailureEvent is evaluation-relative

Candidate definition:

> An episode/state/history evaluation in which a current commitment or Game-local criterion is not satisfied within a declared scope/horizon.

This means one history can be:

```text
success under one commitment
failure under another
```

Example: speedrun.

```text
finish the game
→ SUCCESS

finish under 40:00
→ FAILURE
```

Same run.

Therefore:

```text
Failure requires EvaluationScope.
```

This directly consumes GDF0's:

```text
GameGoal != ParticipationPurpose != PlayerValue
```

and GDF1's current/provenance-bound evaluative relevance.

---

# 10. Error != Failure

An ErrorEvent is a local deviation from a target/prediction/SRVS relation.

Examples:

```text
one mistimed note in a song that is still cleared
one bad chess move in a won game
automatic correction catches steering error
intentional speedrun damage boost sacrifices health
```

So:

```text
ErrorEvent != FailureEvent.
```

Some errors are corrected.
Some are tolerated.
Some are intentionally induced to optimize another evaluation target.

---

# 11. Punishment != Failure

A punishment is an authoritative adverse consequence contingent on an event/action/state.

Examples:

```text
take damage
lose currency
stun
lose combo
respawn delay
```

A participant can be punished repeatedly and still satisfy the relevant commitment.

Therefore:

```text
PunishmentConsequence != FailureEvent.
```

And because negative Player affect is Human-owned:

```text
PunishmentConsequence != Frustration.
```

---

# 12. Loss != Failure

Loss can be strategically valuable.

```text
sacrifice a chess piece
spend health for speed
trade territory for tempo
consume a rare item to win
```

Thus:

```text
Loss != Failure.
```

A loss is an evaluatively negative local resource/status/option change only relative to the selected coordinate; whole-policy evaluation can still be positive.

---

# 13. Setback != Terminal Failure

A setback worsens current progress/cost/optionality while leaving continuation possible.

This distinction matters because player response depends strongly on recovery structure.

Frommel, Klarkowski & Mandryk's game-failure study also pressures the distinction between temporary struggle/failure and more enduring/perpetual failure, and emphasizes goal relativity.

GDF2 does not adopt their terminology as universal ontology, but the empirical result supports the need for scope and recoverability.

---

# 14. Death != Failure

A roguelike is a decisive boundary case.

A character/run death may be:

```text
run-level failure
+
meta-progression gain
+
knowledge acquisition
+
expected practice episode
```

at the same time.

Therefore:

```text
Death != Failure by identity.
```

Likewise:

```text
GameOver != universal ParticipationFailure
```

because evaluation layer and horizon matter.

---

# 15. RecoveryTopology != Retry

`Retry` is one concrete reattempt transition.

`RecoveryTopology` is broader:

```text
continue from current damaged state
checkpoint reload
full run reset
revival by teammate
resource recovery loop
branch to alternative goal
meta-progression then new run
```

with costs potentially in:

```text
time
resources
information
social opportunity
attention
identity/reputation
history/progress
```

Therefore:

```text
RetryCost != FailureSeverity by identity
```

and a future round must model recovery profile rather than only `lives` or `checkpoint distance`.

---

# 16. Failure != Learning Opportunity

This is another major GDF2 guard.

A failed attempt may provide:

```text
clear diagnostic feedback
controllable correction
cheap retry
useful variation
```

or it may provide:

```text
opaque outcome
random death
no actionable signal
excessive reset cost
impossible condition
```

So:

```text
FailureEvent != LearningOpportunity.
```

and:

```text
MoreFailure != MoreLearning.
```

---

# 17. Desirable difficulties make this separation unavoidable

Learning research on desirable difficulties shows an important reversal:

```text
better immediate practice performance
```

can coexist with:

```text
worse later retention/transfer
```

while some harder/interleaved/spaced practice conditions can impair immediate performance but improve later learning.

This is not a license to maximize errors.

The literature explicitly warns that many difficulties are undesirable and that even useful difficulty can fail when the learner lacks the knowledge/cues to respond successfully.

Therefore:

```text
ImmediatePerformanceDifficulty != LearningValue.
```

and GDF2 must eventually model a learning-opportunity region rather than assuming a monotonic harder-is-better law.

---

# 18. Deliberate practice is not the definition of play or challenge

Ericsson, Krampe & Tesch-Römer's deliberate-practice framework emphasizes effortful activities designed to improve performance over long periods under motivational/external constraints.

Useful pressure:

```text
Mastery acquisition may require conditions that are effortful and improvement-directed.
```

But GDF2 rejects:

```text
Challenge = deliberate practice
Play = deliberate practice
Mastery = accumulated effort
```

because deliberate practice is one learning/practice organization, not the ontology of Game challenge.

---

# 19. Mastery needs at least four targets

The word `mastery` is as overloaded as `difficulty`.

A separates:

## CapabilityMasteryClaim

A robust/high-capability claim over a declared relevant challenge/probe region.

This is SkillProfile-side evidence.

## DemonstratedMastery

One or more observed performances consistent with mastery under declared conditions.

```text
DemonstratedMastery != CapabilityMasteryClaim
```

because one performance does not establish robustness/transfer/history.

## SubjectiveCompetence

Human perceived effectiveness/competence.

Ryan, Rigby & Przybylski's studies show perceived in-game competence/autonomy are associated with enjoyment/preferences and related outcomes.

This makes competence important—but also makes owner separation essential:

```text
SubjectiveCompetence != SkillProfile.
```

## SocialMastery

Community/institution-recognized rank/status/credential/role.

It depends on social authority/category practices and may not perfectly track latent capability.

---

# 20. Success != Mastery

A novice can succeed once.
An expert can fail once.
A random process can produce success without capability.
A perfectly mastered trivial task may no longer express mastery differences.

Therefore:

```text
Success != Mastery
Completion != Mastery
HighScore != Mastery
ZeroError != Mastery
```

A's provisional capability-mastering direction is closer to:

> robust control/capability over a declared challenge/probe region,

but B must attack what `robust`, `region`, and `high` mean before anything freezes.

---

# 21. Flow is a Human state, not a difficulty equation

Flow research is directly relevant but easy to misuse.

Experience-sampling work supports relationships between perceived challenge/skill and subjective experience, but effects vary by context.

A later meta-analysis found challenge-skill balance to be a moderate antecedent of flow, with moderators and other important antecedents such as clear goals/control.

Therefore GDF2 adopts:

```text
ChallengeSkillCompatibility
may influence
FlowExperience
```

but rejects:

```text
FlowExperience = ChallengeSkillBalance
GameDifficulty = FlowDistance
BalancedChallenge = PlayerValue
```

by identity.

Flow is Human-owned subjective evidence.

---

# 22. Dynamic difficulty adjustment is a particularly useful falsifier

DDA systems are often described as:

```text
measure skill
match challenge
produce better experience
```

But empirical work is more differentiated.

Ang & Mitchell found different DDA methods produced different experience profiles, including tradeoffs in sense of control.

A 221-participant controlled experiment reported improved performance under performance-based DDA without significant differences in enjoyment or flow.

Therefore:

```text
DifficultyAdjustment != OneTreatment
```

and:

```text
BetterPerformance != BetterExperience
```

again.

GDF2 must name which demand relation, participant capability relation, and outcome target changed.

---

# 23. Accessibility is not `making the game easy` by identity

GDF1 already established that remapping/access can change functional action reach without changing GameAction semantics.

GDF2 now inherits:

```text
same content
+ improved access
→ changed FunctionalDifficultyRelation
```

for a particular participant.

This does not prove:

```text
less PlayerValue
less mastery
less legitimate challenge
```

because those are separate evaluation/social/Human claims.

It may simply remove an unintended access bottleneck and expose the intended SRVS/challenge dimensions more clearly.

---

# 24. Competitive challenge is relational to other agents

PvP makes task-attached difficulty particularly untenable.

Same map, rules and mechanics:

```text
opponent novice
vs
opponent world champion
```

produce different functional difficulty for the same participant.

So adversary/team distribution belongs in the functional relation.

Synthetic controllers make the same point from another direction:

```text
same structural demand
human novice -> hard
human expert -> moderate
superhuman policy -> trivial
```

No content scalar captures all three.

---

# 25. Open sandbox proves Challenge does not require designer terminal failure

A player can adopt:

```text
build without iron
recreate a cathedral
survive with one heart
make a redstone computer
```

without the base Game having a fixed terminal global goal.

The evaluation commitment changes the relevant demand relation.

Therefore:

```text
NoDesignerGlobalGoal != NoChallenge.
```

This consumes GDF0/GDF1 rather than reopening them.

---

# 26. Initial GDF2 relational sketch

A's current research graph is:

```text
Game / Practice / Community / Participant
          │
          ▼
Current Evaluation Commitment
          │
          ▼
StructuralDemandProfile
          │
          ├──────── Opponent / stochastic / history context
          │
          ▼
SkillProfile + Control/Observation Configuration
          │
          ▼
FunctionalDifficultyRelation
          │
          ├─ SkillChallenge component
          ├─ OutcomeRisk / stochastic component
          ├─ Feasibility / reachability
          └─ consequence + recovery topology
          │
          ▼
Performance / Error / Failure / Success Evidence
          │
          ├─ Human experience: difficulty, competence, frustration, flow
          └─ Learning opportunity (not learning itself)
          │
          ▼
History / possible SkillProfile change
```

This graph is **not frozen**.

B must try to break it.

---

# 27. Initial anti-collapse laws

```text
NominalDifficultySetting != StructuralDemandProfile != FunctionalDifficultyRelation != ExperiencedDifficulty

LowSuccessProbability != SkillChallenge
Infeasibility != MaximumSkillChallenge
Stochasticity != SkillChallenge
Challenge != Effort != Uncertainty != OutcomeRisk

Failure != Error != Punishment != Loss != Setback != Death != Reset
Failure != LearningOpportunity
MoreFailure != MoreLearning

ImmediatePerformanceDifficulty != LongTermLearningValue

Success != Mastery
Completion != Mastery
HighScore != Mastery
CapabilityMastery != SubjectiveCompetence != SocialMastery

FlowExperience != ChallengeSkillBalance
DifficultyAdjustment != PlayerValueOptimization

SameStructuralDemand != SameFunctionalDifficultyAcrossSkillProfiles
SameSkillProfile != SameFunctionalDifficultyAcrossControlAccessConfigurations
```

---

# 28. Competing-model map for GDF2-B

A does not put all external theories into one fake tournament.

They target different explananda.

## M1 — Flow / challenge-skill compatibility

Primary target:

```text
Human subjective experience / involvement
```

not formal Game difficulty identity.

## M2 — Challenge Point Framework

Primary target:

```text
motor-learning functional difficulty × learner skill × information
```

not universal PlayerValue.

## M3 — Deliberate Practice

Primary target:

```text
expertise acquisition / improvement-oriented practice
```

not play essence.

## M4 — Desirable Difficulties

Primary target:

```text
practice-condition effects on retention/transfer vs immediate performance
```

not `harder is always better`.

## M5 — Self-Determination / competence

Primary target:

```text
Human need satisfaction / motivation / enjoyment
```

not measured capability identity.

## M6 — Game-failure / struggle accounts

Primary target:

```text
player interpretation and experience of success/failure relative to goals
```

not all structural failure mechanics.

## M7 — Dynamic Difficulty Adjustment

Primary target:

```text
adaptive intervention on game-demand / player-performance relations
```

with experience effects requiring separate measurement.

## M8 — GDF2 relational/probabilistic decomposition

Primary target:

```text
Game-owned structural demand, participant-relative functional difficulty,
skill sensitivity, risk, infeasibility, failure/recovery topology and mastery evidence contracts.
```

This is currently N1 synthesis territory and must be adversarially attacked in B.

---

# 29. Novelty ledger after A

## N0 — established external pressure

```text
task difficulty interacts with performer skill in motor learning;
challenge-skill compatibility relates to flow but is not the only determinant;
deliberate practice is effortful/improvement-directed;
some desirable difficulties reverse immediate-performance vs retention rankings;
perceived competence predicts important game-experience outcomes;
game failure is goal-relative and temporary/perpetual distinctions matter;
DDA effects differ by method and outcome measure.
```

## N1 — Ordivon reconstruction candidates

```text
A1 Four-way Difficulty Target Split
A2 SkillChallenge / OutcomeRisk / Infeasibility separation
A3 FailureEvaluationScope
A4 RecoveryTopology vs Retry
A5 Failure / LearningOpportunity separation
A6 Multi-target Mastery split
A7 FunctionalDifficultyRelation as non-scalar participant/control/history relation
```

## N2

```text
NONE.
```

## N3

```text
NONE.
```

---

# 30. Foundation reopen audit

GDF2-A adds no primitive.

All new terms are downstream configurations/relations/evidence projections over:

```text
State / Relation / Transition / Constraint
Time / History
Authority / Provenance
Observation
Evaluation
Action / Capability / Policy / Control
```

and frozen GDF1 SkillProfile/SRVS/ProbeTransformation.

No cross-GameForm case currently contradicts GDF1.

Therefore:

```text
ACS reopen = NOT TRIGGERED
GDF0 reopen = NOT TRIGGERED
R29 reopen = NOT TRIGGERED
```

---

# 31. Exact GDF2-B frontier

A has separated the terms.

B should now attack the relational model itself:

# **GDF2-B — Difficulty / Challenge Mechanism Tournament & Functional Reconstruction**

Questions:

```text
1. Is FunctionalDifficultyRelation too broad to be useful?
2. Can StructuralDemandProfile be specified without becoming a giant feature bag?
3. Is SkillChallenge really capability sensitivity, or does that miss search, learning, endurance and self-authored challenge?
4. How should feasibility, success probability, skill sensitivity, error tolerance, information burden, opponent pressure, stochasticity and recovery cost relate?
5. Can two tasks with identical success probability have radically different functional difficulty profiles?
6. What becomes of challenge when the outcome is continuous/nonterminal rather than success/failure?
7. Can a task be high challenge while already mastered because the evaluation target is expressive/style optimization?
8. Does assistance reduce challenge, relocate challenge, or change the attribution target?
9. Which variables are Game-owned versus Human experienced difficulty?
10. Which candidate laws survive puzzle, PvP, sandbox, roguelike, rhythm, motor, accessibility and synthetic controls?
```

B should use matched structural probes rather than another terminology expansion.

---

# Primary evidence anchors emphasized in A

- Guadagnoli & Lee (2004), *Challenge Point: A Framework for Conceptualizing the Effects of Various Practice Conditions in Motor Learning*, Journal of Motor Behavior 36(2):212–224, DOI 10.3200/JMBR.36.2.212-224.
- Moneta & Csikszentmihalyi (1996), *The Effect of Perceived Challenges and Skills on the Quality of Subjective Experience*, Journal of Personality 64:275–310, DOI 10.1111/j.1467-6494.1996.tb00512.x.
- Fong, Zaleski & Leach (2015), *The challenge–skill balance and antecedents of flow: A meta-analytic investigation*, Journal of Positive Psychology 10:425–446, DOI 10.1080/17439760.2014.967799.
- Ericsson, Krampe & Tesch-Römer (1993), *The Role of Deliberate Practice in the Acquisition of Expert Performance*, Psychological Review 100:363–406, DOI 10.1037/0033-295X.100.3.363.
- Bjork desirable-difficulties program and subsequent empirical work on spacing/interleaving/retrieval/contextual interference; used only for the performance-vs-learning separation, not a universal hard-is-better claim.
- Ryan, Rigby & Przybylski (2006), *The Motivational Pull of Video Games: A Self-Determination Theory Approach*, Motivation and Emotion 30:344–360, DOI 10.1007/s11031-006-9051-8.
- Frommel, Klarkowski & Mandryk (2021), *The Struggle is Spiel: On Failure and Success in Games*, FDG 2021, DOI 10.1145/3472538.3472565.
- Ang & Mitchell (2017), *Comparing Effects of Dynamic Difficulty Adjustment Systems on Video Game Experience*, CHI PLAY 2017, DOI 10.1145/3116595.3116623.
