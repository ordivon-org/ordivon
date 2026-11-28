# Superpowers Engineering Discipline Kernel — selective extraction

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Superpowers packages a strongly opinionated software-engineering methodology as auto-activated Agent Skills so coding agents consistently design before coding, debug from root causes, use evidence before claims, and delegate/review work with isolated context.**

## Project role

Superpowers is not a new agent runtime, workflow engine, execution provider, Skill standard or task authority. It is primarily:

`engineering methodology + Agent Skills + small harness/plugin bootstrap`

Its runtime value comes from making engineering disciplines difficult for an agent to silently skip.

For Ordivon, most of its end-to-end workflow overlaps with the existing Engineering Method Kernel extracted from Spec Kit and with the open Agent Skills format. Therefore Ordivon should **not** install or reproduce Superpowers as a mandatory global engineering lifecycle merely because the repository is mature/popular.

Use Superpowers as:

- a source of individual proven engineering Skills;
- a source of Skill authoring/evaluation methods;
- evidence for context-isolated delegation/review patterns;
- a reference implementation for enforcing behavioral discipline in coding agents.

## What is already covered elsewhere

The following Superpowers ideas are already represented by Ordivon's Engineering Method Kernel:

- clarify/design intent before implementation when materially useful;
- plan consequential decisions;
- avoid unrequested complexity;
- verification is mandatory;
- agent completion claims are not evidence;
- repair and re-verify gaps;
- process depth should reflect task risk/uncertainty/coordination cost.

The following infrastructure is already externalized:

- Skill format/discovery -> Agent Skills standard;
- coding agent/tool execution -> Codex or another provider;
- Git/worktrees/tests/build tools -> repository-native mature tooling.

Do not duplicate these as Ordivon-specific Superpowers abstractions.

## Mechanism 1: behavioral testing for Skills

The strongest genuinely reusable Superpowers idea is to treat procedural Agent instructions as behavior that should be empirically tested rather than merely reviewed as prose.

For a proposed Skill:

```text
baseline task/scenario without Skill
        ↓
observe failure / undesired behavior
        ↓
write or change minimal Skill guidance
        ↓
run comparable task with Skill
        ↓
observe compliance / outcome improvement
        ↓
refine against new failure/rationalization cases
```

Useful scenario types vary by Skill:

- **discipline Skill** — pressure/adversarial scenarios; does the agent still follow the rule under time/sunk-cost/context pressure?
- **technique Skill** — novel application and edge cases;
- **pattern Skill** — recognition, application and counterexamples;
- **reference Skill** — retrieval and correct application.

### Ordivon adaptation

Do **not** require literal test-first creation for every Skill or documentation edit. Instead use a risk/value gate:

- low-impact reference/procedure: review + one representative application may be sufficient;
- reusable high-impact Skill: baseline/evaluation comparison should normally be required;
- safety/authority-critical Skill: adversarial/pressure evaluation and independent review should be expected.

The retained principle is:

**A Skill is not proven useful because its text sounds good; evaluate the behavior it induces.**

## Mechanism 2: fresh evidence before status claims

Before claiming a technical state such as passing, fixed, built or complete:

1. identify evidence that actually proves the claim;
2. obtain fresh evidence from the current state;
3. inspect the complete relevant result, not a proxy;
4. state only what the evidence establishes.

This strengthens Ordivon's existing `evidence over assertion` rule with a freshness constraint:

`stale/past evidence != current-state proof`

Examples:

- current test result proves the current test run, not deployment behavior;
- linter success does not prove the build;
- a changed diff does not prove the bug is fixed;
- executor/subagent success does not prove requirements are met.

This should be folded into VERIFY rather than becoming a separate Ordivon command.

## Mechanism 3: systematic debugging as hypothesis testing

The useful compact debugging kernel is:

```text
REPRODUCE / OBSERVE
      ↓
TRACE ROOT CAUSE
      ↓
COMPARE WITH WORKING REFERENCE
      ↓
FORM ONE HYPOTHESIS
      ↓
TEST MINIMALLY / ONE VARIABLE
      ↓
FIX ROOT CAUSE
      ↓
VERIFY ORIGINAL SYMPTOM + REGRESSION
```

Key rules:

- gather evidence before proposing fixes;
- reproduce reliably when possible;
- inspect error messages, data flow and recent changes;
- compare broken behavior with a known-working analogue;
- test one causal hypothesis at a time;
- do not stack speculative fixes;
- if repeated independent fixes expose new coupling/shared-state failures, reconsider the architecture instead of continuing local patching.

### Ordivon adaptation

Superpowers uses hard universal thresholds and absolute wording. Ordivon keeps the causal method but not arbitrary fixed counts as architectural truth. Repeated failed hypotheses should increase the probability that the model/system boundary is wrong; the exact escalation threshold should depend on task cost/risk.

## Mechanism 4: isolated-context delegation

For independent implementation/review work, Superpowers deliberately gives fresh subagents **precisely constructed task context instead of the coordinator's entire session history**.

This is valuable because it:

- reduces context pollution;
- prevents reviewer anchoring on the implementer's reasoning/history;
- makes task assumptions explicit;
- preserves coordinator context;
- improves independence of review.

Recommended pattern when subagents are actually useful:

```text
Coordinator
   |
   +--> Implementer: requirement + bounded context + target files/evidence
   |
   +--> Reviewer: requirement + resulting artifact/diff + validation criteria
```

Reviewer context should emphasize the work product and requirements, not inherit the implementer's private reasoning narrative.

## Mechanism 5: two different review questions

Superpowers' subagent workflow separates review roughly into:

1. **spec/requirement compliance** — did we build what was asked, no less/no more?
2. **code/implementation quality** — is the resulting implementation technically sound and maintainable?

These are different predicates and should not be collapsed.

This maps well to Ordivon VERIFY:

```text
intent compliance
    +
implementation quality
    +
reality evidence
```

Not every small change warrants separate reviewer agents; activate this separation when coordination/risk justifies it.

## What Ordivon should NOT copy as universal law

### Mandatory brainstorming/user approval before any creative change

Superpowers intentionally makes brainstorming/design approval mandatory before implementation. This is useful for some product work but too rigid for Ordivon. Low-risk, well-specified engineering changes should not manufacture user checkpoints.

Retain instead:

`clarify/seek approval only when ambiguity, consequence or authority requires it`

### Mandatory TDD for virtually all production code

Superpowers requires test-first RED-GREEN-REFACTOR for almost every feature/bug/refactor and treats deviations as failures.

Ordivon's existing rule remains better generalized:

`testing is conditional; verification is mandatory`

Use TDD when behavior can be efficiently specified by executable tests and the benefits justify it. Use other evidence for configuration, generated artifacts, integration effects, exploratory/prototype work or domains where test-first is not the strongest validation method.

### Mandatory tiny task plans and frequent commits

Detailed 2–5 minute task plans, exact code in plans and fixed commit cadence are workflow preferences, not universal engineering truths. Keep dependency-aware decomposition only when it improves execution/coordination.

### Review after every task

Independent review has value, but reviewing every trivial task can cost more than it saves. Scale review depth with risk, novelty, blast radius and coordination cost.

### Global skill-enforcement bootstrap

Superpowers forces a `using-superpowers` skill check before almost all agent behavior. Ordivon should rely on standard Skill discovery/model-driven activation and only add mandatory policies where evidence proves model-driven activation is insufficient for a consequential rule.

## Prototype architecture

A minimal Superpowers-like prototype requires no new runtime:

1. choose an Agent Skills-compatible coding agent such as Codex;
2. install a small set of engineering Skills, for example:
   - systematic debugging;
   - verification before completion;
   - code review/delegation;
3. add a lightweight bootstrap/instruction telling the agent to consult relevant Skills;
4. expose ordinary coding tools/subagents from the host;
5. evaluate the Skills on scenarios with and without them;
6. refine descriptions/instructions when activation or behavior fails.

That prototype demonstrates the entire architectural idea. The rest of Superpowers is a mature skill library, harness adapters, tests and product packaging.

## Ordivon use rule

Before creating an Ordivon Engineering Skill:

1. check whether a mature external Skill already covers the method;
2. check whether the method is already ordinary model knowledge or project instruction;
3. create/retain a Skill only when progressive task-local procedural guidance materially improves behavior;
4. for important Skills, evaluate induced behavior rather than approving prose alone.

## Extracted additions to Engineering

Superpowers contributes four meaningful additions beyond the existing Spec Kit kernel:

1. **fresh-evidence rule** — current-state claims require current-state evidence;
2. **causal debugging loop** — root cause and single-hypothesis testing before speculative fixes;
3. **context-isolated review/delegation** — construct reviewer/worker context deliberately;
4. **Skill behavior evaluation** — test whether procedures change agent behavior/outcomes.

Everything else is mostly a stricter implementation/profile of engineering practices already present.

## Project-study acceptance

### One-sentence test

PASS: Superpowers is an opinionated software-engineering methodology delivered as automatically activated Skills for coding agents.

### Prototype test

PASS: a small set of Skills plus a coding-agent host/bootstrap is sufficient to reproduce its essential architecture; no new orchestration/runtime primitive is needed.

## Verdict

**PASS — EXTRACT SELECTIVELY / USE INDIVIDUAL SKILLS WHEN THEY OUTPERFORM THE EXISTING KERNEL.**

Do not make the full Superpowers workflow mandatory for Ordivon. Further source study should be demand-driven at the individual-Skill level.
