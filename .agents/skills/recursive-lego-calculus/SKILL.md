---
name: recursive-lego-calculus
description: "Use for real Ordivon LEGO work: question goals and consumers, delete unneeded responsibilities, and compose input/output/contract LEGO. For mathematical contract algebra, assume-guarantee proofs, constraint and state-machine formal verification, or CEGAR counterexample refinement, open the optional formal reference and route to mature tools instead of adding a new framework."
compatibility: Cross-platform. Helps Agents simplify and compose real responsibilities; use the formal reference only when necessary. Does not grant authority, execute effects, define domain truth or replace specialist verification.
metadata:
  ordivon-category: general
  source-authority: Ordivon Recursive LEGO Calculus R2.1, grounded in systems engineering, assume-guarantee composition, formal refinement, verification, optimization and existing canonical Ordivon method Skills
---

# Recursive LEGO Calculus

Useful when an Agent is deciding whether a capability should exist, be deleted, reused, decomposed or composed. Every formally DECLARED or ADMITTED independent LEGO, including an unproved method, capability, ordinary domain responsibility or composite, requires all eleven typed R2.1 coordinates; raw source/discovery and incomplete candidates are not admitted LEGOs.

## Adopt mature semantics

Use LEGO as an engineering profile of established modularity and contract-based
component design. Preserve six practical navigation questions, but full R2.1 coordinates are
mandatory for every independently declared LEGO, not every source file.
Do not invent another module calculus, registry or per-file record.

For a formal task, name the adopted semantic profile: typed signature,
behavioral assume–guarantee contract, protocol interface, or transition system.
Keep specification, implementation and verification evidence distinct. Reuse
that theory's satisfaction, composition and refinement rules with their side
conditions; interface shape and invariant satisfiability alone do not establish
safe composition. See references/formal-model.md, “LEGO contract — adopted
component semantics”, for the exact mapping and sources.

An architectural contract is a legitimate immediate goal. During architecture
reform, establish the abstract design obligations and track implementation and
terminal domain acceptance separately; do not require every downstream
business outcome before improving the kernel. This does not turn a design
proof into deployed-system acceptance.

## Mature-provider default — make the next replacement cheaper

Before material design or implementation, **reuse existing candidate evidence**
and native interfaces; perform a bounded official-standard, mature-project and
relevant-research search only for remaining unknowns. Stop when a candidate
can be decided; don't repeat unchanged investigations.

Prefer **delete → internal reuse → mature external provider → compose/configure
→ thin adapter → upstream contribution → evidenced custom implementation**.
Evaluate candidates against the same consumer contract and negative tests,
including license, maintenance, assumptions and effects. Keep frontier work
isolated; justify custom work by a concrete unmet contract or counterexample.

For each substitution, **retain provider-independent acceptance/proof duties**,
native or standard interfaces, exact source/assumption evidence and any needed
rollback and retirement conditions. Reuse these at the next replacement.
Do not create a universal adapter, new registry, Agent or separate LEGO
calculus for hypothetical future reuse; verifier PASS is always scoped.

For **Formal proof-object assurance**, reuse native `tools/formal/verify.py`
and the installed Lean toolchain's `leanchecker`, not a custom checker.
The same-toolchain binary digest is requalified before and after.
Core and variation `.olean` declarations are each replayed; a
`debug.skipKernelTC` dishonest proof is expected to be rejected even
if compilation and `#print axioms` pass. Non-`--fresh` assumes imported
library environments. This is not an external comparator, installed-code
refinement, source-issuer authorization or permission for domain effects.

### Conditional negative-consumer proof (not deletion authority)

For a contested retirement, use
references/consumer-rooted-retirement.md and the axiom-free Lean theorem
OrdivonR21.RetirementClosure.no_live_consumer_if_closed_and_current
in tools/formal/RecursiveLegoRefinement.lean. Its four required premises
are complete observation of reachable live consumers, no observed witness,
currentEdges subset snapshotEdges, and currentLive subset snapshotLive.
The same file proves three counterexamples when observation closure,
dependency currentness or liveness currentness is missing. A current
systemd file scan or loaded-manager query does **not** establish these
premises; retain UNKNOWN until a separate concrete Owner witness closes
them. This conditional R2.1 pre/inv/prov law is neither a new LEGO nor
permission to delete a Workspace.

The native Formal owner now checks a **consumer-owned theorem statement** in
`tools/formal/RecursiveLegoRetirementChallenge.lean` as part of
`mise run formal:verify`. The independent challenge must prove the exact
four-premise retirement rule and the three missing-premise counterexamples;
a same-named, axiom-free but weakened producer theorem is **not** sufficient.
This protects the *meaning of the modeled permission*, not live consumer
observation, actual filesystem deletion authority, or proof-source issuer.
Do not duplicate the checker as a new Skill or service.

## Practical rule

A LEGO is one **goal-conditioned, replaceable responsibility** with identity, inputs, outputs, behavioral contract and acceptance. It is not a file, Agent, Skill, Tool or required runtime object.

Use whichever of these questions changes the current decision. They are **not** a mandatory checklist, fixed order or Agent organization:

1. **Goal.** Name the Human/domain outcome, exact current source, real consumer and natural owner. If the goal itself is doubtful, investigate before building.
2. **Zero-base.** Pretend the existing file, service, Skill and LEGO do not exist. Trace every consumer through to a real outcome; consumers that exist only to keep each other alive do not justify retention. Prefer deleting the whole chain or using a mature existing provider.
3. **LEGO.** For a responsibility that remains necessary, name the six decision-relevant roles: **identity, one responsibility, inputs, outputs, behavioral contract, acceptance**. Any formally DECLARED/ADMITTED LEGO **MUST instantiate every typed coordinate** of `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` with typed semantics, no omitted fields. An actually stateless or effect-free unit may use a justified Unit/empty effect; an unknown coordinate must be an explicit typed UNKNOWN(reason, scope, obligation) and blocks only proof claims depending on it. Complete declaration does not imply MODEL_PROVED, CODE_REFINED, INSTALLED_CURRENT or DOMAIN_ACCEPTED. LEGO is the responsibility, not its file, class, Agent, Skill or Tool.
4. **Compose.** Connect compatible inputs/outputs, assumptions/guarantees, identities and effect boundaries. Reuse a real owner interface; do not duplicate truth or assume a successful subcomponent implies a successful whole. Split or share only if replaceability and consumer outcomes improve.
5. **Act.** Agents freely choose, compete, cooperate and adapt relevant Skills and Tools; no global minimality guarantee is assumed. Execute only through actual owner-authorized boundaries; no permanent role, mandatory workflow, or new LEGO execution service.
6. **Select.** Observe changed consumer behavior and the scoped native verification evidence. Report PASS, FAIL or UNKNOWN honestly. Keep, replace, merge or delete based on evidence; stop when further decomposition adds glue instead of value.

For raw discovery and INCOMPLETE_CANDIDATE notes, six navigation fields may suffice; they are not independently admitted LEGOs. Every formally DECLARED or ADMITTED independent LEGO needs a complete typed eleven-coordinate contract before any property proof. The declaration is not itself a checked mathematical obligation; proof, source refinement, installed state and user acceptance have independent evidence grades. A version-qualified InstanceOf(archetype, parameters, environment, state, effects) may resolve the full effective contract without duplicating eleven declarations per Run or message. This is a strict admission rule, not permission to create a separate registry, Schema, verifier or eleven new files per LEGO. Never fabricate effects, cost, zero approximation or evidence to fill a field. Reuse the existing source/API/proof carrier.

### Agent public contract view and actual capability invocation

Discovery is a projection of the **same full effective R2.1 contract**, not a
second incomplete LEGO or registry. L0 previews the goal/role/version and
flags known external effects, required authority, failures/timeouts, and
unknown proof/currentness. L1 provides typed I/O, pre/post/invariants,
errors, progress/time bounds, effects, authority and scoped c/epsilon values
(or explicit UNKNOWN). L2 adds proofs, provenance, source cuts and change
readsets. L3 unfolds internals only when the Agent needs them. Hide irrelevant
implementation, never decision-critical effects or assumptions.

Information disclosure is NOT execution authorization: the actual MCP/CLI/
Gateway/Runtime owner must check current principal, grant, scope, inputs and
expiry/revocation at action time. A once-safe public preview is not a license
for later effectful invocation. UNKNOWN demands READ_MORE/UNFOLD or refusal.

Goal-relative required capability coverage, core LEGO transformative leverage
and ordinary terminal product value are independent: an ordinary output can be
required and commercially central. True consumer evidence must reach a named
observed domain or scoped architectural acceptance; mutual references and
test-only cycles do not prove domain use. Any claim of measured improvement
names a baseline source/version, observer, predicate/metric, instrument and
guardrails, or states UNKNOWN. Prioritize consumer bottlenecks and qualified
alternatives, not raw dependency fan-out.

### Optional functional LEGO roles — not a type system

At the broadest level, Ordivon distinguishes **能力型 LEGO (capability: executable
operator, API, bounded tool or service responsibility)** and **思想型 LEGO
(thinking/method: representation, strategy, inference or selection method)**.
These are two main decision-oriented categories, not a closed or exclusive
schema: an effective Skill/Tool composite can contain both. Refine into
consumer-proven subroles only when that split changes substitution, verification
or selection. All admitted responsibilities use the same eleven-coordinate effective LEGO contract;
instances may inherit a qualified versioned archetype without duplicate per-row metadata.
No additional registry or runtime enum is implied.

The six navigation questions alone do not qualify a declared LEGO; the following **overlapping and revisable consumer-role lenses** do not replace this contract.

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

## Consumer-rooted retirement (optional)

When removing a PR, Git ref, source responsibility or Runtime Workspace with
disputed live consumers, read references/consumer-rooted-retirement.md.
Use the existing Repo SourceCut prefilter, natural Owner tests and native
Runtime/Host/Git tools. Source equality alone does not authorize retirement;
separate production, installed, dynamic, test-only and historical consumers.
PR close, remote ref delete, source retirement and Workspace close are distinct
effects. Keep uncovered consumers UNKNOWN. Do not create a new collector,
registry or independent Skill. Do not invoke this reference for routine edits.

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

- All declared/admitted independent Method, Capability and Composite LEGOs require complete typed R2.1 coordinates; an unfinished candidate remains explicitly unadmitted.
- External value acceptance is separate from resource cost c and approximation epsilon: bind the named goal/consumer, observable predicate or metric, baseline or fixed specification, checker/instrument, decision threshold, guardrails, current evidence and UNKNOWN. A mathematical architecture goal is not an installed product result. Test-only self-consuming cycles do not establish terminal use.
- Agent public information may hide implementation but cannot conceal decision-critical errors, effects, authority limits, proof standing or source currentness. Actual invocation still needs separate Owner authorization.

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
