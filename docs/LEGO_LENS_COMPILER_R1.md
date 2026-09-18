# LEGO Lens Compiler R1

Date: 2026-09-18
Status: ACTIVE EXPERIMENTAL META-LAYER R1

## Purpose

LEGO Lens Compiler turns the open-ended observation that "many mature disciplines can be useful lenses" into a controlled engineering process.

The candidate theory space may be extremely large. The active lens set must remain small.

The compiler therefore owns five things:

1. accept one bounded `NO_LENS_METHOD_GAP` residue from LEGO Lens Router;
2. search mature external disciplines for a missing rigorous operator;
3. type-check and compile a thin temporary candidate adapter;
4. test whether the candidate creates unique decision value;
5. return source/evidence/lifecycle material to Lens Router's normal registry-admission process.

It does **not** own active-lens selection, MSTS, the lens registry, project truth, domain authority, or LEGO Core.

## Architecture

```text
raw problem
  |
  v
LEGO Question Compiler
  |  localizes uncertainty / decision
  v
Problem Signature
  |
  v
LEGO Lens Router
  | existing fit / DOMAIN_METHOD
  +-------------------------------> execute natural owner
  |
  | NO_LENS + material method gap
  v
Lens Compiler
  | source-grounded thin candidate
  v
Type Check
  | reject metaphor-only
  v
Shadow / Prospective Comparison
  |
  v
Router Registry Admission
  |
  +--> ACTIVE / MERGE / RETIRE / RESERVE
```

Question Compiler asks **what needs to be known**.

Lens Router asks **which existing method naturally owns it**.

Lens Compiler asks **whether a missing rigorous method should be imported from an external discipline**.

Project/domain owners decide **what becomes truth or action**.

## Structural signature

The signature is not a universal ontology. It is inherited from Question Compiler -> Lens Router and remains evidence-bound. Compiler may refine only the uncovered residue needed for source discovery; it must not invent signals to make a favorite discipline fit.

Useful reserve-pool discovery coordinates include:

| Signature | Mature method families often worth considering |
|---|---|
| dynamic state, delay, disturbance, regulation | control theory, dynamical systems, system identification |
| strategic adaptation, incentives, hidden information | game theory, mechanism design, behavioral/experimental economics |
| causal intervention, mechanism, confounding | causal inference, experimental design, statistics |
| capacity, waiting, contention, service rates | queueing theory, operations research, scheduling |
| constrained allocation, trade-offs | optimization, operations research, decision analysis |
| uncertainty over sequential choices | decision theory, Bayesian methods, bandits, stochastic control |
| dependency topology, cascades, diffusion | graph theory, network science, percolation/epidemic models where assumptions fit |
| component failure and top events | reliability engineering, FMEA/FMECA, FTA |
| unsafe interactions/control | STAMP/STPA |
| information leakage, channels, observability | information-flow security; information theory only when quantities/operators are meaningful |
| distributed agreement/replication/failure | distributed systems, consensus/fault models |
| measurement, calibration, construct validity | metrology, measurement theory, psychometrics where applicable |
| human action, perception, interface | HCI, cognitive science, human factors, behavioral science |
| organization, autonomy, coordination, adaptation | organizational theory, organizational cybernetics |
| open-ended concept/design search | design theory, C-K, evolutionary search after evaluator validity |
| lifecycle, interfaces, whole-system outcomes | systems engineering |
| dense coupling and rework | DSM / architecture dependency methods |

This table is a discovery map, not an activation checklist.

## The type-check

A candidate lens must supply an explicit partial mapping:

```text
target objects/relations/observations/interventions
            |
            | phi
            v
discipline primitives + assumptions + operators
            |
            | analysis
            v
discipline result
            |
            | psi
            v
target evidence / experiment / decision consequence
```

The candidate passes only when:

1. **Primitive fit** — target objects map to meaningful source objects rather than rhetorical analogies.
2. **Assumption fit** — required source assumptions are satisfied, testable, or explicitly bounded.
3. **Operator fit** — using the source method does not silently change the meaning of the target variables.
4. **Observability fit** — relevant inputs and outputs can actually be measured or evidenced.
5. **Decision return path** — the result maps back to a real decision, failure test, or experiment.

If the only mapping is "X resembles Y", classify **METAPHOR_ONLY**.

### Examples

Good candidate:
- worker arrivals + service-time distribution + finite executors + wait time -> queueing model -> capacity/admission experiment.

Bad candidate:
- "the organization has entropy" with no defined state space, probability model, entropy quantity, measurement procedure, or decision consequence.

Good candidate:
- replicated services + crash/partition assumptions + quorum rule -> distributed-systems model -> explicit safety/liveness tests.

Bad candidate:
- "teams behave like quantum particles" because both are uncertain.

## Lens card contract

Every compiled temporary lens must state:

1. target decision;
2. activation;
3. source discipline and authoritative references;
4. target-to-source primitive mapping;
5. assumptions;
6. inputs/evidence;
7. operators;
8. outputs;
9. falsifiers / invalidating conditions;
10. non-claims;
11. promotion law;
12. stop condition.

Use `templates/LEGO_LENS_CARD_R1.md`.

## Lifecycle

### CANDIDATE

Source-grounded and type-checked, but not yet demonstrated on a real case.

### SHADOW

Applied beside the current method. It has no independent authority to alter project state.

### PROSPECTIVE

A validation case and expected value test are declared before observing the result.

### ACTIVE

Registry outcome only: retained as an optional lens after demonstrating unique value and passing Lens Router's admission/overlap contract. Compiler cannot self-assign this state.

### MERGE

Registry outcome: the useful procedure is absorbed into an existing lens because separate routing adds no unique value.

### RETIRE

Registry outcome: the lens repeatedly adds vocabulary or cost without unique decision value, or its assumptions do not survive real cases.

Compiler can recommend these outcomes but does not mutate the registry. No lifecycle state promotes theory vocabulary into the shared LEGO schema automatically.

## Evaluation

A candidate earns retention when it repeatedly produces at least one unique outcome:

- decision changed;
- boundary/edge corrected;
- hidden failure/hazard exposed;
- invalid analysis/application prevented;
- falsifiable experiment created;
- uncertainty measurably reduced;
- analysis cost materially reduced;
- justified no-change that a cheaper existing lens would not have supplied.

A "justified no-change" should not preserve a lens indefinitely. It must remain discriminating and unique.

## Relationship to Lens Router competition and composition

Lens Router owns active-lens competition, Minimum Sufficient Theory Set selection, and composition. Compiler performs only the overlap audit needed to show that a new candidate is not a synonym.

Multiple lenses may ultimately be composed by Router when they answer different typed questions.

Example:

```text
systems engineering -> establish system boundary
queueing theory      -> model capacity/waiting inside that boundary
causal intervention  -> test whether a scheduling change caused latency reduction
STPA                  -> test whether the new admission policy creates unsafe control
```

Do not activate all of them by default.

When two lenses produce substantially the same output on repeated cases, prefer:
- the one with stronger source authority;
- fewer assumptions;
- lower evidence/execution cost;
- clearer falsifiers;
- broader demonstrated transport without semantic loss.

The loser should MERGE or RETIRE.

## Reflexive control

Lens Compiler can analyze Lens Compiler, but cannot self-certify.

Required safeguards:
- freeze the target compiler version before evaluation;
- preserve baseline routing/output;
- use unrelated cases;
- count rejected/non-applicable lenses as legitimate outcomes;
- compare actual decision/experiment deltas, not rhetorical depth;
- retain rollback;
- periodically audit active-lens routing/context cost.

## Relationship to LEGO Core

Core remains thin.

Lens Compiler introduces:
- no mandatory project-plan field;
- no universal cross-discipline ontology;
- no requirement to run every lens;
- no parallel registry.

The existing `knowledge/registries/lego-lens-registry-r1.json` remains Lens Router-owned. Compiler produces candidate evidence for that admission path rather than a second catalog.

## R1 acceptance

R1 is useful only if prospective use demonstrates at least one of:

- discovers a mature method the active lens set missed;
- rejects a seductive but invalid metaphor;
- routes away from a redundant lens;
- produces a smaller/stronger experiment than ad-hoc reasoning;
- retires or merges a lens because marginal value is low;
- reduces active-lens context/routing cost without losing decision quality.

## Non-goals

- no Wave 4 created merely to add disciplines;
- no "theory of everything";
- no requirement that every problem have a mathematical model;
- no fake rigor by renaming ordinary reasoning with academic vocabulary;
- no claim that cross-domain structural similarity proves causal or mechanistic identity;
- no replacement for the mature source discipline.

## Initial reserve-pool examples

Potential source disciplines include, non-exhaustively:

- mathematics/formal: probability, optimization, graph theory, dynamical systems, game theory, category theory;
- engineering: systems, control, reliability, operations research, distributed systems, software architecture, human factors;
- information/computation: information theory, information-flow security, algorithms, complexity, databases, programming languages;
- natural sciences: ecology, evolution, epidemiology, statistical physics — only when their assumptions/operators type-check;
- social/behavioral: economics, mechanism design, organizational theory, sociology, cognitive science, psychology, HCI;
- design/decision: C-K, decision analysis, Bayesian decision theory, experimental design, forecasting.

Reserve-pool membership means only "worth searching when the problem signature matches." It is not lens activation.

## Canonical local references

- `docs/LEGO_THEORY_LAYER_R1.md`
- `docs/LEGO_QUESTION_COMPILER_R1.md`
- `docs/LEGO_LENS_ROUTER_R1.md`
- `knowledge/registries/lego-lens-registry-r1.json`
- `knowledge/lessons/lego-wave23-self-audit-r1.md`

## R1 shadow pilot standing

First shadow case:

- `knowledge/lessons/lego-lens-compiler-queueing-pilot-r1.md`
- `evidence/acceptance/lego-lens-compiler-shadow-pilot-r1.json`

Candidate discipline: queueing theory / operations research.

Result:

- primitive mapping to durable work, workers, waiting and service time is structurally plausible;
- current Agent Service evidence does not contain the arrival/service/utilization/queue measurements required for a serious capacity model;
- provider admission and semantic acceptance remain separate from queue service completion;
- current frontier is not demonstrated queue saturation;
- the compiler therefore retained queueing theory in the reserve pool and **did not create a permanent active queueing lens**.

This is a positive R1 result because it demonstrates discovery plus rejection of premature activation rather than monotonic lens accumulation.
- docs/LEGO_LENS_UNIVERSE_R1.md
