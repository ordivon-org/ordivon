---
schema_version: 1
id: game.deep-foundations.gdf1-b
title: Ordivon Game Deep Foundations — GDF1-B Competing Model Falsification
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Applies the frozen GDF0 ModelConflictProtocol to GDF1 motor/control/skill theories. Finds that many famous theory clashes are target/scope mismatches rather than Game-wide rivals; rejects universal exact-trajectory, open-loop-only, current-score=skill, globally-lower-variability=skill, raw-manual-control=agency and affordance=Game-legality collapses; reconstructs Skill from a scalar state into a condition-relative capability profile while leaving internal-model versus strong ecological/dynamical exclusivity underdetermined.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf1-a
  - game.play-game-deep-foundations.v1
  - game.foundations-research.r21
---
# Ordivon Game Deep Foundations — GDF1-B

## 0. B is a conflict-elimination round

A opened ten model families.

B asks a harsher question:

> Which of these actually make incompatible predictions about the same target, at the same scope, and which only look incompatible because different disciplines reuse words like `control`, `action`, `skill` and `agency`?

Frozen GDF0 conflict rule:

```text
RealTheoryConflict requires overlap in:
Target × ClaimType × Scope × Prediction.
```

Canonical matrix/probes:

```text
evidence/gdf1-b/model-conflict-matrix.json
evidence/gdf1-b/model-falsifier-probes.json
scripts/gdf1-b/model-falsifier-probes.mjs
scripts/gdf1-b/audit-model-conflicts.mjs
```

---

# 1. First result — there is no single `motor-control tournament`

The A models occupy different explananda.

```text
M1 Symbolic Action Pipeline
→ Game-local semantic action / admission / authority

M2 Internal/Predictive Model
→ Human sensorimotor prediction/adaptation

M3 Optimal Feedback
→ coordination policy under noise/redundancy/task costs

M4 Ecological Affordance
→ actor-environment possibility/information for action

M5 Constraints/Dynamical
→ emergence/stability/flexibility of coordination

M6 Schema/Program
→ organization/generalization of learned movement patterns

M7 Speed-Accuracy
→ narrow quantitative aimed-movement relation

M8 Sense of Agency
→ subjective attribution of control

M9 Shared/Hierarchical Control
→ controller contribution topology

M10 SkillProfile candidate
→ learned capability inferred across conditions
```

Treating all ten as alternatives to one another would repeat the exact error GDF0 eliminated.

---

# 2. M1 vs Human motor theories — pseudo-conflict

The Game needs to know:

```text
which GameAction was attempted?
was it admitted?
what state transition occurred?
who had authority?
```

Human motor science may ask:

```text
how was the movement predicted?
how were muscles coordinated?
what error was corrected?
```

These are not rival answers.

A predictive/optimal/dynamical Human controller can implement the movement/expression required to cause one GameAction while the Game maintains a symbolic semantic/authority contract.

Therefore:

```text
M1 vs M2/M3/M5/M6
= mostly layer separation, not theory conflict.
```

This is an important owner boundary: Game should not adopt one neuroscience theory merely to explain its own action semantics.

---

# 3. Internal-model vs ecological/dynamical theory — real only in strong forms

This is the most famous-looking conflict, but B refuses to caricature it.

## Strong internal-model claim

```text
successful adaptive online control necessarily depends on
internally represented predictive dynamics/state transformations.
```

## Strong ecological/direct claim

```text
sufficiently informative organism-environment coupling can regulate action
without internal representational reconstruction of those dynamics.
```

These can conflict over **necessity**.

But current GDF1 evidence does not earn a universal verdict.

Shadmehr/Mussa-Ivaldi and Wolpert/Ghahramani/Jordan pressure pure stimulus-response accounts by showing adaptation/aftereffects and predictive sensorimotor structure.

Warren/ecological work independently demonstrates that action possibilities are actor-relative and can be specified through organism-environment relations.

Neither result by itself proves:

```text
internal model required for all skilled action
```

or:

```text
internal representation never required.
```

Therefore B disposition:

```text
M2 vs strong M4/M5 exclusivity
= PARTIAL REAL CONFLICT
= UNDERDETERMINED at GDF1-wide scope.
```

This is a deliberate non-resolution.

---

# 4. Internal model vs optimal feedback — mostly pseudo-conflict

Optimal feedback control commonly presupposes or can consume state estimation/prediction.

Todorov/Jordan's important distinctive claim is not `there is no internal prediction`.

It is the control policy structure:

```text
correct deviations insofar as they matter to task goals/costs;
allow variability in redundant/task-irrelevant dimensions.
```

Thus:

```text
M2 predictive representation
and
M3 selective task-dependent correction
```

can coexist.

GDF1 should not invent a rivalry here.

---

# 5. Optimal feedback vs exact desired trajectory — real conflict

Now there is a genuine discriminating prediction.

## Exact-trajectory universal

```text
Skilled movement approaches one desired/correct trajectory,
and trial-to-trial deviation is broadly error to be eliminated.
```

## Task-relevant stabilization / minimum intervention

```text
Task-critical variables are stabilized;
redundant degrees of freedom can remain variable
if they do not threaten the relevant objective.
```

Todorov/Jordan explicitly motivate optimal feedback control by the empirical fact that behavioral goals can be achieved reliably although detailed movements are not exactly reproduced, and derive correction concentrated on deviations that interfere with task goals.

Therefore:

```text
ExactDesiredTrajectory as universal skill/control theory
→ REJECTED.
```

Important qualification:

Some tasks really do make a specific trajectory task-relevant.

Examples:

```text
rhythm choreography
racing line constraints
motion-tracked pose target
fighting input path
```

In those tasks, trajectory variability may genuinely be error.

The law is therefore not:

```text
trajectory never matters.
```

It is:

```text
Task relevance decides which variability is error.
```

---

# 6. `lower variability = more Skill` also fails globally

Auto Orbit provides a useful apparent counterpressure: within that timing/chunking task, acquiring skill was associated with reduced variability in action sequencing/timing, and timing variability helped explain individual skill differences.

This does **not** contradict optimal-feedback/UCM reasoning.

Why?

Because Auto Orbit's timing is itself a task-relevant variable.

The correct synthesis is:

```text
Variability has no universal sign.
```

You must ask:

```text
variability of what variable?
relative to what task objective?
under what condition?
```

Thus reject:

```text
LowerGlobalMotorVariability = MoreSkill.
```

Retain:

# B-A — Task-Relevant Variability Profile

```text
Skill evidence should distinguish variability that perturbs
value/task-relevant variables from variability that preserves them.
```

Status:

```text
N1 synthesis candidate.
```

---

# 7. Schema/program vs dynamical/feedback theories — only strong open-loop versions lose

A weak schema/program hypothesis can say:

```text
learned action families possess reusable organization/parameters.
```

That is compatible with:

```text
online feedback
contextual parameterization
constraint-sensitive execution
```

and therefore is not directly falsified by continuous correction.

A much stronger hypothesis says:

```text
once skilled movement begins,
its successful realization is universally a fixed precomputed program
whose within-action trajectory does not require state-dependent correction.
```

That strong version conflicts with feedback/predictive control and perturbation-sensitive tasks.

GDF1-B rejects only the strong universal:

```text
FullyOpenLoopFixedProgramForAllSkill
→ REJECTED.
```

Schema/program-like organization survives as a **subscope mechanism**, especially for discrete/sequential technique families.

---

# 8. Fitts-style speed/accuracy is valuable precisely because it is narrow

Fitts' aimed movement law earns value by making operational predictions for a particular task family.

It does **not** need to become a universal Skill theory.

A player can have high skill in:

```text
rhythm phase control
parry reading
race-line planning
turn-based tactics
shared-control supervision
```

without being adequately summarized by target distance/width and movement time.

Therefore:

```text
M7 vs M10
= scope mismatch, not winner-take-all competition.
```

Lesson:

> A narrow model with sharp predictions is often more scientifically valuable than a broad model that claims to explain all Skill.

---

# 9. Practice performance vs learning — a decisive Skill falsifier

GDF1-A proposed:

```text
PerformanceSample != SkillState.
```

B now obtains stronger experimental pressure.

Motor-learning experiments on contextual interference and guidance show cases where a condition that produces **better performance during acquisition/practice** produces **worse delayed retention or transfer**, while a more difficult/random/less-guided practice condition can perform worse during practice yet retain/transfer better later.

Therefore a theory:

```text
Skill = current observed practice performance
```

makes the wrong ordering prediction.

This is a genuine falsification.

Freeze is premature, but B can now strongly retain:

```text
CurrentPerformance != Learning != Skill capability.
```

Delayed retention/transfer are often stronger evidence of durable learning than end-of-practice performance, but they are still probes rather than the complete definition of Skill.

---

# 10. Aim Lab adds long-horizon pressure against one-score Skill

Large-scale Aim Lab data are especially useful because they separate multiple performance dimensions over long voluntary practice.

The study found:

```text
hit-rate accuracy improved modestly and saturated relatively early;
hits-per-second / motor acuity continued improving substantially over days;
next-day retention was partial rather than complete;
practice amount had nonlinear relations with improvement.
```

Thus even inside one FPS aiming task:

```text
Accuracy trajectory
!= Motor-acuity trajectory.
```

One scalar `score` can hide different learning processes and ceilings.

This supports a multi-variable Skill representation.

---

# 11. FPS kinematics: performance can be decomposed without becoming Skill itself

Warburton et al. showed that FPS-style aiming movements can display kinematic regularities continuous with classic reaching tasks and that spatial movement metrics predicted overall task performance.

This is valuable evidence that Game telemetry can expose motor-control structure.

But:

```text
metric predicts performance
!= metric is Skill.
```

The same participant's skill may need to be tested across:

```text
new target schedules
pressure
mapping/sensitivity
retention interval
transfer task
perturbation
```

before a broad capability claim is justified.

---

# 12. Auto Orbit destroys `Technique = fixed timing sequence`

Auto Orbit directly manipulated environmental speed.

Transfer required recalibration of action timing, while substantial knowledge/procedural structure transferred across speeds.

That means a learned skill can contain both:

```text
invariant/reusable organization
and
condition-dependent tuning.
```

Therefore:

```text
Technique != one fixed parameter sequence.
```

A better future decomposition is:

```text
TechniqueFamily
× Parameterization
× Selection
× OnlineCorrection
× Transfer/Recalibration
```

This should be tested rather than frozen now.

---

# 13. SkillState is still too scalar — reconstruct to SkillProfile

B now attacks Ordivon's own A2 candidate.

A called it `SkillState`, which still invites one hidden number.

But the evidence repeatedly shows condition dependence:

```text
practice vs retention
nominal vs perturbation
one speed vs another
accuracy vs acuity
one mapping vs remapped controller
one technique vs another
```

So B reconstructs:

# **SkillProfile / Conditional Capability Surface**

Working definition:

> A learned, history-dependent conditional capability over a declared task family, inferred from the distribution of task-relevant performance under relevant conditions/probes.

Formal sketch:

```text
P(
  task-relevant performance variables
  |
  participant/agent history,
  task family,
  condition,
  control mapping,
  perturbation
)
```

This is not a claim that Skill literally exists as a probability table in the brain.

It is an epistemically safer **Game/research target** than one score.

---

# 14. What belongs inside a SkillProfile?

Do not pre-freeze mandatory dimensions.

Possible probes include:

```text
acquisition trajectory
delayed retention
transfer
perturbation response
recalibration/adaptation
mapping change
speed/accuracy/timing tradeoffs
robustness
energy/action efficiency
error correction
```

But these are probes of capability, not universal components.

For some skill:

```text
retention may matter greatly;
transfer may intentionally be narrow;
peak performance may matter more than robustness;
variability may be expressive rather than error.
```

Therefore no scalarization yet.

Novelty status:

```text
N1 synthesis candidate only.
```

---

# 15. Skill acquisition and adaptation must separate

Another compression error becomes visible.

## Skill acquisition/refinement

Broad durable change in capability through practice/history.

May include:

```text
new coordination
better prediction
better action selection
technique learning
faster/cleaner execution
new perceptual distinctions
```

## Adaptation/recalibration

Adjustment of an existing controller/skill to changed dynamics, mapping or environment.

Force-field and visuomotor adaptation paradigms study this especially clearly.

Auto Orbit speed transfer also contains recalibration of timing.

Therefore:

```text
Adaptation can contribute to Skill
but
SkillAcquisition != Adaptation by identity.
```

This prevents GDF1 from treating all improvement as error-based recalibration.

---

# 16. Manual control vs assistance — real conflict with a monotonic theory

A common implicit theory is:

```text
More exact human command execution
→ more objective control
→ more SenseOfAgency
→ better control experience.
```

Wen et al. provides a clean falsifier for the monotonic experiential part.

In their continuous target-control task, assistance suppressed commands that would move the dot away from the goal. Under longer/uncertain action-feedback delays, participants could report **greater** control in the assisted condition while performance improved, despite a substantial fraction of their commands not being executed.

Thus:

```text
ExactCommandExecutionShare
is not monotonic with
SenseOfAgency.
```

And:

```text
ManualControlUniversalSuperiority
→ REJECTED.
```

This does **not** imply assistance is universally beneficial.

It means the relevant structure includes:

```text
which intent distinctions are preserved
which errors are corrected
whether assistance is predictable/learnable
what skill layer is intended
performance
attribution
```

---

# 17. Important warning from motor-learning guidance studies

There is an apparent tension:

```text
Wen-style assistance
can improve immediate performance and agency judgment.
```

But motor-learning guidance experiments show that heavy physical guidance or very frequent augmented feedback can produce worse retention/transfer even while helping practice.

These findings are not contradictory because targets/time horizons differ.

```text
ImmediatePerformance
SubjectiveAgency
DurableLearning
```

are distinct outcomes.

This yields one of B's strongest design/research warnings:

# B-B — Assistance Timescale Separation

```text
An assist can improve present execution while weakening independent future performance.
```

Therefore Game accessibility/assist research must state whether the intended value is:

```text
access now
performance now
skill exposure
independent future mastery
shared-controller mastery
```

rather than assuming one outcome.

Status:

```text
N1 synthesis candidate.
```

---

# 18. Affordance vs GameActionAvailability — a genuine target boundary

Warren's ecological result supports:

```text
physical/embodied action possibility
is actor-environment relational.
```

But Games add formal authority.

A chess player may physically be able to pick up a bishop and put it anywhere on the board, while the current GameStructure prohibits most destinations.

A digital character may be granted `TELEPORT` by a rule mutation even though no prior physical geometry afforded ordinary traversal to that state.

Therefore:

```text
EcologicalAffordance
!= GameLegality
!= GameActionAvailability.
```

They can interact:

```text
embodied capability + environment
→ physical/actor-relative affordance

Game rules/capabilities/authority
→ formal action availability/admission
```

For physical sport the two layers can be tightly coupled.

For symbolic/digital games they can diverge sharply.

So M4 is retained for the domain where it earns explanatory power, not stretched into all Game action semantics.

---

# 19. Embodiment theories are not yet competing with Skill theories

B considered whether embodiment should explain skilled Game action.

Current answer:

```text
not generically.
```

Embodiment/body ownership/self-location and skilled task control can covary in VR or vehicle/tool use, but:

```text
turn-based expert
RTS commander
synthetic policy
```

can possess high task competence without strong human body-ownership phenomena.

Therefore embodiment belongs in GDF1, but mostly as a **coupling/modulation target**, not the universal mechanism of Skill.

Future rounds should ask:

```text
When does bodily morphology/self-location change the reachable/control problem?
When does embodiment merely change experience/presence?
When does remapping preserve GameAction but alter motor learning demand?
```

---

# 20. Synthetic controllers resolve some structural questions and no Human mechanism question

A synthetic policy can:

```text
stabilize task variables
adapt to perturbations
transfer across states
choose techniques
execute with low variance
```

This is useful to demonstrate that the abstract Game notions:

```text
GameAction
conditional capability
policy competence
control topology
```

do not require a biological body.

But it cannot decide:

```text
internal human sensorimotor representation
body ownership
felt agency
human motor learning
```

Therefore synthetic controllers remain a **structural dissociation tool** in GDF1-B.

---

# 21. What the model tournament actually eliminates

## Rejected universal theories/collapses

```text
ExpertSkill = exact desired trajectory
→ REJECTED.

Lower global movement variability = more Skill
→ REJECTED.

All skilled movement = fully precomputed open-loop program
→ REJECTED.

Current practice performance = Skill/Learning
→ REJECTED.

More exact manual command execution = more subjective agency
→ REJECTED.

Manual control is universally superior to assistance
→ REJECTED.

Ecological affordance = formal Game action legality/availability
→ REJECTED.
```

## Not adjudicated globally

```text
Internal-model necessity
vs
strong ecological/direct-control sufficiency
→ UNDERDETERMINED.
```

## Scope-limited but retained

```text
Fitts speed-accuracy
Schema/program organization
Ecological affordance
Internal/predictive models
Optimal feedback
Constraints/dynamical coordination
Sense-of-agency inference
Shared/hierarchical control
```

None becomes `the Game skill theory`.

---

# 22. B's first reconstructed multi-level control model

Rather than selecting one Human motor theory, Game can remain mechanism-plural below a stable interface:

```text
Participant-side process
  perception / intention / prediction / coordination / learning
  [Human-owned; competing mechanisms]
             ↓
Input Effector / Control Expression
             ↓
Input Signal
             ↓
Mapping / Assistance / Interpretation
             ↓
Control Signal + Action Attempt
             ↓
GameAction Admission / Authority
             ↓
Executor / Movement / State Transition
             ↓
World / Task Outcome
             ↓
Feedback / Perception
             ↓
Performance sample
             ↓
History-dependent SkillProfile update/inference
```

Embodiment surrounds some of these couplings when a self-relevant body participates; it is not inserted as a mandatory node.

This preserves owner boundaries while supporting later Game-specific mechanics.

---

# 23. Discovery ledger after B

## N0 — external established pressure

```text
- optimal-feedback/minimum-intervention permits task-irrelevant variability;
- predictive motor adaptation/internal-model evidence exists in force-field/sensorimotor tasks;
- ecological affordances are actor-environment relational;
- contextual interference/guidance can reverse acquisition vs retention/transfer rankings;
- Aim Lab longitudinal data separate accuracy and motor-acuity learning trajectories;
- FPS kinematics expose motor-control regularities and performance-predictive measures;
- Auto Orbit transfer requires timing recalibration and shows task-specific variability signatures;
- assistance can improve performance and agency judgment despite suppressing many commands.
```

## N1 — Ordivon synthesis candidates

```text
B-A TaskRelevantVariabilityProfile

B-B AssistanceTimescaleSeparation

B-C SkillProfile / ConditionalCapabilitySurface

B-D MechanismPluralControlInterface:
Game freezes semantic/control interfaces without choosing one universal Human motor theory.
```

Strengthened from A:

```text
DeepActionSeparation
Body-Locus separation
GameActionAvailability guard
Performance != Skill/Learning
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

# 24. Foundation reopen audit

Nothing in B contradicts frozen GDF0 or R29.

Indeed B strengthens the reason for the existing owner split:

```text
Game action semantics can remain stable
while Human control mechanisms admit multiple competing explanations.
```

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 PRC-7 = NOT TRIGGERED
```

A future reopen would require a repeated Game phenomenon that cannot be represented through the frozen action/control/authority target structure, not merely a winner in a Human motor-theory debate.

---

# 25. Exact GDF1-C frontier

B has reduced the theory space enough to build a minimal mechanistic reconstruction.

# GDF1-C — Skill / Control Minimal Reconstruction

C should construct and attack the smallest Game-owned model containing:

```text
GameAction
ControlMapping
ControlContributionTopology
TaskRelevantVariableSet
PerformanceSample
SkillProfile
TechniqueFamily
Perturbation / Transfer / Retention probes
Assistance / Mapping state
```

Questions:

```text
1. Can SkillProfile be made operational without becoming an arbitrary bag of metrics?
2. How should TaskRelevantVariableSet be derived from GameStructure + PlayerValue rather than hand-labeled post hoc?
3. What is the relation among TechniqueFamily, policy, execution and SkillProfile?
4. When does transfer reveal broad skill versus merely a neighboring task?
5. When does remapping change access only, and when does it create a materially different skill?
6. Can assistance expose the same PlayerValue while changing the required SkillProfile?
7. Can Game distinguish skill ceiling, skill floor and skill expression without one scalar skill number?
8. Which parts are structural Game semantics versus Human learning mechanisms?
```

C should use executable synthetic capability surfaces and matched Game-task transformations as falsifiers, without claiming they model human phenomenology.

---

# Primary evidence anchors emphasized in B

- Todorov & Jordan (2002), *Optimal feedback control as a theory of motor coordination*, Nature Neuroscience 5:1226–1235, DOI 10.1038/nn963.
- Shadmehr & Mussa-Ivaldi (1994), *Adaptive representation of dynamics during learning of a motor task*, Journal of Neuroscience 14:3208–3224.
- Warren (1984), *Perceiving affordances: visual guidance of stair climbing*, JEP:HPP 10:683–703.
- Hall & Magill (1995), *Variability of Practice and Contextual Interference in Motor Skill Learning*, Journal of Motor Behavior 27:299–309.
- Winstein et al. (1994), *Effects of physical guidance and knowledge of results on motor learning: support for the guidance hypothesis*, Research Quarterly for Exercise and Sport.
- Tsutsui, Lee & Hodges (1998), *Contextual interference in learning new patterns of bimanual coordination*, Journal of Motor Behavior 30:151–157.
- Wen, Yamashita & Asama (2015), *The Sense of Agency during Continuous Action*, PLOS ONE 10:e0125226.
- Listman et al. (2021), *Long-Term Motor Learning in the Wild With High Volume Video Game Data*, Frontiers in Human Neuroscience 15:777779.
- Gianferrara, Betts & Anderson (2021), *Cognitive & motor skill transfer across speeds: A video game study*, PLOS ONE 16:e0258242.
- Warburton et al. (2023), *Kinematic markers of skill in first-person shooter video games*, PNAS Nexus 2:pgad249.
