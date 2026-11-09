# Agent Delivery Contract R1 — execution-oriented reform specification

Date: 2026-11-09
Status: implementation specification; Wave 0 is the first bounded deliverable, not domain completion.
Baseline: ordivon-org/ordivon main 3b43977e682d8c7668f6371ffd998c7821e4312a.

## 1. Problem and goal

The recurring failure is not a missing paragraph in AGENTS.md. An agent can reinterpret the requested goal, replace a consumer outcome with a convenient intermediate artifact, independently choose a weaker verifier, or overprotect a local component until work stops. Component-local PASS must not be promoted into user/domain success.

**Goal:** make consequential engineering changes follow a stable, consumer-owned objective and verifiable component contracts while allowing the implementer to choose efficient, mature means of execution. Missing evidence remains UNKNOWN; it must not be called SUCCESS or be treated as universal permission to abandon a feasible task.

A successful reform makes the current normal Owner tools sufficient for a complete path from objective -> source/implementation -> verifier -> target consumer. It must not create a universal task authority or an independent orchestration runtime.

## 2. Source anchors and upstream adoption

Existing native interfaces to reuse:
- Root AGENTS.md: scope, consumer-first decisions, R2.1, typed UNKNOWN and delivery reporting.
- tools/repo/owners.toml and affected_owners.py: mechanical Owner discovery and affected test selection.
- packages/composition/src/ordivon_composition/cognitive_circuit_r1.py: exact objectiveRef and manifestDigest, verifier-owned gate binding, mechanicalClosure distinct from domain acceptance.
- packages/composition/src/ordivon_composition/verification_obligation_r1.py: task-local gate -> obligation projection and exact verifier binding.
- packages/composition/src/ordivon_composition/successor_contract_r1.py: immutable predecessor/candidate and evaluator anchor.
- packages/composition/formal/Lego21OwnerBoundary.tla: bounded Host/Runtime/consumer/source-cut acceptance model.
- services/harness: cognition and tool continuity, not domain acceptance.
- services/runtime: Jobs/Attempts/receipt, not domain acceptance.
- services/host: Work, Space, Topic, Message and collaboration continuity, not physical execution.
- capabilities/media: production-owned Claim, source, selected bytes, QC and consumer review.

Upstream references (retrieved 2026-11-09; procedure references only, no foreign hooks or code executed):
- Matt Pocock Skills 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d:
  https://github.com/mattpocock/skills
  - engineering/to-spec, to-tickets, implement, tdd, code-review, retro
  - carry forward: spec from existing conversation, test at existing seams, vertical independently verifiable tickets, blocking edges, spec + standards review.
- ECC d2ef2680594f9a17526a6e1a2e18b3d242c5d17b:
  https://github.com/affaan-m/ECC
  - verification-loop, iterative-retrieval and scoped hooks
  - carry forward: progressive retrieval, native build/test/checkpoint verification and an explicit diff review.
  - reject: repository-wide agent/hook/installer installation or generic npm commands as mandatory verification.
- Superpowers 22f0b463e7a5e579904dd6211a520321035526f7:
  https://github.com/obra/superpowers
  - writing-plans, using-git-worktrees, test-driven-development, verification-before-completion, executing-plans
  - carry forward: isolated source, an executable file/command plan, red-green-refactor where a code seam changes, observed command output, and bounded review.
  - adapt: use Ordivon Runtime Workspaces and native CI instead of replacing their orchestration.

Use Ordivon's skill-supply-chain-audit before any future actual installation of foreign packages. This spec adopts *procedures*, not external software or instruction authority.

## 3. System contract (formal-first, consumer-owned)

For a consequential task define a task-local objective anchor:

    G = (consumer, owner, goalId, objectiveDigest, sourceCut, successPredicate, scope)

The consumer/owner authorizes G. An implementation Agent may generate candidates, but may not silently weaken G or redefine the verifier. A legitimate goal revision creates a newly identified anchor approved at the original objective boundary, rather than mutating prior evidence.

For any proposed candidate C with implementation observations E:

    Accepted(C,G,E) implies
      ExactGoalBinding(C,G)
      AND RelevantOwnerVerification(C,G,E)
      AND ConsumerAcceptance(G,E)

This is a *desired refinement obligation*, not an assertion that the current runtime proves it in full. Existing Composition only establishes mechanical gate satisfaction; it explicitly reports domainAcceptanceEstablished=false.

Bounded temporal properties:
- Safety S1: a stale or different objective digest cannot be used to re-accept old gate evidence.
- Safety S2: gate success, CI PASS, Git merge or Runtime exit does not establish domain completion.
- Safety S3: work on other owners' state and effects uses their native boundaries; Skill activation never grants authority.
- Safety S4: UNKNOWN is not SATISFIED, not UNSATISFIED, and not an invented zero.
- Safety S5: a replacement preserves required pre/post/inv/effect/provenance guarantees without strengthening consumer assumptions.
- Progress P1 (conditional): when a feasible owner-authorized action exists and the environment is cooperative, execution must advance or provide a grounded blocking witness; aim for recovery and replacement of unproductive methods. Do not claim unconditional liveness or encode arbitrary quotas.
- Progress P2: valid ordinary deletion, no-op and mature-provider substitution remain legitimate; no mandatory multi-stage review for trivial changes.

Where a LEGO is formally DECLARED or ADMITTED, use the full typed R2.1:
    ell = (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)
The method reference added in Wave 0 is advisory method routing, not a newly declared independent LEGO, execution authority or separate registry. An actual declared composition binds the existing eleven-coordinate effective contract and its provenance at the natural source owner.

## 4. User stories and externally observed acceptance

1. As a task requester, I can state the desired domain result without specifying how every Owner works internally.
2. As an implementing Agent, I can inspect only relevant methods, native tools and effective contracts, not a cloned all-purpose framework.
3. As a consumer, I can reject a candidate that claims local tests are equivalent to my target result.
4. As a verifier Owner, I control my gate semantics and provenance independently of the candidate implementation.
5. As a maintainer, I can replace a provider without rewriting the goal or tests that define its required guarantees.
6. As a repository maintainer, I can trace from a spec ticket to the touched files, Owner tests, Git range and actual consumer consequence.
7. As an operator, I can distinguish source committed, branch integrated, installed, executed and consumed states.
8. As an Agent, I can select deletion or a mature native replacement without waiting for speculative global governance.
9. As an observer, I can see precise UNKNOWN or observed blockers rather than repeated free-text analysis.
10. As a production Owner, I can apply this method only when it changes the decision; routine work remains routine.

## 5. Architecture decision: owner-native, no universal governance

Natural ownership:
- Host: Work/ticket collaboration and navigation, not domain success.
- Harness: agent/tool turn execution, continuation and context, not a second planning authority.
- Runtime: durable physical execution/effect receipts, not semantic completion.
- Composition: task-local contracts and gate/verification obligations, not a workflow controller.
- Domain Owner: accepts its actual outcome, using its real consumer and evidence.
- Repo: Git SourceCut, affected-Owner verification and integration.
- Skill: progressive-disclosure method instructions only.

Reject any proposed new Task Kernel, global goal ledger, evaluator registry, policy gate, scheduler, report generator or eleven-field database unless a *real consumer* demonstrates that current owner-native mechanisms cannot express the needed contract.

## 6. Execution waves and dependency graph

These tickets are individually bounded vertical slices. Each ticket is complete only with its named evidence, not merely an edited document. Changes affecting an Owner run that Owner's native tests; optional methods never override higher-priority instructions.

### W0 — Adopt upstream engineering method at the existing entry seam
Blocked by: none.
Owned by: repository method/Agent instruction surface.
Files: this spec; .agents/skills/method-router/SKILL.md; .agents/skills/method-router/references/engineering-delivery.md; AGENTS.md if a short pointer is necessary.
Actions:
1. Freeze Ordivon and three upstream revisions and map procedures to native Owners.
2. Implement a scoped engineering-delivery route for *consequential* code changes only.
3. Link from existing Agent guidance without duplicating a mandatory lifecycle.
4. Verify Markdown links to local paths, Git diff whitespace and root repo checks.
Acceptance: an Agent can identify one real consumer, follow the existing native test seam and obtain a concise spec/verification route without installing an upstream framework.
Not claimed: runtime enforcement or full domain acceptance.

### W1 — Objective anchor/old evidence cannot be reused after a goal change
Blocked by: W0.
Owned by: Composition.
Files: packages/composition/tests/test_cognitive_circuit_r1.py, existing cognitive_circuit_r1.py and schema only if a real regression test exposes a gap.
Actions:
1. Write a regression test: create a valid objective and gate result, mutate objectiveRef digest, require CircuitContractError on reuse.
2. Require the existing compiler result to retain objectiveRef and the projection to keep domainAcceptanceEstablished=false.
3. If RED, correct the smallest existing interface; if GREEN, do not rewrite production code.
Acceptance: focused Composition tests pass and old goal-bound evidence cannot be reaccepted after objective mutation.
Not claimed: that a text-only goal digest makes an externally false goal true.

### W2 — Target consumer binding in one Media Production
Blocked by: W1.
Owned by: Media, Runtime and Artifact each for their own interface.
Candidate: capabilities/media/productions/runtime-introduction/.
Actions:
1. Read current Production Claim, Asset/Blob, source/revision and output acceptance.
2. Select exactly one missing consumer seam, if any; attach existing Studio processing / Artifact / Runtime evidence to the Production's native acceptance, not a new global receipt.
3. Reject a false pass when only a file exists, an old SourceCut is presented, or local QC is substituted for semantic review.
4. Use the installed native provider and its actual read-back; remove redundant adapters where no consumer remains.
Acceptance: selected Production's existing native interface distinguishes exact media bytes/claim, technical QC, actual consumer review and UNKNOWN; changed Owner-native tests pass.
Not claimed: creating a new video or evaluating low-capability model performance.

### W3 — Agent delivery continuity and grounded blockers
Blocked by: W1; W2 only if a real Media-to-Harness seam is affected.
Owned by: Harness and Host, each at its natural boundary.
Actions:
1. Determine whether real Work/Run consumers already preserve one next executable action or exact blocking witness.
2. Reuse existing Host Work, Harness turns and Runtime Job observations.
3. Only if an evidenced consumer is missing, change the smallest existing API so absent domain acceptance cannot become a completed *domain* verdict.
4. Preserve legitimate no-op, stop and explicit source-independent blocking; no artificial progress score, runtime watchdog or manual gate.
Acceptance: demonstrable existing consumer failure is corrected by a focused Owner test and a native read-back.
Not claimed: global guaranteed liveness across failed external systems.

### W4 — Formal refinement where proofs have actual consumers
Blocked by: W1; W2/W3 as they affect the chosen seam.
Owned by: Composition / selected domain Owner.
Actions:
1. Reuse Lego21OwnerBoundary.tla and existing gate/source bindings.
2. For a real uncovered property, write a bounded TLA+/Lean/SMT assertion and a counterexample control; do not create a parallel calculus.
3. Bind model assumption -> source implementation -> consumer test; explicitly retain UNKNOWN where a refinement proof is absent.
4. Make a proof test part of an existing Owner verification task only if it protects a current consumer.
Acceptance: a named bounded property and its falsifier are checked by the pinned native verifier; tested implementation refinement is reported separately.

### W5 — Native verification / review / CI integration
Blocked by: W2/W3/W4 for changed seams.
Owned by: each changed Owner and repo integration.
Actions:
1. Select affected Owners using tools/repo/affected_owners.py.
2. Execute focused red-green code tests at changed seams, native Owner verification, exact Git diff review and baseline comparison.
3. Compare acceptance against the spec AND standards, with objective/consumer evidence independent of candidate-generated self-assessment.
4. Keep task graph in the existing issue tracker/Host Work only if actually used; do not create another status database.
Acceptance: executed commands, exit statuses and concrete consumer evidence are preserved; SKIP/NOT_RUN/UNKNOWN are not PASS.

### W6 — Replace and retire redundant mechanisms
Blocked by: the relevant W2/W3/W5 consuming slice.
Owned by: natural Owner.
Actions:
1. Trace actual active consumers, including installed use, not just filename references.
2. Prefer DELETE -> REUSE -> COMPOSE; remove source with no current consumer and no unique recoverable evidence.
3. Use native Git/worktree/Owner cleanup and rollback; avoid a custom garbage collector or catalog.
Acceptance: resulting consumer tests pass, retired source no longer appears on active paths, and versioned Git provenance remains available.

### W7 — Integrate / report actual standing
Blocked by: every modified Owner's implemented slices.
Owned by: existing Git integration + consumers.
Actions:
1. Compare branch against then-current main, handle concurrent Owner changes without force or reset of shared work.
2. Run affected validation and create a conventional PR with exact evidence.
3. Distinguish BRANCH, MERGED, INSTALLED, EXECUTED and CONSUMED; do not claim deployment or consumer acceptance on PR submission.
Acceptance: visible Git source identity, test results and exact remaining work, plus deployment/consumer readback only when actually performed.

Dependency summary:
    W0 -> W1 -> W2 -> W5 -> W6 -> W7
              \-> W3 -> W5
              \-> W4 -> W5
W6 is selected only when a real redundant responsibility is found. Independent W2/W3 work may proceed concurrently after W1 when source seams do not overlap.

## 7. Verification decisions and negative controls

Use contract-native tests, not weak-model benchmarks or prompt imitation experiments.

- Objective changed -> stale gate result rejected by existing Composition.
- Correct gate but wrong consumer/SourceCut -> mechanical evidence cannot be promoted to domain outcome.
- Valid authorized effect -> unaffected by speculative extra approval steps.
- No evidence -> UNKNOWN, not PASS or FAIL.
- Git merge only -> no invented installed or consumed state.
- Replaced provider -> same consumer postcondition and new exact source/provider evidence.
- Existing native solution -> no duplicate provider, schema or owner created.
- Low-risk legitimate deletion -> current native deletion path remains available.

Record an observed before/after for changed implementation behavior. A green pre-existing test is a protected invariant, not evidence of a newly created feature.

## 8. Out of scope

- Weak-model or cross-model A/B experiments.
- Installing the entire Matt/ECC/Superpowers stack or copying unreviewed hooks.
- Universal Task/Workflow/Goal service, new registry or general-purpose Agent scheduler.
- Self-modifying policies, automatic external effect authorization, live trading.
- Declaring a model-checked abstraction equivalent to a Rust/Python/TypeScript implementation without a refinement witness.
- Rewriting all domain Owners or moving source only for architectural symmetry.

## 9. Stop / escalation / success criteria

A wave stops when its named consumer/property is checked and there is no unresolved, decision-changing defect within scope. Continue the next unblocked wave unless it depends on unavailable inputs or would harm current consumers. When blocked, record a concrete dependency and an executable recovery option in the existing Work/PR, not a new framework.

This spec deliberately separates plan, branch implementation, merged source, installed system and observed domain result. Do not label later waves complete because W0/W1 are complete.
