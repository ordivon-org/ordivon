---
name: lego-question-compiler
description: Convert a vague, narrative, overloaded, or prematurely solution-shaped problem into a small evidence-bound set of decision-relevant questions. Use before LEGO planning when the real state, observation boundary, mechanism, strategy space, objective, exploitability, or discriminating experiment is unclear; also use during analysis when a decomposition has become self-confirming. Do not treat generated questions as facts, requirements, priorities, or project truth.
compatibility: Cross-platform. Produces derived analysis questions; it does not alter project truth by itself.
metadata:
  source-authority: Ordivon composition of mature systems, control, scientific, decision, game/information and falsification reasoning
  method-contract: docs/LEGO_QUESTION_COMPILER_R1.md
  theory-layer: docs/LEGO_THEORY_LAYER_R1.md
---

# LEGO Question Compiler

The compiler turns a fuzzy question into a bounded investigation surface. Generated questions are derived analysis artifacts, not truth.

## Activation

Use when one or more are true:
- the prompt asks "why" but mixes facts, mechanisms and judgments;
- the system is partially observable or adaptive;
- current practice may be a convention rather than an invariant;
- the action/strategy space may be artificially narrow;
- a system appears successful but its exploitability or failure boundary is unknown;
- the next useful experiment is unclear;
- a LEGO decomposition is coherent but insufficiently falsifiable.

Do not invoke merely to create more questions.

## Workflow

1. **Bind the target.** State the exact system/phenomenon, decision to be improved, time horizon, and evidence boundary.
2. **Separate known from inferred.** Record direct observations, source-backed claims, assumptions, and unknowns.
3. **Compile candidate question families** only where useful:
   - STATE — what variables determine future behavior?
   - OBSERVABILITY — what is observed, hidden, inferred, stale, or manipulable?
   - ACTION/SEARCH — what actions exist, and which were excluded by convention or search history?
   - OBJECTIVE — what is actually optimized; what proxies or competing objectives exist?
   - POLICY/ADAPTATION — how does state map to action; who adapts to whom?
   - FEEDBACK — what loops, delays, disturbances, and estimators shape dynamics?
   - EXPLOITABILITY/ROBUSTNESS — what stable pattern can a best response exploit?
   - INFORMATION FLOW — what observations reveal hidden state; what actions leak internal state?
   - EMERGENCE — what macro behavior may arise from local rules without direct encoding?
   - CONTROL — which variables are genuine intervention levers?
   - COUNTERFACTUAL — what changes if a node, assumption, rule, or interface is removed/replaced?
   - FALSIFICATION — what observation would discriminate between competing explanations?
4. **Bind the natural method owner.** Record the analysis family best suited to the surviving uncertainty—systems engineering, DSM, feedback control, STPA, regime-shift/deep-uncertainty analysis, domain science, experiments, statistics, or another mature external method—without making cross-Skill invocation part of this Skill's authority.
5. **Prune aggressively.** Keep questions that can change a decision, distinguish hypotheses, expose a hidden boundary, or justify a bounded experiment. Merge duplicates. Drop rhetorical, unanswerable, and purely curiosity-generating questions.
6. **Order by information value, not drama.** Prefer questions whose answers eliminate the largest consequential uncertainty at acceptable evidence cost.
7. **Emit a bounded question set.** Default to 3-7 primary questions plus optional follow-ups, not a giant checklist.
8. **Bind each primary question to evidence or an experiment.** State how it could be answered and what result would change the current model.
9. **Stop.** When remaining questions would not change the current decision or experiment, hand off to the relevant analysis/planning Skill.

## Output

Produce:
- target and decision boundary;
- established / inferred / unknown split;
- 3-7 primary compiled questions;
- for each: family, why it matters, evidence/experiment route, discriminating outcomes;
- discarded questions and why they were pruned when useful;
- next handoff: investigate, experiment, or plan.

## Quality tests

A compiled question is stronger when:
- answering it could change an architecture, research, control, or execution decision;
- it distinguishes at least two plausible models;
- it is answerable by evidence, observation, intervention, or a bounded experiment;
- it does not smuggle its preferred answer into the wording;
- it respects the real authority boundary;
- it exposes uncertainty rather than converting uncertainty into invented structure.

## Promotion law

A question never updates the LEGO plan by itself. Only evidence produced by answering it may support an explicit architecture or project decision.

## Non-claims

A coherent question set does not prove completeness, novelty, causal identification, safety, feasibility, or optimality. "Best response", "information leakage", "state", and similar terms are lenses, not mandatory universal fields.

## Stop condition

Stop compiling when the remaining uncertainty is already localized to a concrete investigation, experiment, or decision and additional question generation would add breadth without decision value.

Canonical references:
- docs/LEGO_QUESTION_COMPILER_R1.md
- docs/LEGO_THEORY_LAYER_R1.md
- knowledge/lessons/lego-theory-foundations-r1.md
