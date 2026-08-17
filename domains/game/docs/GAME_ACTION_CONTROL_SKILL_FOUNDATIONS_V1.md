---
schema_version: 1
id: game.action-control-skill-foundations.v1
title: Ordivon Game — Action / Control / Skill Foundations v1
profile: research
lifecycle: frozen
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Frozen deep foundations for Game action, control and skill after GDF1-A→F. Defines a six-responsibility core—GameActionContract, ControlMapping, ControlLocus, SkillProfile, SkillRelevantVariableSet and ProbeTransformation—plus evidence/anti-collapse guards. Embodiment is not frozen as one construct; body/tool details remain sparse derived action couplings, while Human motor/ownership/agency mechanisms and downstream challenge/mastery constructs are handed off.
readiness: FROZEN_V1
applies_to:
  - ordivon-game
related:
  - game.play-game-deep-foundations.v1
  - game.foundations-research.r21
---
# Ordivon Game — Action / Control / Skill Foundations v1

## 0. Scope

This v1 freezes the minimum Game-owned responsibilities required to reason correctly about:

```text
participant/controller action semantics
control mapping and locus
skill evidence across conditions/history
transfer/remap/perturbation claims
structural body/tool/control coupling when it changes action
```

It does **not** freeze:

```text
one Human motor-control theory
one scalar Skill number
one Technique ontology
one Embodiment variable
one difficulty/skill-floor/skill-ceiling scalar
one PlayerValue assumption
```

R1–R29/F1–F9 and Play/Game Deep Foundations v1 remain the semantic substrate.

---

# 1. Frozen core responsibility C1 — GameActionContract

A GameAction is a Game-local semantic action identity governed by current action/admission/consequence semantics.

The contract must be able to distinguish:

```text
input/control evidence
action attempt/candidate action
admission/current legality
executed GameAction/state transition
world/task consequence
```

Strong laws:

```text
InputSignal != GameAction
PlayerMotorMovement != GameAction
ActionAttempt != ExecutedAction
ExecutedAction != TaskSuccess
MovementTrajectory != TaskOutcome
```

One GameAction may be expressed through multiple physical mappings.
One raw input may denote different GameActions under different contexts.
High-level GameAction may be player-owned while low-level execution is delegated to a system/controller.

---

# 2. Frozen core responsibility C2 — ControlMapping

`ControlMapping` is the current context/version/provenance-bound relation that maps input/control expression into Game-relevant control variables and/or candidate GameActions.

It may include:

```text
remapping
gain/transfer function
deadzone/filtering
mode/context
assistance preprocessing
```

but the exact implementation is not foundational.

Strong laws:

```text
InputEffector != ControlMapping
ControlAccess != GameActionSemantics
DifferentMapping != necessarily DifferentGameSkill
SameGameAction != necessarily SameLowLevelExecutionSkill
```

Mapping changes must be represented as transformations rather than silently treated as equivalent control conditions.

---

# 3. Frozen core responsibility C3 — ControlLocus

`ControlLocus` is the Game-local locus at which a participant/controller's control becomes authoritative/relevant to Game action/state.

Examples may include:

```text
avatar
vehicle
cursor
piece
camera
squad/army
remote tool
policy/command surface
```

Strong laws:

```text
ControlLocus != BiologicalBody
ControlLocus != InputEffector
ControlLocus != AvatarAppearance
ControlLocus != SelfLocationExperience
```

A Game may explicitly bind several roles together, but the binding is a relation, not a universal identity.

---

# 4. Frozen core responsibility C4 — SkillProfile

`SkillProfile` is a learned, history-dependent conditional capability profile over a declared scope.

A serious Skill claim must identify enough scope to make the capability claim falsifiable, including as relevant:

```text
attribution target
practice/task/GameForm/ruleset scope
control configuration
current evaluative commitments
condition/probe/transformation space
history/timescale
```

Formal research sketch:

```text
P(
  SkillRelevantVariable outcomes
  |
  attribution target history,
  practice/task scope,
  control configuration,
  probe transformation
)
```

This is an evidence representation, not a claim about neural storage.

Strong laws:

```text
PerformanceSample != SkillProfile
CurrentPerformance != DurableLearning
Skill != Accuracy
Skill != ReactionTime
Skill != ExactRepetition
SkillProfile need not be scalar
Two SkillProfiles may remain incomparable without declared weighting/value
```

SkillProfile applies to motor, perceptual, strategic, symbolic and synthetic capability claims when the attribution/evidence target is explicit.

---

# 5. Frozen core responsibility C5 — SkillRelevantVariableSet (SRVS)

`SkillRelevantVariableSet` is the current set of variables whose variation is causally/evaluatively relevant to the Skill claim under the current GameStructure, evaluative commitments and control attribution.

Admission requires:

```text
explicit observation/derivation provenance;
a non-arbitrary causal/evaluative relation to the current skill/evaluation claim;
relevance to variables the attribution target can influence, expose or be evaluated upon;
no post-hoc promotion merely because a metric correlates with experts.
```

Relevance may arise from:

```text
formal Game evaluation
participant-authored current project/goal
community-constitutive practice/category
team/social commitment
institutional brief
research measurement target
explicit PlayerValue hypothesis
```

with source/currentness/provenance kept distinct.

Strong laws:

```text
NoFixedGlobalGoal != NoSkillRelevantEvaluation
MetricCorrelatesWithExperts != SkillRelevantByIdentity
DeclaredPlayerValueHypothesis != EmpiricallyEstablishedPlayerValue
GlobalLowVariability != MoreSkill
```

TaskRelevantVariableSet is a fixed-task subtype of SRVS, not the general foundation.

---

# 6. Frozen core responsibility C6 — ProbeTransformation

A `ProbeTransformation` identifies the exact changed and held-fixed dimensions used to interpret:

```text
retention
transfer
remapping
perturbation
adaptation/recalibration
assistance changes
```

Relevant dimensions can include:

```text
input mapping
control gain/transfer function
world/control dynamics
timing/speed
observation/information
action semantics
rules/category/version
evaluation commitment
assistance/contribution topology
task/content distribution
```

Strong law:

```text
TransferEvidence requires TransformationIdentity.
```

Labels such as `near transfer`, `far transfer`, `same controller`, or `same game` are insufficient when the changed/held-fixed dimensions are unknown.

---

# 7. Frozen evidence/anti-collapse guards

## 7.1 Action/control guards

```text
Intent evidence != InputSignal != GameAction != Outcome
Affordance != GameLegality != GameActionAvailability
PlayerGameAction != LowLevelExecutorTrajectory
ControlAccess != GameActionSemantics
```

## 7.2 Skill/learning guards

```text
PerformanceSample != SkillProfile
ImmediatePerformance != DurableLearning
Adaptation/Recalibration != SkillAcquisition by identity
Accuracy != Precision
ReactionTime != TimingSkill
Consistency != ExactRepetition
MotorVariability != Error by identity
```

Task/evaluation relevance determines which variability is error, expressive freedom or irrelevant redundancy.

## 7.3 Assistance/attribution guards

```text
ExactCommandExecutionShare != SenseOfAgency
JointControllerPerformance != HumanIndependentSkill
JointControllerPerformance != SystemIndependentSkill
ImmediateAssistBenefit != IndependentFutureLearning
```

Human, System and Joint capability claims may use the same SkillProfile contract with different attribution targets.

## 7.4 Capability/expression/ceiling guards

```text
Capability != SkillExpression
ObservedPerformancePlateau != SkillCeiling
```

Detailed entry requirement, expression envelope and saturation analysis belongs primarily to GDF2 Challenge/Mastery.

## 7.5 Body/tool/avatar guards

```text
Embodiment != one variable
BiologicalBody != InputEffector != ControlLocus
AvatarAppearance != CollisionBody != VulnerabilityBody
SensorEnvelope != EffectorEnvelope
ObjectiveControl != SenseOfAgency != BodyOwnership != SelfLocationExperience
ToolExtension != BodyOwnership
AnatomicalContinuity != RemoteControlRequirement
StructuralBodyCoupling != ExperientialEmbodiment
```

These are target/owner boundaries, not a frozen Embodiment ontology.

---

# 8. Derived Game views — useful, not frozen core

The following remain valid projections when a concrete GameForm requires them:

```text
SymbolicActionPipeline
ControlContributionTopology
ControlAccessProfile
ActionCouplingProfile
TechniqueFamily
ControllerSpecificSkillProfile
CollisionBody
VulnerabilityBody
ToolVehicleMediation
```

They may be implemented or researched locally without changing this foundation.

## ActionCouplingProfile

The most important derived view is the sparse set of body/tool/control relations whose intervention changes:

```text
observation/sensing
reachable GameActions
effector/reach geometry
control dynamics/inertia
collision/passability
vulnerability/consequence
```

under the current SkillScope.

It is optional and can be nearly empty in symbolic forms.
It is not an `EmbodiedAgent` primitive.

---

# 9. Explicit owner boundaries

## Game owns

```text
GameAction identity/admission/consequence semantics
ControlMapping
ControlLocus
Game-relevant control/action attribution
SkillProfile evidence contract
SkillRelevantVariableSet
ProbeTransformation
structural action/body/tool consequences when Game-authoritative
```

## Human owns

```text
motor-control mechanisms
motor adaptation and neural learning mechanisms
biomechanics/proprioception
body schema/peripersonal representations
body ownership
sense of agency
self-location/felt embodiment
motivation/subjective PlayerValue evidence
```

## Media owns

```text
input/feedback signal representation
avatar/body visual/audio/haptic representation
perspective/scale/multisensory cues
perceptual presentation of action possibilities
```

## World owns

```text
actual material body/tool/environment constraints
```

when Game consumes real-world properties.

---

# 10. Explicit downstream handoffs

## GDF2 Challenge / Difficulty / Failure / Mastery

Consumes:

```text
SkillProfile
SRVS
Capability != Expression
EntryRequirementRegion
SkillExpressionEnvelope
SaturationAttribution
AssistanceTimescaleSeparation
```

GDF1 does not freeze `skill floor`, `skill ceiling` or `difficulty` as intrinsic scalar Game properties.

## GDF3 Game Feel / Feedback / Sensorimotor Coupling

Consumes:

```text
GameActionContract
ControlMapping
ControlLocus
ActionCouplingProfile
ObjectiveControl != SenseOfAgency
```

## GDF4 Time / Rhythm / Pacing

Consumes timing-specific SRVS and ProbeTransformation distinctions.

## GDF5 Space / Level / Navigation

Consumes morphology/reach/collision/control-access projections where spatial action depends on them.

---

# 11. What v1 explicitly does not freeze

```text
SkillState as one number
EvaluationTargetSet as fixed designer goal list
TaskRelevantVariableSet as universal fixed-task ontology
TechniqueFamily as mandatory Skill constituent
EntryRequirementRegion as Action/Skill core
SkillExpressionEnvelope as Action/Skill core
SaturationAttribution as Action/Skill core
Embodiment as one construct
ExperientialEmbodimentProfile as one score
one Internal-Model / Ecological / Optimal-Feedback / Schema winner
```

These are retired, handed off or retained as derived research views.

---

# 12. Action / Control / Skill FoundationReopenConditions

Reopen this v1 only when a concrete repeated phenomenon triggers one of the following.

## ACS-PRC-1 — Action separation failure

A meaningful cross-GameForm GameAction cannot be represented while keeping input/control evidence, semantic action, execution and consequence distinct.

## ACS-PRC-2 — Control locus/mapping failure

A real control form cannot be represented through ControlMapping + ControlLocus + ordinary GameStructure/authority relations without inventing an unmodeled primitive.

## ACS-PRC-3 — SkillProfile failure

A legitimate learned Game capability cannot be represented as a scoped conditional profile over relevant variables/history/probes without losing a repeated causal distinction.

## ACS-PRC-4 — Skill relevance failure

Repeated skill phenomena require relevance that cannot be expressed through current GameStructure, evaluative commitments, causal/evidence provenance and attribution relations.

## ACS-PRC-5 — Transformation failure

Retention/transfer/remap/perturbation claims repeatedly require a relation not expressible as exact changed/held-fixed ProbeTransformation dimensions.

## ACS-PRC-6 — Structural body/tool coupling failure

A body/tool/avatar/vehicle case changes Game action possibility or authoritative consequence in a way that cannot be represented through existing entities/relations plus ControlMapping, ControlLocus and derived ActionCoupling relations.

## ACS-PRC-7 — Attribution failure

Shared/delegated/assisted/synthetic control repeatedly produces capability claims that cannot be correctly attributed to Human/System/Joint targets using current identity/control relations.

## ACS-PRC-8 — Repeated downstream contradiction

At least two materially different downstream GameForms repeatedly falsify the same frozen ACS law rather than merely a derived view or local measurement choice.

A new controller, genre, model, avatar system, accessibility feature or Agent architecture is not itself a reopen condition.

---

# 13. R29 / GDF0 audit

GDF1-A→F stressed the existing foundations with:

```text
continuous and discrete control
symbolic/strategic skill
motor learning
remapping/accessibility
shared assistance
remote control
tool/vehicle mediation
body-scaled reachability
VR/avatar ownership dissociations
synthetic controllers
open sandbox evaluation
community/practice overlays
```

No case requires a new semantic coordinate beyond F1–F9.
No frozen GDF0 Play/Game law was contradicted.

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 PRC-7 = NOT TRIGGERED
```

---

# 14. Freeze verdict

```text
GDF1-A→F = COMPLETE

Action / Control / Skill Foundations v1 = FROZEN

Frozen core responsibilities = 6

GameActionContract
ControlMapping
ControlLocus
SkillProfile
SkillRelevantVariableSet
ProbeTransformation

Embodiment as one Game construct = REJECTED
TechniqueFamily = derived only
ActionCouplingProfile = derived only
Challenge/floor/ceiling/mastery constructs = handed to GDF2
Human motor/ownership/agency mechanisms = handed to Human
Avatar/body representation details = handed to Media

R1–R29/F1–F9 = unchanged
Play/Game Deep Foundations v1 = unchanged

next deep branch = GDF2 Challenge / Difficulty / Failure / Mastery
```
