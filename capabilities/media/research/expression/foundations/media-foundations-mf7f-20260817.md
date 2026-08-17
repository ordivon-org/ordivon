# Ordivon Media Foundations — MF7-F Control, Intervention, Feedback, Regulation & Reachability

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 43 at start  
**Input:** MF0–MF6 frozen; MF7-A→E complete/provisional.  
**Status:** MF7-F complete/provisional. State & Dynamics Foundations remain UNFROZEN.  
**Next:** MF7-G — Multiscale, Coupled, Emergent & Collective Dynamics.

---

# 0. Purpose

MF7-E separated natural invariance/stability from active regulation. MF7-F now asks:

> **What makes an influence genuinely control/intervention rather than merely another cause, disturbance, coupling or input? How do feedback, policy, authority, actuation, reachability and controllability change the evolution family?**

Dangerous collapses:

```text
Control = Cause
Control = Input
Control = Feedback
Control = Goal
Control = Optimization
Intervention = Observation
Intervention = Any Cause
Command = Actuation = Effect
Action = Transition
Policy = Dynamics
Policy = Plan
Feedback = Negative Feedback
Feedback = Stabilizing Feedback
Feedforward = Open Loop by identity
Regulation = Stability
Regulation = Conservation
Setpoint = Goal/Utility
Error Signal = Objective
Plant State = Controller State = Belief State
Plant Dynamics = Controller Dynamics = Closed-Loop Dynamics
Reachability = Controllability
Reachability = Feasibility
Controllability = Stabilizability
Observability = Controllability
Observable = Measurable
Stabilization = Natural Stability
Tracking = Regulation
Control Authority = Physical Causation
Allowed Command = Effective Action
```

---

# 1. Input is broader than control

A system can receive exogenous influences that no controller can choose: wind, ambient temperature, market shock, sensor interference, or another agent's action.

### SF-001
**Input ≠ Control.**

### SF-002
An input becomes a candidate control input only under an admissible-selection/access relation for some controller/system authority.

### SF-003
Disturbance and control can enter the same physical channel while differing in authority/selection role.

---

# 2. Cause is broader than control

A lightning strike can cause a transition without being under any system's control authority.

### SF-004
**Cause ≠ Control.**

### SF-005
Control effects are causal/influential in many realizations, but causal influence is not sufficient for control standing.

### SF-006
MF7-B `Dynamics ≠ Causality` remains intact.

---

# 3. Provisional ControlStanding — control firewall

MF7-F introduces:

```text
ControlStanding(U, Controller, Target | Model, Authority, Scope)
```

when a channel/action variable is non-arbitrarily available to a declared controller/system authority for selection from an admissible action set, and changes the admissible/weighted continuations of the target dynamics through a grounded actuation/effect route.

Compact:

```text
ControlStanding
 = Selectable Influence
 + Authority/Access
 + Admissible Action Set
 + Actuation/Effect Route
 + Evolution Relevance
 + Scope
```

### SF-007
**SelectableInfluence is constitutive; mere causal coupling is insufficient.**

### SF-008
Control standing does not require human consciousness or explicit symbolic goals.

### SF-009
Mechanical, biological and computational controllers can have operationally constituted control authority.

---

# 4. Authority means selectable access, not moral/legal authority by default

`Authority` here means the system/controller is permitted/capable, under the declared mechanics/protocol, to set/choose/trigger an action channel within some admissible set.

### SF-010
**ControlAuthority ≠ CausalPower universally.**

A disturbance may have large causal power yet no controller authority; a controller may have authority to issue a command whose actuator is currently ineffective.

### SF-011
Authority can be physical, protocol, institutional, software, biological or formal.

### SF-012
Authority scope can be partial, revocable, conditional and state-dependent.

---

# 5. Command is not actuation

A controller can emit a command that an actuator fails to realize.

### SF-013
**Command ≠ Actuation.**

### SF-014
Command standing is informational/decision output; actuation standing is the realized transformation at the influence interface.

### SF-015
A command can be valid but ineffective because of saturation, failure, permissions, latency or disconnected actuator.

---

# 6. Actuation is not target effect

An actuator can move but fail to achieve intended target change because target coupling is weak/blocked.

### SF-016
**Actuation ≠ TargetEffect.**

### SF-017
Control chain must preserve at least:

```text
Decision/Command → Actuation → Target Coupling → Target State/Output Effect
```

### SF-018
Each arrow can fail independently and needs evidence/provenance.

---

# 7. Action is not transition

An action may fail, be ignored, be canceled or have no state-changing consequence at the chosen abstraction.

### SF-019
**ActionOccurrence ≠ TargetTransitionOccurrence.**

### SF-020
One action can probabilistically induce several target continuations; one transition can arise from multiple possible actions/causes.

### SF-021
MF7-B `Cause ≠ Transition` survives.

---

# 8. Intervention is not observation

Pearl's intervention calculus explicitly distinguishes ordinary conditioning/observation from externally setting a variable.

### SF-022
**Observation ≠ Intervention.**

### SF-023
Observing `X=x` updates information; intervening to set `X=x` alters/overrides the relevant generation mechanism in the causal/model semantics.

### SF-024
Identical numerical values under observation and intervention can have different consequence distributions.

---

# 9. Intervention is broader/different from control action

An experimenter can intervene on a system without being its endogenous controller; an attacker can intervene; a maintenance operation can alter parameters or topology.

### SF-025
**Intervention ≠ Control by identity.**

### SF-026
Control is an authorized/selectable influence channel inside a declared control relation; intervention is a deliberate/external setting or mechanism modification relative to the model's ordinary evolution/generation route.

### SF-027
A control action may be represented as an intervention in a causal model, but the standing routes remain distinct.

---

# 10. Intervention can target state, input, parameter or dynamics

### SF-028
**Intervention ≠ StateAssignment only.**

An intervention may:

- set an input/action;
- reset state;
- clamp a variable;
- change a parameter;
- disable/replace a mechanism;
- alter topology/boundary;
- inject/remove resources.

### SF-029
Intervention target/type must be explicit.

---

# 11. Open-loop control proves feedback is not necessary for control

A predetermined control sequence can steer a system without using subsequent measured output to alter commands.

### SF-030
**Control ≠ Feedback.**

### SF-031
Open-loop control can have genuine ControlStanding if the sequence is selectable and acts through a grounded channel.

### SF-032
Feedback is an information-coupling architecture over control, not the definition of control itself.

---

# 12. Feedback standing

Provisional:

```text
FeedbackStanding(Y→C | Loop, Delay, Transformation, Scope)
```

when information/effect derived from downstream/system output or state is routed back to modify later upstream/controller/internal evolution.

### SF-033
**Feedback ≠ Control universally.**

### SF-034
Feedback can exist in uncontrolled ecological, financial, physical or social coupling loops.

### SF-035
Control feedback specifically requires feedback information to affect selectable control computation/action.

---

# 13. Maxwell governor hard case

Maxwell's `On Governors` analyzes mechanisms that keep machine velocity nearly uniform despite variations in driving power/resistance by mechanically sensing speed-related effects and modulating resistance/valves.

### SF-036
This is direct evidence that **regulation can arise from embodied feedback without a symbolic planner**.

### SF-037
Controller, sensor and actuator can be physically integrated rather than modular software components.

### SF-038
ControlStanding therefore cannot require explicit internal representation or conscious agency.

---

# 14. Negative feedback is not feedback by identity

### SF-039
**Feedback ≠ NegativeFeedback.**

Positive feedback/amplification loops are also feedback structures.

### SF-040
Sign/effect depends on system variables, loop gain, phase/delay and operating point rather than the word `feedback` alone.

---

# 15. Negative feedback does not guarantee stability

Maxwell's governor analysis already centers stability/oscillation conditions rather than assuming regulation mechanisms always work.

### SF-041
**NegativeFeedback ≠ StableClosedLoop.**

### SF-042
Delay, gain, phase, nonlinearities and actuator dynamics can destabilize a feedback loop.

### SF-043
Feedback architecture and MF7-E StabilityProfile are separate objects.

---

# 16. Feedback can destabilize or amplify

### SF-044
**FeedbackPresence ≠ ErrorReduction.**

### SF-045
A loop may reduce deviations, amplify them, oscillate, saturate or create new regimes.

### SF-046
Regulatory success is an empirical/model property of the closed loop.

---

# 17. Feedforward

Provisional feedforward control uses reference/disturbance/model information to select control without requiring the controlled output consequence to return through the same correction loop.

### SF-047
**Feedforward ≠ Feedback.**

### SF-048
Feedforward can coexist with feedback.

### SF-049
Feedforward ≠ open-loop by identity when downstream measurements/other loops also exist.

---

# 18. Rosenblueth–Wiener–Bigelow: purposeful behavior and feedback are related but not ontology identity

Their 1943 behavioristic framework classifies behavior by relations between input/output and discusses teleological/purposeful feedback behavior.

### SF-050
Historical cybernetic analysis supports feedback as a mechanism for goal-directed correction, but MF7 does **not** define every control process as purposeful agency.

### SF-051
`Goal-directed behavior` is a stronger functional/agency interpretation than mere control standing.

### SF-052
MF8 must decide agency/goal standing separately.

---

# 19. Policy standing

Provisional:

```text
PolicyStanding(π | InformationState, ActionSet, Context)
```

when a rule/distribution maps controller information/state/history/context to admissible control choices.

### SF-053
**Policy ≠ Dynamics.**

### SF-054
A policy selects actions; plant dynamics determines target response; controller dynamics may update internal state; closed-loop dynamics emerges from composition.

### SF-055
A static state-feedback law `u=π(x)` is one policy form, not universal policy ontology.

---

# 20. Policy is not plan

A plan can be an explicit future action sequence; a policy is a contingent mapping from information/state to choice.

### SF-056
**Policy ≠ Plan.**

### SF-057
An open-loop plan can be executed without state-contingent policy updates; a policy may never precompute a full trajectory.

---

# 21. Policy is not goal/utility

### SF-058
**Policy ≠ Objective/Utility.**

The same policy can arise from different objectives; one objective can admit multiple policies.

### SF-059
Policy behavior alone does not identify the optimizing criterion.

### SF-060
Value/utility/intent belongs to MF8/other foundations, not constitutive MF7 control ontology.

---

# 22. Controller state versus plant state

A dynamic controller can carry estimator/integrator/memory state distinct from the controlled plant.

### SF-061
**ControllerState ≠ PlantState.**

### SF-062
The controller may have access only to observations/beliefs, not true plant state.

### SF-063
MF7-A/C `TargetState ≠ BeliefState` remains essential.

---

# 23. Controller belief/state estimate versus controller state

An estimator belief may be part of controller state but not exhaust it; controller can also include integrators, modes, budgets or timers.

### SF-064
**BeliefState ≠ ControllerState universally.**

### SF-065
One controller state variable can be an estimate of plant state while another tracks actuator/resource state.

---

# 24. Plant dynamics versus controller dynamics

### SF-066
**PlantDynamics ≠ ControllerDynamics.**

The plant evolves under physical/system laws and control inputs; the controller evolves under its own computation/internal rules.

### SF-067
They are coupled subsystems with separate StateStanding and EvolutionStanding.

---

# 25. Closed-loop dynamics is a composition

Connecting controller output to plant input and plant observations back to controller creates a joint system.

### SF-068
**ClosedLoopDynamics ≠ PlantDynamics.**

### SF-069
**ClosedLoopDynamics ≠ ControllerDynamics.**

### SF-070
Closed-loop equilibrium/stability/attractors belong to the composed controller+plant+sensor+actuator boundary.

---

# 26. Stabilization versus natural stability

An unstable open-loop plant can be stabilized by feedback.

### SF-071
**StabilizedClosedLoop ≠ NaturallyStablePlant.**

### SF-072
MF7-E `ControlledSteadyCondition ≠ OpenLoopEquilibrium` is strengthened.

### SF-073
Removing controller can change the dynamics family and destroy the stability property.

---

# 27. Regulation standing

Provisional:

```text
RegulationStanding(TargetVariable/Set | Controller, Reference/ViabilityCriterion, Disturbances, Scope)
```

when control organization acts to maintain/return declared variables/conditions within a reference/acceptable set under disturbances/variation.

### SF-074
**Regulation ≠ Stability.**

### SF-075
Regulation is an active control objective/process; stability is a dynamical response property of the relevant closed/open loop.

### SF-076
Successful regulation often requires stability but they are not identical.

---

# 28. Regulation is not conservation

### SF-077
**Regulation ≠ Conservation.**

A regulator can expend energy/resources and continually compensate disturbances while keeping an output near a reference.

### SF-078
A conserved quantity needs no such active correction under the declared dynamics.

---

# 29. Reference/setpoint versus goal

A control reference `r(t)` specifies desired/tracked output/state under a control law.

### SF-079
**Setpoint/Reference ≠ Goal/Utility by identity.**

### SF-080
Reference can be externally supplied, arbitrary, safety-generated or one component of a broader objective.

### SF-081
A goal may be a set, trajectory, distribution or utility criterion rather than scalar setpoint.

---

# 30. Error signal versus objective

`e=r-y` is one control error representation.

### SF-082
**ErrorSignal ≠ Objective.**

### SF-083
Objective may penalize energy, constraints, risk, transient behavior or future outcomes not captured by instantaneous error.

### SF-084
Zero error can coexist with unacceptable control cost/resource use.

---

# 31. Tracking versus regulation

### SF-085
**Tracking ≠ Regulation by identity.**

Tracking commonly follows a varying reference trajectory; regulation commonly maintains/returns near a fixed/set-valued condition, but terminology is domain-dependent.

### SF-086
Both are control-performance profiles, not foundational state categories.

---

# 32. Control action can change reachable futures without changing current state instantly

A command may alter actuator mode/parameter or future input schedule before visible plant state moves.

### SF-087
**ControlEffect ≠ ImmediateStateChange.**

### SF-088
Control standing concerns evolution relevance, including future admissible continuations.

---

# 33. Reachability standing

Provisional:

```text
Reachable(x_target | x0, Dynamics, AdmissibleControls, Horizon, Constraints)
```

when there exists at least one admissible control/input evolution taking the system from the initial condition/class to the target condition/set under declared dynamics and constraints.

### SF-089
**Reachability is existential and relation-specific.**

### SF-090
Bare `reachable` without initial/target/horizon/control/constraint semantics is incomplete.

---

# 34. Reachability is not generic adjacency

### SF-091
**Reachability ≠ OneStepTransition/Adjacency.**

A target may require many control actions/transitions; adjacent states may be unreachable under actuation constraints.

### SF-092
MF7-B reachability separation survives.

---

# 35. Reachability is not feasibility under resources

A mathematical model may allow a control of arbitrarily large magnitude, while real actuator limits forbid it.

### SF-093
**NominalReachability ≠ Resource/ConstraintFeasibility.**

### SF-094
Feasibility needs actuator bounds, energy/fuel, time, risk, safety, authority and state constraints.

### SF-095
Resource model is first-class in operational control claims.

---

# 36. Controllability is stronger/system-level and definition-dependent

Kalman's state-space/control theory formalizes controllability as a system property concerning the ability of admissible controls to transfer states over specified intervals/conditions; exact conventions vary (reach from origin, to origin, arbitrary state-to-state, complete controllability).

### SF-096
**Controllability ≠ Reachability by universal definition.**

### SF-097
Reachability is a relation/query for specific initial-target conditions; controllability is typically a property of a system/state subspace under a declared convention.

### SF-098
MF7 must always attach the exact controllability definition used.

---

# 37. Kalman hard case: uncontrollable internal modes can exist

Kalman's 1963 state-space work distinguishes controllable and observable portions of a realization; input/output relations identify only the completely controllable/observable part of certain linear realizations.

### SF-099
**Presence of an input channel ≠ full state controllability.**

### SF-100
A control may influence some state subspace while leaving other modes unreachable.

### SF-101
ControlAuthority over a channel ≠ Controllability of the whole target.

---

# 38. Controllability is not observability

### SF-102
**Controllability ≠ Observability.**

Controllability concerns influence through admissible inputs; observability concerns inference/distinguishability of internal state from outputs over time.

### SF-103
A system can be controllable but poorly observable, or observable but uncontrollable.

### SF-104
Kalman's theory treats them as dual/distinct structural properties, not synonyms.

---

# 39. Observable is not directly measurable

A hidden state can be inferred over time from output dynamics even if no sensor directly measures that variable.

### SF-105
**Observable ≠ DirectlyMeasured.**

### SF-106
Measurement is an evidence channel; observability is a model/system identifiability property across histories/outputs.

---

# 40. Controllability is not stabilizability

A system can have uncontrollable modes that are already stable, allowing the full system to be stabilized even though not every state direction is controllable.

### SF-107
**Stabilizability ≠ Controllability.**

### SF-108
Stabilizability asks whether unstable/problematic modes can be rendered stable by available control.

### SF-109
Full arbitrary state transfer is a stronger/different requirement.

---

# 41. Detectability is not observability

Analogously, unobservable modes may be harmless if stable/decaying for estimation/control purposes.

### SF-110
**Detectability ≠ Observability.**

### SF-111
Control/estimation adequacy can be weaker than complete structural controllability/observability.

---

# 42. Reachable set

```text
R(x0,T,U,C)
```

is a set of target states reachable under declared horizon/control/constraints.

### SF-112
**ReachableSet ≠ BasinOfAttraction.**

### SF-113
A reachable set is control/action conditioned; a basin is natural/closed-loop attraction under a fixed dynamics/policy profile.

### SF-114
MF7-E basin distinction survives.

---

# 43. Viability/safety is not reachability

A target can be reachable only by passing through forbidden states.

### SF-115
**Reachable ≠ SafelyReachable/Viable.**

### SF-116
State/path constraints define a stricter feasible controlled set.

### SF-117
Control claims should preserve path constraints, not only endpoint existence.

---

# 44. Minimum-time/energy control adds optimization, not control ontology

### SF-118
**Control ≠ OptimalControl.**

### SF-119
Optimal control adds an objective/cost ordering over admissible controls/trajectories.

### SF-120
A nonoptimal but effective control remains control.

---

# 45. Cost is not feasibility

### SF-121
**LowCost ≠ Feasible and Feasible ≠ Optimal.**

An action can be feasible but expensive; infeasible actions should not be treated as candidates merely because a mathematical cost function ranks them.

### SF-122
Resource/constraint and preference/objective layers must remain separate.

---

# 46. State feedback versus output feedback

State feedback assumes access to state/estimate; output feedback uses available observations and may require controller memory/estimation.

### SF-123
**StateFeedback ≠ OutputFeedback.**

### SF-124
Partial observability can require dynamic controller state.

### SF-125
Controller architecture changes closed-loop state dimension/dynamics.

---

# 47. Feedback signal can be stale/delayed/noisy

### SF-126
**FeedbackInformation ≠ CurrentTrueState.**

### SF-127
Delay, sampling, quantization, noise and estimation errors are part of FeedbackProfile.

### SF-128
Feedback can reduce performance or destabilize if temporal/error properties are unfavorable.

---

# 48. Controller internal memory can create closed-loop dynamics

Integral control accumulates past error, filters carry internal state, adaptive controllers update parameters.

### SF-129
**Controller ≠ MemorylessPolicy universally.**

### SF-130
Controller state belongs to the closed-loop state under the enlarged system boundary.

### SF-131
MF7-C history/state augmentation applies directly.

---

# 49. Feedback loop itself can be open to environment

Sensors, actuators and communication links have external disturbances/resources.

### SF-132
**ClosedLoop ≠ ClosedSystem.**

### SF-133
`closed loop` describes feedback interconnection, not thermodynamic/informational environmental closure.

---

# 50. Control can be decentralized/distributed

Multiple controllers can share/compete over target channels with partial information.

### SF-134
**Controller ≠ SingleCentralController.**

### SF-135
Control authority can be partitioned, overlapping or conflicting.

### SF-136
Joint closed-loop dynamics can depend on communication topology and strategic interactions.

---

# 51. Competing controllers hard case

Two agents/controllers can issue incompatible actions to one target.

### SF-137
**ControlAuthority ≠ GuaranteedFinalEffect.**

### SF-138
Arbitration, priority, physical dominance or protocol composition determines effective actuation.

### SF-139
MF8 Agency/game/social foundations will later type strategic control.

---

# 52. Control authority can be conditional

Safety interlocks, permissions, modes or state-dependent constraints can disable an otherwise available actuator.

### SF-140
**ControlSet U can depend on state/context/authority.**

### SF-141
Reachability/controllability must use effective admissible control sets rather than nominal command vocabularies.

---

# 53. Saturation hard case

An actuator command beyond limits clips/saturates.

### SF-142
**CommandSpace ≠ EffectiveActuationSpace.**

### SF-143
Linear unconstrained controllability results do not automatically transfer to constrained actuator reality.

### SF-144
Control capability is resource/envelope dependent.

---

# 54. Dead zone/backlash/hysteresis hard cases

The same command can have no effect or history-dependent effect.

### SF-145
**CommandValue ≠ ActuationEffect by identity.**

### SF-146
Actuator internal state can be required in closed-loop StateProfile.

### SF-147
MF7-C hysteresis/history dependence applies to control channels.

---

# 55. Delayed control can change reachable/stable sets

### SF-148
**ControlAvailabilityNow ≠ TimelyControlCapability.**

### SF-149
Deadline/latency can make an otherwise powerful actuator operationally useless for a task.

### SF-150
MF6 ActionTime/deadline/latency profiles are consumed by control feasibility.

---

# 56. Authority without observability

A controller may be able to actuate state dimensions it cannot accurately observe.

### SF-151
**ActuationAuthority ≠ StateKnowledge.**

### SF-152
Control and perception/estimation channels are independent resources that couple in closed-loop performance.

---

# 57. Observability without authority

An observer can perfectly know target state but have no actuator/control rights.

### SF-153
**Knowledge ≠ Control.**

### SF-154
This is a direct firewall against `measurement/understanding = ability to act`.

---

# 58. Intervention evidence versus intervention effect

An audit/log can record that a command/intervention was requested.

### SF-155
**InterventionRecord ≠ InterventionOccurrence ≠ TargetEffect.**

### SF-156
Provenance must distinguish request, authorization, execution, actuation and effect.

---

# 59. Counterfactual control diagnostic

Hold plant state/context fixed and vary only an authorized control choice within admissible actions.

### SF-157
If admissible future law/reachable set changes through the declared actuator route, this supports ControlStanding.

### SF-158
If varying the nominal `control` variable cannot affect target continuations, it is not an effective control channel under that scope.

---

# 60. De-authorize diagnostic

Keep physical coupling but remove selectable authority/access.

### SF-159
If the influence becomes an exogenous disturbance/input rather than a selectable action, control standing depended on authority rather than causation alone.

---

# 61. Disconnect actuator diagnostic

Keep policy/commands but break command→actuator/plant coupling.

### SF-160
If controller decisions no longer alter target continuations, **policy existence alone does not establish target control effectiveness**.

---

# 62. Freeze policy diagnostic

Hold a policy fixed while perturbing plant dynamics.

### SF-161
Same policy can yield different closed-loop behavior under different plant dynamics.

### SF-162
**Policy ≠ ClosedLoopDynamics.**

---

# 63. Swap controller diagnostic

Hold plant fixed while changing controller/policy.

### SF-163
Closed-loop dynamics/attractors/reachability can change even though plant open-loop dynamics is unchanged.

### SF-164
This is direct evidence for layered dynamics standing.

---

# 64. Observation versus intervention causal hard case

Pearl's 1995 calculus uses separate operators for ordinary conditioning and external setting/intervention.

### SF-165
Statistical association under observation is not generally equal to the distribution under intervention.

### SF-166
Control decisions based on causal effect need intervention/structural assumptions beyond observational correlation.

### SF-167
MF7-F does not otherwise absorb the full causal-inference ontology.

---

# 65. Reference changes can be exogenous commands, not goal changes

A supervisor can change setpoint from 20°C to 22°C while the broader goal `comfort/safety` remains.

### SF-168
**ReferenceChange ≠ Utility/GoalChange by identity.**

### SF-169
Reference provenance/authority must be typed.

---

# 66. Regulation can target a set rather than point

### SF-170
**RegulatoryTarget ≠ ScalarSetpoint universally.**

Targets can be safe sets, invariant regions, trajectories, distributions, constraints or temporal profiles.

### SF-171
This aligns with MF7-E homeostatic bands/regime stability.

---

# 67. Safety control can override performance control

### SF-172
Multiple control criteria can conflict and be hierarchically arbitrated.

### SF-173
**OneController ≠ OneObjective.**

### SF-174
Control authority can be layered: supervisory safety controller can restrict lower-level action set.

---

# 68. Control can alter dynamics parameters, not only state

Adaptive/switching/supervisory control may change gains/modes/rules.

### SF-175
**ControlEffect ≠ StateTransitionOnly.**

### SF-176
A control action can alter the subsequent EvolutionStanding/profile itself within a higher-level dynamics.

### SF-177
Dynamics-change intervention and state-control action must be distinguished.

---

# 69. Learning is not control

Learning updates a model/policy/representation from data; control selects/actions on the target.

### SF-178
**Learning ≠ Control.**

### SF-179
Learning can improve future control but can occur offline with no target actuation.

### SF-180
Control can operate with a fixed nonlearning policy.

---

# 70. Adaptation is not learning by identity

A controller can adapt parameters by fixed update rules without acquiring a general predictive model.

### SF-181
**Adaptation ≠ Learning universally.**

### SF-182
Both can change controller dynamics/policy over time.

---

# 71. Control and agency boundary

Control standing requires selectable influence relative to a controller authority, but does not yet require preferences, self-originated goals, responsibility or consciousness.

### SF-183
**Control ≠ Agency.**

### SF-184
A thermostat/controller has control standing without settling whether it has AgencyStanding.

### SF-185
MF8 must add goal/value/choice/self/world-model/action-ownership criteria if needed.

---

# 72. Regulation can be endogenous without a separate controller object

Biological regulatory networks can distribute sensing/actuation across the same physical substrate.

### SF-186
**Controller ≠ NecessarilyDistinctComponent.**

### SF-187
Controller/plant decomposition is boundary/model-relative.

### SF-188
ControlStanding can be relationally distributed across coupled processes.

---

# 73. Controller/plant decomposition is not unique

A motor's low-level electronics may be considered part of actuator, controller or plant depending modeling boundary.

### SF-189
**Plant/Controller labels are role assignments under a model boundary, not intrinsic material categories.**

### SF-190
Closed-loop predictions must preserve the chosen decomposition/provenance.

---

# 74. Control effectiveness is task/horizon relative

A weak actuator may control slow long-horizon drift but not reject fast disturbances.

### SF-191
**ControlCapability requires horizon/task/precision profile.**

### SF-192
Binary `has control` can be too coarse even when channel standing exists.

---

# 75. Approximate reachability/control

Exact state transfer can be impossible while approximate transfer within tolerance is feasible.

### SF-193
**ExactReachability ≠ ApproximateReachability.**

### SF-194
Tolerance/equivalence must be declared, especially in continuous/high-dimensional systems.

---

# 76. Probabilistic reachability/control

Under stochastic dynamics, control changes probability distributions over target events/states.

### SF-195
**StochasticControl ≠ DeterministicStateTransfer.**

### SF-196
Reachability can be probability-thresholded/chance-constrained rather than existential certainty.

### SF-197
MF7-C uncertainty source/type remains active.

---

# 77. Adversarial/game reachability

Under nondeterministic/adversarial environment, one can distinguish:

- exists a control path if environment cooperates;
- a policy guarantees target against all allowed disturbances;
- target reached with probability threshold.

### SF-198
**ExistentialReachability ≠ GuaranteedControllability.**

### SF-199
Quantifier order over controller/environment choices is first-class.

### SF-200
This will bridge later Agency/Game foundations.

---

# 78. Control privilege versus capability

A system may have permission to issue commands but insufficient actuator power; or physical capability but no authorized protocol route.

### SF-201
**Authority ≠ Capability.**

### SF-202
Operational control requires both admissible authority/access and effective influence capability.

### SF-203
Security/governance can alter authority without changing physical plant dynamics.

---

# 79. Control capability versus option

Having an actuator creates possible actions; actual command selection creates one action occurrence.

### SF-204
**ControlCapability/Option ≠ ControlActionOccurrence.**

### SF-205
Available action set, selected action and realized effect are distinct stages.

---

# 80. Provisional ControlProfile

```text
ControlProfile = <
  Controller/Bearer,
  Target/Plant Boundary,
  ControlStanding,
  Authority/Access,
  Action/Command Set,
  State/Context Dependence of Action Set?,
  Policy/DecisionRule?,
  ControllerState?,
  PlantState/Belief/Observation Access?,
  Actuator/Effect Route,
  Delays/Saturation/Failures?,
  Disturbances/Environment,
  Objective/Reference/Constraint?,
  Horizon/Timing,
  Reachability/Controllability/Stabilizability?,
  Resource/Cost/Safety Envelope?,
  Uncertainty,
  Evidence/Provenance,
  Scope
>
```

### SF-206
Bare `controller controls X` is under-specified.

---

# 81. Provisional FeedbackProfile

```text
FeedbackProfile = <
  SourceOutput/StateEstimate,
  Measurement/Observation Route,
  FeedbackTransformation,
  DestinationController/System,
  Delay/Sampling/Noise,
  Sign/Gain/Phase?,
  ControllerState/Memory?,
  ActionCoupling?,
  ClosedLoopBoundary,
  Stability/Performance Evidence,
  Uncertainty,
  Provenance,
  Scope
>
```

### SF-207
`feedback=true` does not assert negative/stable/control feedback.

---

# 82. Provisional InterventionProfile

```text
InterventionProfile = <
  InterveningAuthority/Source,
  TargetVariable/Mechanism/Boundary,
  InterventionType : set/clamp/reset/disable/replace/parameter/topology/etc.,
  OrdinaryGenerationRouteOverridden?,
  Value/Action,
  Duration/Timing,
  Actuation/Implementation,
  TargetEffect,
  CausalModelSemantics?,
  ControlRelation?,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### SF-208
Intervention and control remain distinct typed fields.

---

# 83. Provisional RegulationProfile

```text
RegulationProfile = <
  ControlledVariable/Condition/Set,
  Reference/ViabilityCriterion,
  Controller/RegulatoryMechanism,
  Plant/Target,
  Feedback/Feedforward Structure,
  DisturbanceClass,
  AllowedDeviation,
  Recovery/Tracking Profile,
  Resource/Actuator Limits,
  ClosedLoop Stability?,
  Failure/Saturation Modes?,
  Uncertainty,
  Provenance,
  Scope
>
```

### SF-209
Regulation quality is typed, not one scalar.

---

# 84. Provisional ReachabilityControlProfile

```text
ReachabilityControlProfile = <
  System/Dynamics,
  InitialSet,
  TargetSet,
  Horizon,
  AdmissibleControlSet,
  ControllerInformation?,
  Disturbance/Adversary Quantifiers?,
  State/Path Constraints,
  Resource/Cost Limits,
  Exact/Approximate/Probabilistic Criterion,
  ReachableSet?,
  ControllabilityConvention?,
  Stabilizability/Viability?,
  Certificate/Algorithm?,
  Evidence/Model Provenance,
  Uncertainty,
  Scope
>
```

### SF-210
`controllable=true` without convention/constraints is under-specified.

---

# 85. Strongest non-collapse stack after MF7-F

```text
Cause
 ≠ Input
 ≠ Control
```

```text
ControlStanding
 ≠ ControlActionOccurrence
 ≠ TargetEffect
```

```text
Command
 ≠ Actuation
 ≠ Effect
```

```text
Observation
 ≠ Intervention
```

```text
Intervention
 ≠ Control by identity
```

```text
Control
 ≠ Feedback
 ≠ NegativeFeedback
```

```text
NegativeFeedback
 ≠ StableClosedLoop
```

```text
Feedback
 ≠ Regulation
```

```text
Policy
 ≠ Dynamics
 ≠ Plan
 ≠ Objective
```

```text
PlantState
 ≠ ControllerState
 ≠ BeliefState
```

```text
PlantDynamics
 ≠ ControllerDynamics
 ≠ ClosedLoopDynamics
```

```text
Regulation
 ≠ Stability
 ≠ Conservation
```

```text
Reference/Setpoint
 ≠ Goal/Utility
```

```text
ErrorSignal
 ≠ Objective
```

```text
Reachability
 ≠ Controllability universally
 ≠ Feasibility
```

```text
Controllability
 ≠ Stabilizability
 ≠ Observability
```

```text
Observable
 ≠ DirectlyMeasured
```

```text
Basin
 ≠ ReachableSet
```

```text
Control
 ≠ OptimalControl
 ≠ Learning
 ≠ Agency
```

---

# 86. Claims rejected by MF7-F

Reject as universal/foundational:

- every cause/input is control;
- control requires conscious agent or explicit symbolic goal;
- command, actuation and target effect are identical;
- action occurrence equals target transition;
- observation and intervention are interchangeable;
- every intervention is an endogenous control action;
- control requires feedback;
- feedback means negative feedback;
- negative feedback guarantees stability/error reduction;
- feedforward means absence of every feedback loop;
- policy is dynamics/plan/objective;
- plant state, controller state and belief state are one state;
- plant/controller/closed-loop dynamics are identical;
- regulation is stability or conservation;
- setpoint is goal/utility;
- error signal is the objective;
- reachability and controllability are universal synonyms;
- mathematical reachability implies physical/resource/safety feasibility;
- an input channel implies full controllability;
- controllability equals observability/stabilizability;
- observable means directly measurable;
- open-loop instability and closed-loop stabilization are contradictory;
- controller is necessarily a distinct centralized component;
- nominal command set equals effective actuator capability;
- authority implies capability/effect;
- optimization/learning/agency is constitutive of control.

---

# 87. Primary/authoritative anchors

- **James Clerk Maxwell (1868), `On Governors`, Proceedings of the Royal Society.** Analyzes mechanical regulators that maintain nearly uniform machine speed against drive/load variation and investigates conditions for stability/oscillation. Anchors embodied feedback regulation, `feedback ≠ guaranteed stability`, and control without symbolic planner.
- **Arturo Rosenblueth, Norbert Wiener & Julian Bigelow (1943), `Behavior, Purpose and Teleology`, Philosophy of Science 10(1):18–24.** Classifies input/output behavior and emphasizes negative feedback in teleological/purposeful behavior. Useful historical anchor while MF7 keeps control distinct from full agency/purpose ontology.
- **R. E. Kalman (1963), `Mathematical Description of Linear Dynamical Systems`, J. SIAM Series A Control 1(2):152–192.** Distinguishes state-variable and input/output descriptions and uses controllability/observability to characterize realizations. Anchors `input ≠ full controllability`, `controllability ≠ observability`, and controller/plant state-space discipline.
- **R. E. Kalman, Y. C. Ho & K. S. Narendra (1963), `Controllability of Linear Dynamical Systems`, Contributions to Differential Equations 1:189–213.** Foundational systematic controllability analysis; anchors controllability as a system/state-space property rather than one realized action or reachability anecdote.
- **Judea Pearl (1995), `A Causal Calculus for Statistical Research` and `Causal Diagrams for Empirical Research`.** Explicitly distinguishes ordinary observational conditioning from externally setting/intervening on a variable, anchoring `Observation ≠ Intervention`.

---

# 88. Deep reconstruction

Naive model:

```text
X affects system
    ↓
X is an input
    ↓
X controls system

controller observes y
    ↓
feedback exists
    ↓
system is stable/regulating

some path reaches target
    ↓
system is controllable
```

MF7-F replaces it with:

```text
Target/Plant Dynamics
        │
        ├── exogenous coupled causes/disturbances
        │
        └── selectable influence channel
                    │
              Authority/Access
                    │
              Admissible Action Set
                    │
          Decision/Policy/Command
                    │
                Actuation
                    │
            Target Coupling/Effect
                    │
                    ▼
             Modified Evolutions

Observation/estimate ──> controller information
          │                    │
          └──── feedback ──────┘

Plant + Sensor + Controller + Actuator
                 │
                 ▼
          ClosedLoopDynamics
                 │
       ┌─────────┼──────────┐
       ▼         ▼          ▼
  regulation  stabilization tracking

Separately:
Reachability = exists admissible controlled path for a query.
Controllability = system-level transfer capability under a convention.
Feasibility = reachability plus real constraints/resources/authority.
```

The decisive move is:

> **Control is not causation and not input. It is selectable, authorized, evolution-relevant influence through an effective actuation route. Feedback is a loop architecture that can inform control but can also occur without control and can destabilize. Regulation/stabilization are closed-loop performance properties. Reachability and controllability describe what the controlled dynamics can achieve, but only relative to action sets, horizons, information, disturbances, resources and constraints.**

---

# 89. Deepest MF7-F result

Provisional:

> **A system has control standing over a target only where some influence channel is genuinely available for conditional selection by a declared controller/authority and that selection can alter the target's admissible or weighted future continuations through a grounded actuation/effect route. Control therefore differs from generic cause, input, observation, intervention, feedback, policy and goal. Connecting controller and plant creates a new closed-loop dynamics whose stability, regulation and attractors need not match the plant's open-loop properties. Reachability asks whether particular target conditions can be attained under admissible actions; controllability is a stronger/system-level property whose exact convention must be declared; practical capability additionally depends on information, timing, resource, safety, authority and actuator constraints.**

Compact:

```text
Input enters.
Cause influences.
Control is selectable influence.
Command requests.
Actuation realizes influence.
Effect changes target evolution.
Feedback returns consequences/information.
Policy chooses controls from information.
Closed loop composes controller + plant.
Regulation maintains a declared condition.
Reachability asks what can be attained.
Controllability asks how much of state/evolution is steerable.
Feasibility asks what remains achievable under real constraints.
```

---

# 90. MF7-A→E audit

## MF7-A State
Survives. Plant/controller/belief states are distinct standing routes; control channels can be state-dependent.

## MF7-B Dynamics
Survives and strengthens. Control modifies/selects among continuations but policy/action ≠ dynamics; closed-loop composition yields a new EvolutionStanding.

## MF7-C Stochasticity/Markov
Survives. Stochastic/adversarial/nondeterministic control require typed continuation/quantifier semantics; controller memory can augment closed-loop state.

## MF7-D Identity
Survives. Controller/plant/service identity can persist/change independently of control capability and regime; authority can move between tokens.

## MF7-E Stability
Survives. Regulation/stabilization are active/control-conditioned, distinct from natural invariance/stability. Robustness/resilience must include actuator/resource authority where relevant.

### SF-211
**MF7-F triggers no restart of MF7-A→E.**

---

# 91. Earlier-foundation audit

- **MF6 Time:** control deadlines, delay, horizon and feedback latency consume Time profiles but do not redefine Time; no reopen.
- **MF5 Space:** actuator reach/workspace/reachable-set geometry does not make control state space physical space by default; no reopen.
- **MF4 Composition:** closed-loop dynamics is explicit composition of plant/controller/sensor/actuator; no reopen.
- **MF3 Representation:** commands, state estimates, references and intervention records can represent target/control state without being target effect; no reopen.
- **MF2 Perception:** observation/measurement informs controller but does not equal target state/control; no reopen.

### SF-212
**MF0–MF6 remain FROZEN; MF7-F triggers no concrete earlier FoundationReopenCondition.**

---

# 92. MF7-G handoff

Next round should attack whether subsystem-level states/dynamics compose straightforwardly into system-level behavior:

```text
Coupling
Interaction
Network Dynamics
Collective State
Synchronization
Coordination
Emergence
Macro/Micro Dynamics
Coarse Graining
Effective Dynamics
Order Parameter
Collective Mode
Distributed Process
Network Topology
Cascade
Propagation
Criticality
Self-Organization
Pattern Formation
Collective Control
```

Central attacks:

```text
JointDynamics ≠ SumOfSubsystemDynamics
Coupling ≠ Control
Synchronization ≠ SameState
CollectiveState ≠ ConcatenatedMicrostate by necessity
MacroDynamics ≠ MicroDynamics
Emergence ≠ Mystery/NewLaw by naming
OrderParameter ≠ SystemState universally
NetworkTopology ≠ Dynamics
InteractionGraph ≠ Causal/Temporal History
Coordination ≠ Synchronization
SelfOrganization ≠ Agency
CollectiveBehavior ≠ SharedGoal
```

Central question:

> **When do interacting stateful dynamical systems acquire legitimate higher-level state/evolution standing that cannot be captured by treating components independently, and how do coarse variables inherit or fail to inherit dynamics?**

**Next: MF7-G — Multiscale, Coupled, Emergent & Collective Dynamics.**
