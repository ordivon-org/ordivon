# Ordivon Media Foundations — MF7-E Invariants, Stability, Equilibria, Attractors & Regimes

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 42 at start  
**Input:** MF0–MF6 frozen; MF7-A→D complete/provisional.  
**Status:** MF7-E complete/provisional. State & Dynamics Foundations remain UNFROZEN.  
**Next:** MF7-F — Control, Intervention, Feedback, Regulation & Reachability.

---

# 0. Purpose

MF7-D separated bearer persistence/identity from state constancy, structural similarity and lineage. MF7-E asks a different question:

> **What remains invariant, stable, attractive, regulated or regime-defining under a dynamical family and perturbation class?**

Dangerous collapses:

```text
Invariant = Constant State
Invariant = Conserved Quantity
Conserved Quantity = No Dynamics
Symmetry = Conservation Law by identity
Equilibrium = Stability
Equilibrium = Attractor
Fixed Point = Attractor
Steady State = Equilibrium universally
Stationary = Static
Stable = Convergent
Attractive = Stable
Attractor = Goal
Attractor = Equilibrium Point
Basin = Reachability
Stability = Robustness = Resilience
Homeostasis = Static State
Homeostasis = Equilibrium
Metastable = Stable Forever
Regime = State
Regime = Attractor
Mode/Phase = Regime by identity
Bifurcation = Random Jump
Observed Constancy = Invariant Law
One Stable Trajectory = Stable Dynamics
One Return After Perturbation = General Stability
```

---

# 1. Invariant is a relation to admissible evolution, not mere observed constancy

Provisional:

```text
InvariantStanding(I | Dynamics, Domain, EvolutionFamily, Scope)
```

when a property, set, relation, measure or structure is preserved under the declared admissible evolution/transformations for the stated class of initial conditions/inputs.

### SE-001
**Invariant ≠ ObservedConstantOnOneRun.**

### SE-002
One trajectory can accidentally keep a quantity constant without that quantity being invariant under the dynamics family.

### SE-003
An invariant claim must name dynamics/evolution family and scope.

---

# 2. Constant state is one special invariant trajectory, not the invariant concept

A fixed state `x*` satisfying the evolution law without changing is a special trajectory/property.

### SE-004
**Invariant ≠ ConstantState.**

### SE-005
A moving system can preserve energy, angular momentum, topology, probability mass or other quantities while state changes continuously.

### SE-006
Persistence of a bearer from MF7-D is also distinct from invariance of a state property.

---

# 3. Conserved quantity

Provisional:

```text
ConservationClaim(Q | Dynamics, AdmissibleTrajectoryClass)
```

means `Q(state/process)` remains constant along the declared admissible evolution.

### SE-007
**ConservedQuantity ≠ NoDynamics.**

### SE-008
A system can move through a large state-space orbit while a conserved quantity remains fixed.

### SE-009
Conservation is property preservation under dynamics, not bearer/state immobility.

---

# 4. Noether hard case: symmetry and conservation are related but typed

Noether's 1918 invariant variational-problem theorem links continuous transformation groups/invariance of variational problems to identities/conservation structures under specified mathematical conditions.

### SE-010
**Symmetry ≠ ConservedQuantity by identity.**

### SE-011
A symmetry is a transformation/invariance structure; a conserved quantity is a function/quantity preserved along evolution.

### SE-012
The connection requires a declared action/variational structure and theorem conditions; not every informal visual symmetry is automatically a physical conservation law.

---

# 5. Invariant set versus invariant quantity

A set `A` can be invariant if trajectories starting in `A` remain in `A`; a scalar `Q` can be conserved while trajectories move inside a level set.

### SE-013
**InvariantSet ≠ ConservedScalar.**

### SE-014
A conserved quantity can induce invariant level sets `Q(x)=c`.

### SE-015
Invariant standing can apply to sets, measures, relations, manifolds, constraints or properties, not only scalars.

---

# 6. Constraint versus invariant

A state constraint can specify an admissible set even if the declared dynamics does not preserve it automatically.

### SE-016
**Constraint ≠ InvariantSet.**

### SE-017
An invariant constraint/set requires compatibility with evolution: once entered/started there, admissible trajectories respect preservation under scope.

### SE-018
MF7-B `Constraint ≠ Dynamics` remains intact.

---

# 7. Equilibrium standing

For an autonomous deterministic state evolution `x'=f(x)`, an equilibrium state commonly satisfies `f(x*)=0`; for a map `x_{k+1}=F(x_k)`, a fixed point satisfies `F(x*)=x*`.

MF7-E generalizes cautiously:

```text
EquilibriumStanding(E | Dynamics, Inputs/Boundary, Granularity, Scope)
```

when the declared macro/state condition can persist indefinitely under the specified evolution/context without endogenous drift away from that condition class.

### SE-019
**Equilibrium ≠ Stability.**

### SE-020
Equilibrium describes a stationary solution/condition under a law; stability describes behavior under perturbations.

---

# 8. Turing hard case: equilibrium can be unstable

Turing's reaction-diffusion analysis explicitly studies a homogeneous equilibrium that can become unstable to spatially nonuniform disturbances and generate patterns.

### SE-021
**Equilibrium does not imply perturbation stability.**

### SE-022
A system can remain at an equilibrium if placed exactly there, while arbitrarily small relevant perturbations drive it away.

### SE-023
This is a decisive hard case against `Equilibrium = Stable`.

---

# 9. Fixed point versus equilibrium

### SE-024
**FixedPoint is a representation/formal case of equilibrium, not universal equilibrium ontology.**

### SE-025
For maps/flows, fixed points are natural state-space representations; open systems can maintain steady macroscopic conditions through balanced flows even while lower-level variables/processes change.

### SE-026
`FixedPoint` must name which state/granularity map is fixed.

---

# 10. Steady state is not universally equilibrium

A system can maintain time-independent macroscopic observables while sustaining nonzero throughputs/fluxes.

### SE-027
**SteadyState ≠ StaticState.**

### SE-028
**SteadyState ≠ ThermodynamicEquilibrium by universal identity.**

### SE-029
Steady-state standing is level/profile dependent: selected state variables/statistics remain constant while internal process may continue.

---

# 11. Homeostasis provides the organismal steady-regulation hard case

Cannon's homeostasis program treats organismal internal conditions as actively controlled/maintained against environmental variation rather than as mere absence of process.

### SE-030
**Homeostasis ≠ StaticState.**

### SE-031
Homeostatic maintenance can require ongoing sensing, feedback, transport, metabolic work and compensatory changes.

### SE-032
A maintained variable can fluctuate within a viable band rather than remain mathematically constant.

---

# 12. Homeostasis is not equilibrium by identity

### SE-033
**Homeostasis ≠ Equilibrium universally.**

### SE-034
A regulated living system can maintain selected internal variables through active nonequilibrium processes.

### SE-035
The target of regulation may be a range/set/profile rather than one fixed point.

---

# 13. Stability is a perturbation-response relation

Provisional:

```text
StabilityStanding(Target | Dynamics, PerturbationClass, Metric/Equivalence, Horizon, Scope)
```

when perturbations from a reference state/trajectory/set/distribution produce deviations whose future behavior satisfies a declared boundedness/return/convergence criterion.

### SE-036
**Stable is incomplete without perturbation class and target relation.**

### SE-037
Stability can refer to equilibrium, trajectory, set, distribution, process or controlled system.

### SE-038
Stability is not a scalar intrinsic property detached from metric/tolerance/horizon/context.

---

# 14. Lyapunov stability versus asymptotic stability

Lyapunov's stability framework distinguishes staying sufficiently near a reference motion from stronger convergence behavior.

### SE-039
**LyapunovStable ≠ AsymptoticallyStable.**

### SE-040
A trajectory can remain near without converging to the reference.

### SE-041
Asymptotic convergence adds an attraction/limit property beyond bounded-nearness stability.

---

# 15. Stable does not mean fast recovery

### SE-042
**Stability ≠ RecoveryRate.**

### SE-043
Two stable systems can have very different return times/transient excursions.

### SE-044
Recovery time/rate belongs in a separate resilience/transient profile.

---

# 16. Stability does not require equilibrium target

Periodic orbit/trajectory/set stability is meaningful.

### SE-045
**StableTarget ≠ FixedPointOnly.**

### SE-046
A limit cycle can be stable while every state on it changes over time.

### SE-047
Therefore `stable` cannot mean `unchanging`.

---

# 17. Stable cycle hard case

May's 1976 analysis of simple deterministic difference equations explicitly includes stable points and stable cycles of increasing period before chaotic regimes.

### SE-048
**StableDynamics can sustain recurring change.**

### SE-049
A stable periodic orbit is not an equilibrium point, yet can attract nearby trajectories under an appropriate model.

### SE-050
This falsifies `Attractor = FixedPoint` and `Stable = Static`.

---

# 18. Attraction and stability are distinct dimensions

A set can have trajectories approach it from some region while local perturbation behavior requires separate stability conditions; formal attractor definitions differ by field.

### SE-051
**Attractive ≠ LyapunovStable by identity.**

### SE-052
MF7 does not freeze one universal mathematical attractor definition across all domains.

### SE-053
Claims must specify attraction criterion, limiting relation, basin and invariance/stability assumptions if required.

---

# 19. Provisional AttractorStanding

```text
AttractorStanding(A | Dynamics, Basin, LimitRelation, PerturbationClass, Scope)
```

when a state/set/process/statistical structure is invariant or recurrently maintained under the declared dynamics and a nontrivial set of admissible initial conditions approaches/stays asymptotically associated with it under the declared notion of distance/limit.

### SE-054
**Attractor ≠ Goal.**

### SE-055
Attraction is a property of dynamics, not necessarily desired utility or agency.

### SE-056
MF8 Agency must not interpret every attractor as an intention.

---

# 20. Attractor can be more than a point

### SE-057
**Attractor ≠ EquilibriumPoint universally.**

Candidate attracting structures can include fixed points, cycles, invariant sets or more complex bounded sets depending formalism.

### SE-058
Lorenz's bounded nonperiodic deterministic trajectories provide a foundational hard case against reducing long-run organization to fixed points/cycles alone.

### SE-059
An attractor claim must type whether the target is point/set/orbit/distribution/statistical regime.

---

# 21. Basin of attraction

Provisional:

```text
Basin(A) = {initial conditions whose admissible evolution approaches A under declared criterion}
```

### SE-060
**Basin ≠ Attractor.**

### SE-061
Basin describes initial-condition domain feeding an attracting set/profile.

### SE-062
Basin boundaries can strongly affect perturbation outcomes even when local stability near attractor is strong.

---

# 22. Basin is not generic reachability

Reachability asks whether some admissible path can reach a target; basin asks whether evolution from an initial condition converges/approaches under the declared dynamics/policy.

### SE-063
**Basin ≠ Reachability.**

### SE-064
A state can reach an attractor under one control sequence without belonging to its uncontrolled basin.

### SE-065
MF7-B `Reachability ≠ Dynamics` remains intact.

---

# 23. One successful return does not establish stability

### SE-066
**SinglePerturbationRecovery ≠ StabilityLaw.**

### SE-067
A stability claim concerns a perturbation class/neighborhood/family, not one anecdotal run.

### SE-068
Empirical stability requires repeated/structured perturbation evidence or model-grounded guarantees.

---

# 24. One unchanged run does not establish invariance

### SE-069
**ObservedConstancy ≠ InvariantStanding.**

### SE-070
An invariant must survive the declared admissible evolution family, not merely the realized path.

### SE-071
This is the preservation analogue of MF7-B `one trajectory ≠ dynamics`.

---

# 25. Conservation can coexist with instability

### SE-072
A system can conserve a quantity while trajectories separate under perturbations.

### SE-073
**Conservation ≠ Stability.**

### SE-074
Preservation of one scalar does not bound all state deviations.

---

# 26. Stability can exist without an exact conserved quantity

Dissipative systems can converge toward stable sets while quantities such as mechanical energy decrease.

### SE-075
**Stability ≠ Conservation.**

### SE-076
A Lyapunov-like monotone function need not be conserved; it may decrease along trajectories.

### SE-077
Invariant/conserved/monotone structures must be typed separately.

---

# 27. Monotone quantity versus invariant

### SE-078
**MonotoneFunction ≠ ConservedInvariant.**

A monotone function can encode dissipation/progress while changing every step.

### SE-079
Lyapunov functions are certificates/analysis tools under conditions, not necessarily physical conserved quantities.

### SE-080
Representation/certificate standing must not be confused with target state property.

---

# 28. Stability certificate versus stability itself

### SE-081
**LyapunovFunction/Certificate ≠ StabilityStanding by identity.**

### SE-082
A certificate can prove sufficient properties for a model; failure to find one does not establish target instability.

### SE-083
Different certificates can establish the same stability property.

---

# 29. Perturbation class is constitutive to practical stability claims

Perturbations can differ by:

- initial-state displacement;
- sustained disturbance;
- parameter variation;
- model uncertainty;
- structural component failure;
- input shock;
- adversarial action;
- stochastic noise.

### SE-084
**StableToInitialPerturbation ≠ RobustToParameter/ModelChange.**

### SE-085
A system can be locally stable under state perturbation yet fragile to model/parameter changes.

---

# 30. Robustness

Provisional:

```text
RobustnessStanding(Property | Uncertainty/VariationClass, PerformanceCriterion, Scope)
```

when a declared property/performance remains acceptable across a class of model/parameter/environment/component variations.

### SE-086
**Robustness ≠ Stability.**

### SE-087
Stability concerns trajectory response under a fixed/declared dynamics family; robustness often quantifies persistence of a property when the dynamics/model itself varies.

### SE-088
The boundary is domain dependent but must be explicit.

---

# 31. Resilience

Holling's ecological analysis distinguishes persistence/ability to absorb disturbance while maintaining system relationships from notions emphasizing local return toward equilibrium.

MF7 provisional:

```text
ResilienceStanding(System/Regime | DisturbanceClass, Identity/RegimeCriterion, Recovery/AdaptationProfile, Scope)
```

### SE-089
**Resilience ≠ Stability.**

### SE-090
A system can exhibit strong local return around one state yet have low tolerance to a large perturbation crossing a regime/basin boundary.

### SE-091
A resilient system may recover to an acceptable regime/set rather than the exact pre-shock state.

---

# 32. Resilience versus robustness

### SE-092
**Resilience ≠ Robustness.**

### SE-093
Robustness can mean little performance change under variation; resilience can permit substantial deviation/damage followed by persistence/reorganization/recovery.

### SE-094
Recovery, adaptation, absorptive capacity and tolerated regime change should be separately typed rather than merged into one score.

---

# 33. Homeostasis versus resilience

### SE-095
**Homeostasis ≠ Resilience.**

Homeostasis concerns active maintenance/regulation of selected variables/conditions; resilience concerns behavior under disturbances and possible recovery/regime persistence.

### SE-096
A homeostatically regulated variable can fail catastrophically under perturbations outside control authority/resources.

### SE-097
Resilience can involve reconfiguration rather than returning every variable to the old set point.

---

# 34. Set-point regulation is not the universal form of homeostasis

### SE-098
**Homeostasis ≠ ExactSetPointTracking.**

### SE-099
Viable bands, multiple coupled variables, adaptive setpoints and context-dependent ranges remain admissible profiles.

### SE-100
MF7-F will study feedback/regulation mechanisms rather than assuming one controller architecture.

---

# 35. Equilibrium versus homeostatic maintenance

### SE-101
A homeostatically maintained condition can require continuous compensatory flow/work.

### SE-102
**ConstantMacroscopicVariable ≠ NoUnderlyingDynamics.**

### SE-103
This extends MF7-B `MacrostateConstancy ≠ NoDynamics`.

---

# 36. Metastability

Provisional:

```text
MetastabilityStanding(Regime/StateSet | Timescale, Perturbation/Noise, EscapeProfile, Scope)
```

when a system remains for long but finite/condition-dependent periods in a quasi-stable region before transition/escape becomes appreciable under declared noise/perturbation/timescale.

### SE-104
**Metastable ≠ StableForever.**

### SE-105
Metastability is explicitly timescale- and perturbation-dependent.

### SE-106
A metastable state may look stable within short observation windows.

---

# 37. Observation horizon can confound stability classification

### SE-107
**ShortRunPersistence ≠ LongTermStability.**

### SE-108
Slow escape, critical slowing, rare transitions and finite observation windows can produce apparent stability.

### SE-109
Stability claims need horizon/timescale provenance.

---

# 38. Regime standing

MF7-E proposes:

```text
RegimeStanding(R | DynamicsFamily, CoarseVariables, Transition/StatisticalProfile, Parameter/EnvironmentRange, Scope)
```

when a coarse domain of behavior is non-arbitrarily distinguished by a relatively coherent dynamical/statistical/structural profile over a region of state/parameter/environment space.

### SE-110
**Regime ≠ State.**

### SE-111
One regime can contain many states/trajectories and internal fluctuations.

### SE-112
Regime identity depends on declared coarse variables/behavioral criteria.

---

# 39. Regime versus attractor

### SE-113
**Regime ≠ Attractor by identity.**

### SE-114
A regime may be associated with an attractor, metastable set, statistical distribution, mode family or operating region, but the term is broader and more coarse-grained.

### SE-115
Attractor is a dynamical limiting relation; regime is an organizational classification of behavior.

---

# 40. Mode versus regime

A mode can be a discrete formal/control configuration in a hybrid system.

### SE-116
**Mode ≠ Regime universally.**

### SE-117
One mode may contain several dynamical regimes as parameters/states vary; a regime may span several modes in a coarse description.

### SE-118
Henzinger-style discrete mode standing remains separate from emergent regime classification.

---

# 41. Phase is overloaded

`Phase` can mean oscillator phase, thermodynamic phase, phase-space coordinate language, lifecycle stage or mode.

### SE-119
**Phase ≠ Regime by naming.**

### SE-120
Every phase claim must type its domain/criterion.

---

# 42. Bifurcation

Provisional:

```text
BifurcationStanding(DynamicsFamily | Parameter/Control, QualitativeDynamicalChange, Scope)
```

when varying a parameter/context through a critical region changes the qualitative organization of admissible long-term dynamics/solutions (e.g. number/stability/type of equilibria or cycles).

### SE-121
**Bifurcation ≠ RandomJump.**

### SE-122
A deterministic family can undergo bifurcations as a parameter varies.

### SE-123
May's simple difference-equation examples provide a direct hard case: stable point behavior can transition through period-doubling stable cycles into chaotic regimes under deterministic parameter changes.

---

# 43. Bifurcation versus transition occurrence

### SE-124
**BifurcationInModelFamily ≠ OneSystemStateTransitionOccurrence.**

### SE-125
A bifurcation describes qualitative change in dynamics structure across parameter/context, while a transition is an occurrence/path in a fixed/declaration dynamics context.

### SE-126
Parameter sweep order is not Time by MF6; bifurcation parameter need not be temporal.

---

# 44. Critical transition versus bifurcation

### SE-127
**CriticalTransition ≠ Bifurcation by identity.**

A realized system may cross a threshold/change regime due parameter drift/noise/perturbation; the underlying model may or may not involve a mathematical bifurcation.

### SE-128
Empirical abrupt change requires model evidence before being labeled a bifurcation.

---

# 45. Stability can change without identity change

A continuing bearer/process can move from stable to unstable regime while retaining token identity under MF7-D.

### SE-129
**StabilityIdentity ≠ BearerIdentity.**

### SE-130
Identity persistence and dynamical stability are orthogonal profiles.

---

# 46. Identity can end while regime persists

Individual component/process tokens can be replaced while a higher-level regime/service stays stable.

### SE-131
**RegimePersistence ≠ MemberTokenPersistence.**

### SE-132
MF7-D multiscale identity and MF7-E multiscale stability must be co-typed.

---

# 47. Stability of what?

Potential targets:

- state/equilibrium;
- trajectory/orbit;
- invariant set;
- distribution;
- regime;
- process/output;
- controller-plant interconnection;
- identity/continuation property.

### SE-133
**Bare `stable` is semantically incomplete.**

### SE-134
Target type is part of StabilityProfile.

---

# 48. Stability under which metric/equivalence?

Two states can be close spatially but far in task/semantic variables, or vice versa.

### SE-135
**Stability requires a declared deviation/equivalence profile.**

### SE-136
State-space norm is not a universal ontology of deviation.

### SE-137
MF5 physical/perceptual geometry and MF3 semantic/representation structure must not be silently reused as one distance.

---

# 49. Local versus global stability

### SE-138
**LocalStability ≠ GlobalStability.**

### SE-139
A target can be stable for sufficiently small perturbations while larger perturbations leave its basin/regime.

### SE-140
Basin size/geometry and local stability are separate profiles.

---

# 50. Robust stability

### SE-141
**StableNominalModel ≠ RobustlyStableModelFamily.**

### SE-142
Robust stability requires stability preservation across declared model/parameter uncertainty set.

### SE-143
Uncertainty source and admissible variation must be explicit per MF7-C.

---

# 51. Structural stability is another distinct concept

A dynamics family can retain qualitative phase-portrait/topological organization under small model perturbations even when individual trajectories diverge.

### SE-144
**StructuralStability ≠ TrajectoryCloseness.**

### SE-145
MF7 does not yet freeze a universal formal definition, but requires separate typing when used.

---

# 52. Resilience can include regime transformation

Some systems preserve higher-level identity/function while adapting internal structure after perturbation.

### SE-146
**RecoveryToIdenticalPreShockState is not universally required for resilience.**

### SE-147
Resilience profile can distinguish recovery, adaptation, transformation and replacement.

### SE-148
MF7-D identity criterion determines what counts as `same system/regime` after reorganization.

---

# 53. Invariant versus persistent identity

### SE-149
**InvariantProperty ≠ PersistentBearer.**

A bearer can persist while an invariant property changes if dynamics/context changes; an invariant mathematical property can be shared by many distinct bearers.

### SE-150
Persistence is token continuation; invariance is property preservation under evolution.

---

# 54. Conservation versus regulation

A conserved quantity remains fixed because the evolution law preserves it; a regulated variable can remain near target because active feedback compensates disturbances.

### SE-151
**Conservation ≠ Regulation.**

### SE-152
Externally maintaining a quantity does not make it a conservation law.

### SE-153
MF7-F will separate control authority/feedback from autonomous invariance.

---

# 55. Equilibrium versus controlled setpoint

A controller can hold a plant near a non-natural operating point.

### SE-154
**ControlledSteadyCondition ≠ OpenLoopEquilibrium by identity.**

### SE-155
Closed-loop equilibrium belongs to controller+plant dynamics, not necessarily plant-alone dynamics.

### SE-156
Boundary choice changes equilibrium/stability standing just as MF7-C changes open-system state classification.

---

# 56. Attractor versus controller target

### SE-157
A controller can deliberately create/change closed-loop attractors.

### SE-158
**Attractor ≠ Goal**, though a designed goal may be implemented as an attracting set.

### SE-159
Agency/value standing remains deferred to MF8.

---

# 57. Multiple attractors and regime dependence

A dynamics can have multiple attracting sets with distinct basins.

### SE-160
**OneDynamics ≠ OneAttractor.**

### SE-161
Initial condition/perturbation can select among long-run regimes without changing the dynamics law.

### SE-162
Multistability is distinct from stochasticity; deterministic systems can have multiple basins.

---

# 58. Basin crossing versus law change

### SE-163
**RegimeTransition can occur under unchanged dynamics through perturbation crossing a basin boundary.**

### SE-164
Conversely a law/parameter change can alter/remove basins without an immediate state jump.

### SE-165
Dynamics-law change and state/regime transition remain separate.

---

# 59. Hysteresis and regime history dependence

MF7-C established that hysteresis can reflect hidden state/path dependence.

### SE-166
**SameParameterValue ≠ SameRegime under hysteresis.**

### SE-167
Regime membership/transition threshold can depend on path/history.

### SE-168
Bifurcation/regime diagrams must record direction/history assumptions when hysteresis occurs.

---

# 60. Stability and stochastic systems

A stochastic system may use stability notions in probability, distribution, moments, recurrence or invariant measures.

### SE-169
**Deterministic Lyapunov stability definitions do not exhaust stochastic stability.**

### SE-170
MF7-E keeps stochastic stability as a typed profile family rather than forcing all dynamics into deterministic-neighborhood language.

### SE-171
MF7-C probability-law/sample-path distinction remains active.

---

# 61. Stationarity is distribution-level invariance

MF7-C established stationarity ≠ static.

### SE-172
**Stationarity is an invariant property of a stochastic law/distribution under time shift, not one individual state being fixed.**

### SE-173
A stationary process can continuously fluctuate.

### SE-174
Stationarity ≠ attractor ≠ equilibrium by default.

---

# 62. Invariant measure versus attractor

An invariant probability measure can be supported on a set while not being identical to the set.

### SE-175
**InvariantMeasure ≠ AttractorSet.**

### SE-176
Distribution-level invariance and state-set attraction are different claims.

### SE-177
Same mathematical distribution can have physical/ensemble/belief standing depending MF7-A/C route.

---

# 63. Stability of distributions versus sample paths

### SE-178
**DistributionalStability ≠ PathwiseStability.**

### SE-179
A distribution can converge while paired sample paths remain separated; conversely trajectories can stay bounded without ensemble distribution convergence.

### SE-180
Target/equivalence level is mandatory.

---

# 64. Regime detection is inference, not regime ontology

A clustering/change-point algorithm can label regimes from data.

### SE-181
**RegimeLabel/Detection ≠ TargetRegimeStanding.**

### SE-182
Detected clusters can reflect sampling/representation/model assumptions.

### SE-183
Regime claims require target-grounded dynamics/statistical distinctions and provenance.

---

# 65. Stability observation is inference too

### SE-184
**ObservedReturn ≠ ProvenStableDynamics.**

### SE-185
Sensor noise, limited perturbations, finite horizons and hidden variables can misclassify stability.

### SE-186
Stability evidence must separate target behavior, observation model and theoretical guarantee.

---

# 66. Provisional InvariantProfile

```text
InvariantProfile = <
  System/Dynamics,
  InvariantBearer : quantity/set/relation/measure/structure,
  PreservationCriterion,
  EvolutionFamily,
  Initial/Input/Parameter Scope,
  Exact/Approximate?,
  Symmetry/ConservationRelation?,
  Evidence/Proof/Observation,
  Uncertainty,
  Provenance,
  Scope
>
```

### SE-187
`invariant=true` without evolution family/scope is under-specified.

---

# 67. Provisional EquilibriumProfile

```text
EquilibriumProfile = <
  System/Boundary,
  State/Condition Granularity,
  Dynamics/Inputs,
  EquilibriumCondition,
  FixedPointRepresentation?,
  InternalFlux/Process?,
  StabilityProfile?,
  Basin?,
  Regulation/Control?,
  Evidence,
  Uncertainty,
  Provenance,
  Scope
>
```

### SE-188
Equilibrium and stability are separate fields by design.

---

# 68. Provisional StabilityProfile

```text
StabilityProfile = <
  Target : equilibrium/trajectory/set/distribution/regime/etc.,
  Dynamics/Boundary,
  PerturbationClass,
  DeviationMetric/Equivalence,
  Neighborhood/InitialSet,
  Horizon,
  BoundednessCriterion,
  Attraction/ConvergenceCriterion?,
  RecoveryRate/Transient?,
  Local/Global?,
  RobustnessAcrossModels?,
  Stochastic/Deterministic Semantics,
  Evidence/Certificate,
  Uncertainty,
  Provenance,
  Scope
>
```

### SE-189
Bare `stable=true` is under-specified.

---

# 69. Provisional AttractorProfile

```text
AttractorProfile = <
  Dynamics/Boundary,
  AttractingObject : point/orbit/set/distribution/statistical structure,
  Invariance/RecurrentCriterion?,
  Basin/InitialSet,
  Limit/DistanceRelation,
  AttractionHorizon,
  StabilityRequirement?,
  CompetingAttractors?,
  Noise/PerturbationProfile?,
  Evidence,
  Uncertainty,
  Provenance,
  Scope
>
```

### SE-190
MF7-E intentionally leaves exact attractor axioms field-specific until final falsification.

---

# 70. Provisional ResilienceRobustnessProfile

```text
ResilienceRobustnessProfile = <
  System/Bearer/Regime,
  PropertyToPreserve,
  Perturbation/VariationClass,
  AbsorptionCapacity?,
  MaximumDeviation?,
  RecoveryTarget : exact state/set/function/regime/identity,
  RecoveryTime/Rate?,
  Adaptation/Reconfiguration?,
  Model/Parameter Robustness?,
  Basin/Threshold/CriticalTransitions?,
  Resource/Control Dependence?,
  Uncertainty,
  Provenance,
  Scope
>
```

### SE-191
Do not collapse robustness/resilience/homeostasis into one scalar.

---

# 71. Provisional RegimeProfile

```text
RegimeProfile = <
  System/DynamicsFamily,
  CoarseVariables/Observables,
  State/Parameter/Environment Region,
  Characteristic Dynamics/Statistics,
  Attractor/Invariant/Metastable Structure?,
  Mode/Phase Relation?,
  Entry/Exit/Transition Criteria,
  Hysteresis/HistoryDependence?,
  Stability/Resilience?,
  IdentityCriterion?,
  Evidence/DetectionModel,
  Uncertainty,
  Provenance,
  Scope
>
```

### SE-192
Regime is a coarse dynamical organization claim, not one state label.

---

# 72. Strongest non-collapse stack after MF7-E

```text
ObservedConstancy
 ≠ InvariantStanding
```

```text
Invariant
 ≠ ConstantState
 ≠ ConservedQuantity by identity
```

```text
Symmetry
 ≠ ConservedQuantity
```

```text
Constraint
 ≠ InvariantSet
```

```text
Equilibrium
 ≠ Stability
 ≠ Attractor
```

```text
FixedPoint
 ≠ Attractor universally
```

```text
SteadyState
 ≠ StaticState
 ≠ ThermodynamicEquilibrium universally
```

```text
LyapunovStable
 ≠ AsymptoticallyStable
```

```text
Attractive
 ≠ Stable by identity
```

```text
Attractor
 ≠ Goal
 ≠ Regime
```

```text
Basin
 ≠ Attractor
 ≠ Reachability
```

```text
Stability
 ≠ Robustness
 ≠ Resilience
 ≠ Homeostasis
```

```text
Homeostasis
 ≠ StaticState
 ≠ ExactSetPointTracking
```

```text
Metastable
 ≠ StableForever
```

```text
Regime
 ≠ State
 ≠ Mode
 ≠ Phase by naming
```

```text
Bifurcation
 ≠ RandomJump
 ≠ StateTransitionOccurrence
```

```text
Stationary
 ≠ Static
 ≠ Equilibrium
```

```text
InvariantMeasure
 ≠ AttractorSet
```

```text
BearerPersistence
 ≠ DynamicalStability
```

---

# 73. Claims rejected by MF7-E

Reject as universal/foundational:

- a property unchanged on one observed trajectory is a dynamical invariant;
- invariant means state is constant;
- conserved quantity means no motion/dynamics;
- informal symmetry automatically gives a conservation law;
- equilibrium implies stability;
- equilibrium/fixed point automatically attracts nearby states;
- fixed point is the only attractor form;
- steady state means no internal flows/processes;
- steady state universally equals thermodynamic equilibrium;
- homeostasis means static state or exact set point;
- stable means convergent;
- attractive means Lyapunov stable by identity;
- attractor means intended goal;
- basin is generic reachability;
- one recovery observation proves stability/resilience;
- stability/robustness/resilience/homeostasis are interchangeable;
- metastability means permanent stability;
- regime is one state/attractor/mode by identity;
- bifurcation is a random jump or one state transition;
- stationarity means static state;
- invariant measure is the attractor set;
- nominal stability implies robust stability;
- component/member identity persistence is required for regime/system stability;
- stability can be represented by one context-free scalar.

---

# 74. Primary/authoritative evidence anchors

- **Emmy Noether (1918), `Invariante Variationsprobleme`.** Connects continuous invariance groups of variational problems to corresponding identities/conservation structures under theorem conditions; anchors `symmetry ≠ conserved quantity by identity` and `conservation can coexist with nontrivial dynamics`.
- **A. M. Lyapunov (1892; English translation of author-reviewed French version published 1992), `The General Problem of the Stability of Motion`.** Foundational distinction between stability of motion and stronger convergence concepts; anchors perturbation/neighborhood standing rather than static-state identity.
- **Alan M. Turing (1952), `The Chemical Basis of Morphogenesis`.** Explicitly studies instability of a spatially homogeneous equilibrium under disturbances, producing patterned states; anchors `equilibrium ≠ stability` and perturbation-mode dependence.
- **Edward N. Lorenz (1963), `Deterministic Nonperiodic Flow`.** Bounded deterministic nonlinear trajectories can be nonperiodic and unstable to small initial-condition modifications; anchors long-run organization that cannot be reduced to stable fixed-point intuitions.
- **Robert M. May (1976), `Simple Mathematical Models with Very Complicated Dynamics`, and May & Oster (1976), `Bifurcations and Dynamic Complexity in Simple Ecological Models`.** Deterministic difference equations exhibit stable points, stable cycles, bifurcation cascades and chaotic regimes as parameters vary; anchors fixed-point/cycle/regime/bifurcation separation.
- **Walter B. Cannon (1929), `Organization for Physiological Homeostasis`.** Organismal internal constancy is organized/regulated against disturbance rather than equivalent to inactivity; anchors `homeostasis ≠ static state`.
- **C. S. Holling (1973), `Resilience and Stability of Ecological Systems`.** Explicitly distinguishes resilience/persistence under disturbance from equilibrium-centered stability behavior; anchors `resilience ≠ stability` and regime/basin disturbance thinking.

---

# 75. Deep reconstruction

Naive model:

```text
state stops changing → equilibrium → stable
                 ↓
             attractor
                 ↓
      system is robust/resilient

one variable stays constant → invariant/conserved

returns once after shock → resilient
```

MF7-E replaces it with:

```text
Dynamics family + admissible trajectories
                 │
                 ├── property/set preserved ───────> InvariantStanding
                 │        └── scalar constant ─────> ConservationClaim
                 │
                 ├── persistent state solution ────> EquilibriumStanding
                 │
                 ├── response to perturbations ────> StabilityStanding
                 │        ├── bounded-near
                 │        └── attraction/convergence
                 │
                 ├── limiting/recurrent set from basin
                 │                               ──> AttractorStanding
                 │
                 ├── behavior coherent over coarse region
                 │                               ──> RegimeStanding
                 │
                 └── model/environment variation
                          ├── property preserved ───> Robustness
                          └── disturbance absorbed/recovered/adapted
                                                   ─> Resilience

Active regulation can maintain selected variables/sets:
Homeostasis / closed-loop steady behavior
but regulation ≠ conservation ≠ equilibrium.
```

The decisive move is:

> **Preservation and stability are family-level dynamical claims, not observations of temporary constancy. An invariant concerns what a dynamics preserves; equilibrium concerns a state/condition that can persist under the law; stability concerns responses to perturbations; attraction concerns long-run approach from a basin; resilience/robustness concern preservation or recovery across disturbance/model variation; regime concerns coarse organization of behavior. None of these notions can safely substitute for the others.**

---

# 76. Deepest MF7-E result

Provisional:

> **The ontology of dynamical persistence must be typed by what is preserved and under which family of evolutions/perturbations. State constancy, conserved quantities, equilibrium, stability, attraction, steady state, stationarity, homeostasis, robustness, resilience and regime persistence are different preservation/response relations. A stable or resilient system can change continuously; an equilibrium can be unstable; an invariant can coexist with chaotic or nontrivial motion; an attractor need not be a point or a goal; a regime can survive replacement and internal fluctuations without any individual state remaining fixed.**

Compact:

```text
Invariant: what evolution preserves.
Equilibrium: what condition can remain.
Stability: what perturbations do to deviation.
Attraction: what nearby/initial states approach.
Basin: which initials feed that attraction.
Robustness: what survives model/environment variation.
Resilience: what survives/recovers/reorganizes after disturbance.
Homeostasis: what is actively regulated/maintained.
Regime: what dynamical organization remains coherent at a coarse level.
Bifurcation: where the dynamics organization qualitatively changes.
```

---

# 77. MF7-A/B/C/D audit

## MF7-A State
Survives. Equilibrium/stability are properties of state occurrences/sets under dynamics, not definitions of state.

## MF7-B Dynamics
Survives and strengthens. Invariance/stability require an EvolutionStanding family; one trajectory is insufficient.

## MF7-C Stochasticity/Markov
Survives. Distributional/sample-path stability and stationarity remain typed; stochastic stability cannot be collapsed into deterministic notions.

## MF7-D Identity
Survives. Bearer persistence is separate from dynamical stability/regime persistence; component replacement can coexist with higher-level stable regimes.

### SE-193
**MF7-E triggers no restart of MF7-A→D.**

---

# 78. Earlier-foundation audit

- **MF6 Time:** stability/horizon/metastability/recovery depend on temporal profiles but do not redefine Time; no reopen.
- **MF5 Space:** basins/state-space neighborhoods are formal/dynamical geometry, not physical-space identity; no reopen.
- **MF4 Composition:** homeostasis/resilience/regime maintenance may be compositional/multiscale; no reopen.
- **MF3 Representation:** stability certificates, phase diagrams and regime labels represent target dynamics; no reopen.
- **MF2 Perception:** observed constancy/stability is evidence and can differ from target dynamics; no reopen.

### SE-194
**MF0–MF6 remain FROZEN; MF7-E triggers no concrete earlier FoundationReopenCondition.**

---

# 79. MF7-F handoff

Next round must ask how systems are deliberately or endogenously steered rather than merely analyzed:

```text
Control
Intervention
Action/Input
Feedback
Feedforward
Regulation
Policy
Controller State
Plant
Reference/Setpoint
Error Signal
Authority
Actuation
Reachability
Controllability
Observability
Stabilization
Tracking
Constraint Satisfaction
Resource/Cost
Disturbance Rejection
Adaptive Control
Learning vs Control
```

Central attacks:

```text
Control ≠ Cause
Control ≠ Input by identity
Intervention ≠ Observation
Feedback ≠ Control universally
Regulation ≠ Stability
Setpoint ≠ Goal/Utility
Controllability ≠ Reachability by every definition
Reachability ≠ Feasibility under resources/constraints
Stabilization ≠ Natural Stability
ControllerState ≠ PlantState
Policy ≠ Dynamics
Action ≠ StateTransition by identity
ClosedLoopDynamics ≠ PlantDynamics
```

Central question:

> **What makes an influence genuinely control/intervention rather than merely another coupled cause/input, and how do authority, feedback, resource constraints and target criteria alter dynamics?**

**Next: MF7-F — Control, Intervention, Feedback, Regulation & Reachability.**
