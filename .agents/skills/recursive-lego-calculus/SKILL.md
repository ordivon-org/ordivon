---
name: recursive-lego-calculus
description: "Use for real Ordivon LEGO work: question the goal and consumers, delete unneeded responsibilities, express the smallest useful input/output/contract, and compose existing capabilities without adding a new framework. For hard cross-layer reasoning, open the optional formal reference and route to specialist Skills."
compatibility: Cross-platform. Helps Agents simplify and compose real responsibilities; use the formal reference only when necessary. Does not grant authority, execute effects, define domain truth or replace specialist verification.
metadata:
  ordivon-category: general
  source-authority: Ordivon Recursive LEGO Calculus R2.1, grounded in systems engineering, assume-guarantee composition, formal refinement, verification, optimization and existing canonical Ordivon method Skills
---

# Recursive LEGO Calculus

Useful when an Agent is deciding whether a capability should exist, be deleted, reused, decomposed or composed. For hard cross-layer proof and optimization, the formal reference is optional.

## Practical rule

A LEGO is one **goal-conditioned, replaceable responsibility** with identity, inputs, outputs, behavioral contract and acceptance. It is not a file, Agent, Skill, Tool or required runtime object.

Use whichever of these questions changes the current decision. They are **not** a mandatory checklist, fixed order or Agent organization:

1. **Goal.** Name the Human/domain outcome, exact current source, real consumer and natural owner. If the goal itself is doubtful, investigate before building.
2. **Zero-base.** Pretend the existing file, service, Skill and LEGO do not exist. Trace every consumer through to a real outcome; consumers that exist only to keep each other alive do not justify retention. Prefer deleting the whole chain or using a mature existing provider.
3. **LEGO.** For a responsibility that remains necessary, name only six things: **identity, one responsibility, inputs, outputs, behavioral contract, acceptance**. Add state, authority, effects, provenance, cost or children only when they change the decision. LEGO is the responsibility, not its file, class, Agent, Skill or Tool.
4. **Compose.** Connect compatible inputs/outputs, assumptions/guarantees, identities and effect boundaries. Reuse a real owner interface; do not duplicate truth or assume a successful subcomponent implies a successful whole. Split or share only if replaceability and consumer outcomes improve.
5. **Act.** Agents freely choose, compete, cooperate and adapt the smallest relevant Skills and Tools. Execute only through actual owner-authorized boundaries; no permanent role, mandatory workflow, or new LEGO execution service.
6. **Select.** Observe the changed consumer behavior and the smallest relevant native check. Report PASS, FAIL or UNKNOWN honestly. Keep, replace, merge or delete based on evidence; stop when further decomposition adds glue instead of value.

For a simple case a working note can fit in six short fields, but six fields do NOT prove globally minimum or sufficiently safe representation. Reuse real APIs and their owner-native tests rather than creating a redundant specification file.

### Representation method decision: CEGAR; MSR is not a default

Do **not** default to Minimum Sufficient Representation (MSR). The adjective minimum requires an explicit feasible candidate space, cost ordering and proof against alternatives. The adjective sufficient requires an actual specification and proof that the abstraction preserves what its consumers require, including security and physical effects. Those proofs may cost more than solving the domain problem; unknown future requirements and attacks are not guaranteed covered. MSR remains an OPTIONAL, removable method/Skill LEGO for reversible, low-risk, independently verified local compression. Never label a candidate PROVEN MINIMUM, SUFFICIENT or SAFE solely because it has few fields or passed bounded tests.

Use established **Counterexample-Guided Abstraction Refinement (CEGAR)** when a real abstraction affects safety or contract claims. Define the concrete source and property, sound abstraction relation, encoded target and accepted assumptions. Check the abstract model; concretize every reported trace against real model constraints before declaring a failure. A feasible exact trace is a concrete-model counterexample; an infeasible trace justifies a sound refinement; an unverified trace is UNKNOWN. Rerun the bounded checker after refinement. An abstract PASS needs sound property-preservation and source-to-implementation bridges before it can support an actual system claim. CEGAR does NOT generally prove termination, minimality or that unmodelled requirements are safe.

The original R2.1 formal-model reference has an exact historical source digest. **Do not alter that frozen reference to change current method policy.** The optional reference references/abstraction-refinement-policy.md records this subsequent decision, MSR advantages/risks and the formal CEGAR proof obligations.

### Advanced mode — only if the actual problem requires it

Open references/formal-model.md when a decision depends on representation loss/refinement, complex preconditions or state transitions, formal assume/guarantee reasoning, uncertain verifier-to-goal soundness, probabilistic qualifications, search/optimization or self-refinement. In that case distinguish the real problem specification from the encoded verifier target, use legal operators, preserve model/source identity and provenance, and keep independent evaluators and rollback where needed. A formal-tool PASS proves only its encoded target. Do not run all advanced steps on routine file deletion or ordinary module reuse.

## Specialist routing

Use this Skill as the cross-layer scaffold, then delegate specialist questions to natural owners, for example:

- boundary/context -> `systems-engineering`;
- coupling/decomposition test -> `design-structure-matrix`;
- causal effect -> `causal-intervention`;
- failure propagation -> `fmea-fta`;
- unsafe interactions -> `stpa`;
- dynamics/control -> `feedback-control`;
- information influence / evaluator-anchor leakage -> `information-flow-analysis`;
- open-ended concept generation -> `ck-design`;
- candidate-population search -> `evolutionary-search`;
- sequential exploration allocation -> `exploration-policy`;
- organizational viability -> `organizational-cybernetics`;
- project-native transferable kernel -> `project-kernel-decomposition`.

For algebraic assume/guarantee composition or substitution, prefer an admitted formal-contract provider when the seam is actually formalized; do not create a proprietary universal contract language merely to satisfy this Skill.

Do not activate every lens. Choose only methods/providers that can change the decision.

## Essential distinctions

- Goal and domain truth are not decided by a LEGO; a verifier result does not replace the user's or owner's acceptance.
- Agent acts; Skill explains a method; Tool performs a bounded operation; Runtime/Host/natural owners retain their existing authority.
- Similar code does not guarantee a good shared boundary; independent deployments may benefit from duplication.
- Interface shape is not substitutability; local PASS is not whole-system PASS; execution is not semantic completion.
- PASS, FAIL and UNKNOWN are different evidence states. Never promote historical or toy-model proof into current real-world correctness.
- Method choice and even this LEGO procedure are removable if they cost more than they return.

## Output

Report only what changes the action: goal and consumer; whether the capability is needed; the smallest LEGO inputs/outputs/contract; decision to reuse, compose, replace or delete; actual source/owner effect; observed acceptance and unresolved UNKNOWNs. For complex cases include only the additional formal obligations that materially affect acceptance.

## Non-claims

- This Skill is not a definition of intelligence.
- It does not make a model, verifier, solver, benchmark or fitness function authoritative.
- It does not prove that encapsulation lowers total complexity.
- It does not guarantee global improvement, convergence or a fixed point under self-reference.
- It does not create new Runtime/Host/Gateway owners or a Representation/LEGO mega-service.
- It does not replace domain standards or the specialist Skills/tools it routes to.

## Stop condition

Stop when the real consumer outcome is served by the simplest owner-authorized composition, or when missing evidence is clearly UNKNOWN and has a concrete next decision. Re-enter after changes in goals, source, consumer, interfaces, effects or evidence. Do not keep decomposing or auditing to satisfy this Skill.

Optional exact mathematics: references/formal-model.md. Read only for a genuine composition/proof problem and use the natural mature formal provider on the actual task model; never create a routine self-conformance harness.
