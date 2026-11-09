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

## 11. Theory-to-owner proof obligations and execution dependencies (2026-11-09)

This section sharpens *the existing T0–T5 plan*, not another planning service or a fifth architecture Spec. The full mathematical method selection belongs to the current scoped [formal-thinking reference](../../.agents/skills/recursive-lego-calculus/references/formal-thinking-legos-human-agent.md). A method profile is a candidate thinking LEGO until its actual natural-Owner consumer and complete R2.1 eleven-coordinate contract are admitted. No per-file LEGO declaration.

### Theory selection and legitimate transfer to execution

| Proven theory/practice | Exact use and limit | Existing Ordivon consumer and native test |
| --- | --- | --- |
| Hoare logic and weakest preconditions (Hoare 1969) | A triple {P} C {Q} establishes *partial correctness* of C under P, not termination or truth of P in production. For a destructive action, calculate which previous state makes Q valid rather than treating deletion count as success. | Runtime workspace.close preconditions, Host PG Work CAS, Owner negative tests. |
| Assume–guarantee contracts / Pacti (Nuzzo et al. 2014, Incer et al. 2025) | For an existing consumer contract (A,G) and a replacement (A',G'), require A ⇒ A' and A ∧ G' ⇒ G on the old consumer scope; this is a **necessary simplified behavioral criterion**, alongside actual compatible wiring, effect, identity and state obligations. Not every interface-to-contract translation preserves sequential composition. | Existing compositional-contracts Skill, narrow Gateway→Runtime/Harness provider seams. Use Pacti only for a supported assumption/guarantee class that changes a real choice. |
| Transition systems, temporal logic, fairness (Lamport, AWS TLA+ practice) | Check invariant Init ∧ Next ⇒ □Inv within actual model and explicitly qualified finite scope; liveness is conditional on enabledness, capacity, fair execution and no irreversible unknown effect. | Runtime Job/Attempt/Workspace lifecycle, Tool reentry/replay; existing native TLA+/TLC and state tests, not a new scheduler. |
| Refinement mappings (Abadi & Lamport 1988/1991) | Establish a mapping α from concrete Owner transitions to the relevant abstract obligation; stuttering, environmental steps, concurrency and proof readsets must be modeled. Trace(model) alone is not Trace(production). | One existing Rust/Python Owner state machine plus negative source/refinement and live effect readback. |
| Abstract interpretation, CEGAR (Cousot 1977; Clarke et al.) | Build the smallest adequate *sound for the claimed property* abstraction. Abstract counterexamples may be spurious; check concrete feasibility and refine only relevant false alarms. Preserve UNKNOWN where the abstraction drops necessary environment. | Existing recursive-lego-calculus, owner tests and counterexample replay; do not claim universally minimum representation. |
| Separation logic / incremental summaries (Meta Infer) | Recheck affected dependent assertions/readsets rather than whole-system proofs on every edit; the frame principle applies only when disjointness/footprints are justified. | tools/repo/affected_owners.py, source dependency contracts, scoped formal invalidation. |
| Linearizability (Herlihy & Wing 1990) | For actual concurrent shared objects, establish a valid sequential history respecting real-time order, not mere test pass. This is an optional target only where a current CAS/replay race matters. | Host Work transaction, Runtime admission/request identity, native PG concurrency tests. |
| Proof-producing/integrity evidence (in-toto / SLSA provenance) | Bind exact subject bytes, source commit, toolchain and producer to verifiable receipts. Such provenance proves stated build steps, not a domain outcome. | Git SHA, GitHub protected checks, Artifact native digest/consumer, installed systemd binary/source identity. |
| Verification-guided development (AWS Cedar) | Formal model proof + differential property-based tests against actual code + remaining unmodeled-path tests; never promote simulated oracle agreement to physical deployment. | Existing Lean/TLC/Kani/CrossHair/Hypothesis/pytest only at the natural Owner seam, with negative controls and exact versions. |

### Mathematical contract and observation algebra

Let a real consumer c own a predicate phi_c at source/version/environment cut sigma, with authorized effect e and current witness w. Its acceptance is conditional:

    Accept(c,g,sigma)  iff  Verify_c(phi_c(g), w, sigma) = PASS

The executor cannot create a valid acceptance statement merely by returning a proposal. Keep evidence standing local to *each claim* rather than adding a global enum: NOT_OBSERVED, SUPPORTED, REFUTED, CONFLICT, UNKNOWN_CURRENTNESS. A conflicting or stale witness is not FALSE or PASS. A valid independent action may proceed while an unrelated claim is UNKNOWN.

For an admitted effect with source action a:

    EffectCommitted(a) => OwnerAdmitted(a, sourceCut, principal, grant, nativePreconditions)
    CompletionClaim(g) => ConsumerWitness(g, currentCut, requiredEffects)

The first obligation is local *authorization/effect admission*; it does not assert actual external exactly-once side effects. The second is local *semantic evidence acceptance*, not a Job outcome. If an action's external effect is UNKNOWN after timeout, reconcile its exact identity instead of retrying blindly. No claim that all natural-language goals are mechanically decidable.

For conditional progress under fair scheduler F and bounded resources B:

    Ready(a) and NativeAllowed(a) and F and B
       leadsto NativeEffectObserved(a) or VerifiedBlocker(a)

Only a current Owner reason may establish VerifiedBlocker. Planning text, a hypothetical permission concern, and an unavailable unrelated verifier cannot globally block other admitted work. Never call the condition an unconditional temporal theorem without actual fairness/environment assumptions.

**Non-vacuity / no fake safety:** exhibit a reachable Ready-and-NativeAllowed state followed by a genuine permitted Owner effect, as well as a separately rejected illegal effect. If a model simply makes Ready unreachable or refuses every operation, a trivially true safety or progress implication is **not** qualified acceptance. Check reachability with the natural Owner tool and bind that path to one real consumer.

### Exact execution dependency graph (source-cut-qualified)

These are vertical increments of T0–T5, *not* a parallel ticket tracker. The root Spec only records the cross-Owner target; each actual test/code/PR belongs to its natural Owner.

| ID | Blocking edges | Concrete action and reuse | Independent stop/readback |
| --- | --- | --- | --- |
| E0 / T0 | none | Adopt this theory/reference mapping in existing method-router and existing R2.1 reference; leave upstream Skills as pinned research guidance. | Exact source, link/Skill checks, no second registry or copied upstream source. |
| E1 / T3 Runtime | E0 for method only | Continue existing GitHub #1921 bounded PG workspace.list; compare failing repo-mechanics assertion and Composition 504 against current main, merge owner branch, rerun existing checks. **Do not write a new list backend.** | Healthy page through real Runtime; poison nonselected workspace does not globally fail; protected PR check/merge and installed readback separated. |
| E2 / T1 | independent | Audit actual Authority/Host historical-revision consumer; only if still faulty, RED/GREEN at PG public seam; keep legitimate compaction distinguishable from silent missing revisions. | Real database negative and positive results, no fabricated history. |
| E3 / T2 | independent after E0 | Find one current caller that incorrectly promotes Harness candidate to domain completion. Fix **only if** there is a failing native consumer case. | candidate success and absent consumer witness cannot accept; correct current witness can. |
| E4 / T4 | dependent on a concrete E1/E2/E3 Owner | Prove/check the one relevant transition/Hoare/A–G property; keep exact code refinement, permitted effects and physical receipt bound to the same source. | Abstract PASS, code PASS, installed PASS and domain acceptance reported separately. |
| E5 / T5 | after affected replacement is accepted | Delete superseded helper/spec/plans with no remaining unique consumer; preserve independent falsification evidence and current native Worker/Job receipts. | Git tree and live final consumer readback; simpler current path and no stale authoritative copies. |

Execution protocol per ready vertical slice: Matt to-spec/consumer and to-tickets blocking edges → ECC search-first and contract-first only for a genuine provider boundary → Superpowers smallest RED/GREEN commit using the Owner's tests → ECC change-impact actual readset and native regression → Superpowers verification-before-completion with real PR/installed/consumer readback. The method cannot turn a legal direct native operation into a mandatory approval queue. Do not run weak-model trials, model ranking, blanket testing rituals, or all formal tools merely because they are available.

### Failure classification and proof invalidation

A verification failure must retain its actual class and exact readset:
- **SPEC_COUNTEREXAMPLE:** a reachable violating abstract state; check feasibility against the code.
- **CODE_REGRESSION:** native test reproduces the concrete defect.
- **EXTERNAL_DEPENDENCY_UNAVAILABLE:** a pinned official tool/artifact is unavailable; proof status NOT_RUN, not FAIL against the owner algorithm and not PASS.
- **SOURCE_DRIFT:** assumptions, Git SHA, dependency or verifier version changed; previously valid evidence must be requalified.
- **INSTALLATION_MISMATCH:** source merged but installed binary/config differs.
- **CONSUMER_UNACCEPTED:** real output misses the agreed predicate despite passing local checks.

2026-11-09 observed example: GitHub #1921 has one stale GitHub-governance expectation in repo-mechanics and an HTTP 504 fetching the Composition formal tool in owner-shard-2. Both require native CI reruns / main reconciliation, not a speculative Rust rewrite. Earlier #1925 and #1980 were verified as MERGED; recheck before future claims. No assertion in this dated note establishes their actual installed state.

### Primary research and mature tool links

- C. A. R. Hoare, *An Axiomatic Basis for Computer Programming* (1969): https://doi.org/10.1145/363235.363259
- Nuzzo et al., *From Relational Interfaces to Assume–Guarantee Contracts* (2014): https://www2.eecs.berkeley.edu/Pubs/TechRpts/2014/EECS-2014-21.html
- Pacti, algebra and compatible contract fragment: https://www.pacti.org/docs/getting_started/
- Abadi & Lamport, *The Existence of Refinement Mappings*: https://www.microsoft.com/en-us/research/publication/the-existence-of-refinement-mappings/
- Cousot & Cousot, *Abstract Interpretation* (1977): https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml
- Clarke et al., *Counterexample-guided Abstraction Refinement*: https://web.stanford.edu/class/cs357/cegar.pdf
- Herlihy & Wing, *Linearizability* (1990): https://www.cs.cmu.edu/~wing/publications/HerlihyWing90.pdf
- AWS, *How AWS Uses Formal Methods*: https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods
- AWS, *Cedar verification-guided approach*: https://www.amazon.science/publications/how-we-built-cedar-a-verification-guided-approach
- Meta Infer, incremental pre/post summaries: https://engineering.fb.com/2017/09/06/android/finding-inter-procedural-bugs-at-scale-with-infer-static-analyzer/
- Hypothesis rule-based state machines: https://hypothesis.readthedocs.io/en/latest/stateful.html
- Kani Rust bounded verifier: https://model-checking.github.io/kani/
- Verus Rust verifier: https://verus-lang.github.io/verus/guide/
- in-toto attestation and SLSA provenance: https://in-toto.io/docs/specs/ ; https://slsa.dev/spec/v1.0/provenance
