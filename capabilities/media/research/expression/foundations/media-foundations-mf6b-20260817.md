# Ordivon Media Foundations — MF6-B Temporal Order, Interval, Duration, Measure & Clocks

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 33 at start  
**Input:** MF0–MF5 frozen; MF6-A complete/provisional.  
**Status:** MF6-B complete and PROVISIONAL. Time Foundations remain UNFROZEN.  
**Next:** MF6-C — Relativity, Proper Time, Simultaneity & Spacetime.

---

# 0. Purpose

MF6-A established:

```text
Time ≠ R ≠ Sequence ≠ Change
Clock ≠ ClockReading ≠ TimeUnit ≠ Timescale ≠ Time
TemporalPosition ≠ Timestamp ≠ Event
TemporalInterval ≠ Duration
LogicalTime ≠ PhysicalTime
```

MF6-B asks:

> **What extra structure is required to move from temporal standing and qualitative order to intervals, numerical duration, measurement and clocks?**

The dangerous collapses are:

```text
Order = Duration
Interval = Duration
Point-Time = Interval-Time
Before = Positive Metric Distance
Temporal Metric = Temporal Order
Equal Duration = Same Interval
Clock = Oscillator = Time
Same Frequency = Same Clock Time
Synchronization = Syntonization
Same Offset Once = Same Rate
Monotonic = Accurate
Stable = Accurate
High Resolution = High Accuracy
Precision = Resolution = Stability = Accuracy
Clock Error = Frequency Error
Logical Clock = Physical Clock
Clock Reading Difference = Target Duration universally
```

MF6-B deliberately stays mostly pre-relativistic/abstract. Proper time, coordinate time, inertial/gravitational effects and spacetime invariants are deferred to MF6-C.

---

# 1. Temporal order is the weakest major enrichment above standing

A strict temporal precedence relation can be represented provisionally as:

```text
Earlier(a,b)
```

with domain-specific properties such as irreflexivity and transitivity when justified.

### TB-001
**Temporal precedence can be meaningful without numerical timestamps or duration.**

### TB-002
`Earlier(a,b)` does not imply a known value for how much earlier.

### TB-003
Order is therefore structurally weaker than duration measure.

---

# 2. Strict and non-strict orders are descriptions, not Time itself

One may use `<` for strict precedence and `≤` for precedence-or-coincidence under a model.

### TB-004
**StrictOrder ≠ NonStrictOrder ≠ TemporalDomain.**

### TB-005
The algebra chosen to encode order is a formal enrichment/description of temporal standing.

---

# 3. Partial order remains legitimate

Lamport's `happened-before` relation gives a partial order over distributed events; independent/concurrent events can be incomparable even though each process has local order.

### TB-006
**A temporal/order domain does not universally require one known total order.**

### TB-007
Adding a total tie-breaking order for computation does not retroactively establish physical elapsed-time facts.

### TB-008
`TotalOrderExtension ≠ NewPhysicalTemporalEvidence`.

---

# 4. Total order and simultaneity are different structures

A total order can prohibit incomparability by convention, while simultaneity/equivalence can group alternatives as co-temporal under a declared reference.

### TB-009
**TotalOrder ≠ SimultaneityStructure.**

### TB-010
A tie-breaker can order two events that are causally unrelated without claiming one physically preceded the other.

---

# 5. Temporal order may be discrete or dense

A formal temporal domain may have immediate successors (`tick n → tick n+1`) or permit alternatives between any two ordered positions.

### TB-011
**TemporalStanding does not universally require discreteness.**

### TB-012
**TemporalStanding does not universally require density/continuity.**

### TB-013
Discrete logical ticks and continuous physical models are different valid temporal profiles.

---

# 6. Temporal topology is optional enrichment

Order can induce/use notions of neighborhood, limit and continuity, but temporal standing can exist in a finite/discrete event order without a rich continuum topology.

### TB-014
**TemporalTopology ≠ TemporalStanding by identity.**

### TB-015
Continuity/discreteness must remain declared properties rather than built into the universal core.

---

# 7. Interval-first models are a decisive anti-point-reduction hard case

James F. Allen's temporal-reasoning program explicitly treats intervals as primary objects and develops interval relations without requiring all reasoning to reduce first to timestamped instants.

### TB-016
**Temporal interval reasoning can be semantically useful without primitive numerical endpoints.**

### TB-017
MF6 therefore does not freeze point-first temporal ontology.

### TB-018
Likewise, interval-first representation need not deny point/instant models; the two can be interdefined under additional assumptions in some formalisms.

---

# 8. Allen-style interval relation family separates qualitative structure from duration

For two nondegenerate intervals, the classic family distinguishes relations corresponding to:

```text
before / after
meets / met-by
overlaps / overlapped-by
starts / started-by
during / contains
finishes / finished-by
equal
```

### TB-019
**Interval relations encode temporal organization without assigning numerical length.**

### TB-020
`Before ≠ Meets ≠ Overlaps ≠ During ≠ Starts ≠ Finishes ≠ Equal`.

### TB-021
The inverse relation of an interval relation is itself semantically typed; reversing relata is not merely negation.

---

# 9. Interval relation does not determine duration

Two intervals may both satisfy `A before B` while being one nanosecond or one century apart.

### TB-022
**Qualitative interval relation ≠ quantitative separation.**

Two intervals may satisfy `overlaps` while their overlap fraction/duration differs arbitrarily.

### TB-023
**OverlapRelation ≠ OverlapDuration.**

---

# 10. Same duration does not mean same interval

Intervals `[0,1]` and `[5,6]` under a simple coordinate model can have equal duration while occupying different temporal regions.

### TB-024
**EqualDuration ≠ IntervalIdentity.**

### TB-025
Temporal extent is one property of an interval, not its identity.

---

# 11. Same interval can receive different numerical duration representations

One second = 1000 milliseconds under exact unit conversion.

### TB-026
**DurationQuantity ≠ NumericalRepresentation.**

### TB-027
Unit conversion can alter the number while preserving the measured duration relation.

---

# 12. Interval boundaries and duration measurement are separable

One may know duration accurately while having conventional/criterion-dependent onset boundaries, or know interval ordering without precise duration.

### TB-028
**BoundaryStanding ≠ DurationMeasure.**

### TB-029
Temporal boundary vagueness and duration uncertainty must remain typed separately.

---

# 13. Open/closed endpoint conventions are representational/formal choices

Formal intervals may include/exclude endpoints depending on model.

### TB-030
**Endpoint-inclusion convention ≠ target temporal ontology universally.**

### TB-031
For continuous measure, endpoint inclusion may not alter duration while it can alter membership/equality/contact-like relations.

---

# 14. Degenerate/zero-duration intervals require typed treatment

Some formalisms admit `[t,t]`; Allen's classic interval calculus is usually formulated for nonzero finite intervals.

### TB-032
**Instant-like degeneracy ≠ ordinary extended interval by default.**

### TB-033
MF6 should not silently use an interval algebra's assumptions as universal ontology.

---

# 15. Duration is a measure-like enrichment, not interval identity

MF6-B provisionally defines:

```text
Duration(I | M, reference, scope)
```

as quantitative temporal extent assigned to interval/process `I` under a temporal measure structure `M`.

### TB-034
**Duration requires more structure than qualitative order alone.**

### TB-035
Temporal standing and interval structure can be valid when duration is unknown or undefined.

---

# 16. Additivity is powerful but conditional

In familiar additive temporal measure, adjacent non-overlapping intervals can satisfy:

```text
Dur(A ∪ B) = Dur(A) + Dur(B)
```

when `A` and `B` meet appropriately and the measure model permits composition.

### TB-036
**Duration additivity is a property of a measure structure, not a universal consequence of temporal order.**

### TB-037
Overlapping intervals require overlap-aware composition rather than naive addition.

---

# 17. Directed elapsed duration and symmetric metric distance are not identical

A symmetric metric `d(t1,t2)` discards whether `t1` is earlier or later, whereas a signed/ordered temporal difference can preserve orientation.

### TB-038
**TemporalMetricDistance ≠ TemporalPrecedence.**

### TB-039
A temporal domain can combine order and magnitude, but neither recovers the other universally.

---

# 18. Order-preserving transformations can destroy duration ratios

Any strictly monotone reparameterization preserves earlier/later relations while generally altering coordinate differences.

### TB-040
**OrderStanding is weaker/invariant under a larger transformation class than metric-duration standing.**

### TB-041
Metric/affine duration claims therefore require a narrower admissible transformation/equivalence class.

---

# 19. Affine temporal coordinates are an enrichment, not the core

Under a simple affine model:

```text
t' = a t + b,  a > 0
```

order is preserved; durations scale uniformly by `a` and origin changes by `b`.

### TB-042
**Temporal origin/epoch is conventional under affine coordinate description.**

### TB-043
Uniform scale structure supports duration-ratio comparisons stronger than bare order.

### TB-044
MF6-B does not universalize affine time because relativity and nonuniform computational coordinates require later treatment.

---

# 20. Unit choice is not temporal scale structure itself

Choosing seconds versus milliseconds changes numerical expression while preserving a calibrated duration quantity.

### TB-045
**UnitChoice ≠ DurationStructure.**

### TB-046
A unit realizes a comparison convention/standard; the target temporal relation is not recreated by unit conversion.

---

# 21. The SI second anchors duration unit, not all temporal ontology

BIPM defines the second by fixing the caesium-133 transition frequency numerical value at `9 192 631 770 Hz`, equivalent to a duration of that many periods of the corresponding radiation.

### TB-047
**The SI second is a unit of time/duration, not a universal temporal coordinate system.**

### TB-048
Defining a unit through periodic physical behavior does not imply every temporal domain is cyclic or atomic.

---

# 22. A clock combines a time base with counting/state and representation

A practical clock minimally involves a process/oscillator or timing source plus a mechanism that accumulates/divides/counts state and exposes a reading/code.

### TB-049
**Oscillator ≠ Clock.**

### TB-050
A pure frequency standard can provide rate without by itself providing time-of-day/epoch phase.

### TB-051
Clock output semantics require reference/scale/initialization in addition to periodicity.

---

# 23. Same frequency does not mean same time

Two ideal oscillators can run at identical frequency but differ in phase/clock offset.

### TB-052
**SameFrequency ≠ SamePhase ≠ SameClockReading.**

### TB-053
This is why NIST distinguishes syntonization (same frequency) from synchronization (same time).

---

# 24. Synchronization and syntonization are distinct

NIST defines:

- synchronization: setting clocks to the same time;
- syntonization: setting oscillators to the same frequency.

### TB-054
**Synchronization ≠ Syntonization.**

### TB-055
A synchronized pair with different rates will diverge after synchronization.

### TB-056
A syntonized pair with nonzero phase/time offset can remain offset indefinitely while maintaining rate agreement.

---

# 25. Clock offset is not frequency offset

NIST distinguishes time offset (difference between a measured on-time signal and reference) from frequency offset (difference between measured and nominal frequency).

### TB-057
**TimeOffset ≠ FrequencyOffset.**

### TB-058
Clock state errors therefore need at least phase/time and rate/frequency components.

---

# 26. A simple clock model clarifies the distinction

For a reference temporal coordinate `t`, model one clock reading as:

```text
C(t) = β + α t + ε(t)
```

where:

- `β` ≈ offset/phase term;
- `α-1` ≈ fractional rate/frequency error;
- `ε(t)` ≈ noise/fluctuation/model residual.

### TB-059
**ClockReadingError is not one scalar phenomenon across time.**

### TB-060
A clock can have zero offset at one instant while having incorrect rate.

### TB-061
A clock can have nearly correct rate while retaining large constant offset.

---

# 27. Drift is change of frequency behavior, not offset itself

NIST defines frequency drift as undesired progressive change in frequency with time, caused by oscillator/environmental effects and not necessarily linear.

### TB-062
**FrequencyDrift ≠ FrequencyOffset.**

### TB-063
Drift can cause future accumulated time error even when current time offset is corrected.

---

# 28. Stability is not accuracy

NIST explicitly distinguishes oscillator stability from whether its frequency is correct: stability describes how well frequency remains the same over a specified interval.

### TB-064
**Stability ≠ Accuracy/Trueness.**

### TB-065
A very stable oscillator can be consistently wrong.

### TB-066
A less stable oscillator can have small mean offset over some calibration interval.

---

# 29. Stability is timescale-dependent

NIST SP 1065 emphasizes frequency stability analysis over averaging intervals; devices can have different short-term and long-term stability behavior.

### TB-067
**Clock/Oscillator stability is a function/profile over observation interval, not one context-free scalar.**

### TB-068
`ShortTermStability ≠ LongTermStability`.

---

# 30. Allan deviation is a stability statistic, not Time itself

Frequency metrology commonly uses Allan deviation and related statistics to characterize oscillator fluctuations over averaging interval `τ`.

### TB-069
**AllanDeviation ≠ FrequencyAccuracy ≠ TimeOffset.**

### TB-070
A stability statistic characterizes noise/process behavior under a measurement model; it is not an ontological primitive of temporal standing.

---

# 31. Resolution is not accuracy

NIST defines resolution as the smallest significant difference an instrument can distinguish; a device can report fine increments while remaining offset/noisy.

### TB-071
**Resolution ≠ Accuracy.**

### TB-072
High timestamp/clock display resolution can coexist with large uncertainty/error.

---

# 32. Precision is ambiguous and must not be used as a catch-all

NIST notes `precision` has multiple uses: agreement/repeatability-like meaning, or sometimes computer/value resolution.

### TB-073
**Precision ≠ one canonical clock-quality variable.**

### TB-074
For foundations, prefer explicit terms: resolution, repeatability, uncertainty, stability, accuracy/offset.

---

# 33. Accuracy/trueness is reference-dependent

Time/frequency accuracy is evaluated relative to a definition/reference such as UTC realization or nominal frequency.

### TB-075
**ClockAccuracyClaim requires reference/authority.**

### TB-076
A clock cannot be called absolutely `accurate` without declaring what its output is intended to conform to.

---

# 34. Uncertainty is not the same as known error

A measured clock offset can have an estimate plus measurement uncertainty.

### TB-077
**EstimatedError ≠ MeasurementUncertainty.**

### TB-078
Calibration/evidence should retain both correction/offset estimates and confidence/uncertainty.

---

# 35. Calibration is comparison/estimation, not temporal creation

A clock/oscillator can be compared with a standard to estimate offset/rate and corrections.

### TB-079
**Calibration ≠ Synchronization ≠ Syntonization.**

### TB-080
Calibration establishes evidence about relation to a reference; synchronization/syntonization are adjustment goals/actions.

---

# 36. Monotonicity is an order property, not correctness

A clock function can increase strictly while running fast, slow or with a huge offset.

### TB-081
**Monotonic ≠ Accurate.**

### TB-082
Monotonicity is useful for preserving local order/elapsed computations even when wall-clock synchronization is poor.

---

# 37. Accuracy does not guarantee monotonicity under correction

A clock can be stepped backward/forward to reduce offset relative to reference.

### TB-083
**Closer-to-reference after correction does not imply monotonic reading history.**

### TB-084
Systems that require elapsed-duration ordering may therefore distinguish monotonic clocks from civil/wall clocks.

---

# 38. One synchronization event is not persistent synchronization

If two clocks have different rates, setting them equal at `t0` only guarantees equality at that event (modulo uncertainty).

### TB-085
**SynchronizationAt(t0) ≠ SynchronizationForAllFutureTime.**

### TB-086
Maintaining synchronization requires rate control, repeated comparison, or bounded-error mechanisms.

---

# 39. Same rate does not establish epoch alignment

If `C1(t)=t` and `C2(t)=t+100`, their rates match exactly.

### TB-087
**RateAgreement ≠ Epoch/PhaseAgreement.**

### TB-088
Syntonized clocks can remain unsynchronized.

---

# 40. Time transfer is a measurement problem with propagation uncertainty

A remote clock comparison observes signals after propagation/network delay.

In a simplified one-way case:

```text
ObservedDifference = ClockOffset + PropagationDelay + MeasurementNoise
```

### TB-089
**Remote offset is not identifiable from one-way timestamp difference without assumptions/evidence about delay.**

### TB-090
Synchronization quality therefore depends on transfer-path model/calibration as well as clocks.

---

# 41. Asymmetric delay can masquerade as clock offset

If forward and reverse paths differ, symmetric-delay assumptions can bias estimated clock offset.

### TB-091
**NetworkPathAsymmetry ≠ ClockError but can contaminate clock-error inference.**

### TB-092
Temporal provenance must retain transfer method and uncertainty.

---

# 42. Logical clocks establish order semantics rather than SI duration

Lamport logical clock values satisfy order constraints constructed from events/messages; they can be used to extend event order without measuring physical seconds.

### TB-093
**LogicalClockDifference ≠ PhysicalDuration.**

### TB-094
A difference of `10` Lamport-clock units has no universal SI duration meaning.

---

# 43. Vector/logical clocks enrich causal/order information, not physical metric by default

More expressive distributed logical clocks can encode causality/concurrency distinctions.

### TB-095
**More precise causal-order representation ≠ more accurate physical clock.**

### TB-096
Computational temporal standing and physical duration measurement remain separate profiles.

---

# 44. Counter/tick time can be perfectly deterministic yet physically miscalibrated

A simulation advancing exactly one tick per update has exact logical tick order and count.

### TB-097
**DeterministicTickCount ≠ PhysicalElapsedTime.**

### TB-098
Mapping ticks to seconds is an additional simulation/representation rule.

---

# 45. Variable-step simulation is another hard case

A simulation can update with varying `Δt` or multiple substeps while rendering frames at a separate cadence.

### TB-099
**SimulationStep ≠ RenderFrame ≠ WallClockInterval.**

### TB-100
Temporal models can maintain several coordinated but nonidentical clocks/timescales.

---

# 46. Sampling interval is not event duration

A sensor sampled every 10 ms can observe an event lasting 1 ms or 1 s.

### TB-101
**SamplingPeriod ≠ TargetEventDuration.**

### TB-102
Acquisition cadence belongs to measurement process, not target temporal extent by identity.

---

# 47. Clock granularity can alias temporal distinctions

Events separated by less than clock/timestamp resolution may receive equal recorded timestamps.

### TB-103
**SameRecordedTimestamp ≠ SameTemporalPosition.**

### TB-104
Coarse temporal measurement creates non-identifiability analogous to MF1 sampling/quantization.

---

# 48. Quantized timestamps do not make target time discrete

A device recording only whole seconds produces discrete codes even if the target model is continuous.

### TB-105
**DiscreteTimestampDomain ≠ DiscreteTargetTime.**

### TB-106
Representation granularity cannot be transferred to target ontology without evidence.

---

# 49. Conversely continuous coordinate models can represent discrete target events

A database may timestamp discrete transactions with real-valued/continuous-style coordinates.

### TB-107
**ContinuousCoordinateCodomain ≠ ContinuousEventOntology.**

---

# 50. Duration may be bounded rather than point-estimated

Measurements/partial evidence can yield:

```text
Dur(I) ∈ [a,b]
```

### TB-108
**Temporal measure can be interval-valued/uncertain without losing duration standing.**

### TB-109
A fabricated exact scalar is not epistemically superior to an honest bound.

---

# 51. Different clocks can disagree while preserving compatible order

Two clocks with monotonic functions and modest rate differences can assign different coordinates yet agree that `A before B` locally.

### TB-110
**Clock-coordinate disagreement ≠ temporal-order disagreement necessarily.**

### TB-111
Order claims can be more robust than metric/coordinate claims.

---

# 52. Duration equality can be stronger or weaker depending standing route

Two measured intervals may be declared equal within uncertainty/tolerance rather than exactly mathematically equal.

### TB-112
**OperationalDurationEquality ≠ ExactMathematicalEquality universally.**

### TB-113
Tolerance/reference/uncertainty belong in duration comparison claims.

---

# 53. Clock phase and temporal phase are typed

For periodic processes, phase describes position within cycle relative to a reference.

### TB-114
**OscillatorPhase ≠ GlobalClockTime.**

### TB-115
Phase comparison can support synchronization/measurement but needs cycle identification and reference semantics.

---

# 54. Frequency ratio can be measured more precisely than absolute time alignment

Metrology often compares oscillator rates/frequencies separately from time-of-day phase alignment.

### TB-116
**Rate metrology and epoch/time-transfer metrology are separable measurement problems.**

This is the operational basis of the synchronization/syntonization distinction.

---

# 55. Clock quality is multidimensional

MF6-B proposes a clock-quality vector rather than one `precision` score:

```text
ClockQuality = <
  Offset/TimeError,
  FrequencyOffset/RateError,
  Drift/Aging,
  Stability(τ),
  Resolution,
  Repeatability,
  Accuracy/Uncertainty vs Reference,
  Monotonicity,
  HoldoverBehavior,
  Transfer/SynchronizationUncertainty,
  Provenance
>
```

### TB-117
**No one scalar universally ranks clocks for all tasks.**

### TB-118
A navigation clock, distributed database clock and laboratory frequency standard can optimize different profiles.

---

# 56. Clock standing is role-relative

A clock can serve as:

- duration meter;
- time-of-day coordinate source;
- synchronization reference;
- frequency standard;
- ordering token generator;
- simulation timebase.

### TB-119
**ClockType/Role determines which quality dimensions matter.**

### TB-120
Calling all of these simply `clock` hides operational distinctions.

---

# 57. DurationProfile

MF6-B proposes:

```text
DurationProfile = <
  Interval/Process,
  TemporalStanding,
  MeasureStructure,
  Unit,
  Reference/Worldline/Frame if applicable,
  AdditivityRules,
  CoordinateRepresentation?,
  MeasurementMethod/Clock?,
  Resolution,
  Uncertainty,
  Provenance,
  Scope
>
```

### TB-121
**Duration claims need a measure/evidence profile, not only endpoints.**

---

# 58. IntervalRelationClaim

```text
IntervalRelationClaim = <
  IntervalA,
  IntervalB,
  Relation : before/meets/overlaps/starts/during/finishes/equal/etc.,
  BoundaryConvention,
  TemporalFrame/Scope?,
  Uncertainty/Vagueness,
  Evidence/Provenance
>
```

### TB-122
**Qualitative interval relation is independently meaningful from duration.**

---

# 59. ClockClaim

```text
ClockClaim = <
  Clock/Timebase,
  Output/Reading,
  Role,
  Reference/Timescale,
  Epoch/Phase,
  Frequency/Rate,
  TimeOffset,
  FrequencyOffset,
  Drift/Aging,
  Stability(τ),
  Resolution,
  Accuracy/Uncertainty,
  Synchronization/SyntonizationState,
  TransferPath/Method?,
  CalibrationHistory,
  Provenance,
  Scope
>
```

### TB-123
Bare `clock is precise/accurate/synchronized` is under-specified.

---

# 60. TemporalMeasureStanding

MF6-B proposes an enrichment relation:

```text
TemporalMeasureStanding(M, D | Σ)
```

when quantitative extent/comparison of temporal intervals/processes is formally constituted, operationally recruited or physically/institutionally calibrated in domain `D`.

### TB-124
**TemporalMeasureStanding ≠ TemporalStanding universally.**

### TB-125
A domain can have valid temporal order/interval standing without quantitative duration measure.

---

# 61. Final structural ladder after MF6-B

```text
Temporal Standing
   ↓ + order relations
Temporal Order Structure
   ↓ + interval objects/relations
Temporal Interval Structure
   ↓ + quantitative extent/comparison
Temporal Measure / Duration Structure
   ↓ + physical/computational realization
Clock / Timescale / Measurement System
```

### TB-126
This ladder describes added commitments/information, not degrees of reality.

### TB-127
No upward layer is automatically constitutive of the layers below.

---

# 62. Failure taxonomy

## Order-duration collapse
Earlier/later relation treated as known elapsed duration.

## Interval-duration collapse
Temporal region identity reduced to one scalar length.

## Total-order inflation
Algorithmic tie-break order interpreted as full physical chronology.

## Point-first inflation
All temporal reasoning forced through primitive instants despite interval-native standing.

## Endpoint subtraction inflation
Coordinate difference treated as universally invariant physical duration.

## Clock-time collapse
Clock device/oscillator identified with Time.

## Oscillator-clock collapse
Frequency source treated as fully initialized time-of-day clock.

## Synchronization-syntonization collapse
Same time and same frequency conflated.

## Offset-rate collapse
Current time error confused with frequency/rate error.

## Drift-offset collapse
Progressive frequency change confused with static error.

## Stability-accuracy collapse
Consistent wrong oscillator treated as accurate.

## Resolution-accuracy collapse
Fine digit granularity treated as true timing quality.

## Precision catch-all
Ambiguous `precision` word hides distinct error/stability/resolution concepts.

## Monotonic-accuracy collapse
Increasing clock treated as correct clock.

## Logical-physical collapse
Logical clock differences interpreted as SI elapsed duration.

## Timestamp-target granularity transfer
Discrete recorded timestamps used to infer discrete target time.

## Transfer-delay/offset confounding
Network propagation asymmetry attributed to clock error.

## Calibration-adjustment collapse
Measurement/calibration treated as synchronization act or vice versa.

### TB-128
**Temporal measurement failure is a typed family, not one `clock error`.**

---

# 63. Strongest non-collapse stack after MF6-B

```text
Temporal Standing
 ≠ Temporal Order
 ≠ Duration Measure
 ≠ Clock Realization
```

```text
Temporal Order
 ≠ Temporal Metric
```

```text
Interval Identity
 ≠ Duration
 ≠ Duration Number
```

```text
Before
 ≠ Meets
 ≠ Overlaps
 ≠ During
 ≠ Equal
```

```text
Clock
 ≠ Oscillator
 ≠ Clock Reading
 ≠ Timescale
 ≠ Time
```

```text
Time Offset
 ≠ Frequency Offset
 ≠ Frequency Drift
 ≠ Stability
```

```text
Synchronization
 ≠ Syntonization
```

```text
Same Frequency
 ≠ Same Phase
 ≠ Same Time
```

```text
Monotonic
 ≠ Accurate
 ≠ Stable
```

```text
Resolution
 ≠ Precision/Repeatability
 ≠ Accuracy
 ≠ Uncertainty
```

```text
Logical Clock Difference
 ≠ Physical Duration
```

```text
Timestamp Granularity
 ≠ Target Time Granularity
```

---

# 64. Claims rejected by MF6-B

Reject as universal/foundational:

- temporal order requires numerical duration;
- temporal order is universally total;
- interval relations reduce to endpoint timestamps in all ontologies;
- duration is interval identity;
- equal duration means same interval;
- endpoint inclusion always changes duration;
- all valid temporal intervals have nonzero duration;
- duration is universally `t2 - t1` independent of frame/model;
- temporal measure is constitutive of all temporal standing;
- all time is continuous or all time is discrete;
- a clock is just an oscillator;
- an oscillator with correct frequency is synchronized to time-of-day;
- synchronization and syntonization are synonyms;
- equal clock readings once imply equal future readings;
- zero time offset implies zero frequency offset;
- frequency drift equals current frequency offset;
- stable means accurate;
- high resolution means accurate;
- `precision` is one well-defined universal clock-quality measure;
- monotonic means correct;
- calibration and synchronization are the same act;
- network timestamp difference directly reveals remote clock offset without delay assumptions;
- logical clock increments measure SI duration;
- simulation ticks equal wall-clock seconds by default;
- frame/sample period equals target event duration;
- timestamp discreteness proves target temporal discreteness;
- one scalar clock-quality ranking is valid for every consumer.

---

# 65. Primary/authoritative anchors

- **James F. Allen (1983)**, `Maintaining Knowledge about Temporal Intervals`, *Communications of the ACM* 26(11):832–843, DOI 10.1145/182.358434. Interval-based temporal reasoning establishes rich qualitative temporal relations without requiring metric duration as the first primitive.
- **Leslie Lamport (1978)**, `Time, Clocks, and the Ordering of Events in a Distributed System`, *Communications of the ACM* 21(7):558–565, DOI 10.1145/359545.359563. Happened-before partial order, logical-clock ordering and separate physical-clock synchronization provide hard cases for order ≠ duration and logical ≠ physical time.
- **BIPM, SI second**, current SI definition: fixed numerical value `Δν_Cs = 9 192 631 770 Hz`. Used as the authoritative metrological anchor for unit realization ≠ temporal ontology and periodic standard ≠ clock/time identity.
- **Michael A. Lombardi / NIST Time and Frequency terminology**, official NIST educational/reference material: synchronization = clocks set to same time; syntonization = oscillators set to same frequency; time offset, frequency offset, resolution, stability and accuracy are separate quantities.
- **William Riley & David A. Howe (2008)**, NIST SP 1065 `Handbook of Frequency Stability Analysis`. Stability depends on averaging interval and is characterized through Allan-family statistics; stability is not frequency correctness.

---

# 66. Deep reconstruction

Naive model:

```text
Time = one real-number axis
      ↓
interval = [t1,t2]
      ↓
duration = t2 - t1
      ↓
clock measures t
      ↓
more digits = better clock
```

MF6-B replaces it with:

```text
Temporal standing
    │
    ├─ qualitative order
    │    └─ partial/total/local order
    │
    ├─ interval structure
    │    └─ before/meets/overlaps/contains/etc.
    │
    └─ optional quantitative measure
         ├─ duration/extent
         ├─ unit/scale
         └─ additivity/equivalence assumptions
                 │
                 ▼
        measurement realization
         ├─ oscillator/time base
         ├─ counting/clock state
         ├─ epoch/phase/timescale
         ├─ synchronization / syntonization
         ├─ transfer path
         └─ uncertainty/calibration
```

The decisive move is:

> **Order, interval structure, duration measure and clock realization are successive typed enrichments. A clock is evidence/realization machinery for temporal measure/coordinates, not Time itself; and clock quality decomposes into offset, rate, drift, stability, resolution and uncertainty rather than one `precision` number.**

---

# 67. Deepest MF6-B result

The strongest surviving provisional formulation is:

> **Temporal order establishes qualitative earlier/later/succession relations; interval structure adds relations among extended temporal regions; duration adds a quantitative measure of temporal extent under declared invariance/additivity/reference assumptions; clocks and timescales operationalize or represent those measures/coordinates through physical or computational processes. None of these layers is identical to the others, and temporal domains need not possess quantitative duration in order to possess genuine temporal standing.**

Compact:

```text
Order gives who precedes whom.
Intervals give how temporal regions relate.
Duration gives how much temporal extent.
Clocks realize/estimate/reference those quantities.
```

---

# 68. MF6-A→B reconstructed picture

```text
MF6-A Temporal Ontology
 = temporal alternatives + TemporalStanding + typed temporal relations

MF6-B Temporal Structure & Measurement
 = order / interval / duration layers
   + clock/timebase/synchronization metrology
```

MF6 remains UNFROZEN because relativity may materially revise what counts as duration, simultaneity and clock comparison.

---

# 69. No FoundationReopenCondition

MF6-B does not trigger reopen of MF1–MF5.

- MF1 precision/uncertainty distinctions are strengthened by clock metrology.
- MF3 representation standing cleanly separates timestamps/readings from target temporal positions.
- MF5 structural-isomorphism/standing discipline remains essential.

### TB-129
**MF0–MF5 remain frozen.**

---

# 70. MF6-C handoff — Relativity, Proper Time, Simultaneity & Spacetime

MF6-B deliberately stops before treating Newtonian/affine clock relations as universal.

MF6-C must ask:

> **Which temporal quantities survive changes of inertial frame/worldline/gravitational context, what exactly does a clock measure in relativity, and how should temporal standing coexist with spacetime geometry without collapsing back into MF5?**

Required topics/hard cases:

- Einstein synchronization revisited precisely;
- relativity of simultaneity;
- invariant causal/timelike ordering versus spacelike order disagreement;
- proper time along timelike worldlines;
- coordinate time versus proper time;
- time dilation as worldline/frame relation rather than `clock defect`;
- twin/worldline hard case;
- Minkowski interval and sign/type separation;
- light cones / causal structure;
- spacetime coordinates versus physical observables;
- inertial frames and synchronization convention;
- accelerated clocks/worldlines;
- gravitational redshift/proper time in GR;
- clock hypothesis;
- path/worldline dependence of elapsed proper time;
- GPS-like clock systems as engineering hard case if needed;
- global time coordinates not universally available in arbitrary spacetimes;
- simultaneity surfaces and foliation/model dependence;
- whether `TemporalStanding` requires revision under spacetime unification;
- explicit MF5 FoundationReopenCondition test.

Central attack:

```text
Coordinate Time ≠ Proper Time
Same Coordinate Duration ≠ Same Proper Duration
Time Dilation ≠ Clock Malfunction
Simultaneity ≠ Frame-Invariant Universally
Spacetime Coordinate ≠ Observable by Identity
Worldline ≠ Spatial Path Alone
Spatial Standing ≠ Temporal Standing even inside one spacetime manifold
```

**Next: MF6-C — Relativity, Proper Time, Simultaneity & Spacetime.**

---

# 71. NTP remote-synchronization hard case

RFC 5905 models remote clock discipline using multiple distinct quantities rather than one generic clock error: clock/time offset, frequency offset, aging rate, round-trip delay, dispersion and jitter.

### TB-130
**Remote timestamp disagreement is an inverse problem over clock state plus transfer-path delay/noise, not a direct observation of clock offset.**

### TB-131
`ClockOffset ≠ NetworkDelay ≠ Dispersion ≠ Jitter ≠ FrequencyOffset ≠ AgingRate`.

### TB-132
Even when a synchronization protocol produces one best offset estimate, the estimate's standing depends on path/model assumptions and uncertainty; estimated synchronization ≠ exact target co-temporality.

### TB-133
A system can improve frequency discipline and phase/time discipline through different feedback components; physical/computational synchronization remains a control-and-estimation problem layered on temporal standing.

---

# 72. Time scale ensemble hard case

NIST's UTC(NIST) is not simply the reading of one privileged atomic clock. NIST continuously compares an ensemble, estimates relative stability, produces the free-running composite scale TA(NIST), and then applies coordination adjustments so UTC(NIST) agrees with UTC in both time (synchronization) and frequency (syntonization).

### TB-134
**TimeScale ≠ BestSingleClock.**

### TB-135
A time scale can be algorithmically/compositionally defined from multiple clocks and comparison evidence.

### TB-136
**FreeRunningScale ≠ CoordinatedScale.** TA(NIST) and UTC(NIST) differ in standing/use even though the latter is derived from the former.

### TB-137
Clock ensemble membership/weighting can change while the time-scale identity/continuity is intentionally preserved, so `TimeScaleIdentity ≠ ConstituentClockIdentity`.

### TB-138
A clock ensemble can improve robustness/stability without making constituent clocks individually more accurate; aggregation quality and device quality are distinct profiles.

---

# 73. Additional primary/authoritative anchor

- **Mills et al. / IETF (2010), RFC 5905, `Network Time Protocol Version 4: Protocol and Algorithms Specification`.** NTP explicitly models timestamp/clock offset, frequency offset, aging rate, round-trip delay, dispersion and jitter separately, and disciplines system clock phase/frequency using remote measurements. This provides a protocol-level hard case for `timestamp difference ≠ clock offset`, `offset ≠ rate`, and `synchronization estimate ≠ exact temporal truth`.
- **NIST, `How UTC(NIST) Works`.** The national time scale is produced from an ensemble algorithm (TA(NIST)) plus steering/coordination to UTC; synchronization and syntonization are explicitly distinct. This anchors `time scale ≠ single clock` and `free-running scale ≠ coordinated scale`.

### TB-139
**MF6-B final claim count: TB-001→TB-139. These additions strengthen rather than revise the existing reconstruction.**
