---
schema_version: 1
id: game.foundations-research.r23
title: Ordivon Game Foundations Research — R23 Time, Sequence, Simultaneity, Duration, Timing, Rhythm, Turn, Cooldown, Deadline and Temporal Agency
type: research
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - researcher
  - builder
  - agent
updated: 2026-08-17
summary: Canonical R23 decomposition of temporal frames, event order, simultaneity, concurrency, duration, timing, tempo, rhythm, turns, phases, ticks, windows, deadlines, waiting, reversibility, persistence and temporal agency across action, strategy, social, creative and generative game forms.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.r18
  - game.foundations-research.r19
  - game.foundations-research.r20
  - game.foundations-research.r21
  - game.foundations-research.r22
  - game.foundations-research.map
  - game.foundations-research.continuation
  - game.core-research.reset
---
# Ordivon Game Foundations Research — R23 Time, Sequence, Simultaneity, Duration, Timing, Rhythm, Turn, Cooldown, Deadline and Temporal Agency

## 0. Status and boundary

R23 continues the foundation programme after R1–R22. It is a research record, not a product specification and not a G0–G8 promotion.

R22 asked:

> What changes when future states and outcomes cannot be known exactly?

R23 asks:

> How are actions, opportunities and consequences ordered through time, and how does temporal structure itself create choice, skill, coordination, commitment and meaning?

The overloaded terms under attack are:

```text
Time
Clock
Timestamp
Sequence
Order
Before / After
Simultaneity
Concurrency
Turn
Round
Phase
Tick
Duration
Timing
Tempo
Rhythm
Pacing
Cadence
Window
Deadline
Timeout
Delay
Latency
Wind-up
Active Interval
Recovery
Cooldown
Commitment
Initiative
Reaction
Waiting
Pause
Slow Motion
Fast-forward
Asynchrony
Persistence
Replay
Undo
State Restore
Rewind
Temporal Agency
```

Starting warnings:

```text
Time != Clock value
Sequence != Duration
Clock order != Causal order
Simultaneity != Concurrency
Turn != Tick != Phase
Duration != Timing
Tempo != Rhythm != Pacing
Latency != Game-world duration
Deadline != Timer UI
Cooldown != Recovery
Waiting != Dead Time
Real-time != More agency
Faster != Deeper
Persistence != Continuous computation
Replay != Undo != StateRestore != InWorldRewind
World-state reversal != Player-knowledge reversal
```

No product is selected by R23.

---

# 1. External anchors and what they do — and do not — establish

R23 triangulates game-time research, temporal reasoning, distributed/concurrent systems, real-time formal methods, temporal cognition, sensorimotor synchronization, decision making under time pressure, strategic timing and recent game-waiting/AI interaction research. These are pressure tests, not a universal Game ontology.

## 1.1 Juul — play time and event time can map differently

Jesper Juul's 2004 *Introduction to Game Time / Time to Play* distinguished the time spent playing from time represented/passing in the game world, and examined different mappings between them. His analysis also highlights pause, save/load, cutscenes and turn-based structures as temporal transformations rather than one universal clock.

Game lesson:

```text
Player elapsed time
!=
World/event elapsed time
```

and their mapping may pause, accelerate, compress, jump or become only weakly metric.

R23 does not adopt a two-clock ontology as sufficient for every multiplayer, narrative, persistent or generative form.

## 1.2 Zagal and Mateas — temporality is relational and multi-frame

Zagal and Mateas' 2010 analysis defines a temporal frame as a set of events plus the temporality induced by relationships between them. They identify real-world, gameworld, coordination and fictive frames as common analytic frames.

Game lesson:

```text
“Game time” should not be one scalar by default.
```

Different event sets can carry different order/rate/coordination semantics and map nontrivially to one another.

## 1.3 Tychsen and Hitchens — multiplayer time is interactively created and nonlinear

Their game-time model emphasizes multiple perspectives and complex temporal behavior in multiplayer/MMO contexts.

Game lesson:

```text
Shared temporality is partly a coordination structure,
not only a simulation clock.
```

## 1.4 Zagal, Fernández-Vara and Mateas — temporal segmentation coordinates activity

Their work on rounds, levels and waves separates temporal, spatial and challenge segmentation; temporal segmentation can limit, synchronize and coordinate player activity.

Game lesson:

```text
Round / wave / phase structures can be coordination mechanisms,
not merely chapter labels.
```

## 1.5 Lamport — causal order does not require one global physical-time order

Lamport's 1978 distributed-systems work formalized a causal “happened-before” relation and showed why distributed events naturally form a partial order before any artificial total order is imposed.

Game lesson:

```text
WallClockOrder != CausalOrder
NetworkArrivalOrder != SemanticPriority
```

If two actions are causally independent, forcing a millisecond arrival race into gameplay can create accidental mechanics. If they conflict, the game must define a semantic resolution relation rather than inherit transport timing by accident.

## 1.6 Allen — temporally extended processes need interval relations

Allen's 1983 temporal-interval work formalizes qualitative relations among intervals, such as before, meets, overlaps, during, starts and finishes.

Game lesson:

```text
Action != Point timestamp by necessity.
```

Actions, vulnerabilities, cooldowns, casts and commitments can occupy intervals whose relationships matter even when exact milliseconds do not.

## 1.7 Alur and Dill — timing can constrain state transitions

Timed automata add real-valued clocks and timing constraints to state-transition graphs.

Game lesson:

```text
Time can be part of legality / transition guards,
not merely presentation.
```

A door being open only for five seconds is a different possibility space from an animation that happens to last five seconds.

## 1.8 Block and Zakay — objective duration, experienced duration and remembered duration differ

Their meta-analysis found systematic differences between prospective and retrospective duration judgments and supports partly different attentional versus memory-related processes.

Game lesson:

```text
ClockDuration
!= ExperiencedDuration
!= RememberedDuration
```

Do not assume ten measured seconds create the same temporal experience in every context.

## 1.9 Repp — rhythm skill includes phase correction, not merely speed

Sensorimotor synchronization experiments show rapid correction to phase perturbations in rhythmic tapping.

Game lesson:

```text
Tempo != Rhythm
Fast input != Timing mastery
```

Temporal skill can involve prediction, phase alignment and error correction.

## 1.10 Ben Zur and Breznitz — time pressure changes information processing and choice

Their 1981 experiment compared risky choices under 8-, 16- and 32-second decision windows. In that task, high time pressure changed information acquisition/processing and choice patterns.

Game lesson:

```text
TimePressure != merely “difficulty +1”.
```

Temporal scarcity can change which evidence is inspected, how long deliberation lasts and which policy is selected.

Do not generalize the direction of risk change from one experiment into a universal player law.

## 1.11 Fudenberg and Tirole — timing itself can be strategic

Preemption models show cases in which the date/timing of adoption changes strategic payoff because moving earlier or later changes leader/follower positions and opponent incentives.

Game lesson:

```text
Same substantive action
+ different time
→ different strategic game
```

## 1.12 Waiting can be gameplay, not merely absence of gameplay

Recent peer-reviewed work on waiting in video games finds that waiting situations span loading, turn-taking, cutscenes and other contexts and can affect anticipation, frustration, boredom, decision making and behavior.

Game lesson:

```text
Waiting must be decomposed by cause, state change, goal and consequence.
```

## 1.13 Recent VLM game benchmarks are a temporal-fit pressure test

VideoGameBench (2025) reported inference latency as a major limitation for frontier vision-language models in real-time games and introduced a setting that pauses the game while waiting for the model.

Game lesson:

```text
Agent capability is temporal-form relative.
```

Pausing is not merely an optimization; it changes the temporal interaction contract. A model too slow for a sensorimotor loop can still fit turn-based, command or asynchronous play.

### Primary/high-quality reference anchors used in this round

- Juul, J. (2004), *Introduction to Game Time / Time to Play*.
- Zagal, J. P. & Mateas, M. (2010), *Time in Video Games: A Survey and Analysis*, DOI 10.1177/1046878110375594.
- Tychsen, A. & Hitchens, M. (2009), *Game Time: Modeling and Analyzing Time in Multiplayer and Massively Multiplayer Games*, DOI 10.1177/1555412008325479.
- Zagal, J. P., Fernández-Vara, C. & Mateas, M. (2008), *Rounds, Levels, and Waves*, DOI 10.1177/1555412008314129.
- Lamport, L. (1978), *Time, Clocks, and the Ordering of Events in a Distributed System*, Communications of the ACM 21(7), 558–565.
- Allen, J. F. (1983), *Maintaining Knowledge about Temporal Intervals*, DOI 10.1145/182.358434.
- Alur, R. & Dill, D. L. (1994), *A Theory of Timed Automata*, DOI 10.1016/0304-3975(94)90010-8.
- Block, R. A. & Zakay, D. (1997), *Prospective and Retrospective Duration Judgments: A Meta-analytic Review*, DOI 10.3758/BF03209393.
- Repp, B. H. (2001), *Phase Correction, Phase Resetting, and Phase Shifts after Subliminal Timing Perturbations in Sensorimotor Synchronization*, DOI 10.1037/0096-1523.27.3.600.
- Ben Zur, H. & Breznitz, S. J. (1981), *The Effect of Time Pressure on Risky Choice Behavior*, DOI 10.1016/0001-6918(81)90001-9.
- Fudenberg, D. & Tirole, J. (1985), *Preemption and Rent Equalization in the Adoption of New Technology*, DOI 10.2307/2297660.
- Tepponen, N., Bhatnagar, P., Väkevä, J. & Hämäläinen, P. (2025), *Towards Understanding Waiting in Video Games*, DOI 10.1145/3748613.
- Zhang, A. L., Griffiths, T. L., Narasimhan, K. R. & Press, O. (2025), *VideoGameBench: Can Vision-Language Models Complete Popular Video Games?*, arXiv:2505.18134.

These sources constrain and falsify R23; they do not replace Game-specific causal analysis.

---

# 2. Core term separation

| Term | Working meaning | Not equivalent to |
| --- | --- | --- |
| **Temporal Frame** | A set of events/processes plus temporal relations, optional metric and progression semantics used to interpret them. | One global clock. |
| **Clock / Metric** | Mechanism/coordinate for measuring or labeling temporal distance/order in a frame. | Causal order itself. |
| **Sequence** | An ordered arrangement/relation among events/actions. | Duration. |
| **Causal Order** | Ordering required by dependence: one event can affect another. | Wall-clock arrival order. |
| **Simultaneity** | Events assigned the same semantic temporal point/window/resolution relation. | Concurrency. |
| **Concurrency** | Events/processes overlap or remain only partially ordered; neither must causally precede the other. | Same timestamp. |
| **Duration** | Extent between start/end boundaries in a specified frame. | Timing. |
| **Timing** | Placement of an event/action relative to another event, interval, beat, window or boundary. | Duration or speed. |
| **Tempo** | Rate/density of relevant events/actions in a chosen frame. | Rhythm or pacing. |
| **Rhythm** | Patterned relations among intervals, accents, recurrence and/or phase. | Average event rate. |
| **Pacing** | Macro distribution of tension, decisions, novelty, feedback, recovery and closure through time. | Tempo. |
| **Turn** | Rule-bounded opportunity/authority to commit one or more actions/decisions. | Tick or fixed duration. |
| **Round** | Coordination/segmentation cycle grouping opportunities, turns or simultaneous commitments. | Universal time unit. |
| **Phase** | Temporal regime in which legal actions, information or resolution rules differ. | Turn. |
| **Tick** | Discrete simulation/update quantum when the model chooses one. | Player turn. |
| **Window** | Interval in which an action/state/reaction is available, legal or valuable. | Deadline alone. |
| **Deadline** | Boundary after which action legality/value/option set changes. | Timer UI. |
| **Timeout** | Rule/system consequence triggered by lack of completion/response before a boundary. | Every deadline. |
| **Delay** | Temporal separation between two relevant events. | Latency specifically. |
| **Latency** | System/communication delay between input/request and relevant response/effect. | World duration. |
| **Wind-up** | Committed/preparatory interval before primary effect becomes active. | Cooldown. |
| **Recovery** | Post-effect interval constraining next action/capability. | Cooldown necessarily. |
| **Cooldown** | Temporal availability constraint preventing reuse until a condition/time passes. | Recovery animation. |
| **Commitment Point/Window** | Boundary/interval after which revision/cancellation becomes impossible or costly. | Effect time. |
| **Initiative** | Rule-defined temporal priority/opportunity relation among competing actors/actions. | Physical speed. |
| **Waiting** | Passage of time without another overt intervention by the participant; may still transform state, information, options, costs or experience. | Dead time. |
| **Asynchrony** | Participants act/observe at different real-world times while contributions connect to shared state. | Turn-based only. |
| **Persistence** | Relevant state/history survives session/attention/time boundaries. | Continuous simulation. |
| **Pause** | Progression of one or more temporal frames is suspended while others may continue. | Stop all time. |
| **Replay** | Re-observation/reconstruction of past events without changing authoritative past state. | Undo. |
| **Undo** | Meta/action operation cancelling or compensating a prior committed change under defined rules. | State restore. |
| **State Restore** | Replace current authoritative state with a previously retained state/checkpoint. | In-world time travel. |
| **In-world Rewind** | Temporal reversal/manipulation represented as a world/game mechanic with its own causal rules. | Save/load. |
| **Temporal Agency** | Meaningful participant influence over timing/order/duration/synchronization/interruption/reversal when those choices alter reachable futures. | Acting faster. |

Compact separation:

```text
Time != Clock
Sequence != Duration
ClockOrder != CausalOrder
Simultaneity != Concurrency
Turn != Tick != Phase
Duration != Timing
Tempo != Rhythm != Pacing
Deadline != Timer
Cooldown != Recovery
Latency != GameWorldTime
Waiting != DeadTime
Persistence != ContinuousSimulation
Replay != Undo != StateRestore != InWorldRewind
```

---

# 3. Time — avoid the one-clock ontology

R23 does not attempt to settle the metaphysics of time.

For Game analysis, the minimum useful structure is relational:

```text
TemporalFrame =
Events / Processes
+ TemporalRelations
+ optional Metric / Clock
+ ProgressionRule
```

The same play session can contain several frames.

## 3.1 Common useful frames

```text
Real / Wall Time
Gameworld / Simulation Time
Coordination Time
Fictive / Narrative Time
Subjective / Experienced Time
Authority Time (when a rule explicitly needs one)
```

These are analytic roles, not mandatory engine clocks.

## 3.2 Real / Wall Time

Physical elapsed time for player/system interaction.

Examples:

```text
30 seconds spent deliberating
network request takes 400 ms
player returns tomorrow
```

## 3.3 Gameworld / Simulation Time

Temporal evolution that determines world dynamics.

Examples:

```text
day/night
stamina regeneration
unit movement
crop growth
```

## 3.4 Coordination Time

Temporal structure allocating and synchronizing opportunities among Subjects.

Examples:

```text
turn
planning phase
auction deadline
simultaneous reveal
respawn wave
```

## 3.5 Fictive / Narrative Time

Represented chronology and culturally meaningful labels:

```text
“three years later”
flashback
winter of year 12
```

It can advance without simulating every intervening state.

## 3.6 Subjective / Experienced Time

The participant's lived temporal experience.

It need not match wall time or remembered duration.

## 3.7 Authority Time

When rules require one exact temporal reference, the game must define which clock/order is authoritative for:

```text
deadlines
expiry
commitment
resolution
cooldown completion
persistent timers
```

Authority Time is a responsibility relation, not necessarily another physical clock.

---

# 4. Temporal Mapping — frames can run at different rates or jump

R23 introduces:

```text
TemporalMapping(F_a → F_b)
```

as the mapping between events/intervals in different temporal frames.

The mapping may be:

```text
1:1
scaled
piecewise
paused
discontinuous
many-to-one
one-to-many
weakly metric / action-triggered
```

## 4.1 Real-time action game

Approximately:

```text
1 second wall time
≈ 1 second simulation time
```

for relevant local action.

## 4.2 Fast-forward

```text
1 second wall time
→ many seconds world time
```

## 4.3 Slow motion

```text
1 second wall time
→ fraction of world time
```

## 4.4 Pause

```text
wall time advances
world/coordination frame selected by pause does not
```

## 4.5 Turn-based deliberation

A player may think for 60 real seconds while the represented action consumes one move or a few world seconds.

```text
WallDuration
is not necessarily mapped proportionally to
WorldDuration.
```

## 4.6 Narrative time skip

```text
one sentence / cut
→ years of fictive time
```

without continuous simulation.

## 4.7 Persistent world

```text
player session absent
while world/authority time continues
```

## 4.8 Idle/offline progression

A system may use elapsed authority time to compute state on return instead of continuously simulating every tick.

This yields a crucial rule:

```text
Persistence != Continuous Computation
```

---

# 5. Sequence and order — time without duration

A sequence can matter even when exact durations do not.

```text
A before B
```

is different from:

```text
B before A
```

without requiring “A was 2.31 seconds earlier.”

## 5.1 Order can change reachable futures

Examples:

```text
unlock → open door
vs
open door → unlock
```

```text
heal → receive damage
vs
receive lethal damage → heal
```

```text
buy information → bid
vs
bid → information arrives
```

## 5.2 Presentation order is another order

```text
WorldChronology
!= NarrativePresentationOrder
!= UIAnimationOrder
!= ResolutionOrder
```

A flashback presents later in play what occurred earlier in fictive chronology.

## 5.3 History depends on order

R13 established that history is not merely an event log. R23 adds:

```text
Same event multiset
+ different order
→ potentially different history
```

---

# 6. Causal order versus clock order

Lamport provides a strong formal pressure test.

R23 adopts the distinction:

```text
CausalOrder:
e1 must precede e2 because e1 can influence e2
```

versus:

```text
ClockOrder:
a clock/timestamp system labels e1 earlier than e2
```

## 6.1 Independent events may be unordered

If two remote actions cannot affect each other before resolution, forcing them into a first/second semantic order may be unnecessary.

## 6.2 Total order can still be required by the game

The game may deliberately impose:

```text
initiative order
seat order
priority stack
server sequence
```

but this is a rule choice.

## 6.3 Transport order is not a neutral design decision

```text
packet arrived first
```

should not automatically mean:

```text
player acted first
```

unless the product intentionally makes network arrival timing part of play.

Core rule:

```text
NetworkArrivalOrder != SemanticPriority by default.
```

---

# 7. Simultaneity versus concurrency

## 7.1 Simultaneity

```text
Simultaneity =
events are assigned the same semantic resolution time/window
or explicitly treated as jointly occurring.
```

## 7.2 Concurrency

```text
Concurrency =
events/processes can proceed without a complete causal order;
they may overlap or remain partially ordered.
```

Therefore:

```text
Simultaneity != Concurrency
```

Two concurrent processes may start/end at different times.
Two simultaneous commitments may be resolved as one joint transition.

## 7.3 Simultaneous intent does not imply simultaneous effect

A game can collect orders simultaneously and then resolve them by:

```text
initiative
speed
joint collision rules
resource priority
random tie-break
```

The collection and resolution frames must remain distinct.

---

# 8. Commutativity — a cheap test for whether order matters

For deterministic local transitions `T_a` and `T_b`, compare:

```text
T_a(T_b(s))
```

with:

```text
T_b(T_a(s))
```

If equal under the relevant semantics:

```text
order is locally irrelevant / actions commute
```

If unequal:

```text
order is causally meaningful
```

## 8.1 Noncommuting actions need explicit semantics

Options include:

```text
priority ordering
initiative
joint/simultaneous transition
conflict rejection
shared-resource allocation
stochastic tie-break
```

## 8.2 Simultaneous resolution != arbitrary sequentialization

Serializing two actions in implementation is not enough to justify one happening “first” in game semantics.

This is especially important for:

```text
movement collision
simultaneous attacks
shared inventory claims
auctions
multi-Agent commitments
```

---

# 9. Duration — extent in a specified frame

```text
Duration_F(e) =
end_F(e) - start_F(e)
```

when the frame has a suitable metric.

## 9.1 Duration is frame-relative

```text
10 real seconds
```

can correspond to:

```text
10 world seconds
1 turn
3 fictional days
0 paused world time
```

## 9.2 Not all useful frames need metric duration

A strict turn sequence may only require:

```text
before / after / same round
```

without assigning world seconds.

## 9.3 Duration can be a mechanic

Examples:

```text
hold shield for 3 seconds
charge spell longer for more power
survive until dawn
maintain alliance for 5 turns
```

---

# 10. Timing — relative placement, not duration

```text
Timing =
placement of an action/event relative to
another event, interval, boundary, beat or opportunity window.
```

Examples:

```text
parry just before impact
buy before price update
interrupt during cast
attack after guard recovery
speak before vote closes
```

A zero-duration button press can have deep timing.
A long-duration process can have trivial timing.

Therefore:

```text
Duration != Timing
```

---

# 11. Tempo — rate/density, not temporal structure as a whole

Working definition:

```text
Tempo =
rate/density of relevant events/actions/decisions
per unit of a chosen temporal frame.
```

But several rates may differ:

```text
World event rate
Input rate
Meaningful decision rate
Information arrival rate
Threat rate
Reward rate
```

Therefore:

```text
WorldSpeed != DecisionDensity
```

A visually fast game can have sparse meaningful decisions.
A slow turn-based game can have dense decision structure.

---

# 12. Rhythm — patterned temporal relations

```text
Rhythm =
structured pattern of intervals, accents, recurrence and/or phase
across events/actions.
```

## 12.1 Tempo and rhythm separate

Two sequences can share average tempo while having different interval patterns.

```text
Tempo != Rhythm
```

## 12.2 Rhythm can be learned and corrected

Sensorimotor synchronization work supports phase correction as a genuine timing process.

Game skill can therefore involve:

```text
beat prediction
phase alignment
temporal error correction
pattern recognition
anticipatory action
```

not merely faster reaction.

## 12.3 Rhythm beyond music games

Examples:

```text
attack → dodge → punish cadence
production/economy cycles
enemy wave intervals
dialogue turn cadence
creative iteration cycles
```

---

# 13. Pacing — macro temporal distribution

R7 already established:

```text
Pacing =
distribution of tension,
decision density,
novelty,
feedback,
recovery,
and closure through time.
```

R23 preserves:

```text
Pacing != ClockSpeed
Pacing != Tempo
Pacing != Rhythm
```

Examples:

```text
High tempo + flat pacing
Slow tempo + escalating pacing
Regular rhythm + varied pacing
```

Pacing is primarily an experience/structure question across larger spans.

---

# 14. Clock Duration, Experienced Duration and Remembered Duration

R23 distinguishes:

```text
ClockDuration
ExperiencedDuration
RememberedDuration
```

Block and Zakay's prospective/retrospective findings support the broader claim that these are not interchangeable.

## 14.1 Prospective time experience

When temporal monitoring itself is relevant, attention to time can change experienced duration.

## 14.2 Retrospective time

Remembered duration can depend more on memory/contextual change than on how time was monitored while occurring.

## 14.3 Game consequence

Do not optimize pacing from seconds alone.

A five-second wait and a five-second decision window can have very different experience and value.

## 14.4 No universal “time flies when fun” law

R23 rejects simplistic one-factor claims. Attention, task structure, memory, anticipation and uncertainty can all matter.

---

# 15. Turn — temporal authority, not a unit of seconds

Working definition:

```text
Turn =
a rule-bounded opportunity/authority interval
for a Subject/player to commit specified decisions/actions.
```

## 15.1 Turn duration can be unbounded, bounded or zero-deliberation

```text
untimed chess turn
30-second turn timer
precommitted automated turn
```

all remain turns.

## 15.2 Turn can advance no explicit world duration

A board-game move need not correspond to a fixed number of fictional seconds.

## 15.3 Turn grants authority

The important structure is often:

```text
who may act
what may be committed
what can be observed before committing
when resolution occurs
```

not elapsed seconds.

---

# 16. Round — grouping and synchronization

```text
Round =
a recurring coordination segment that groups
turns, commitments, actions or resolution.
```

Examples:

```text
all players act once
planning then reveal
combat exchange
auction round
```

A round can contain:

```text
sequential turns
simultaneous commitments
multiple phases
multiple simulation ticks
```

Therefore:

```text
Round != Turn
Round != Tick
```

---

# 17. Phase — temporal regime of rules

```text
Phase =
an interval/regime in which legal actions,
information access or resolution rules differ.
```

Examples:

```text
planning
commit
reveal
resolution
recovery
```

or:

```text
day / night
attack / defense
build / combat
```

A phase may be:

```text
real-time
turn-based
fixed-duration
event-terminated
```

Therefore:

```text
Phase != Turn
```

---

# 18. Tick — simulation/update quantum

```text
Tick =
a chosen discrete quantum/event at which
simulation/update rules advance.
```

Ticks may be:

```text
fixed-rate
variable-rate
event-driven equivalents
visible or invisible to players
```

## 18.1 Tick is often implementation-level

If player value is invariant to exact tick granularity, do not elevate it into game ontology.

## 18.2 Tick can become semantic

If actions explicitly cost/occur on ticks:

```text
next tick
three ticks to complete
```

then it becomes player-facing temporal structure.

## 18.3 Higher tick rate is not more depth

```text
TemporalResolution != TemporalDepth
```

---

# 19. Temporalized Action — action is often an interval protocol

R21's action/control chain is extended by temporal stages:

```text
Opportunity opens
→ Intent
→ Commit
→ Preparation / Wind-up
→ Effect / Active interval
→ Completion
→ Recovery
→ Next availability
```

Not every action needs every stage.

## 19.1 Commitment and effect can be separated

This creates:

```text
telegraphing
counterplay
interruption
prediction
risk
```

## 19.2 Completion and next availability can differ

A sword swing may finish visually while recovery still prevents another attack.

## 19.3 Presentation must not silently redefine authority

```text
AnimationEnd
!= necessarily
ActionLegalityBoundary
```

unless intentionally bound.

---

# 20. Wind-up, active interval, recovery and cooldown

## 20.1 Wind-up

```text
Commit
→ before primary effect
```

Often creates commitment/counterplay.

## 20.2 Active/effect interval

Interval during which effect is causally live.

## 20.3 Recovery

Post-effect restriction on movement/action/cancellation.

## 20.4 Cooldown

Temporal condition preventing reuse until a later boundary.

Cooldown may outlast recovery or overlap it.

Therefore:

```text
WindUp != ActiveInterval != Recovery != Cooldown
```

## 20.5 Timer UI is representation

```text
CooldownState
!= CooldownTimerWidget
```

---

# 21. Temporal windows — affordances in time

R21 defined affordance relationally. R23 adds temporal conditions.

```text
TemporalAffordance =
action possibility whose availability/effectiveness
depends on temporal relation/window.
```

Useful windows include:

```text
Availability Window
Reaction Window
Execution/Tolerance Window
Vulnerability Window
Cancellation Window
Commitment Window
Information Window
Negotiation Window
```

## 21.1 Window width can encode difficulty

But only if the targeted skill is temporal.

Narrowing every timer is not universal depth.

## 21.2 Windows can overlap

Overlapping opportunity windows create concurrency/choice pressure.

---

# 22. Deadline and timeout

## 22.1 Deadline

```text
Deadline =
temporal boundary after which
legality, value or opportunity set changes.
```

Examples:

```text
vote closes
train leaves
auction ends
hostage is moved
```

## 22.2 Deadline != timer UI

The timer is a cue/representation of the boundary.

## 22.3 Timeout

```text
Timeout =
specified consequence when required action/response
has not completed by a boundary.
```

A deadline may create lower reward rather than timeout.

## 22.4 Deadlines change policy

They can transform:

```text
information acquisition
risk preference
coordination
commitment
```

not merely reaction speed.

---

# 23. Time pressure — temporal scarcity relative to required work

A useful R23 representation is:

```text
TimePressure(subject, decision) grows when
AvailableDecisionWindow
becomes small relative to
time needed for desired deliberation / coordination / execution quality.
```

This is capability-relative.

## 23.1 Same timer, different pressure

Expert and novice may experience different pressure from the same ten-second window.

## 23.2 Time pressure changes cognition

Ben Zur/Breznitz demonstrates in one controlled risky-choice setting that pressure altered information processing and choice.

## 23.3 Time pressure is not always desirable

If motor speed is not the intended question, a short timer may destroy the intended strategic/creative value.

Core rule:

```text
TemporalScarcity should target the intended temporal skill/question.
```

---

# 24. Delay and latency

## 24.1 Delay is general

```text
Delay(A → B) = temporal separation between relevant events A and B.
```

It can be:

```text
world delay
strategic delay
reward delay
information delay
network/system latency
```

## 24.2 Latency is specific

R21's responsiveness work applies to system/input response.

```text
Latency != GameWorldDuration
```

A deliberate one-second spell wind-up can be immediately responsive if feedback acknowledges commitment at once.

## 24.3 Delay can change value

Temporal-discounting research shows that delayed consequences can change choice in many contexts.

R23 does not impose one universal discount curve on players/Subjects.

## 24.4 Information delay can create strategic structure

Old intelligence may be accurate but no longer actionable.

R17's information value therefore includes timeliness.

---

# 25. Initiative and temporal priority

```text
Initiative =
rule-defined priority/opportunity relation
among competing actors/actions.
```

It can be derived from:

```text
fixed order
role
speed stat
bid/resource
prior commitment
random tie-break
alternation
```

## 25.1 Initiative != physical speed

A political chair may speak first by procedure.

## 25.2 First-mover and last-mover advantages differ

Moving first can secure a resource; moving later can reveal information.

Therefore no universal “initiative is good.”

## 25.3 Initiative can itself be contested resource

Players may spend resources to alter order.

---

# 26. Reaction — contingent temporal opportunity

```text
Reaction =
a newly available action whose legality/effect
is triggered by another event and bounded by a response relation/window.
```

Examples:

```text
parry
counterspell
overwatch
interrupt
accept/counteroffer before expiry
```

Reaction is not necessarily real-time.

A turn-based system can create explicit reaction windows.

Therefore:

```text
Reaction != Reflex input
```

---

# 27. Waiting — decompose before removing it

Waiting is:

```text
passage of a relevant temporal frame
without another overt intervention by the participant.
```

It may be voluntary or forced.

R23 distinguishes at least:

## 27.1 Access/dead waiting

```text
nothing relevant changes
no information arrives
no meaningful anticipation/choice exists
```

Usually pure friction.

## 27.2 Process/maturation waiting

```text
resource/world process changes with time
```

Examples:

```text
crop grows
craft completes
weather changes
```

## 27.3 Information waiting

```text
future evidence/signal arrives
```

## 27.4 Strategic waiting

Withholding action changes another Subject's incentives/information/costs.

Preemption and war-of-attrition-like structures show that timing/waiting itself can be strategy.

## 27.5 Synchronization waiting

Waiting aligns with:

```text
teammate
transport
world cycle
shared phase
```

## 27.6 Recovery/cooldown waiting

Capability is temporarily unavailable.

## 27.7 Anticipatory/aesthetic waiting

Suspense, ritual or dramatic pause can carry experience value.

## 27.8 Async dependency waiting

Another human/Agent must respond or a persistent event must occur.

### High-yield test

Waiting is more likely to be meaningful when at least one changes:

```text
World state
Information
Option set
Value/cost
Strategic relation
Synchronization
Anticipation/meaning
```

Otherwise it is likely dead/access time.

---

# 28. Waiting can be an action — but not always

A deliberate policy:

```text
Wait / Hold / Delay commitment
```

can be an Action when choosing not to intervene now changes future possibilities.

But forced idle:

```text
system prevents input for no meaningful reason
```

is not automatically player agency.

Therefore:

```text
No overt movement
!= No action

Forced inactivity
!= Strategic waiting
```

---

# 29. Strategic timing — when can matter more than what

R19 defined Strategy as policy conditioned on others.

R23 adds timing strategies:

```text
act early
act late
wait for information
preempt
commit before rival
let rival reveal first
coordinate simultaneous strike
```

## 29.1 Timing changes role

The same investment/action can create:

```text
leader
follower
late adopter
```

positions.

## 29.2 Waiting can impose/absorb cost

In attrition-like structures, the policy may mainly concern willingness to continue waiting.

## 29.3 Bargaining time

Deadlines, patience, delayed outside options and expiring offers alter bargaining power.

Thus:

```text
Strategy != ActionChoice alone
Strategy may include ScheduleChoice.
```

---

# 30. Temporal Causality

R20 introduced AuthorialCausality.
R21 introduced ActionCausality.
R22 introduced DistributionalAgency.
R23 adds:

```text
TemporalCausality =
important properties of consequence/reachable futures
counterfactually depend on
when, in what order, for how long,
or in what synchronization relation
action/events occur.
```

Formally as a test:

```text
same relevant action content A
schedule τ
versus
schedule τ'

if Outcome/Future(A, τ) != Outcome/Future(A, τ')
for value-bearing properties,
then temporal difference is causal.
```

## 30.1 Temporal causality does not require real-time execution

A turn-order decision can have strong TemporalCausality.

## 30.2 Timing animations are not enough

If moving an animation by 500 ms changes no decision, legality, information or consequence:

```text
PresentationTiming changed
TemporalCausality may not.
```

---

# 31. Temporal Agency

Working definition:

```text
TemporalAgency =
participant's meaningful ability to influence
when/order/duration/synchronization/interruption/reversal
of relevant actions/opportunities
where those choices alter reachable futures.
```

## 31.1 Temporal Agency profile

Do not collapse into one score. Analyze:

```text
Scheduling authority — when to act
Ordering authority — before/after whom
Duration authority — how long to sustain
Rate authority — pause/slow/fast
Synchronization authority — align with what/whom
Interruption authority — cancel/interrupt
Commitment authority — when decision locks
Reversal authority — undo/restore/rewind scope
```

## 31.2 Faster input does not imply more Temporal Agency

Turn-based Chess can have enormous temporal strategic consequence.

## 31.3 Real-time can have low Temporal Agency

If timing is automated and player only chooses one fixed path, world motion can be continuous while timing choice is minimal.

Core rule:

```text
TemporalAgency != ActingFaster
```

---

# 32. Temporal Skill

Temporal skill can include:

```text
Reaction skill
Anticipation/prediction
Phase/rhythm synchronization
Window execution
Sequence planning
Resource timing
Deadline planning
Initiative management
Scheduling/coordination
Patience/waiting strategy
```

Therefore:

```text
ReactionSpeed != AllTemporalSkill
```

## 32.1 Turn-based temporal skill

Examples:

```text
move order
cooldown sequencing
initiative control
planning around future turns
```

## 32.2 Social temporal skill

Examples:

```text
when to reveal information
when to commit
when to respond
when to wait
```

---

# 33. Coordination and synchronization

Temporal coordination is broader than acting at the same instant.

Useful patterns:

```text
Sequential handoff
Barrier / everyone ready
Simultaneous commitment
Simultaneous reveal
Shared deadline
Periodic rendezvous
Soft overlap window
Asynchronous dependency
```

## 33.1 Simultaneous planning reduces observation advantage

Collecting sealed plans before reveal can prevent later submitters from conditioning on earlier visible actions.

## 33.2 Synchronization has cost

Waiting for the slowest participant can create coordination friction.

## 33.3 Loose synchronization can preserve value

If exact simultaneity is not the intended skill, broad windows or role-local execution can avoid unnecessary barriers.

---

# 34. Real-time, turn-based, phased, ticked and asynchronous are composable

These should not be treated as mutually exclusive genres.

## 34.1 Real-time

Relevant world/coordination state advances independently of player action submission.

## 34.2 Turn-based

Action authority is segmented into turns.

## 34.3 Real-time with pause

World progression is real-time while player can alter temporal mapping.

## 34.4 Tick-based

Simulation advances in discrete quanta; player input may be real-time or turn-based relative to ticks.

## 34.5 Phase-based

Rules/opportunities change by phase; phases may contain real-time or turn-based play.

## 34.6 Simultaneous-turn

Participants commit during one coordination window and actions resolve together/later.

## 34.7 Asynchronous

Participants need not be co-present in wall time.

A correspondence chess game is turn-based and asynchronous.
A persistent market is asynchronous without conventional turns.

Therefore:

```text
Asynchronous != TurnBased
RealTime != ContinuousSimulation necessarily
```

---

# 35. Persistent time — world continuity without always-on cognition

Persistence means state/history survives temporal/session boundaries.

It does **not** require:

```text
every object simulated every millisecond
every Agent thinking every tick
```

## 35.1 Event-driven persistence

A world can retain:

```text
state
last update time
scheduled events
```

and derive/catch up relevant changes when needed.

## 35.2 Lazy temporal materialization

If a resource grows predictably:

```text
amount_now = f(amount_then, elapsed_authority_time)
```

continuous tick execution may be unnecessary.

## 35.3 Persistent Agent world

Use:

```text
event scheduling
deadlines
wake-on-relevance
local temporal neighborhoods
commitments
periodic low-cost policies
```

rather than full-model deliberation every tick.

Core rule:

```text
PersistentWorld != AlwaysRunningFullSimulation
PersistentAgent != ThinkEveryTick
```

---

# 36. Pause — selective frame suspension

```text
Pause =
suspend progression in selected temporal frames
while other frames may continue.
```

Examples:

```text
simulation paused
wall time continues
music/UI may continue
network session may or may not continue
```

## 36.1 Pause can be Temporal Agency

If player can choose pause tactically, it changes deliberation budget.

## 36.2 Pause can change the game form

Pausing a real-time system during Agent inference changes temporal pressure and control requirements.

Therefore:

```text
Pause != Neutral presentation feature
```

---

# 37. Replay, Undo, Restore and Rewind

Keep these separate.

## 37.1 Replay

```text
observe/reconstruct retained past
without authoritative state reversal
```

## 37.2 Undo

```text
cancel/compensate a previous command/change
under explicit meta/rule semantics
```

## 37.3 State Restore / Save-Load

```text
replace current state with a previously retained state
```

This can branch the player's play history.

## 37.4 In-world Rewind

```text
temporal reversal is itself represented as world action/mechanic
```

and may preserve selected entities/memory.

Compact rule:

```text
Replay != Undo != StateRestore != InWorldRewind
```

---

# 38. Reversal does not erase all consequence

A major R23 insight:

```text
WorldStateReversal
!=
PlayerKnowledgeReversal
```

The player usually remembers failed attempts after loading an earlier save.

## 38.1 Knowledge can accumulate across reset

This creates:

```text
learning
route optimization
puzzle mastery
prediction
```

while world state repeats.

## 38.2 Real play time also persists

Restoring a game state does not restore the player's spent wall time.

## 38.3 History branches

Two play traces can share an identical world snapshot while differing in player knowledge and discarded branches.

Thus:

```text
SameWorldState != SamePlayHistory
```

## 38.4 Reversibility can support stakes at another layer

Local world loss may be reversible while:

```text
attention
time
knowledge
meta-resource
social commitment
```

remain consequential.

---

# 39. Temporal irreversibility and commitment

Commitment becomes meaningful when later revision is impossible or costly.

```text
Reversibility ↓
→ CommitmentWeight often ↑
```

but not monotonically for player value.

## 39.1 Commitment point

Action can be editable until:

```text
submit
cross threshold
release input
phase closes
```

## 39.2 Irreversibility can create stakes

But too much irreversible uncertainty can suppress experimentation.

## 39.3 Reconsideration is itself temporal design

R18's commitment needs an explicit reconsideration policy:

```text
when may an intention be revised?
```

R23 supplies the temporal boundary.

---

# 40. Temporal fairness

R22 established plural Fairness. R23 adds temporal mechanisms.

## 40.1 Opportunity-window fairness

Do participants receive justified access to relevant windows?

Equal milliseconds are not always required; role/asymmetry may justify differences.

## 40.2 Order fairness

Is initiative/priority determined by a declared and legitimate procedure?

## 40.3 Latency fairness

If network latency changes semantic action priority, geographic/network differences can become hidden gameplay advantage.

## 40.4 Asynchronous fairness

Wall-clock deadlines can privilege time zones or availability patterns.

## 40.5 Resolution fairness

Simultaneous conflicts require stable authoritative semantics.

Core rule:

```text
Fair temporal resolution
!= First packet wins
```

unless that is intentionally part of the game contract.

---

# 41. Temporal Contract

R22 introduced UncertaintyContract.
R23 introduces:

```text
TemporalContract =
which frames advance?
what pauses?
what clock/order is authoritative?
when may actors act?
when do commitments lock?
how are simultaneous conflicts resolved?
what deadlines/windows exist?
what progresses while absent?
what may be reversed?
what timing feedback is promised?
```

## 41.1 Hidden temporal rules damage mental models

Examples:

```text
secret variable cooldown
server deadline differs from displayed timer
hidden pause exceptions
packet arrival unexpectedly defines priority
```

## 41.2 Temporal contracts can be intentionally ambiguous only where ambiguity itself is valued

A horror game may hide exact creature timing but should still preserve enough stable causal structure to support learning if mastery is intended.

---

# 42. Temporal information and signaling

Time itself can carry information.

Examples:

```text
hesitation
instant response
late bid
long silence
attack cadence
cooldown timing
```

R17 therefore extends:

```text
Signal content
+ Signal timing
→ Belief update
```

## 42.1 Timing can reveal policy/type

A player waiting unusually long may signal uncertainty or bluff.

## 42.2 Timing information can be hidden deliberately

Simultaneous sealed commitments prevent one Subject's timing/order from leaking usable information before the other commits.

---

# 43. Time as resource and opportunity

R14 treats resources as stored optionality. Time differs because it often cannot be stockpiled in the same way, but temporal opportunities can still be scarce.

Examples:

```text
one action before deadline
three turns before winter
one reaction window
limited daylight
```

R23 calls this:

```text
TemporalScarcity =
limited time/opportunity relative to desired actions,
attention, deliberation or coordination.
```

## 43.1 Time budget

A time budget may constrain:

```text
number of actions
quality of deliberation
information search
coordination
```

## 43.2 Temporal optionality

Keeping options open longer can itself be valuable.

Commitment often trades future optionality for certainty/position.

---

# 44. Temporal compression — long world time need not require long play time

A game can compress processes through:

```text
summary
fast-forward
skip
event abstraction
turn abstraction
macro command
simulation catch-up
```

Core rule:

```text
WorldDuration != RequiredPlayDuration
```

## 44.1 Preserve causal questions, not every micro-step

If low-level waiting/motion does not carry player value, compress it.

## 44.2 Do not compress the intended temporal skill

If timing/anticipation is the core question, automatic skipping can destroy the game.

This mirrors earlier laws:

```text
Automate friction,
not the intended question.
```

---

# 45. Agent systems — temporal fit, not “real-time intelligence” as universal goal

AI/Agent Game should ask:

```text
What temporal layer carries player value?
```

## 45.1 Sensorimotor Agent

Needs tight observation-action timing and continuous/fast correction.

## 45.2 Tactical/strategic Agent

Can operate on slower decision intervals if world/coordination structure permits it.

## 45.3 Command/delegation Agent

Player may specify:

```text
goal
deadline
constraints
interruptibility
```

while Agent chooses lower-level schedule.

## 45.4 Asynchronous Agent

Can execute over long horizons with:

```text
checkpoint
condition
schedule
deadline
cancel/revoke
notification
```

## 45.5 Inference latency is form-relative

VideoGameBench is a useful falsifier:

```text
slow inference
```

is catastrophic when the intended question is real-time sensorimotor action, but may be irrelevant in correspondence-like or asynchronous forms.

Core rule:

```text
Match Agent decision timescale
to player-value timescale.
```

---

# 46. Temporal Intent for delegated/Agent action

R21 IntentFidelity gains temporal fields.

A delegated action may require:

```text
EarliestStart
Deadline
DurationLimit
Cadence
Priority
Interruptibility
CancellationCondition
RetryWindow
SynchronizationCondition
```

Example:

```text
“Scout the valley before dusk;
return immediately if detected.”
```

contains:

```text
Goal
Deadline
Trigger
Exit condition
```

Temporal intent must survive Agent planning/execution just like target/style/risk intent.

---

# 47. Generated temporal debt

Generative systems create obligations when they speak temporal claims into existence.

```text
Generated duration claim
→ world-time consistency debt

Generated “later” event
→ trigger / scheduling debt

Generated deadline
→ authority / enforcement debt

Generated promise “tomorrow”
→ commitment / calendar debt

Generated recurring plan
→ cadence / cancellation debt

Generated time skip
→ compressed-state-transition debt

Generated simultaneous event
→ conflict-resolution debt

Generated rewind/alternate timeline
→ provenance / history-branch debt
```

The scarce resource is often not prose generation but temporal authority and persistence.

---

# 48. Playable Temporality

R23 adds:

```text
PlayableTemporality =
temporal relations, windows, rates, orderings and mappings
that participants can perceive/model enough to anticipate,
influence, coordinate around or deliberately exploit,
and whose temporal differences alter meaningful future possibilities.
```

`PlayableTime` may be used informally, but `PlayableTemporality` is the more precise term.

## 48.1 Playability does not require clock UI

Players can learn timing from:

```text
animation
sound
world cycles
opponent behavior
phase structure
narrative cues
```

## 48.2 Hidden exact timing can remain playable

A boss need not expose “1.42 s cooldown” if cues support reliable inference.

## 48.3 Unplayable temporality

```text
hidden variable delay
+ no cue
+ no stable rule
+ severe consequence
```

usually feels arbitrary.

---

# 49. Minimum sufficient temporal complexity

This is not a maturity ladder. Choose the cheapest temporal mechanism that preserves the intended question.

## TM0 — Untimed logical order

```text
before / after / dependency
```

No metric clock required.

Useful for:

```text
puzzles
narrative causality
simple workflow
```

## TM1 — Discrete opportunity/order

```text
turn / round / phase
```

Useful when authority/order matter but real duration does not.

## TM2 — Metric windows/durations

```text
deadline
cooldown
wind-up
reaction window
```

Adds timing skill/risk.

## TM3 — Concurrent/joint resolution

Adds partial order, simultaneous commitment and conflict-resolution semantics.

## TM4 — Multiple mapped temporal frames

Adds pause/fast-forward/fictive jumps/persistent mappings.

## TM5 — Persistent asynchronous temporal ecology

Adds durable schedules, offline progression, multi-Subject clocks/deadlines and long-horizon Agent commitments.

Core rule:

```text
Increase temporal complexity
only when it creates a new playable temporal counterfactual.
```

---

# 50. Cross-form falsification tests

## 50.1 Chess without clock

```text
Turn order strong
Metric wall-time weak/nonbinding
Motor timing minimal
Temporal strategic order high
```

Therefore:

```text
TemporalAgency != Realtime reflex
```

## 50.2 Chess with clock

Adds a real/coordination deadline mapping.

Same board rules, different temporal game.

Time pressure changes policy because deliberation becomes scarce.

## 50.3 Fighting game

```text
startup / active / recovery
reaction/cancel windows
opponent timing
```

TemporalCausality is central.

A faster animation is not automatically deeper; stable windows and counterplay matter.

## 50.4 Rhythm game

Tempo and rhythm separate. Skill includes phase synchronization, anticipation and correction.

## 50.5 RTS

World time advances continuously while player issues higher-level commands. Real-time does not require every unit decision to be direct human motor control.

Pause/slow-speed options alter deliberation and therefore the temporal contract.

## 50.6 Simultaneous-order strategy

Players commit plans without observing each other's current choice, then resolve jointly.

This separates:

```text
CommitTime
RevealTime
ResolutionOrder
```

## 50.7 Poker / card play

Turn/round/phase structure organizes information revelation, betting rights and commitment. Deliberation clocks can add temporal scarcity without changing card probabilities.

## 50.8 Attrition/preemption-like strategy

Waiting or moving early is itself strategic action. This falsifies:

```text
Waiting = no gameplay
```

## 50.9 XCOM-like turn-based tactics

No real-time motor pressure is required for:

```text
cooldown sequencing
turn order
reaction fire
future-turn planning
```

## 50.10 Persistent MMO/social world

World and social opportunities can continue while one player is absent. Auctions, crafting, respawn waves and scheduled events create multiple temporal frames.

## 50.11 Idle game

Offline time can be part of production/progression. It is a direct counterexample to “waiting is inherently bad.”

But if return calculation can reproduce the same state, full continuous simulation is unnecessary.

## 50.12 Creative tool / sandbox

Pause, undo and version restore can strengthen experimentation and authorship. Real-time pressure is optional unless temporal execution is itself the creative medium.

## 50.13 Mystery / Casefile-like form

The crime may have fixed fictive chronology while the player's evidence-discovery order differs.

```text
EventChronology != DiscoveryOrder
```

## 50.14 Rewind puzzle

In-world temporal reversal can be a mechanic while player memory survives, producing new reachable futures from previously learned information.

## 50.15 SillyTavern-like roleplay

Conversation turn-taking is one coordination frame; one utterance can advance fictive time minutes, days or years.

Natural-language turn count is not world duration.

## 50.16 AI companion

Player command may occur in a turn-like interaction while Agent execution unfolds across world time. Interrupt/cancel/deadline semantics become more important than token latency alone.

## 50.17 Persistent Agent world

Full cognition every tick is unnecessary and often harmful. Durable event scheduling, local wakeups and commitments can preserve temporal coherence more cheaply.

## 50.18 Real-time VLM action agent

Inference latency may destroy intended sensorimotor timing. Pausing the environment converts the task into another temporal form rather than simply “making the same game easier.”

---

# 51. Major collapse / failure modes

## 51.1 Time = seconds collapse

Failure: all temporal structure represented by one numeric `t`.

Result: turns, causal order, fictive time, subjective time and coordination disappear.

## 51.2 One global clock collapse

Failure: assume every subsystem/player/narrative event shares one temporal frame.

Result: pause, async, persistence and time skips become awkward hacks.

## 51.3 Clock order = causal order collapse

Failure: earlier timestamp always treated as semantic cause/priority.

Result: transport timing leaks into game rules.

## 51.4 Arrival order = fairness collapse

Failure: first packet wins every conflict.

Result: network geography becomes hidden initiative.

## 51.5 Simultaneity = concurrency collapse

Failure: overlapping/independent processes forced into same timestamp semantics.

Result: incorrect conflict reasoning.

## 51.6 Concurrent = arbitrarily sequential collapse

Failure: implementation serialization becomes canonical event order.

Result: accidental first-mover advantage.

## 51.7 Turn = tick collapse

Failure: player authority window confused with simulation quantum.

Result: implementation granularity leaks into design ontology.

## 51.8 Phase = turn collapse

Failure: rule regime treated as one actor's opportunity.

Result: planning/reveal/resolution structure becomes unclear.

## 51.9 Duration = timing collapse

Failure: long action assumed to require precise timing.

Result: temporal skill misidentified.

## 51.10 Tempo = rhythm collapse

Failure: same average speed assumed same temporal pattern.

Result: phase/pattern skill disappears.

## 51.11 Pacing = tempo collapse

Failure: increase event rate to fix flat macro experience.

Result: faster monotony.

## 51.12 Faster = more exciting collapse

Failure: shorten every interval.

Result: anticipation, weight, planning and legibility can disappear.

## 51.13 Real-time = more agency collapse

Failure: continuous world advancement assumed higher player control.

Result: turn-based strategic agency discounted.

## 51.14 Lower latency = universally better timing collapse

Failure: remove intentional wind-up/inertia alongside system lag.

Result: materiality/fantasy/counterplay lost.

## 51.15 Cooldown = arbitrary waiting collapse

Failure: all temporary unavailability treated as one timer.

Result: recovery, opportunity, commitment and resource structure obscured.

## 51.16 Waiting = dead time collapse

Failure: remove maturation, strategic, synchronization or anticipatory waiting.

Result: valid temporal questions erased.

## 51.17 Forced waiting = strategy collapse

Failure: unavoidable idle delay labeled meaningful merely because state eventually changes.

Result: access friction disguised as gameplay.

## 51.18 More time pressure = more difficulty/depth collapse

Failure: shrink timer regardless of intended skill.

Result: deliberative/creative value replaced by haste.

## 51.19 Deadline = timer widget collapse

Failure: UI countdown treated as authoritative rule.

Result: display drift and hidden semantic boundaries.

## 51.20 Pause = no consequence collapse

Failure: assume pause is neutral.

Result: deliberation budget and Agent feasibility changes ignored.

## 51.21 Replay = state reversal collapse

Failure: observing past changes authoritative state.

Result: history/evidence semantics blur.

## 51.22 Undo = save/load collapse

Failure: command cancellation and snapshot restore treated identically.

Result: branching/history responsibility unclear.

## 51.23 Save/load = in-world rewind collapse

Failure: meta persistence becomes character/world power.

Result: fiction and authority conflict.

## 51.24 State reversal = knowledge reversal collapse

Failure: restored world assumed to erase player learning.

Result: time-loop/mastery structures misunderstood.

## 51.25 Persistence = continuous computation collapse

Failure: simulate everything every tick because world persists.

Result: massive cost without player-facing distinction.

## 51.26 Agent = think every tick collapse

Failure: each persistent Agent repeatedly invokes expensive cognition at fixed frequency.

Result: temporal scalability failure and incoherent micro-drift.

## 51.27 Agent latency hidden by arbitrary freeze

Failure: world secretly pauses for model calls without exposing that temporal contract.

Result: world dynamics and agency become inconsistent.

## 51.28 Async = turn-based collapse

Failure: all asynchronous interaction modeled as strict alternating turns.

Result: event-driven markets/social systems misrepresented.

## 51.29 Story chronology = presentation order collapse

Failure: flashback/reveal order treated as world event order.

Result: narrative causal model breaks.

## 51.30 Objective duration = experienced duration collapse

Failure: seconds used as direct proxy for boredom/tension/value.

Result: player experience mis-modeled.

## 51.31 Delay = neutral offset collapse

Failure: postpone consequence without considering information, preference, risk or commitment effects.

Result: materially different choices treated equivalent.

## 51.32 Initiative = speed collapse

Failure: fast character always semantically acts first.

Result: institutional/procedural priority ignored.

## 51.33 Reaction = reflex collapse

Failure: every contingent response window implemented as real-time button test.

Result: turn-based/strategic reactions excluded.

## 51.34 More temporal complexity = more depth collapse

Failure: add clocks, phases, cooldowns and schedules without new counterfactuals.

Result: temporal bureaucracy.

---

# 52. R23 connections back to R1–R22

## R1 — GameForm

Time is now decomposed beyond real-time/turn-based labels into temporal frames, ordering, mapping, windows and reversibility.

## R2 / R5 / R6 — Player Value

Temporal structure can carry mastery, anticipation, reflection, social coordination, suspense and ritual; raw play duration remains non-value by itself.

## R3 — Mechanics

Mechanics may have temporal guards, intervals and resolution order. An action is not necessarily instantaneous.

## R4 — Loops

Loops occur across nested temporal scales. Loop frequency is not loop quality.

## R7 — Tension / pacing

Pacing remains macro distribution. Time pressure is temporal scarcity; more speed/variance is not automatically more tension.

## R8 — Narrative

Fictive chronology, presentation order and play order can differ. Time skips need not simulate every intervening state.

## R9 — World

World dynamics require progression semantics but not necessarily continuous real-time simulation.

## R10 — Subject / Agent

Subject policies can include schedule, waiting, deadline and temporal commitments. Agents need not deliberate every tick.

## R11 — Agency

Temporal Agency is a distinct dimension of influence over when/order/duration/synchronization/reversal.

## R12 — Feedback / learning

Timing windows and delays must be legible enough for calibration when temporal skill is intended.

## R13 — History / persistence

History depends on ordered traces. State restore can branch play history; persistent state need not mean continuous computation.

## R14 — Resource / scarcity

Time opportunities can be scarce; waiting, deadlines and production rates transform resource optionality.

## R15 — Institution

Institutions define schedules, terms, deadlines, priority, office duration and procedures — temporal rules transform social games.

## R16 — Space / topology

Reachability often depends jointly on space and time: route may be reachable only before a window closes.

## R17 — Information

Information has arrival time and expiry. Signal timing itself can carry information.

## R18 — Motivation / commitment

Goals/intention require temporal persistence and reconsideration boundaries; delayed consequences can change preference without requiring one universal discount model.

## R19 — Strategy

Timing, patience, preemption, deadlines and turn order can be strategic variables. Waiting can be policy.

## R20 — Creation

Creative work often benefits from reversible iteration/versioning; temporal pressure is optional unless timing/rhythm is part of the medium.

## R21 — Control

Latency/responsiveness is only one temporal relation. Timing fidelity becomes part of IntentFidelity; action stages create windows/counterplay.

## R22 — Uncertainty / risk

Risk evolves through time: information arrives, hazards accumulate, deadlines close, options decay. Realization timing relative to commitment remains first-class.

---

# 53. New high-yield abstractions

## 53.1 Temporal Frame

```text
Events / Processes
+ Temporal Relations
+ optional Metric
+ Progression Rule
```

## 53.2 Temporal Mapping

```text
mapping between wall/gameworld/coordination/fictive/subjective frames
```

can pause, scale, jump or be action-triggered.

## 53.3 Temporal Causality

```text
same substantive action
+ different time/order/duration/synchronization
→ materially different future
```

## 53.4 Temporal Agency

```text
meaningful influence over schedule/order/duration/rate/synchronization/interruption/reversal
```

## 53.5 Temporal Affordance

```text
action possibility whose legality/effectiveness depends on temporal relation/window
```

## 53.6 Temporal Scarcity

```text
available temporal opportunity is insufficient for all desired action/deliberation/coordination
```

## 53.7 Temporal Contract

```text
what advances, pauses, resolves first, expires, persists, can be reversed and which clock/order is authoritative
```

## 53.8 Commutativity test

```text
if action order does not alter result, do not manufacture order significance;
if it does, specify resolution semantics.
```

## 53.9 Persistence without continuous computation

```text
stored state + authority time + scheduled rules
can reproduce persistent evolution lazily.
```

## 53.10 State reversal versus knowledge/history

```text
WorldStateReversal != PlayerKnowledgeReversal
SameWorldState != SamePlayHistory
```

## 53.11 Playable Temporality

```text
temporal structure becomes playable when it can be modeled/anticipated/influenced
and timing differences alter valued futures.
```

---

# 54. Direct answers to the R23 continuation questions

### What kinds of Time exist in a game?

Do not start from one clock. Use temporal frames such as wall time, gameworld/simulation time, coordination time, fictive time and subjective time, adding an authority relation where rules need an exact temporal reference.

### What is Sequence relative to Time?

Sequence is order. It can be meaningful without metric duration. A before B can change causality even if no seconds are assigned.

### What is Simultaneity relative to Concurrency?

Simultaneity is a semantic same-time/joint-resolution relation. Concurrency means events are not fully causally ordered and may overlap. Concurrent events need not be simultaneous.

### Turn, Phase and Tick?

Turn grants bounded action/decision authority; Phase changes legal/coordination regime; Tick is a simulation/update quantum. They can be composed but should not be equated.

### Duration, Timing, Tempo, Rhythm and Pacing?

Duration is interval extent; Timing is placement relative to an event/window; Tempo is rate/density; Rhythm is patterned interval/phase relation; Pacing is macro distribution of tension/decisions/feedback/recovery.

### What are cooldown, wind-up and recovery?

Different temporal constraints around an action protocol. Wind-up precedes effect after commitment; recovery follows effect and constrains action; cooldown prevents reuse until a later condition.

### What is a Deadline?

A temporal boundary after which legality, value or options change. The countdown UI is only a representation.

### What is Waiting?

Passage of relevant time without overt intervention. It can be dead friction, maturation, information acquisition, strategy, synchronization, recovery, anticipation or asynchronous dependency. Waiting becomes player action when choosing to wait changes futures.

### How do deadlines change decisions?

They create temporal scarcity and can alter information search, deliberation, coordination, risk and commitment — not merely execution speed.

### What is Initiative?

Rule-defined temporal priority/opportunity among competing actors/actions; it may derive from procedure, role, resource, speed or random tie-break and is not synonymous with physical speed.

### How should simultaneous actions resolve?

First ask whether actions commute. If not, define priority, joint transition, allocation or conflict semantics. Do not inherit network arrival order accidentally.

### What is Temporal Agency?

Ability to influence timing/order/duration/synchronization/interruption/reversal where those temporal choices materially alter reachable futures.

### Is real-time more agentic than turn-based?

No. Real-time describes progression/coordination structure; temporal agency depends on meaningful timing influence. Turn-based games can have deep timing/initiative/commitment strategy.

### How does pause affect a game?

Pause changes mapping among temporal frames and often changes deliberation budget, pressure and Agent feasibility. It is not always neutral presentation.

### Replay, Undo, Save/Load and Rewind?

Replay observes past; Undo cancels/compensates; State Restore replaces current state from retained state; In-world Rewind is a represented temporal mechanic. Their history/knowledge consequences differ.

### Does persistence require continuous simulation?

No. Event schedules and elapsed-time materialization can preserve equivalent state evolution more cheaply when no intermediate event needs player-facing causality.

### How should Agent systems handle time?

Match decision timescale to player-value timescale and represent temporal intent explicitly: start, deadline, cadence, interruption, cancellation and synchronization. Do not invoke expensive cognition every tick without evidence.

---

# 55. Explicit non-conclusions

R23 does **not** establish that:

- every game needs metric time;
- every game needs multiple physical clocks;
- real-time is superior to turn-based;
- turn-based is better for AI by definition;
- higher tick rate means deeper simulation;
- faster input creates more agency;
- all actions should expose startup/recovery data numerically;
- narrower timing windows always create more skill;
- more time pressure means more tension/depth;
- waiting is inherently bad;
- waiting is inherently meaningful;
- every cooldown is good design;
- all delays should be removed;
- all latency can be justified as materiality;
- pause is always desirable;
- pause is always neutral;
- save/load removes consequence;
- rewind erases player knowledge;
- persistent worlds require always-on simulation;
- persistent Agents should think continuously;
- simultaneous actions should resolve by timestamp;
- equal timing windows are always fair;
- one global clock should own every temporal rule;
- subjective duration can be derived directly from clock duration;
- temporal discounting has one universal function for all players;
- narrative chronology must match presentation order;
- more temporal systems mean more depth.

The governing criterion remains player-facing causal value.

---

# 56. R23 synthesis

The deepest compression of R23 is:

```text
Time in games is not one clock.

Temporality is structure among events/processes:
order,
duration,
rate,
windows,
synchronization,
commitment,
and mappings among temporal frames.
```

A compact temporal stack is:

```text
Temporal Frames
        ↓
Opportunity / Window
        ↓
Intent
        ↓
Commitment
        ↓
Action Interval / Order / Synchronization
        ↓
Resolution
        ↓
Consequence
        ↓
Feedback
        ↓
History / New Availability
        ↺
```

R23's strongest ordering rule is:

```text
ClockOrder != CausalOrder.
```

The strongest control rule is:

```text
TemporalAgency != ActingFaster.
```

The strongest simulation rule is:

```text
Persistence != ContinuousComputation.
```

The strongest reversal rule is:

```text
WorldStateReversal != PlayerKnowledgeReversal.
```

The strongest experiential rule is:

```text
ClockDuration != ExperiencedDuration != RememberedDuration.
```

The strongest Agent rule is:

```text
Match Agent decision timescale to player-value timescale.
```

R23 adds:

```text
TemporalFrame
TemporalMapping
TemporalCausality
TemporalAgency
TemporalAffordance
TemporalScarcity
TemporalContract
PlayableTemporality
```

to the foundation vocabulary.

---

# 57. Unresolved questions left by R23

With temporal structure isolated, one conspicuously under-modeled component remains at the beginning of the Subject stack: **Identity**.

R10 separated Object / Actor / Subject / NPC / Agent / Player, and later rounds repeatedly use Identity, role, persona, status and reputation, but they have not been decomposed from first principles.

Important unresolved questions include:

1. What is Identity relative to persistent state, memory, body, role and social recognition?
2. What is Character relative to Subject, Persona and Avatar?
3. What is a Role: capability bundle, social expectation, institutional position, narrative function or all of these?
4. What is Persona relative to generated surface behavior and deeper policy/value continuity?
5. What makes a Subject “the same one” through change, body swap, memory loss, rewind or cloning?
6. How do self-identity and observer-assigned identity differ?
7. What is Status relative to Reputation, Rank, Role and Power?
8. How does Reputation differ from identity when reputation is observer-relative belief?
9. Which changes count as development versus identity break?
10. How do disguises, aliases, secret identities and roleplay create playable identity uncertainty?
11. How does identity constrain Goals, Commitments, Relationships and Institutions?
12. What is player identification versus Avatar/Body ownership from R21?
13. How does authorship/self-expression from R20 become identity over repeated history?
14. How should generative Personas maintain continuity without freezing all variation?
15. What provenance is required when one Agent/character is reconstructed across sessions/models?
16. How do collective identities differ from organizations and individual Subjects?

---

# 58. Exact next foundation round

The next foundation round should be:

```text
R24 — Identity, Character, Role, Persona, Self, Status, Reputation, Continuity and Transformation
```

The transition is:

```text
R23:
How are actions and consequences ordered through time?

→ R24:
What makes a Subject, character or collective count as the same entity
through time, transformation, role change and social recognition?
```

R24 should connect R10 Subject/Agent, R13 memory/history, R15 institutions, R18 values/commitment, R19 reputation/strategy, R20 expression/authorship, R21 embodiment and R23 continuity without collapsing identity into a name, avatar or memory store.

Do not select a product before R24 and the remaining obvious foundation dimensions have been examined and later synthesized.
