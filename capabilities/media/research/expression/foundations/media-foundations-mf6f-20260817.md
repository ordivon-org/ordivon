# Ordivon Media Foundations — MF6-F Time Falsification & Reconstruction

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 37 at start  
**Input:** MF0–MF5 frozen; MF6-A→E complete/provisional.  
**Status:** MF6-F complete. **MF6 Time Foundations v1 FROZEN.**  
**Next:** MF7 — State & Dynamics Foundations.

---

# 0. Purpose

MF6-A→E established a broad typed account of temporal structure across physics, clocks, perception, biology, distributed computation, media and simulation. The remaining danger is over-inclusion.

The provisional formula:

```text
TemporalDomain
 = Temporal Alternatives
 + Temporal Standing
 + Typed Temporal Relation Structure
 + Standing Route
 + Scope
```

was still vulnerable because `Temporal Standing` could become circular or too permissive:

```text
System uses an order
→ call it temporal
→ therefore TemporalStanding
```

That would incorrectly temporalize:

- alphabetical order;
- priority ranking;
- semantic version precedence;
- arbitrary DAG topological order;
- workflow dependency;
- array index;
- optimization iteration number;
- parameter sweep;
- state-transition possibility graphs.

MF6-F must therefore find the Time analogue of MF5-I's `PositionalStanding` firewall.

---

# 1. Final decisive primitive: OccurrenceStanding

MF6-F introduces:

```text
OccurrenceStanding(X, D | Σ)
```

A distinction has **OccurrenceStanding** when it is non-arbitrarily constituted, operationally recruited, represented with grounding, or target-grounded as a distinction in the **obtaining, persistence, cessation, recurrence, or co-occurrence of an event/state/process/condition**, rather than merely as rank, label, dependency, membership, similarity or abstract transition possibility.

### TF-001
**AbstractOrder ≠ OccurrenceStanding.**

### TF-002
**OperationalUseOfOrder ≠ OccurrenceStanding by itself.**

### TF-003
OccurrenceStanding concerns the realization/obtaining profile of relata, not just comparison among symbols.

### TF-004
The primitive does not require conscious observation, physical materiality, a clock, a scalar coordinate, or actual change visible to an observer.

---

# 2. Why `when-like` was not strong enough

MF6-A used `when-like alternatives` as provisional language. This was useful but partly circular.

### TF-005
`CalledWhenLike ≠ TemporalStanding`.

### TF-006
OccurrenceStanding replaces lexical resemblance with a role test: does the domain distinguish how events/states/processes obtain, persist, cease, recur or co-obtain?

### TF-007
Temporal vocabulary alone cannot establish temporal ontology.

---

# 3. Final TemporalStanding

MF6-F reconstructs:

```text
TemporalStanding
 = OccurrenceStanding
 + TemporalRelationStanding
 + StandingRoute
 + Scope
```

where `TemporalRelationStanding` includes one or more relations such as:

- precedence/succession;
- co-occurrence/simultaneity under a reference structure;
- interval overlap/containment/meeting;
- persistence/validity;
- duration/extent;
- rate/frequency/recurrence;
- deadline/horizon/latency;
- reference-relative coordinate time;
- proper-time accumulation;
- presentation/sample/simulation timing.

### TF-008
OccurrenceStanding is constitutive; any particular relation family is not universally constitutive.

---

# 4. Final Time Foundations v1 definition

> **A temporal domain is a scope-relative domain in which distinctions have non-arbitrary standing as alternatives in the obtaining, persistence, cessation, recurrence or co-occurrence of events, states, processes or conditions, and in which one or more typed relations among those alternatives—such as precedence, succession, co-occurrence, interval organization, duration, rate, recurrence, latency, deadline, coordinate-time relation or proper-time relation—are formally constituted, operationally recruited, represented with grounding, or target-grounded. Pure ordering, numbering, ranking, dependency, parameterization, version precedence or state-transition structure does not establish temporal standing unless it is grounded in occurrence/persistence semantics. Clocks, timestamps, metrics, instants, total order, continuity, global simultaneity, observers, change and physical realization are optional enrichments or standing routes rather than universal constituents.**

Compact:

```text
Time / TemporalDomain
 = Occurrence-Possibility Domain
 + OccurrenceStanding
 + Typed Temporal Relation Standing
 + Standing Route
 + Scope
```

### TF-009
This is the MF6 v1 frozen core.

---

# 5. Arbitrary ordered set falsifier

Consider `{a,b,c}` with `a<b<c`.

### TF-010
The set/order alone does not say that `a`, `b`, `c` obtain, persist or occur.

### TF-011
**OrderedSet ≠ TemporalDomain.**

The same order can represent rank, temperature, alphabet, size, utility, version precedence or time.

### TF-012
Structural isomorphism does not transfer temporal standing.

---

# 6. Alphabetic/order hard case

`A < B < C` alphabetically has total order and adjacency.

### TF-013
Alphabetical succession does not imply occurrence succession.

### TF-014
Adding numeric gaps or a metric over alphabet positions still does not create Time.

### TF-015
**Order + Metric ≠ TemporalStanding.**

---

# 7. Priority ranking hard case

Task priority `P0 > P1 > P2` is operationally consumed by a scheduler.

### TF-016
**Operational priority order is not temporal standing by itself.**

A lower-priority task can occur earlier in wall time; priority rank expresses policy preference, not occurrence position.

### TF-017
This directly falsifies `operationally consumed order => Time`.

---

# 8. Semantic version hard case

Version labels `1.0 < 2.0 < 3.0` may encode compatibility/release precedence semantics.

### TF-018
**VersionPrecedence ≠ RevisionOccurrenceTime.**

### TF-019
A version object can separately possess temporal claims such as creation time, validity interval, release date or supersession event.

### TF-020
The same object can therefore have non-temporal version standing and temporal occurrence standing without identity.

---

# 9. Git/DAG history hard case

A commit graph has parent/dependency relations and real commit/repository events.

### TF-021
**CommitParentRelation ≠ CommitPhysicalTimestamp by identity.**

### TF-022
The graph's structural ancestry can have logical/causal-history standing while author/committer timestamps are separate sourced temporal claims.

### TF-023
A topological ordering chosen for display does not become the unique target chronology.

### TF-024
Actual commit occurrences can have temporal standing independently of graph numbering.

---

# 10. Workflow hard case

A workflow says `A must precede B`.

### TF-025
**WorkflowDependency ≠ WorkflowExecutionHistory.**

The dependency can exist before any execution and need not assign duration, start time or actual occurrence.

### TF-026
Once an execution instantiates `A` and `B` as occurring/persisting task episodes, execution-time relations gain temporal standing.

### TF-027
Static procedure structure and realized temporal history must be modeled separately.

---

# 11. State-transition graph hard case — the MF7 firewall

A transition graph specifies which state changes are possible:

```text
S1 → S2
S1 → S3
```

### TF-028
**StateTransitionPossibility ≠ TemporalHistory.**

### TF-029
A graph can be defined without specifying when or whether any transition actually obtains.

### TF-030
A trajectory/run gains temporal standing when state instances/transitions are assigned occurrence/order/persistence in a realized or simulated history.

### TF-031
MF7 owns the ontology/laws of state and change; MF6 owns temporal occurrence relations among state/process instances.

Frozen boundary:

```text
State ≠ TemporalPosition
TransitionRelation ≠ TemporalOrder
Dynamics ≠ Time
RealizedHistory = State/Dynamics + TemporalOccurrenceStanding + Scope
```

---

# 12. Parameter sweep hard case

A model evaluates `f(λ)` for increasing `λ`.

### TF-032
**ParameterProgression ≠ TemporalProgression by default.**

Even if computation visits values sequentially, target `λ` may represent temperature, mass, regularization strength or spatial coordinate.

### TF-033
Execution events have processing-time standing; parameter values do not thereby gain target temporal standing.

---

# 13. Optimization iteration hard case

Iteration `k=100` happens after iteration `k=99` during an execution, but model parameter state `θ_k` also has algorithmic iteration identity.

### TF-034
**IterationIndex ≠ PhysicalElapsedTime.**

### TF-035
The execution episodes can have temporal standing while iteration index remains a computational step coordinate.

### TF-036
Mapping iteration index to temporal occurrence requires explicit execution/run semantics.

---

# 14. Bare array index versus sampled-time index

An array index is ordinal storage structure.

### TF-037
**ArrayIndex ≠ Time.**

When index `n` belongs to a sampled stream with declared clock/sample rate/origin:

```text
t_n = origin + n / fs
```

it gains representational/computational temporal standing through the mapping.

### TF-038
**Index + OccurrenceGrounding/ClockMapping => temporal standing; index alone does not.**

---

# 15. RTP repeats the firewall in a production protocol

RTP separately carries sequence number and sampling timestamp. Sequence numbers track packet transmission sequence; timestamps track sampling instants, can repeat across packets, and may be non-monotonic when transmission order differs from sampling order.

### TF-039
**Transport sequence standing and media occurrence standing are protocol-level distinct roles.**

### TF-040
This is direct evidence that sophisticated systems do not need to collapse ordered units into one time axis.

---

# 16. Logical clocks — admitted, but only at a typed level

Lamport defines happened-before over actual distributed-system events and constructs logical clocks that respect/extend event ordering while separately treating physical clocks.

### TF-041
A bare logical-clock integer is not physical duration.

### TF-042
A logical clock obtains **computational temporal/order standing** only because it is grounded in occurrences of computational events and their happened-before relation.

### TF-043
**LogicalClockStanding ≠ PhysicalClockStanding.**

### TF-044
A generic counter with no occurrence semantics remains non-temporal even if monotonically increasing.

---

# 17. Causal DAG hard case

A causal/dependency DAG can constrain possible influence or explanation.

### TF-045
**CausalDependency ≠ TemporalStanding by definition.**

### TF-046
When causal relata are actual/possible occurrences in a physical/computational history, causality can constrain temporal ordering without becoming identical to all temporal relations.

### TF-047
`CausalOrder ≠ TemporalOrder` remains frozen.

---

# 18. Allen interval algebra protects interval-first temporal standing

Allen's interval approach explicitly models temporal knowledge with intervals and relations such as before, meets, overlaps, starts, during and finishes, particularly where exact dates/instants are inadequate.

### TF-048
**Point/instant primitives are not universally required.**

### TF-049
OccurrenceStanding can attach directly to intervals/process episodes.

### TF-050
Interval relation standing can be temporally legitimate without numerical duration.

---

# 19. Point-first versus interval-first versus event-first — final decision

MF6-F does not select one universal metaphysical primitive.

Frozen:

```text
TemporalAlternative may be:
  occurrence/event
  interval/process episode
  temporal position/instant
  state-validity episode
  phase/recurrence position
  worldline segment
  presentation/sample/simulation occurrence
```

### TF-051
**No universal point-first ontology is frozen.**

### TF-052
**No universal interval-first ontology is frozen.**

### TF-053
**No universal event-first ontology is frozen.**

The constitutive primitive is role/standing, not one representation basis.

---

# 20. Duration remains optional enrichment

A partial/qualitative temporal relation can establish `A before B`, overlap or containment without exact metric duration.

### TF-054
**TemporalStanding does not require DurationMeasure.**

### TF-055
Duration/metric remains an optional enrichment profile.

### TF-056
Clock-free and metric-free temporal domains remain admissible.

---

# 21. Clock remains optional

Clocks realize/estimate/represent temporal relations; they do not constitute all Time.

### TF-057
**TemporalStanding does not require ClockStanding.**

### TF-058
A domain with occurrence/order relations but no measuring clock can remain temporal.

### TF-059
A clock can also be wrong while target temporal standing remains.

---

# 22. Coordinates remain optional

### TF-060
**TemporalPosition ≠ Timestamp/Coordinate.**

### TF-061
An arbitrary coordinate origin/epoch is not the beginning of time.

### TF-062
Coordinate relabeling/reparameterization can preserve temporal standing while changing numerical values.

---

# 23. Total order is not required

Lamport's happened-before relation is partial; relativity also distinguishes invariant causal order from frame-relative order for spacelike-separated events.

### TF-063
**TemporalStanding does not require one global total order.**

### TF-064
Causal incomparability does not automatically mean simultaneity.

### TF-065
Total-order extensions can be useful computational conventions without becoming unique target chronology.

---

# 24. Continuity/density/discreteness are not constitutive

### TF-066
A temporal domain can be modeled discretely, continuously or with mixed/event-driven structure depending scope.

### TF-067
**Discrete representation ≠ discrete target time.**

### TF-068
**Continuous coordinate ≠ proof of continuously realized target events.**

---

# 25. Change is not constitutive of Time

A fixed historical record or block-spacetime representation can carry temporal occurrence relations without a current observer witnessing change.

### TF-069
**Time ≠ Change.**

### TF-070
Change/dynamics describe differences/transitions in state; temporal standing organizes when/how long/with what recurrence those state/process instances obtain.

### TF-071
MF7 may model change without redefining Time.

---

# 26. Time is not dynamics

A dynamical law can be expressed over a parameter, but target temporal interpretation requires occurrence standing.

### TF-072
**DynamicalEquation ≠ TemporalOntology.**

### TF-073
A timeless constraint relation over possible states is not temporal merely because solutions can be parameterized.

### TF-074
Conversely a temporal domain need not specify transition laws/dynamics.

---

# 27. Relativity passes the reconstructed core

Einstein's synchronization analysis and Minkowski spacetime demonstrate reference-relative coordinate times/simultaneity, invariant causal structure and worldline-local proper time.

### TF-075
OccurrenceStanding survives spacetime unification: events/worldline segments obtain as spacetime occurrences while spatial and temporal roles remain typed.

### TF-076
**SpacetimeCoupling ≠ PositionalStanding = TemporalStanding.**

### TF-077
MF5 remains frozen.

---

# 28. Proper time passes without becoming universal Time

### TF-078
Proper time is a duration measure along a timelike worldline, an enrichment over temporal occurrence structure.

### TF-079
**ProperTime ≠ GlobalTemporalCoordinate.**

### TF-080
OccurrenceStanding can apply to null/spacelike event relations even where material-clock proper duration is not the relevant measure.

---

# 29. Simultaneity remains typed

### TF-081
**RemoteSimultaneity requires reference/frame/synchronization structure where relativity matters.**

### TF-082
Local coincidence, coordinate simultaneity and perceptual simultaneity remain non-identical.

### TF-083
Global universal present is not a constitutive Time primitive.

---

# 30. Perceptual time passes without multiplying worlds vacuously

MF6-D found task/modality/history/action-dependent temporal perception.

### TF-084
Perceptual temporal standing is legitimate because the perceptual system discriminates occurrence/order/simultaneity/duration relations among sensory/sensorimotor events.

### TF-085
The existence of distinct perceptual profiles does not create separate physical times; it creates typed mappings from physical/signal occurrence structure to perceptual occurrence organization.

### TF-086
**Typed temporal plurality ≠ ontological anything-goes.**

Standing route and mapping/provenance constrain each profile.

---

# 31. Biological timing passes, but oscillator state alone does not

An oscillator state/phase is dynamical structure.

### TF-087
**OscillatorState ≠ Time by identity.**

When phase/period/recurrence are recruited to organize the timing of biological occurrences—sleep/wake, hormonal release, feeding anticipation, etc.—biological temporal standing is established.

### TF-088
**BiologicalTimingStanding = dynamics + occurrence/recurrence recruitment, not dynamics alone.**

### TF-089
This preserves the MF6/MF7 boundary.

---

# 32. Circadian phase hard case

The same phase recurs each cycle.

### TF-090
**Phase ≠ unique temporal position.**

### TF-091
Phase becomes temporal relation standing only relative to an oscillator/cycle and occurrence mapping.

### TF-092
`CircadianPhase ≠ GlobalTime` remains frozen.

---

# 33. Action time passes through occurrence consequences

Deadlines, expected delays and control horizons concern when actions/outcomes may obtain and how long opportunities persist.

### TF-093
**ActionTemporalStanding is grounded by occurrence-sensitive consequences for feasibility/control.**

### TF-094
Priority/utility order alone is not temporal; deadline/horizon/latency relations are.

---

# 34. Simulation time passes as enacted temporal standing

Simulation time is not metaphor merely because it differs from wall time.

### TF-095
Simulation states/processes are assigned occurrence/persistence relations under an enacted simulation timeline.

### TF-096
Pause, rate change, rewind and branching demonstrate that simulation occurrence standing is independently manipulable from wall-clock standing.

### TF-097
**SimulationTime is genuine computational temporal standing at its target/system level, not physical wall time.**

---

# 35. Media presentation time passes as designed occurrence standing

PTS specifies when a frame should occupy/present on a media presentation timeline; duration specifies how long it occupies that interval; DTS specifies decoding dependency timing.

### TF-098
**PresentationTime has designed/operational occurrence standing.**

### TF-099
It does not automatically transfer to original source/capture occurrence time.

### TF-100
DecodeTime and PresentationTime can both be temporal at different system levels while remaining non-identical.

---

# 36. Edited timeline hard case

A film can reorder source events while preserving a coherent presentation timeline.

### TF-101
**PresentationOccurrenceStanding ≠ RepresentedTargetOccurrenceStanding.**

### TF-102
Temporal representation may intentionally transform order/duration.

### TF-103
Source chronology transfer requires MF3-style grounding/provenance, not shared numeric timestamps.

---

# 37. Watermarks do not gain target Time standing

A stream watermark estimates computational completeness relative to event timestamps.

### TF-104
**WatermarkStanding is progress/completeness standing, not EventOccurrenceStanding.**

### TF-105
It is temporally related metadata about expected event-time progress but should not be typed as a target event time itself.

This demonstrates that temporal systems can contain non-temporal control variables related to time.

---

# 38. Buffer depth/latency/jitter do not become Time objects

### TF-106
Latency is a duration relation; jitter is variation in latency; buffer depth is a resource/control state.

### TF-107
**Temporal quantity/relation ≠ Temporal domain by itself.**

A scalar duration can be a property of a transformation without being a standalone temporal world.

---

# 39. Retiming counterfactual — strong diagnostic

Where meaningful, hold non-temporal identity/content/dependency fixed and alter occurrence placement/extent:

- delay an event;
- stretch an interval;
- shift a presentation;
- pause a simulation;
- alter a deadline;
- change sampling cadence.

### TF-108
If declared occurrence/persistence/overlap/deadline/latency consequences change systematically, this strongly supports TemporalStanding.

### TF-109
**RetimingCounterfactual is a diagnostic, not a universal constitutive requirement.**

Historical facts or pure formal temporal calculi may not admit physically realizable retiming while still having temporal standing.

---

# 40. Relabeling diagnostic

Replace words `before`, `after`, `time`, `later` with generic `<`, `>`, `rank` while preserving all formal operations.

### TF-110
If no occurrence/persistence semantics or consumer consequence is lost, the structure was probably only abstract order.

### TF-111
If changing the supposed temporal relation changes occurrence/persistence/scheduling/presentation semantics, temporal standing has stronger evidence.

---

# 41. Degrounding diagnostic

Remove the mapping between a timestamp/counter and target/system occurrences.

### TF-112
If only numeric/order structure remains, target temporal standing does not survive degrounding.

### TF-113
This distinguishes PTS from source-event time, sample index from sampling time, and logical clock integer from physical duration.

---

# 42. Standing routes — final v1

Nonexclusive standing routes:

1. **Formal/Axiomatic Temporal** — events/intervals/occurrence alternatives explicitly constituted in a temporal calculus.
2. **Physical/Spacetime** — target events/worldlines/processes with physical temporal/causal/proper-time relations.
3. **Perceptual/Experiential** — perceived/experienced order, simultaneity, duration, presentness.
4. **Biological/Physiological** — recurrence/phase/interval relations functionally recruited by organisms.
5. **Action/Control** — deadlines, horizons, latency and temporal opportunity constraints.
6. **Computational/Logical** — event-order/logical-clock/scheduler/monotonic temporal roles grounded in execution occurrences.
7. **Designed/Enacted Media/Simulation** — presentation/sample/simulation timelines whose occurrences are constituted by system rules.
8. **Representational/Institutional** — calendars, timestamps, schedules and timelines standing for target temporal relations.
9. **Hybrid** — combinations.

### TF-114
**StandingRoute ≠ EvidenceRoute.**

A physical occurrence may be evidenced by a timestamp; a represented temporal claim can be checked by a clock; measurement does not define the target route.

---

# 43. Final standing ladder

```text
L0 — Nominal/metaphorical `time`
     e.g. "time dimension" label with no semantics

L1 — Abstract order/index/parameter/dependency
     sequence, rank, DAG, counter

L2 — Formal/operational temporal standing
     occurrence/persistence semantics enacted or axiomatically constituted
     e.g. logical event time, simulation time, media presentation time

L3 — Representational temporal standing
     timestamps/timelines/calendars grounded as standing for another target's timing

L4 — Target temporal standing
     independently evidenced physical/perceptual/biological/action occurrence relations
```

### TF-115
Levels are standing/evidence distinctions, not `reality ranks`.

### TF-116
Formal temporal domains can be legitimate terminal targets at L2 when the formal system itself is the target.

---

# 44. Final standing-transfer rule

```text
Abstract Order/Parameter
 + OccurrenceStanding
 => Formal/Operational TemporalStanding
```

```text
Operational/Formal TemporalStanding
 + MF3 Grounded Mapping/Fidelity
 => Representational TemporalStanding
```

```text
Representational TemporalStanding
 + Independent Target Occurrence Evidence
 => Target TemporalStanding
```

### TF-117
No arrow reverses by default.

### TF-118
Useful operational timing does not prove represented physical time is correct.

### TF-119
Target temporal standing does not imply one particular coordinate/clock representation.

---

# 45. Final TemporalProfile

```text
TemporalProfile = <
  Domain,
  OccurrenceBearers/TemporalAlternatives,
  OccurrenceStanding,
  TemporalRelationFamilies,
  StandingRoute,
  OrderStructure?,
  IntervalStructure?,
  Duration/Measure?,
  Rate/Periodicity?,
  CausalStructure?,
  Coordinate/Timescale?,
  Clock/MeasurementProfile?,
  Reference/Frame/Simultaneity?,
  ProperTime/Worldline?,
  Perceptual/ExperiencedProfile?,
  BiologicalProfile?,
  ActionProfile?,
  Computational/LogicalProfile?,
  Media/SimulationProfile?,
  Representation/InstitutionalProfile?,
  Equivalence/Invariants,
  Uncertainty/Vagueness,
  Provenance/Authority,
  Scope
>
```

### TF-120
Only the occurrence/standing/relation/route/scope core is constitutive; most fields are optional enrichments.

---

# 46. Final TemporalClaim

```text
TemporalClaim = <
  Relata/Event/State/Process/Condition,
  OccurrenceRole,
  RelationType,
  StandingRoute,
  Reference/Frame/Clock/Timeline if applicable,
  Coordinate/Timestamp/Interval/Duration if applicable,
  TemporalRole : event/validity/observation/processing/presentation/etc.,
  MappingToOtherTemporalDomains?,
  Precision/Resolution?,
  Uncertainty/Vagueness,
  Evidence/Provenance,
  Scope
>
```

### TF-121
Bare timestamps remain under-specified.

---

# 47. Final MF6 non-collapse stack

```text
Time / TemporalStanding
 ≠ R
 ≠ Sequence
 ≠ Change
 ≠ Dynamics
```

```text
AbstractOrder
 ≠ OccurrenceStanding
```

```text
VersionPrecedence
 ≠ RevisionOccurrenceTime
```

```text
WorkflowDependency
 ≠ WorkflowExecutionHistory
```

```text
StateTransitionPossibility
 ≠ TemporalHistory
```

```text
ParameterProgression
 ≠ TemporalProgression
```

```text
Clock
 ≠ ClockReading
 ≠ TimeUnit
 ≠ Timescale
 ≠ TargetTime
```

```text
TemporalPosition
 ≠ Timestamp
 ≠ Event
```

```text
TemporalOrder
 ≠ Duration
 ≠ CausalOrder
```

```text
CoordinateTime
 ≠ ProperTime
```

```text
PhysicalTime
 ≠ PerceptualTime
 ≠ ExperiencedTime
 ≠ BiologicalTiming
 ≠ ActionTime
```

```text
LogicalClock
 ≠ PhysicalClock
```

```text
FrameIndex
 ≠ PTS
 ≠ DTS
 ≠ Duration
```

```text
EventTime
 ≠ ProcessingTime
 ≠ PresentationTime
```

```text
SimulationTime
 ≠ WallClockTime
```

```text
PresentationOccurrenceStanding
 ≠ RepresentedTargetOccurrenceStanding
```

```text
SpatialStanding
 ≠ TemporalStanding
```

---

# 48. MF6 v1 frozen axioms

## T1 — Standing before representation
A coordinate/timestamp/order does not constitute Time without temporal/occurrence standing.

## T2 — Occurrence firewall
Temporal standing requires non-arbitrary occurrence/persistence/co-occurrence role; generic order/rank/dependency is insufficient.

## T3 — Typed relation bundle
No one temporal relation family—order, simultaneity, duration, recurrence—is universally sufficient/necessary by itself.

## T4 — Order is weaker than measure
Temporal order/interval structure can exist without quantitative duration.

## T5 — Clock is enrichment/evidence
Clocks realize/estimate/reference temporal relations; Time is not reduced to clock readings.

## T6 — No universal total/global chronology
Partial order, reference-relative order and local temporal structure are admissible.

## T7 — Relativity typing
Coordinate time/simultaneity, invariant causal order and worldline proper time are distinct typed relations.

## T8 — Point/interval/event neutrality
No one representational/metaphysical primitive is required across all temporal domains.

## T9 — Organismal plurality
Perceptual, experienced, biological and action temporal profiles are coupled but non-identical to physical/clock time.

## T10 — Computational/media legitimacy without transfer
Simulation, logical and presentation times can have real operational temporal standing without becoming target physical time.

## T11 — Time is not dynamics/causality
State/change/dynamics and causality can constrain temporal structure but are not identical to Time.

## T12 — Transfer is grounded
Formal/computational/media temporal standing transfers to represented target timing only through explicit grounded mapping and independent target evidence.

## T13 — Uncertainty/provenance first-class
Temporal claims can be partial, interval-bounded, vague, clock-uncertain or mapping-uncertain; fabricated exact timestamps are not required.

## T14 — Structural isomorphism does not erase temporal role typing
The same order, graph or real line can be temporal or non-temporal depending standing.

---

# 49. Claims rejected by MF6-F

Reject as universal/foundational:

- every operational order is temporal;
- every sequence/version/workflow/DAG is a timeline;
- state transition graph is temporal history by identity;
- model parameter or iteration number is target time;
- ordering plus a metric is sufficient for Time;
- temporal vocabulary/naming establishes temporal ontology;
- one universal scalar/line/clock is constitutive of Time;
- Time requires points/instants;
- Time requires intervals as the unique primitive;
- Time requires metric duration;
- Time requires a clock;
- Time requires continuity/density/discreteness of one fixed type;
- Time requires global total order or global simultaneity;
- Time equals change, dynamics or causality;
- proper time is the universal global temporal coordinate;
- perceptual/biological/action timing are mere errors around one internal clock;
- biological oscillator phase is global Time;
- logical clock values are physical elapsed time;
- simulation/media presentation time is metaphor merely because it differs from wall time;
- presentation time automatically equals represented source/event time;
- timestamp equality across unmapped domains proves temporal identity;
- useful temporal prediction/operation proves target temporal truth.

---

# 50. Primary/authoritative falsification anchors

- **Leslie Lamport (1978), `Time, Clocks, and the Ordering of Events in a Distributed System`.** Defines happened-before as a partial ordering over distributed-system events, constructs logical clocks/total-order extensions, and treats physical clock synchronization separately. Supports `event-order standing ≠ physical duration`, `partial order ≠ global timestamp line`, and logical/physical clock separation.
- **James F. Allen (1983), `Maintaining Knowledge about Temporal Intervals`, Communications of the ACM 26(11):832–843.** Introduces interval-based temporal reasoning specifically for cases where exact dates/instants are inadequate; supports interval-first admissibility and qualitative temporal relations without metric duration.
- **RFC 3550, RTP.** Separates packet sequence numbers from media sampling timestamps; timestamps can repeat or be non-monotonic while transmission sequence numbers remain monotonic, and cross-stream synchronization requires reference-clock mappings. This is a production hard case for `sequence ≠ time` and temporal standing transfer.
- **POSIX / The Open Group clock APIs.** `CLOCK_MONOTONIC` has an arbitrary/unspecified origin but supports stable elapsed-time measurement and is distinct from settable realtime/civil clock coordinates. This supports `global epoch ≠ temporal utility/standing` and wall-clock/monotonic separation.
- **Einstein (1905), `Zur Elektrodynamik bewegter Körper`; Minkowski (1908), `Raum und Zeit`.** Remote common time/simultaneity requires reference/synchronization structure; spacetime unification preserves typed causal/proper-time versus coordinate relations. Supports no universal absolute timestamp/simultaneity and preserves MF5/MF6 role separation.

---

# 51. Deep reconstruction

Naive model:

```text
anything ordered
   ↓
call the order time
   ↓
assign timestamps
   ↓
sort timestamps
   ↓
claim one chronology
```

MF6 v1:

```text
Relata / possible conditions / events / processes
                  │
                  ▼
          OccurrenceStanding
   obtaining / persistence / cessation /
      recurrence / co-occurrence
                  │
                  ▼
     Typed Temporal Relation Standing
   ┌──────────────┼────────────────┐
   ▼              ▼                ▼
 order/interval  duration/rate   causal/reference
   │              │                │
   └────── optional enrichments ────┘
                  │
          standing-route typing
   physical / perceptual / biological /
   action / computational / media /
   representational / formal
                  │
                  ▼
      clocks / timestamps / timelines
        as measurement/representation
                  │
                  ▼
 explicit grounded mapping between domains
```

The decisive move is:

> **Time is not abstract order. Time is occurrence-structured standing. Order, duration, clocks and coordinates are typed structures over or representations of that standing.**

---

# 52. Deepest MF6 result

The deepest result of MF6-A→F is:

> **Temporal structure begins not with a clock or a line, but with distinctions in how events, states, processes or conditions obtain, persist, cease, recur or co-occur. Once such OccurrenceStanding exists, a domain may enrich it with precedence, intervals, duration, rates, clocks, coordinates, simultaneity, causal constraints, perceptual organization, biological timing, action horizons, logical clocks, media presentation or simulation time. These enrichments can be operationally real at their own standing route while remaining non-identical across routes. Generic ordering, transition possibility, numbering and dependency remain outside Time unless they are grounded in occurrence/persistence semantics.**

Compact:

```text
Time is occurrence-structured, not merely ordered.

Order says relative precedence.
Intervals organize persistence.
Duration measures extent.
Clocks realize/reference measure.
Coordinates describe.
Relativity types invariance/reference.
Perception calibrates occurrence relations.
Biology entrains recurrence.
Action consumes horizons/deadlines.
Computation enacts logical/simulation timing.
Media schedules sample/decode/presentation occurrences.

None alone is universal Time.
```

---

# 53. Point/interval/event question — closed for v1

MF6 does not need to solve the philosophical question `what is ultimately primitive: instants, intervals, events, change?` to have a useful foundation.

### TF-122
The frozen core is intentionally **basis-neutral**.

### TF-123
Point-, interval- and event/process-based formalisms are alternative constructions over OccurrenceStanding under declared equivalences/scope.

### TF-124
A future empirical/formal result can reopen this only if one basis is shown necessary to every coherent temporal standing.

---

# 54. Final MF7 boundary

MF7 begins with:

```text
What is a State?
What is Change?
What is a Transition?
What is a Process/Dynamics law?
What makes a trajectory/history?
What is persistence/identity through change?
```

MF6 contributes only temporal substrate:

```text
when/relative occurrence
persistence interval
before/after/co-occurrence
duration/rate/deadline
clock/reference mappings
```

### TF-125
**MF7 may consume Time Foundations but must not redefine Time as Change.**

### TF-126
**MF6 must not predefine dynamics simply because temporal histories exist.**

---

# 55. MF6 FoundationReopenConditions

Reopen MF6 v1 only on a concrete case satisfying one of the following:

1. **Occurrence-Core Counterexample** — a clearly temporal domain cannot coherently be expressed through occurrence/persistence/co-occurrence standing of events/states/processes/conditions or equivalent alternatives.
2. **Over-Inclusion Failure** — a clearly non-temporal rank/order/dependency/parameter system passes the OccurrenceStanding firewall without an independent temporalization/occurrence semantics.
3. **Universal-Structure Evidence** — clocks, metric duration, instants, total order, continuity, global simultaneity, change or another optional field is shown necessary to all temporal standing.
4. **Relativity Failure** — proper/coordinate/causal typing becomes incoherent under a concrete relativistic model.
5. **Organismal Failure** — perceptual/biological/action temporal profiles cannot be separated from physical/reference time without contradiction.
6. **Computational/Media Failure** — logical/simulation/presentation time cannot coherently have operational temporal standing without either becoming mere metaphor or falsely transferring to physical target time.
7. **Standing-Transfer Failure** — grounded mapping cannot distinguish vehicle/system temporal standing from represented target occurrence time.
8. **MF7 Boundary Failure** — a concrete state/dynamics theory shows occurrence standing necessarily collapses into change/dynamics or vice versa.
9. **Circularity Failure** — OccurrenceStanding proves vacuous/circular under adversarial formalization and cannot be operationally distinguished from generic ordering.
10. **Point/Interval/Event Necessity Evidence** — one primitive basis is demonstrated necessary across all coherent temporal domains.

### TF-127
No current MF6-A→F hard case triggers these conditions.

---

# 56. Earlier-foundation audit

## MF0 Media Ontology
Temporal mediation remains optional/contextual; no reopen.

## MF1 Signal
Sampling, latency, timing uncertainty/provenance fit existing distinction-flow model; no reopen.

## MF2 Perception
Temporal discrimination/recalibration fits frozen stateful selective action-coupled perception; no reopen.

## MF3 Representation
Timestamp/timeline standing transfer confirms representation grounding; no reopen.

## MF4 Composition
Temporal ordering/synchronization are typed organization relations; no reopen.

## MF5 Space
Relativistic spacetime coupling remains compatible with scope-relative PositionalStanding; no reopen.

### TF-128
**MF0–MF5 remain FROZEN.**

---

# 57. Freeze decision

MF6-F attacked:

- arbitrary total orders;
- ranking;
- semantic versions;
- Git/DAG ancestry;
- workflows;
- state-transition graphs;
- parameter sweeps;
- optimization iterations;
- array/sample indices;
- logical clocks;
- causal DAGs;
- interval-only temporal models;
- metric/clock-free time;
- relativity;
- perceptual temporal plurality;
- biological oscillators/circadian phase;
- action deadlines/horizons;
- simulation time;
- media presentation/decode/source time;
- watermarks/buffering/latency.

The provisional `when-like` core required reconstruction, but the revised `OccurrenceStanding` firewall survived the tested over-/under-inclusion cases.

### TF-129
**MF6 Time Foundations v1 is FROZEN.**

### TF-130
Freeze means current stable substrate, not final metaphysical truth. Reopen only through the explicit FoundationReopenConditions above.

---

# 58. Handoff

Next frontier:

```text
MF7 — State & Dynamics Foundations
```

MF7 should begin without assuming:

```text
State = Snapshot
State = Memory
State = Vector
Change = Difference
Transition = Time Step
Dynamics = Sequence
Process = Function of Time
History = Log
Persistence = Same Identifier
Cause = Transition
```

First required split:

```text
State
Condition
Property
Configuration
Snapshot
Observation
Representation
Memory
Change
Transition
Process
Dynamics
Trajectory
History
Persistence
Identity
Invariant
Attractor
Control
```

with the explicit bridge:

```text
PossibleTransitionStructure ≠ RealizedTemporalHistory
```

**Next: MF7-A — State Ontology & Term Separation.**
