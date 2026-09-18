# LEGO Lens Router R1

Date: 2026-09-18
Status: ACTIVE EXPERIMENTAL META-METHOD

## Purpose

LEGO Lens Router selects the smallest useful set of analytical lenses for a concrete decision.

It exists because the theory library can grow much faster than any one problem needs. The router therefore optimizes for **minimum sufficient theory**, not maximum intellectual coverage.

The router is a meta-method. It does not own project truth, domain truth, or the external disciplines.

## Core idea

`more lenses != better analysis`

A useful lens must have marginal decision value.

The target is:

`Minimum Sufficient Theory Set (MSTS)`

A set is sufficient when:
- each material uncertainty in the current decision has a natural method owner or evidence route;
- no omitted lens is expected to change the next bounded decision enough to justify its analysis cost;
- adding another lens would mostly duplicate vocabulary, evidence, or questions.

MSTS is a reasoning principle, not a calibrated global optimum.

## External foundations

The router borrows mature ideas rather than claiming a new universal science of method selection:

- **adaptive toolbox / ecological rationality** — reasoning strategies are useful when matched to the structure of the environment/problem;
- **model selection / parsimony** — additional model complexity should pay for itself in improved explanatory or predictive value;
- **value of information** — information matters when it can improve a decision relative to alternatives;
- **bounded rationality / satisficing** — stop once the decision is sufficiently resolved rather than exhaustively analyzing every possible frame.

Canonical starting references:
- Gerd Gigerenzer, adaptive toolbox / ecological rationality;
- statistical model-selection literature including complexity-penalized selection;
- decision-theoretic value-of-information reasoning.

These are intellectual substrates, not claims that selecting scientific disciplines is mathematically equivalent to AIC, bandits, or formal VOI.

## Lens classes

The registry distinguishes:

### Discipline lens

A compact operationalization of a mature external discipline or method family.

Examples:
- systems engineering;
- DSM;
- feedback control;
- STPA;
- causal intervention;
- FMEA/FTA;
- information flow;
- C-K design;
- evolutionary search.

### Composite profile

A validated composition of several lenses plus domain-specific analytical laws.

Examples:
- Regime Shift / Deep-Uncertainty Decision;
- Agent Security LEGO.

A composite profile must declare which primitive lenses it reuses. It must not silently duplicate their ontology.

### Operator

A method that transforms or routes analysis rather than analyzing the target directly.

Examples:
- LEGO Question Compiler;
- LEGO Lens Router;
- LEGO Project Planning.

Operators are not counted as theory lenses.

## Input — Problem Signature

The router works from a bounded decision and an evidence-backed problem signature.

Record only relevant signals:

- target / system of interest;
- decision to improve;
- domain-native owner/method;
- ambiguity of the object itself;
- boundary/interface ambiguity;
- dependency density/cycles;
- dynamic state/feedback/delay;
- safety/security consequence;
- replaceability/composition question;
- causal/intervention claim;
- explicit failure/reliability question;
- sensitive information/observer question;
- regime shift / irreversibility / deep uncertainty;
- open-ended concept generation;
- repeated comparable choices with attributable feedback;
- candidate population + evaluator quality;
- organizational autonomy/coordination/recursion;
- analysis budget / time / evidence cost.

Unknown properties remain UNKNOWN. Do not invent activation signals merely to justify a lens.

## Routing procedure

### R0 — Domain-owner preemption

Ask first:

> Is there a mature domain-native method that directly owns this question?

If yes, use it unless a LEGO lens adds a distinct cross-cutting question.

Examples:
- statistical inference -> domain statistics;
- cryptographic protocol proof -> cryptographic method;
- user research -> appropriate Human/player research;
- accounting -> accounting standard/provider;
- compiler correctness -> language/compiler verification.

The Lens Router must not replace the mature domain method merely because a LEGO analogue exists.

### R1 — Candidate generation

Use the registry activation signals to produce a small candidate set.

Do not search the whole catalog by semantic similarity alone.

A candidate lens must answer a distinct decision-relevant question.

### R2 — Prerequisite gate

Reject a lens whose prerequisites are not met.

Examples:
- Exploration Policy requires repeated comparable choices and feedback.
- Evolutionary Search requires a meaningful candidate representation and evaluator.
- Causal Intervention requires a causal/intervention question, not mere description.
- DSM requires enough interaction evidence to make a dependency model meaningful.

A missing prerequisite is a reason not to use the lens, not a reason to fabricate the prerequisite.

### R3 — Contraindication / anti-activation gate

Reject lenses when the task shape conflicts with them.

Examples:
- do not use bandits for one-shot incomparable choices;
- do not use Evolutionary Search when fitness is a weak proxy for unknown value;
- do not use VSM as a five-service software template;
- do not use STPA as a generic bug checklist;
- do not use FTA for interactions whose loss does not require component failure when STPA is the better owner.

### R4 — Dominance and overlap pruning

For each pair of candidate lenses ask:

- do they answer the same question?
- do they consume the same evidence?
- do they produce the same decision consequence?
- does one contain the other as a validated composite profile?
- does the second add a unique falsifier, hazard, boundary, or intervention?

If not, remove the dominated lens.

Composite profiles may dominate their component lenses for routing only when the profile explicitly consumes those lenses and the current problem matches the validated profile boundary.

### R5 — Minimum sufficient cover

Choose the smallest set that covers the material uncertainties.

Default:
- 0 lenses is allowed;
- 1 primary lens is preferred;
- 2 lenses are common when uncertainties are orthogonal;
- 3 lenses require explicit marginal-value justification;
- >3 lenses is exceptional and must state why each additional lens changes the decision.

Do not numerically score lenses unless the project has a defensible quantitative value model.

Qualitative preference:

`marginal lens value ~ expected decision change × discrimination / analysis cost`

This is a pruning aid, not a calibrated equation.

### R6 — Execution order

Order lenses when one changes the validity of another.

Typical precedence:

- Question Compiler before Lens Router when the question itself is vague.
- Systems Engineering before detailed analysis when the boundary is unresolved.
- C-K before optimization when the object/candidate space is not yet known.
- Causal Intervention before claiming an experiment reveals mechanism.
- Information Flow before a security profile only if the profile does not already consume it.
- Domain-native verification after generative/search lenses before promotion.

Parallel use is allowed only for genuinely orthogonal questions.

### R7 — Stop / handoff

Stop routing when:
- the next bounded decision is clear;
- each material uncertainty has an evidence/method owner;
- an additional lens would not change the next action;
- the correct result is NO_LENS because the domain-native method is already sufficient.

The router emits a handoff, not a permanent analysis mode.

When the correct result is `NO_LENS`, distinguish two cases:

- **NO_LENS_SUFFICIENT** — the domain-native method/evidence route is sufficient; stop.
- **NO_LENS_METHOD_GAP** — a material decision-relevant uncertainty remains but no admitted lens naturally owns it; hand only that uncovered residue to `lego-lens-compiler` for source-grounded candidate discovery and type-checking.

This distinction does not create two new registry lens types. Lens Compiler is an operator and cannot self-admit its output; any durable candidate returns through this router's lens-admission contract.

## Default output

### Target
One sentence.

### Decision
One sentence.

### Problem signature
Only evidence-backed signals.

### Selected MSTS
For each selected lens:
- lens id;
- unique question it owns;
- why its prerequisites are met;
- expected decision value;
- evidence route;
- stop condition.

### Rejected candidates
Record only decision-relevant exclusions:
- prerequisite missing;
- overlap/dominated;
- domain-native method owns it;
- no marginal decision value;
- contraindicated.

### Execution order
Sequential / parallel with dependency reason.

### Stop condition
What makes the theory set sufficient.

### Handoff
INVESTIGATE / EXPERIMENT / PLAN / DOMAIN_METHOD / NO_LENS.

## Lens admission into the registry

The statement "almost any discipline can become a lens" is accepted only under an admission contract.

A candidate discipline/profile must provide:

1. **Distinct object/question** — what does it see that existing lenses do not?
2. **Mature substrate** — authoritative external discipline/method, or clearly labeled Ordivon composite.
3. **Activation conditions** — when it should be used.
4. **Prerequisites** — what must already be true/observable.
5. **Contraindications** — when it should not be used.
6. **Operators** — what analysis it actually performs.
7. **Outputs/non-claims** — what it can and cannot establish.
8. **Stop condition** — when to stop.
9. **Overlap audit** — closest existing lenses and why this is not redundant.
10. **Prospective case** — at least one real decision where it changes/corrects/prevents something.
11. **Retention evidence** — periodic unique value or retirement.

A useful academic field can still fail admission as an Ordivon lens if the current registry already covers its decision function.

## Retention / retirement

A retained lens must periodically demonstrate at least one:

- unique decision changed;
- unique boundary/edge corrected;
- unique hazard/failure discovered;
- invalid method/application prevented;
- measurable uncertainty or analysis-cost reduction.

Repeated terminology-only contribution is grounds to MERGE or RETIRE.

A retired lens may remain as historical knowledge without staying model-visible or routed.

## Non-goals

- no universal ranking of academic disciplines;
- no claim that one theory is objectively superior across all problems;
- no mandatory numeric score;
- no requirement to use LEGO lenses when domain-native methods suffice;
- no automatic activation from keywords;
- no unlimited multi-lens ensemble;
- no promotion of registry fields into project truth;
- no Wave 4 merely to increase coverage;
- no using Lens Compiler to bypass a matching admitted lens or domain-native owner.

Canonical local references:
- docs/LEGO_QUESTION_COMPILER_R1.md
- docs/LEGO_THEORY_LAYER_R1.md
- docs/LEGO_THEORY_WAVE2_R1.md
- docs/LEGO_THEORY_WAVE3_R1.md
- knowledge/registries/lego-lens-registry-r1.json
- docs/LEGO_LENS_COMPILER_R1.md
