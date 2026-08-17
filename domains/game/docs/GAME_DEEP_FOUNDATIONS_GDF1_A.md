---
schema_version: 1
id: game.deep-foundations.gdf1-a
title: Ordivon Game Deep Foundations — GDF1-A Action / Control / Skill / Embodiment Target Separation
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: First deep round after frozen Play/Game GDF0. Consumes R21 rather than repeating it, decomposes Action below Input→Intent→Action→Outcome into signal/control/action/movement/execution/task-outcome layers, separates Skill from performance/technique/accuracy/precision/timing, separates human body/effector from Game control locus and embodiment experience, and opens a competing-model tournament across predictive/feedback/dynamical/affordance/information-theoretic/agency/shared-control accounts.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.play-game-deep-foundations.v1
  - game.foundations-research.r21
  - game.deep-foundations.gdf0-h
---
# Ordivon Game Deep Foundations — GDF1-A

## 0. Why GDF1 exists if R21 already exists

R21 already established a strong first semantic decomposition:

```text
Intent != Input != Command != Action != Outcome
Control != SenseOfAgency
Avatar != Body
Affordance != Capability != Legality
Latency != Responsiveness
```

GDF1 does not reopen or discard R21.

It asks where R21 is still too compressed for mechanistic research.

Three gaps dominate:

```text
1. Action still conflates semantic act, movement, execution and task result.
2. Skill still risks being replaced by one performance score, accuracy number or repeatability metric.
3. Control/embodiment/affordance remain under-specified under remapping, assistance,
   motor abundance, accessibility and synthetic control.
```

GDF1-A therefore performs **target separation**, not mechanism freeze.

---

# 1. First attack — `Action` is still overloaded

Consider the apparently simple statement:

```text
The player jumped.
```

At least seven different things may be meant:

```text
PlayerIntent
InputSignal
InterpretedCommand / ActionAttempt
ControlSignal trajectory
GameAction identity
Executed movement / state transition
Task/World Outcome
```

These cannot remain one variable.

## 1.1 PlayerIntent

Participant-side intended distinction at the relevant control layer.

Examples:

```text
jump now
turn slightly left
parry high
move squad to cover
keep the car inside the corner exit
```

It is not directly observable by Game code except through evidence/inference.

Human owns the deeper formation of intention; Game owns the interface contract through which relevant intent distinctions can become causally effective.

## 1.2 InputSignal

Observable interface evidence:

```text
key down
stick value
mouse delta
touch trajectory
voice token
gaze event
body pose
BCI classification
```

Input is not yet semantic GameAction.

## 1.3 ControlSignal

A signal used to influence one or more controlled variables after filtering/scaling/interpretation.

Examples:

```text
steering = -0.31
camera angular velocity = +4.2 deg/s
throttle = 0.7
move-vector = (0.4, 0.9)
```

One raw input event may contribute to a continuous control signal; one control signal trajectory may realize one semantic action.

Therefore:

```text
InputSignal != ControlSignal
```

## 1.4 ActionAttempt / Candidate Action

A semantically interpretable attempt submitted to the Game's current action/admission structure.

```text
JUMP
DASH_EAST
PARRY_HIGH
ORDER_SQUAD(HOLD_ZONE)
```

It may still fail admission/execution.

## 1.5 GameAction

A Game-local semantic action identity: the distinction the rules/history treat as an action by a participant/subject.

A GameAction need not correspond one-to-one with human movement.

```text
one GameAction ← many physical mappings
one GameAction ← trajectory of analog signals
one input event → different GameActions in different contexts
```

## 1.6 Movement / Execution Trajectory

The spatiotemporal realization of action through player body, controlled locus, avatar, vehicle, cursor or other executor.

A movement trajectory can be highly variable while preserving the same task-relevant result.

Optimal-feedback and uncontrolled-manifold evidence directly pressure any theory that equates skill with exact repetition: biological control often stabilizes task-relevant dimensions while allowing variation in redundant dimensions.

## 1.7 Outcome / Task Result

World/task consequence relative to one or more evaluation variables.

```text
jump action executed
but ledge not reached

shot executed
but target moved

squad order admitted
but unit lost before arrival
```

Therefore freeze remains impossible at A, but the working chain becomes:

```text
Intent
→ Input Evidence
→ Mapping / Interpretation
→ Control Signal / Action Attempt
→ Admission / Execution
→ Movement / State Transition
→ Task / World Outcome
→ Feedback
```

---

# 2. First new anti-collapse laws

GDF1-A adopts these as **research separations**, not frozen foundations yet:

```text
InputSignal != GameAction
PlayerMotorMovement != GameAction
ActionAttempt != ExecutedAction
MovementTrajectory != TaskOutcome
ExecutedAction != TaskSuccess
```

These laws immediately survive:

```text
accessibility remapping
RTS semantic command
turn-based action
analog steering
shared control
synthetic controller
BCI/voice input
```

---

# 3. Accessibility is a foundational control falsifier, not an edge UX case

A GameAction such as:

```text
MOVE_RIGHT
JUMP
CONFIRM
```

can be expressed through:

```text
key press
stick displacement
grip contraction
large-body touch pad
voice adapter
switch controller
```

without changing its Game-local semantic identity.

Studies of adapted control interfaces for people with motor impairment show that changing the input/controller mapping can dramatically change who can successfully direct a cursor or game control while the software task remains substantially the same.

Therefore:

```text
PlayerMotorMovement != GameAction
InputEffector != ControlLocus
ControlAccess is mapping-relative.
```

This is not merely an accessibility principle.

It tells us the ontology of Game action itself cannot be defined by one bodily gesture.

---

# 4. Control must be split into different explananda

`Control` is too overloaded for GDF1.

At least four targets must remain distinct.

## 4.1 System controllability

A property of the dynamical/action system: what state variables can be influenced/reached under admissible controls.

Classical control-theoretic controllability is a mathematical special case, not the full player-facing concept.

## 4.2 Participant objective control

Actual causal influence of participant policy/commands over task-relevant variables.

## 4.3 Control policy/process

How actions/control signals are selected and corrected over time.

This may be:

```text
feedforward/predictive
feedback-corrective
mixed
hierarchical
delegated/shared
```

## 4.4 Subjective control / Sense of Agency

Human experiential attribution that `I am controlling/causing this`.

Wen et al.'s assisted continuous-control experiment is a strong boundary case: the system ignored some erroneous commands, improving performance while reported agency could increase despite reduced exact command execution.

Thus:

```text
ObjectiveCommandExecutionShare != SenseOfAgency
```

and:

```text
ControlQuality cannot be one scalar by default.
```

---

# 5. Open-loop vs closed-loop is not the right binary for Game skill

R21 emphasized feedback loops. GDF1-A adds predictive control pressure.

Wolpert/Ghahramani/Jordan and Shadmehr/Mussa-Ivaldi provide classic experimental evidence that human sensorimotor adaptation uses predictive/internal-model-like structure rather than waiting only for retrospective feedback.

Todorov/Jordan's optimal-feedback account adds another correction: control can selectively correct deviations that matter to the task while tolerating variability in redundant dimensions.

Therefore real skilled execution is better pressured by:

```text
prediction
state estimation
ongoing feedback
selective correction
task-relevant error
```

than by a simple:

```text
Input → Reaction → Feedback → Reaction
```

chain.

GDF1 must compare internal-model, optimal-feedback, dynamical/constraints and ecological accounts rather than prematurely choosing one.

---

# 6. Exact repeatability is not Skill

One of GDF0's unresolved debts was `PerformanceProgress`.

A naive skill theory might say:

```text
expert = same motion every time
```

Motor-control evidence attacks this directly.

Goal-equivalent/uncontrolled-manifold studies find that variability can be larger in dimensions that preserve important task variables than in dimensions that disturb them.

Todorov/Jordan likewise formalize a minimum-intervention principle in which task-irrelevant deviations need not be strongly corrected.

Therefore:

```text
Consistency != ExactRepetition
MotorVariability != Error by identity
```

A more useful Game question is:

> Which variables does skilled play stabilize, and which degrees of freedom remain available for adaptation/expression?

This is likely to matter deeply for:

```text
fighting
racing
sports
platforming
aiming
rhythm
```

and later for Game Feel.

---

# 7. Skill is not Performance

GDF1-A needs a stricter target separation.

## 7.1 Performance

Observed result in one episode/condition.

```text
score
hit rate
completion time
endpoint error
lap time
combo success
```

## 7.2 Skill

Working target:

```text
SkillState = a learned, condition-relative capability
that changes the distribution of task-relevant performance
through perception/prediction/selection/execution/correction.
```

This is deliberately not frozen yet.

Why distribution rather than one score?

Because two controllers/players can rank differently under:

```text
nominal condition
perturbation
new speed
new mapping
new opponent
fatigue
transfer task
```

The structural probe in this round gives one controller a higher nominal score but catastrophic perturbation performance, while another has slightly lower nominal performance and much higher cross-condition robustness.

No universal value ordering is claimed.

The point is:

```text
PerformanceSample != SkillState
```

## 7.3 Learning

Learning concerns durable change in SkillState/behavioral capability across practice/history.

Transient compensation, warm-up, fatigue or lucky performance does not automatically establish learning.

Thus:

```text
MotorPerformanceChange != MotorLearning
```

---

# 8. Skill is not Technique

A `Technique` is an organized means/policy/coordination solution.

Examples:

```text
wave-dash
flick aim
trail braking
heel-toe
specific parry sequence
one combo route
```

A participant may know/attempt a technique but execute it poorly.

A skilled participant may switch techniques according to context.

Therefore:

```text
Technique != Skill
```

Potential future decomposition:

```text
Technique repertoire
× technique selection
× execution capability
× adaptation/transfer
```

must be tested in later GDF1 rounds.

---

# 9. Accuracy, precision, speed, consistency and timing must separate

These terms are often compressed into `good execution`.

GDF1-A uses the following operational distinctions:

```text
Accuracy
= closeness of task result to target/reference.

Precision
= dispersion/variability of repeated results around their own distribution.

Speed
= temporal rate/duration of execution.

Consistency
= stability of task-relevant performance properties across repetitions/conditions.

TimingSkill
= ability to place/control action relative to relevant temporal structure/state.

ReactionTime
= delay between a designated signal/event and response initiation/registration.
```

Fitts' original aimed-movement experiments are useful because they make speed and accuracy constraints interact systematically rather than treating either as the definition of motor skill.

Auto Orbit adds a Game-like pressure: transferring skill across environmental speeds required recalibration of action timing, and higher skill related to lower variability in timing/chunking measures.

So:

```text
Fast != Skilled
Accurate != Precise
LowReactionTime != GoodTiming
LowVariability != universally Skilled
```

The task/evaluation topology decides which combination matters.

---

# 10. Affordance must be protected from Game-design overloading

R21 correctly used Warren's relational account:

```text
Affordance = Actor × Environment relation
```

GDF1-A adds a warning.

Digital Game design often uses `affordance` for:

```text
button is shown
rule allows action
UI communicates action
object has interaction tag
```

These are not automatically the same target.

Separate:

```text
ActorCapability
ActualAffordance
PerceivedAffordance
GameLegality / Admission
AffordanceCue / Representation
```

Warren's stair-climbing experiments are specifically strong because climbability scaled with body-environment fit rather than absolute stair geometry.

But a digital Game can create formally authorized actions whose possibility is not a physical ecological affordance in the same sense.

So GDF1 should avoid forcing every symbolic GameAction into Gibsonian vocabulary.

Working guard:

```text
GameActionAvailability != Affordance by identity.
```

---

# 11. Embodiment needs four different bodies/loci

R21 separated Body, Avatar and ControlLocus. GDF1-A makes the control chain more explicit.

## 11.1 Player biological body

Human bodily substrate with sensory/motor capabilities and constraints.

Owned by Human foundations at the deeper mechanism level.

## 11.2 Input effector/channel

The current physical channel used to supply control evidence:

```text
finger
hand
arms/legs
gaze
voice
whole-body pose
BCI signal
```

It need not equal the whole body.

## 11.3 Game ControlLocus

The Game-local locus through which participant control becomes authoritative action/state change:

```text
avatar
vehicle
cursor
piece
camera
army
menu/policy surface
```

## 11.4 Embodiment experience

Human experiential target involving some profile of:

```text
agency
ownership
self-location
sensorimotor contingency
body representation
```

Kalckert/Ehrsson already show agency and body ownership can dissociate.

VR avatar-control experiments further show that changing the fidelity/degree of body control can change embodiment measures, but objective control and embodiment remain distinct.

Therefore:

```text
PlayerBody != InputEffector != ControlLocus != EmbodimentExperience
```

This is foundational for accessibility, VR and Agent control alike.

---

# 12. Synthetic control is a boundary case, not a model of human motor skill

A synthetic controller can possess:

```text
policy competence
state estimation
trajectory optimization
reaction speed
precision
```

without a human body or established human-like embodiment experience.

Therefore synthetic systems are useful to attack structural claims such as:

```text
GameAction requires bodily movement
Skill requires conscious motor experience
Embodiment is required for competent control
```

but they cannot establish:

```text
human motor learning mechanism
felt agency
felt embodiment
PlayExperience
```

GDF0's structural/experiential guard remains binding.

---

# 13. First competing-model map

GDF1-A does not choose a winner. It opens the models that GDF1-B must force into real conflict.

## M1 — Symbolic Action Pipeline

```text
Intent → input/command → action → resolution → outcome
```

Strength:
clear Game authority and semantic action identity.

Weakness:
under-models continuous prediction, correction, dynamics and motor abundance.

## M2 — Internal/Predictive Model Control

Pressure from Wolpert/Shadmehr tradition:

```text
learn dynamics / predict state/effect
→ use prediction in control/adaptation
```

Strength:
perturbation learning, anticipation, transfer/generalization questions.

Weakness:
`internal model` is not automatically the right description of every skill/control form and belongs primarily to Human mechanism science.

## M3 — Optimal Feedback / Minimum Intervention

Pressure from Todorov/Jordan:

```text
stabilize task-relevant variables
allow variability where it does not harm the objective
```

Strength:
explains skilled variability and goal-equivalent solutions.

Weakness:
requires declared costs/task variables; Game player value cannot be assumed to equal one optimal-control objective.

## M4 — Ecological Affordance / Actor–Environment Dynamics

Pressure from Warren/Gibson lineage:

```text
possible action emerges from actor-environment fit
```

Strength:
embodiment, locomotion, scale, reachability, direct perception/action coupling.

Weakness:
symbolic commands and formal rule-authorized digital actions may not map cleanly onto physical ecological affordance language.

## M5 — Constraints-Led / Dynamical Coordination

Pressure from Newell and coordination dynamics:

```text
organism/actor × task × environment constraints
→ emergent coordination solution
```

Strength:
multiple solutions, adaptation, morphology/environment dependence.

Weakness:
can become too broad unless it predicts which coordination variables stabilize/change.

## M6 — Motor Program / Schema

Pressure from Schmidt-type motor learning:

```text
generalized action structure + parameterization / recognition
```

Strength:
technique families, discrete skills, transfer/generalization.

Weakness:
must compete with feedback/dynamical accounts and cannot explain all continuous online correction by itself.

## M7 — Information-Theoretic / Speed–Accuracy

Pressure from Fitts-style tasks:

```text
target tolerance × distance × movement time
```

Strength:
precise operational tradeoffs for aimed control.

Weakness:
not a general theory of skill, timing, strategy, rhythm or rich embodied action.

## M8 — Agency / Comparator / Inferential Control

Pressure from Haggard/Wen and agency research:

```text
prediction/contingency/performance/context
→ subjective authorship/control judgment
```

Strength:
explains objective/subjective control dissociations.

Weakness:
SenseOfAgency is an experiential target, not the mechanism of GameAction execution itself.

## M9 — Shared / Assistive / Hierarchical Control

```text
human intent/command
× assistance/autonomy
→ final action trajectory
```

Strength:
accessibility, delegation, automation, mixed control.

Weakness:
needs explicit variable/locus topology; one `percent human control` number is inadequate.

## M10 — Skill-as-Conditional-Capability

GDF1 candidate synthesis:

```text
Skill is latent learned capability expressed as a conditional performance distribution,
not one observed performance outcome.
```

Strength:
handles robustness, transfer, perturbation and task specificity.

Weakness:
may be too generic unless GDF1-B/C derive sharper discriminating measures and distinguish knowledge/strategy/execution components.

Status:

```text
N1 candidate only.
```

---

# 14. Boundary corpus for GDF1-B

The model tournament must span materially different control regimes.

```text
precision platforming
fighting
FPS aiming
racing / vehicle dynamics
sports
rhythm
direct manipulation / tool use
RTS / command control
turn-based symbolic action
delegation/shared control
accessibility remapping
VR embodiment
BCI/nonstandard input
synthetic controllers
```

A model that only works for one of these is a subdomain theory, not GDF1-wide foundation.

---

# 15. First executable structural probes

Canonical research-only probe:

```text
scripts/gdf1-a/target-separation-probes.mjs
```

## Probe A — same input, different action

```text
A button in gameplay → JUMP
A button in menu     → CONFIRM
```

Therefore under the declared mappings:

```text
InputSignal != GameAction
```

## Probe B — different physical movement, same action

```text
keyboard keypress
adaptive grip contraction
voice adapter
```

all produce the same normalized `BUTTON_A → JUMP` GameAction.

Therefore:

```text
PlayerMotorMovement != GameAction
```

## Probe C — different trajectory, same task result

Three different toy trajectories all end with zero endpoint error.

Therefore:

```text
MovementTrajectory != TaskOutcome
```

and exact movement repetition is not logically necessary for identical task-level success.

## Probe D — nominal performance vs robustness

One toy controller scores higher in the nominal condition but collapses under perturbation; another is slightly worse nominally but much better across both conditions.

Therefore one nominal score cannot define SkillState.

```text
PerformanceSample != SkillState
```

## Probe E — attempt vs execution

A `DASH_EAST` attempt is admitted as an intent/action attempt but lacks the required capability resource.

```text
ActionAttempt exists
ExecutedAction = false
```

Therefore:

```text
ActionAttempt != ExecutedAction
```

No human motor-control claim is made by these probes.

---

# 16. External evidence pressure selected for A

## 16.1 Prediction and adaptation

Shadmehr & Mussa-Ivaldi's force-field study found strong aftereffects and generalization patterns after adaptation, supporting learned predictive representation of changed movement dynamics.

Wolpert, Ghahramani & Jordan provided experimental support for internal-model/state-estimation accounts in sensorimotor integration.

GDF1 use:

```text
Skill/control cannot be modeled as stimulus→reaction only.
```

## 16.2 Task-relevant variability

Todorov & Jordan's optimal-feedback model and UCM/goal-equivalent experiments show that skilled coordination may preserve variability in dimensions irrelevant to the task objective while stabilizing important variables.

GDF1 use:

```text
MotorVariability != Error
ExactRepeatability != Skill
```

## 16.3 Actor-relative affordance

Warren's stair-climbing experiments tie perceived climbability to body/environment scaling.

GDF1 use:

```text
Affordance != object tag
```

but digital formal legality must remain separately modeled.

## 16.4 Speed/accuracy

Fitts' aimed-movement work establishes systematic interaction of movement time and target tolerance/distance.

GDF1 use:

```text
Speed and accuracy are performance dimensions, not Skill by identity.
```

## 16.5 Video games as real motor-skill environments

Large-scale Aim Lab work observed motor-acuity improvement over long voluntary practice windows.

FPS kinematic work found strong continuity with standard sensorimotor measures and task-performance prediction from movement metrics.

Auto Orbit work shows timing-skill recalibration under speed perturbation.

GDF1 use:

```text
Game execution is a legitimate motor-skill research domain;
Game telemetry can expose long-horizon learning/transfer rather than only toy lab tasks.
```

## 16.6 Assistance and accessibility

Wen et al. demonstrate that assistance may increase performance and reported agency even when some erroneous commands are not executed.

Adapted-controller evidence shows interface mapping can change which participants can control the same task.

GDF1 use:

```text
raw motor authority != agency
physical movement != GameAction
control access is mapping-relative.
```

---

# 17. Owner boundary after A

## Human owns

```text
neural motor commands
biomechanics
proprioception
motor adaptation mechanisms
motor memory
subjective agency/body ownership
fatigue/development
```

Game consumes these as constraints/evidence when player-facing action depends on them.

## Media owns

```text
signal acquisition
perceptual organization
attention
representation
multimodal feedback encoding
```

Game specifies which control/action distinctions must become perceptually available.

## Game owns

```text
GameAction identity
control mapping into Game-local actions/variables
current action legality/admission
controlled locus semantics
world consequence/action resolution coupling
value-bearing execution distinctions
affordance/capability/legality presentation contract within GameStructure
```

This boundary prevents GDF1 from becoming a duplicate textbook of motor neuroscience.

---

# 18. First GDF1 discovery ledger

## N0 — established external pressure

```text
predictive/internal-model evidence in motor adaptation/integration
optimal-feedback/minimum-intervention accounts
motor abundance/goal-equivalent variability
actor-relative affordance evidence
speed–accuracy tradeoff
objective-control / sense-of-agency dissociation
ownership / agency dissociation
long-horizon video-game motor learning and kinematic skill measures
accessibility/control-remapping effects
```

## N1 — Ordivon synthesis candidates

```text
A1 DeepActionSeparation:
InputSignal != ControlSignal != GameAction != MovementTrajectory != Outcome

A2 SkillState / Performance separation:
PerformanceSample != learned conditional SkillState

A3 Body-Locus separation:
PlayerBody != InputEffector != ControlLocus != EmbodimentExperience

A4 GameActionAvailability guard:
Capability / ecological affordance / perceived affordance / Game legality / cue remain distinct

A5 TaskRelevantConsistency:
skilled stability should be evaluated against task-relevant variables,
not exact movement repetition by default
```

These are N1 candidates only.

## N2

```text
NONE.
```

## N3

```text
NONE.
```

---

# 19. What A rejects already

```text
Action = bodily movement
→ REJECTED.

Input = Action
→ REJECTED.

Action attempt = executed action
→ REJECTED.

Skill = one performance score
→ REJECTED.

Skill = accuracy
→ REJECTED.

Skill = reaction speed
→ REJECTED.

Skill = exact repeatability
→ REJECTED.

Motor variability = noise/error by identity
→ REJECTED.

Affordance = UI cue
→ REJECTED.

Affordance = Game legality
→ REJECTED.

Embodiment = objective control
→ REJECTED.

Human physical movement = Game action identity
→ REJECTED.
```

---

# 20. Foundation reopen audit

GDF1-A creates a finer research vocabulary but no contradiction with frozen foundations.

All distinctions remain expressible through:

```text
F1 Entity/Reference
F2 State
F3 Relation
F4 Transition/Constraint
F5 Time
F6 Authority/Provenance
F7 Observation/Representation
F8 Evaluation/Motivation
F9 Action/Capability/Policy/Control
```

Likewise, frozen GDF0 explicitly permits later mechanistic decomposition.

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 PRC-7 = NOT TRIGGERED
```

A new distinction inside `F9 Action/Control` is not itself a reason to add a new semantic primitive.

---

# 21. Exact GDF1-B frontier

A is intentionally broad.

B must now force the competing models into **real conflicts** rather than accumulate compatible metaphors.

Priority attacks:

```text
B1 Internal-model prediction vs ecological/dynamical direct-coupling accounts.
B2 Optimal-feedback/task-variable stabilization vs exact-technique/repetition models.
B3 Schema/program vs continuous online correction and transfer.
B4 SkillState as conditional capability vs score/expertise/technique alternatives.
B5 Affordance vs formal GameActionAvailability under digital/symbolic rules.
B6 Direct/manual control vs shared/assistive control under matched intent/performance.
B7 Embodiment/control coupling under remapping, VR, vehicle/tool and abstract control.
B8 Synthetic controller as structural falsifier without human-mechanism/experience leakage.
```

B should define explicit target, scope and falsifier for each theory, following frozen GDF0 C3 ModelConflictProtocol.

---

# Primary evidence anchors used in GDF1-A

- Todorov & Jordan (2002), *Optimal feedback control as a theory of motor coordination*, Nature Neuroscience 5:1226–1235, DOI 10.1038/nn963.
- Shadmehr & Mussa-Ivaldi (1994), *Adaptive representation of dynamics during learning of a motor task*, Journal of Neuroscience 14:3208–3224, DOI 10.1523/JNEUROSCI.14-05-03208.1994.
- Wolpert, Ghahramani & Jordan (1995), *An internal model for sensorimotor integration*, Science 269:1880–1882, DOI 10.1126/science.7569931.
- Warren (1984), *Perceiving affordances: visual guidance of stair climbing*, JEP:HPP 10:683–703, DOI 10.1037/0096-1523.10.5.683.
- Fitts (1954), *The information capacity of the human motor system in controlling the amplitude of movement*, Journal of Experimental Psychology 47:381–391, DOI 10.1037/h0055392.
- Schmidt (1975), *A schema theory of discrete motor skill learning*, Psychological Review 82:225–260, DOI 10.1037/h0076770.
- Newell (1986), *Constraints on the Development of Coordination*, in Motor Development in Children, DOI 10.1007/978-94-009-4460-2_19.
- Haggard, Clark & Kalogeras (2002), *Voluntary action and conscious awareness*, Nature Neuroscience 5:382–385, DOI 10.1038/nn827.
- Kalckert & Ehrsson (2012), *Moving a Rubber Hand that Feels Like Your Own*, Frontiers in Human Neuroscience 6:40, DOI 10.3389/fnhum.2012.00040.
- Wen, Yamashita & Asama (2015), *The Sense of Agency during Continuous Action*, PLOS ONE 10:e0125226, DOI 10.1371/journal.pone.0125226.
- Gozli, Bavelier & Pratt (2014), *The effect of action video game playing on sensorimotor learning*, Human Movement Science 38:152–162, DOI 10.1016/j.humov.2014.09.004.
- Listman et al. (2021), *Long-Term Motor Learning in the Wild With High Volume Video Game Data*, Frontiers in Psychology 12, PMID 34987368.
- Warburton et al. (2023), *Kinematic markers of skill in first-person shooter video games*, PNAS Nexus 2:pgad249, DOI 10.1093/pnasnexus/pgad249.
- *Cognitive & motor skill transfer across speeds: A video game study* (2021), PLOS ONE, DOI 10.1371/journal.pone.0258242.
- *Democratizing Neurorehabilitation: How Accessible are Low-Cost Mobile-Gaming Technologies for Self-Rehabilitation of Arm Disability in Stroke?* (2016), PMCID PMC5051962.
