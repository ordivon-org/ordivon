# Ordivon Media Foundations — MF7-A State Ontology & Term Separation

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 38 at start  
**Input:** MF0–MF6 frozen; MF6 Time Foundations v1 final core uses OccurrenceStanding.  
**Status:** MF7-A complete/provisional. State & Dynamics Foundations remain UNFROZEN.  
**Next:** MF7-B — Change, Transition, Process & Dynamics.

---

# 0. Purpose

MF6 froze the boundary:

```text
State ≠ TemporalPosition
TransitionRelation ≠ TemporalOrder
Dynamics ≠ Time
PossibleTransitionStructure ≠ RealizedTemporalHistory
```

MF7-A now asks what `state` itself means before studying change/dynamics.

Dangerous collapses:

```text
State = Snapshot
State = Observation
State = Measurement
State = Representation
State = Memory
State = Full Reality
State = Configuration
State = Property Set
State = State Vector
State = Coordinate Tuple
State = Database Row
State = Belief/Estimate
State = Output
Same Observation = Same State
Different State Vector = Different State
Complete State = Directly Observable State
State Space = Physical Space
State = History
```

---

# 1. First-principles requirement

A state concept earns its role only if distinctions among candidate conditions matter for what the declared system can do next, emit, persist as, or transition into under a specified model/boundary and exogenous conditions.

### SA-001
**State is system- and scope-relative.** There is no unqualified state without declaring what system and behavior/evolution semantics are being modeled.

### SA-002
**State ≠ complete reality.** A state may intentionally omit distinctions irrelevant to the declared model/task.

### SA-003
A stronger state description can refine a weaker state description without making the weaker one meaningless in its own scope.

---

# 2. Provisional StateStanding

MF7-A proposes:

```text
StateStanding(S, System | Model, Scope)
```

when distinctions in `S` have non-arbitrary standing as alternatives in the system's endogenous condition such that, conditional on declared exogenous inputs/noise/context, those distinctions are recruited by the system/model to determine or probabilistically condition admissible contemporaneous outputs, persistence, transitions or future behavior.

### SA-004
**StateStanding is behavioral/dynamical standing, not visual resemblance to a snapshot.**

### SA-005
The relevant sufficiency can be deterministic or probabilistic.

### SA-006
State need not predict one exact future; stochastic state can condition a distribution over future behavior.

### SA-007
This definition is provisional until MF7 falsification; predictive/behavioral sufficiency may need reconstruction later.

---

# 3. State versus history

A central formal motivation for state is compression/separation of relevant past from future behavior.

### SA-008
**State ≠ full past history.**

### SA-009
A state representation is useful when histories equivalent for future system behavior can be treated as the same current condition under the declared model.

### SA-010
This does not imply the past is physically erased; it means omitted historical distinctions are behaviorally irrelevant within scope.

### SA-011
History dependence can force state augmentation: if omitted past information changes future behavior, the proposed state was insufficient for that model.

---

# 4. Kalman/control hard case: state description ≠ input/output description

Kalman's state-space program explicitly distinguishes describing a dynamical system by state variables from describing it only by input/output relations, and uses controllability/observability to study minimal realizations.

### SA-012
**State ≠ Input/Output relation.**

### SA-013
Two internal state descriptions can realize the same external input/output behavior while differing by representation/redundancy.

### SA-014
Observable behavior can fail to identify every internal state distinction.

### SA-015
Minimal state dimension is a property of a declared realization/equivalence problem, not a universal count of reality's degrees of freedom.

---

# 5. State versus observation

Smallwood–Sondik's partially observable Markov model directly separates an internal finite-state process from outputs probabilistically related to that internal state.

### SA-016
**State ≠ Observation.**

### SA-017
The same observation can be compatible with multiple states.

### SA-018
Different observations can be generated from the same underlying state under noise/stochastic observation models.

### SA-019
`ObservableState` is a special relation/profile, not a constitutive property of all states.

---

# 6. State versus measurement

A measurement is an evidence-acquisition event/result about selected variables.

### SA-020
**MeasurementResult ≠ TargetState.**

### SA-021
Measurement can be partial, noisy, delayed, quantized or transformed.

### SA-022
A measurement may itself become part of another system's state (e.g. controller memory) while remaining evidence about the target system.

### SA-023
Evidence route ≠ target state standing route.

---

# 7. State versus snapshot

A snapshot is a representation/record at one occurrence time.

Gibbs' mechanics treats the relevant mechanical condition as configuration plus velocities; a picture of positions alone can therefore be insufficient to determine future motion.

### SA-024
**Snapshot ≠ State.**

### SA-025
A snapshot can omit hidden variables, velocities/momenta, internal memory, latent modes, environment coupling or unresolved fields required by the declared dynamics.

### SA-026
A sufficiently rich snapshot may represent a state, but representation adequacy must be established rather than assumed.

---

# 8. Configuration versus state

Classical mechanics supplies the cleanest counterexample.

Let `q` denote configuration and `p` momentum/velocity-related variables.

### SA-027
**Configuration q ≠ mechanical phase/state (q,p) in standard first-order Hamiltonian/state descriptions.**

### SA-028
Two systems can share the same configuration while evolving differently because momentum/velocity differs.

### SA-029
Configuration can be a component/projection of state rather than state itself.

### SA-030
In other domains configuration may be sufficient; sufficiency is model-relative, not a word-level law.

---

# 9. Property versus state

Temperature, color, position, battery level, role, health status and similar predicates/variables may describe a system.

### SA-031
**Property ≠ State by identity.**

### SA-032
A property can be a state variable/component if its current value contributes to sufficient system condition under the model.

### SA-033
One property rarely establishes full state sufficiency by itself.

### SA-034
A state can also include relational properties involving environment/other systems when system boundary/model requires them.

---

# 10. Condition versus state

`Condition` is broader than state: e.g. `temperature > 100°C`, `damaged`, `reachable`, `authenticated`.

### SA-035
**Condition ≠ State.**

### SA-036
A condition commonly denotes a predicate/subset over state space rather than one exact state.

### SA-037
Multiple distinct states can satisfy the same condition.

### SA-038
A coarse condition can itself serve as an abstract state only if the abstraction preserves required behavior/transition distinctions under scope.

---

# 11. State versus state variable

### SA-039
**StateVariable ≠ State.**

A state variable is one component/function/coordinate used to distinguish states.

### SA-040
Different choices of variables can coordinatize/represent the same underlying state standing.

### SA-041
A variable can be redundant, derived or non-minimal without invalidating the represented state.

---

# 12. State vector versus state

### SA-042
**StateVector ≠ State.**

`x ∈ R^n` is one representational/formal realization.

### SA-043
Invertible coordinate transformations can change vector components while preserving state identity/evolution structure.

### SA-044
Different-dimensional realizations can encode equivalent external behavior when redundant/unobservable/uncontrollable variables are present.

### SA-045
State need not be a finite-dimensional Euclidean vector: discrete, hybrid, manifold-valued, field/infinite-dimensional, symbolic or distributional states are admissible profiles.

---

# 13. State space versus physical space

### SA-046
**StateSpace ≠ PhysicalSpace.**

A state space is a domain of possible system conditions under a model.

### SA-047
A single state point may encode positions, velocities, temperatures, internal modes, memory bits, beliefs or other variables simultaneously.

### SA-048
State-space distance/adjacency does not automatically inherit MF5 physical spatial standing.

### SA-049
MF5's structural-isomorphism firewall applies: visualization of a state space does not make target state differences physically spatial.

---

# 14. State versus coordinate tuple

### SA-050
**State ≠ CoordinateTuple.**

### SA-051
Same state can have different coordinate tuples in different charts/bases/encodings.

### SA-052
Same numeric tuple can denote different states in different state spaces/models.

### SA-053
Coordinate provenance/model identity is therefore first-class.

---

# 15. State versus representation

A record/object/vector/graph can stand for a state.

### SA-054
**State ≠ StateRepresentation.**

### SA-055
Representation can be stale, lossy, approximate, inconsistent or wrong while the target system has some actual state.

### SA-056
A representation can also be the actual operational state of a computational system when the represented object is itself the target system; standing route must be declared.

### SA-057
MF3 grounding rules remain active for target-state claims.

---

# 16. State versus memory

Memory means stored influence/information about prior events, but its relation to system state is conditional.

### SA-058
**Memory ≠ State by identity.**

### SA-059
Internal memory variables belong to state when future behavior depends on their current values under the declared system model.

### SA-060
External logs/history archives are not system state merely because they record the past.

### SA-061
A stateless/transient system can have external history recorded elsewhere.

### SA-062
A system can have state without explicit symbolic memory (e.g. mechanical momentum, oscillator phase, field configuration).

---

# 17. State versus database row / serialization

### SA-063
**SerializedState ≠ State.**

A database row/checkpoint/file can encode a state representation.

### SA-064
Serialization can omit ephemeral resources, environment coupling, timebase, external authority or hidden runtime variables.

### SA-065
Restoring identical bytes does not guarantee identical effective state if relevant exogenous/environmental conditions differ.

### SA-066
Conversely different serializations can represent equivalent effective state.

---

# 18. State versus observation history

### SA-067
**ObservationHistory ≠ TargetState.**

Observation history may permit inference of target state but is an epistemic evidence object.

### SA-068
Under partial observability multiple state histories can remain compatible with the same observation history.

### SA-069
A sufficiently constructed statistic of observation history may become an information state for the controller without becoming target physical state.

---

# 19. Belief/information state versus target state

Smallwood–Sondik's partially observable control model separates hidden internal process states from probability distributions used for control decisions.

### SA-070
**BeliefState ≠ TargetState.**

### SA-071
A belief state is a state of information/decision process: a probability distribution or sufficient decision statistic over target states.

### SA-072
The same target state can coexist with different beliefs in different agents/observers.

### SA-073
The same belief can assign probability to multiple mutually exclusive target states.

### SA-074
Belief state can nevertheless have genuine operational state standing for the controller/agent itself.

---

# 20. Estimate versus state

Kalman filtering is explicitly an estimation problem over hidden dynamical state from noisy observations.

### SA-075
**StateEstimate ≠ State.**

### SA-076
Estimate error/covariance is epistemic/statistical structure about uncertainty, not an extra physical target coordinate by default.

### SA-077
A perfect estimate may numerically equal a state representation while remaining a distinct epistemic relation/provenance role.

---

# 21. Macrostate versus microstate

Gibbsian statistical mechanics motivates separating detailed mechanical phase from ensemble/probabilistic descriptions.

### SA-078
**Macrostate ≠ Microstate.**

### SA-079
Many microstates can correspond to one coarse/macroscopic state under an abstraction map.

### SA-080
A macrostate can be legitimate if its coarse distinctions are sufficient/relevant for the declared thermodynamic/statistical model, even though it is not a complete microphysical state.

### SA-081
Coarse state ≠ false state; it is a scoped quotient/abstraction.

---

# 22. State abstraction and equivalence

Let `π: X → Z` map fine states to abstract states.

### SA-082
A state abstraction is justified when distinctions collapsed by `π` are irrelevant to declared outputs/transitions/predictions/control objective within tolerance/scope.

### SA-083
**SameAbstractState ≠ SameFineState.**

### SA-084
Abstraction validity is consumer/model relative and can fail under a new intervention/task.

### SA-085
State granularity is therefore not universally fixed.

---

# 23. State completeness is relative

### SA-086
**CompleteState is always complete relative to a declared dynamical/system model and exogenous boundary.**

An allegedly complete mechanical state can become incomplete if hidden environment coupling is later admitted.

### SA-087
`Complete` must name which future/output/transition questions are intended to be conditionally determined.

### SA-088
No finite description is assumed to be metaphysically complete reality.

---

# 24. Endogenous versus exogenous variables

State aims to carry endogenous condition; inputs/disturbances/context may remain external.

### SA-089
**Input ≠ State by default.**

### SA-090
A variable may be exogenous in one system boundary and endogenous state in a larger enclosing model.

### SA-091
System boundary choice changes state decomposition without necessarily changing physical reality.

### SA-092
Boundary provenance is first-class.

---

# 25. Parameter versus state

Model parameters such as mass, constant gain or learned weights may influence dynamics.

### SA-093
**Parameter ≠ State by identity.**

### SA-094
A parameter becomes state-like when it is allowed to vary/endogenously evolve and its current value is needed for future behavior under the model.

### SA-095
Fixed parameter standing and evolving state standing must remain distinct.

---

# 26. Input versus control versus disturbance

MF7-A records but defers detailed control ontology.

### SA-096
**ControlInput ≠ State ≠ Disturbance.**

### SA-097
The same physical variable can change role under different model boundaries/authority assumptions.

### SA-098
Role typing matters more than variable name.

---

# 27. Output versus state

### SA-099
**Output ≠ State.**

Output is a system-emitted/observable variable or function of state/input under the model.

### SA-100
Outputs can be many-to-one in state, making internal states observationally indistinguishable.

### SA-101
A full-state output is a special design/model case, not the definition of output.

---

# 28. Same output does not imply same state

Observability theory exists precisely because external outputs may fail to distinguish internal states.

### SA-102
**SameOutputHistory can be compatible with distinct internal states in a non-observable model.**

### SA-103
Inference/identifiability must not be confused with state identity.

---

# 29. State identity versus object identity

The same persisting object/system can occupy different states.

### SA-104
**ObjectIdentity ≠ StateIdentity.**

### SA-105
Changing state need not create a new object; persistence/identity through state change is a later MF7 problem.

### SA-106
Conversely two different objects can instantiate equivalent states under an abstract model.

---

# 30. State occurrence versus state type

### SA-107
**StateType/Value ≠ StateOccurrence/Token.**

A system may revisit the same abstract state value at different temporal occurrences.

### SA-108
MF6 OccurrenceStanding types when a state instance obtains; MF7 state ontology types what condition obtains.

### SA-109
This prevents `state = temporal position` collapse.

---

# 31. State versus temporal position

### SA-110
**State ≠ TemporalPosition.**

Two different states may be defined at the same temporal coordinate in alternative/counterfactual runs; the same abstract state may recur at multiple temporal positions.

### SA-111
Time indexes occurrences of state; it does not constitute state content.

---

# 32. State versus transition

### SA-112
**State ≠ Transition.**

A state is a condition alternative; a transition is a relation/process/change from one condition occurrence/type to another.

### SA-113
Transition ontology is deferred to MF7-B.

### SA-114
A transition graph may exist without any transition occurrence, preserving MF6-F's firewall.

---

# 33. State versus trajectory/history

### SA-115
**State ≠ Trajectory ≠ History.**

A trajectory/history is an organized sequence/path/process of state occurrences under temporal standing.

### SA-116
A single current state can summarize relevant history for some models; another model may require history augmentation.

### SA-117
History is not automatically a state, although a history window can be embedded as state when required for Markov/sufficiency purposes.

---

# 34. State versus attractor/invariant

MF7-A only marks boundaries.

### SA-118
**State ≠ Attractor.** An attractor is a set/structure of long-run dynamical behavior, not one instantaneous condition.

### SA-119
**State ≠ Invariant.** An invariant is a property/function preserved across dynamics, potentially shared by many states.

Detailed dynamics comes later.

---

# 35. State versus control policy

### SA-120
**State ≠ Policy.**

A policy maps state/information/action context to action choice.

### SA-121
A controller may itself have internal state/memory distinct from the controlled plant state.

### SA-122
PlantState ≠ ControllerState ≠ BeliefState, though they can be coupled.

---

# 36. State as sufficient condition — strength and limitation

The strongest common systems concept is:

```text
Given current state + future exogenous inputs/noise/model,
relevant future behavior is conditionally independent of earlier history.
```

### SA-123
MF7-A adopts this as a **powerful diagnostic**, not yet an unrestricted metaphysical definition.

### SA-124
If history beyond proposed state changes allowed future behavior under fixed declared inputs/model, the proposed state is insufficient and must be augmented or the model declared non-Markov/history-dependent.

### SA-125
Stochastic sufficiency means future distributions/transition kernels may be conditioned, not exact outcomes fixed.

### SA-126
Open systems can require environment state/input in the boundary; insufficiency does not prove `state` is impossible.

---

# 37. State counterfactual diagnostic

Hold declared exogenous inputs and model fixed; substitute one candidate current condition for another.

### SA-127
If the substitution can change admissible output/transition/future distributions, the distinction has strong state relevance.

### SA-128
If no declared behavior can distinguish the candidates, they may belong to the same abstract state equivalence class within scope.

### SA-129
This is a diagnostic, not a universal metaphysical test; hidden/unmodeled consumers can invalidate the abstraction later.

---

# 38. Observation-deletion diagnostic

Remove the observer/sensor/record while leaving target system condition unchanged.

### SA-130
If target evolution remains well-defined, observation was not constitutive of target state.

### SA-131
This blocks `state = observation record` except when the recording subsystem is itself included in target system state.

---

# 39. Representation-change diagnostic

Apply an invertible state-coordinate/serialization transformation preserving transition/output structure.

### SA-132
If system behavior is preserved, representation changed without target state identity changing.

### SA-133
This blocks `state = vector components/bytes` by default.

---

# 40. Boundary-expansion diagnostic

Enlarge the modeled system to include previously external environment/controller variables.

### SA-134
Variables can move from input/context into endogenous state under boundary expansion.

### SA-135
**State decomposition is boundary-relative without being arbitrary.** Boundaries are judged by model purpose, causal/interaction structure and predictive/control adequacy.

---

# 41. Provisional StateProfile

```text
StateProfile = <
  System/Boundary,
  StateDomain,
  StateStanding,
  StateVariables/Coordinates?,
  Granularity/Abstraction,
  EndogenousVariables,
  ExogenousInputs/Disturbances,
  Output/ObservationMap?,
  Transition/DynamicsInterface?,
  BehavioralSufficiencyClaim?,
  ObservabilityProfile?,
  ControllabilityProfile?,
  Representation/Serialization?,
  Estimate/BeliefProfile?,
  Uncertainty,
  Provenance/Authority,
  Scope
>
```

### SA-136
Not every profile field is constitutive; MF7-A has not frozen the final state core.

---

# 42. Provisional StateClaim

```text
StateClaim = <
  System,
  Occurrence/ValidityScope,
  ClaimedState/Condition,
  StateType/Granularity,
  StandingRoute,
  Coordinates/Representation?,
  Evidence/Observation?,
  Estimate/Belief?,
  Model/Boundary,
  Sufficiency/BehavioralScope,
  Uncertainty,
  Provenance,
  Scope
>
```

### SA-137
A bare `system is in state X` claim is under-specified when model/boundary/granularity differ materially.

---

# 43. Provisional standing routes

1. **Physical/Dynamical** — endogenous physical condition relevant to evolution.
2. **Formal/Mathematical** — state explicitly constituted in a transition/dynamical formalism.
3. **Computational/Enacted** — machine/software/runtime condition consumed by transition/output rules.
4. **Biological/Organismal** — physiological/neural/internal condition relevant to subsequent organism behavior.
5. **Perceptual/Cognitive** — internal perceptual/cognitive condition where empirically/model-grounded.
6. **Information/Belief** — observer/controller information state sufficient for decisions/inference.
7. **Representational** — snapshot/record/vector standing for another target state.
8. **Institutional/Social** — rule-governed states such as account/status/process stage when operationally constituted.
9. **Hybrid**.

### SA-138
**StandingRoute ≠ EvidenceRoute.** A sensor can evidence physical state; a probability distribution can be controller state about that physical state.

---

# 44. Strongest non-collapse stack after MF7-A

```text
State
 ≠ Full Reality
 ≠ Temporal Position
 ≠ History
```

```text
State
 ≠ Snapshot
 ≠ Observation
 ≠ Measurement
 ≠ Representation
```

```text
State
 ≠ Configuration
 ≠ Property
 ≠ Condition
```

```text
State
 ≠ StateVariable
 ≠ StateVector
 ≠ CoordinateTuple
```

```text
StateSpace
 ≠ PhysicalSpace
```

```text
TargetState
 ≠ Estimate
 ≠ BeliefState
 ≠ ObservationHistory
```

```text
Memory
 ≠ State by identity
```

```text
Macrostate
 ≠ Microstate
```

```text
Input
 ≠ State
 ≠ Output
```

```text
Parameter
 ≠ State by identity
```

```text
ObjectIdentity
 ≠ StateIdentity
```

```text
State
 ≠ Transition
 ≠ Trajectory
 ≠ Attractor
 ≠ Invariant
```

```text
PossibleTransitionStructure
 ≠ RealizedTemporalHistory
```

---

# 45. Claims rejected by MF7-A

Reject as universal/foundational:

- state is a snapshot/image/record;
- state is whatever is directly observable;
- state equals measurement or output;
- state is complete reality;
- configuration alone is universally full state;
- any property/condition is automatically a state;
- state must be a finite-dimensional vector;
- coordinate tuple is state identity;
- state space is physical space;
- serialization/database row is effective state by identity;
- memory/log/history is state by identity;
- belief/estimate is target state;
- same observation implies same state;
- different state vectors imply different underlying states;
- state must be directly observable;
- one universally correct state granularity exists;
- macrostate is false/incomplete state and only microstate is legitimate;
- input/output/parameter roles are intrinsic properties of variables independent of system boundary;
- state is temporal position;
- state transition possibility is already a realized history.

---

# 46. Primary/authoritative anchors

- **J. Willard Gibbs (1902), _Elementary Principles in Statistical Mechanics_.** In the mechanics setup Gibbs treats a system's condition for prediction in terms of configuration plus velocities and explicitly distinguishes actual succession from the broader space of conceivable conditions. This is the foundational hard case against `configuration/snapshot = full state`.
- **R. E. Kalman (1963), `Mathematical Description of Linear Dynamical Systems`, SIAM Journal on Control.** Explicitly separates state-variable description from input/output description and develops controllability/observability/minimal realization. This anchors `state ≠ output`, `representation/minimal realization is model-relative`, and hidden/redundant state distinctions.
- **R. E. Kalman (1960), `A New Approach to Linear Filtering and Prediction Problems`.** Filtering estimates the state of a dynamical system from observations under noise, anchoring `state ≠ observation ≠ estimate`.
- **R. D. Smallwood & E. J. Sondik (1973), `The Optimal Control of Partially Observable Markov Processes over a Finite Horizon`, Operations Research.** Internal Markov states are not directly observable; controllers receive outputs only probabilistically related to internal state and make decisions over state probabilities. This anchors `target state ≠ observation ≠ information/belief state`.

---

# 47. Deep reconstruction

Naive software/image model:

```text
system at time t
   ↓
take snapshot / serialize values
   ↓
that byte/vector/image is the state
   ↓
compare next snapshot
   ↓
call difference change
```

MF7-A replaces it with:

```text
Declared system + boundary + model
             │
             ▼
   Endogenous condition alternatives
             │
       StateStanding
             │
     ┌───────┼────────┐
     ▼       ▼        ▼
 variables  relations hidden/internal condition
     │
     ├── coordinates / vectors / serializations
     │      (representations)
     │
     ├── observations / outputs / measurements
     │      (evidence channels)
     │
     └── estimates / beliefs
            (epistemic/controller states)

Given state + declared exogenous inputs/model,
future/output/transition possibilities are conditionally determined
or probabilistically conditioned within scope.
```

The decisive move is:

> **State is not what a system looks like at an instant. State is a scope-relative endogenous condition standing whose distinctions carry the behaviorally relevant information needed by the declared system/model for outputs, persistence and admissible future evolution, conditional on exogenous drivers. Snapshots, vectors, observations and beliefs are distinct representations/evidence/information states around that target.**

---

# 48. Deepest MF7-A result

Provisional:

> **A system state is a scope- and boundary-relative condition alternative whose distinctions are non-arbitrarily recruited by a declared system/model as behaviorally sufficient endogenous information for contemporaneous outputs and/or admissible future evolution given declared exogenous inputs, disturbances and stochastic structure. State is therefore not identical to its coordinates, snapshot, observation, estimate, memory or full reality; these are typed relations or realizations around state.**

Compact:

```text
State
 = Endogenous Condition Standing
 + Behavioral Sufficiency under Model/Boundary
 + Granularity/Equivalence
 + Scope
```

with optional:

```text
coordinates / variables / observations / estimates /
serialization / uncertainty / control relevance
```

MF7-A does **not** freeze this yet. MF7-B→later rounds must attack sufficiency, state-transition and history/persistence cases.

---

# 49. Earlier-foundation audit

- MF5: state space is not physical space; no reopen.
- MF6: state occurrence is indexed by temporal standing but state content ≠ temporal position; no reopen.
- MF3: snapshot/vector/serialization distinction reinforces representation grounding; no reopen.
- MF2: observation/perception ≠ target state; no reopen.

### SA-139
**MF0–MF6 remain FROZEN; MF7-A triggers no concrete FoundationReopenCondition.**

---

# 50. MF7-B handoff

Next round must separate:

```text
Difference
Change
Transition
Event
Process
Dynamics
Evolution law
Flow / map / kernel
Trajectory
Run
History
Derivative / rate
Update
Mutation
Action effect
Cause
```

Central attacks:

```text
Change ≠ Difference
Transition ≠ Time Step
Transition Possibility ≠ Transition Occurrence
Dynamics ≠ Sequence
Dynamics ≠ History
Process ≠ FunctionOfTime by identity
Trajectory ≠ Dynamics
History ≠ Log
State Update ≠ Physical Change
Different Observation ≠ State Change
Same State Representation ≠ No Hidden Change
Cause ≠ Transition
```

Key question:

> **What makes a relation/process genuinely dynamical rather than merely a static relation between state descriptions?**

**Next: MF7-B — Change, Transition, Process & Dynamics.**
