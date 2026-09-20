# Ordivon Media Foundations — MF4-E Temporal Composition, Sequence, Rhythm & Synchronization

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 16 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4-A Composition Ontology, MF4-B Parts/Units/Boundaries/Segmentation, MF4-C Relations/Binding/Dependency/Constraint and MF4-D Hierarchy/Recursion/Modularity/Scale complete and provisional.  
**Status:** MF4-E complete and PROVISIONAL. Composition Foundations remain UNFROZEN.  
**Next:** MF4-F — Spatial Composition, Layout, Geometry & Topology.

---

# 1. Problem statement

MF4-C already admitted temporal relation types such as before/after/overlap and synchronization. MF4-D admitted multiple timescales and temporal hierarchy.

But neither answers the stronger question:

> **When does a succession of states/events become one temporal composition rather than merely happening one after another?**

Temporal composition appears in:

- music;
- speech;
- gesture;
- animation;
- film/video editing;
- event perception;
- interaction loops;
- real-time computation;
- sensor fusion;
- narrative;
- distributed systems;
- motor coordination.

The dangerous collapses are:

`Time = Timestamp`;

`Succession = Sequence = Temporal Whole`;

`Order = Timing`;

`Rhythm = Periodicity = Meter = Beat = Tempo`;

`Synchrony = Exact Simultaneity = Binding`;

`Presentation Order = Causal Order = Narrative Order`;

`Deadline = Duration`;

`Retiming = Same Composition`.

MF4-E rejects all of them as universal identities.

---

# 2. Time coordinate is not temporal composition

A timestamp assigns a coordinate such as `t_i` to an event/state.

A set of timestamped events can remain organizationally unrelated.

### Result

**CE-01 — Temporal coordinates/timestamps provide location in a time reference system but do not by themselves establish temporal composition.**

---

# 3. Succession is only a weak relation

If `A` occurs before `B`, then succession/order exists.

But random unrelated events also succeed one another.

### Result

**CE-02 — Mere succession is insufficient for temporal composition.**

---

# 4. Sequence requires selected membership + order

A temporal sequence minimally requires:

- a selected set of events/states;
- an order relation among them;
- a scope under which they count as one ordered series.

### Result

**CE-03 — Sequence is stronger than succession because it requires membership/series identity in addition to temporal precedence.**

---

# 5. Sequence is still weaker than a temporal whole

A log file may list ordered independent events.

A playlist may contain unrelated clips.

### Result

**CE-04 — Ordered sequence does not by itself establish one temporally integrated whole; additional continuity, grouping, constraint, role, causal, rhythmic, narrative or task relations may be required.**

---

# 6. Temporal composition requires relation-bearing order

A provisional skeleton:

`TempComp(E, R_t, B_t, H_t, Σ) -> W_t`

where:

- `E` = events/states/intervals;
- `R_t` = temporal relations/order/timing constraints;
- `B_t` = temporal boundaries/grouping;
- `H_t` = history/predictive/phase state;
- `Σ` = scope/granularity/task;
- `W_t` = temporal whole.

### Result

**CE-05 — Temporal composition is organization of events/states through typed temporal relations and boundary/grouping conditions under scope, not simply timestamped membership.**

---

# 7. Event time has multiple descriptors

An event may have:

- onset;
- offset;
- duration;
- internal phase;
- peak/accent;
- deadline;
- recurrence period;
- uncertainty interval.

### Result

**CE-06 — Event timing cannot universally be represented by one timestamp.**

---

# 8. Point events and interval events differ

A click can be approximated as a point event.

A spoken phrase, shot, gesture or computation occupies duration.

### Result

**CE-07 — Temporal ontology must support both point-like and interval/process events.**

---

# 9. Duration ≠ Position

Two events can start at the same time but have different durations.

Two equal-duration events can occur at different times.

### Result

**CE-08 — Temporal location and duration are independent dimensions.**

---

# 10. Duration ≠ Inter-onset Interval

If event A lasts 500 ms and next onset follows after 600 ms, duration and onset spacing are distinct.

### Result

**CE-09 — Event duration, inter-onset interval, gap and period must not be collapsed.**

---

# 11. Allen-style interval relations remain essential

Intervals can:

- precede;
- meet;
- overlap;
- contain/be during;
- start together;
- finish together;
- equal.

### Result

**CE-10 — Temporal composition requires richer interval relations than scalar timestamp sorting.**

---

# 12. Order and timing are distinct

Sequence `[A,B,C]` can preserve order under many different inter-event spacings.

### Result

**CE-11 — Ordinal order and metric timing are distinct temporal structures.**

---

# 13. Same order can produce different rhythm/meaning

Changing intervals while preserving event order changes:

- rhythm;
- perceived grouping;
- urgency;
- synchronization demands;
- speech prosody;
- edit pacing.

### Result

**CE-12 — Ordinal equivalence is weaker than temporal-composition equivalence.**

---

# 14. Same metric intervals can support different role/accent organization

Identical onset intervals can be interpreted differently depending accents/grouping/context.

### Result

**CE-13 — Metric timing alone does not uniquely determine temporal role structure.**

---

# 15. Rhythm is not simply temporal repetition

A nonperiodic sequence can still exhibit rhythm through structured relative timing/accent/grouping.

### Result

**CE-14 — Rhythm is structured temporal patterning, not synonymous with exact periodic repetition.**

---

# 16. Rhythm ≠ Meter

Povel–Essens distinguish temporal patterns that readily support a metrical framework from nonmetrical patterns.

A rhythm can exist without a regular metric grid.

### Result

**CE-15 — Rhythm and meter are distinct; meter is a stronger periodic/hierarchical temporal framework that can organize rhythmic events.**

---

# 17. Meter ≠ Beat

A beat can be a perceived/maintained periodic pulse.

Meter organizes pulses/events into higher-order recurring accent structures.

### Result

**CE-16 — Beat/pulse and meter/hierarchical accent organization are distinct temporal profiles.**

---

# 18. Beat ≠ Event onset

The perceived beat can occur at moments without an actual acoustic onset.

### Result

**CE-17 — Temporal reference points can be inferred/maintained internally and need not coincide with every physical event.**

---

# 19. Tempo ≠ Rhythm

Uniformly speeding a rhythm can preserve relative timing pattern while changing rate.

### Result

**CE-18 — Tempo/rate is a scale parameter of temporal realization, not the complete rhythm identity.**

---

# 20. Uniform retiming is a candidate invariance

Let event times be transformed by:

`t'_i = a t_i + b`, `a > 0`.

Translation `b` changes absolute placement.

Scaling `a` changes tempo while preserving order and relative interval ratios.

### Result

**CE-19 — Many temporal compositions admit affine time-shift/tempo-scale equivalence under appropriate scope, but this invariance must be declared rather than assumed.**

---

# 21. Uniform scaling can still break composition

At extreme rates:

- auditory streams may segregate/fuse differently;
- motor synchronization may fail;
- speech becomes unintelligible;
- real-time deadlines change relevance.

### Result

**CE-20 — Structural retiming invariance can fail when perceptual, action or resource constraints are rate-dependent.**

---

# 22. Local time warping differs from global tempo scaling

Changing one interval while preserving others can alter rhythm, grouping or event identity.

### Result

**CE-21 — Global retiming and local temporal distortion are distinct transformations.**

---

# 23. Relative timing can be composition-defining

If changing interval ratios changes recognition/grouping/function, those relations are composition-defining under MF4-C's counterfactual criterion.

### Result

**CE-22 — Temporal intervals/ratios can be constitutive relations of a temporal whole.**

---

# 24. Accent is not duration/onset alone

Temporal accents can arise from:

- intensity;
- pitch/change;
- duration;
- position;
- learned metric expectation.

### Result

**CE-23 — Temporal accent/salience and physical onset/duration are distinct.**

---

# 25. Povel–Essens make meter an organization hypothesis, not raw input

Their temporal-pattern work proposes that perceivers can induce an internal temporal clock/framework from accented event structure and use it to encode/reproduce patterns.

### Result

**CE-24 — Higher-order metric organization can be inferred from event relations rather than explicitly present as a separate signal channel.**

---

# 26. Temporal framework can improve encoding

Metrical structure can make otherwise similar interval patterns easier to encode/discriminate/reproduce in the studied paradigms.

### Result

**CE-25 — Temporal composition can change accessibility/precision of constituent timing without changing constituent identities.**

---

# 27. Meter induction is not universal rhythm ontology

Nonmetrical rhythms and speech-like timing remain possible.

### Result

**CE-26 — Metric-clock models are powerful profiles/mechanisms for some temporal patterns, not definitions of all temporal composition.**

---

# 28. Dynamic attending adds prospective structure

Jones & Boltz propose future-oriented attending for temporally coherent events; Large & Jones model attending rhythms that can entrain to changing event rates and concentrate attention near expected times.

### Result

**CE-27 — Temporal composition can support prospective expectancy: relations organize not only past event order but predictions about when future events are likely/relevant.**

---

# 29. Temporal expectancy ≠ Physical periodicity

A listener/system can maintain expectations under tempo change, syncopation or missing events.

### Result

**CE-28 — Temporal expectation is stateful/model-relative and not reducible to exact physical repetition.**

---

# 30. Entrainment ≠ Synchronization identity

Entrainment is dynamical adjustment/locking of an internal/action process to external temporal structure.

Synchronization describes a relative timing relation/state.

### Result

**CE-29 — Entrainment is a process/mechanism leading to temporal coordination; synchrony is a relation/profile.**

---

# 31. Phase ≠ Tempo

Two oscillations can have the same frequency but different phase.

### Result

**CE-30 — Rate/frequency and phase alignment are distinct synchronization dimensions.**

---

# 32. Phase locking does not require zero phase difference

Stable coordination can maintain a nonzero relative phase.

### Result

**CE-31 — Synchronization may mean stable phase relation rather than exact simultaneous onsets.**

---

# 33. Synchronization is reference/tolerance dependent

Real systems require a tolerance/window:

`Sync(A,B | frame, ε, phase_target, history)`.

### Result

**CE-32 — Exact `Δt=0` is not the universal definition of synchrony.**

---

# 34. Jitter ≠ Drift

Jitter is short-timescale timing variability around a reference.

Drift is systematic change of relative phase/clock relation across time.

### Result

**CE-33 — Timing noise/jitter and clock/phase drift are distinct synchronization failures.**

---

# 35. Offset ≠ Drift

A constant 50 ms lag can be stable synchronization under one relation even though not zero-offset simultaneity.

### Result

**CE-34 — Fixed offset and unstable drift are distinct temporal relation profiles.**

---

# 36. Subjective simultaneity is adaptive

Fujisaki et al. found that sustained exposure to a fixed audiovisual lag shifts subjective simultaneity toward that lag; related work shows temporal-order judgments also recalibrate.

### Result

**CE-35 — Cross-modal simultaneity is adaptively calibrated and history-dependent; physical onset equality and perceived simultaneity are distinct.**

---

# 37. Temporal recalibration can be content/context specific

Concurrent audiovisual pairings can support different recalibrations when distinguishable by source/context.

### Result

**CE-36 — There need not be one global audiovisual synchrony offset; synchronization calibration can be source/context-specific.**

---

# 38. Recalibration ≠ Arbitrary binding

Fujisaki-style adaptation shifts the point of subjective simultaneity but does not imply arbitrarily large lags will be fused indefinitely.

### Result

**CE-37 — Temporal binding has adaptive but bounded relation structure; recalibration changes tolerance/reference, not the identity of every asynchronous event.**

---

# 39. Cross-modal synchrony ≠ Common cause by itself

Two unrelated events can coincide accidentally.

### Result

**CE-38 — Temporal coincidence is evidence/cue for common-source binding, not sufficient common-cause identity.**

---

# 40. Common cause can tolerate asynchrony

Light and sound from one event arrive/process at different times.

### Result

**CE-39 — Common-source temporal composition can require compensation for propagation/processing delays rather than raw physical simultaneity at the observer.**

---

# 41. Temporal binding window is relation/task dependent

Different modalities/stimuli/tasks tolerate different asynchronies.

### Result

**CE-40 — Temporal binding should be modeled with typed, potentially asymmetric windows rather than one universal constant.**

---

# 42. Temporal binding window ≠ Temporal resolution

A system may discriminate that two events are asynchronous yet still bind them into one event/source under another task.

### Result

**CE-41 — Temporal order/simultaneity discrimination and multisensory binding tolerance are distinct capabilities.**

---

# 43. Sequence membership can survive temporal gaps

A melody can pause and resume.

A conversation can be interrupted.

A software transaction can await external input.

### Result

**CE-42 — Temporal contiguity is not universally necessary for temporal-whole identity.**

---

# 44. Interruption ≠ Termination

A gap can mean:

- pause;
- suspension;
- boundary/end;
- missing evidence;
- dropped packet.

### Result

**CE-43 — Gap interpretation depends on whole model/context; temporal silence/absence does not uniquely define termination.**

---

# 45. Resumption requires identity criterion

To say one process/event resumes, the system needs continuity in some profile:

- goal;
- role;
- state;
- causal chain;
- participant identity;
- unresolved obligation;
- musical/narrative pattern.

### Result

**CE-44 — Temporal-whole persistence across interruption requires typed continuity invariants rather than mere later similarity.**

---

# 46. Resumption ≠ Repetition

Repetition instantiates a similar/new token.

Resumption continues the same token/process under an identity criterion.

### Result

**CE-45 — Resumption and recurrence/repetition are distinct temporal identity relations.**

---

# 47. Recurrence ≠ Periodicity

An event/type may recur irregularly.

### Result

**CE-46 — Recurrence requires re-occurrence/type relation, not fixed period.**

---

# 48. Periodicity ≠ Rhythm

A machine clock is periodic but may not constitute rhythm in a perceptual/musical sense.

### Result

**CE-47 — Periodicity is a temporal regularity profile, not the full ontology of rhythm.**

---

# 49. Repetition can create higher-order grouping

Repeated motifs/events can become units at a larger temporal scale.

### Result

**CE-48 — Repetition/recurrence can support temporal hierarchy/chunking but does not guarantee it.**

---

# 50. Loop ≠ Simple repetition

A loop adds a rule returning control/playback from endpoint to an earlier state/segment.

### Result

**CE-49 — Looping is recursive/cyclic temporal control structure, not merely similarity across repeated events.**

---

# 51. Loop identity can survive iterations

Each iteration may be a distinct episode while belonging to one loop process.

### Result

**CE-50 — Iteration token identity and loop/process identity are distinct levels.**

---

# 52. Temporal hierarchy is multi-scale grouping

Notes → motif → phrase → section.

Actions → subevent → event → episode.

### Result

**CE-51 — Temporal composition can be recursively hierarchical across durations/granularities.**

---

# 53. Fine boundary ≠ Coarse boundary

MF4-B event segmentation already showed nested event boundaries.

### Result

**CE-52 — Temporal boundary status is granularity-relative; the same instant can close one subevent while remaining inside a larger whole.**

---

# 54. Temporal hierarchy need not be perfectly nested

Musical phrase boundaries, gesture boundaries and linguistic boundaries can cross-cut.

### Result

**CE-53 — Multiple temporal segmentation/hierarchy systems can overlap or misalign.**

---

# 55. Temporal chunking ≠ Hierarchy ontology

A chunk may reflect memory/processing convenience rather than a stable structural event/module.

### Result

**CE-54 — Temporal chunking is one unitization strategy, not automatic proof of a natural temporal hierarchy.**

---

# 56. Rhythm can organize attention prospectively

Dynamic attending accounts suggest regularity guides allocation toward expected future time points.

### Result

**CE-55 — Temporal organization can alter information-acquisition priority across future time, connecting MF4 composition to MF2 attention without collapsing them.**

---

# 57. Temporal attention ≠ Temporal composition

A sequence can have temporal organization regardless of whether an observer currently attends to it.

### Result

**CE-56 — Attention can exploit temporal composition but is not constitutive of standing temporal structure.**

---

# 58. Presentation order ≠ Causal order

A film can show effect before cause.

A report can present outcomes before methods.

### Result

**CE-57 — The order in which information is presented/experienced is distinct from the represented causal order of events.**

---

# 59. Narrative order ≠ Story/chronological order

Narratives can use flashback, flashforward and parallel timelines.

### Result

**CE-58 — Narrative/discourse order and represented chronological order are distinct temporal compositions.**

---

# 60. Causal order ≠ Physical timestamp order in all descriptions

Causal claims operate at model/event abstractions; measured timestamps can be delayed/noisy and mediated.

### Result

**CE-59 — Causal ordering and observed timestamp ordering require separate provenance/model assumptions.**

---

# 61. Edit order can be composition-defining

Reordering identical shots can change inferred relation/meaning while preserving shot contents.

### Result

**CE-60 — Temporal juxtaposition/order can contribute representational content beyond individual clip content.**

---

# 62. Cut ≠ Event boundary

A film edit can cut within one represented event or span one shot across an event boundary.

### Result

**CE-61 — Presentation/medium segmentation boundaries and represented event boundaries are distinct.**

---

# 63. Transition duration matters

Hard cut, dissolve, fade and continuous camera move differ temporally even if the before/after scenes match.

### Result

**CE-62 — Temporal transition form/duration is a composition dimension distinct from sequence membership/order.**

---

# 64. Pace ≠ Tempo exactly

Narrative/editing pace can depend on event density, shot duration, information rate and action intensity rather than one periodic beat frequency.

### Result

**CE-63 — Tempo is one rate construct; broader pacing can be defined by several event/information-density profiles.**

---

# 65. Real-time composition introduces deadlines

Liu & Layland's hard-real-time scheduling work treats tasks as requiring guaranteed completion relative to deadlines/periods under specific scheduling assumptions.

### Result

**CE-64 — In real-time systems, temporal correctness can depend not only on result value/order but on whether operations occur before declared deadlines.**

---

# 66. Deadline ≠ Duration

A task can take 10 ms and still miss a 5 ms deadline.

A 100 ms task can satisfy a 1 s deadline.

### Result

**CE-65 — Execution duration and deadline satisfaction are distinct.**

---

# 67. Deadline ≠ Period

Periodic task recurrence interval and each job's deadline can be related but are conceptually distinct.

### Result

**CE-66 — Period, release time, execution time and deadline are separate temporal parameters.**

---

# 68. Lateness ≠ Incorrect value

A computation can produce semantically correct output after it is no longer useful/valid.

### Result

**CE-67 — Temporal correctness and value/content correctness are separate evaluation dimensions.**

---

# 69. Hard vs soft deadline

Some deadlines define validity/safety boundaries; others produce graded utility loss.

### Result

**CE-68 — Deadline semantics can be hard, firm or soft/utility-graded; temporal failure is not universally binary.**

---

# 70. Deadline is relation to an external requirement

A timestamp alone does not create urgency.

### Result

**CE-69 — Deadline is a normative/operational temporal constraint linking an event/computation to a required completion time under a task.**

---

# 71. Temporal utility is time-dependent

Let utility of effect/output be `U(y,t)`.

### Result

**CE-70 — Temporal composition can alter value because identical outputs at different times can have different utility.**

---

# 72. Scheduling order ≠ Causal dependency order

A scheduler may choose among causally independent tasks based on deadlines/priorities.

### Result

**CE-71 — Execution/scheduling order is a resource-allocation composition layer distinct from logical/causal dependency order.**

---

# 73. Priority ≠ Temporal precedence

Higher-priority task may execute first, but priority is a control policy property, not the observed order itself.

### Result

**CE-72 — Priority and realized temporal order are distinct.**

---

# 74. Earliest deadline ≠ Earliest arrival

Real-time scheduling provides a direct case where event release/order and optimal scheduling priority can differ.

### Result

**CE-73 — Temporal organization can be policy-dependent rather than simply chronological.**

---

# 75. Real-time constraint can make small delays composition-defining

If a response must occur within a control window, changing latency can alter whole-level validity/function despite identical logical relation structure.

### Result

**CE-74 — Latency/deadline relations can be composition-defining under MF4-C's counterfactual criterion.**

---

# 76. Latency ≠ Throughput

A system can process many items per second while individual responses are slow, or vice versa.

### Result

**CE-75 — Latency and rate/throughput are distinct temporal performance dimensions.**

---

# 77. Throughput ≠ Tempo

Throughput is count/output per time over a process/system; tempo is a realization rate of a temporal pattern.

### Result

**CE-76 — System throughput and temporal-pattern tempo are distinct rate concepts.**

---

# 78. Temporal ordering can be partial

Distributed/concurrent events need not admit a meaningful total order.

Some are causally independent/concurrent.

### Result

**CE-77 — Temporal composition can use partial orders; forcing one total sequence can invent relations absent from the system.**

---

# 79. Concurrency ≠ Simultaneity

Two operations are concurrent if their intervals/causal relations overlap or are unordered under the relevant model; exact same timestamp is unnecessary.

### Result

**CE-78 — Concurrency and exact simultaneity are distinct.**

---

# 80. Synchronization can reduce concurrency freedom

A barrier forces processes to wait for one another.

### Result

**CE-79 — Synchronization is a constraint on relative temporal freedom and can reduce admissible schedules.**

---

# 81. Synchronization has cost

Waiting/coordination can reduce throughput or increase latency.

### Result

**CE-80 — Synchronization can improve coherence while imposing temporal/resource costs.**

---

# 82. Too little synchronization can fail coherence

Examples:

- audiovisual lip-sync error;
- race condition;
- ensemble desynchronization;
- stale distributed state.

### Result

**CE-81 — Temporal composition often trades coordination accuracy against latency/flexibility.**

---

# 83. Too much synchronization can be harmful

Global barriers can create unnecessary waiting and fragility.

### Result

**CE-82 — Maximal synchrony is not universally optimal.**

---

# 84. Sensorimotor synchronization is active temporal control

Metronome tapping experiments show synchronization involves error correction/adaptation rather than static equality of timestamps.

### Result

**CE-83 — Active synchronization is a feedback/control process maintaining a relation under perturbations.**

---

# 85. Synchronization error correction can be nonlinear

Engbert et al. model/test nonlinear error correction in metronome synchronization.

### Result

**CE-84 — Synchronization dynamics need not be linear proportional correction; mechanism must be empirically specified.**

---

# 86. Phase correction ≠ Period correction

A system can correct current phase offset without changing its internal period, or adjust tempo/period separately.

### Result

**CE-85 — Phase and period correction are distinct coordination operations.**

---

# 87. Temporal prediction enables proactive coordination

A system can act before observing the next event if periodic/structured timing supports prediction.

### Result

**CE-86 — Temporal composition can support anticipatory control, not only reactive alignment.**

---

# 88. Prediction failure can trigger temporal regrouping

MF4-B event-segmentation work already suggested event-model updating near prediction failures.

### Result

**CE-87 — Temporal boundary formation and temporal prediction can interact reciprocally; prediction error is a mechanism cue, not universal boundary ontology.**

---

# 89. Repetition creates expectation but not certainty

A repeated rhythm can be violated/syncopated.

### Result

**CE-88 — Temporal regularity induces probabilistic expectations rather than logical necessity in many perceptual compositions.**

---

# 90. Syncopation shows event absence can be structurally meaningful

A missing/shifted expected event can be perceived relative to a maintained metrical framework.

### Result

**CE-89 — Temporal composition can give representational/perceptual significance to expected-but-absent events.**

---

# 91. Silence can be a temporal constituent

Rests/gaps can carry structural role in music/speech/editing.

### Result

**CE-90 — Absence of signal can function as a temporal component when bounded/expected within a compositional framework.**

---

# 92. Missing event ≠ Silence token automatically

Packet loss or sensory dropout may be an error rather than intended rest.

### Result

**CE-91 — Intended gap/rest and missing evidence/data loss are distinct provenance/evaluation states.**

---

# 93. Temporal regularity can be hierarchical

Meter/rhythm can organize beats into nested cycles.

### Result

**CE-92 — Multiple periodicities can coexist and coordinate across temporal scales.**

---

# 94. Polyrhythm falsifies one-clock universality

Multiple periodic structures can coexist without reducing to one immediately salient pulse.

### Result

**CE-93 — Temporal composition can sustain multiple interacting rhythmic frames; one global beat is not universally required.**

---

# 95. Cross-rhythm coordination requires relation profiles

Two rhythms can be related by frequency ratios, phase relations and recurrence alignment.

### Result

**CE-94 — Multi-rhythm composition is relational across periodic processes, not mere superposition.**

---

# 96. Rhythm and grouping can conflict

Local intervals may suggest one grouping while metric accent suggests another.

### Result

**CE-95 — Temporal whole inference can involve competing constraints rather than one deterministic segmentation.**

---

# 97. Temporal composition can remain ambiguous

Listeners may hear the same sequence under different metric/grouping interpretations.

### Result

**CE-96 — Temporal organization can be probabilistic/multistable; unique temporal parse is not universally required.**

---

# 98. Time reference frame matters

Timing can be measured relative to:

- global clock;
- local device clock;
- event onset;
- beat phase;
- narrative chronology;
- causal chain.

### Result

**CE-97 — Temporal relation content depends on declared reference frames/clocks.**

---

# 99. Clock equality ≠ Event simultaneity

Unsynchronized clocks can produce unequal timestamps for simultaneous events; synchronized timestamps can be misleading under delays.

### Result

**CE-98 — Clock calibration/provenance is part of temporal evidence, not equivalent to event ontology.**

---

# 100. Clock drift can change inferred order

In distributed measurement, clock error can invert close event orders.

### Result

**CE-99 — Temporal evidence uncertainty must be distinguished from uncertainty about underlying event relation.**

---

# 101. Temporal relation confidence is first-class

A system may maintain:

`P(before(A,B)|evidence)`

rather than a fixed relation.

### Result

**CE-100 — Temporal relation/order/boundary/synchrony uncertainty is admissible and distinct from event identity uncertainty.**

---

# 102. Resampling is a signal operation, not temporal-composition identity

Changing sampling rate changes observed temporal discretization.

### Result

**CE-101 — Temporal signal resampling and higher-level event/rhythm retiming are distinct transformations.**

---

# 103. Temporal aliasing can destroy recoverability

If sampling is too sparse relative to underlying variation, different temporal patterns can produce identical samples.

### Result

**CE-102 — MF1 aliasing applies to temporal composition evidence: sampling can erase distinctions needed to infer order, rhythm, phase or events.**

---

# 104. Event aliasing is higher-level

Even with signal-level recovery, coarse event segmentation may collapse distinct event sequences into one macro event label.

### Result

**CE-103 — Signal temporal aliasing and event/macro temporal aliasing are distinct levels.**

---

# 105. Retiming equivalence must name preserved structure

Possible invariants:

- event order;
- relative interval ratios;
- metric hierarchy;
- phase relation;
- causal dependency;
- narrative structure;
- deadline validity.

### Result

**CE-104 — `Same after retiming` is underspecified unless the preserved temporal relations are named.**

---

# 106. Uniform tempo scaling may preserve rhythm but violate deadline

Same temporal pattern at half speed can preserve musical structure while missing real-time control constraints.

### Result

**CE-105 — Temporal equivalence is role/scope dependent; one transformation can preserve one composition profile and destroy another.**

---

# 107. Time reversal is a strong falsifier

Reversing a sequence can preserve constituent durations while changing:

- causal plausibility;
- speech intelligibility;
- motor feasibility;
- narrative meaning;
- entropy/irreversibility constraints.

### Result

**CE-106 — Temporal compositions are not universally invariant under reversal.**

---

# 108. Some temporal patterns are reversal-symmetric

A palindrome-like event pattern can retain selected formal relations under reversal.

### Result

**CE-107 — Reversal invariance is composition-specific, not universally absent.**

---

# 109. Temporal direction can be representational

A video played backward can represent a different event trajectory while containing the same frames.

### Result

**CE-108 — Direction/order can be content-bearing at the representational level.**

---

# 110. Temporal direction can be causal/physical

Some processes have irreversible dynamics/thermodynamic constraints.

### Result

**CE-109 — Presentation-direction effects and physical irreversibility are distinct temporal phenomena.**

---

# 111. Temporal composition can be standing

A score, animation timeline, schedule or video file specifies temporal relations while not playing/executing.

### Result

**CE-110 — Standing temporal composition and active temporal realization are distinct.**

---

# 112. Active performance can deviate from standing temporal specification

A musician plays behind beat; a scheduler misses deadline; playback drops frames.

### Result

**CE-111 — Temporal specification and realized timing are separate evaluation layers.**

---

# 113. Realized deviation can be expressive rather than erroneous

Rubato intentionally alters local timing while preserving higher-level phrase/meter identity.

### Result

**CE-112 — Temporal deviation from nominal specification can be expressive/allowed under an equivalence/tolerance profile rather than automatically error.**

---

# 114. Timing tolerance can be asymmetric

Late and early events may have different costs/acceptability.

### Result

**CE-113 — Temporal error profiles need not be symmetric around target time.**

---

# 115. Temporal tolerance can be role-dependent

A subtitle, percussion hit, safety shutdown and background animation have different acceptable timing windows.

### Result

**CE-114 — Temporal precision requirements are role/task typed, not one universal threshold.**

---

# 116. Temporal coherence is multi-dimensional

A sequence can be coherent in:

- order;
- rhythm;
- causal progression;
- narrative expectation;
- synchronization;
- deadline satisfaction;

while failing another dimension.

### Result

**CE-115 — `Temporal coherence` is a profile, not a scalar.**

---

# 117. Local temporal correctness ≠ Global temporal coherence

Each pair of events can satisfy local order constraints while a global cycle/deadline/resource schedule is impossible.

### Result

**CE-116 — MF4-C local/global consistency distinction applies temporally.**

---

# 118. Temporal composition can constrain future possibilities

A completed prefix changes which continuations are valid/expected.

### Result

**CE-117 — Temporal composition is stateful: history can alter admissible/predicted future event structure.**

---

# 119. Prefix identity ≠ Whole identity

Two sequences can share the same prefix and diverge later.

### Result

**CE-118 — Temporal whole identity cannot be inferred from partial prefix alone without predictive/closure assumptions.**

---

# 120. Suffix can reinterpret prefix

Narrative reveal, musical cadence or linguistic continuation can change interpretation of earlier events.

### Result

**CE-119 — Temporal composition can support retrospective reorganization; interpretation is not necessarily fixed online at first occurrence.**

---

# 121. Retrospective reinterpretation ≠ Physical history change

Later context changes representation/interpretation, not what physically happened.

### Result

**CE-120 — Temporal representation history and underlying event history must remain distinct.**

---

# 122. Causal, logical and temporal precedence are separate

A prerequisite can be logically required while physically precomputed; causal influence can be mediated; narrative order can reorder both.

### Result

**CE-121 — `precedes` must always be typed: temporal, causal, logical, presentation, narrative, execution or dependency precedence.**

---

# 123. Temporal dependency can be conditional

B must follow A only if condition C holds.

### Result

**CE-122 — Temporal constraints can be conditional/contextual, not static total order rules.**

---

# 124. Partial-order sequence can admit many schedules

A dependency graph may define multiple valid linearizations.

### Result

**CE-123 — One temporal composition can correspond to a set of valid realized orders.**

---

# 125. Schedule token ≠ Temporal specification

One concrete execution order is one realization of a broader partial-order/deadline specification.

### Result

**CE-124 — Temporal type/specification and execution episode are distinct.**

---

# 126. Timing resource constraints interact with temporal structure

Two individually valid events may compete for one executor/channel and become unschedulable together.

### Result

**CE-125 — Temporal composition can depend jointly on relation structure and finite resource availability.**

---

# 127. Temporal composition can be active-information-seeking

A system can delay, speed up or sample at strategic times to disambiguate dynamics.

### Result

**CE-126 — Temporal sensing/action policy can alter the composition evidence itself, connecting MF2 active perception to MF4 temporal organization.**

---

# 128. Waiting is an action in temporal composition

Choosing not to act yet can preserve synchronization, gather evidence or satisfy sequencing constraints.

### Result

**CE-127 — Temporal control includes timing of inaction/waiting, not merely event execution.**

---

# 129. Temporal resource budgeting

Systems have finite processing/action windows.

### Result

**CE-128 — Time itself can function as a consumable/opportunity resource when delayed processing removes future options or violates constraints.**

---

# 130. But physical time is not literally consumed

What is consumed/lost is opportunity/slack/deadline margin.

### Result

**CE-129 — `time resource` should be operationalized as slack/opportunity windows rather than metaphysically treating time as a material stock.**

---

# 131. Slack is distinct from deadline

Slack depends on remaining work and available time before deadline.

### Result

**CE-130 — Deadline, remaining execution demand and slack are separate temporal-control variables.**

---

# 132. Temporal optionality decreases irreversibly in many tasks

As deadline approaches, some possible actions become infeasible.

### Result

**CE-131 — Temporal composition can constrain future option sets even when current state content is unchanged.**

---

# 133. Temporal redundancy can improve robustness

Repeated cues, retransmission, multiple synchronization markers can tolerate dropouts.

### Result

**CE-132 — Temporal redundancy can be a robustness resource rather than inefficiency.**

---

# 134. Temporal redundancy can also create ambiguity/load

Excess repetition can crowd channels or confuse event identity.

### Result

**CE-133 — Temporal redundancy value is task/failure-mode dependent.**

---

# 135. Temporal segmentation can depend on rhythm

Regular patterns create expectations that make deviations/boundaries salient.

### Result

**CE-134 — Rhythm/expectancy can help individuate temporal units, linking MF4-E back to MF4-B.**

---

# 136. Temporal hierarchy can constrain rhythm interpretation

A local pattern can function differently under different higher-level meters/phrasings.

### Result

**CE-135 — Temporal role is cross-scale/context dependent, linking MF4-E to MF4-D.**

---

# 137. Temporal relations can define module coupling

Near-decomposability depends partly on faster/stronger within-module than between-module interactions.

### Result

**CE-136 — Timescale is composition-defining for some modular organizations, linking MF4-E to MF4-D.**

---

# 138. Temporal composition can be representationally specified without physical periodicity

A score/schema can encode meter/rhythm/deadlines that no current physical process instantiates.

### Result

**CE-137 — Temporal representation and active temporal dynamics are distinct.**

---

# 139. Temporal composition can be perceived without explicit symbolic timing

Humans can hear rhythm without timestamps/notation.

### Result

**CE-138 — Explicit temporal symbols are not required for temporal perceptual composition.**

---

# 140. Temporal composition can be computational without conscious timing perception

A protocol/scheduler can enforce timeouts/deadlines automatically.

### Result

**CE-139 — Conscious temporal awareness is not constitutive of temporal composition.**

---

# 141. Temporal relation provenance

Timing may come from:

- physical clock;
- sensor timestamp;
- inferred event model;
- score/specification;
- scheduler contract;
- narrative convention;
- perceptual calibration.

### Result

**CE-140 — Temporal relation provenance is distinct from relation content and must be preserved for strong attribution.**

---

# 142. Temporal evidence can be delayed

A sensor/log record about event E arrives after E.

### Result

**CE-141 — Observation/report time and target event time are distinct.**

---

# 143. Processing time ≠ Event time

A model may infer an earlier event at a later processing timestamp.

### Result

**CE-142 — Media/perception systems require at least target-time vs observation/processing-time discipline.**

---

# 144. Publication/transmission time can be another layer

A recording may be created, edited and published at different times from represented events.

### Result

**CE-143 — Temporal provenance can contain multiple time axes: event, capture, processing/edit, storage, transmission and consumption.**

---

# 145. Multiple time axes can conflict

A live feed can have old content; a delayed broadcast can appear current without metadata.

### Result

**CE-144 — `When is this?` is under-specified unless the temporal axis is named.**

---

# 146. Timestamp provenance affects trust

Clock source, synchronization and editing history matter when timestamps support evidence claims.

### Result

**CE-145 — Temporal provenance/evidence quality is distinct from temporal composition itself but critical for attribution.**

---

# 147. Temporal whole identity is profile-based

Possible invariants:

- participant/event identity;
- order;
- interval ratios;
- meter;
- phase relations;
- causal dependencies;
- goal;
- narrative relation;
- deadline class.

### Result

**CE-146 — No universal temporal identity criterion exists; temporal-whole persistence must declare invariants.**

---

# 148. Temporal composition failure taxonomy

MF4-E proposes:

## Missing event

Required constituent absent.

## Spurious event

Extraneous event inserted.

## Misordering

Correct constituents, wrong ordinal relation.

## Timing displacement

Event too early/late without order change.

## Duration distortion

Event length incorrect.

## Gap distortion

Inter-event silence/gap wrong.

## Tempo/rate error

Global rate outside intended profile.

## Local time warp

Relative timing altered non-uniformly.

## Phase error

Wrong relative phase.

## Drift

Phase/clock relation changes systematically.

## Jitter

Short-timescale timing variability.

## Synchronization failure

Coordination outside allowed tolerance.

## Deadline miss

Correct operation/output delivered too late.

## Premature execution

Event occurs before allowed/ready time.

## Temporal binding error

Distinct events falsely fused or common event split because timing relation misinterpreted.

## Boundary timing error

Event/segment boundary too early/late.

## Interruption identity error

Pause treated as termination or new event treated as resumption.

## Recurrence identity error

Repetition confused with continuation or vice versa.

## Temporal aliasing

Sampling/coarse-graining collapses relevant timing distinctions.

## Cross-clock/order error

Unsynchronized clocks create false event ordering.

## Presentation/causal-order confusion

Display order mistaken for represented causal chronology.

### Result

**CE-147 — Temporal failure is a typed family, not one latency/error scalar.**

---

# 149. Temporal evidence profile

Possible dimensions:

- clock/timestamp provenance;
- onset/offset precision;
- order confidence;
- interval uncertainty;
- phase/synchrony confidence;
- boundary confidence;
- source/common-cause evidence;
- specification vs realization;
- deadline contract;
- cross-modal calibration/history;
- resampling/edit history.

### Result

**CE-148 — Temporal composition claims require evidence matched to the claimed timing relation, not generic timestamp presence.**

---

# 150. Provisional TemporalCompositionEpisode

```text
TemporalCompositionEpisode = <
  E      : event/state/interval constituents,
  Id     : temporal-whole identity profile,
  Ord    : order/partial-order relations,
  Int    : intervals/durations/gaps,
  Bound  : temporal boundaries/grouping,
  Rate   : tempo/rate/period profile,
  Rhythm : rhythm/accent/meter profile,
  Phase  : phase/synchronization relations,
  Cont   : continuity/interruption/resumption,
  Recur  : repetition/recurrence/loop structure,
  Hier   : temporal hierarchy/granularity,
  Causal : causal/dependency temporal relations,
  Pres   : presentation/narrative order,
  RT     : deadlines/latency/slack/resource timing,
  Frame  : clocks/reference frames/time axes,
  Hist   : history/adaptation/expectancy,
  Spec   : standing specification vs active realization,
  Unc    : timing/relation uncertainty,
  Prov   : temporal provenance,
  Eval   : coherence/failure/tolerance profile,
  Scope  : task/consumer/granularity
>
```

---

# 151. Provisional SynchronizationProfile

```text
SynchronizationProfile = <
  Processes/Events,
  ReferenceFrame/Clock,
  TargetRelation,
  PhaseOffset,
  Frequency/RateRelation,
  ToleranceWindow,
  Jitter,
  Drift,
  Adaptation/Recalibration,
  Feedback/ErrorCorrection,
  CommonSourceHypothesis,
  Lifetime,
  Evaluation
>
```

---

# 152. Provisional RhythmProfile

```text
RhythmProfile = <
  OnsetPattern,
  IntervalPattern,
  DurationPattern,
  AccentPattern,
  Grouping,
  Beat/Pulse,
  Meter,
  Tempo,
  Phase,
  Hierarchy,
  Expectancy,
  RetimingInvariants,
  Scope
>
```

---

# 153. Provisional RealTimeProfile

```text
RealTimeProfile = <
  ReleaseTimes,
  ExecutionDemand,
  Dependencies,
  Periods,
  Deadlines,
  Priorities/Policy,
  Latency,
  Slack,
  ResourceConstraints,
  Hard/SoftUtility,
  CompletionEvidence,
  FailureSemantics
>
```

---

# 154. Provisional temporal composition profiles

## T0 — Ordered series

Selected events with an ordinal/partial order.

## T1 — Metric interval composition

Durations/gaps/relative timing are whole-relevant.

## T2 — Rhythmic/metrical composition

Structured recurrence/accent/beat/meter organizes temporal expectancy.

## T3 — Synchronized/phase-coordinated composition

Multiple processes/events maintain typed timing relation under tolerance.

## T4 — Stateful event/process composition

Continuity, interruption, resumption and prediction define temporal-whole identity.

## T5 — Hierarchical/recursive temporal composition

Events compose into nested/recurrent multi-timescale wholes.

## T6 — Real-time/deadline composition

Temporal validity/utility depends on completion windows/resource scheduling.

## T7 — Multi-axis representational/narrative composition

Presentation time, represented event time, causal order and narrative order are explicitly distinguished/coordinated.

Profiles overlap and are not a mandatory scalar ladder.

---

# 155. Provisional non-collapse stack

```text
Timestamp
 ≠ Temporal Relation
 ≠ Succession
 ≠ Sequence
 ≠ Temporal Composition
```

```text
Order
 ≠ Timing
 ≠ Duration
 ≠ Interval
 ≠ Rate
```

```text
Rhythm
 ≠ Periodicity
 ≠ Beat
 ≠ Meter
 ≠ Tempo
```

```text
Synchrony
 ≠ Exact Simultaneity
 ≠ Entrainment
 ≠ Binding
```

```text
Pause
 ≠ Termination
 ≠ Resumption
 ≠ Repetition
```

```text
Presentation Order
 ≠ Narrative Order
 ≠ Represented Chronology
 ≠ Causal Order
 ≠ Scheduling Order
```

```text
Duration
 ≠ Latency
 ≠ Period
 ≠ Deadline
 ≠ Slack
```

---

# 156. Provisional axioms CE-01→CE-148 — compressed core

**CE-01–13** Timestamp, succession, sequence, temporal whole, onset/offset/duration/gap/order/metric timing are distinct.

**CE-14–26** Rhythm, periodicity, beat, meter, tempo and accent are typed/non-equivalent; metrical organization can be inferred and can change encoding without being universal rhythm ontology.

**CE-27–41** Temporal expectancy, entrainment, phase, synchrony, recalibration and multisensory binding are distinct; subjective simultaneity is adaptive/history/source dependent and not exact zero-lag identity.

**CE-42–56** Temporal-whole continuity can bridge gaps; interruption, termination, resumption, repetition, recurrence, loop, hierarchy, chunking and temporal attention must remain distinct.

**CE-57–63** Presentation, represented chronology, causal/narrative order, cuts/transitions and pacing are separate temporal composition layers.

**CE-64–82** Real-time validity introduces deadline/latency/slack/resource constraints; temporal correctness differs from value correctness; synchronization trades coherence against waiting/flexibility.

**CE-83–96** Active sensorimotor synchronization uses feedback/prediction; phase/period correction differ; expected absence/silence, multiple rhythms and ambiguous temporal grouping are first-class.

**CE-97–105** Temporal reference clocks, evidence uncertainty, resampling/aliasing and retiming equivalence require explicit frames/invariants; one transformation can preserve rhythm while violating deadlines.

**CE-106–120** Reversal, standing specification, expressive deviation, asymmetric tolerance, local/global coherence, prefix/suffix reinterpretation and physical-vs-represented history are distinct.

**CE-121–133** Temporal/causal/logical/presentation/execution precedence are typed; partial orders admit multiple schedules; finite resources, waiting, slack/optionality and temporal redundancy matter.

**CE-134–148** Rhythm/segmentation/hierarchy/timescale interact; temporal composition can be standing, perceptual, computational and multi-axis with explicit provenance/evidence/failure profiles.

---

# 157. Claims rejected by MF4-E

Reject as universal foundational claims:

- time is exhausted by timestamps;
- succession equals sequence or temporal composition;
- order determines timing;
- one onset timestamp fully characterizes an event;
- duration, gap, period and inter-onset interval are interchangeable;
- timestamp sorting captures interval temporal structure;
- same event order implies same temporal whole;
- rhythm equals periodicity;
- rhythm equals meter, beat or tempo;
- every rhythm has one internal clock/metric grid;
- physical periodicity uniquely determines temporal expectancy;
- entrainment equals synchrony;
- same rate implies same phase;
- synchrony means exact zero lag;
- jitter, offset and drift are equivalent;
- subjective audiovisual simultaneity is fixed and history-independent;
- temporal coincidence proves common cause;
- common-source features must arrive simultaneously at the observer;
- one universal temporal binding window exists;
- binding tolerance equals temporal discrimination threshold;
- any gap terminates a temporal whole;
- resumption equals repetition;
- recurrence requires periodicity;
- loop equals repeated content;
- temporal hierarchy is always perfectly nested;
- chunking proves natural hierarchy;
- attention is constitutive of temporal structure;
- presentation order equals causal/chronological/narrative order;
- film/edit cuts equal represented event boundaries;
- pace equals tempo;
- deadline equals duration/period;
- correct value delivered late is always temporally correct;
- all deadlines are binary hard constraints;
- scheduling order equals causal order;
- priority equals realized temporal precedence;
- temporal composition requires a total order;
- concurrency equals simultaneity;
- more synchronization is always better;
- synchronization is a static relation only;
- phase correction equals period correction;
- expected event absence cannot be a constituent;
- silence always means no event;
- one global beat is required for temporal composition;
- one unique temporal parse is always available;
- one global clock/reference is sufficient;
- timestamp equality proves simultaneity;
- resampling preserves all temporal structure;
- uniform tempo scaling always preserves whole identity/function;
- time reversal always preserves or always destroys temporal identity;
- specification and realized timing are identical;
- deviation from nominal timing is always error;
- temporal tolerance is symmetric/universal;
- local temporal correctness guarantees global schedulability/coherence;
- early prefix uniquely determines temporal whole meaning;
- every precedence relation means physical temporal precedence;
- one temporal specification has one valid schedule;
- time is a material resource rather than opportunity/slack structure;
- all temporal redundancy is waste;
- one latency/error scalar captures temporal composition quality.

---

# 158. Primary/original literature anchors

- Allen, J. F. (1983), `Maintaining Knowledge About Temporal Intervals`, *Communications of the ACM* 26(11), 832–843. DOI: 10.1145/182.358434. Interval relation system and constraint propagation; retained as evidence that temporal organization is richer than point timestamps.
- Povel, D.-J. & Essens, P. (1985), `Perception of Temporal Patterns`, *Music Perception* 2(4), 411–440. DOI: 10.2307/40285311. Studies reproduction/perception of onset-interval patterns and proposes flexible internal clock/metrical organization driven by accent structure.
- Essens, P. J. & Povel, D. J. (1985), `Metrical and nonmetrical representations of temporal patterns`, *Perception & Psychophysics* 37(1), 1–7. DOI: 10.3758/BF03207132. Distinguishes patterns that support metrical frameworks from nonmetrical patterns.
- Jones, M. R. & Boltz, M. (1989), `Dynamic attending and responses to time`, *Psychological Review* 96(3), 459–491. DOI: 10.1037/0033-295X.96.3.459. Future-oriented attending and temporal expectancy for coherent event structures.
- Large, E. W. & Jones, M. R. (1999), `The dynamics of attending: How people track time-varying events`, *Psychological Review* 106(1), 119–159. DOI: 10.1037/0033-295X.106.1.119. Oscillatory/entrainment model of attentional tracking under changing event rates; retained as a mechanism/model for temporal expectancy, not universal temporal ontology.
- Fujisaki, W., Shimojo, S., Kashino, M. & Nishida, S. (2004), `Recalibration of audiovisual simultaneity`, *Nature Neuroscience* 7(7), 773–778. DOI: 10.1038/nn1268. Fixed audiovisual lag exposure shifts subjective simultaneity, demonstrating adaptive/history-dependent cross-modal timing calibration.
- Vroomen, J., Keetels, M., de Gelder, B. & Bertelson, P. (2004), `Recalibration of temporal order perception by exposure to audio-visual asynchrony`, *Cognitive Brain Research* 22(1), 32–35. DOI: 10.1016/j.cogbrainres.2004.07.003. Temporal-order/simultaneity judgments shift toward exposure lag, strengthening the recalibration falsifier.
- Engbert, R., Krampe, R. T., Kurths, J. & Kliegl, R. (2002), `Synchronizing movements with the metronome: nonlinear error correction and unstable periodic orbits`, *Brain and Cognition* 48(1), 107–116. DOI: 10.1006/brcg.2001.1307. Empirical/model evidence that active synchronization error correction need not be linear.
- Liu, C. L. & Layland, J. W. (1973), `Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment`, *Journal of the ACM* 20(1), 46–61. DOI: 10.1145/321738.321743. Hard-real-time task scheduling under deadlines/periodic requests; canonical case where temporal correctness depends on deadline constraints and scheduling policy.

---

# 159. Deep reconstruction

The naive temporal model is:

```text
Events
  ↓ sort by timestamp
Sequence
  ↓
Temporal whole
```

MF4-E replaces it with:

```text
Events / states / intervals
        │
        ├─ onset / offset / duration / gaps
        ├─ order / partial order / interval relations
        ├─ rhythm / accent / beat / meter
        ├─ rate / tempo / phase
        ├─ synchronization / tolerance / recalibration
        ├─ continuity / interruption / resumption
        ├─ recurrence / repetition / loops
        ├─ deadlines / latency / slack / resources
        ├─ event hierarchy / granularity
        ├─ causal / dependency order
        ├─ presentation / narrative order
        ├─ clock / temporal provenance
        └─ uncertainty / expectation / history
        │
        ▼
Candidate temporal whole(s)
        │
        ├─ can persist through gaps
        ├─ can admit several valid schedules/parses
        ├─ can be retimed under selected invariants
        ├─ can fail deadline while preserving logical content
        ├─ can bind asynchronous modalities after calibration
        └─ can be retrospectively reinterpreted
```

Temporal composition is therefore not `time coordinates` but **structured organization across time**.

---

# 160. Deepest MF4-E conclusion

The strongest surviving candidate is:

> **A temporal composition is a scope-relative organization of events, states, intervals or processes whose ordering, durations, boundaries, relative timing, recurrence, phase/synchronization, continuity or deadline relations are constitutive or operationally relevant to a temporal whole, potentially across multiple granularities and reference clocks.**

And:

> **Temporal identity/equivalence is relation-profile dependent: preserving event order is weaker than preserving rhythm, meter, phase, causal chronology, narrative structure or real-time validity.**

Compactly:

`TemporalComposition = Events/Intervals + Typed Temporal Relations/Constraints + Temporal Boundaries/State + Whole/Scope`.

---

# 161. Cross-round MF4 state after E

```text
MF4-A — Whole / composition criterion
          ↕
MF4-B — Units / boundaries / segmentation
          ↕
MF4-C — Relations / binding / dependency / constraint
          ↕
MF4-D — Hierarchy / modularity / scale / coarse-graining
          ↕
MF4-E — Temporal ordering / rhythm / synchrony / continuity / deadline
```

MF4 is increasingly a multi-scale reciprocal constraint ontology rather than atom concatenation.

---

# 162. Why MF4 is still unfrozen

Temporal structure is only one major composition dimension.

Still required:

- spatial layout/topology;
- multimodal/cross-medium composition;
- scene/montage/narrative organization;
- interaction/action/feedback;
- global coherence/Gestalt;
- final cross-domain falsification/reconstruction.

---

# 163. MF4-F handoff — Spatial Composition, Layout, Geometry & Topology

MF4-F should ask:

- spatial adjacency vs part-of/ownership;
- metric distance vs topology;
- containment;
- overlap;
- occlusion;
- orientation;
- alignment;
- symmetry;
- proximity;
- enclosure;
- whitespace/negative space;
- figure/ground;
- visual hierarchy/layout;
- coordinate/reference frames;
- responsive/reflowing layout;
- topology-preserving deformation;
- viewpoint/projective transformation;
- map/diagram spatial composition;
- screen/page/scene composition;
- continuous fields vs discrete objects;
- spatial attention/read order;
- layout semantics;
- spatial invariance/equivariance;
- spatial aliasing/occlusion;
- cross-scale geometry;
- spatial composition failure taxonomy.

Core question:

> **When do spatial relations merely locate parts, and when do layout/topology/geometry relations constitute the identity, function or content of a whole?**

**Next: MF4-F — Spatial Composition, Layout, Geometry & Topology.**

---

# Final MF4-E handoff

MF4-E rejects the assumption that time is just another scalar coordinate attached to already-defined parts.

Temporal composition has independent structure:

`succession ≠ sequence ≠ temporal whole`;

`order ≠ timing`;

`rhythm ≠ periodicity ≠ beat ≠ meter ≠ tempo`;

`synchrony ≠ exact simultaneity ≠ binding`;

`presentation order ≠ causal order ≠ narrative order`;

`duration ≠ latency ≠ deadline ≠ slack`.

Temporal wholes can persist through gaps, admit partial orders, be retimed under selected invariants, recalibrate cross-modal synchrony, depend on deadlines/resources and support prospective/retrospective organization.

Composition Foundations remain UNFROZEN.

**Next: MF4-F — Spatial Composition, Layout, Geometry & Topology.**
