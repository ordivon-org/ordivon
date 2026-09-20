# Ordivon Media Foundations — MF6-E Computational, Media, Sequencing & Synchronization Time

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 36 at start  
**Input:** MF0–MF5 frozen; MF6-A→D complete/provisional.  
**Status:** MF6-E complete and PROVISIONAL. Time Foundations remain UNFROZEN.  
**Next:** MF6-F — Time Falsification & Reconstruction.

---

# 0. Purpose

MF6-E attacks the computational/media domain where `time` is routinely overloaded into one scalar field despite systems actually carrying several non-equivalent temporal roles.

Central failures:

```text
Sequence = Time
Timestamp = Event Time
Timestamp = Truth
Packet Order = Sample/Presentation Order
Frame Index = Presentation Time
Decode Order = Presentation Order
Sample Index = Wall Time
Media Timeline = Source/Capture Timeline
Playback Position = Physical Current Time
Playback Rate = Time Rate
Logical Clock = Physical Clock
Event Time = Processing Time
Watermark = Event Time
Late Data = Physically Late Event
Wall Clock = Monotonic Duration Clock
Low Latency = Low Jitter = Good Synchronization
Same Media Timestamp = Same Physical Event Time
Same RTP Timestamp Across Streams = Synchronized
Buffering = Synchronization Error
Live Edge = Physical Now
Simulation Time = Wall Clock Time
Render Time = Simulation Time
Pause = Time Stops Physically
Rewind = Past Physical State Becomes Past Reality
```

The target is a typed temporal model that can describe distributed systems, real-time transport, audio/video, playback/editing and simulation without laundering implementation order into target chronology.

---

# 1. Computational sequence is not Time

An integer sequence can encode identity/order without temporal measure.

### TE-001
**SequenceNumber ≠ Timestamp.**

### TE-002
`i < j` can mean packet order, log order, version order, dependency order or temporal order; semantics must be grounded separately.

### TE-003
A monotonically increasing identifier does not establish equal temporal spacing or physical chronology.

---

# 2. RTP provides a decisive sequence-versus-time hard case

RFC 3550 gives each RTP packet both a sequence number and a timestamp. Sequence numbers increment per transmitted packet and support loss/order reconstruction; RTP timestamps correspond to media sampling/presentation timing.

### TE-004
**RTPSequenceNumber ≠ RTPTimestamp by protocol design.**

### TE-005
Packet transmission order can remain monotonic while media timestamps are non-monotonic when media data is transmitted out of sampling/presentation order.

### TE-006
Therefore `TransmissionOrder ≠ MediaTemporalOrder`.

---

# 3. One media instant may occupy several packets

RFC 3550 permits consecutive packets to share one RTP timestamp, e.g. packets belonging to one video frame.

### TE-007
**PacketCount/PacketOrder ≠ MediaEventCount/Timing.**

### TE-008
Multiple transport units can represent one media temporal unit.

### TE-009
Conversely one packet may contain multiple audio samples spanning a nonzero temporal interval.

---

# 4. RTP timestamp is a domain clock, not wall time by identity

RTP timestamps use a payload-format-specific clock rate and random initial offset.

### TE-010
**RTPTimestamp ≠ WallClockTimestamp.**

### TE-011
Numeric RTP timestamp comparison only has temporal meaning under the stream's declared clock rate/origin semantics.

### TE-012
Timestamp value magnitude is not absolute date/time.

---

# 5. Different RTP streams are not directly timestamp-comparable

RFC 3550 explicitly notes that different media streams usually have independent random offsets and potentially different timestamp rates.

### TE-013
**RTPTimestampAudio ≠ RTPTimestampVideo in a directly comparable coordinate system by default.**

### TE-014
Inter-media synchronization requires a relation from each stream's RTP clock to a shared reference clock, carried via RTCP sender reports or equivalent grounding.

### TE-015
`SameNumericRTPTimestamp ≠ SameSamplingTimeAcrossStreams`.

---

# 6. Synchronization requires clock correspondence, not equality of counters

RTCP sender reports pair an RTP timestamp with an NTP/reference-clock timestamp representing the same reference instant.

### TE-016
**ClockMapping/Correspondence is additional structure beyond per-stream timestamps.**

### TE-017
A/V synchronization is a relation among media clocks/reference mappings, not a property of equal raw timestamp integers.

### TE-018
Different sample rates/timebases can remain synchronized through a calibrated mapping.

---

# 7. Sampling time is not send time or receive time

RFC 3550 intentionally bases RTP timestamps on the sampling instant rather than packet transmission time, insulating media synchronization from variable encoding/transmission delay.

### TE-019
**SampleTime ≠ PacketSendTime ≠ PacketReceiveTime.**

### TE-020
Transport latency can change without changing source sampling timestamps.

### TE-021
Reception order/timing is evidence about delivery, not a replacement source chronology.

---

# 8. Stored media can use a virtual presentation timeline

RFC 3550 allows stored media RTP timing to be derived from a virtual presentation timeline; actual receiver presentation can occur later.

### TE-022
**MediaPresentationTimeline ≠ WallClockArrivalTimeline.**

### TE-023
A stored program can replay the same media temporal relations on many different wall-clock occasions.

### TE-024
Presentation-time standing can therefore be genuine without identifying with original capture wall time.

---

# 9. Media Source Extensions formalizes decode versus presentation time

MSE defines coded frames with presentation timestamp (PTS), decode timestamp (DTS) and duration.

### TE-025
**PTS ≠ DTS ≠ FrameDuration.**

### TE-026
PTS says when a coded frame belongs/rendering starts on the presentation timeline; DTS constrains when decoding must occur given dependencies.

### TE-027
`DecodeOrder ≠ PresentationOrder` whenever codec dependencies permit/require reordering.

---

# 10. Decode temporal standing is operational, not target chronology

A frame can need decoding before another frame that is displayed earlier/later because of inter-frame dependencies.

### TE-028
**DecodeTime is a computational dependency deadline, not source-world event time.**

### TE-029
Codec dependency order can differ from narrative/presentation order without contradiction.

### TE-030
Computational temporal standing can be genuine at the decoder level while not transferring to represented target chronology.

---

# 11. Presentation timestamp is a media-coordinate claim

MSE/WebCodecs treat timestamps as presentation coordinates.

### TE-031
**PresentationTimestamp ≠ PhysicalEventTimestamp by identity.**

### TE-032
PTS becomes a claim about source/capture chronology only when the container/production pipeline grounds that correspondence.

### TE-033
Edited, looped, slowed or reordered media can deliberately break one-to-one source-time correspondence while retaining valid presentation timestamps.

---

# 12. Frame index is not presentation time

With variable frame duration, dropped/duplicated frames, edit gaps or VFR content, successive frame indices need not correspond to equal temporal intervals.

### TE-034
**FrameIndex ≠ PresentationTimestamp.**

### TE-035
`FrameCount / nominalFPS` is only valid under declared constant-rate assumptions.

### TE-036
Frame identity/order can remain well-defined when timing is irregular.

---

# 13. WebCodecs reinforces timestamp/duration separation

WebCodecs exposes `VideoFrame.timestamp` as presentation timestamp and `duration` separately.

### TE-037
**FrameTimestamp ≠ FrameDuration.**

### TE-038
A sequence of frames can carry explicit per-frame temporal extent rather than infer extent from index spacing.

### TE-039
Constant-rate timestamp generation is a convenience case, not universal media ontology.

---

# 14. Presentation interval is not frame identity

A coded frame can have presentation interval `[PTS, PTS+duration)`.

### TE-040
**FrameIdentity ≠ PresentationInterval.**

### TE-041
Different frames can have different durations; intervals can touch or potentially overlap depending media semantics/editing rules.

### TE-042
Temporal occupancy on a presentation timeline is a relation/profile of a media unit.

---

# 15. Media timeline can be shifted/rebased

MSE supports timestamp offsets and sequence append modes that remap media timestamps into a presentation timeline.

### TE-043
**SourceTimestamp ≠ EffectivePresentationTimestamp after temporal transform.**

### TE-044
Changing timestamp offset is a presentation/representation transformation, not physical movement of original source events.

### TE-045
Temporal remapping needs provenance just as MF5-C coordinate transformations do spatially.

---

# 16. Editing timeline is not source chronology

Cuts, inserts, speed changes and reordering map source temporal intervals to new presentation intervals.

### TE-046
**EditTimeline ≠ CaptureTimeline.**

### TE-047
A media artifact can represent an event chronology while presenting fragments in a different sequence/order.

### TE-048
Presentation order, narrative order and represented target chronology are separate relations.

---

# 17. Playback position is a coordinate on a media timeline

The HTML media model defines current playback position as a time on the media timeline.

### TE-049
**PlaybackPosition ≠ WallClockTime.**

### TE-050
Seeking can change playback position discontinuously without rewinding physical time.

### TE-051
A paused media timeline can stop advancing while wall/monotonic clocks continue.

---

# 18. Playback rate is a timeline transformation

HTML `playbackRate` changes the speed at which the media resource advances relative to ordinary playback.

### TE-052
**PlaybackRate ≠ PhysicalTimeRate.**

### TE-053
Slow motion/fast forward transforms presentation-time relation to wall time while preserving a declared media timeline.

### TE-054
A negative/reverse playback implementation, where supported, would reverse presentation traversal without reversing source-world causality.

---

# 19. Pause distinguishes timeline progress from elapsed wall time

A player may remain paused for one hour at one presentation coordinate.

### TE-055
**MediaTimelineElapsed ≠ WallClockElapsed.**

### TE-056
`Pause` is a control over timeline advancement, not suspension of physical time.

### TE-057
This is the clearest consumer-level hard case for `simulation/media time ≠ wall time`.

---

# 20. Web Audio has its own temporal coordinate system

Web Audio defines `currentTime` from processed sample frames; its zero corresponds to the first processed block and it may not be synchronized with other system clocks. Offline audio need not approximate real time at all.

### TE-058
**AudioContextTime ≠ WallClockTime.**

### TE-059
An audio graph can have internally coherent sample/render time without external clock identity.

### TE-060
Offline rendering proves computational media time can progress independently of real-time pace.

---

# 21. Sample index is temporal only through sample-rate standing

For fixed-rate audio, a sample index can map to stream time through sample rate and origin.

### TE-061
**SampleIndex ≠ Time without SampleRate + Origin/ClockStanding.**

### TE-062
Changing sample rate changes the index→duration mapping without changing sample index identity.

### TE-063
Resampling creates a new sampled representation/timebase, not a change in original source event time.

---

# 22. Audio clock and video clock may be distinct

Independent capture/render devices can have different oscillator rates/drift.

### TE-064
**AudioClock ≠ VideoClock by default.**

### TE-065
A/V sync requires relation/discipline between media clocks or a common master/reference timeline.

### TE-066
Long-run A/V drift can occur even when initial offset is zero.

This mirrors MF6-B:

```text
Synchronization ≠ Syntonization
```

---

# 23. A/V offset and A/V drift are different failures

### TE-067
**AVOffset ≠ AVRateMismatch/Drift.**

### TE-068
A fixed lip-sync offset can coexist with matched rates; perfect initial alignment can later diverge under rate mismatch.

### TE-069
Synchronization quality is a trajectory/profile, not one instantaneous offset.

---

# 24. Output latency is not media timestamp

Web Audio distinguishes context/render time from output latency—the estimated interval between requesting output and actual device production.

### TE-070
**PresentationScheduleTime ≠ PhysicalOutputTime.**

### TE-071
Device/output latency is a transformation between computational timeline and emitted physical signal.

### TE-072
Accurate A/V or sensorimotor sync may require modeling this latency explicitly.

---

# 25. Latency is not jitter

Latency is elapsed delay along a path/process; jitter concerns variation in delay/interarrival timing.

RFC 3550 computes interarrival jitter from variation in relative transit time.

### TE-073
**Latency ≠ Jitter.**

### TE-074
A stream can have high but stable latency (low jitter), or low mean latency with high jitter.

### TE-075
Neither alone equals synchronization error.

---

# 26. Jitter is not packet reordering or loss

### TE-076
**Jitter ≠ PacketLoss ≠ Reordering.**

### TE-077
They can interact operationally but are distinct transport profiles.

### TE-078
One packet sequence/arrival trace can support separate loss, reorder, latency and jitter claims.

---

# 27. Buffering trades latency for timing regularity

A jitter buffer can delay presentation to absorb arrival variation.

### TE-079
**LowerPlaybackJitter can require HigherLatency.**

### TE-080
Buffer depth is therefore a control/resource variable, not simply `wasted time`.

### TE-081
Synchronization/continuity optimization is multi-objective.

---

# 28. Low latency does not imply synchronization

Two streams can each arrive quickly but with a large relative offset.

### TE-082
**LowLatency ≠ AVSynchronization.**

### TE-083
Likewise synchronized presentation can intentionally include substantial absolute latency.

### TE-084
Absolute delay and relative alignment are different temporal objectives.

---

# 29. HLS program date-time is an explicit wall-clock mapping

RFC 8216 `EXT-X-PROGRAM-DATE-TIME` associates the first sample of a media segment with an absolute date/time.

### TE-085
**ProgramDateTime is an added correspondence from media timeline to civil/wall-clock time.**

### TE-086
Its existence demonstrates that ordinary segment/media timing is not automatically absolute wall-clock time.

### TE-087
A wall-clock anchor enables live-origin/display semantics but remains a representation/reference claim with accuracy provenance.

---

# 30. Live edge is not metaphysical `now`

A live stream's newest available/presentable point is shaped by capture, encoding, packaging, transport, buffering and player policy.

### TE-088
**LiveEdge ≠ PhysicalNow.**

### TE-089
Live-edge latency is a pipeline relation between source/reference event time and currently available/presented media time.

### TE-090
Two viewers can have different live edges for the same source.

---

# 31. Program origination time is not viewer presentation time

RFC 8216 permits display of program origination time while clients load/buffer media before presentation.

### TE-091
**Source/ProgramTime ≠ ClientPresentationWallTime.**

### TE-092
Live streaming can preserve source chronological anchoring while introducing transport/playout delay.

---

# 32. Event time and processing time are separate computational domains

Apache Beam distinguishes event time (timestamp associated with the event) from processing time (clock time at which the pipeline processes the element).

### TE-093
**EventTime ≠ ProcessingTime.**

### TE-094
Elements need not be processed in event-time order.

### TE-095
Out-of-order processing does not rewrite target event chronology.

---

# 33. Ingestion/observation/commit times are additional roles

A real system can assign:

```text
source_event_time
observation_time
ingestion_time
processing_time
commit_time
publication_time
presentation_time
```

### TE-096
**One generic timestamp field is insufficient when these roles matter.**

### TE-097
Ordering by database/queue insertion time is not target-event order by default.

### TE-098
Temporal provenance must name the role being timestamped.

---

# 34. A timestamp is data plus semantics, not truth

Beam allows element timestamps to be assigned by sources or manually from event fields.

### TE-099
**ElementTimestamp ≠ VerifiedOccurrenceTime by identity.**

### TE-100
Timestamp standing depends on source semantics/authority and can be wrong, delayed, synthetic or absent.

### TE-101
A pipeline can process temporal claims without independently validating their physical truth.

---

# 35. Watermark is not event time

Beam defines a watermark as an estimate/lower-bound-like progress signal about event timestamps expected to arrive.

### TE-102
**Watermark ≠ EventTime.**

### TE-103
Watermark is a computational completeness/progress claim about the stream, not the time of one target event.

### TE-104
Heuristic watermarks can be wrong; `late` data may arrive after a watermark estimate.

---

# 36. Late data is relative to computational progress semantics

### TE-105
**LateData ≠ EventOccurredLate.**

An event can have occurred long ago on time but be delivered/processed late.

### TE-106
`Late` must be typed relative to watermark/window/processing policy.

### TE-107
Dropping late data is a system policy, not an ontological deletion of the event.

---

# 37. Event-time window is not physical container

Beam windows group elements according to timestamps/windowing functions.

### TE-108
**WindowMembership is a computational grouping relation over timestamp claims.**

### TE-109
Changing window size/alignment changes aggregation semantics without changing target event times.

### TE-110
A session window can be inference/grouping structure rather than a physically bounded event object.

---

# 38. Trigger time is not window/event time

Beam can trigger output based on event-time watermarks, processing time, counts or combinations.

### TE-111
**TriggerTime/EmissionTime ≠ EventTime.**

### TE-112
The same event-time window can emit early, on-time and late panes at different processing times.

### TE-113
Result publication chronology is distinct from represented event chronology.

---

# 39. Logical time remains distinct from event/physical time

Lamport/vector-style logical clocks encode causal/order information, not SI duration.

### TE-114
**LogicalClock ≠ EventTimestamp ≠ PhysicalClock.**

### TE-115
A logical-clock step can occur after arbitrary wall-clock duration.

### TE-116
Causal order can be useful when physical timestamp order is unavailable/untrusted.

---

# 40. Version/order numbers are not logical clocks automatically

### TE-117
**VersionNumber ≠ LogicalClock by naming alone.**

A counter becomes logical temporal/order standing only if update/merge rules operationally encode causality/version precedence.

### TE-118
Repository revision order, database sequence ID and media frame index each need separate standing semantics.

---

# 41. Wall-clock and monotonic clocks serve different roles

POSIX distinguishes realtime/epoch-oriented clocks from monotonic clocks whose absolute origin may be arbitrary and which are intended for interval measurement without wall-clock setting jumps.

### TE-119
**WallClock/Realtime ≠ MonotonicClock.**

### TE-120
Civil/reference clock correction can alter wall-clock coordinates without invalidating a monotonic elapsed-duration measurement.

### TE-121
Duration/deadline code should not infer monotonicity from a civil timestamp source by default.

---

# 42. Monotonic does not mean synchronized to UTC

### TE-122
**MonotonicClock ≠ CivilTimeReference.**

### TE-123
Its arbitrary origin can make absolute value meaningless while differences remain operationally useful.

### TE-124
This is a computational hard case for `usefulness of time coordinate does not require global epoch`.

---

# 43. Wall clock can jump while physical elapsed time does not

Administrative/NTP/time-scale corrections may change civil clock coordinates.

### TE-125
**WallClockJump ≠ PhysicalTimeJump.**

### TE-126
Timeout/deadline semantics and record timestamps can therefore require different clock domains.

---

# 44. Deadline is not timestamp by identity

A deadline can be expressed as absolute reference time or as duration from a monotonic state.

### TE-127
**Deadline ≠ Duration ≠ CurrentTimestamp.**

### TE-128
Timeout measures waiting/control horizon; it does not necessarily claim target-event chronology.

---

# 45. Scheduling time is not execution time

A task scheduled for time `t` may execute after `t` because of load, timer granularity or scheduler policy.

### TE-129
**ScheduledTime ≠ ActualStartTime ≠ CompletionTime.**

### TE-130
Timer firing lateness is an execution property, not proof that scheduled temporal standing was wrong.

---

# 46. Simulation time is its own operational temporal domain

A simulation may define state evolution under `t_sim` while running faster/slower than wall time.

### TE-131
**SimulationTime ≠ WallClockTime.**

### TE-132
Simulation pause can hold `t_sim` fixed while computation/wall time continues.

### TE-133
Offline simulation can advance years of model time in seconds of wall time.

---

# 47. Render time is not simulation time

A renderer may draw multiple frames per simulation step, skip rendering steps, or interpolate between states.

### TE-134
**RenderFrameTime ≠ SimulationStateTime.**

### TE-135
Visual smoothness can be improved through interpolation without increasing simulated dynamics update frequency.

### TE-136
Render order is a presentation profile over simulation state history.

---

# 48. Fixed timestep does not mean fixed display frame rate

### TE-137
**PhysicsStep ≠ DisplayFrame.**

### TE-138
A 60 Hz simulation and 120 Hz display can coexist; one simulation state interval can contribute to multiple rendered frames.

### TE-139
Conversely overloaded rendering can drop frames without necessarily dropping simulation steps.

---

# 49. Game/media time scale is transformation, not physical time control

A system can map:

```text
dt_sim = k * dt_wall
```

for adjustable `k`.

### TE-140
**TimeScaleFactor changes system temporal evolution mapping, not external physical time.**

### TE-141
Pause corresponds approximately to `k=0` for selected subsystems, not universal temporal cessation.

### TE-142
Different subsystems may use different clocks/time scales (UI, physics, network, animation).

---

# 50. Rewind changes represented/system state chronology, not reality chronology

A game/editor can restore an earlier recorded simulation state.

### TE-143
**Rewind ≠ PhysicalTimeReversal.**

### TE-144
System state can revisit a prior simulation coordinate at a later wall-clock event.

### TE-145
This creates a branching/versioned state history problem for MF7, not a contradiction in MF6.

---

# 51. Replay time and original event time are distinct

A replay can present a recorded event sequence now.

### TE-146
**ReplayPresentationTime ≠ OriginalEventTime.**

### TE-147
One artifact can preserve original event timestamps while assigning new playback timestamps.

---

# 52. Temporal transformation can preserve order while changing duration

Speed-up/slow-down can map source presentation time `t` to `t'=f(t)`.

### TE-148
**OrderPreservingTemporalTransform ≠ DurationPreservingTransform.**

### TE-149
Uniform rate change preserves order but rescales duration; cuts can remove intervals; reverse playback can reverse presentation order.

### TE-150
Temporal fidelity must declare which relations are intended to survive.

---

# 53. Audio time-stretch demonstrates multi-profile transformation

Time stretching can change duration while attempting to preserve pitch; ordinary resampling changes duration and pitch together.

### TE-151
**TemporalDurationTransform ≠ Frequency/PitchTransform by necessity.**

### TE-152
Media processing can selectively preserve temporal/spectral profiles.

This inherits MF1/MF4 typed-fidelity discipline.

---

# 54. Media synchronization is consumer/profile relative

A/V synchronization aims to align related content for presentation/perception, not necessarily make numeric timestamps equal.

### TE-153
**Synchronization = relation under declared clocks/content/consumer tolerance, not raw equality.**

### TE-154
Physical source simultaneity, media sampling synchrony, presentation synchrony and perceptual lip-sync are distinct.

### TE-155
MF6-D perceptual tolerance can differ from engineering clock alignment tolerance.

---

# 55. Perfect clock alignment does not guarantee perceptual synchrony

Different device/audio/video output latencies can create perceptual offset after media clocks are numerically aligned.

### TE-156
**ClockSync ≠ SignalEmissionSync ≠ PerceptualSync.**

### TE-157
End-to-end synchronization requires mapping across computational, device, physical-signal and perceptual layers.

---

# 56. Perceptual sync does not prove clock sync

A player can compensate known path latency by scheduling one stream earlier/later.

### TE-158
**PerceptualAlignment can be achieved despite unequal internal clock coordinates.**

### TE-159
Compensation is a transformation, not proof of identical clocks.

---

# 57. Temporal provenance is mandatory in media pipelines

A timestamp may denote:

- capture/sample time;
- source event time;
- encode/decode time;
- packet send/receive time;
- media PTS/DTS;
- wall-clock program time;
- ingestion/processing time;
- playback/output time.

### TE-160
**TimestampRole is part of the claim's semantics.**

### TE-161
A bare `timestamp` field is an ontology smell when multiple roles coexist.

---

# 58. Temporal uncertainty also has multiple sources

Clock uncertainty, timestamp quantization, network delay/asymmetry, scheduler jitter, codec buffering, device latency and inferred source time contribute differently.

### TE-162
**TemporalUncertainty ≠ Jitter ≠ TimestampResolution.**

### TE-163
Uncertainty must attach to the temporal role/transformation where it arises.

---

# 59. Same timestamp does not imply same physical event time

Two frames from unrelated timelines can share PTS `10s`.

### TE-164
**CoordinateEquality ≠ CrossDomainTemporalIdentity.**

### TE-165
Timestamp equality is meaningful only within a shared or mapped temporal coordinate system.

This is MF6's temporal analogue of MF5-C `same coordinates ≠ same position across frames`.

---

# 60. Different timestamps need not mean different target event time

Two systems/clocks with offsets can timestamp the same event differently.

### TE-166
**DifferentTimestampValues ≠ DifferentTargetTemporalPosition by default.**

### TE-167
Cross-system temporal reconciliation requires clock/reference mapping and uncertainty.

---

# 61. Computational temporal standing

MF6-E proposes:

```text
ComputationalTemporalStanding =
  typed order/time role
  + operational recruitment
  + clock/reference semantics
  + transition/scheduling consequences
  + scope/provenance
```

### TE-168
**A computational counter/timebase gains temporal standing through system semantics/consumption, not merely numeric ordering.**

### TE-169
Computational temporal standing need not transfer to represented physical/event time.

---

# 62. Media temporal standing

```text
MediaTemporalStanding =
  source/capture timing?
  + sample timing
  + decode timing
  + presentation timing
  + playback transformation
  + wall-clock mapping?
  + synchronization relations
  + provenance/scope
```

### TE-170
**MediaTime is a typed bundle, not one timeline scalar.**

---

# 63. ComputationalTemporalProfile

```text
ComputationalTemporalProfile = <
  System/Domain,
  TimeRole : event/processing/logical/wall/monotonic/simulation/etc.,
  Clock/Counter/Reference,
  Origin/Epoch?,
  Rate/Unit,
  OrderProperties,
  Monotonicity?,
  MappingToOtherClocks?,
  Scheduling/DeadlineSemantics?,
  Watermark/Completeness?,
  Uncertainty/Drift/Jitter?,
  Provenance/Authority,
  Scope
>
```

### TE-171
Bare `system time` is under-specified.

---

# 64. MediaTemporalProfile

```text
MediaTemporalProfile = <
  Asset/Stream/Track,
  Source/CaptureTimeline?,
  SampleClock/Rate?,
  Frame/SampleIdentity,
  PTS,
  DTS?,
  Duration,
  PresentationTimeline,
  Edit/TransformMapping?,
  PlaybackPosition/Rate,
  WallClockProgramMapping?,
  TransportSend/ReceiveTimes?,
  Buffer/Latency/Jitter,
  SyncGroup/MasterReference?,
  DeviceOutputLatency?,
  PerceptualSyncTarget?,
  Uncertainty,
  Provenance,
  Scope
>
```

### TE-172
One video/audio object can validly carry many timestamps without redundancy.

---

# 65. MediaFrameTemporalClaim

```text
MediaFrameTemporalClaim = <
  Frame/SampleUnit,
  Identity/SequenceIndex,
  PresentationTimestamp,
  DecodeTimestamp?,
  Duration,
  Timebase/Unit,
  Source/CaptureMapping?,
  WallClockMapping?,
  Transform/EditHistory,
  Uncertainty,
  Provenance,
  Scope
>
```

### TE-173
`frame N at time T` is incomplete unless `T`'s temporal role is declared.

---

# 66. StreamSynchronizationClaim

```text
StreamSynchronizationClaim = <
  Streams/Tracks,
  SyncRelation : source/sample/presentation/perceptual,
  PerStreamClocks,
  Reference/MasterClock?,
  ClockMappings,
  Offset,
  RateMismatch/Drift,
  BufferPolicy,
  Latency/Jitter,
  OutputDeviceLatency?,
  Tolerance,
  Uncertainty,
  Provenance,
  Scope
>
```

### TE-174
`A/V synchronized=true` without relation/tolerance/reference is under-specified.

---

# 67. EventTimeClaim

```text
EventTimeClaim = <
  Event/Record,
  ClaimedEventTime,
  Clock/Reference,
  SourceAuthority,
  Observation/Ingestion/Processing/CommitTimes?,
  ClockUncertainty,
  TransportDelay?,
  ValidationEvidence?,
  Provenance,
  Scope
>
```

### TE-175
An event timestamp is a sourced temporal claim, not an automatically verified fact.

---

# 68. SimulationTemporalProfile

```text
SimulationTemporalProfile = <
  Simulation/World,
  SimulationTime,
  Step/IntegrationTime,
  TimeScale,
  Pause/Rewind/BranchRules,
  Wall/MonotonicMapping?,
  RenderTime/FrameTime?,
  Network/AuthoritativeTick?,
  Input/EventTimeMapping?,
  Determinism/ReplaySemantics?,
  Uncertainty/Approximation,
  Provenance,
  Scope
>
```

### TE-176
Simulation state chronology is system-enacted temporal standing, not metaphor merely because it differs from wall time.

---

# 69. Strongest non-collapse stack after MF6-E

```text
SequenceNumber
 ≠ Timestamp
 ≠ Duration
```

```text
PacketOrder
 ≠ SampleOrder
 ≠ DecodeOrder
 ≠ PresentationOrder
```

```text
FrameIndex
 ≠ PTS
 ≠ DTS
 ≠ FrameDuration
```

```text
SampleIndex
 ≠ SampleTime
 ≠ WallTime
```

```text
Source/CaptureTime
 ≠ MediaPresentationTime
 ≠ PlaybackWallTime
```

```text
EventTime
 ≠ ObservationTime
 ≠ IngestionTime
 ≠ ProcessingTime
 ≠ CommitTime
 ≠ PublicationTime
```

```text
Watermark
 ≠ EventTime
 ≠ ProcessingTime
```

```text
LateData
 ≠ LateOccurrence
```

```text
LogicalClock
 ≠ PhysicalClock
 ≠ WallClock
 ≠ MonotonicClock
```

```text
SimulationTime
 ≠ RenderTime
 ≠ WallClockTime
```

```text
PlaybackRate
 ≠ PhysicalTimeRate
```

```text
Latency
 ≠ Jitter
 ≠ Loss
 ≠ Reordering
 ≠ SynchronizationError
```

```text
ClockSync
 ≠ SignalEmissionSync
 ≠ PerceptualSync
```

```text
LiveEdge
 ≠ PhysicalNow
```

```text
TimestampEquality
 ≠ CrossDomainTemporalIdentity
```

---

# 70. Failure taxonomy

## Sequence-time collapse
Packet/frame/version order treated as temporal measure.

## Timestamp-truth collapse
Stored timestamp treated as verified occurrence time.

## Decode-presentation collapse
Codec dependency time treated as presentation/source chronology.

## Frame-index timing collapse
Index/fps arithmetic used despite VFR/reordering/gaps.

## Sample-wall collapse
Sample clock coordinate treated as civil/wall time.

## Stream-clock collapse
Independent RTP/audio/video clocks directly compared without mapping.

## Transport-source collapse
Send/receive times substituted for source sampling/event time.

## Media-wall collapse
PTS/playback coordinate treated as absolute physical time.

## Edit-source collapse
Edited timeline treated as unchanged capture chronology.

## Playback-physical collapse
Seeking/pause/reverse interpreted as physical temporal manipulation.

## Event-processing collapse
Pipeline arrival/execution order treated as target event chronology.

## Watermark-truth collapse
Completeness estimate treated as event-time fact.

## Late-occurrence collapse
Late delivery/processing interpreted as event occurred late.

## Logical-physical collapse
Logical/version clocks treated as SI elapsed time.

## Wall-monotonic collapse
Civil clock used as invariant duration counter.

## Latency-jitter-sync collapse
Network/output temporal quality compressed into one delay scalar.

## Low-latency-sync inflation
Fast arrival interpreted as correct inter-stream alignment.

## Clock-perceptual collapse
Numerical media clock alignment treated as perceptual synchrony.

## Live-now collapse
Newest available stream point treated as physical present.

## Simulation-wall collapse
Simulation timeline treated as identical to wall time.

### TE-177
**Computational/media temporal failure is a typed family, not one `timestamp bug`.**

---

# 71. Primary/authoritative anchors

- **RFC 3550 — RTP: A Transport Protocol for Real-Time Applications.** Separates packet sequence number from media timestamp; timestamps reference sampling instants, can differ from transmission order, different media streams have different clock rates/random offsets, and RTCP RTP↔NTP timestamp pairs support inter-media synchronization. Interarrival jitter is separately defined from timing variation.
- **W3C Media Source Extensions 2.** Defines coded frame presentation timestamp, decode timestamp, coded-frame duration, presentation interval/order, timestamp offsets and coded-frame processing; directly anchors `DTS ≠ PTS ≠ duration` and decode-order/presentation-order separation.
- **W3C WebCodecs.** Exposes `VideoFrame.timestamp` as presentation timestamp and `duration` separately; constant-rate generated timestamps are a special case.
- **WHATWG HTML Standard — Media elements.** Defines current playback position on the media timeline and `playbackRate` as the speed of media-resource playback, establishing media timeline/playback time as a distinct operational coordinate.
- **W3C Web Audio API.** Defines `AudioContext.currentTime` in the audio rendering/sample-frame coordinate system, explicitly noting it may not synchronize with other clocks and that offline rendering need not approximate real time; distinguishes output latency.
- **Apache Beam programming model.** Separates event time from processing time, defines watermarks as stream-completeness/progress estimates, and supports event-time/processing-time triggers and windows; anchors event/processing/watermark separation.
- **POSIX / The Open Group clock APIs.** Distinguish CLOCK_REALTIME from CLOCK_MONOTONIC; monotonic absolute origin can be arbitrary while interval measurements remain useful and unaffected by wall-clock setting.
- **RFC 8216 — HTTP Live Streaming.** `EXT-X-PROGRAM-DATE-TIME` explicitly maps the first sample of a media segment to an absolute date/time, demonstrating wall-clock anchoring as an added relation rather than intrinsic media timestamp identity.

---

# 72. Deep reconstruction

Naive digital model:

```text
one system clock
   ↓
everything gets a timestamp
   ↓
sort timestamps
   ↓
reconstruct true chronology
   ↓
use same value for packets, frames, media, simulation and UI
```

MF6-E replaces it with:

```text
Target/source event chronology
       │
       ├─ capture/sample clock
       │      ↓
       │   sampled media timestamps
       │
       ├─ encode/decode dependency timeline
       │      ↓ DTS
       │
       ├─ presentation/edit timeline
       │      ↓ PTS + duration
       │
       ├─ transport timeline
       │      send / receive / sequence / latency / jitter
       │
       ├─ wall/reference mapping
       │      RTP↔NTP / program-date-time / time scale
       │
       ├─ processing timeline
       │      ingestion / processing / commit / watermark
       │
       ├─ playback/output timeline
       │      player position / rate / buffer / device latency
       │
       └─ perceptual/action consumer
              ↓ sync tolerance / experienced timing

Separate system domains may also carry:

logical/causal time
monotonic elapsed time
simulation time
render time
scheduler/deadline time
```

The decisive move is:

> **Computational systems do not possess `the timestamp`. They operate several typed temporal coordinates and relations. Correctness comes from preserving mappings and standing between those domains, not from forcing them into one scalar.**

---

# 73. Deepest MF6-E result

> **Computational/media time is a family of operational temporal standings: event/source time, sampling time, logical/causal order, decode time, presentation time, transport send/receive time, processing time, wall/reference time, monotonic elapsed time, playback/output time and simulation time. These domains may share numerical representations while remaining semantically distinct. Synchronization is therefore the establishment/maintenance of typed correspondences among clocks/timelines within declared tolerances, not simple timestamp equality. Sequence, latency, jitter, buffering and scheduling are related temporal structures but are not Time itself.**

Compact:

```text
Sequence orders units.
Clocks coordinate domains.
Timestamps state temporal claims.
PTS schedules presentation.
DTS schedules decoding.
Buffers reshape delivery→presentation timing.
Watermarks estimate stream completeness.
Simulation time enacts model chronology.
Synchronization relates clocks/timelines.
None is universal Time.
```

---

# 74. Earlier-foundation audit

## MF1 Signal
RTP/sample/latency/jitter distinctions reinforce signal transformation/provenance. No reopen.

## MF2 Perception
Engineering sync versus perceptual sync separation reinforces MF2/MF6-D. No reopen.

## MF3 Representation
PTS/source timestamp mapping is a representation/grounding problem; `timestamp ≠ target event time` directly fits MF3. No reopen.

## MF4 Composition
A/V temporal coordination is typed compositional organization, not a contradiction. No reopen.

## MF5 Space
No spatial contradiction. No reopen.

### TE-178
**MF0–MF5 remain FROZEN; MF6-E triggers no concrete earlier FoundationReopenCondition.**

---

# 75. MF6-A→E reconstruction

```text
MF6-A — Temporal ontology
Temporal standing / alternatives / typed relations

MF6-B — Order, interval, measure, clocks
Order → interval → duration → clock/time-scale realization

MF6-C — Relativity
Invariant causal order vs coordinate order/simultaneity;
proper time vs coordinate time

MF6-D — Organismal time
Physical/reference time → perceptual/experienced/biological/action profiles

MF6-E — Computational/media time
Event/source/sample/logical/decode/presentation/transport/
processing/wall/monotonic/playback/simulation time
connected by explicit mappings
```

MF6 remains UNFROZEN.

---

# 76. MF6-F handoff — Time Falsification & Reconstruction

MF6-F is the final adversarial synthesis before a Time Foundations v1 freeze decision.

Required attacks:

1. **Over-inclusion:** Does TemporalStanding make arbitrary sequence/version/state-transition structures temporal?
2. **Under-inclusion:** Can temporal domains exist without metric duration, global clocks, instants, total order or continuity?
3. **Primitive choice:** Is point/instant-first, interval-first or event/process-first required, or must the core remain plural?
4. **Order:** Does typed earlier/later survive distributed partial orders, relativity and perceptual uncertainty?
5. **Duration:** Is duration a universal temporal constituent or optional measure profile?
6. **Clock:** Can Time remain meaningful without clocks; can clock standing be defined without circularity?
7. **Relativity:** Does proper/coordinate/causal typing remain coherent under spacetime coupling?
8. **Perception:** Does perceptual temporal plurality create vacuous many-times inflation?
9. **Biology:** Are circadian/interval/action timing genuinely temporal standing or merely dynamics/state?
10. **Computation:** When does logical/simulation/media `time` become genuine temporal standing rather than metaphorical sequence?
11. **Media:** Can PTS/DTS/edit/playback timelines be integrated without laundering presentation time into target chronology?
12. **Standing transfer:** Formal/computational/media temporal coordinates → represented target time require what grounding?
13. **MF7 boundary:** Is Time being contaminated by State/Dynamics/Change?
14. **Uncertainty/provenance:** Can partial order, uncertain timestamps, watermarks and perceptual timing live in one claim model?
15. **Freeze:** Only freeze if no surviving hard case requires foundational reconstruction.

Central final candidate to attack:

```text
TemporalDomain
 = Temporal Alternatives
 + Temporal Standing
 + Typed Temporal Relation Structure
 + Standing Route
 + Scope

Optional enrichments:
 order / interval / duration / metric /
 clocks / coordinates / simultaneity /
 perception / biology / computation / media
```

Potential key falsifier:

> If any operational sequence with `before/after` becomes temporal merely because a system uses it, MF6 over-includes version numbers/workflows. MF6-F must derive a stronger `temporal role` firewall analogous to MF5-I's PositionalStanding correction.

**Next: MF6-F — Time Falsification & Reconstruction.**
