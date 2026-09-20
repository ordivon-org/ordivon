---
schema_version: 1
id: game.deep-foundations.gdf2-b
title: Ordivon Game Deep Foundations — GDF2-B Difficulty / Challenge Mechanism Tournament & Functional Reconstruction
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Attacks GDF2-A's broad FunctionalDifficultyRelation and local-sensitivity SkillChallenge candidate. Uses matched response-surface probes and external IRT/game-difficulty evidence to separate capability threshold/location from capability discrimination, skill-independent chance/opponent effects and consequence/recovery. Retires StructuralDemandProfile and FunctionalDifficultyRelation as giant named objects, reconstructing difficulty as query-specific projections over a CapabilityOutcomeSurface under an exact ChallengeConditionSpec. Assistance can shift, flatten or relocate challenge; continuous challenge need not contain binary failure. No frozen foundation reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf2-a
  - game.action-control-skill-foundations.v1
---
# Ordivon Game Deep Foundations — GDF2-B

## 0. B attacks A rather than decorating it

A proposed:

```text
StructuralDemandProfile
+
SkillProfile / access / opponent / stochasticity / history
→ FunctionalDifficultyRelation
```

and suggested that a `SkillChallengeRelation` might be approximated by sensitivity of relevant outcomes to changes in SkillProfile.

B finds two problems.

First:

```text
StructuralDemandProfile
```

is on a path toward a giant feature bag.

Second:

```text
local skill sensitivity
```

is useful, but it resembles **discrimination**, not the whole phenomenon called challenge.

So B performs a reconstruction.

Canonical artifacts:

```text
evidence/gdf2-b/functional-reconstruction.json
evidence/gdf2-b/functional-difficulty-probes.json
scripts/gdf2-b/functional-difficulty-probes.mjs
scripts/gdf2-b/audit-functional-reconstruction.mjs
```

---

# 1. The external model we had not yet exploited enough: response functions

Item Response Theory provides a useful pressure test precisely because it is **narrow**.

A one-parameter logistic/Rasch response function separates:

```text
person ability
item difficulty/location
```

through the probability of a correct response.

A two-parameter model adds:

```text
item discrimination / response-curve slope.
```

A three-parameter model can additionally represent a lower asymptote such as guessing.

The lesson for Game is not:

```text
All game difficulty = Rasch/IRT.
```

The lesson is:

> even a mature one-dimensional binary-response science refuses to identify success probability, capability threshold and capability discrimination as the same variable.

GDF2 should be at least as careful.

---

# 2. B1 — Equal success probability, different skill discrimination

Construct two response curves at the same current SkillProfile.

Both satisfy:

```text
P(success) = 0.5
```

but one has a steep slope around the current profile while the other is nearly flat.

The steep task strongly distinguishes nearby capability differences.

The shallow task gives nearly the same success probability across a broad capability range.

Therefore:

```text
EqualFailureRate != EqualSkillChallenge.
```

More precisely:

```text
OutcomeProbability != CapabilityDiscrimination.
```

This directly falsifies pass/fail rate as a complete challenge measure.

---

# 3. B2 — Equal discrimination, different threshold

Now hold response-curve shape/slope constant and move its location.

One criterion is reached around a lower capability region.
The other requires a higher capability region.

Therefore:

```text
CapabilityThreshold != CapabilityDiscrimination.
```

This distinction is conceptually close to IRT's location/difficulty versus discrimination separation, but GDF2 generalizes away from:

```text
one scalar ability
one binary item
one fixed test condition.
```

---

# 4. A's `SkillChallengeRelation = local sensitivity` is therefore demoted

The local derivative is useful.

It tells us:

> around this current capability point, how much does a small capability change alter the relevant outcome distribution?

But it fails as the complete definition of challenge.

Why?

A task can have:

```text
high threshold
low local discrimination at the current point
```

because the player is far below the frontier.

Another can have:

```text
moderate threshold
very high discrimination
```

near a tight precision boundary.

A continuous expressive task can have useful gradients over several dimensions without any binary threshold.

Thus B replaces one `SkillChallengeRelation` with two derived views:

# **CapabilityThresholdRegion**

and

# **CapabilityDiscriminationProfile**

Neither alone is `challenge`.

---

# 5. StructuralDemandProfile is also too broad

A's list contained:

```text
information limits
timing
precision
resources
opponents
stochasticity
constraints
consequence/recovery
```

This is descriptively true but theoretically weak.

Almost anything can be put into the bag.

B therefore retires it as a primary explanatory object.

What we need first is not a feature vector but an exact **condition boundary**.

---

# 6. New minimal contract: ChallengeConditionSpec

A challenge query must bind the current:

```text
evaluation commitment / criterion
Game/practice state and rules
horizon
attribution target
ControlMapping / ControlLocus / observation/access configuration
opponent/team policy or distribution
stochastic/exogenous process
relevant history/currentness
```

This is metadata/evidence scope, not difficulty itself.

It answers:

> Under exactly what situation are we asking the difficulty/challenge question?

---

# 7. Central reconstruction: CapabilityOutcomeSurface

Instead of asking for one difficulty number, define:

# **CapabilityOutcomeSurface**

> the conditional distribution of evaluation-relevant outcomes/SRVS as the attribution target's SkillProfile/policy varies under one ChallengeConditionSpec.

Research sketch:

```text
P(
  relevant outcome
  |
  target SkillProfile / policy,
  ChallengeConditionSpec
)
```

`Outcome` need not be binary.

It can be:

```text
success probability
completion time
score/quality
error distribution
resource consumption
damage taken
style/expressive quality
multi-objective vector
```

This makes the model compatible with the non-scalar SkillProfile frozen in GDF1.

---

# 8. Why this is better than `Difficulty = fail rate`

Puzzle-difficulty work explicitly notes that completion probability alone fails to describe what players do inside a level, motivating richer action-distribution models.

Earlier game-difficulty work similarly tried to estimate the conditional relationship between player ability and probability of losing/completing a challenge rather than treating content as carrying one absolute difficulty number.

GDF2-B takes the next step:

```text
one ability variable
→ SkillProfile

one binary result
→ relevant outcome distribution

one content item
→ ChallengeConditionSpec
```

without claiming this reconstruction is already a scientific theory of every GameForm.

---

# 9. Feasibility becomes its own relation

Define:

# **FeasibilityRegion**

> the region in which the declared evaluation criterion has nonzero admissible support under current action possibilities/horizon.

Then:

```text
infeasible target
```

and:

```text
very hard but possible target
```

are fundamentally different.

The executable probe preserves:

```text
infeasible:
  support = 0
  skill sensitivity = 0

overmatched-but-possible:
  support > 0
  capability sensitivity > 0
```

Therefore:

```text
Infeasibility != ExtremeDifficulty.
```

---

# 10. Skill-independent outcome variation needs explicit treatment

Consider two tasks with the same 50% midpoint success.

One is mostly controlled by the player's capability.
The other mixes a large random component into the result.

The second response surface is flatter with respect to SkillProfile.

B calls the residual category:

# **SkillIndependentOutcomeComponent**

This can include, depending on attribution target:

```text
RNG
hidden exogenous state transition
uncontrolled teammate behavior
system automation
environmental process
```

But note:

```text
Opponent policy
```

is often better represented separately, because another adaptive controller is not mere noise.

---

# 11. Opponent challenge needs a multi-controller surface

PvP exposes the limitation of content-attached difficulty immediately.

Research sketch:

```text
P(outcome |
  target SkillProfile/policy,
  opponent SkillProfile/policy,
  current Game condition)
```

The same player on the same map can have:

```text
P(win) high vs novice
P(win) low vs expert
```

with no map/content change.

Therefore introduce:

# **OpponentInteractionSurface**

as a multi-controller specialization.

Strong law:

```text
OpponentChallenge != ContentDifficulty.
```

This also generalizes to team composition and Agent opponents.

---

# 12. Consequence and recovery must stay outside the immediate capability surface

Now hold the exact same immediate action/performance challenge fixed.

Version A:

```text
fail
→ restart 2 seconds ago
→ no resource loss
```

Version B:

```text
fail
→ 15-minute run reset
→ large resource/history loss
```

The immediate capability requirement can be identical.

But the consequences of failure differ drastically.

Therefore:

```text
ConsequenceRecoveryProfile
!= CapabilityOutcomeSurface.
```

and:

```text
CheapRetry != EasyChallenge
SevereReset != HighSkillChallenge.
```

This is essential for roguelike, soulslike, checkpoint, permadeath and competitive stakes analysis.

---

# 13. FunctionalDifficultyRelation is demoted to a projection

A treated FunctionalDifficultyRelation almost like a named object.

B finds it is better understood as a query.

# **FunctionalDifficultyProjection**

A purpose-specific projection over:

```text
CapabilityOutcomeSurface
FeasibilityRegion
CapabilityThresholdRegion
CapabilityDiscriminationProfile
SkillIndependentOutcomeComponent
OpponentInteractionSurface when relevant
ConsequenceRecoveryProfile
```

Examples:

```text
"What capability region gives 80% completion?"
→ threshold projection.

"How strongly does this encounter distinguish nearby aiming SkillProfiles?"
→ discrimination projection.

"How likely is run loss and how expensive is recovery?"
→ outcome-risk + recovery projection.

"Will this exercise reveal useful retention differences?"
→ learning-specific projection.
```

There is no privileged universal projection.

---

# 14. Functional difficulty is therefore not one latent Game scalar

This is now stronger than A.

A said:

```text
Difficulty is relational.
```

B says:

> Even after making difficulty relational, there may still be no single latent scalar relation worth recovering.

Different questions legitimately project different aspects of the surface.

So:

```text
FunctionalDifficulty != hidden scalar f(Game, Player).
```

unless a specific narrow model earns that reduction for a specific task family.

---

# 15. Continuous challenge kills binary-failure dependence

Consider a free-form performance target:

```text
make the racing line smoother
increase style quality
optimize a combo route
produce a more elegant sandbox structure
```

There may be no authoritative binary FailureEvent.

Yet differences in capability can continuously alter relevant quality.

The executable probe produces:

```text
binaryFailureDefined = false
quality(skill=0.8) > quality(skill=0.2)
```

Therefore:

```text
Challenge does not require binary FailureEvent.
```

This preserves open-ended and mastery-oriented forms.

---

# 16. Mastered tasks can remain challenge-bearing under changed evaluation commitments

Suppose the participant has mastered ordinary completion.

The original completion surface may saturate:

```text
P(clear) ≈ 1
```

but the participant/community adopts:

```text
no-damage clear
speed target
style target
minimal-resource route
higher opponent class
```

This creates a new ChallengeConditionSpec and therefore a new response surface.

No contradiction exists with:

```text
Capability != SkillExpression.
```

The old evaluation stopped expressing capability; the new one may expose it again.

---

# 17. Assistance has at least three different geometric effects

A said assistance can alter functional difficulty.

B specifies **how**.

## 17.1 Threshold shift

An accessibility remap or assist can reduce the capability region required to access/complete the target while preserving slope/discrimination of relevant higher-order skill.

```text
CapabilityThresholdRegion shifts
CapabilityDiscriminationProfile roughly preserved
```

This is not simply `challenge removed`.

## 17.2 Surface flattening

Automation can make outcomes less sensitive to Human SkillProfile.

```text
joint performance ↑
Human capability discrimination ↓
```

This can reduce Human skill expression even while success rises.

## 17.3 Challenge relocation

An assist can remove one capability demand and expose another.

Example:

```text
auto-stabilize aiming precision
+
leave target selection / resource strategy fully participant-controlled
```

Then challenge changes dimension rather than monotonically falling.

Thus:

```text
Assistance can shift, flatten, or redirect a capability-outcome surface.
```

---

# 18. This also clarifies rehabilitation/adaptive-interface evidence

Experiments that independently manipulate game difficulty and haptic assistance are especially useful because they show these are not one control knob.

One intervention changes external task/challenge parameters.
Another changes the effective participant-system capability relation.

GDF2 therefore refuses:

```text
assist level = inverse difficulty
```

as a universal law.

It depends on what dimension the assist changes and whose capability is attributed.

---

# 19. History belongs in the condition, not as an afterthought

Same puzzle:

```text
same artifact
same formal rules
same control mapping
```

Before knowing the solution, a participant may have low success.

After solution memory/history, success can approach certainty.

The artifact's structural content did not change.

Therefore:

```text
SameArtifact + SameRules
!= SameCurrentChallengeSurface.
```

History/knowledge belongs in the scope through frozen SkillProfile/current state rather than forcing the content's `difficulty` parameter to mutate metaphysically.

---

# 20. Response-surface theory also exposes population-selection errors

Suppose a live game reports:

```text
Level 50 pass rate = 80%.
```

That does not by itself identify the challenge for a new population.

Players who reached Level 50 may already be selected for:

```text
higher skill
higher persistence
specific playstyle
better equipment
survival through prior gates
```

So empirical pass rate is a projection of:

```text
challenge surface × observed population/history
```

not a content constant.

This reinforces GDF1's evidence discipline and is one reason synthetic/policy probes can help separate content structure from population selection—without becoming PlayerValue evidence.

---

# 21. Model tournament verdict

## IRT/Rasch-style response model

**Survives strongly as analogy/measurement pressure**:

```text
ability relation
location/threshold
discrimination
chance/asymptote
```

**Does not generalize unchanged** to multidimensional SkillProfile, adversarial policy, continuous quality, recovery or open evaluation.

## Completion/pass-rate difficulty

**Survives as one projection**.

**Rejected as total difficulty**.

## Challenge Point Framework

**Survives for learning-specific relational challenge**.

**Not universal Game challenge ontology**.

## Flow challenge-skill models

**Survive as Human antecedent/outcome research**.

**Not structural difficulty law**.

## DDA

**Survives as intervention framework**.

**Not proof that one performance-matching target optimizes experience, learning or PlayerValue**.

## GDF2 response-surface reconstruction

**Survives B**, but remains N1 and unproven as the minimal final model.

C must attack identifiability and measurement burden.

---

# 22. B's reconstructed graph

```text
Current Evaluation Commitment
          +
ChallengeConditionSpec
          │
          ├── target SkillProfile / policy
          ├── access/control/observation
          ├── opponent/team profiles/policies
          ├── stochastic/exogenous process
          └── history/horizon
          │
          ▼
CapabilityOutcomeSurface
          │
          ├── FeasibilityRegion
          ├── CapabilityThresholdRegion
          ├── CapabilityDiscriminationProfile
          ├── SkillIndependentOutcomeComponent
          └── OpponentInteractionSurface
          │
          ▼
Performance / Error / Failure distributions
          │
          └── ConsequenceRecoveryProfile
          │
          ▼
query-specific FunctionalDifficultyProjection
```

Human-side:

```text
ExperiencedDifficulty
Frustration
SubjectiveCompetence
Flow
PlayerValue
```

consume this structure plus Human state/history; they are not contained inside it.

---

# 23. Strong B laws

```text
FunctionalDifficulty is a projection, not a primitive scalar.

OutcomeProbability != CapabilityThreshold != CapabilityDiscrimination.

CapabilityDiscrimination != PlayerValue.

SkillIndependentOutcomeVariation != SkillChallenge.

OpponentChallenge != ContentDifficulty.

ConsequenceRecoveryProfile != CapabilityOutcomeSurface.

FailureProbability != FailureCost.

CheapRetry != EasyChallenge.

SevereReset != HighSkillChallenge.

ContinuousChallenge does not require binary FailureEvent.

Assistance can shift, flatten or redirect a capability-outcome surface.

AssistanceEffect requires attribution target.

Same artifact/rules != same current challenge surface when history/access/opponent/evaluation changes.
```

---

# 24. What B retires from A

```text
StructuralDemandProfile
→ RETIRE as primary object.

FunctionalDifficultyRelation
→ DEMOTE to query/projection family.

SkillChallengeRelation = local skill sensitivity
→ RETIRE as complete definition.
```

Retained/reconstructed:

```text
ChallengeConditionSpec
CapabilityOutcomeSurface
FeasibilityRegion
CapabilityThresholdRegion
CapabilityDiscriminationProfile
SkillIndependentOutcomeComponent
OpponentInteractionSurface
ConsequenceRecoveryProfile
FunctionalDifficultyProjection
```

This is not final freeze vocabulary.

C should be expected to delete more.

---

# 25. Novelty ledger after B

## N0

```text
IRT response models separate location/difficulty and discrimination;
completion rate is an incomplete level descriptor in richer game telemetry;
adaptive systems already manipulate multiple difficulty/assistance dimensions;
flow/experience outcomes remain separate from absolute skill/performance.
```

## N1

```text
ChallengeConditionSpec
CapabilityOutcomeSurface
FeasibilityRegion
CapabilityThresholdRegion
CapabilityDiscriminationProfile
SkillIndependentOutcomeComponent
OpponentInteractionSurface
ConsequenceRecoveryProfile
FunctionalDifficultyProjection
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

# 26. Foundation reopen audit

B changed GDF2's derived model substantially but does not challenge frozen GDF1.

Indeed the response-surface reconstruction directly consumes:

```text
SkillProfile
SRVS
ProbeTransformation
ControlMapping / ControlLocus
Capability != Expression
```

No new semantic coordinate is required.

Therefore:

```text
ACS reopen = NOT TRIGGERED
GDF0 reopen = NOT TRIGGERED
R29 reopen = NOT TRIGGERED
```

---

# 27. Exact GDF2-C frontier

B has a smaller and more testable model, but one danger remains:

> We may have replaced one giant feature bag with one giant abstract response surface that is impossible to identify or use.

So C must be a **minimal operational reconstruction / identifiability round**.

# **GDF2-C — Challenge Surface Operationalization & Identifiability**

Questions:

```text
1. What is the minimum evidence needed to distinguish threshold, discrimination, stochasticity and infeasibility?
2. Which of these can be inferred from player data, synthetic agents, structural analysis, or interventions?
3. When are two CapabilityOutcomeSurfaces observationally indistinguishable under current probes?
4. How does multidimensional SkillProfile create compensatory routes rather than one threshold?
5. Can nonmonotonic capability-outcome relations exist and how should mastery/challenge handle them?
6. How should opponent/team policies be probed without collapsing them into noise?
7. What exact information does recovery topology add beyond a post-outcome cost vector?
8. Can assistance transformations be classified by response-surface intervention rather than design label?
9. Which parts should freeze later and which are measurement tools only?
```

C should construct executable identifiability counterexamples rather than add more `difficulty dimensions`.
