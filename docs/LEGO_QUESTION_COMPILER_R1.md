# LEGO Question Compiler R1

Date: 2026-09-18
Status: ACTIVE EXPERIMENTAL ANALYSIS LENS R1

## Purpose

LEGO Question Compiler turns an initially vague, narrative, overloaded, or solution-shaped prompt into a small set of evidence-bound questions that can change a real decision.

It is not a universal ontology, research-question database, backlog generator, prioritization authority, or replacement for domain methods.

The central transformation is:

```text
vague question
-> bind target + decision + evidence boundary
-> separate observed / inferred / unknown
-> expose hidden state, mechanism, strategy, feedback and counterfactual structure
-> generate candidate questions
-> prune by decision value and discriminating power
-> bind surviving questions to evidence or experiments
-> hand off to the natural owner
```

## Why this exists

LEGO Project Planning intentionally begins after a project is sufficiently understood. A separate analysis problem exists earlier:

- the wrong target may be bound;
- "why" may conflate facts, mechanisms, incentives and judgments;
- current conventions may be mistaken for invariants;
- a system may be partially observable;
- the environment or opponent may adapt;
- a clean decomposition may be self-confirming;
- the next experiment may not be obvious.

Question Compiler owns only this framing and discrimination step.

## Truth boundary

Generated questions are derived analysis artifacts.

Mandatory non-equivalences:

```text
question != fact
question != requirement
question != priority
question != task admission
question != hypothesis confirmation
question set != complete state space
interesting != decision-relevant
unanswered != important
```

Project-native evidence, domain science, external standards, source code, tests, Runtime evidence, and real external authorities remain authoritative.

## Compiler pipeline

### Q0 — Target binding

Record:

- exact system/phenomenon under investigation;
- concrete decision the investigation should improve;
- time horizon and operating context;
- explicit do-not-own boundary;
- current evidence sources.

If no decision can be named, the output may still be exploratory, but it must say so rather than pretending to be implementation guidance.

### Q1 — Epistemic split

Separate current material into:

- **OBSERVED** — directly measured or source-backed;
- **INFERRED** — interpretation supported by evidence but not directly observed;
- **ASSUMED** — working premise not yet established;
- **UNKNOWN** — unresolved variable or mechanism;
- **UNOBSERVABLE/COSTLY** — relevant but currently inaccessible or impractical to measure.

This prevents a fluent explanation from silently turning assumptions into state.

### Q2 — Candidate compilation

Select only useful families.

#### STATE

Ask what variables are sufficient to explain or predict relevant evolution.

Typical probe:
"What history has been compressed out of the current state representation even though it still changes future behavior?"

#### OBSERVABILITY

Ask what is directly seen versus inferred, stale, censored, delayed, or strategically manipulated.

Typical probe:
"Are we treating a display/projection as if it were the underlying state?"

#### ACTION / SEARCH

Ask what the actual action or design space contains and what has been removed by convention, tooling, cost, or historical path dependence.

Typical probe:
"Is this option impossible, dominated, merely infeasible today, or simply underexplored?"

#### OBJECTIVE

Ask what objective actually governs behavior, including proxies, constraints and competing objectives.

Typical probe:
"What would this system optimize if it followed the measured proxy perfectly?"

#### POLICY / ADAPTATION

Ask how state maps to action and whether the environment, users, adversaries, institutions, or other agents adapt in response.

Typical probe:
"If we change policy, what changes on the other side of the interaction?"

#### FEEDBACK

Ask what closes the loop: sensing, estimation, control action, effect, delay, disturbance and recovery.

Typical probe:
"Which delayed or missing feedback allows local success to create global failure?"

#### EXPLOITABILITY / ROBUSTNESS

Ask whether a stable observable pattern permits a profitable or damaging best response.

Typical probe:
"What would an observer with long memory learn to exploit about our policy?"

Use "best response" literally only where game-theoretic framing fits. Else interpret it as an adversarial or worst-case response hypothesis.

#### INFORMATION FLOW

Ask which observations reveal hidden state and which actions leak internal state.

Typical probe:
"What can an external observer infer from our action choice, timing, errors, retries, ordering or omissions?"

#### EMERGENCE

Ask which macro behavior may arise from local interaction without direct encoding.

Typical probe:
"Should this capability be specified centrally, or can the desired behavior arise from objective + feedback + selection?"

#### CONTROL

Ask which variables are actual intervention levers and which are merely correlated indicators.

Typical probe:
"If we can change only one variable, which intervention can causally move the outcome?"

#### COUNTERFACTUAL

Ask whether the claimed mechanism survives removal, replacement, reversal, or alternate history.

Typical probe:
"If this LEGO disappears and behavior barely changes, was it ever causally necessary?"

#### FALSIFICATION

Ask what evidence would discriminate competing explanations.

Typical probe:
"What result would make us abandon the current mechanism story?"

### Q3 — Mature-lens routing

Question Compiler does not absorb other disciplines.

Route when applicable:

- **lego-systems-engineering** — unclear system boundary, environment, interface, lifecycle, or local/global outcome.
- **lego-dsm** — suspected coupling, cycles, hubs, or wrong decomposition.
- **lego-feedback-control** — dynamic state, observation, delay, regulation, disturbance, recovery.
- **lego-stpa** — unacceptable loss from unsafe control/interactions.
- **lego-regime-shift** — suspected turning point, lagged downstream outputs, stock/flow divergence, buffers/delays, constraint migration, or partly irreversible decisions under deep uncertainty.
- **domain science / experimental design / statistics** — when the question becomes empirical and the domain has a mature method.
- **security analysis** — when exploitability concerns actual security boundaries; do not treat a metaphorical attacker as authorization for intrusive testing.

The compiler chooses questions; the natural owner supplies the rigorous method.

### Q4 — Pruning

A primary question should satisfy at least one strong criterion:

1. **Decision impact** — a plausible answer changes what we do.
2. **Discrimination** — answers distinguish competing models.
3. **Boundary discovery** — answers reveal a hidden state, authority, interface, or do-not-own boundary.
4. **Experiment value** — answers justify a bounded test with observable outcomes.
5. **Robustness value** — answers expose a consequential failure or best-response surface.

Reject or demote questions that are:

- rhetorical;
- duplicated;
- impossible to operationalize with available evidence;
- answerable but irrelevant to the current decision;
- merely interesting extensions;
- loaded with a preferred conclusion;
- so broad that no bounded evidence can move them.

Do not force numeric scoring. Qualitative ordering is preferred unless the task has a defensible value-of-information model.

### Q5 — Evidence binding

For each retained question record:

- **why now** — which uncertainty it controls;
- **answer route** — source review, observation, measurement, simulation, ablation, intervention, experiment, external authority, or domain-native method;
- **discriminating outcomes** — at least two plausible result classes;
- **decision consequence** — what would change for each result class;
- **claim boundary** — what answering this question still would not establish.

### Q6 — Handoff

A successful compile ends in one of three modes:

1. **INVESTIGATE** — evidence already exists and should be read.
2. **EXPERIMENT** — uncertainty needs a bounded prospective test.
3. **PLAN** — uncertainty is sufficiently reduced to enter LEGO Project Planning or a domain workflow.

Question generation itself is not a fourth permanent work mode.

## Default output contract

Keep the output compact:

### Target
One sentence.

### Decision
One sentence.

### Epistemic split
Compact table or bullets.

### Primary questions
Default 3-7.

For each:
- ID;
- family;
- question;
- decision relevance;
- evidence/experiment route;
- discriminating outcomes.

### Pruned questions
Only when the pruning decision is useful evidence.

### Handoff
INVESTIGATE / EXPERIMENT / PLAN.

No machine-readable schema is introduced in R1. Cross-domain proof is required before any common schema promotion.

## Information-value rule

The compiler is not rewarded for generating many questions.

A rough qualitative preference is:

```text
question value
~ expected decision change
  x discriminating power
  x consequence of uncertainty
  / evidence cost
```

This is a reasoning aid, not a calibrated formula.

Prefer one question that collapses a major uncertainty over ten questions that merely add detail.

## Reflexive use

Question Compiler may analyze Question Compiler.

Required safeguards:

- version the target method separately from the analyzing method;
- preserve the original question set;
- compare whether compiled questions produce better decisions or experiments on real cases;
- do not call the method successful because its questions sound deeper;
- keep rollback to the prior method.

## R1 acceptance

R1 is useful only if prospective cases show at least one of:

- it finds a hidden variable/boundary missed by the initial question;
- it removes a misleading or loaded question;
- it discovers an underexplored action/design alternative;
- it identifies a falsifying observation or counterfactual;
- it converts broad curiosity into a bounded evidence/experiment handoff;
- it prevents premature planning around an unverified mechanism.

## Non-goals

- no universal 12- or 17-question checklist;
- no automatic "deep question" inflation;
- no replacement for scientific research design;
- no replacement for game theory, information theory, systems engineering, control, security, or causal inference;
- no core LEGO schema expansion in R1;
- no claim that every system has an adversary, equilibrium, controller, or meaningful hidden state.

## Initial external/mature foundations

R1 composes existing mature concepts already referenced by LEGO Theory Layer:

- INCOSE systems engineering / systems thinking for system boundaries and interfaces;
- standard feedback-control/state-space reasoning for state, observation, disturbance and intervention;
- DSM for interaction/decomposition diagnostics;
- STAMP/STPA for unsafe control/interactions;
- scientific falsification, controlled comparison, ablation and domain-native experimental design for discriminating evidence;
- game-theoretic and imperfect-information concepts only when strategic adaptation is actually present.

Canonical local references:

- docs/LEGO_THEORY_LAYER_R1.md
- knowledge/lessons/lego-theory-foundations-r1.md
- .agents/skills/lego-systems-engineering/SKILL.md
- .agents/skills/lego-feedback-control/SKILL.md
- .agents/skills/lego-dsm/SKILL.md
- .agents/skills/lego-stpa/SKILL.md
- .agents/skills/lego-regime-shift/SKILL.md
