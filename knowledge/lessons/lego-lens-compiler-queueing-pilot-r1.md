# LEGO Lens Compiler — Queueing Theory Shadow Pilot R1

Date: 2026-09-18
Status: SHADOW COMPLETE / CANDIDATE NOT PROMOTED

## Question

Should queueing theory / operations research become an active LEGO lens for the current Ordivon Agent Service capacity and throughput problem?

## Target decision

Decide whether the next Agent Service architecture slice should add queue/capacity scheduling machinery or a permanent lego-queueing lens.

## Evidence boundary

Current local evidence includes:

- Agent Service R14 source integration and provider-admission standing;
- Agent Service R16 read-only deployment canary;
- the existing LangSmith Agent Service kernel study showing a durable Run + worker/queue architecture pattern;
- no new production load test or provider effect was run for this pilot.

This is a meta-method shadow test, not production capacity evidence.

## Problem signature

Observed/relevant coordinates:

- durable run/work identity: YES;
- background worker execution: structurally relevant;
- queue/wake-up substrate: relevant as replaceable transport;
- end-to-end accepted-throughput funnel: explicitly identified as future instrumentation;
- measured arrival rate: NOT AVAILABLE;
- measured service-time distribution: NOT AVAILABLE;
- measured queue length / wait time: NOT AVAILABLE;
- measured worker utilization: NOT AVAILABLE;
- demonstrated capacity saturation: NOT AVAILABLE;
- current provider admission blocker: YES — CHALLENGE_GATED in the R14 evidence;
- current R16 surface: read-only canary, no production provider effect.

## Existing-lens coverage

Existing LEGO lenses already cover:

- feedback/control stability -> lego-feedback-control;
- authority/failure interaction -> STPA/FMEA/Agent Security;
- lifecycle and service boundary -> systems engineering/compositional contracts;
- current regime/admission propagation -> regime-shift lens.

Uncovered residue would be **quantitative capacity/waiting behavior under real load**, if such a bottleneck becomes evidenced.

## Candidate discipline

Queueing theory / operations research.

Mature source anchors used for this pilot:

- John D. C. Little (1961), *A Proof for the Queuing Formula: L = λW*, Operations Research.
- John D. C. Little (2011), *Little's Law as Viewed on Its 50th Anniversary*, Operations Research.
- Kim & Whitt (2013), *Statistical Analysis with Little's Law*, Operations Research.

The 2013 work is particularly relevant to the warning that finite-time operational measurements need statistical treatment rather than naive steady-state substitution.

## Primitive mapping / type-check

| Agent Service target | Queueing primitive | Current standing |
|---|---|---|
| admitted durable Run/Task | customer/job arrival | structurally plausible |
| eligible execution worker | server | structurally plausible |
| pending admitted work | queue/work in process | structurally plausible |
| admission -> dispatch delay | waiting time | measurable in principle |
| dispatch -> terminal execution | service time | measurable in principle |
| total admitted work in system | L / work in process | measurable in principle |
| accepted arrival rate | λ | not currently measured for the real service |
| mean time in bounded system | W | not currently measured for the real service |
| worker busy fraction | utilization | not currently measured |
| semantic acceptance | downstream outcome, not automatically queue service completion | must remain separate |

### Type-check verdict

**PARTIAL PASS.**

The core queue primitives map cleanly enough to justify future measurement.

However, the semantic return path is not yet complete because:

1. worker completion is not the same as provider/domain semantic acceptance;
2. current evidence does not establish stationarity or a stable arrival/service process;
3. current production-like throughput is blocked upstream/downstream by provider admission;
4. no saturation, queue growth, or waiting-time failure has been demonstrated.

Therefore a full queueing model is premature.

## Baseline comparison

Without the candidate lens, current Agent Service work already says:

- instrument the end-to-end accepted-throughput funnel;
- provider admission is currently CHALLENGE_GATED;
- preserve durable run truth separately from queue wake-up;
- do not infer semantic success from transport/execution progress.

Queueing theory adds one unique improvement:

> when throughput instrumentation is introduced, measure explicit arrival, work-in-process, waiting, service and utilization coordinates rather than a single aggregate throughput number.

It does **not** currently justify:

- another queue implementation;
- worker-pool expansion;
- M/M/1 or M/M/c assumptions;
- scheduler optimization;
- a permanent active LEGO queueing skill.

## Minimal future instrumentation

If capacity becomes a real frontier, capture at least:

~~~text
intent_at
admitted_at
queued_at
dispatch_at
execution_terminal_at
provider_effect_observed_at
semantic_acceptance_at

queue_length_at_dispatch
eligible_worker_count
busy_worker_count
retry/replay identity
provider/admission standing
~~~

Then keep separate:

~~~text
queue wait
execution service time
provider wait
semantic acceptance latency
~~~

Only after the bottleneck is localized should a queueing model be chosen.

## Lifecycle verdict

~~~text
candidate discipline     QUEUEING THEORY / OPERATIONS RESEARCH
type check               PARTIAL_PASS
shadow value             POSITIVE_BUT_NOT_CURRENTLY_DECISION_CHANGING
permanent skill          NOT_CREATED
active lens              NOT_PROMOTED
standing                 RESERVE_POOL / REACTIVATE_ON_MEASURED_CAPACITY_FRONTIER
~~~

## Why this pilot matters

This is a useful Lens Compiler outcome precisely because it rejects premature adoption.

The method:
- discovered a mature external discipline;
- established a valid structural mapping;
- extracted a concrete future measurement improvement;
- detected that current evidence does not support the discipline's stronger models;
- refused to expand the active lens set.

That is stronger than either "ignore queueing theory" or "create a queueing lens because workers exist."

## Promotion trigger

Reopen only when real evidence shows at least one of:

- persistent queue growth;
- waiting latency dominates end-to-end latency;
- worker utilization/capacity constrains accepted throughput;
- admission/scheduling policy materially changes backlog or latency;
- capacity allocation among task classes becomes a real decision.

Until then, STOP.
