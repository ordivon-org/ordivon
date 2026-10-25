---
name: recursive-lego-calculus
description: "Use for real Ordivon LEGO work: question goals and consumers, delete unneeded responsibilities, and compose input/output/contract LEGO. For mathematical contract algebra, assume-guarantee proofs, constraint and state-machine formal verification, or CEGAR counterexample refinement, open the optional formal reference and route to mature tools instead of adding a new framework."
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
3. **LEGO.** For a responsibility that remains necessary, name the six decision-relevant roles: **identity, one responsibility, inputs, outputs, behavioral contract, acceptance**. Add state, authority, effects, provenance, cost or children only when they change the decision. LEGO is the responsibility, not its file, class, Agent, Skill or Tool.
4. **Compose.** Connect compatible inputs/outputs, assumptions/guarantees, identities and effect boundaries. Reuse a real owner interface; do not duplicate truth or assume a successful subcomponent implies a successful whole. Split or share only if replaceability and consumer outcomes improve.
5. **Act.** Agents freely choose, compete, cooperate and adapt relevant Skills and Tools; no global minimality guarantee is assumed. Execute only through actual owner-authorized boundaries; no permanent role, mandatory workflow, or new LEGO execution service.
6. **Select.** Observe changed consumer behavior and the scoped native verification evidence. Report PASS, FAIL or UNKNOWN honestly. Keep, replace, merge or delete based on evidence; stop when further decomposition adds glue instead of value.

For a simple case the entire working note can fit in a sentence and six short fields. Reuse an existing API and its tests; do not create a separate LEGO specification file merely to restate the API.

### Optional functional LEGO roles — not a type system

At the broadest level, Ordivon distinguishes **能力型 LEGO (capability: executable
operator, API, bounded tool or service responsibility)** and **思想型 LEGO
(thinking/method: representation, strategy, inference or selection method)**.
These are two main decision-oriented categories, not a closed or exclusive
schema: an effective Skill/Tool composite can contain both. Refine into
consumer-proven subroles only when that split changes substitution, verification
or selection. All instances still use the same six-part canonical LEGO identity;
no additional registry, runtime enum, or mandatory metadata is implied.

The original identity/responsibility/inputs/outputs/contract/acceptance define one LEGO; the following **overlapping and revisable consumer-role lenses** do not replace this contract.

| Role | Contribution | Native carrier |
| --- | --- | --- |
| **Capability / operator** | Executes bounded reads, calculations, transformations or authorized effects | Tool/API, Git, FFmpeg, Z3, Bevy |
| **Method / strategy** | Guides an Agent's representation, selection, composition and testing of capabilities | Skill, CEGAR, experiment design, inverse synthesis |
| Representation | Makes problems, interfaces, structures or states expressible | types, graphs, schemas, models |
| Contract | Defines admissible inputs, guarantees, invariants and seams | owner API, assume/guarantee |
| Material / resource | Provides composable data or authored inputs | dataset, game recipe, media asset |
| Evidence | Supports or refutes a bounded claim | trace, test, proof result, receipt |

Tool often carries a capability; Skill often carries a method; either package can mix roles. A verifier is an operator, its technique a method, its predicate a contract and the proof output evidence. A produced artifact is **not automatically a reusable LEGO**: the composite becomes a higher-level LEGO only when a real consumer needs its independently replaceable contract. Roles classify a *responsibility in context*, not filenames, and are not asserted to have measured population proportions.

**Update by evidence:** after changes to consumer, interface, method or evidence, revise/merge/split/retire role labels in the existing natural owner and Skill/Tool discovery path. Promote a new role only for a repeated decision-changing distinction. Do not add role metadata to every file, a closed enum, a registry, validator, runtime, extra Agent or universal Skill index. Role assignment gives neither execution authority nor Formal PASS. If roles do not change the decision, omit them.

### Advanced mode — only if the actual problem requires it

Open references/formal-model.md when a decision depends on representation loss/refinement, complex preconditions or state transitions, formal assume/guarantee reasoning, counterexamples, uncertain verifier-to-goal soundness, probabilistic qualifications, search/optimization or self-refinement. In that case distinguish the real problem specification from the encoded verifier target, use legal operators, preserve model/source identity and provenance, and keep independent evaluators and rollback where needed. A formal-tool PASS proves only its encoded target. Do not run all advanced steps on routine file deletion or ordinary module reuse.

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

## Default proof discipline — CEGAR, not MSR

Do **not** optimize for a purported Minimum Sufficient Representation by default.
Neither minimality nor sufficiency has been established in general; trying to
prove them may cost more than the task. Start from an adequate *explicitly
scoped* Owner model; use actual or abstract counterexamples to decide whether
to fix a real defect or refine a sound abstraction. An abstract counterexample
is not necessarily a concrete defect; a verifier PASS needs an admitted bridge.
See `references/formal-model.md` (CEGAR section) for the full conditions.

`minimum-sufficient-representation` is an optional **method Skill LEGO** for
bounded, consumer-evidenced reductions, not a top-level architectural First,
required acceptance gate, proof of safety or a reason to delete unique evidence.
Prefer mature Owner model checkers, type systems and replay for real obligations.

## Essential distinctions

- Goal and domain truth are not decided by a LEGO; a verifier result does not replace the user's or owner's acceptance.
- Agent acts; Skill explains a method; Tool performs a bounded operation; Runtime/Host/natural owners retain their existing authority.
- Similar code does not guarantee a good shared boundary; independent deployments may benefit from duplication.
- Interface shape is not substitutability; local PASS is not whole-system PASS; execution is not semantic completion.
- PASS, FAIL and UNKNOWN are different evidence states. Never promote historical or toy-model proof into current real-world correctness.
- Method choice and even this LEGO procedure are removable if they cost more than they return.

## Output

Report only what changes the action: goal and consumer; whether the capability is needed; the justified LEGO inputs/outputs/contract; decision to reuse, compose, replace or delete; actual source/owner effect; observed acceptance and unresolved UNKNOWNs. For complex cases include only the additional formal obligations that materially affect acceptance.

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
