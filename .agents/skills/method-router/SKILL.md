---
name: method-router
description: "Route substantial Agent engineering, source-bound Spec-to-implementation, and complex system analysis to the smallest useful canonical method: R2.1 LEGO contracts, system boundaries, causal reasoning and native verification. Not a mandatory workflow or execution authority."
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

1. State the decision or uncertainty in one sentence. If the demand is obsolete, delete the demand before routing any method.
2. If representation is the obstacle, consult references/representation-first.md to try eliminate / quotient / constrain / decouple / resolve **before** choosing a technique; otherwise classify the dominant question using references/method-map.md.
3. Select one primary method whenever one method is sufficient.
4. Add a second method only when it answers a materially different question or falsifies a weakness of the primary method.
5. Sequence methods only when one method's output is an input assumption for another; otherwise they may run independently.
6. Use the canonical project Skill named by the route when available.
7. Preserve the selected method's own stop condition, non-claims, external authority and evidence requirements.
8. If no existing method fits, do not invent a new reusable method immediately. Perform a bounded ad-hoc analysis, record the gap, and promote a new Skill only after repeated evidence that the gap is durable.
9. Stop routing once the next method set is clear. The router must not absorb the method's actual analysis.

## Engineering delivery methods (select only when they change the task)

For a substantial task whose goal and consumer are already known, reuse the
existing [goal-to-consumer R1 scope](../../../docs/architecture/AGENT_OUTCOME_CONTRACT_REFORM_SPEC_R1.md)
and **choose the smallest applicable upstream method**:

- Ambiguous domain vocabulary or a real trade-off -> Matt Pocock
  [domain-modeling](https://github.com/mattpocock/skills/tree/main/skills/engineering/domain-modeling)
  or to-spec; only create a lasting ADR for a hard-to-reverse decision.
- Agreed multi-step implementation with independent ready work -> Matt
  [to-tickets](https://github.com/mattpocock/skills/tree/main/skills/engineering/to-tickets)
  for tracer-bullet dependency slices, or Superpowers
  [writing-plans](https://github.com/obra/superpowers/tree/main/skills/writing-plans)
  for exact files and native test commands. Do not run both just to generate
  two equivalent plans.
- Existing providers or interfaces might already solve the problem -> ECC
  [search-first](https://github.com/affaan-m/ECC/tree/main/skills/search-first);
  a real multi-consumer API boundary -> ECC
  [contract-first](https://github.com/affaan-m/ECC/tree/main/skills/contract-first)
  and change-impact. Ordinary local changes need neither a new API schema nor
  an impact-report file.
- Behavior change with an actual failing consumer -> existing Owner tests
  using Superpowers [TDD](https://github.com/obra/superpowers/tree/main/skills/test-driven-development)
  as a method; for implementation handoff choose Superpowers executing-plans
  or Matt implement, **not two orchestrators**.
- Before claiming delivery -> ECC verification-loop or Superpowers
  verification-before-completion using the Owner's actual commands and final
  consumer readback. Neither method's narrative grants domain acceptance.

A read upstream page is not an installed, trusted Skill binding, an execution
permission, or evidence that the Owner verifier passed. Resolve the Skill from
current project Skills when available; otherwise apply only its source-qualified
engineering practice. Do not bulk-install Matt, ECC or Superpowers, duplicate
their Skills, or introduce a second workflow authority. Routine deterministic
Git/Runtime/Owner operations execute directly without method routing.

## Typical routes

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
For innovation/search questions requiring a comparative theory lens, consult
references/innovation-lens-routing.md only after the basic method route is insufficient.
This external-theory map is a source reference, not new authority or a mandatory stage.

## Multi-step Agent engineering (optional)

When the task is a substantial Owner change needing a spec, tracer-bullet execution,
independent verification or upstream Skill adoption, read
`references/agent-engineering-delivery.md`. It selectively adapts Matt Pocock
Skills, ECC and Superpowers to existing Ordivon contracts. It is not a required
life cycle for ordinary edits, a second task engine or an effect permission.

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
