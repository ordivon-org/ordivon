---
name: lego-lens-router
description: "Select the minimum sufficient set of Ordivon LEGO theory lenses for a concrete decision. Use after a target/question is sufficiently bound, especially when many possible disciplines could apply. Filter by problem shape, prerequisites, contraindications, overlap, marginal decision value, and analysis cost; allow NO_LENS, domain-native method handoff, merge, or retirement. Do not activate every plausible lens or treat theory coverage as analysis quality."
compatibility: Cross-platform. Reads the local lens registry and emits a routing/handoff decision; it does not alter project truth by itself.
metadata:
  source-authority: Ordivon meta-method grounded in adaptive-toolbox, parsimony/model-selection, value-of-information and bounded-rationality ideas
  method-contract: docs/LEGO_LENS_ROUTER_R1.md
  registry: knowledge/registries/lego-lens-registry-r1.json
---

# LEGO Lens Router

Choose the smallest theory set that can materially improve the current decision.

## Workflow

1. Bind target, decision and evidence boundary. If they are vague, hand off to `lego-question-compiler` first.
2. Ask whether a domain-native mature method already owns the question. Prefer it unless a LEGO lens adds a distinct cross-cutting uncertainty.
3. Build an evidence-backed problem signature.
4. Read the lens registry and generate only candidates whose activation signals match.
5. Enforce prerequisites. Missing prerequisites reject the lens.
6. Enforce contraindications. Do not force a method onto the wrong problem shape.
7. Prune overlaps/dominated candidates:
   - same question;
   - same evidence;
   - same decision consequence;
   - component lens already consumed by a validated composite profile.
8. Select the **Minimum Sufficient Theory Set**:
   - 0 is valid;
   - prefer 1;
   - use 2 for orthogonal uncertainties;
   - 3 requires explicit marginal-value justification;
   - >3 is exceptional.
9. Order lenses only when dependencies require it.
10. Stop when another lens would not change the next bounded action.
11. Emit handoff: INVESTIGATE / EXPERIMENT / PLAN / DOMAIN_METHOD / NO_LENS.

## Critical routing distinctions

- Unknown desired object/concept -> `lego-ck-design`.
- Known repeated comparable choices + attributable feedback -> `lego-exploration-policy`.
- Population variation + meaningful representation + trustworthy evaluator -> `lego-evolutionary-search`.
- Organizational autonomy/coordination/control -> `lego-organizational-cybernetics`.
- Causal claim/intervention -> `lego-causal-intervention`.
- Explicit component/process failure propagation -> `lego-fmea-fta`.
- Unsafe system interaction/control action with high consequence -> `lego-stpa`.
- Dynamic feedback/delay/state estimation -> `lego-feedback-control`.
- Sensitive information visibility/observer boundary -> `lego-information-flow`.
- Replaceability/substitutability/composition -> `lego-compositional-contracts`.

Do not infer activation from keywords alone.

## Output

Produce:
- target;
- decision;
- problem signature;
- selected MSTS;
- unique question per selected lens;
- rejected candidates with brief reason;
- execution order;
- stop condition;
- handoff.

## Promotion law

Routing output is derived analysis. It never changes architecture or project truth by itself.

## Non-claims

The router does not prove the chosen lens set is globally optimal or complete. It minimizes obvious redundancy and analysis cost under current evidence.

## Stop condition

Stop routing once the next decision is covered by the minimum useful method set and additional lenses have no clear marginal decision value.

Canonical references:
- docs/LEGO_LENS_ROUTER_R1.md
- knowledge/registries/lego-lens-registry-r1.json
- docs/LEGO_QUESTION_COMPILER_R1.md
- docs/LEGO_THEORY_LAYER_R1.md
