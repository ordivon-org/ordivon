# LEGO Lens Portfolio & Evolution R1

Date: 2026-09-18
Status: ACTIVE EXPERIMENTAL META-OPERATOR R1

## Purpose

Lens Portfolio & Evolution closes the longitudinal governance gap between:

- Lens Router — selects the Minimum Sufficient Theory Set for one bounded decision;
- Lens Compiler — discovers and type-checks a missing candidate when Router exposes a material method gap;
- Lens Portfolio — decides what deserves long-term model-visible lens status after evidence accumulates.

The candidate theory universe can remain open-ended. The durable active registry should remain sparse.

## Architecture

~~~text
Question Compiler
      |
      v
Lens Router -----------------------> existing LENS / DOMAIN_METHOD
      |
      | NO_LENS_METHOD_GAP
      v
Lens Compiler
      |
      v
candidate + shadow/prospective evidence
      |
      v
Router admission
      |
      v
active registry
      |
      +-----------------------------+
                                    |
all application evidence            |
      |                             |
      v                             |
Lens Portfolio & Evolution <--------+
      |
      +--> KEEP
      +--> MERGE
      +--> RETIRE
      +--> RESERVE
      +--> ADMIT proposal
~~~

Portfolio is longitudinal governance, not per-problem routing.

## Fundamental distinction

### LENS

A reusable cross-cutting analytical perspective that owns a distinct class of material uncertainty and can be selected by Router.

### DOMAIN_METHOD

A mature technical method that naturally owns a bounded analysis or verification step.

Examples include state-machine reachability, experimental design, timing analysis, queueing calculations, distributed-systems consistency checks, and statistical estimation.

A DOMAIN_METHOD can decisively change a design without becoming a permanent cross-domain lens.

### OPERATOR

A method that transforms the reasoning process itself.

Current operators include Question Compiler, Lens Router, Lens Compiler, Lens Portfolio, and Project Planning.

Operators are not counted toward MSTS.

## Role law

For one bounded case, every named discipline or method should have one primary role:

~~~text
LENS
DOMAIN_METHOD
OPERATOR
INFORMATIVE_ONLY
DEFERRED
REJECTED
~~~

A discipline may play a different role in another case, but the role cannot stay ambiguous merely because the discipline is broadly useful.

## Why this layer is needed

The readiness-damping multidisciplinary experiment at detached commit 4f4942e428bbf24c58e3bc4e360805c93ed82fc6 reported eight ACTIVE disciplines in one case.

That experiment produced valuable evidence, but ACTIVE in one analysis is not equivalent to active durable LEGO lens.

Without a portfolio layer, a successful multidisciplinary study can accidentally explode the registry.

## MSTS pressure

The Router law remains authoritative:

- 0 lenses is valid;
- 1 is preferred;
- 2 is normal for orthogonal uncertainties;
- 3 requires explicit marginal-value justification;
- more than 3 is exceptional.

Portfolio performs a pressure audit whenever an application reports more than 3 active lenses.

Useful methods are not demoted in scientific value when reclassified as DOMAIN_METHOD. The change is only about routing and durable model-visible status.

## Longitudinal evidence

Useful fields, when observable:

| Evidence | Meaning |
|---|---|
| applications | bounded cases where the lens was actually used |
| selected_by_router | cases where it entered MSTS |
| decisions_changed | distinct decisions materially changed or corrected |
| boundaries_or_hazards_exposed | unique boundary or hazard findings |
| tests_created | new falsifiable tests or experiments |
| invalid_uses_prevented | invalid method applications blocked |
| justified_no_change | unique no-change decisions |
| false_leads | cost without useful delta |
| domain_method_preemptions | cases where a mature method made the lens unnecessary |
| context_cost | qualitative model-visible routing burden |
| evidence_cost | qualitative evidence and execution burden |

R1 does not collapse these into a universal numeric score. A scalar lens fitness would create false precision without a calibrated utility model.

## Lifecycle recommendations

### ADMIT
Repeated unique value, bounded overlap, stable activation and contraindication rules, and justified routing cost.

### KEEP
Active lens remains distinct and useful.

### MERGE
Useful procedure belongs inside another lens, profile, or operator.

### RETIRE
Repeated evidence shows terminology-only contribution, persistent domination, rare prerequisites, or high cost with little unique delta.

### RESERVE
Legitimate mature method, but current evidence does not justify durable active lens status.

RESERVE is not a Portfolio-owned second pool. Any durable reserve disposition maps back to the canonical Lens Universe reservePool in knowledge/registries/lego-lens-registry-r1.json through an explicit registry proposal.

## Portfolio contraction law

~~~text
open candidate universe
        +
strict role classification
        +
MSTS per decision
        +
longitudinal unique-yield evidence
        +
merge / retirement
        =
bounded active portfolio
~~~

## Pressure test: Agent Service readiness damping

Source evidence:
- detached commit: 4f4942e428bbf24c58e3bc4e360805c93ed82fc6;
- original lens graph digest: sha256:ad00e8d5460cd3aef89372e728fe57cfceda2d463dfa7b1dc2b6c00932445243;
- original decision: generic asymmetric time dwell retained, production promotion blocked by reachability.

Portfolio reclassification:

| Original item | R1 role | Why |
|---|---|---|
| control theory | LENS: feedback-control | owns oscillation and asymmetric edge dynamics |
| reliability/STPA | LENS: STPA | owns false-ready unacceptable-loss constraint |
| distributed systems | DOMAIN_METHOD | freshness and ordering semantics |
| signal processing | DOMAIN_METHOD | one-sided filtering inside the control problem |
| real-time systems | DOMAIN_METHOD | dwell and cadence timing semantics |
| optimization/OR | DOMAIN_METHOD | feasible-controller Pareto comparison |
| experimental design | DOMAIN_METHOD | benchmark identifiability |
| formal reachability | DOMAIN_METHOD | real-provider bad-state reachability |
| complexity/nonlinear dynamics | INFORMATIVE_ONLY | no unique additional decision |
| Bayesian decision theory | DEFERRED | calibrated likelihood model absent |
| game theory | REJECTED | no strategic actor in the disturbance model |

Contracted lens set:

~~~text
MSTS = { feedback-control, STPA }
lens_count = 2
domain_method_handoffs = 6
informative_only = 1
deferred = 1
rejected = 1
~~~

No material decision from the original study is lost:
- asymmetric positive-edge damping remains explained by feedback-control;
- immediate non-READY loss remains a STPA hard constraint;
- freshness, timing, filtering, Pareto comparison, DOE correction, and reachability remain owned by mature domain methods;
- the final no-production-change decision still follows from formal reachability evidence.

## Registry mutation rule

Portfolio does not mutate registry automatically.

A proposal states exact lens id, requested action, evidence, closest overlaps, routing/context effect, and rollback path.

## Reflexive / RSI use

Portfolio itself must be audited for whether it:
- contracts over-counted lens sets;
- prevents duplicate registry entries;
- preserves decision quality after contraction;
- wrongly demotes unique lenses;
- creates governance overhead larger than saved context cost.

Portfolio cannot validate itself from one pressure test.

## Non-goals

- no ranking of academic prestige;
- no universal scalar lens score;
- no claim that domain methods are less valuable than lenses;
- no automatic retirement from non-use alone;
- no requirement that every case use a lens;
- no registry growth from one successful technique;
- no ontology of all sciences.

## R1 acceptance

R1 must show at least one real contraction where a prior analysis used more than 3 active lenses, role normalization reduces durable lens count, material decisions remain preserved, domain methods retain natural authority, and no project truth is changed.

The Agent Service readiness-damping pressure test satisfies this initial criterion, subject to unrelated-domain follow-up.

Canonical references:
- docs/LEGO_LENS_ROUTER_R1.md
- docs/LEGO_LENS_COMPILER_R1.md
- docs/LEGO_THEORY_LAYER_R1.md
- knowledge/registries/lego-lens-registry-r1.json

## Unrelated-domain retention audit

Game Wave 3 provides the anti-overcontraction case:
- Exploration Policy remains distinct because it blocks invalid repeated-choice algorithms when options/feedback are not comparable;
- C-K Design remains distinct because it expands concept space when the object is not yet known;
- Evolutionary Search remains distinct because it gates population search on representation/evaluator validity.

These are used on separate Game decisions rather than stacked together. Portfolio therefore recommends preservation with routing guards rather than forced merge.

Evidence:
- knowledge/lessons/lego-lens-portfolio-game-wave3-audit-r1.md
- evidence/acceptance/lego-lens-portfolio-game-wave3-r1.json

## Executable portfolio audit

R1 includes scripts/lego_lens_portfolio_audit_r1.py and evidence/analysis/lego-lens-portfolio-ledger-r1.json.

The audit mechanically enforces:
- only known roles;
- no duplicate method identity inside one case;
- selected LENS identities must exist in the registry unless explicitly candidate;
- OPERATOR identities must exist in registry operators;
- DOMAIN_METHOD does not require registry membership;
- more than three selected lenses requires explicit exceptional justification.

The audit intentionally does not infer lifecycle recommendations from counts alone.
