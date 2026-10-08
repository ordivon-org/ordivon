---
name: method-router
description: "Select the smallest useful set of standards-backed analysis methods for an already scoped Ordivon problem. Use when the problem is complex enough that choosing the reasoning method matters: ambiguous system boundaries, coupling/decomposition, composition/substitutability, causal claims, reliability failures, unsafe interactions, control/feedback, organizational coordination, information flow, exploration/search, or project-kernel decomposition. Route to existing canonical Agent Skills rather than inventing a new lifecycle, private trigger engine, or all-purpose methodology."
compatibility: Cross-platform. Routes among existing project Agent Skills; it does not execute tools, grant authority, or prove a method's conclusions.
metadata:
  source-authority: Agent Skills progressive disclosure plus Ordivon standards-backed method Skills
---

# Method Router

Use this Skill when the main uncertainty is **which analysis method to apply**, not when the correct method is already obvious.

## Core rule

Choose the **smallest method set that can change the decision**.

Do not activate every method merely because it exists. Do not turn the method catalog into a mandatory lifecycle.

## Procedure

1. State the decision or uncertainty in one sentence.
2. Classify the dominant question using references/method-map.md.
3. Select one primary method whenever one method is sufficient.
4. Add a second method only when it answers a materially different question or falsifies a weakness of the primary method.
5. Sequence methods only when one method's output is an input assumption for another; otherwise they may run independently.
6. Use the canonical project Skill named by the route when available.
7. Preserve the selected method's own stop condition, non-claims, external authority and evidence requirements.
8. If no existing method fits, do not invent a new reusable method immediately. Perform a bounded ad-hoc analysis, record the gap, and promote a new Skill only after repeated evidence that the gap is durable.
9. Stop routing once the next method set is clear. The router must not absorb the method's actual analysis.

## Typical routes

A request to **create or adopt a new forward Research Study/paper project** is a lifecycle/admission handoff rather than a reasoning-method choice: use `research-study-birth` first, then return to method routing only if the admitted Study still has a method-selection uncertainty.

- unclear system boundary / system-of-systems / interface inventory -> systems-engineering
- decomposition quality / coupling / cycles / clusters -> design-structure-matrix
- interfaces compose? / replacement / assumptions and guarantees -> compositional-contracts
- what causes what? / intervention / ablation validity -> causal-intervention
- component/process failure propagation -> fmea-fta
- unsafe interactions despite locally correct components -> stpa
- feedback, stability, observability, controllability -> feedback-control
- organizational recursion, coordination, viable structure -> organizational-cybernetics
- authority/data/evidence leakage across boundaries -> information-flow-analysis
- search over candidate designs under an explicit fitness/evaluation function -> evolutionary-search
- exploration/exploitation or information-gathering policy -> exploration-policy
- project-native decomposition into responsibilities/contracts/evidence -> project-kernel-decomposition

See references/method-map.md for disambiguation and multi-method combinations.

## Anti-patterns

- **Method maximalism:** applying all available methods.
- **Name matching:** selecting a method because its title resembles a project term.
- **Tool substitution:** treating an executable tool as the reasoning method.
- **Authority transfer:** allowing the router to become scientific, architectural, safety, or execution authority.
- **Router recursion:** repeatedly routing instead of performing the selected analysis.
- **Private trigger engine:** adding hidden scores, embeddings, learned routing, or mandatory global activation without evidence.

## Output

Produce only:

- decision/question;
- primary method;
- optional secondary method(s) with why each is necessary;
- ordering or independence;
- explicit non-selected nearby methods when confusion is likely;
- stop condition for routing.

## Stop condition

Stop as soon as the smallest defensible method set is selected or the problem is classified as not needing a reusable method Skill.
