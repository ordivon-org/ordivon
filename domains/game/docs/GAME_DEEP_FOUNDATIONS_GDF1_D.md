---
schema_version: 1
id: game.deep-foundations.gdf1-d
title: Ordivon Game Deep Foundations — GDF1-D Cross-GameForm Skill / Control Falsification
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Cross-GameForm falsification of the GDF1-C minimal skill/control model across motor-heavy, symbolic/strategic, open sandbox, accessibility, shared-control and synthetic forms. SkillProfile and ProbeTransformation survive; TechniqueFamily is demoted to optional derived structure; fixed EvaluationTargetSet fails under participant-authored/evolving sandbox goals and is reconstructed as time/provenance-bound EvaluationCommitmentSet; skill-floor/expression relations survive; SaturationBoundary requires causal attribution; embodiment remains non-universal but earns a dedicated next round because it can alter reachability/sensing/dynamics structurally.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf1-c
  - game.play-game-deep-foundations.v1
---
# Ordivon Game Deep Foundations — GDF1-D

## 0. D's job

C built a compact Skill/Control contract.

D tries to break it by moving far away from the motor-heavy cases that motivated GDF1:

```text
precision platforming
fighting
FPS
racing
rhythm
RTS
chess
open sandbox / creative construction
speedrun/community overlays
accessibility remapping
shared assistance
synthetic controllers
```

The question is not whether C can be made flexible enough to describe everything after the fact.

The question is:

> Which constructs continue to make discriminating claims, which become generic containers, and which fail under new GameForms?

Canonical evidence/probes:

```text
evidence/gdf1-d/cross-gameform-matrix.json
evidence/gdf1-d/cross-gameform-falsifiers.json
scripts/gdf1-d/cross-gameform-falsifiers.mjs
scripts/gdf1-d/audit-cross-gameform.mjs
```

---

# 1. SkillProfile survives the motor → symbolic transition

The strongest falsifier is chess.

A chess expert may make the same trivial physical mouse movement as a novice while being dramatically better at:

```text
recognizing domain-specific patterns
detecting relevant regions
candidate move generation/evaluation
search allocation
state evaluation
```

Primary chess expertise studies show that expert advantages are strongly domain-specific and can appear in early visual relevance/pattern processing rather than general visual superiority.

Therefore GDF1 cannot define Skill around motor telemetry.

But C's abstract form survives:

```text
SkillProfile
= conditional learned capability over TaskRelevantVariables
```

provided `TaskRelevantVariables` may include:

```text
perceptual
informational
strategic/policy
motor
social/coordination
```

variables.

Strong result:

```text
SkillProfile is broader than MotorSkillProfile.
```

GDF1 remains Action/Control/Skill/Embodiment research, not merely movement science.

---

# 2. Chess also kills `TechniqueFamily` as a mandatory Skill component

We can sometimes identify chess motifs, openings, endgame techniques or search heuristics.

But no clean recurrent motor/policy organization must be present for every legitimate chess Skill claim.

Thus C's warning becomes stronger:

```text
TechniqueFamily != necessary constituent of SkillProfile.
```

D disposition:

```text
TechniqueFamily
→ DEMOTE to optional derived explanatory view.
```

It remains useful where participants/practices actually stabilize recognizable organizations:

```text
racing cornering
fighting execution routes
sports strokes
speedrun movement
```

but should not be frozen into the minimal Skill core.

---

# 3. RTS preserves SkillProfile but changes what `control` means

StarCraft-like RTS games are a direct falsifier of:

```text
PlayerAction = low-level movement trajectory.
```

The player may:

```text
select squad
choose target
issue attack order
```

while:

```text
pathfinding
local unit movement
collision avoidance
some targeting behavior
```

are executed by game systems/unit controllers.

Yet the high-level order is still the player's GameAction.

RTS training/expertise studies also show relevance in multi-source switching, attention and gaze allocation, not merely click speed.

Therefore C's `ControlContributionTopology` survives, but D compresses its responsibility:

> Track only contributions at Game/value-relevant control variables, layers and authority boundaries; do not model every micro-causal actuator step.

Strong law:

```text
DelegatedExecution != LossOfPlayerGameAction.
```

---

# 4. Cross-GameForm evidence supports domain-specific relevance, not generic expertise metrics

Chess experts detect task-relevant board information earlier than novices.

RTS experts/training show domain demands involving gaze control, switching and coordination over multiple information/action sources.

FPS experts show motor-acuity/kinematic differences whose form changes with target/task demands.

These are not three instances of one universal telemetry metric.

They support C's deeper principle:

```text
Skill evidence must be conditioned on the Game's current relevance/evaluation structure.
```

But D now finds that C's `EvaluationTargetSet` is still too static.

---

# 5. Open sandbox breaks the fixed EvaluationTargetSet

Consider an open construction episode.

At time t0 the participant adopts:

```text
build a weather-safe shelter
```

Relevant variables include:

```text
resource cost
closure/protection
construction time
```

At time t1 the same participant abandons that project and adopts:

```text
turn the structure into a sculpture
```

Now relevant variables can become:

```text
shape control
visual composition
material expression
```

No base Game rule changed.

No designer had to assign a new global goal.

Yet the participant's current Skill-relevant evaluation changed.

Therefore C's static:

```text
EvaluationTargetSet
```

fails as the general contract.

---

# 6. Reconstruction: EvaluationCommitmentSet

D replaces it with:

# **EvaluationCommitmentSet**

A time/provenance-bound set of currently operative evaluative commitments relevant to the skill claim.

Possible sources:

```text
formal Game goal / score
participant-authored project/goal
community-constitutive category
team/social commitment
institutional task brief
researcher-declared measurement target
PlayerValue hypothesis
```

Each commitment must record at least:

```text
source/principal
scope
time/currentness
provenance
target/relation
status: authoritative / adopted / hypothesized / negotiated etc.
```

Strong law:

```text
EvaluationCommitment != UniversalPlayerValue.
```

A current participant project can make variables locally relevant without proving a stable preference or category essence.

---

# 7. This fixes sandbox without reopening GDF0

GDF0 already established:

```text
NoFixedGlobalGoal != NoEvaluation
```

and allowed participant-authored/local evaluation.

D therefore does not discover a contradiction.

It simply gives GDF1 a better consumption contract:

```text
GameStructure
+ current EvaluationCommitmentSet
+ ControlContributionTopology
→ candidate SkillRelevantVariables
```

The relevant set can change over time as commitments change.

Thus:

```text
SkillRelevantVariableSet(t)
```

is permitted to be dynamic.

---

# 8. `TaskRelevantVariableSet` should therefore become less task-centric in name

Chess, RTS, sandbox expression and social/team commitments expose another problem with the label `TaskRelevantVariableSet`.

`Task` can misleadingly suggest a fixed externally assigned objective.

D therefore recommends the reconstruction:

# **SkillRelevantVariableSet (SRVS)**

Definition:

> variables whose variation is causally/evaluatively relevant to the current SkillScopeSpec under the current GameStructure, EvaluationCommitmentSet and ControlContributionTopology.

This is not a new semantic primitive.

It is the more general name for C's admission logic.

`TaskRelevantVariableSet` remains a convenient subtype when the skill claim genuinely concerns a fixed task.

---

# 9. Participant-authored relevance remains authority/provenance bound

D does **not** mean:

```text
player says anything
→ it becomes authoritative Game truth.
```

A participant can adopt:

```text
"I will build this without using stone"
```

as a self-imposed evaluative/constraint commitment.

That can become relevant to **that participant's current skill claim/practice**.

It does not automatically mutate:

```text
official rules
community category
other players' commitments
```

GDF0 RuleAuthority and ConstitutiveOverlay distinctions remain binding.

---

# 10. Speedrunning shows why SkillScope needs rule/category provenance

Speedrun skill is not defined only by the base executable.

The relevant practice may depend on:

```text
Any%
Glitchless
No Major Glitches
specific patch/version
community timing rules
allowed input methods
```

These overlays change what counts as valid performance and which techniques matter.

Thus `SkillScopeSpec` survives D strongly, but its purpose becomes clearer:

```text
it is research/evidence metadata,
not a metaphysical Skill object.
```

For practice-defined skill, scope must bind the effective rules/category lineage under study.

---

# 11. SkillScopeSpec survives, but is compressed

D found no case where a serious cross-player/cross-condition Skill claim can safely omit scope.

But treating SkillScopeSpec as a rich domain entity would be over-formalization.

Disposition:

```text
SkillScopeSpec
→ RETAIN as evidence contract / metadata boundary.
```

Its irreducible questions are only:

```text
who/what is attributed capability?
what practice/task family?
under which Game/control/evaluation configuration?
across which transformation/history claim?
```

Everything else should remain owner-local data.

---

# 12. Remapping splits into three materially different transformations

D's executable probe distinguishes:

## Access-only remap

Changed:

```text
physical input channel
```

Held approximately fixed:

```text
GameAction semantics
timing
information
world dynamics
```

Likely interpretation:

```text
higher-order Game skill mostly preserved;
access boundary changes.
```

## Expression remap

Changed:

```text
effector
gain
control transfer function
```

Interpretation:

```text
higher-order skill may transfer,
but low-level recalibration/execution skill changes.
```

## Skill-family-changing transformation

Changed together:

```text
action vocabulary
observation
timing
dynamics
```

Now the old SkillScope may no longer be the right claim.

Therefore:

```text
Remap != one transformation class.
```

`ProbeTransformation` survives D as one of C's strongest constructs.

---

# 13. Skill floor survives only as a relational EntryRequirementRegion

Across platforming, rhythm, accessibility and assistance, the intuition remains valid:

> some capability region is needed before a participant can produce a declared viable/evaluated result.

But D further rejects scalar language.

A threshold can require a vector such as:

```text
minimum timing tolerance
+ minimum action access
+ minimum recognition capability
```

with compensations/tradeoffs.

So `EntryRequirementSet` survives better as:

# **EntryRequirementRegion**

in SkillProfile space.

It remains:

```text
configuration-relative
evaluation-relative
participant/access-relative
```

not an intrinsic number belonging to a game title.

---

# 14. ExpressionEnvelope survives strategic skill too

`Capability != Expression` is not only a motor phenomenon.

A chess expert facing trivial positions cannot express much of their deeper search/evaluation capability.

An RTS expert against a static low-pressure opponent may not need multi-front switching.

An FPS expert in a coarse aim-assist mode may not express fine motor acuity.

Thus:

```text
SkillExpressionEnvelope
```

survives cross-GameForm.

It is one of C's strongest derived relations.

---

# 15. But `SaturationBoundary` was underspecified

Suppose expert scores plateau.

C called this a possible saturation boundary.

D asks:

> saturation caused by what?

The same observed plateau can be produced by:

```text
Game/action-resolution cap
measurement rounding/censoring
opponents/tasks too easy
population sample lacking stronger players
assistance suppressing differences
```

Therefore:

```text
ObservedPlateau != GameSkillCeiling.
```

D reconstructs the term:

# **SaturationBoundary + SaturationAttribution**

A ceiling claim must state which part of the system is believed to be saturating and what intervention would distinguish alternative causes.

---

# 16. TechniqueFamily survives only as derived practice analysis

D's corpus produces a clean split.

Useful:

```text
racing cornering families
fighting execution/spacing routes
speedrun movement techniques
sports strokes
```

Not required:

```text
chess expertise
some RTS strategic control
open sandbox creative practice
synthetic continuous policies
```

Therefore no later GDF1 freeze should require:

```text
SkillProfile → TechniqueFamily
```

as a mandatory relation.

TechniqueFamily remains optional and must earn its invariants empirically/practice-historically.

---

# 17. `ControlContributionTopology` survives RTS and assistance — if bounded

There was a risk that this construct would explode into workflow ontology.

D finds a compression rule:

> model only contributions that change attribution, authority, action availability, task/value-relevant control variables or learning/skill exposure.

Do not model every implementation microstep.

So in RTS:

```text
Player order selection
Pathfinder movement realization
Unit local control
Game admission/damage resolution
```

are relevant because they determine which capability is attributed to whom.

But internal low-level pathfinding arithmetic does not belong in the Game skill model unless it changes one of those boundaries.

Thus `ControlContributionTopology` survives as a **sparse attribution/control boundary graph**.

---

# 18. Synthetic controllers strengthen the abstraction boundary

A synthetic controller can have a meaningful SkillProfile over:

```text
policy quality
perturbation response
transfer
stabilization
strategy
```

without human motor physiology.

This confirms that SkillProfile is structurally broader than Human Motor Skill.

But GDF0/GDF1 guards remain:

```text
SyntheticSkillProfile
!= HumanMotorMechanism
!= SenseOfAgency
!= EmbodimentExperience
!= PlayExperience.
```

No phenomenology is imported.

---

# 19. Embodiment finally produces a real split

D asked whether embodiment belongs in the minimal core.

Cross-GameForm answer:

```text
NO as universal requirement.
```

Chess and many symbolic/RTS skill claims do not require body morphology or body ownership to define the core capability target.

But other forms provide the opposite pressure.

In:

```text
VR climbing
sports
motion control
body-scaled reachability
accessibility mappings
tool/vehicle coupling
```

body morphology / sensing / effector constraints can change:

```text
which actions are reachable
what information is available
control dynamics
vulnerability/collision
energy/timing constraints
```

That is **structural**, not merely experiential.

Therefore embodiment cannot simply be handed off to Human and forgotten.

---

# 20. D verdict: embodiment earns GDF1-E

The correct conclusion is not:

```text
Embodiment = core of all Skill.
```

Nor:

```text
Embodiment = only subjective VR presence.
```

Instead:

> embodiment is a conditional structural coupling whose necessity and role vary by GameForm.

This is important enough to deserve a dedicated falsification round.

Thus next frontier is earned rather than preplanned:

# **GDF1-E — Embodiment / Body / Tool / Avatar Structural Falsification**

---

# 21. Cross-GameForm verdicts on C constructs

```text
SkillScopeSpec
→ RETAIN, compress to research/evidence scope contract.

EvaluationTargetSet
→ FAILS generality.
→ REPLACE with EvaluationCommitmentSet.

TaskRelevantVariableSet
→ RECONSTRUCT as SkillRelevantVariableSet;
  task-specific version remains subtype.

ProbeTransformation
→ STRONGLY RETAIN.

SkillProfile
→ STRONGLY RETAIN.

TechniqueFamily
→ DEMOTE to optional derived view.

ControlContributionTopology
→ RETAIN as sparse attribution/control boundary graph.

EntryRequirementSet
→ RETAIN/rename conceptually to EntryRequirementRegion.

SkillExpressionEnvelope
→ RETAIN.

SaturationBoundary
→ RETAIN only with SaturationAttribution.

ControlAccessProfile
→ RETAIN derived.

Embodiment
→ NOT universal core;
  dedicated next falsification round required.
```

This is substantial compression/reconstruction, not simple confirmation of C.

---

# 22. Strongest new D laws

## D-A — Evaluation Commitment Currentness

```text
Skill relevance can change when participant/social/formal evaluative commitments change,
even without a base Game rule mutation.
```

## D-B — Symbolic Skill Generality

```text
SkillProfile does not require motor telemetry;
it requires scope-bound task/value-relevant capability evidence.
```

## D-C — Delegated Execution Separation

```text
PlayerGameAction != low-level executor trajectory.
```

## D-D — Saturation Attribution

```text
ObservedPerformancePlateau != SkillCeiling
without identifying the saturating mechanism/boundary.
```

## D-E — Conditional Embodiment

```text
Embodiment is not necessary for all Game Skill,
but body/tool coupling can become structurally constitutive when it changes
reachability, sensing, control dynamics or consequence.
```

All are N1 synthesis/reconstruction candidates.

---

# 23. External evidence pressure emphasized in D

Chess expertise work reports domain-specific expert advantages in object/pattern processing and rapid detection of relevant board information, directly supporting non-motor SkillProfile variables.

RTS training/expertise research uses StarCraft as a high-workload multi-source control environment and reports changes/differences in cognitive flexibility, attended information and gaze control.

FPS expertise research shows that kinematic signatures depend on task demands and that one standard speed-accuracy law does not fully characterize combined performance.

Minecraft Education research describes the sandbox form as lacking a predetermined global goal and records users emphasizing freedom to create; D uses this only as pressure for participant-authored/evolving evaluation, not as proof of a universal creativity mechanism.

Rhythm-game training provides the complementary narrow case: a Game may intentionally make temporal synchronization the dominant controlled/evaluated variable and adapt challenge around performance.

Together these cases strongly reject a motor-only or fixed-task-only Skill model.

---

# 24. Discovery ledger after D

## N0 external pressure

```text
chess expertise is domain-specific and includes early relevance/pattern-processing advantages;
RTS skill/training involves multi-source switching/gaze/information control;
FPS motor metrics vary with task demand and are not fully summarized by one law;
open sandbox can support participant-directed creation without predetermined global goal;
rhythm-game skill can make narrow temporal synchronization an explicit adaptive target.
```

## N1 reconstructed candidates

```text
D-A EvaluationCommitmentSet
D-B SkillRelevantVariableSet
D-C SkillScope as evidence contract rather than ontology object
D-D Sparse ControlContributionTopology
D-E SaturationAttribution
D-F Conditional Embodiment
```

Strengthened:

```text
SkillProfile
ProbeTransformation
ControlAccessProfile
EntryRequirementRegion
SkillExpressionEnvelope
Human/System/Joint attribution
```

Demoted:

```text
TechniqueFamily → optional derived view
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

# 25. Foundation reopen audit

The most important D failure—fixed EvaluationTargetSet—does not contradict GDF0.

GDF0 already permits:

```text
participant-authored/dynamic/local evaluation
NoFixedGlobalGoal != NoEvaluation
practice/community overlays
```

Likewise symbolic Skill uses existing F7/F8/F9 coordinates rather than requiring a new primitive.

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 PRC-7 = NOT TRIGGERED
```

D has falsified a **GDF1-C derived measurement contract**, exactly as the freeze architecture was intended to allow.

---

# 26. Exact next frontier: GDF1-E

# **GDF1-E — Embodiment / Body / Tool / Avatar Structural Falsification**

E should now separate and attack:

```text
biological body
morphology
sensor/effector envelope
body schema / body representation
input effector
controlled tool/vehicle
avatar
control locus
self-location
ownership
sense of agency
vulnerability/collision body
action reachability
energy/inertia/dynamics
```

Across:

```text
traditional controller games
VR full-body interaction
sports/racing/tool use
motion control
accessibility remapping
vehicle embodiment
remote/teleoperation
body-swap/avatar scaling
synthetic/non-bodied controller
```

The decisive question is:

> Which embodiment variables belong to Game's structural action/control contract because changing them changes reachable causal possibility, and which remain Human-side phenomenology/perception mechanisms consumed through an interface?

Only after E should GDF1 begin final compression/freeze planning.
