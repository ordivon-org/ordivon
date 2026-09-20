# Ordivon Media Foundations — MF5-F Action, Configuration, Navigation & Reachability Space

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 28 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4 Composition Foundations v1 frozen; MF5-A→E complete and provisional.  
**Status:** MF5-F complete and PROVISIONAL. Space Foundations remain UNFROZEN.  
**Next:** MF5-G — Representational, Map, Diagram & Virtual Space.

---

# 0. Purpose

MF5-E showed that perceptual/body-centered space cannot be reduced to physical geometry. MF5-F asks the next question:

> **What makes a spatial relation action-relevant, and when should possible configurations, reachable states, navigation structure, costs and affordances be treated as distinct spatial organizations rather than as ordinary physical distance?**

The dangerous collapses are:

```text
Physical Space = Configuration Space = State Space = Action Space
Configuration = State
Connected = Reachable = Controllable
Instantaneous Motion Direction = Eventual Reachability
Near = Easy To Reach
Shortest Euclidean Distance = Shortest Feasible Path = Least Cost = Fastest Path
Free = Empty
Obstacle = Occupant
Reachable = Afforded
Possible Action = Chosen Action
Navigation Graph = Physical Geometry
Place/Grid/Head-Direction Code = One Cartesian Neural Map
```

MF5-F uses configuration-space planning, nonholonomic systems, optimal control, affordance experiments and spatial-navigation neurophysiology as falsifiers.

---

# 1. Physical space and configuration space are different domains

A physical workspace describes physical locations/regions/bodies.
A configuration space describes possible configurations of a system, often including position, orientation and joint degrees of freedom.

Lozano-Pérez's 1983 formulation explicitly maps object position/orientation to a single point in configuration space, one coordinate per degree of freedom.

### SF-01

**Physical point/location ≠ configuration-space point.**

### SF-02

**One configuration can encode the pose/state of an extended physical body, not one material point.**

---

# 2. Configuration space is system-relative

LaValle defines a robot's C-space from the set of transformations/configurations available to that robot; its dimension generally follows the robot's degrees of freedom.

### SF-03

**Configuration space is indexed to a configured system/model, not intrinsic to the environment alone.**

### SF-04

Two agents/bodies in one physical environment may have different configuration spaces.

---

# 3. C-space obstacle regions are derived relationally

Physical obstacles induce forbidden configurations depending on body shape, orientation, kinematic structure and collision criterion.

### SF-05

**World obstacle ≠ C-space obstacle region.**

### SF-06

**C-space obstaclehood is a relation among body geometry, environment and configuration model.**

This strengthens MF5-D.

---

# 4. C-free is not physical emptiness

```text
C_free = C \ C_obs
```

means allowed/noncolliding configurations under the model.

### SF-07

**Configuration-free ≠ physically empty.**

### SF-08

A physically empty region can correspond to unreachable/forbidden configurations; a physically occupied/shared world region can still permit some configurations/actions.

---

# 5. Configuration space is a special state space, not all state space

For purely kinematic planning, configuration `q` may be enough.
For dynamics, velocity/momentum/internal variables can matter, so one uses a larger state or phase space.

LaValle explicitly distinguishes C-space from phase/state space when differential/dynamic constraints are present.

### SF-09

**Configuration ≠ full dynamical state.**

### SF-10

**State space may include configuration plus velocity and other variables required to predict action consequences.**

---

# 6. Same configuration can have different action possibilities

A vehicle at the same position/orientation but with different velocities may have different stopping ability, future reachable sets and collision outcomes.

### SF-11

**Same configuration ≠ same reachable set.**

### SF-12

**Action possibility is state-dependent, not position-only.**

---

# 7. Region of inevitable collision is the decisive state-space hard case

LaValle defines an inevitable-collision region `X_ric`: states from which collision eventually occurs regardless of applied actions.

At one physical position/configuration, a low-speed state may remain avoidable while a high-speed state may be doomed because stopping/turning is impossible in time.

### SF-13

**Collision inevitability is a state/action-dynamics relation, not a pure occupancy relation.**

### SF-14

**Obstacle region `X_obs` ≠ inevitable-collision region `X_ric`.**

### SF-15

A noncolliding current configuration can already be action-doomed.

---

# 8. Action space is not automatically spatial

In planning/control, an action set `U(x)` denotes actions admissible at state `x`.
These may be steering commands, forces, discrete choices, communication acts or termination actions.

### SF-16

**Action set/space ≠ spatial domain by linguistic default.**

### SF-17

An action domain has MF5 spatial standing only when its structure genuinely encodes spatially organized transformations/configurations/relations, not merely because actions are parameter vectors.

---

# 9. Action, transition and trajectory are different

Let:

```text
u ∈ U(x)
xdot = f(x,u)
```

An action/control input influences a state transition; a trajectory is the resulting state history under actions and dynamics.

### SF-18

**Action ≠ state transition ≠ state trajectory.**

### SF-19

The same action value can produce different spatial consequences in different states.

---

# 10. Path and trajectory must remain separate

A path can denote an ordered geometric curve through configurations/states without explicit timing.
A trajectory normally carries time/dynamics/action realization.

### SF-20

**Geometric path ≠ dynamically feasible trajectory.**

### SF-21

A collision-free geometric path may be impossible to execute under velocity, acceleration, curvature, nonholonomic or control constraints.

---

# 11. Connectivity is weaker than reachability

A state/configuration domain may be topologically/path connected while the system cannot follow arbitrary local directions because of dynamics/differential constraints.

### SF-22

**Connected ≠ reachable.**

### SF-23

**Path existence in the underlying manifold ≠ feasible controlled trajectory existence.**

---

# 12. Reachability is directed, state- and action-model-relative

LaValle defines the reachable set from `x0` as states visited by trajectories generated by permissible action histories from `x0`.

Provisionally:

```text
Reach(x0 | U, f, constraints, horizon)
```

### SF-24

**Reachability is indexed to initial state, admissible actions, transition dynamics, constraints and often time horizon.**

### SF-25

`Reachable(x,y)` need not imply `Reachable(y,x)`.

---

# 13. Time-limited reachability differs from eventual reachability

A state may be reachable eventually but not within deadline `T`.

### SF-26

**Eventually reachable ≠ reachable within T.**

### SF-27

Temporal horizon is part of action-space semantics even though MF6 will later provide the full Time ontology.

---

# 14. Backward reachability is not merely forward reachability reversed

Backward reachable sets ask which starting states can reach a target under the declared dynamics/actions.
For irreversible/asymmetric systems, forward and backward structures differ.

### SF-28

**Forward-reachable and backward-reachable regions are distinct profiles.**

---

# 15. Instantaneous feasible directions do not determine eventual reachability trivially

Nonholonomic systems can lack direct velocity in one direction yet achieve net motion through sequences of controls.

A car cannot instantaneously slide sideways, but parallel-parking maneuvers can produce net lateral displacement.

### SF-29

**Instantaneous mobility distribution ≠ finite-horizon reachable set.**

### SF-30

**Missing one direct velocity direction does not imply the corresponding finite displacement is unreachable.**

---

# 16. Lie-bracket/parking hard case

LaValle's nonholonomic examples show how composed motion primitives can produce effective displacement in a direction unavailable instantaneously.

### SF-31

**Action composition can create effective spatial directions absent from individual primitive actions.**

### SF-32

**Action-space geometry is therefore path/composition sensitive.**

---

# 17. Reachability and controllability are not synonyms

Reachability is a relation/set from a starting condition under specified actions/horizon.
Controllability is a stronger system property asserting suitable ability to transfer among states under a chosen formal definition.

Kalman's 1960 control-system work made controllability a central systems concept; later nonlinear/nonholonomic theory generalizes beyond linear rank tests.

### SF-33

**Reachability claim ≠ controllability property.**

### SF-34

Controllability must state domain, locality/horizon and model assumptions.

---

# 18. Small-time local controllability is stronger than eventual global reachability

LaValle's simple-car comparison is decisive:

- the Dubins car, moving only forward with bounded turning, can reach any configuration in a sufficiently large obstacle-free plane;
- but it is not small-time locally controllable;
- a Reeds–Shepp car allowed to reverse has stronger local maneuverability/STLC.

### SF-35

**Global eventual reachability ≠ local maneuverability.**

### SF-36

**Controllability profile can change by adding/removing one action primitive such as reverse gear while physical space remains unchanged.**

---

# 19. Obstacles make local controllability especially important

A system that is globally reachable in open space may fail in narrow clutter because it cannot execute the maneuvering room required by its dynamics.

### SF-37

**Open-space reachability ≠ obstacle-constrained reachability.**

### SF-38

**Clearance requirements belong to agent/system action geometry, not environment geometry alone.**

---

# 20. Same endpoints do not determine shortest feasible motion

Dubins' 1957 bounded-curvature problem fixes positions and tangents/headings; shortest feasible curve depends on curvature constraint and endpoint orientation, not simply Euclidean endpoint distance.

### SF-39

**Endpoint Euclidean distance ≠ shortest feasible path length.**

### SF-40

**Orientation/configuration constraints can alter optimal path even when physical start/end positions are unchanged.**

---

# 21. Reeds–Shepp shows action repertoire changes optimal geometry

Reeds & Shepp 1990 allow forward and reverse movement for a curvature-bounded car and derive a different finite family of shortest-path candidates with reversals/cusps.

### SF-41

**Changing allowed actions changes the induced action-distance/geodesic structure.**

### SF-42

**Action geometry is agent/action-model relative even over the same physical plane.**

---

# 22. `Distance` induced by optimal control may fail metric axioms

LaValle notes that ideal motion-planning distance can be defined as optimal cost-to-go between states, but with nonholonomic/asymmetric actions it may not be symmetric; obstacles can also make some targets unreachable.

### SF-43

**Optimal action cost ≠ mathematical metric universally.**

### SF-44

`Cost(x,y)` can be asymmetric, infinite or policy/model dependent.

---

# 23. Near in physical space can be far in action space

A Dubins car may be centimeters from a state behind it but require a long loop to reach that configuration.
A wall may make nearby positions require long travel.

### SF-45

**Physical nearness ≠ action-cost nearness.**

### SF-46

**Action-near is typed by admissible controls, constraints and objective.**

---

# 24. Conversely, physically far can be action-near

A fast transit edge, elevator, portal/teleport, wormhole-like virtual link or remote actuator can connect states cheaply despite large physical separation.

### SF-47

**Action adjacency can be nonlocal in physical metric geometry.**

### SF-48

Virtual/design systems can intentionally create action topology inconsistent with Euclidean display/world distance.

---

# 25. Shortest distance, fastest path and least-cost path differ

Planning cost may optimize:

- geometric length;
- elapsed time;
- energy;
- risk;
- discomfort;
- monetary cost;
- control effort;
- uncertainty/exposure;
- weighted combinations.

LaValle's planning framework explicitly treats time, distance and energy as different cost criteria.

### SF-49

```text
ShortestPath ≠ FastestPath ≠ LeastEnergyPath ≠ LeastRiskPath
```

### SF-50

**One state domain can carry multiple grounded cost geometries.**

---

# 26. Cost is not reachability

A target can be reachable with prohibitively large cost.
An unreachable target is often represented with infinite cost, but this is a modeling convention linking feasibility and optimization.

### SF-51

**Feasible/reachable ≠ desirable/low-cost.**

### SF-52

**Cost-to-go is an evaluation over possible trajectories, not the ontology of reachability itself.**

---

# 27. Optimality is objective-relative

Hamilton–Jacobi–Bellman and Pontryagin frameworks optimize a declared cost functional; changing that functional changes the optimum while the dynamics and feasible trajectories can stay fixed.

### SF-53

**Optimal trajectory ≠ intrinsically best trajectory.**

### SF-54

**Optimization objective/provenance must be explicit in action-space claims.**

---

# 28. Feasible path is not robust path

A mathematical shortest path may graze obstacles/boundaries and have almost zero clearance.
LaValle notes shortest paths can conflict with maximum-clearance objectives.

### SF-55

**Shortest ≠ safest ≠ most robust.**

### SF-56

Clearance/resilience is an additional action/navigation criterion.

---

# 29. Dynamics can create irreversibility and traps

With momentum/drift, entering a state region can make escape impossible even before collision occurs.

### SF-57

**Topological free region ≠ dynamically safe region.**

### SF-58

**Action safety requires future-trajectory structure, not current occupancy alone.**

---

# 30. State constraints and action constraints are different

A region can be state-forbidden (`x ∉ X_free`), while an action can be inadmissible at an otherwise valid state (`u ∉ U(x)`).

### SF-59

**Forbidden state ≠ forbidden action.**

### SF-60

Both can shape reachable/action space through different mechanisms.

---

# 31. Capability is not an environmental property alone

A stair riser of fixed physical height can be climbable for one body and unclimbable for another.

Warren 1984 experimentally found climbability category boundaries scaled with the actor's leg length, and preferred/energy-efficient riser heights likewise reflected actor-environment fit.

### SF-61

**Action possibility can depend on agent capability × environment relation rather than environment geometry alone.**

---

# 32. Affordance is provisionally relational, not object-intrinsic

MF5-F does not freeze all of Gibson's ecological theory or direct-perception claims.
It retains the empirically useful relational core:

```text
AffordanceCandidate(A, E, actionType, context)
```

where actor/system capability and environmental conditions jointly determine a possible functional action relation.

### SF-62

**Affordance ≠ object property considered independently of actor capability.**

### SF-63

**Affordance ≠ chosen action.**

---

# 33. Affordance is not identical to geometric reachability

`Reachable(x,y)` describes state-transition feasibility under a model.
An affordance such as `sittable`, `climbable`, `graspable` or `pass-through-able` includes action type and actor-environment fit, potentially with posture, scale, force, semantics or convention.

### SF-64

**Reachability ≠ affordance.**

### SF-65

**Geometric access can be necessary for an affordance without being sufficient.**

---

# 34. Possible action, affordance, policy and executed action are separate

Provisionally:

```text
AdmissibleAction      : allowed control/action at state
ReachableOutcome      : possible resulting state/outcome
AffordanceCandidate   : actor-environment action possibility relation
Policy                : rule selecting actions from states/information
ChosenAction          : selected current action
ExecutedAction        : physically/computationally realized action
```

### SF-66

**Possible action ≠ selected action ≠ executed action.**

### SF-67

**Affordance standing does not imply current intention.**

---

# 35. Tool use changes capability/action relations without changing physical world geometry

MF5-E's Iriki evidence already showed body/action-centered spatial plasticity during rake use.
MF5-F interprets the action-side consequence:

### SF-68

**Tool availability can expand reachable/manipulable/action-relevant regions without deforming physical metric space.**

### SF-69

**Capability change can alter affordance/action-space standing while target environment remains fixed.**

---

# 36. Peripersonal, reachable and manipulable spaces remain separate

A near-body stimulus may be in peripersonal defensive/contact space but not manipulable.
A tool can make something reachable/manipulable outside bare-hand reach.

### SF-70

```text
Peripersonal ≠ Reachable ≠ Manipulable ≠ Graspable
```

### SF-71

These are body/action relations with different capability predicates.

---

# 37. Navigation space is not necessarily a metric map

Navigation can rely on graph/topological relations such as connected routes, landmarks, turns and sequence order without storing exact Euclidean coordinates/distances.

### SF-72

**Navigability does not require one complete Euclidean map representation.**

### SF-73

Topological navigation and metric navigation are distinct but combinable profiles.

---

# 38. Navigation graph is not physical space

A graph edge can encode:

- direct traversability;
- doorway connection;
- route segment;
- transport link;
- portal;
- learned transition.

### SF-74

**Navigation adjacency ≠ physical contact/proximity.**

### SF-75

**Graph shortest path depends on edge semantics/weights and does not automatically represent physical shortest distance.**

---

# 39. Navigation representation can intentionally omit metric geometry

A route plan can be sufficient as:

```text
Room A -> corridor -> stair -> Room B
```

without exact coordinates.

### SF-76

**Route sufficiency ≠ metric-map completeness.**

This parallels MF3/MF5-D selective fidelity.

---

# 40. Place, direction and metric-like codes are empirically dissociable

Primary neurophysiology identifies different spatial correlates:

- O'Keefe & Dostrovsky: hippocampal place-related unit activity;
- Taube, Muller & Ranck: head-direction cells whose firing correlated strongly with head direction and minimally with location;
- Hafting et al.: entorhinal grid cells with periodic triangular spatial firing structure.

### SF-77

**Place-related code ≠ head-direction code ≠ grid-like metric/periodic code.**

### SF-78

Their coexistence argues against collapsing navigation into one scalar coordinate variable.

---

# 41. Neural spatial correlates do not prove a literal Cartesian map

A place cell field, grid-cell firing lattice or head-direction tuning is an empirical response profile.

### SF-79

**Neural spatial tuning ≠ explicit coordinate-map data structure.**

### SF-80

**Implementation hypotheses require additional evidence about population coding, dynamics, readout and causal use.**

---

# 42. Grid cells do not license `brain uses exact Euclidean metric` as a foundation

Hafting et al. showed regular triangular grid firing across environments, strongly supporting spatial metric-like organization in medial entorhinal cortex.
But the ontology-level inference must remain weaker than a literal Euclidean coordinate-table claim.

### SF-81

**Grid-like periodicity is evidence for structured spatial coding, not proof that all navigation geometry is one globally Euclidean neural metric.**

---

# 43. Head-direction evidence reinforces frame/profile separation

Taube et al. found preferred directional firing remained stable and was largely independent of animal location in the test chamber.

### SF-82

**Orientation/direction information can be represented separately from position information.**

This reinforces MF5-A/C/E.

---

# 44. Navigation requires state estimation as well as action structure under uncertainty

An agent may possess a valid map/action model but be uncertain where it currently is.

### SF-83

**Navigation capability ≠ localization certainty.**

### SF-84

**Reachability under known state ≠ reachability under uncertain belief/information state.**

Full information-space planning remains primarily a later computation/agency topic, but the distinction must be preserved here.

---

# 45. Path integration introduces accumulated spatial uncertainty

Updating position/orientation from self-motion can accumulate error without external correction.

### SF-85

**Integrated displacement estimate ≠ ground-truth displacement.**

### SF-86

Navigation spatial standing can be maintained with uncertainty/calibration rather than perfect coordinate truth.

---

# 46. Landmark correction and path integration need not collapse into one code

External cues can recalibrate orientation/location while self-motion supports continuity between cues.

### SF-87

**Landmark-anchored localization ≠ self-motion integration, though they can cooperate.**

---

# 47. Planning representation is not action ontology

RRTs, A*, PRMs, dynamic programming and graph search are algorithmic methods for exploring/selecting feasible trajectories under models.

LaValle's RRT work demonstrates an efficient search representation for high-dimensional/nonholonomic planning, but the tree itself is not the underlying action space.

### SF-88

**Planning/search tree ≠ reachable set ≠ action-space ontology.**

### SF-89

Algorithm failure to discover a path does not by itself prove unreachable unless completeness/assumptions justify that inference.

---

# 48. Sampling representation can distort apparent connectivity

Discretization/lattice/roadmap choices may omit narrow passages or create approximation artifacts.

### SF-90

**Search-graph connectivity ≠ target reachability without approximation guarantees.**

This is MF1 sampling/aliasing applied to action space.

---

# 49. Motion primitives are not the full reachable repertoire

A planner may restrict itself to a finite library of primitives even though the physical/controller action model permits more trajectories.

### SF-91

**Planner primitive set ≠ system action capability.**

### SF-92

Planning incompleteness due to abstraction must not be laundered into physical impossibility.

---

# 50. Policy changes can change realized navigation without changing reachability

Two policies over the same action/state model can select different routes/costs/risk behavior.

### SF-93

**Reachable set ≠ policy-induced visitation distribution.**

### SF-94

**Frequently visited ≠ uniquely reachable ≠ geometrically near.**

---

# 51. Learned action geometry can reflect policy/data bias

If an embedding/model is learned from trajectories produced by one policy, its similarity may reflect visited transitions rather than all physically possible transitions.

### SF-95

**Behavior-data geometry ≠ full capability/reachability geometry by default.**

### SF-96

Coverage/provenance must be retained when inferring action space from observed behavior.

---

# 52. Reachable-space boundary can be capability/state dependent

Change actuator strength, joint limit, injury, payload, battery state or tool, and the reachable region may change while physical scene geometry does not.

### SF-97

**Reachability boundary ≠ environment boundary.**

### SF-98

**Reachability is agent/system-state dependent.**

---

# 53. Dynamic obstacles make action space state/time dependent

Moving agents/obstacles can change safe trajectories even with unchanged static geometry.

### SF-99

**Static free-space topology ≠ dynamic safe reachability.**

MF5-F records this fact but defers the full temporal/dynamical ontology to MF6/MF7.

---

# 54. Multi-agent reachability is relational and strategic

Another agent can create, remove or condition access based on its possible actions.

### SF-100

**Reachability in interactive systems ≠ single-agent geometric reachability.**

Full strategic/game-theoretic agency belongs later to MF8/MF10, but MF5 must not freeze action space as single-agent only.

---

# 55. Portals and teleports falsify physical-distance primacy in designed spaces

A virtual system can define transitions between regions with no continuous intervening physical/display path.

### SF-101

**Action topology can include nonlocal edges and discontinuous transitions by design.**

### SF-102

**Continuous physical/display geometry is not a universal requirement for navigable/action space.**

This is a bridge to MF5-G virtual space.

---

# 56. Action-space standing needs an anti-inflation criterion

An analyst can always invent a state graph or assign costs.

MF5-F proposes:

```text
ActionSpatialStanding(S | Agent/System, Environment, ActionModel, Scope)
```

when spatially organized possibilities/constraints are established by actual system dynamics, capabilities, design/specification, stable behavior/control effects, formal construction or another non-arbitrary route.

### SF-103

**Analyst-defined transition graph ≠ target action space.**

### SF-104

**Analyst cost function ≠ grounded action cost without task/system standing.**

---

# 57. Action-space evidence must be intervention-sensitive

Strong evidence includes:

- executing controls and observing transitions;
- capability/constraint perturbations;
- body/tool scaling;
- collision/reachability tests;
- timing/energy measurements;
- system identification;
- formal dynamics/specification;
- repeated navigation behavior;
- controlled obstacle/action changes.

### SF-105

**Action possibility claims need evidence about what transitions can actually be produced, not only static geometry.**

---

# 58. Counterfactual capability perturbation is especially diagnostic

If changing reverse gear, tool length, leg length, actuator bounds or obstacle shape predictably changes reachable/afforded regions, this supports relational action-space standing.

### SF-106

**Capability-sensitive counterfactual change is strong evidence that an action relation is not merely analyst-imposed.**

---

# 59. But action standing does not require current execution

A door may be traversable even if the agent chooses not to cross it.
A stair may be climbable even if no climb occurs.

### SF-107

**Action possibility/affordance standing ≠ action occurrence.**

### SF-108

Intent/choice is not constitutive of all action possibility.

---

# 60. Uncertainty must separate capability, state and environment

An agent may be uncertain about:

- current state;
- actuator capability;
- obstacle location;
- dynamics parameters;
- action outcome;
- cost;
- other agents.

### SF-109

**Reachability uncertainty is typed by uncertainty source.**

### SF-110

A probability of successful transition is not the same as fuzzy spatial membership or deterministic reachability.

---

# 61. Risk-sensitive reachability is not ordinary reachability

A target might be physically reachable but only through trajectories with unacceptable failure probability.

### SF-111

**Possible ≠ reliably possible ≠ acceptably safe.**

### SF-112

Safety/reliability thresholds add policy/task constraints rather than redefining physical space.

---

# 62. Action-space equivalence is capability/objective relative

Two environments may be physically different but action-equivalent for an agent if they offer the same reachable transitions/cost profile under task scope.
Conversely, physically identical layouts can be action-nonequivalent for different agents.

### SF-113

**Physical spatial equivalence ≠ action-space equivalence.**

### SF-114

**Action equivalence must declare agent, action repertoire, constraints and objective.**

---

# 63. ActionSpaceProfile

MF5-F proposes:

```text
ActionSpaceProfile = <
  Agent/System,
  Environment/TargetDomain,
  StateSpace,
  ConfigurationSpace?,
  ActionSet U(x),
  Transition/Dynamics f,
  Constraints,
  Free/Forbidden/Safe Regions,
  ReachableSets,
  ControllabilityProfile,
  Cost/Objectives,
  Affordance/CapabilityRelations,
  NavigationRepresentation?,
  Policy/Planner?,
  Frames/Geometry,
  Time/Horizon,
  Uncertainty/Risk,
  StandingRoute,
  Evidence/Provenance,
  Scope
>
```

### SF-115

**Not every action-space profile requires an explicit configuration manifold, cost function, map or planner.**

---

# 64. ReachabilityClaim

```text
ReachabilityClaim = <
  StartState/Region,
  TargetState/Region,
  Agent/System,
  ActionModel,
  Dynamics/Transition,
  Constraints,
  Horizon,
  EnvironmentState,
  RequiredSuccess/SafetyLevel,
  CostBound?,
  Uncertainty,
  Evidence/Provenance,
  Scope
>
```

### SF-116

**Bare `reachable` is under-specified when action consequences matter.**

---

# 65. NavigationProfile

```text
NavigationProfile = <
  NavigatingAgent,
  Target/Goal,
  Localization/BeliefState,
  SpatialRepresentation : topological/metric/landmark/hybrid/etc.,
  Traversability/Reachability Graph,
  Orientation/Heading Structure,
  Cost/Policy,
  PathIntegration/SelfMotionUpdate,
  Landmark/ExternalCorrection,
  Planning/Feedback Mechanism,
  Uncertainty,
  Evidence/Provenance,
  Scope
>
```

### SF-117

**Navigation is a coupled localization + action-selection problem under spatial structure, not merely path geometry.**

---

# 66. AffordanceClaim

MF5-F provisionally uses a deliberately theory-light schema:

```text
AffordanceClaim = <
  Agent/System,
  Environment/Object/Region,
  ActionType,
  CapabilityProfile,
  EnvironmentalConditions,
  RelevantScale/Geometry,
  Feasibility/CriticalBoundary,
  OptionalCost/Preference,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### SF-118

**This captures actor-environment action fit without freezing direct-perception, representation or phenomenology theories.**

---

# 67. Failure taxonomy

## Physical/configuration collapse

Configuration-space point treated as physical point location.

## Configuration/state collapse

Velocity/momentum/internal state ignored when action possibility depends on it.

## Connectivity/reachability collapse

Continuous/geometric path existence treated as controlled feasibility.

## Instantaneous/eventual collapse

Unavailable instantaneous direction treated as impossible eventual displacement, or vice versa.

## Reachability/controllability collapse

One successful transition interpreted as a general system property.

## Global/local maneuverability collapse

Eventual open-space reachability interpreted as STLC/obstacle maneuverability.

## Distance/cost collapse

Euclidean length used as time/energy/risk/action cost without grounding.

## Cost/reachability collapse

Expensive target declared unreachable or reachable target declared cheap.

## Free/empty collapse

Allowed configuration treated as materially empty region.

## Obstacle/occupancy collapse

Constraint-exclusion region treated as material occupant.

## Affordance/reachability collapse

Actor-environment functional possibility reduced to point-to-point transition existence.

## Possibility/choice collapse

Available action treated as selected/executed action.

## Policy/capability collapse

Observed policy trajectories treated as complete action repertoire.

## Planner/ontology collapse

RRT/tree/roadmap/search graph treated as the target reachable structure itself.

## Sampling alias

Discretization/primitive library destroys or invents apparent connectivity.

## Neural-map reification

Place/grid/head-direction correlates treated as one literal Cartesian map implementation.

## Safety/possibility collapse

Low-probability or inevitable-collision trajectories treated as ordinary feasible states.

## Environment-only affordance error

Capability-relative action boundary treated as object property independent of actor.

### SF-119

**Action-space error is a typed family; no one geometric path error captures it.**

---

# 68. Strongest non-collapse stack after MF5-F

```text
Physical Space
 ≠ Configuration Space
 ≠ State/Phase Space
 ≠ Action Space
```

```text
Configuration
 ≠ Dynamical State
```

```text
Connected
 ≠ Reachable
 ≠ Controllable
 ≠ Small-Time Locally Controllable
```

```text
Instantaneously Feasible Direction
 ≠ Eventually Reachable Displacement
```

```text
Geometric Path
 ≠ Feasible Trajectory
 ≠ Controlled Execution
```

```text
Physical Distance
 ≠ Feasible Path Length
 ≠ Travel Time
 ≠ Energy/Control Cost
 ≠ Risk
```

```text
Free
 ≠ Empty
 ≠ Safe
```

```text
Obstacle Occupancy
 ≠ Configuration Exclusion
 ≠ Inevitable-Collision Region
```

```text
Peripersonal
 ≠ Reachable
 ≠ Manipulable
 ≠ Graspable
```

```text
Reachable
 ≠ Afforded
 ≠ Desirable
 ≠ Chosen
 ≠ Executed
```

```text
Navigation Graph
 ≠ Physical Geometry
 ≠ Reachable Set
```

```text
Place Code
 ≠ Grid Code
 ≠ Head-Direction Code
 ≠ One Canonical Neural Map
```

```text
Planner Representation
 ≠ Target Action-Space Standing
```

---

# 69. Claims rejected by MF5-F

Reject as universal foundational claims:

- physical space, configuration space, state space and action space are interchangeable;
- a C-space point is one physical point;
- configuration alone always determines action possibility;
- current noncollision implies future avoidability/safety;
- connected states are necessarily dynamically reachable;
- a continuous configuration path is automatically executable;
- lack of instantaneous lateral motion means lateral displacement is unreachable;
- reachability and controllability are synonymous;
- eventual global reachability implies small-time local controllability;
- same physical geometry gives all agents the same reachability/action geometry;
- Euclidean endpoint distance determines shortest feasible path;
- shortest path equals fastest, least energy, safest or lowest-cost path;
- optimal control cost is universally a symmetric metric;
- physical nearness implies action nearness;
- action adjacency must be physically local;
- free means empty or safe;
- obstacle means material occupancy;
- one policy's observed trajectories reveal the full capability space;
- an action set is automatically a spatial domain because it is parameterized;
- affordance is an environment-only property independent of actor capability;
- affordance equals geometric reachability;
- possible action equals chosen or executed action;
- peripersonal equals reachable/manipulable space;
- navigation requires a complete Euclidean coordinate map;
- graph adjacency is physical adjacency;
- place/grid/head-direction cells prove a single literal Cartesian neural map;
- grid firing proves all navigation geometry is globally Euclidean;
- a planning/search tree is the reachable set itself;
- planner failure proves physical unreachability absent completeness conditions;
- discretized search-graph connectivity is target reachability by default;
- motion primitives equal the full action repertoire;
- physical spatial equivalence implies action-space equivalence;
- reachable means reliable/safe/acceptable;
- action relevance defines spatial existence.

---

# 70. Primary/original/authoritative anchors

- **Tomás Lozano-Pérez (1983)**, `Spatial Planning: A Configuration Space Approach`, *IEEE Transactions on Computers* C-32(2), 108–120, DOI 10.1109/TC.1983.1676196. Position/orientation encoded as one configuration-space point; forbidden configurations induced by obstacles form configuration-space obstacle regions.
- **Steven M. LaValle (2006; official open online edition)**, *Planning Algorithms*, Chapters 4, 13–15. Authoritative synthesis defining C-space, state/phase space, differential constraints, reachable sets, STLC, nonholonomic planning, optimal control and action-dependent distance/cost. Used here as a synthesis/reference framework, not as evidence that one planning formalism is universal ontology.
- **R. E. Kalman (1960)**, `On the General Theory of Control Systems`, IFAC proceedings. Foundational modern controllability formulation for dynamical/control systems.
- **Lester E. Dubins (1957)**, `On Curves of Minimal Length with a Constraint on Average Curvature, and with Prescribed Initial and Terminal Positions and Tangents`, *American Journal of Mathematics* 79(3), 497–516, DOI 10.2307/2372560. Hard case showing shortest feasible motion depends on curvature/orientation constraints.
- **J. A. Reeds & L. A. Shepp (1990)**, `Optimal Paths for a Car That Goes Both Forwards and Backwards`, *Pacific Journal of Mathematics* 145(2), 367–393, DOI 10.2140/pjm.1990.145.367. Shows altered action repertoire (reverse allowed) changes shortest-path structure.
- **William H. Warren Jr. (1984)**, `Perceiving Affordances: Visual Guidance of Stair Climbing`, *Journal of Experimental Psychology: Human Perception and Performance* 10(5), 683–703, DOI 10.1037/0096-1523.10.5.683. Critical climbability and preferred/energetic boundaries scale with actor-environment fit, supporting capability-relative action relations.
- **John O'Keefe & Jonathan Dostrovsky (1971)**, `The Hippocampus as a Spatial Map. Preliminary Evidence from Unit Activity in the Freely-Moving Rat`, *Brain Research* 34(1), 171–175, DOI 10.1016/0006-8993(71)90358-1. Foundational place-related hippocampal unit evidence.
- **Jeffrey S. Taube, Robert U. Muller & James B. Ranck Jr. (1990)**, `Head-direction cells recorded from the postsubiculum in freely moving rats. I. Description and quantitative analysis`, *Journal of Neuroscience* 10(2), 420–435, DOI 10.1523/JNEUROSCI.10-02-00420.1990. Directional code largely separable from location in the experiment.
- **Torkel Hafting, Marianne Fyhn, Sturla Molden, May-Britt Moser & Edvard I. Moser (2005)**, `Microstructure of a spatial map in the entorhinal cortex`, *Nature* 436, 801–806, DOI 10.1038/nature03721. Grid-cell periodic spatial firing provides evidence for metric-like structured neural coding while not forcing one literal global coordinate-map ontology.
- **Steven M. LaValle (1998)**, `Rapidly-exploring random trees: A new tool for path planning`, TR 98-11. Search/planning hard case demonstrating algorithmic exploration of high-dimensional/nonholonomic spaces; planner representation remains distinct from target reachability ontology.

---

# 71. Deep reconstruction

Naive model:

```text
Physical map
   ↓ mark obstacles
Free space
   ↓ shortest line/path
Reachable space
   ↓ choose action
Navigation
```

MF5-F replaces it with:

```text
Physical environment
       │
       ├─ body/system geometry & degrees of freedom
       ▼
Configuration space C
       │
       ├─ collision/configuration constraints -> C_free/C_obs
       │
       ├─ dynamics/velocity/internal state
       ▼
State / phase space X
       │
       ├─ admissible actions U(x)
       ├─ transition dynamics f(x,u)
       ├─ nonholonomic / actuation / safety constraints
       ▼
Reachability / controllability structure
       │
       ├─ time horizon
       ├─ asymmetric transitions
       ├─ possible traps / inevitable collision
       ├─ agent capability / tools
       │
       ├──────────────┐
       │              │
   cost/objective   affordance/action-fit
       │              │
 time/energy/risk   climbable/graspable/etc.
       │              │
       └──────┬───────┘
              ▼
       navigation / planning / policy
              │
     topological + metric + landmark +
     orientation + learned representations
              │
              ▼
        selected/executed action
```

The crucial move is:

> **Action space is not a deformation of physical space. It is a system-relative possibility structure over configurations/states whose topology, directionality, reachable regions and costs are induced by capabilities, dynamics, constraints and objectives.**

---

# 72. Deepest MF5-F result

The strongest surviving candidate is:

> **An action-spatial domain is a scope-relative structured domain of configurations or states in which possible state transitions, reachable regions, controllability, exclusion/safety constraints and optional cost/affordance relations have standing through an agent/system's capabilities, dynamics, environment and action model. Its geometry can be directed, asymmetric, state-dependent, nonlocal relative to physical distance and objective-dependent.**

Compact:

```text
ActionSpace
 = State/Configuration Possibility Domain
 + Agent/System Capability
 + Transition/Dynamics Structure
 + Constraints
 + Reachability/Controllability
 + Optional Cost/Affordance Profile
 + Standing
 + Scope
```

with planner/policy/representation optional.

---

# 73. MF5-A→F reconstructed picture

```text
MF5-A Space
 = standing spatial possibility domain

MF5-B Geometry
 = typed relation/invariance/equivalence structures

MF5-C Description
 = frames/charts/coordinates/transforms

MF5-D Regionalization
 = regions/boundaries + occupancy/locality/visibility/access

MF5-E Perceptual/Embodied Space
 = body/world-relative sensorimotor spatial organization

MF5-F Action Space
 = system-relative configurations/states + feasible transitions/reachability/cost/action relations
```

MF5-F demonstrates that action geometry is neither physical geometry nor merely perceptual geometry, although all three can be calibrated/coupled.

---

# 74. No FoundationReopenCondition

MF5-F does not falsify MF2 Perception, MF3 Representation or MF4 Composition Foundations.

- MF2 already permits action-coupled perception without collapsing action and perception.
- MF3 accommodates maps/planners as representations without making represented target geometry identical to vehicle geometry.
- MF4 accommodates transition graphs, paths and control compositions as organized multiplicities without defining action-space ontology itself.

### SF-120

**MF2, MF3 and MF4 remain frozen.**

---

# 75. MF5-G handoff — Representational, Map, Diagram & Virtual Space

MF5-A→F now distinguish physical, geometric, descriptive, regional, perceptual and action spatial structures. The next falsifier is representation/design itself.

MF5-G must ask:

> **When does a map, diagram, layout, screen, game world or virtual environment possess its own spatial standing, and how does that vehicle space relate to the physical/action/perceptual space it represents or enacts?**

Required topics/hard cases:

- map vehicle space vs represented target space;
- topological transit maps and metric distortion;
- cartographic projection and selective invariants;
- diagrammatic space and symbolic spatial conventions;
- screen/pixel/layout space;
- responsive/reflow space;
- scene graph/world space vs camera/view/screen space;
- virtual/game spaces with portals/teleports/non-Euclidean topology;
- designed collision/navigation geometry vs rendered geometry;
- minimaps and multiple simultaneous spatial representations;
- scale changes and level-of-detail;
- spatial metaphor versus genuine representational spatial standing;
- UI hit regions and operational coordinate standing;
- AR registration: physical ↔ virtual spatial correspondence;
- map error, alignment and calibration;
- represented-space fidelity typed by topology/metric/orientation/action relations;
- representation vehicle geometry vs target geometry;
- when a virtual domain is merely represented and when its rules computationally enact a spatial world;
- spatial provenance and uncertainty.

Central attack:

```text
Map Space ≠ Target Space
Vehicle Geometry ≠ Represented Geometry
Screen Space ≠ World Space
Rendered Geometry ≠ Collision/Action Geometry
Virtual Space ≠ Physical Space
Spatial Metaphor ≠ Spatial Standing
Projection Distortion ≠ Total Spatial Failure
Portal Adjacency ≠ Physical Nearness
```

**Next: MF5-G — Representational, Map, Diagram & Virtual Space.**
