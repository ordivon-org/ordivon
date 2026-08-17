---
schema_version: 1
id: game.deep-foundations.gdf1-c
title: Ordivon Game Deep Foundations — GDF1-C Skill / Control Minimal Reconstruction
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Reconstructs the smallest Game-owned skill/control measurement contract after GDF1-A/B falsification. Makes SkillProfile explicitly scope-bound and non-scalar; derives task-relevant variables from declared GameStructure/evaluation/control relevance before expert telemetry; represents transfer as exact task/configuration transformation; separates Human, system and joint-controller capability; and replaces intrinsic scalar skill-floor/ceiling language with configuration-relative entry requirement, expression envelope and saturation boundary.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf1-a
  - game.deep-foundations.gdf1-b
  - game.play-game-deep-foundations.v1
---
# Ordivon Game Deep Foundations — GDF1-C

## 0. The problem B left us

B removed several bad identities:

```text
Performance != Skill
PracticePerformance != Learning
GlobalLowVariability != Skill
ManualCommandShare != Agency
Technique != exact trajectory
```

But `SkillProfile` could still become an arbitrary bag of metrics.

C therefore asks:

> What is the **minimum Game-owned contract** required to make a Skill claim operational, falsifiable and correctly attributed without choosing one Human motor theory?

Canonical model/probes:

```text
evidence/gdf1-c/minimal-skill-control-model.json
evidence/gdf1-c/capability-surface-probes.json
scripts/gdf1-c/capability-surface-probes.mjs
scripts/gdf1-c/audit-minimal-model.mjs
```

---

# 1. First reconstruction — there is no context-free `Skill`

A statement such as:

```text
Alice has more skill than Bob.
```

is incomplete unless it declares at least:

```text
whose capability?
which task family?
which mapping/control configuration?
which evaluation/value target?
which condition/probe space?
which history/timescale?
```

C therefore introduces the first minimal contract:

# C1 — SkillScopeSpec

```text
SkillScopeSpec =
AttributionTarget
× TaskFamily
× ControlConfigurationSet
× EvaluationTargetSet
× ProbeTransformationSet
```

This is not a new R29 primitive.

It is an evidence/measurement contract over existing identity, state, relation, evaluation, action/control and history coordinates.

Strong guard:

```text
UnscopedSkillClaim = incomplete claim.
```

---

# 2. SkillProfile is a surface, not a hidden number

B's working definition now becomes operational:

> **SkillProfile is a learned, history-dependent conditional capability profile over one declared SkillScopeSpec, inferred from distributions of task-relevant performance under the declared conditions/probes.**

Formal sketch:

```text
P(
  TaskRelevantVariable outcomes
  |
  subject/controller history,
  TaskFamily,
  ControlConfiguration,
  ProbeTransformation
)
```

This does **not** mean the brain stores a probability table.

It means Ordivon refuses to infer a general capability from one sample without declaring the transformation space over which the claim should hold.

---

# 3. C attacks hidden scalarization with a Pareto-style counterexample

The executable probe defines two synthetic profiles.

## Peak specialist

```text
base condition:
  excellent

perturbation/remap/retention:
  weak
```

## Robust generalist

```text
base condition:
  slightly lower peak

perturbation/remap/retention:
  much stronger
```

Across the declared multi-condition profile:

```text
PeakSpecialist does not dominate RobustGeneralist
RobustGeneralist does not dominate PeakSpecialist
```

Therefore:

```text
SkillProfile_A
and
SkillProfile_B
can be incomparable
without an explicit value/weighting rule.
```

This is not a claim that Pareto ordering is the final theory of skill.

It is an anti-collapse guard:

```text
no hidden weighting → no honest universal scalar ranking.
```

---

# 4. The hardest problem: which variables should count as skill-relevant?

If we simply observe experts and then select whatever telemetry separates them, we create a circular theory:

```text
expert = person with expert-like metrics
```

C therefore requires **pre-telemetry structural admission**.

# C6 — TaskRelevantVariableSet

A variable is admitted into the candidate TaskRelevantVariableSet when:

```text
1. it has explicit observation/derivation provenance;
2. under the current GameStructure it has an authoritative causal path
   to a declared EvaluationTarget,
   or it is directly declared as the evaluated control/expression target;
3. it lies within the influence/exposure surface of the subject/controller
   whose skill is being evaluated;
4. expert telemetry may validate usefulness but may not create relevance post hoc.
```

This is the first serious answer to B's largest unresolved question.

---

# 5. EvaluationTargetSet prevents `score` from owning Skill

The declared target can be:

```text
formal Game goal/evaluation
local task objective
explicit PlayerValue hypothesis
research/measurement target
```

but these must not silently substitute for one another.

Suppose a toy aiming Game has causal structure:

```text
endpointError → hitQuality → formalScore
completionTime → formalScore
animationStylePhase → styleValue
```

If the skill question is:

```text
formal competitive performance
```

then `animationStylePhase` is not admitted merely because experts happen to move stylishly.

If the declared PlayerValue question becomes:

```text
expressive movement style
```

then the relevant set legitimately changes.

The executable probe derives both sets **without changing expert telemetry at all**.

Therefore:

```text
TaskRelevantVariableSet
is EvaluationTarget-relative.
```

---

# 6. This does not allow designers to declare PlayerValue true by fiat

A critical boundary:

```text
DeclaredPlayerValueHypothesis
!= EmpiricallyEstablishedPlayerValue.
```

The structural model can say:

> if expressive movement is the value target, these variables are causally capable of carrying that distinction.

It cannot say:

> players actually value expressive movement.

That still requires Human/player evidence.

Thus:

```text
Game derives candidate causal/value-bearing variables;
Human/player research validates whether the hypothesized value is real.
```

This preserves GDF0's owner boundary.

---

# 7. Task relevance is not the same as movement relevance

The UCM/optimal-feedback pressure from B now has a formal place.

A movement dimension can have high physical variance and still lie largely in a task-equivalent/null direction.

Conversely a very small temporal variation can be highly relevant if it changes:

```text
parry success
rhythm grade
race exit state
shot hit
```

Nisky, Hsieh & Okamura's robotic-teleoperation study is particularly useful: experienced surgeons and novices differed in how joint-angle variability was structured relative to task-relevant versus task-irrelevant manifolds, and teleoperation affected experts and novices differently.

C's inference is narrow:

```text
Interface/configuration can change how a capability is expressed,
and skill-relevant variability must be defined relative to task variables,
not total movement variability.
```

---

# 8. Transfer cannot remain a word like `near` or `far`

When someone says:

```text
this skill transferred
```

C asks:

> What exactly changed?

Introduce:

# C8 — ProbeTransformation

A transfer/perturbation probe records explicit changed and held-fixed dimensions such as:

```text
input mapping
control gains
dynamics
world physics
timing/speed
observation/information
action semantics
evaluation target
assistance topology
task content
```

Then transfer evidence means:

```text
capability survived or adapted across this exact transformation.
```

Not:

```text
some vaguely related task looked similar.
```

Strong guard:

```text
TransferEvidence requires TransformationIdentity.
```

---

# 9. Same GameAction × different mapping

C's first matched transformation keeps:

```text
GameAction semantics = AIM / FIRE
formal evaluation = fixed
```

and changes only:

```text
mouse delta
→ adaptive-stick deflection
```

The normalized GameActions are identical.

Therefore:

```text
GameAction identity is preserved.
```

Yet access and immediate performance can change because the bodily/control mapping changed.

Thompson, Loke & Argall's assistive-teleoperation work provides real pressure: customized control-interface remapping based on user-specific bias profiles improved reachability of device control space in their six-participant evaluation, especially for users with more restricted reachable control space.

Thus C retains:

# D4 — ControlAccessProfile

```text
which GameAction/control distinctions are actually reachable
for this subject under this mapping/configuration.
```

And:

```text
ControlAccess != GameActionSemantics.
```

---

# 10. Does remapping create a new Skill?

Not automatically.

C distinguishes three possibilities.

## Access-only change

The new mapping exposes the same task-relevant distinctions with little additional learning burden.

## Expression remapping

The same higher-order SkillProfile can remain relevant, but mapping-specific execution requires recalibration/new low-level capability.

## Material task-family change

The mapping alters timing, information, reachable actions or action dynamics so substantially that the original SkillScopeSpec no longer covers the new task without revision.

Therefore:

```text
Same GameAction
!= necessarily Same MotorSkill
```

but also:

```text
Different Controller
!= necessarily Different GameSkill.
```

C needs D/cross-GameForm pressure before freezing the boundary.

---

# 11. Shared control requires contribution topology, not `70% human`

A scalar `percent manual control` loses too much information.

Consider racing assistance:

```text
Human:
  selects line / steering intention / braking strategy

Assist system:
  filters unstable steering
  corrects slip
  clips unsafe command

Game/system:
  admits action and resolves vehicle dynamics
```

These are different variables and layers.

Introduce:

# C4 — ControlContributionTopology

Each contribution names:

```text
controller
controlled variable/layer
time scope
contribution kind
authority scope
```

Possible contribution kinds:

```text
proposal
selection
filter
correction
stabilization
execution
admission
override
```

Therefore:

```text
SharedControl != weighted average of controllers.
```

---

# 12. Human skill, system skill and joint-controller skill must separate

C makes the attribution target explicit.

```text
HumanIndependentSkillProfile
SystemCapabilityProfile
JointControllerSkillProfile
```

are different claims.

The executable probe holds the Human-independent profile fixed while an assist system raises immediate joint task performance.

Therefore:

```text
JointControllerPerformance ↑
```

cannot by itself imply:

```text
HumanIndependentSkill ↑
```

This is a structural rule, not a claim that assistance cannot teach.

Indeed, recent shared-autonomy training work goes the other direction: Srivastava et al.'s HRI 2025 study used assistance responses to identify teachable racing subskills and reported improvements in driving time, behavior and smoothness in a 50-participant user study.

The correct conclusion is:

```text
Assistance can execute,
assist access,
expose learning opportunities,
or teach;
which effect occurred must be separately evidenced.
```

---

# 13. Assistance therefore has at least three timescales

B introduced AssistanceTimescaleSeparation.

C makes it operational.

## Immediate execution

```text
Can the joint controller succeed now?
```

## Independent post-assist capability

```text
Can the Human perform after assistance is removed?
```

## Assisted/joint-controller mastery

```text
Can the Human become skilled at using the assistance itself?
```

The third target is frequently overlooked.

A racing driver with ABS/traction control, a player with aim assist, or a surgeon using teleoperation may develop a real skill **of the coupled system** rather than approximating the unassisted skill.

Thus:

```text
AssistedSkill != degraded UnassistedSkill by identity.
```

It may be a distinct SkillScopeSpec.

---

# 14. Teleoperation gives direct evidence for coupled-system skill

Nisky et al. compared experienced surgeons and novices under freehand and robotic teleoperation.

Their UCM analysis found expertise-dependent differences in stabilization structure, and the effect of teleoperation itself depended on expertise.

That is important because it rejects a simple model:

```text
interface = transparent channel
skill = unchanged latent property merely revealed through it.
```

Instead:

```text
SkillExpression = f(SkillProfile, Mapping/Tool/ControlConfiguration, Task)
```

and expertise may include skill in exploiting the tool/control system itself.

---

# 15. Skill floor is not a Game constant

The usual phrase:

```text
this Game has a high skill floor
```

compresses multiple relations.

C replaces it with:

# D1 — EntryRequirementSet

> the minimum region of SkillProfile capability required to satisfy a declared viability/evaluation threshold under one exact Game/control configuration.

Formally:

```text
EntryRequirementSet(
  TaskFamily,
  EvaluationThreshold,
  Mapping,
  Assistance,
  Condition
)
```

The executable probe keeps one threshold fixed while changing:

```text
manual mapping
remapped access
shared assistance
```

and changes whether the same nominal capability can cross that threshold.

Therefore:

```text
SkillFloor != intrinsic scalar Game property.
```

Guadagnoli & Lee's Challenge Point framework gives broader motor-learning pressure in the same direction: the functional difficulty of a task depends on performer skill and practice conditions, not only nominal task properties.

---

# 16. Skill ceiling also needs reconstruction

`Skill ceiling` often mixes:

```text
maximum possible performance
maximum human capability
maximum distinguishable player difference
maximum rewarded difference
```

These are not the same.

C introduces two derived relations.

# D2 — SkillExpressionEnvelope

```text
range of evaluation/task differences that changes in the target subject's
SkillProfile can causally express under the current Game/control configuration.
```

# D3 — SaturationBoundary

```text
region where further improvement on a declared capability dimension
no longer produces distinguishable change in the declared evaluation/value targets.
```

The executable probe compares two otherwise similar control surfaces:

```text
coarse action resolution
→ capability improvements saturate early

fine action resolution
→ further capability remains behaviorally/evaluatively expressible
```

Therefore:

```text
SkillCeiling != maximum human skill.
```

It is shorthand for a configuration- and target-relative expression/saturation relation.

---

# 17. This makes `skill expression` a first-class distinction

A player may have latent capability that the current Game cannot expose because:

```text
automation removes the relevant distinction
input mapping blocks access
action resolution is too coarse
task never probes the skill
evaluation saturates
opponent/environment is too easy
```

Therefore:

```text
Capability != Expression.
```

This will become central in GDF2 Challenge/Mastery later.

A Game can have:

```text
high capability requirements but poor expression above threshold
```

or:

```text
low entry requirements but a broad expression envelope.
```

So `easy to learn, hard to master` should eventually be decomposed rather than treated as one slogan.

---

# 18. TechniqueFamily receives its first operational definition

B showed that technique cannot be one frozen motor sequence.

C defines:

# C10 — TechniqueFamily

> a derived family of recurrent policy/execution organizations sharing declared functional invariants while permitting parameterization, mapping-specific realization and online correction.

Possible invariants include:

```text
action ordering relation
controlled task variable
role/goal relation
coordination relation
decision/transition grammar
```

The executable racing probe keeps the family:

```text
brake before apex
steer through apex
accelerate on exit
```

while changing:

```text
brake lead time
steering rate
throttle resume timing
```

under faster dynamics.

Thus:

```text
TechniqueFamily can persist while exact timing/trajectory changes.
```

---

# 19. Technique is optional explanatory structure, not Skill ontology

Some skills may have strongly named technique families:

```text
fighting combo routes
racing cornering methods
sports strokes
speedrun movement techniques
```

Others may be better described through:

```text
continuous policy adaptation
perception-action coupling
strategic selection
```

without clean technique categories.

Therefore:

```text
TechniqueFamily != mandatory component of every SkillProfile.
```

It is a derived explanatory view when recurrent organization earns it.

---

# 20. C's minimal Game-owned architecture

After compression:

```text
              GAME STRUCTURE / EVALUATION
                       │
                       ▼
             EvaluationTargetSet
                       │
       authoritative causal relevance
                       ▼
            TaskRelevantVariableSet
                       ▲
                       │
                 GameActionContract
                       ▲
                       │
Input → ControlMapping → ActionAttempt
                       │
             ControlContributionTopology
               ↙        ↓        ↘
            Human     System     Joint
                       │
                       ▼
              GameAction / Execution
                       │
                       ▼
                 PerformanceSample
                       │
            exact condition/provenance
                       │
                       ▼
               ProbeTransformation
                       │
              history across probes
                       ▼
                    SkillProfile
```

`TechniqueFamily`, `EntryRequirementSet`, `ExpressionEnvelope` and `SaturationBoundary` are derived views over this contract.

This is much smaller than importing an entire motor-neuroscience ontology into Game.

---

# 21. Strong anti-collapse laws after C

```text
SkillClaim -> explicit SkillScopeSpec.

PerformanceSample != SkillProfile.

TaskRelevantVariableSet
!= whatever happens to correlate with experts.

JointControllerPerformance
!= HumanIndependentSkillProfile.

ControlAccess
!= GameActionSemantics.

SkillFloor
!= intrinsic Game constant.

SkillCeiling
!= universal scalar maximum.

Capability
!= SkillExpression.

TechniqueFamily
!= exact trajectory.

TransferEvidence
requires exact ProbeTransformation.

SkillProfile comparisons
can remain incomparable without declared weighting.
```

---

# 22. C does not solve PlayerValue by declaration

One possible failure mode is now visible.

Because TaskRelevantVariableSet consumes `EvaluationTargetSet`, a designer could declare:

```text
Our PlayerValue is pixel-perfect animation style.
```

and generate a structurally valid Skill model.

That does not make the premise true.

Therefore future Game research must maintain:

```text
Structural Skill Model
×
Empirical PlayerValue Evidence
```

as separate evidence streams.

A valid skill architecture can still be built around the wrong value target.

---

# 23. Challenge is already peeking through, but C does not absorb GDF2

Guadagnoli & Lee's Challenge Point framework explicitly relates practice difficulty to performer skill and task conditions.

This strongly suggests that later Challenge research must treat difficulty as relational:

```text
Task × PlayerCapability × Condition
```

rather than a scalar property of content.

But C stops here.

It only establishes the Skill side of that future relation:

```text
SkillProfile
+ EntryRequirement/Expression relations.
```

GDF2 will own Challenge/Difficulty/Failure/Mastery.

---

# 24. External pressure added in C

## 24.1 Challenge Point

Guadagnoli & Lee (2004) model functional task difficulty as depending on performer skill and task/practice conditions.

GDF1 use:

```text
skill floor / task difficulty cannot be context-free intrinsic scalars.
```

## 24.2 Teleoperation × expertise

Nisky, Hsieh & Okamura (2014) show experienced surgeons and novices structure task-relevant/task-irrelevant joint variability differently and respond differently to robotic teleoperation.

GDF1 use:

```text
interface configuration can alter skill expression and experts can possess tool/coupled-system-specific coordination.
```

## 24.3 Personalized remapping

Thompson, Loke & Argall (2022) evaluate customized control-space remapping for six users with upper-limb motor impairment and report improved reachability, especially for users with more limited control-space reach.

GDF1 use:

```text
ControlAccess is mapping/actor relative while GameAction semantics can remain stable.
```

## 24.4 Shared autonomy as teaching

Srivastava et al. (HRI 2025) use shared autonomy to identify and target interpretable racing subskills; their 50-participant CARLA study reports improvements in driving time, behavior and smoothness.

GDF1 use:

```text
assistance may be part of a learning/curriculum system rather than only substituting execution;
human, assist and joint capability attribution must remain explicit.
```

---

# 25. Discovery ledger after C

## N0 — external pressure

```text
functional task difficulty depends on performer skill/task/practice condition;
teleoperation changes task-relevant variability structure in expertise-dependent ways;
personalized control remapping can increase reachable control space;
shared autonomy can be used to target teachable subskills rather than only execute for the user.
```

## N1 — retained/reconstructed Ordivon candidates

```text
C-A SkillScopeSpec
C-B TaskRelevantVariableSet structural admission
C-C ProbeTransformation / transfer identity
C-D SkillProfile as non-scalar conditional capability surface
C-E ControlContributionTopology
C-F Capability/Expression separation
C-G EntryRequirementSet / ExpressionEnvelope / SaturationBoundary reconstruction
C-H TechniqueFamily as invariant + parameterized/online realization family
C-I Controller-specific attribution: Human / System / Joint
```

These are not all intended to freeze as independent ontology terms. D must pressure them cross-GameForm and compress further.

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

C makes skill/control measurement much richer but does not expose a missing R29 coordinate.

Everything remains representable through:

```text
F1 identity/reference
F2 state
F3 relation
F4 transition/constraint
F5 time/history
F6 authority/provenance
F7 observation/representation
F8 evaluation
F9 action/capability/policy/control
```

The frozen GDF0 laws are also strengthened rather than contradicted:

```text
PerformanceEffect != ExperienceEffect
GameAction authority remains separate from representation/input
PlayerValue != formal GameGoal
```

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 PRC-7 = NOT TRIGGERED
```

---

# 27. Exact GDF1-D frontier

C now has a real minimal model worth trying to break.

The next round should **not** yet become embodiment-only, because the new SkillProfile/TRVS/ContributionTopology constructs have only been tested with toy matched transformations plus a few motor domains.

# GDF1-D — Cross-GameForm Skill / Control Falsification

D should attack C across:

```text
precision platforming
fighting game
FPS aiming
racing
rhythm
sports/tool-like control
RTS/indirect command
turn-based symbolic play
accessibility remapping
shared/assistive control
synthetic controller
```

Questions:

```text
1. Does every meaningful Skill claim need SkillScopeSpec, or is C overformalizing obvious cases?
2. Can TaskRelevantVariableSet be structurally derived in open-ended/creative/sandbox skill without circular PlayerValue labels?
3. Does SkillProfile remain useful for strategic/symbolic Skill where motor telemetry is nearly absent?
4. Can TechniqueFamily survive fighting/racing/platforming without becoming arbitrary analyst clustering?
5. Does ControlContributionTopology handle RTS delegation and Agent/shared control without exploding into workflow ontology?
6. Do EntryRequirementSet and ExpressionEnvelope survive real accessibility/assist cases?
7. When does mapping change the skill family versus only expression/access?
8. Does any cross-GameForm case require embodiment to enter the minimal core rather than remain a coupling layer?
```

Only after D should GDF1 decide whether E should be a dedicated Embodiment Falsification round or whether the branch can already begin reconstruction toward freeze.

---

# Primary evidence anchors emphasized in C

- Guadagnoli & Lee (2004), *Challenge point: a framework for conceptualizing the effects of various practice conditions in motor learning*, Journal of Motor Behavior 36(2):212–224, DOI 10.3200/JMBR.36.2.212-224.
- Nisky, Hsieh & Okamura (2014), *Uncontrolled manifold analysis of arm joint angle variability during robotic teleoperation and freehand movement of surgeons and novices*, IEEE Transactions on Biomedical Engineering 61(12):2869–2881, DOI 10.1109/TBME.2014.2332359.
- Thompson, Loke & Argall (2022), *Control Interface Remapping for Bias-Aware Assistive Teleoperation*, arXiv:2205.08489.
- Srivastava et al. (2025), *Shared Autonomy for Proximal Teaching*, ACM/IEEE HRI 2025, arXiv:2502.19899.
