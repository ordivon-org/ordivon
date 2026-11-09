# Agent Contract Execution — R2.1 Reform Spec

**Source baseline:** `3b43977e682d8c7668f6371ffd998c7821e4312a` (Git main, 2026-11-09).
**Standing:** implementation spec; decisions are accepted design constraints, not proof of installed behavior.
**Goal:** make architecture-critical agent mistakes fail at their natural Owner boundary while keeping solution exploration and real delivery possible.

## 1. Problem and desired outcome

An Agent may faithfully optimize a mistaken local representation. This is visible in the Authority Catalog incident: PR #1944 rewrote historical registration witnesses to current path locations; PR #1961 restored them; PR #1942 proposed the same regression and was closed; PR #1962 introduced a Git-base/head history check. Local path existence and catalog schema success were not historical truth. The desired improvement is not a longer system prompt or a second orchestrator. It is a source-bound, consumer-observed chain of requirements, candidate action, native execution and independent acceptance.

Success means:

1. A change cannot satisfy one locally convenient metric by violating a proven invariant at the responsible Owner seam.
2. A model's `candidate_completed`, Runtime Job exit, current document, or Skill activation never masquerades as domain acceptance.
3. A plan, research note or `needs_input` conclusion is not misrepresented as completed execution; real blockers remain reportable as scoped UNKNOWN.
4. Agents may choose DELETE / REUSE / COMPOSE / IMPLEMENT and use mature upstream providers without extra approval loops for routine work.
5. Every retained cross-owner contract is discoverable via the *existing* route and has a concrete consumer, a source version and a failing negative control.

## 2. Prior art adopted, and what is not adopted

Source-checked official upstream Git main revisions on 2026-11-09:

- Matt Pocock Skills, [`4ae2317ddb22b046e264`](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e264): `to-spec` (derive requirements from established context), `to-tickets` (dependency-explicit vertical tracer bullets), `codebase-design` (deep module at a narrow seam), `tdd` (public-seam red/green) and `code-review` (spec vs coding standards). No issue-manager bootstrapping where GitHub and Host already suffice.
- ECC, [`d2ef2680594f9a17526a`](https://github.com/affaan-m/ECC/tree/d2ef2680594f9a17526a): selective, event-triggered `PreToolUse` / `PostToolUse` checks, optional profiles and progressive Skill loading. Integrate *principles* at existing Runtime/Gateway admission and GitHub Owner CI, not an unqualified Claude hook runtime or copied profiles.
- Superpowers, [`22f0b463e7a5e579904d`](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904d): isolated worktree, writing-plans with executable steps, test-first incremental implementation, verification-before-completion and scoped code review. Existing Runtime Workspace and `mise` are the host-native realization.

The repositories are methodology **providers**, not execution/truth/permission authorities. External source instructions do not override Ordivon AGENTS.md or Owner contracts. Do not import their complete Skill trees, management planes, agents, global settings, hooks, memory systems or language requirements. License and exact version must be reassessed before vendoring any bytes; this iteration vendors none.

## 3. Representation: goal-conditioned effective R2.1 LEGO

For independently admitted responsibility \(\ell\), use the canonical full typed tuple:

`ell = (I, O, S, pre, post, inv, eff, c, epsilon, prov, unfold)`.

| Coordinate | Meaning for the execution reform |
| --- | --- |
| `I` | Typed Goal/Consumer/SourceCut/Authority and qualified input evidence. |
| `O` | Candidate result, scoped execution observation, consumer acceptance or evidenced noncompletion; never conflate them. |
| `S` | Existing Host Work/Agent Run/Runtime Job/owner-domain states, not another global state database. |
| `pre` | Relevant input/source/authority assumptions checked by the natural owner. |
| `post` | Action-level or consumer-level behavioral guarantee owned by its producer. |
| `inv` | History preservation, effect identity, evidence non-promotion and domain acceptance separation. |
| `eff` | Explicit potential physical/external effects; a Skill has no implied effect authorization. |
| `c` | Scoped resource/time/verification cost or typed `UNKNOWN`, never invented zero. |
| `epsilon` | Explicit approximation/error bound or typed `UNKNOWN`; `0` only where proven exact. |
| `prov` | Model/source/contract/observation version, toolchain and evidence identity. |
| `unfold` | Bounded L0-to-L3 disclosure of assumptions, errors, proof gaps, implementation only as needed. |

A procedure such as Matt's `to-spec` is a **method candidate**: this plan does not automatically admit it as an independent runtime LEGO. A method becomes an independently contractable LEGO only if its real consumer and replaceable interface justify it; then every coordinate must be instantiated with typed evidence, including UNKNOWN. Do not invent one record per file or per workflow stage.

### Adopted semantic profile and proof boundary

Use assume–guarantee composition at producer/consumer interfaces, typed transition systems for statuses, and source-bound refinement where a consumer demonstrably needs proof. Define `RunCandidate`, `ExecutionReceipt` and `DomainAcceptance` as **distinct conceptual evidence classes**, not a mandatory new serialized universal enum.

Let `Accepted_c(x,w)` mean consumer `c` verifies outcome `x` with current scoped witness `w`. For every existing implementation claiming task acceptance:

- **Safety S1:** `DomainAccepted => Exists(CurrentConsumerWitness)`.
- **Safety S2:** `RuntimeJobSucceeded !=> DomainAccepted`, `AgentRunCandidate !=> DomainAccepted`.
- **Safety S3:** historical registration content at date `t` is not rewritten merely because current navigation changed at `t'`.
- **Safety S4:** `UNKNOWN` never silently becomes `FALSE`, `FAIL` or `PASS`.
- **Effect S5:** a Skill/router/model belief never authorizes an effect; the executing Owner checks the current principal/operation/source.
- **Progress P1 (conditional):** when a task has an available qualified action, finite resources and an admitted recovery path, it must reach a new observable frontier or explicit bounded blocker. No unbounded fairness guarantee or promise of eventual domain success is implied.

Formal targets are selected only where they reduce a named defect. Separate (a) mathematical model proof, (b) implementation refinement, (c) current installation evidence and (d) domain acceptance. A Lean/Z3/TLA+/Quint PASS does not imply the other three. Use CEGAR to refine abstraction on counterexamples, without defaulting to claims of minimal sufficient representation.

## 4. Ownership and public seams

| Responsibility | Natural Owner / real seam | Existing, reusable behavior | Requested improvement |
| --- | --- | --- | --- |
| Goal → source/consumer | Human/domain Owner; `AGENTS.md`, Owner README, `docs/start/tasks.md` | SourceCut / owner mapping / consumer navigation | Route material agent-engineering reform to this Spec and selected Skills only when relevant. |
| Reusable thinking method | project `.agents/skills/method-router/` and Skills MCP `search/resolve/read` | on-demand method selection, R2.1 links, package revisions | Add one optional upstream-informed engineering reference, not a second router. |
| Plan → independently demonstrable delivery | GitHub PR/Issue and existing Host Work | Work snapshots; PR gates; dedicated Runtime Workspace | Tracer-bullet slices with true blocking edges; no one-file-per-LEGO task explosion. |
| Run candidate and structured result | `services/harness/` public `HarnessRunContract`, `AgentRunConclusion` | `candidate_completed` vs `needs_input`, explicit unknowns, independent receipts | Preserve candidate-only meaning, prove boundary on a real caller where missing. |
| Physical execution / recovery | `services/runtime/` Job/Attempt, effect identity and reconciliation | native Postgres-backed admission and Job receipts | Consumer-specific effect/readback checks, never infer semantic task completion from exit 0. |
| Work continuity | `services/host/` Work Snapshot, Topic/Message | source snapshots, statuses | Repair only demonstrated consumer blockage; Work is not execution. |
| Gate at critical boundary | Owner-native tests; `.github/workflows/ci.yml` | affected-owner tasks / Merge Queue; historical provenance gate | Add highest useful owner-native negative controls, not global prose-rule linters. |
| Real user outcome | Artifact, Media, Game, Capital, Data, etc. | domain-specific contracts/tests and external effects | The relevant consumer provides final accept/reject/UNKNOWN. |

**No new global Agent owner, TaskDisposition database, arbitration broker, completion oracle, universal schema, second proof registry, hook daemon, run scheduler, or hidden agent approval system.** Existing Harness already means candidate completion, not task completion; reproducing that machine is incorrect.

## 5. Implementable slices (each ships one usable path)

Each slice has a native Owner, observable result, a negative example and a check command. Dependencies are real blocking edges, not an organizational mandate. Existing active PRs must be checked before work to avoid concurrent modification.

### T0 — Source and method intake (no blockers)

- **Consumer:** the project Agent solving a substantial code/system task from a cold source snapshot.
- **Deliverable:** this Spec plus a bounded routing reference within the existing `method-router`; source pins, exact responsibilities and acceptance/readback states are clear. No upstream vendor or global install.
- **Native verification:** `mise run skills:verify`; check project Skills resolve/read on available installed provider, if accessible; Markdown references and root architecture checker.
- **Negative:** asking for a routine one-line edit does not trigger a required planning apparatus; a tool provider is not treated as an Owner or as proof.
- **Done when:** source and Skill consumer can follow the route at the exact source revision; installed currentness is separately observed or marked UNKNOWN.

### T1 — Protect historical truth as a first contract (already partly done; T0 not a blocker)

- **Owner:** Authority Catalog; `registrationBasis` at registered time vs live link at HEAD.
- **Current foundation:** merged #1961 repaired history; #1942 was closed; merged #1962 includes a source/base change check.
- **Follow-up:** inspect whether deletion/re-creation, renamed identity, rebases, historical corrections and actual CI merge-group readset have legitimate contract coverage. Do not ban authorized retirement or true evidence-backed correction merely to keep a field immutable.
- **Negative:** rerun prior historical PR as a counterexample; show legitimate navigation-only change still passes.
- **Done when:** scoped owner-native checks preserve historical semantics without preventing ordinary deletions and source migration.

### T2 — Harness candidate cannot certify consumer completion (T0 only for method; functional work independent)

- **Owner:** Harness plus one real caller; public Run API and consumer acceptance, not `AGENTS.md` prose.
- **Deliverable:** where the actual caller currently conflates them, use the existing `candidate_completed`/receipt/current witness types or a narrow adapter; do not add a global enum. A candidate with unresolved UNKNOWN remains representable.
- **Negative:** candidate summary says success while the downstream consumer rejects or has not checked it; `DomainAccepted` remains unavailable. Positive: consumer witness permits its specific acceptance.
- **Native check:** focused harness/consumer tests then `mise run harness:verify` or the exact documented queue task. If no real violating caller is found, **delete this slice as redundant** and record the evidence.

### T3 — Runtime/Host progress truth without blocking progress (depends on a demonstrated owner consumer)

- **Owner:** Runtime/Host where execution effects and Work projection are genuinely consumed.
- **Deliverable:** a real workflow resumes from durable state, makes an eligible action, produces new evidence, or reports a justified, scoped blocker. Reuse existing cancellation, idempotence, reconciliation and Work Snapshot instead of starting a second state machine.
- **Negative:** repeated notes/identical plans are not counted as new execution; a timed-out Job cannot be auto-declared semantically successful. Positive: a legal batch cleanup/action remains possible without per-record approvals.
- **Check:** native PostgreSQL state/readback and affected consumer test; run failure/recovery test only if it changes the contract.

### T4 — Owner domain acceptance and effects (T2/T3 only if their actual seams are required)

- **Owner:** one at a time, whichever of Artifact/Media/Game/Capital/Data has an evidenced acceptance gap.
- **Deliverable:** a thin vertical path from contract to native execution to consumer acceptance. Apply established provider interfaces and the smallest suitable formal/checking tool.
- **Negative:** a misleading local PASS, missing provider effect, false source currentness, or replayed output cannot be promoted to domain accepted.
- **Check:** domain-specific native `mise` plus independent readback. For Capital, paper/demo/live remain distinct and no capital is transferred as part of this engineering work.

### T5 — Retire duplicate policy and workflow instructions (after the new native consumer is effective)

- **Owner:** each affected module and existing project Skills.
- **Deliverable:** remove stale duplicated steering docs, redundant Skill wrappers, obsolete alternative validators and unused plans only after the real consumer is covered; retain unique historical observations and valid source evidence.
- **Check:** current consumer/readback, owner tests, exact Git diff and PR/Merge Queue. PR success without installation is `MERGED`, not `CONSUMED`.

## 6. Small-step procedure for each slice

1. **Select:** identify actual consumer, natural Owner, exact current Git main, live caller and one behavior it lacks. If the capability already works, do not create a ticket.
2. **Specify:** define a thin vertical path from input through public Owner seam to observable acceptance; full typed R2.1 only for an independently declared LEGO. State assumptions, competing explanation, likely counterexample and what remains UNKNOWN.
3. **Red:** reproduce a real old error at the public seam; the failing condition must be able to distinguish broken and fixed behavior. No weak-model benchmarks or generic persona tests.
4. **Green:** choose DELETE → REUSE local → mature upstream → COMPOSE → minimal adapter → custom only if necessary; change one owner-native implementation and any directly affected consumers.
5. **Refine:** model-check or prove only an actual invariant requiring it; link assumptions, code refinement boundary and current source. A formal example without code binding is not a production fix.
6. **Verify:** run focused negative/positive tests; then affected Owner's native task; inspect full output, failures/skips and one independent consumer readback. Use isolated Runtime Workspaces; do not touch other Agents' branches.
7. **Review:** compare fixed-base diff to both the Spec and repo conventions; verify real consumer value and DELETE redundant additions. Correct surfaced flaws immediately.
8. **Integrate:** commit, push, create PR; use GitHub Merge Queue. Report SOURCE, MERGED, INSTALLED, LOADED, EXECUTED and CONSUMED separately, with explicit remaining UNKNOWN; no claim of background work.

## 7. Quality gates and acceptance

| Gate | Evidence | What it does NOT claim |
| --- | --- | --- |
| Valid Spec/readable Skill | current Git bytes, working references, Skills MCP path resolve/read when installed | Agent followed instructions; domain outcome |
| Native RED→GREEN | bad counterexample rejected, good case accepted through Owner public seam | complete correctness across all inputs |
| R2.1 model | complete typed contract, named theorem/model verdict, assumptions | implementation refinement or real effect |
| Code/consumer refinement | current implementation behavior checked against property at the target seam | semantics beyond exercised scope |
| PR / CI | exact SHA, review, required job results, Merge Queue | deployed owner version |
| Real usage | provider readback/effect receipt, consumer acceptance currentness | all possible future domain success |

Avoid arbitrary percentage scores, universal checklists and unjustified time estimates. Review blockers are genuine failed preconditions or unverified assumptions, not model preference or automatic human approval. Resource budgets and environment constraints remain real.

## 8. Risks and decisions

- **Verifier wrong target:** one positive and one true negative control for every material new gate; compare actual consumer semantics, not cosmetic scores.
- **Method maximalism:** activate relevant upstream procedures only when a multi-step implementation needs them. One-line changes do not require a plan.
- **Model/Owner semantic drift:** R2.1 model proof is not code refinement; source and tool identities must be pinned.
- **Plan accumulation:** GitHub and Host are the canonical plan carriers; do not create issues for T2–T5 absent a confirmed actual caller. This Spec is a temporary architecture decision document; once active consumers and tests subsume it, merge into owner docs or retire it.
- **Currentness and history:** historical provenance is not a live path, and stale reference is not proof a source is absent.
- **Conservatism feedback:** progress is judged by actual new effects/evidence and qualified blockers, not reports written or steps counted.

## 9. Exit conditions and next executable action

This reform is not closed by committing this Spec. Its architecture-level exit requires: (a) T0 live source navigation works and is in main; (b) T1 existing historical provenance gate retained with true negative coverage; (c) at least one independently observed Owner consumer misconception is eliminated at a real implementation seam (T2/T3/T4), or those proposed changes are deliberately retired as duplicates with evidence; (d) existing test/CI records clearly separate proposal, implementation, proof, installation and domain acceptance; (e) no additional governance service or obsolete duplicate workflow remains.

**Immediate frontier:** implement T0 in `method-router` and validate with existing Skills consumers; independently inspect T1/T2 callers and implement the first concrete failing native consumer rather than launching a broad redesign.

## 10. First effective method profile, and precise next-file map

The selected T0 `method-router` delivery route has an **effective R2.1 declaration**, with no assertion of automatic proof or installed capability:

| Coordinate | Typed effective value |
| --- | --- |
| `I` | `EngineeringIntent(goal, consumer, naturalOwner, gitSourceCut, constraints, evidenceRefs)`; the intent comes from the caller, not invented by the Skill. |
| `O` | `AdvisoryEngineeringRoute(specCandidate, testSeam, verticalSlices, evidenceRequirements, unresolvedUnknowns)`, not a permission or completed Task. |
| `S` | `Unit` for the read-only procedure; durable Host Work or Git state belongs to the corresponding Owner. |
| `pre` | Caller names the real consumer and an adequate source boundary; unknown scope leads to bounded inquiry, not an arbitrary gate. |
| `post` | Advisory route points to qualified incumbent interfaces and native verification; application remains a caller decision. |
| `inv` | No model result promoted to real consumer acceptance; historical witness and SourceCut identity not silently revised; UNKNOWN preserved. |
| `eff` | `Empty` for Skill lookup/read. Git/Runtime/Owner actions are separate explicit effects. |
| `c` | `UNKNOWN(cost-of-method-use, until measured for the named consumer)`, no assumed zero. |
| `epsilon` | `UNKNOWN(semantic-approximation, advisory method has no universal accuracy bound)`. |
| `prov` | Ordivon source baseline above; upstream Matt/ECC/Superpowers Git pins and project Skill file identity; current installed digest is `UNKNOWN` until read back. |
| `unfold` | L0 discover `method-router`; L1 read SKILL; L2 optionally read `references/agent-engineering-delivery.md` and this Spec; L3 source/native verifier only as needed. |

**Declaration standing:** scoped Method LEGO *definition*, with typed unknowns. `MODEL_PROVED`, `CODE_REFINED`, `INSTALLED_CURRENT` and `DOMAIN_ACCEPTED` are **not** claimed. Do not turn this table into a global LEGO schema or second router.

Exact implementation readset for the first and following vertical slices:

| Slice | Owner-owned source / concrete next place to inspect | Command / observation / STOP |
| --- | --- | --- |
| T0 | `.agents/skills/method-router/SKILL.md`, `references/agent-engineering-delivery.md`, `docs/start/tasks.md`, `extensions/chatgpt-skills-mcp/tests/test_method_router_skill.py` | `mise run skills:verify`; consumer `SkillCatalog.resolve/read_text` scoped to actual project. Source-only acceptance until installed readback. |
| T1 | `catalogs/authorities/scripts/check_historical_registration.py`, `catalogs/authorities/tests/test_authority_catalog.py`, `.github/workflows/ci.yml` | `mise run authority-catalog:verify`; prior #1942 rejection and real navigation-only legal change. **STOP** if current gate already covers the proven need. |
| T2 | `services/harness/src/ordivon_harness/ordivon/model.py`, `src/ordivon_harness/completion.py`, `tests/test_structured_completion.py`, one actual downstream caller | First demonstrate a caller that promotes `candidate_completed` to DomainAccepted without consumer witness. If absent, do not change Harness; report that the existing boundary already holds. |
| T3 | `services/runtime/README.md`, `services/host/README.md`, `services/harness/ARCHITECTURE.md`, the actual Job/Work public client and PG tests discovered from Owner | Select one currently failing resume/progress consumer and its native test; never infer a task is blocked solely because the model asks for more planning. |
| T4 | `capabilities/artifact/README.md`, `capabilities/media/README.md`, `domains/game/README.md`, `domains/capital/README.md`, `packages/data/README.md` | Pick one real terminal consumer and write its actual owner acceptance test; preserve independent accounting/financing effects. |
| T5 | same specific Owner documents / Skills changed by T2–T4 | Delete redundant implementation and instructions only after live consumer equivalent readback; native Owner verification. |

The `docs/start/tasks.md` link is a navigation projection, not new task authority. This document is **one bounded planning carrier** with explicit consumers, not a standing requirement to create six GitHub tickets before any action. Its future deletion is permitted when superseded by working Owner contracts/tests.

---

## 11. Mathematical and computer-science foundation: adopted thought-LEGO profiles

**Evidence update, 2026-11-09.** This section extends the existing R2.1 contract; it does not supersede the eleven-coordinate definition or proclaim a theorem about installed code. The sources below are primary papers, official reference implementations, and existing Ordivon-native theorem/consumer paths. These are selectively activated **method lenses**, not eleven new runtime modules.

| Decision / thought LEGO | Mathematical foundation and precise question | Existing Ordivon carrier / executable obligation | Explicit non-claim |
| --- | --- | --- | --- |
| T11.1 **Hoare contract / weakest precondition** | A Hoare triple `{P} a {Q}` means that, if action `a` terminates from a `P` state, `Q` holds; distinguish partial correctness from termination. Choose a predecessor obligation `wp(a,Q)` when it changes execution admissibility. | Owner-native input validation, state-machine tests, Kani/Verus/Dafny as applicable. | A precondition or source comment is not proof that all actual effects honor `Q`. |
| T11.2 **Assume–Guarantee contract algebra** | `C=(I,O,A,G)`. Discharge `G_producer => A_consumer` under typed adapters, complete scopes and effect/temporal compatibility. Use Pacti's already-researched composition/refinement/quotient rather than a custom algebra. | `.agents/skills/compositional-contracts/SKILL.md`, `tools/formal/RecursiveLegoRefinement.lean` and the natural owner's concrete consumer test. | Identical JSON schemas, local PASS or a composed paper contract do not prove real consumer compatibility. |
| T11.3 **Behavioral subtyping** | A replacement must not narrow inputs accepted by the original consumer or weaken their required outputs/history invariants; an implementation must remain substitutable in the consumer's observation context. | Existing Lean `Refines`, `refinement_preserves_implementation`, `narrowed_assumptions_cannot_substitute` and source-bound Owner adapters. | Do not require byte-for-byte equality of an internal implementation. |
| T11.4 **Abstract interpretation / evidence information order** | Abstractions summarize sets of possible concrete states; a sound over-approximation may produce UNKNOWN rather than false confidence. `UNKNOWN` is an evidence limitation, *not* a domain FALSE. | `recursive-lego-calculus` and Owner claim/evidence projection; native verification for refuted/proven and unresolved hypotheses. | A status hierarchy is not a universal, timeless scalar lattice; source/environment drift can invalidate old evidence. |
| T11.5 **CEGAR** | If an abstract counterexample exists, concretize it; if realizable, fix source/contract, otherwise refine the abstraction. Stop when the actual consumer decision is resolved. | `.agents/skills/recursive-lego-calculus/references/formal-model.md`, actual Owner negative fixtures, model checker. | A finite abstract witness is not automatically a real-world exploit. |
| T11.6 **TLA safety/liveness** | `Spec = Init ∧ □[Next]_vars ∧ Fairness`. Prove `□Inv`; assert progress only with explicit environmental fairness, resources and nonblocking qualified action assumptions. | Existing TLA+/TLC/Quint and Host/Runtime native state transitions. | Generic `◇Done` is not provable for unconstrained external services or human requests. |
| T11.7 **Separation Logic / frame law** | A locally valid state transformation preserves the nonoverlapping frame `R` only under its locality and heap/ownership assumptions. Use consumer readset/footprint to avoid global reproof. | Existing natural Owner/SourceCut partitioning, immutable-input witness, consumer-directed regression tests. | `git grep` or a file-level ownership table is not a proof of exclusive physical or dynamic ownership. |
| T11.8 **Effect/replay algebra** | Distinguish intent, admitted operation, physical effect, receipt, reconciliation and semantic success. A timeout cannot prove nonexecution; exactly-once effects require an owner/provider-specific mechanism. | Runtime Job/Attempt, Harness Run/Tool and domain receipts; native idempotency keys, PostgreSQL transactions and effect readback. | Neither Job `succeeded` nor a retry policy is a universal exactly-once guarantee. |
| T11.9 **Systems engineering V&V** | Track versioned requirement, observation method, instrument, product and anomaly; verification asks whether specification holds, validation asks whether the realized product meets the consumer need. | Existing Owner `mise` verification, GitHub Merge Queue, installed/current readback and domain acceptance. | `SOURCE` / `MERGED` / `MODEL_CHECKED` are not synonymous with `INSTALLED` / `DOMAIN_ACCEPTED`. |
| T11.10 **Proof-carrying evidence / independent witness** | A decision must have a witness that binds the **specific proposition**, exact subject, source revision, checker/readset and validity interval. A generic PASS supporting a different proposition is not a witness. | Artifact `claim_coverage.py`, Authority provenance gate, Scope-specific formal proof and direct consumer tests. | An arbitrary pointer to an object with `status=PASS` does not prove the required individual claim. |

### 11.1. Original mature sources and mapping

- **Contracts:** [Pacti official getting started](https://www.pacti.org/docs/getting_started/) and [Pacti source](https://github.com/pacti-org/pacti) (2025 published compositional A/G implementation). Use only for a mathematical contract whose assumptions and guarantees can be represented in its supported theory; check operator side conditions before declaring refinement.
- **Behavioral substitution:** [Liskov & Wing, *A Behavioral Notion of Subtyping* (1994)](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf). Replacement must satisfy real consumer invariants/history, not merely export identical method names.
- **State and progress:** [Lamport, *The Temporal Logic of Actions* (1994)](https://lamport.azurewebsites.net/tla/papers.html) and [Specifying and Verifying Systems with TLA+](https://lamport.org/pubs/spec-and-verifying.pdf). Use Init/Next/temporal fairness rather than naive finite-run liveness claims.
- **Abstraction:** [Cousot & Cousot, POPL 1977 abstract interpretation](https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml) and [Clarke et al., CEGAR](https://web.stanford.edu/class/cs357/cegar.pdf). Define concrete-to-abstract observation before relying on a model verdict.
- **Local reasoning:** [Reynolds, *An Overview of Separation Logic*](https://www.cs.cmu.edu/afs/cs/user/jcr/ftp/seplogoverview.pdf). Do not assert a frame law when operations share mutable state or external effects.
- **Native model-based tests:** [Hypothesis rule-based state machines](https://hypothesis.readthedocs.io/en/latest/stateful.html). Use if the Owner already has a meaningful stateful API to falsify, not as a mandatory test for every file.
- **Realization and V&V:** [NASA Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf); [AWS durable execution idempotency/retry guide](https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/) for distinguishing replay/at-least-once from external effect truth.
- **Engineering procedures:** upstream [Matt `to-tickets`](https://github.com/mattpocock/skills/blob/main/docs/engineering/to-tickets.md), [ECC Hooks](https://github.com/affaan-m/ECC/blob/main/hooks/README.md), [Superpowers writing-plans](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md). Version-qualified source pins remain section 2. These are NOT formal proof systems and do not confer execution authority.

**Method selection:** use `method-router` to choose the smallest method that can change a decision. For example, a missing producer/consumer assumption calls for T11.2, not all ten methods. A cancellation/retry defect calls for T11.6 plus T11.8. An incomplete evidence claim calls for T11.4 plus T11.10. Only formalize an independently contractable replacement as the complete R2.1 `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`; other lenses are borrowed mature methods, not automatically admitted new LEGOs.

## 12. Precise refinement calculus and proof duties (no new calculus)

Let a stateful capability operate with state `s` and visible event trace `τ`:

`R_impl ⊆ (I × S) × (O × S × Trace(Eff))`.

Let `Obs_c` be the observation function of the *named consumer* `c`, projecting internal state/transitions away but retaining every visible error, effect, timeout, cancellation and ordering condition relevant to `c`. Let `E` be the explicitly qualified environment, and `α` map concrete implementation states to the model's states. The candidate implementation is a contextual refinement only if the associated assumptions and simulation/trace obligations establish:

`Obs_c(Traces(R_impl | E)) ⊆ Obs_c(Traces(R_spec | E))`.

This is a **proof obligation**, not a theorem proved by writing this equation. The subset is sometimes too strong without allowing stuttering, internal-event hiding, weak simulation and fairness; the natural Owner must choose an observer and justify the transport. For replacement of an existing service, do not strengthen the old accepted inputs or weaken its externally required guarantees. For an abstract model, prove or test the `α` bridge; a matching field name is not such a bridge.

The existing Lean implementation in `tools/formal/RecursiveLegoRefinement.lean` already defines `IOContract`, `Implements`, `Refines`, and proves `refinement_preserves_implementation` and `narrowed_assumptions_cannot_substitute`. **REUSE these definitions** for same-type bounded claims rather than declaring another axiomatized Ordivon logic. That Lean model is deliberately restricted to equal input/output types; port adapters and real external effects remain independent obligations.

### Real proof-discharge table (required only for the property being claimed)

| Claim | Necessary independent witness | Practical native tool | Prohibited inference |
| --- | --- | --- | --- |
| A/G compatibility | Producer G entails consumer A, including typed port/effect/timeout assumptions | Pacti or existing Lean contracts | Identical schema ⇒ compatible behavior |
| Safety `□Inv` | Valid model, nonvacuous base state, all modeled transitions, and counterexample check | TLC, Lean, Z3/Kani/Verus where applicable | Finite model PASS ⇒ universal production safety |
| Progress under fairness | Explicit environment/fairness/budget, reachable transition and actual recovery path | TLA+/TLC and owner state-machine tests | Available action ⇒ eventual external service success |
| Code refinement | Directly exercises current Rust/TS/Python implementation through its public seam, with model/source readset | Native owner tests/property tests/real effect reconciliation | Formal theorem name/AST resemblance ⇒ implementation theorem |
| Release currentness | Exact Git revision, installed executable/manifest digest and time-bound readback | Existing Runtime/Workstation/CI/owner operations | PR merge ⇒ current service installed |
| Domain value | Named consumer tests actual externally observable result | Domain acceptance/readback | `candidate_completed` or `status=PASS` ⇒ user goal achieved |

When no checker or exact model-to-code bridge is available, keep the stronger standing `UNKNOWN`; still execute ordinary demonstrably useful changes under the Owner's actual native acceptance process. Do **not** convert an unproved universal claim into an automatic block on unrelated work.

## 13. One independently reproduced cross-Agent counterexample (2026-11-09)

**Real consumer:** Artifact's profile-required evidence qualification (current peer PR #1974). The typed responsibility is an Artifact Owner evaluator, *not* an independent global LEGO or Harness completion oracle.

**SourceCut:** peer PR head `be4f579990a135e0973bb60a7108ea4dba4b71f4`, `capabilities/artifact/artifact_verification/claim_coverage.py:assess_required_evidence`. This source is **not** merged/main proof. **Runtime reproduction:** `job-01a1c0ed-0fb7-744d-ab7f-ecc0d92a9ff6`, actual Python import from exact Git blob, exit 0. **Space collaboration:** `space:ordivon-capability-task-forum-r1:20261101`, topic `03-refinement`, message sequence 25763. The Agent owning Artifact PR has been asked to validate and implement, rather than writing into their branch.

**Failing public-seam example:** the Profile requires two independent claims, `decoderMatrix` and `deliveryReadback`. `native_result` contains both `claimResults` statuses PASS, but both entries use `nativePointers=['/verification']` to point to a *single unrelated aggregate* `{'status':'PASS'}`. The tested evaluator returns `{'status':'COMPLETE','complete':True,'issues':[]}` despite the absence of claim-specific native evidence. Changing the aggregate status to FAIL yields `complete=False`. The matcher checks same status, not semantic identity between **this required claim** and **the native observation used to discharge it**.

**Formal obligation:** let `Required(p,k)` denote that Profile `p` requires claim key `k`. Every complete decision needs a witness `w_k` with both source identity and claim relation:

`Complete(p,o) ⇒ ∀k. Required(p,k) ⇒ ∃w. NativeFor(w,o,k) ∧ VerifiedPass(w,o,k) ∧ Current(w,o)`.

Simply `w.status=PASS` is insufficient. This negative example does not establish that the installed production result was corrupted; source input trust and actual caller qualification remain separate. **Fix in the existing Artifact Owner:** reject generic aggregate pointer reuse when it does not identify the required claim; retain exact legitimate claim-specific evidence PASS. Add one failing case plus one positive case at the current public seam; run Artifact's native verification. No third evaluator, new workflow, or fabricated domain PASS.

This example concretely connects T11.2 (unfulfilled assumptions), T11.4 (UNKNOWN evidence), T11.10 (claim-bound witnesses) and the Superpowers/Matt *public seam RED→GREEN* methodology. It demonstrates why the theory is useful without running any weak-model evaluation.

## 14. Executable dependency frontier and cross-Agent responsibilities

The existing T0–T5 are a **task DAG**, not sequential theater. Treat dependencies as formal preconditions `BlockedBy(task)`; any independent consumer with satisfied predecessors may proceed. Do not create a separate planner or one ticket for each theory lens.

| Frontier | Current verified evidence / overlap | Next executable contract obligation | Integrates via |
| --- | --- | --- | --- |
| T0 — intake | PR #1973 merged on 2026-11-09 (source/Skill method adoption) | Preserve one `method-router` and optional scoped reference; reconcile duplicate current PR #1977 rather than merge a second router blindly | Skills Owner native search/resolve/read |
| T1 — source truth | PR #1962 merged; historic Authority counterexample #1942 blocked | Keep real historic-vs-current navigation distinction; any legitimate correction path must have its own provenance witness | Authority native verify, existing CI gate |
| T2 — model/candidate | Harness already uses `candidate_completed`; other Agent owns current Harness #1979, formal Run work #1835 | First produce a real caller that incorrectly promotes candidate or Job to DomainAccepted; otherwise DELETE a proposed duplicate completion enum | Harness and actual caller public APIs |
| T3 — state/effects | Runtime #1983 and Host #1976 open as of this SourceCut; existing PG Job/Work continuity | Independently review one actual recovery/replay consumer; distinguish `lost`, canceled, side effect committed and receipt certainty | Runtime/Host native PG + readback |
| T4 — real domain | Artifact #1974 open, Media/Game/Capital own their separate contracts; Artifact counterexample above is independently reproduced | Artifact Agent fixes claim-specific evidence binding; this contributor supplies falsifying inputs and reviews result only | Artifact owner test and consumer acceptance |
| T5 — subtract | Specs, old plans, duplicate validators and experimental code exist across Owners | Retire only proven superseded responsibilities and zero-live-consumer ephemeral work with current evidence; keep historical proofs/negative examples | Git, natural Owner retirement, formal/native readback |

### Concrete execution steps per frontier (Matt → ECC → Superpowers adaptation)

1. **Spec the actual negative:** from the existing Work/issue/SourceCut, state one consumer-visible failure, pre/post, errors, assumption and evidence target; if the consumer is already satisfied, retire the proposed custom change.
2. **Select a deep seam:** identify the highest stable public Owner interface. Do not split work by technical layers; a ticket includes everything required to witness one behavior end-to-end.
3. **Negative before change:** run the observed bad input against the old source (RED). Ensure the oracle is independently derived from consumer semantics, not the candidate code's own status bits.
4. **REUSE first:** select mature upstream contract/model checker or existing Owner-native primitive; avoid a new schema/runtime/agent. Use full eleven-coordinate profile only when an independently admitted responsibility truly needs it.
5. **Green and narrow:** implement at the natural Owner, cover the original counterexample and one positive valid operation; use existing unit/PG/stateful tests and optional formal checker when it materially strengthens this claim.
6. **Independent review:** review spec compliance *and* code/standards against exact base; compare actual effect/readback, run native `mise` and retain negative result as a regression.
7. **Integrate and consume:** send exact PR/commit/Job or readback to the corresponding Space Topic, deduplicate overlapping PRs, use GitHub Merge Queue; separate MERGED from installed, executed and DomainAccepted.
8. **Subtract:** remove the superseded workaround, duplicate instructions, old experiment files or self-referential tests only once the real replacement consumer is current. Preserve unique historical/falsification records.

### Stop conditions

- **Positive:** an Owner's actual consumer can demonstrate the originally missing behavior with current, independently observed evidence; old bad input is rejected and valid input still succeeds.
- **Legitimate no-change:** the incumbent already fulfills the consumer contract; record SOURCE+test and avoid creating a second implementation.
- **Scoped blocker:** named missing source, authority, installed owner, dynamic edge or external observation; UNKNOWN remains explicitly bounded, not converted to an indefinite generic request for more planning.

The leadership goal is not a count of mathematics terms, Specs, proof artifacts, agents or PRs. It is a system in which independent errors are detectable by the correct native owner while qualified work continues to deliver value.
