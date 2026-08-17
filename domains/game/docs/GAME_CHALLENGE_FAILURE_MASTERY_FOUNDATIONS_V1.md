---
schema_version: 1
id: game.challenge-failure-mastery-foundations.v1
title: Ordivon Game — Challenge / Failure / Mastery Foundations v1
profile: research
lifecycle: frozen
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Frozen GDF2 foundations for challenge/difficulty, failure/recovery and mastery after A-F. Rejects intrinsic scalar difficulty, context-free failure and global Mastered state. Freezes exactly three Game-owned responsibility/query contracts—ChallengeAssessmentContract, FailureRecoveryContract and MasteryClaimContract—plus minimal anti-collapse, attribution, currentness and identification guards. Response surfaces, thresholds/discrimination, recovery-transition views and identifiability tooling remain derived; Human experience/learning, social mastery and deeper opponent strategy are explicit handoffs.
readiness: FROZEN_V1
applies_to:
  - ordivon-game
related:
  - game.action-control-skill-foundations.v1
  - game.play-game-deep-foundations.v1
---
# Ordivon Game — Challenge / Failure / Mastery Foundations v1

## 0. Scope

This v1 freezes the minimum Game-owned responsibilities needed to reason correctly about:

```text
challenge / difficulty claims
failure / recovery claims
mastery claims
```

without creating:

```text
one Difficulty scalar
one Failure essence
one FailureSeverity scalar
one LearningOpportunity checklist
one Mastered boolean
one universal mastery breadth
```

It consumes frozen:

```text
R1-R29 / F1-F9
Play / Game Deep Foundations v1
Action / Control / Skill Foundations v1
```

especially:

```text
Evaluation / Authority / Provenance / Currentness
State / Transition / History
Observation
GameActionContract
ControlMapping / ControlLocus
SkillProfile
SkillRelevantVariableSet
ProbeTransformation
Capability != SkillExpression
```

The three frozen items below are **domain responsibility/query contracts**, not new semantic primitives.

---

# 1. Frozen responsibility CFM-1 — ChallengeAssessmentContract

A challenge/difficulty claim is incomplete unless it binds enough scope to identify what relation is being queried.

As relevant, declare:

```text
current evaluation criterion / commitment
criterion authority/provenance/currentness
attribution target
Game/practice state and rules
horizon
control / observation / access configuration
relevant history/knowledge
opponent/team condition when present
stochastic/exogenous condition when present
```

Then report only the challenge property actually established by the evidence.

Possible derived projections include:

```text
outcome probability/distribution
feasibility/reachability
capability threshold region
capability discrimination/sensitivity
outcome risk
opponent-conditioned outcome
recovery/consequence cost
```

No projection is privileged universally.

Strong laws:

```text
Difficulty/Challenge != intrinsic scalar property of content
OutcomeProbability != CapabilityThreshold != CapabilityDiscrimination
OutcomeRisk != SkillChallenge by identity
Infeasibility != MaximumSkillChallenge
OpponentChallenge != ContentDifficulty
SameArtifact/Rules != SameCurrentChallenge when history/access/opponent/evaluation changes
```

`FunctionalDifficulty` is therefore a query/projection family, not a frozen latent scalar field.

---

# 2. Challenge evidence and identification guard

Challenge structure is often underidentified from aggregate observational data.

Therefore:

```text
AggregatePassRate != unique ChallengeAssessment
```

A challenge claim must not be upgraded beyond what current structural analysis, observations and interventions support.

Acceptable epistemic descriptions can include:

```text
structurally proven
intervention-identified under assumptions
statistically estimated under a declared model
bounded only
unidentified / multiple explanations remain
```

Exact labels are methodology vocabulary, not Game ontology.

If multiple materially distinct challenge explanations remain compatible with the evidence, preserve the unresolved alternatives rather than selecting one silently.

Synthetic policies can provide controlled structural probes, but:

```text
Synthetic challenge/mastery evidence != Human experienced difficulty/mastery by identity.
```

---

# 3. Frozen responsibility CFM-2 — FailureRecoveryContract

Failure is not a context-free event essence.

A `FailureAssessment` is an evaluation/provenance-bound determination that a declared criterion was not satisfied within a declared scope/horizon.

Therefore:

```text
Failure requires EvaluationScope / Horizon.
```

The same history can be:

```text
success for one commitment
failure for another.
```

Strong laws:

```text
Failure != Error
Failure != Punishment
Failure != Loss
Failure != Setback
Failure != Death
Failure != GameOver
Failure != Reset
Failure != Terminality
```

A Game may emit an authoritative failure signal, but that signal remains scoped to the criterion/practice for which the Game has authority.

---

# 4. Recovery responsibility is conditional, not universal

When post-outcome continuation matters, represent the authoritative recovery transitions explicitly enough for the claim.

A derived `RecoveryTransitionSet` can include:

```text
continue from current state
checkpoint restore
revive
full reset
team rescue
alternate route/goal
meta-progression then new run
no continuation
```

and relevant preservation/loss of:

```text
state
resources
history/progress
information
time/opportunity
pursuit identity
```

But sandbox/creative/continuous practice can have challenge without any authoritative failure/recovery structure.

Therefore RecoveryTransitionSet is an optional derived view, not a universal Game object.

Terminality is a derived question:

> under the current pursuit identity and horizon, does any authoritative continuation transition preserve pursuit of the same commitment?

No independent terminality primitive is required.

---

# 5. Failure severity remains query-relative

Different recovery transitions can trade off:

```text
time loss
resource loss
history/progress loss
information loss
social/opportunity interruption
```

without one transition dominating every coordinate.

Therefore:

```text
RecoveryTransitionSet != UniversalFailureSeverityScalar
FailureProbability != FailureCost
CheapRetry != EasyChallenge
SevereReset != HighSkillChallenge
```

A `QuerySpecificRecoveryCostProjection` is legitimate only when the evaluation/weighting purpose is explicit.

---

# 6. Failure, feedback and learning

GDF2 does **not** freeze a universal LearningOpportunityProfile.

Cross-GameForm attack showed that:

```text
direct controllability
same-instance retry
single-message diagnosticity
```

are useful in many learning settings but are not universal necessary conditions for acquiring useful information.

The frozen boundary is smaller:

```text
Failure / Feedback != LearningOpportunity != ActualLearning.
```

A Game-side claim that an episode provides learning opportunity should state what relevant information/distinction becomes available and what future SkillProfile/policy probe could reveal its use.

Actual Human/System learning, memory, retention and learning mechanism remain owner-specific evidence.

---

# 7. Multi-controller failure attribution

Collective outcomes require attribution discipline.

```text
TeamLoss != IndividualFailure != IndividualSkillDeficit.
```

A team can lose while one participant satisfies an independently declared role criterion.

Likewise joint/shared-controller outcomes do not identify which controller supplied the relevant capability without contribution/attribution evidence.

This guard applies to Human-Human, Human-Agent, Agent-Agent and assistive/shared-control systems.

---

# 8. Frozen responsibility CFM-3 — MasteryClaimContract

Mastery is not a Game-state boolean.

A mastery claim is a scoped inference over the frozen `SkillProfile` of an explicit attribution target.

As relevant, the claim declares:

```text
attribution target
practice/category/evaluation scope
criterion and its authority/provenance
condition/currentness/version scope
ProbeTransformation set
claimed robustness/generalization dimensions
history/retention horizon where claimed
assistance/control configuration
identification/evidence status
```

The criterion and claimed probe/condition region must have independent provenance from the target performance used as evidence, **or** the claim must be validated on held-out/independent ProbeTransformations.

This prevents circular mastery definitions.

---

# 9. Mastery evidence guards

```text
DemonstratedPerformance != CapabilityMasteryClaim
Completion != Mastery
HighScore != Mastery
ZeroError != Mastery
PerformancePlateau != Mastery
ObservedPlateau != SkillCeiling
```

A single run, score, rank or zero-error streak can be evidence under exact conditions; it does not establish a broader SkillProfile claim by identity.

A saturated trivial condition can fail to express capability differences entirely.

---

# 10. Mastery scope and transfer

A local mastery claim may be narrow and legitimate.

```text
TaskSpecificMastery != TransferMastery.
```

Retention, perturbation and transfer probes are required only when those dimensions are part of the claim.

When transfer is claimed, exact changed/held-fixed dimensions must be represented through frozen `ProbeTransformation`.

Currentness matters:

```text
Mastery(version/context A) != Mastery(version/context B) by identity.
```

Patch, ruleset, mapping, opponent distribution, assistance or evaluation changes are transformations whose transfer must be established rather than assumed.

---

# 11. Open-ended and continuous mastery

Mastery does not require terminal completion.

A creative/expressive/open-ended practice can support a bounded claim such as:

```text
robustly satisfies an independently anchored quality/control criterion
across a declared probe region
```

without implying:

```text
global maximum capability
exhaustive domain mastery
maximum creativity
```

Therefore:

```text
LocalMasteryClaim != ExhaustiveDomainMastery.
```

---

# 12. Mastery attribution boundaries

```text
JointControllerMastery != HumanIndependentMastery
SyntheticControllerMastery != HumanMastery
CapabilityMastery != SubjectiveCompetence
CapabilityMastery != SocialMastery
```

A Human+assist system can legitimately be the mastery attribution target.
A synthetic policy can legitimately satisfy a synthetic-policy mastery claim.
Neither creates Human-independent capability or Human experience evidence automatically.

Subjective competence belongs to Human.
Community rank/recognition/credential legitimacy belongs to Practice/Social/Institutional authority.

---

# 13. Frozen minimal anti-collapse law set

## Challenge

```text
Difficulty/Challenge != intrinsic content scalar
Challenge claim requires evaluation + attribution + condition/horizon/currentness scope
OutcomeProbability != CapabilityThreshold != CapabilityDiscrimination != OutcomeRisk != RecoveryCost
Infeasibility != MaximumSkillChallenge
AggregatePassRate != unique ChallengeAssessment
```

## Failure / recovery

```text
Failure requires evaluation scope/horizon
Failure != Error/Punishment/Loss/Setback/Death/GameOver/Reset
Failure != Terminality
RecoveryTransitionSet != UniversalFailureSeverity
TeamLoss != IndividualFailure != IndividualSkillDeficit
Failure/Feedback != LearningOpportunity != ActualLearning
```

## Mastery

```text
DemonstratedPerformance != CapabilityMasteryClaim
Completion/HighScore/ZeroError/Plateau != Mastery
TaskSpecificMastery != TransferMastery
Mastery criterion/probe region cannot be defined solely from the same target performance used as evidence
JointControllerMastery != HumanIndependentMastery
Synthetic mastery evidence != Human mastery/experience evidence
Mastery does not require terminal completion or globally maximal capability
```

## Evidence/currentness

```text
Unidentified alternatives remain explicit
Challenge/failure/mastery claims are version/currentness/provenance bound
PlayerValue / felt difficulty / flow / frustration / subjective competence require Human evidence
```

---

# 14. Derived research views — useful, not frozen core

```text
NominalDifficultySetting
OutcomeRisk
CapabilityOutcomeSurface / ChallengeResponseModelFamily
CapabilityThresholdRegion
CapabilityDiscriminationProfile
AttributionResidualClass
FunctionalDifficultyProjection
PursuitTerminalityQuery
RecoveryTransitionSet
QuerySpecificRecoveryCostProjection
DemonstratedMasteryEvidence
ChallengeObservationDesign / ChallengeInterventionSet / IdentificationStatus
```

These can evolve without reopening v1 unless a frozen law is contradicted.

---

# 15. Explicit owner boundaries

## Game owns

```text
challenge/failure/mastery claim scope over Game-authoritative criteria/conditions
Game-authoritative outcome/history evaluation
post-outcome recovery transitions when they exist
Game-side capability/mastery evidence over SkillProfile
currentness/provenance of Game criteria/rules/conditions
```

## Human owns

```text
ExperiencedDifficulty
Frustration
FlowExperience
SubjectiveCompetence
Human learning/memory/retention mechanisms
Human PlayerValue / felt meaning
```

## Practice / Social / Institution owns

```text
community category criteria
rank / credential / recognition legitimacy
SocialMastery
```

## Later Strategy foundations own

```text
adaptive opponent policy
counterplay
nontransitivity
equilibrium/balance/team strategic interaction
```

GDF2 can consume those conditions without owning their deeper mechanism.

---

# 16. FoundationReopenConditions

Reopen this v1 only when a concrete repeated phenomenon satisfies one of the following.

## CFM-PRC-1 — Challenge scope failure

A meaningful challenge/difficulty claim cannot be represented as an evaluation/attribution/condition/horizon-bound identified or bounded projection without losing a repeated causal distinction.

## CFM-PRC-2 — Scalar necessity failure

At least two materially different GameForms require the same privileged intrinsic challenge/difficulty scalar, and that scalar predicts counterfactuals not expressible by current scoped relations/projections.

## CFM-PRC-3 — Failure evaluation failure

A repeated failure phenomenon cannot be represented as criterion/scope/horizon-relative assessment over existing evaluation/state/history authority relations.

## CFM-PRC-4 — Recovery failure

A repeated continuation/reset/revival/retry phenomenon materially affects failure semantics but cannot be represented through existing Transition/State/History/Authority relations plus an optional recovery-transition view.

## CFM-PRC-5 — Mastery claim failure

A legitimate mastery/capability claim cannot be represented as a scoped inference over frozen SkillProfile with explicit attribution/currentness/probes/criterion provenance.

## CFM-PRC-6 — Attribution failure

Shared/team/synthetic/assistive cases repeatedly require challenge/failure/mastery attribution not expressible through existing target identity/control contribution relations.

## CFM-PRC-7 — Learning boundary failure

Repeated Game-side learning-opportunity phenomena require a domain responsibility beyond information/distinction exposure plus future probe claims and cannot be handed to Human/System learning owners without explanatory loss.

## CFM-PRC-8 — Repeated downstream contradiction

At least two materially different downstream GameForms repeatedly falsify the same frozen CFM law rather than a derived measurement model, local criterion or owner-specific mechanism.

A new difficulty mode, boss, genre, ranking system, accessibility option, Agent controller, live-service patch, failure animation or mastery badge is not itself a reopen condition.

---

# 17. Upstream foundation audit

GDF2-A→F attacked the frozen stack with:

```text
motor and symbolic challenge
random and infeasible outcomes
continuous/open-ended quality targets
PvP/team attribution
roguelike death/permadeath
checkpoint/reset/recovery variation
sandbox/self-authored criteria
creative/expressive mastery
accessibility/shared control
synthetic policies
population selection / underidentification
live-service/version changes
learning-opportunity and transfer pressure
```

No case requires a new semantic primitive beyond F1-F9.
No GDF0 Play/Game law is contradicted.
No GDF1 Action/Control/Skill law is contradicted.

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 reopen = NOT TRIGGERED
GDF1 ACS reopen = NOT TRIGGERED
```

---

# 18. Freeze verdict

```text
GDF2-A→F = COMPLETE

Challenge / Failure / Mastery Foundations v1 = FROZEN

Frozen core responsibilities = 3

ChallengeAssessmentContract
FailureRecoveryContract
MasteryClaimContract

Difficulty scalar = REJECTED
FunctionalDifficultyRelation latent object = RETIRED
CapabilityOutcomeSurface = DERIVED MODEL FAMILY
LearningOpportunityProfile = RETIRED
PursuitTerminalityClaim = DERIVED QUERY
RecoveryTransitionSet = OPTIONAL DERIVED STRUCTURAL VIEW
MasteredBoolean = RETIRED
OpponentInteractionSurface = HANDOFF Strategy
Human difficulty/flow/frustration/competence/learning = HANDOFF Human
Social mastery/rank legitimacy = HANDOFF Practice/Social/Institution

R1-R29 / F1-F9 = unchanged
GDF0 = unchanged
GDF1 = unchanged

next deep branch = GDF3 Game Feel / Feedback / Sensorimotor Coupling
```
