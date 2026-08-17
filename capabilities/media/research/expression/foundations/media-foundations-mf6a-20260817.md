# Ordivon Media Foundations — MF6-A Temporal Ontology & Term Separation

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 32 at start  
**Input:** MF0–MF5 frozen. MF5 Space Foundations v1 frozen at `e4de7098d925cffa43e20846ca8de447d892813b`.  
**Status:** MF6-A complete and PROVISIONAL. Time Foundations remain UNFROZEN.  
**Next:** MF6-B — Temporal Order, Interval, Duration, Measure & Clocks.

---

# 0. Purpose

MF5-I ended by proving that temporal and spatial structures can share the same mathematics without sharing ontological role:

```text
SpatialAxis ≠ TemporalAxis
```

even when both are represented by `R`.

MF6-A therefore does not begin from `time is a line`, `time is a clock reading`, `time is a sequence`, or `time is what changes measure`.

Central question:

> **What makes a distinction genuinely temporal rather than merely ordered, indexed, changing, causal, represented on a timeline, or measured by a clock?**

Dangerous collapses:

```text
Time = R
Time = Clock
Time = Clock Reading
Time = Timestamp
Time = Sequence
Time = Change
Temporal Order = Causal Order
Temporal Position = Event
Instant = Timestamp
Interval = Duration
Same Timestamp = Simultaneous
Frame Index = Physical Time
Processing Order = Event Time
Logical Time = Physical Time
Frequency = Time
Calendar = Time
```

MF6-A is term separation and ontology only. Detailed duration/clock theory moves to MF6-B; relativity/proper time/spacetime to a later round; subjective time and media rhythm later still.

---

# 1. The first over-inclusion attack: `Time = R`

The real line can parameterize position, time, temperature, probability, model parameters and latent factors.

### TA-001

**Real-valued parameterization ≠ temporal standing.**

### TA-002

`R` supplies formal order/metric structure only after the relevant structure is declared; it does not determine what the represented quantity means.

### TA-003

**Structural isomorphism between a temporal axis and a spatial/semantic/parameter axis does not transfer temporal ontology.**

This directly inherits MF5-I:

```text
StructuralIsomorphism ≠ OntologicalRoleIdentity
```

---

# 2. The second over-inclusion attack: `Time = Sequence`

A book has page order. A program has instruction order. A playlist has track order. A deck has card order.

### TA-004

**Ordinal succession ≠ temporal standing by default.**

### TA-005

A sequence can represent or prescribe temporal order, but sequence structure alone is insufficient.

### TA-006

`Index(i) < Index(j)` does not by itself establish `Earlier(i,j)` in an external target domain.

---

# 3. Frame index is not physical time

Video frames may be uniformly sampled, variably timed, duplicated, dropped, reordered for coding, or assigned presentation timestamps independently of stored index.

### TA-007

**FrameIndex ≠ Timestamp ≠ PresentationTime ≠ SourceEventTime.**

### TA-008

A frame sequence can have temporal representational standing when index/timestamps are grounded in acquisition/presentation order, but the integer index alone does not constitute elapsed physical time.

---

# 4. The third over-inclusion attack: `Time = Change`

Change presupposes comparison of states/conditions under some ordering, but not every mathematical change parameter is temporal in its target role.

### TA-009

**Change ≠ Time.**

### TA-010

A parameter sweep `f(λ)` can change with `λ` while `λ` is not target time.

### TA-011

Temporal structure can organize possible/represented events even in a description where no current observer witnesses change.

MF6-A therefore does not make observable change constitutive.

---

# 5. The fourth over-inclusion attack: `Time = Clock`

A clock is a physical/computational process used to realize or represent temporal measure/order.

BIPM currently defines the SI second by fixing the numerical value of the unperturbed caesium-133 hyperfine transition frequency to `9 192 631 770 Hz`; the historical SI definition changed from astronomical day/year references to atomic frequency standards while remaining a unit of time.

### TA-012

**Clock/oscillator/process ≠ Time.**

### TA-013

**Time standard realization can change without recreating the temporal relations being measured.**

### TA-014

`ClockProcess ≠ ClockReading ≠ UnitOfTime ≠ TargetTemporalStructure`.

---

# 6. Frequency is not Time

Frequency expresses repetition rate relative to a time unit/interval.

### TA-015

**Frequency ≠ Time.**

### TA-016

A periodic process can operationalize duration measurement only after the relation between cycles and temporal measure is established.

### TA-017

The SI second's caesium definition therefore supports a measurement standard; it does not ontologically reduce time to caesium atoms.

---

# 7. Clock reading is a representation/measurement state

A clock face showing `7:00` is a state of a measuring device under a convention/timescale.

### TA-018

**ClockReading ≠ TemporalPosition by identity.**

### TA-019

A reading can stand for a temporal coordinate only with calibration, reference/timescale, synchronization and provenance.

### TA-020

Two malfunctioning clocks can show the same reading without their associated events being target-simultaneous.

---

# 8. Timestamp is not Time

A timestamp is a symbolic/numeric representation claim about temporal position/order under a specified scale/reference/convention.

### TA-021

**Timestamp ≠ event ≠ temporal position ≠ duration.**

### TA-022

A timestamp requires at least interpretation context such as scale/epoch/unit/precision and often timezone/calendar/clock source.

### TA-023

The same target temporal position can admit multiple timestamp representations.

### TA-024

The same numeric timestamp value under different epochs/scales can denote different temporal claims.

This mirrors MF5-C:

```text
Locus ≠ Coordinate
```

as:

```text
TemporalPosition ≠ Timestamp
```

---

# 9. Calendar/date representation is not temporal ontology

Calendar systems partition/name temporal intervals/positions through institutional conventions.

### TA-025

**CalendarDate ≠ Time.**

### TA-026

Calendar representation can have strong institutional standing while remaining a description layer over target temporal structure.

### TA-027

Changing calendar convention does not normally move the target event in time.

---

# 10. Event is not Time

An event/occurrence is something temporally situated or extended; `time` is not identical to the event content.

### TA-028

**Event ≠ TemporalPosition.**

### TA-029

Multiple distinct events can share one temporal-position claim under a given frame/scale.

### TA-030

One event/process can also extend over an interval rather than occupy one idealized instant.

MF6-A leaves a full event ontology partly open because MF7 State & Dynamics and MF8 Agency will specialize occurrences/processes.

---

# 11. Instant is not event

An instant is provisionally a zero-duration/point-like temporal alternative in a model, not a material occurrence.

### TA-031

**Instant ≠ Event.**

### TA-032

A temporal ontology need not assume every real occurrence is instantaneous.

### TA-033

MF6-A does not yet freeze instants as universal primitives; interval-first/process-first temporal models remain admissible.

---

# 12. Temporal position is not timestamp

MF6-A introduces provisionally:

```text
TemporalPositionStanding(T, X | Σ)
```

for a distinction that has standing as a `when-like` alternative in target/formal/system domain `X` under scope `Σ`.

### TA-034

**Temporal position can be relationally or frame-relative individuated without one global scalar coordinate.**

### TA-035

Timestamp is one possible description/representation of temporal position, not its ontology.

---

# 13. Temporal standing is the MF6 analogue of positional standing — but not the same role

MF5 froze `PositionalStanding` to block arbitrary graphs/embeddings from becoming spatial.

MF6-A analogously proposes:

```text
TemporalStanding(R, X | Σ)
```

when distinctions/relations are formally constituted, operationally recruited or target-grounded as when-/earlier-later-/co-temporal-/interval-/duration-like structure.

### TA-036

**TemporalStanding ≠ PositionalStanding.**

### TA-037

They can share formal mathematics while playing different roles.

### TA-038

A spacetime theory may couple both roles in one formal structure without erasing the typed distinction automatically.

---

# 14. Temporal vocabulary is not enough

Calling a version `newer`, a node `future`, or a workflow stage `later` can be metaphorical/conventional.

### TA-039

**Temporal vocabulary ≠ target TemporalStanding.**

### TA-040

Standing requires target/formal/system rules that actually establish temporal ordering/interval/occurrence roles.

---

# 15. Order is not duration

A relation can establish:

```text
a before b
b before c
```

without supplying numerical elapsed duration.

### TA-041

**TemporalOrder ≠ TemporalMetric/Duration.**

### TA-042

Order can therefore survive in domains without clocks or metric duration.

Lamport's distributed-system work is a direct computational hard case: `happened-before` defines a partial order among events before any physical-time duration is assigned.

---

# 16. Partial order is not total order

Lamport defines an event ordering generated by same-process order, message send→receive relations and transitivity; concurrent events may be incomparable under this relation.

### TA-043

**Temporal/causal ordering need not be total.**

### TA-044

A total timestamp order can be added for system purposes without becoming the only underlying event-order truth.

### TA-045

`Incomparable ≠ Simultaneous` by default.

In distributed systems, incomparability often means absence of the specified happened-before relation, not proof of equal physical time.

---

# 17. Logical clock is not physical clock

Lamport constructs logical clocks so clock ordering respects happened-before and can extend ordering for distributed algorithms; the paper separately discusses physical-clock synchronization.

### TA-046

**LogicalTime ≠ PhysicalTime.**

### TA-047

A logical clock value can encode event-order constraints without measuring elapsed SI seconds.

### TA-048

A total logical order may deliberately break ties among causally unrelated events for computation.

---

# 18. Processing order is not source event time

A system can receive, process, persist or display records in an order different from when represented target events occurred.

### TA-049

```text
EventTime
 ≠ ObservationTime
 ≠ IngestionTime
 ≠ ProcessingTime
 ≠ PersistenceTime
 ≠ PresentationTime
```

### TA-050

One record may legitimately carry several typed temporal claims.

### TA-051

Sorting by database insertion time does not reconstruct target event order by default.

---

# 19. Validity time is not transaction/record time

A statement may become stored today while describing a fact valid yesterday or tomorrow.

### TA-052

**ValidityTime ≠ Record/TransactionTime.**

### TA-053

Temporal provenance must say what relation a timestamp actually timestamps.

This is a direct temporal analogue of MF5 standing-route/provenance discipline.

---

# 20. Observation time is not occurrence time

A delayed signal can be observed after the target event that generated it.

### TA-054

**ObservationTime ≠ SourceEventTime.**

### TA-055

Signal propagation delay is a relation between events; sensor receipt time cannot be silently substituted for target occurrence time.

This inherits MF1 signal-transformation provenance.

---

# 21. Detection time is not decision time

A system may detect evidence at one temporal position and decide/act later.

### TA-056

**EvidenceAcquisitionTime ≠ InferenceTime ≠ DecisionTime ≠ ActionTime.**

### TA-057

Temporal claims in agent systems therefore need typed provenance, not one generic `timestamp` field.

---

# 22. Interval is not duration

Provisionally:

- a temporal interval is a temporal region/range/between-structure;
- duration is a quantitative extent/measure assigned to such an interval/process under a temporal measure model.

### TA-058

**TemporalInterval ≠ Duration.**

### TA-059

Intervals can be ordered/nested/overlap even when exact duration is unknown.

### TA-060

Duration measurement requires additional metric/clock structure; temporal ordering alone does not provide it.

MF6-B will attack this separation more deeply.

---

# 23. Duration is not endpoint-coordinate subtraction universally

In a simple affine time coordinate, one may compute `Δt=t2-t1`.

### TA-061

**Coordinate difference ≠ invariant/physical duration by universal identity.**

Relativity already warns that frame/worldline/reference structure matters; the proper/coordinate-time distinction is deferred to the dedicated relativity round.

### TA-062

MF6-A therefore does not freeze `duration = scalar endpoint difference` as ontology.

---

# 24. Simultaneity is not same clock reading by default

Einstein's 1905 special-relativity construction explicitly required a synchronization rule using exchanged light signals to define a common time for spatially separated stationary clocks.

### TA-063

**Remote simultaneity is not supplied merely by owning two clocks.**

### TA-064

A synchronization/coordinate framework is part of the claim.

### TA-065

`SameLocalClockReading` and `SimultaneousUnderFrame/Convention` are different predicates.

---

# 25. There is no universal global simultaneity claim frozen into MF6

Special relativity supplies the decisive hard case: inertial frames need not agree on simultaneity/order for spacelike-separated events, while causal/timelike ordering is more constrained.

### TA-066

**Global absolute simultaneity is not a universal constitutive requirement of Time.**

### TA-067

Simultaneity claims must carry reference/frame/convention/model scope where relevant.

### TA-068

MF6-A does not infer that simultaneity is always conventional or absent in every domain; only the universal absolute version is rejected.

---

# 26. Causal order and temporal order are not identical

Causal influence normally constrains temporal structure, but temporal ordering can be stated between events that do not causally affect one another.

### TA-069

**CausalPrecedence ≠ TemporalPrecedence by definition.**

### TA-070

Lamport's `happened-before` is causality-like/communication-derived in a distributed system; it is not the complete ontology of physical time.

### TA-071

Causality can be one temporal-order grounding route or constraint without constituting all temporal relation families.

---

# 27. Succession/order and metric duration can vary independently

A clock can run at a different rate while preserving order of successive local events.

### TA-072

**OrderPreservation ≠ DurationPreservation.**

### TA-073

A monotonic transformation of a temporal coordinate can preserve earlier/later relations while changing numerical interval differences.

### TA-074

Temporal topology/order standing can therefore be weaker than temporal metric standing.

---

# 28. Clock rate is not temporal order

Clock rate compares evolution of a clock reading/process to a reference temporal measure.

### TA-075

**ClockRate ≠ TemporalOrder.**

### TA-076

A clock can drift yet remain monotonic, preserving local event order while mismeasuring durations.

### TA-077

Accuracy, stability, precision, resolution and synchronization are distinct clock qualities and are not definitions of Time.

MF6-B will type them explicitly.

---

# 29. Period, phase and frequency are separate

For cyclic processes:

```text
Period = temporal extent per cycle
Frequency = cycles per temporal unit
Phase = position within a cycle
```

### TA-078

**Period ≠ Frequency ≠ Phase ≠ Time.**

### TA-079

Two oscillators can share frequency while having different phase; phase equality need not imply global event simultaneity without synchronization semantics.

---

# 30. Temporal scale is not Time

A timescale is provisionally a rule/system for assigning temporal coordinate values and maintaining reference relations.

### TA-080

**Timescale ≠ Time.**

### TA-081

Different timescales/coordinate systems can describe related temporal structure with transformations/conventions.

### TA-082

Coordinate/timescale plurality does not imply multiple unrelated physical realities by itself.

---

# 31. Epoch is not origin of Time

An epoch selects a zero/reference for a temporal coordinate representation.

### TA-083

**Epoch ≠ beginning of target time.**

### TA-084

Changing epoch adds/relabels coordinate values without changing target event relations.

This is the temporal analogue of shifting a spatial coordinate origin.

---

# 32. Unit is not coordinate

A second is a unit of temporal duration; a timestamp combines values with a scale/epoch/representation.

### TA-085

**TimeUnit ≠ TemporalCoordinate ≠ Timestamp.**

### TA-086

Changing unit rescales numerical values while preserving the represented temporal relation when conversion is valid.

---

# 33. Precision/resolution are not uncertainty/truth

A timestamp can be recorded to nanoseconds while its actual event-time uncertainty is seconds.

### TA-087

**TimestampResolution ≠ TemporalAccuracy ≠ TemporalUncertainty.**

### TA-088

More digits do not establish stronger temporal evidence.

This directly inherits MF1 precision/trueness/uncertainty separation.

---

# 34. Temporal uncertainty can be relational

An event may be known to occur after A and before B without exact timestamp.

### TA-089

**Temporal standing does not require exact temporal coordinate.**

### TA-090

Partial order/interval bounds can be stronger evidence than a fabricated point timestamp.

---

# 35. Temporal vagueness and measurement uncertainty are distinct

Natural/institutional events can have vague onset/end criteria while clock measurement itself is precise.

### TA-091

**TemporalBoundaryVagueness ≠ ClockMeasurementUncertainty.**

### TA-092

An event/process can have fuzzy/criterion-dependent beginning while its observations are timestamped exactly.

MF6 later must decide whether temporal regions/boundaries need an MF5-D-like dedicated round.

---

# 36. Same timestamp can describe different typed claims

A record might carry:

```text
created_at
observed_at
valid_from
published_at
processed_at
```

with identical numeric values by coincidence.

### TA-093

**Numeric equality ≠ temporal-role identity.**

### TA-094

Temporal field names/provenance are semantically constitutive for interpretation.

---

# 37. Temporal order can be local/scoped

Different processes/agents can have well-defined local event order without a single known global total order.

### TA-095

**Local temporal order ≠ global total chronology.**

### TA-096

A system can reason safely with partial temporal information.

This is important for distributed systems, media synchronization and later agency.

---

# 38. `Now` is not yet a foundational primitive

`Now/present` can mean local clock reading, perceptual present, conversational indexical, coordinate hypersurface, validity window or phenomenological present.

### TA-097

**Now ≠ one universal temporal primitive at MF6-A.**

### TA-098

Presentism/eternalism/growing-block metaphysics are not frozen here; physics/perception/experience rounds may constrain them differently.

---

# 39. Past/future are typed relative predicates

### TA-099

**Past/Future claims require a reference event/observer/frame/order structure.**

### TA-100

A database's `future scheduled task` and a relativistic event's causal future are not the same relation simply because both use `future`.

---

# 40. Relativity is a boundary condition, not a full MF6-A solution

Einstein 1905 operationalized remote time coordination through synchronized clocks/light signals; Minkowski 1908 recast special relativity in a unified spacetime formalism.

### TA-101

**Space/time coupling in relativity does not license `space = time` or `temporal standing = positional standing`.**

### TA-102

MF6 must allow one formal spacetime domain to carry typed spatial, temporal and causal relations whose invariants differ.

### TA-103

MF5 is not reopened merely because spacetime unifies coordinates; a concrete contradiction with MF5 PositionalStanding is still required.

---

# 41. Candidate minimal TemporalStanding

MF6-A proposes provisionally:

> **Temporal standing exists when distinctions or relations in a target, formal construction or operating system are non-arbitrarily constituted/recruited as when-like alternatives, succession/earlier-later relations, co-temporality/simultaneity relations, temporal intervals, or duration/recurrence structures, under a declared scope and provenance.**

Compact:

```text
TemporalStanding
 = When/Occurrence Alternatives
 + Typed Temporal Relation Structure
 + Standing Route
 + Scope
```

### TA-104

This is provisional and must survive MF6-B/C falsification.

### TA-105

Neither scalar coordinates nor clocks are required by the candidate core.

---

# 42. Candidate temporal alternatives

MF6-A keeps multiple possible primitives open:

- instants/temporal positions;
- intervals;
- events/occurrences;
- process phases;
- relational order positions;
- equivalence classes under simultaneity/co-temporality;
- logical/computational temporal states where genuinely temporally grounded.

### TA-106

**MF6 does not yet commit to point-first versus interval/event-first metaphysics.**

### TA-107

A final Time ontology may need typed alternatives rather than one universal primitive.

---

# 43. Standing routes — provisional

Candidate nonexclusive routes:

1. **Formal/Axiomatic** — temporal order/interval structure explicitly constructed.
2. **Physical/Dynamical** — temporal relations established through physical theory/processes/causal structure.
3. **Measurement/Clock** — calibrated clocks/time standards evidence duration/order.
4. **Perceptual/Experiential** — temporal discriminability/ordering/duration experience; later rounds.
5. **Computational/Logical** — operational event order/logical clocks/scheduling semantics.
6. **Representational/Institutional** — calendars/timestamps/media timelines/validity conventions standing for target time.
7. **Hybrid** — combinations.

### TA-108

**Standing route ≠ evidence route**, as in MF5.

A physical temporal relation may be evidenced through a clock record; a computational logical-time relation may be represented with an integer timestamp.

---

# 44. Provisional TemporalProfile

```text
TemporalProfile = <
  Domain,
  TemporalAlternatives : instant/interval/event/process-position/etc.,
  TemporalStanding,
  OrderStructure,
  Simultaneity/CoTemporality?,
  IntervalStructure?,
  Duration/Metric?,
  Clock/MeasurementProfile?,
  Timescale/Coordinate?,
  Rate/Frequency/Periodicity?,
  CausalRelation?,
  Representation/Timestamps?,
  Validity/Observation/ProcessingRoles?,
  Uncertainty/Vagueness,
  Provenance/Authority,
  Scope
>
```

### TA-109

Only standing + typed temporal relation structure + scope are candidate core; most remaining fields are optional enrichments.

---

# 45. Provisional TemporalClaim

```text
TemporalClaim = <
  Relata/Event/Process,
  ClaimType : before/after/simultaneous/at/interval/duration/etc.,
  Reference/Frame/Timescale if applicable,
  Clock/MeasurementSource?,
  Coordinate/Timestamp?,
  ValidityRole : event/observation/record/processing/etc.,
  Precision/Resolution,
  Uncertainty,
  Evidence/Provenance,
  Scope
>
```

### TA-110

Bare timestamps are under-specified when temporal consequences matter.

---

# 46. Strongest non-collapse stack after MF6-A

```text
Time / Temporal Structure
 ≠ R
 ≠ Sequence
 ≠ Change
```

```text
Clock
 ≠ Clock Reading
 ≠ Time Unit
 ≠ Timescale
 ≠ Target Time
```

```text
Temporal Position
 ≠ Timestamp
 ≠ Event
```

```text
Instant
 ≠ Event
 ≠ Interval
```

```text
Temporal Interval
 ≠ Duration
```

```text
Temporal Order
 ≠ Causal Order
 ≠ Processing Order
```

```text
Logical Time
 ≠ Physical Time
```

```text
Event Time
 ≠ Observation Time
 ≠ Ingestion Time
 ≠ Processing Time
 ≠ Record Time
 ≠ Presentation Time
```

```text
Same Timestamp
 ≠ Simultaneous by default
```

```text
Frame Index
 ≠ Physical Time
```

```text
Frequency
 ≠ Period
 ≠ Phase
 ≠ Time
```

```text
Spatial Standing
 ≠ Temporal Standing
```

---

# 47. Claims rejected by MF6-A

Reject as universal/foundational claims:

- time is the real line by identity;
- any ordered sequence is temporal;
- any changing parameter is time;
- time is a clock or clock reading;
- time is reduced to caesium oscillations because the SI second is atomically defined;
- timestamp equals temporal position or event;
- calendar date equals target time;
- frame index equals elapsed/source time;
- event equals instant;
- all events are instantaneous;
- temporal interval equals numerical duration;
- endpoint coordinate subtraction always equals invariant duration;
- same timestamp implies simultaneity without synchronization/reference semantics;
- simultaneity is globally absolute in all domains;
- causality and temporal order are identical relations;
- temporal order must be total;
- incomparable distributed events are necessarily simultaneous;
- logical clocks measure physical elapsed time;
- processing/insertion order equals target event order;
- observation time equals occurrence time;
- one generic timestamp field is sufficient provenance for agent/data systems;
- period/frequency/phase are interchangeable with Time;
- temporal coordinate epoch is the beginning of Time;
- timestamp precision equals temporal accuracy;
- spatial and temporal axes are ontologically identical because relativity uses spacetime coordinates;
- relativity by itself reopens MF5 Space Foundations.

---

# 48. Primary/authoritative anchors

- **Albert Einstein (1905)**, `Zur Elektrodynamik bewegter Körper`, *Annalen der Physik* 322(10):891–921, DOI 10.1002/andp.19053221004. In §1 Einstein makes the physical meaning of a common time for spatially separated locations depend on a synchronization convention/procedure involving clocks and light signals; remote simultaneity is therefore not obtained from isolated local readings alone.
- **Hermann Minkowski (1908)**, `Raum und Zeit / Space and Time`. Special-relativity spacetime is the decisive warning that space/time coordinates can belong to one coupled formal domain without warranting an ontological collapse of all spatial and temporal relations.
- **Bureau International des Poids et Mesures (BIPM), SI base unit second / 26th CGPM Resolution 1 (2018; effective 2019; current SI brochure updated 2026)**. The SI second is defined via the fixed numerical value `Δν_Cs = 9 192 631 770 Hz`; the historical definition moved from solar/astronomical to atomic standards. This anchors `unit/realization ≠ temporal ontology` and `frequency standard ≠ Time`.
- **Leslie Lamport (1978)**, `Time, Clocks, and the Ordering of Events in a Distributed System`, *Communications of the ACM* 21(7):558–565, DOI 10.1145/359545.359563. The paper distinguishes a happened-before partial order, logical clocks/total-order extensions, and physical-clock synchronization, providing hard counterexamples to `order = physical time` and `logical timestamp = elapsed time`.

---

# 49. Deep reconstruction

Naive model:

```text
Reality
  ↓
events occur on one universal real-number line
  ↓
clock reads the number
  ↓
timestamp is the time
  ↓
sort timestamps to recover truth
```

MF6-A replaces it with:

```text
Target / formal / system domain
        │
        ▼
Temporal standing
 ├─ occurrence/when alternatives
 ├─ earlier/later/succession
 ├─ simultaneity/co-temporality? (typed/reference-relative where needed)
 ├─ interval structure?
 ├─ duration/metric?           optional enrichment
 └─ causal/periodic structure? optional relation
        │
        ├─ observed/measured by clocks/processes
        │      ↓
        │   clock states/readings + uncertainty
        │
        ├─ represented via timescale/epoch/unit/calendar
        │      ↓
        │   timestamps/dates
        │
        └─ consumed by systems
               ↓
          logical order / scheduling /
          validity / synchronization
```

The key move is:

> **Temporal standing is prior to any one clock, coordinate, timestamp, sequence or metric representation.**

---

# 50. Deepest MF6-A result

The strongest provisional result is:

> **A temporal domain is a scope-relative domain in which distinctions among occurrences, temporal positions, intervals or process phases have non-arbitrary standing as when-like or temporal-order/interval alternatives, and in which one or more typed temporal relation families—such as earlier/later, succession, co-temporality, interval inclusion/overlap, duration or recurrence—are formally constituted, operationally recruited or target-grounded. Clock readings, timestamps, timescales, calendars, frames and numerical coordinates are representations/measurement enrichments rather than Time itself.**

Compact:

```text
TemporalDomain
 = Temporal Alternatives
 + Temporal Standing
 + Typed Temporal Relation Structure
 + Standing Route
 + Scope
```

with point/interval/event primacy still intentionally unresolved.

---

# 51. MF5 boundary check

MF6-A does **not** trigger an MF5 FoundationReopenCondition.

Why:

- MF5 already says shared `R` structure does not imply spatial role identity.
- Einstein/Minkowski coupling requires typed spacetime relations, not `temporal = positional`.
- Temporal coordinate axes can be part of a spacetime chart while retaining different metric/causal roles from spatial axes.

### TA-111

**MF5 remains frozen.**

A reopen requires a later concrete spacetime counterexample showing MF5 PositionalStanding itself is incoherent, not merely that space and time are physically coupled.

---

# 52. MF6-B handoff — Temporal Order, Interval, Duration, Measure & Clocks

MF6-A deliberately leaves the hardest measurement question unresolved:

> **Given temporal standing, what additional structures are required to compare temporal extent, define duration, construct clocks, synchronize them, and decide which duration/clock relations are invariant or reference-relative?**

MF6-B must research:

- strict/non-strict temporal order;
- total vs partial orders;
- interval orders and interval algebra;
- point-first vs interval-first temporal models;
- open/closed/instantaneous intervals;
- temporal topology/continuity/discreteness;
- duration versus interval identity;
- additive duration/measure;
- metric/affine temporal structures;
- periodic processes and clock construction;
- clock rate, offset, drift, stability, precision, accuracy, resolution;
- synchronization versus syntonization/rate agreement;
- physical clock versus logical clock;
- clock comparison and calibration;
- SI second and realization;
- monotonicity versus correctness;
- uncertainty/bounds rather than fabricated timestamps;
- whether all temporal domains need duration/metric structure;
- leap/discontinuous civil representations only as measurement/representation hard cases;
- defer full special/general-relativistic proper/coordinate time to the dedicated relativity round.

Central attack:

```text
Order ≠ Duration
Interval ≠ Duration
Clock ≠ Time
Clock Rate Agreement ≠ Clock Synchronization
Same Frequency ≠ Same Phase
Monotonic ≠ Accurate
Precise ≠ Correct
Coordinate Difference ≠ Invariant Duration
```

**Next: MF6-B — Temporal Order, Interval, Duration, Measure & Clocks.**
