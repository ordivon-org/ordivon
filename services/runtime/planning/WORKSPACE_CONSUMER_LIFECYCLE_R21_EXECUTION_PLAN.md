# Workspace Consumer Lifecycle R2.1 — Implementation Plan

> **For agentic workers:** Use the installed obra-superpowers/writing-plans, obra-superpowers/test-driven-development, obra-superpowers/verification-before-completion and matt-native/domain-modeling; ECC-native/contract-first governs cross-Owner API changes. Execute tasks on their actual native owner. No weak-model evaluations.
>
> Goal: 让 Workspace 生命周期由可证明的消费者事实、成果处置及公平回收控制，而非 Agent 性格、目录年龄或 dirty 标志决定。
>
> Architecture: 在既有 Runtime Core + PG Job + Git + Artifact/Host + systemd 原生工具链上增加最小可观察消费者/处置合同；TLA+/TLC 检查安全与活性，Rust/PG/native tests 证明代码精化和物理消费者。复用并最终删除重叠的 cleanup 路径。
>
> Tech Stack: Rust 1.99+, Python 3.15+, PostgreSQL, TLA+/TLC, Git, systemd, native Windows Runtime, mise; no new registry, language or third-party framework.
>
> Spec: services/runtime/planning/WORKSPACE_CONSUMER_LIFECYCLE_R21_SPEC.md.
>
> Current source cut: 3b43977e682d8c7668f6371ffd998c7821e4312a, 2026-11-09. Always compare latest origin/main before modifying; already merged #1960 4h hold is not a pending task.

## Global constraints

- R2.1 eleven-coordinate LEGO only; existing .agents/skills/recursive-lego-calculus is the semantic authority.
- Do not invent domain outcome from Job exit, Git dirty state or absence of CWD process; UNKNOWN != FALSE.
- Safety AND liveness: not delete valid consumers, not retain released garbage indefinitely under stated scheduler/environment assumptions.
- Owner boundaries: Runtime physical state; Host semantic Work; Git source; Artifact results. Source, model, merged, installed and consumed independent.
- RED → GREEN → refactor for implementation seams; real verified command outputs required before completion claims.
- No independent orchestrator, GC service, universal LEGO registry, custom test DSL, weak-model tests or second approval chain.
- Do not unilaterally remove evidence while another Agent is working; use isolated source-based worktree and existing GitHub PR/merge-queue.

## Source map and interfaces

- services/runtime/crates/ordivon-runtime-core/src/universal/types.rs: WorkspaceCloseRequest with consumer_released, force, expected_source_state_digest.
- services/runtime/crates/ordivon-runtime-core/src/universal/workspace/close_recovery.rs: physical close and extension guard; source behavior.
- services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/workspace.rs: PG workspace.close invocation, lifecycle transaction boundary.
- services/runtime/crates/ordivon-runtime-mcp/src/server/tools.rs and pg_server.rs: public MCP closure surfaces.
- services/runtime/crates/ordivon-runtime-core/src/universal/tests.rs: close errors, protected jobs, idempotence and source-state tests.
- services/runtime/formal/WorkspaceConsumerCloseR1.tla plus .cfg: bounded formal contract; source abstraction only.
- services/runtime/scripts/tla-formal and services/runtime/formal/README.md: upstream-pinned TLA+ runner and deliberate negative controls.
- services/runtime/scripts/ordivon-runtime-lifecycle and scripts/tests/test_lifecycle.py: current repo operator lifecycle.
- installed /usr/local/libexec/ordivon/ordivon-runtime-pg-reclaim: production PG cleanup; do not assume version equality with repo.
- services/runtime/docs/guides/runtime-legos.md: one consumer-facing navigation point.
- services/runtime/packaging/systemd/ordivon-workspace-retention.json: source policy; runtime.describe / systemctl / deployed receipt to establish installation.

## Task 1 — Formal liveness baseline (first executable vertical slice)

**Files:**
- Modify: services/runtime/formal/WorkspaceConsumerCloseR1.tla
- Create: services/runtime/formal/WorkspaceConsumerCloseR1.liveness.cfg
- Modify: services/runtime/scripts/tla-formal
- Modify: services/runtime/formal/README.md

**Interface:**
- Consumes: existing Init/Next/Close/Spec/vars and upstream-locked TLC.
- Produces: FairCloseSpec; EligibleForClose; StableEligibleEventuallyClosed; model-check command and a falsification test that removing fairness is detected.
- Not a claim that installed Runtime has consumer proof.

Steps:
- [x] 1.1 RED: create liveness CFG specifying FairCloseSpec and StableEligibleEventuallyClosed, then run TLC. It must fail because these model names do not yet exist.

    SPECIFICATION FairCloseSpec
    INVARIANT TypeOK
    INVARIANT FreshActiveConsumerCannotBeClosed
    INVARIANT ClosedHasNoLiveJob
    INVARIANT ClosedHasNoGitDependent
    INVARIANT ReleasedAssumesConsumerFinished
    PROPERTY StableEligibleEventuallyClosed
    CHECK_DEADLOCK FALSE

  Command from services/runtime: scripts/tla-formal verify; then java -cp PATH_FROM_formal/toolchain.lock.json tlc2.TLC -config WorkspaceConsumerCloseR1.liveness.cfg WorkspaceConsumerCloseR1.tla (working directory formal/). The RED outcome must be a named missing property, not an I/O/environment error.

- [x] 1.2 GREEN: add to existing model the following conditional property; fairness is explicit and does not purport to guarantee arbitrary consumer termination.

    EligibleForClose ==
        /\ phase = "open"
        /\ ~liveJob
        /\ ~gitDependent
        /\ (released \/ age = "expired")

    FairCloseSpec == Spec /\ WF_vars(Close)

    StableEligibleEventuallyClosed ==
        (<>[]EligibleForClose) => <> (phase = "closed")

  Run the same TLC command. Expect 0 invariant/property violations. This establishes conditional model liveness only.

- [x] 1.3 Mutation negative control: copy the model into temporary directory; replace exactly one occurrence of FairCloseSpec == Spec /\ WF_vars(Close) with FairCloseSpec == Spec; run TLC with the liveness CFG and verify a named temporal-property violation and an actual counterexample trace. Do not treat arbitrary nonzero return as falsification.
- [x] 1.4 Add this check to existing scripts/tla-formal check and falsify branches; reuse its existing verify_jar and workspace_close_expect_named_counterexample architecture. Update formal README with assumptions, liveness scope and counterexample. Run scripts/tla-formal check and scripts/tla-formal falsify, then mise run formal:verify.
- [x] 1.5 Commit only when actual commands returned PASS. If toolchain unavailable, store the exact blocker and do not claim model checked.

## Task 2 — Age-only false-completion counterexample

**Files:**
- Modify: services/runtime/formal/WorkspaceConsumerCloseR1.tla
- Modify: services/runtime/scripts/tla-formal
- Modify: services/runtime/formal/README.md

**Interface:**
- Produces: a named negative witness where an expired, still-active abstract Consumer can be closed in R1; does not falsely imply installed code has been proven unsafe.

Steps:
- [x] 2.1 Define ExpiredActiveConsumerCannotBeClosed == ~ (phase = "closed" /\ consumer = "active" /\ age = "expired"). Keep it out of the normal pass CFG while R1 still permits age-only close.
- [x] 2.2 In a temporary config, require the invariant and run TLC. Expect exit code 12, exact named violation, and a trace with Consumer active/age expired/phase closed.
- [x] 2.3 Add explicit open P0 obligation to the spec model-readset: either a checked bounded lease whose expiry removes live consumer claim, or independently witnessed consumer release. Do not invent synthetic consumer truth.
- [ ] 2.4 After Task 3/4 implementation, replace this expected counterexample with a normal positive invariant; require previous counterexample to be absent and use a separate mutation to prove detectability.

## Task 2B — R2 candidate formal profile + negative controls (same TLA model)

**Files:**
- Modify: services/runtime/formal/WorkspaceConsumerCloseR1.tla
- Create: services/runtime/formal/WorkspaceConsumerCloseR1.r2-candidate.cfg
- Modify: services/runtime/scripts/tla-formal
- Modify: services/runtime/formal/README.md

**Interfaces:**
- Consumes: existing Init/Next/Close/age/consumer/liveJob/gitDependent and TLC.
- Produces: R2CandidateClose, FairR2CandidateSpec, R2CandidateClosedConsumerFinished, StableR2CandidateEligibleEventuallyClosed.
- Explicit non-guarantee: no authenticated consumer witness, no Rust/PG code refinement.

- [x] 2B.1 RED: missing R2 candidate symbols in TLC CFG produced exit 151 and an exact missing-invariant error.
- [x] 2B.2 GREEN: stronger candidate Close requires abstract consumer="finished"; TLC bounded safety and WF-scoped liveness PASS (81 generated, 27 distinct).
- [x] 2B.3 Native falsifiers and non-vacuity: legal fresh-release Close must be reachable; remove consumer-finished guard -> TLC named invariant violation; remove fairness -> TLC temporal stuttering counterexample. Existing R1 age-only counterexample remains.
- [ ] 2B.4 On exact Git committed state, run mise run formal:verify, scripts/check_docs.py, git diff --check, native PR/CI and record source SHA; source refinement remains UNKNOWN.
- [ ] 2B.5 Task 3/4 real Runtime consumer evidence and outcomes must discharge candidate-to-source obligations before replacing the old R1 operational semantics.

## Task 3 — Honest consumer/disposition evidence in Runtime

**Files:**
- Modify: services/runtime/crates/ordivon-runtime-core/src/universal/types.rs
- Modify: services/runtime/crates/ordivon-runtime-core/src/universal/workspace/close_recovery.rs
- Modify: services/runtime/crates/ordivon-runtime-core/src/runtime/pg_runtime/workspace.rs
- Modify: services/runtime/crates/ordivon-runtime-core/src/universal/tests.rs
- Modify: services/runtime/crates/ordivon-runtime-mcp/src/server/tools.rs and server/tests/tool_catalog.rs only if wire shape actually changes.

**Interface:**
- Consumer result types: PUBLISHED(ref, exact source), DISCARDED(owner assertion, exact source), UNKNOWN(reason, scope); existing Job/Workspace sourceStateDigest are inputs, not replaced. Preserve legacy consumerReleased field during Expand→Migrate.
- Runtime response: CLOSE, RETAIN or RECONCILE with typed refusal/reason/currentness; never accept arbitrary unbound text as proof.

Steps:
- [ ] 3.1 First inspect the exact types in universal/types.rs and current PG close behavior. Use the smallest compatible change at this seam; do not create a new task store.
- [ ] 3.2 RED public-interface tests: active Job, unresolved exclusive source output, explicit discarded dirty output, force false, mismatched expectedSourceStateDigest, stale evidence epoch, already-closed replay. Assert response fields and physical path evidence.
- [ ] 3.3 GREEN: implement the smallest type/logic and durable PG compare-and-swap that makes these tests pass. A caller-provided boolean alone cannot be called verified, so leave any unproven external consumer as UNKNOWN.
- [ ] 3.4 Run cargo fmt --check, focused transactional-runtime tests and actual PG-native tests from services/runtime/mise.toml. Capture exact commands/receipts; do not claim installed behavior from tests.
- [ ] 3.5 Formal model: reflect only actual source-refined semantics; if model property currently exceeds source support, mark CODE_REFINEMENT=UNKNOWN, not proven.

### Live owner convergence note

As of 2026-11-09 PR #1983 (fix/runtime-pg-workspace-contract-20261109)
already implements the PG-native source-owned reclaim candidate and covers
13 native behavior tests. Do not duplicate its module or claim merged/deployed
until GitHub and installed release receipts prove it. Prioritize reviewing
the missing consumer/disposition witnesses and tests that can falsify its
actual native behavior, then route changes to the existing natural Owner.
Its repo-preflight failure is tied to an unauthenticated `mise` GitHub
PowerShell release lookup at CI time; do not misdiagnose this as a PG semantic
counterexample.

## Task 4 — Fix normal-task progress and provider-owned GC

**Files:**
- Modify: services/runtime/scripts/ordivon-runtime-lifecycle
- Test: services/runtime/scripts/tests/test_lifecycle.py
- Audit: installed /usr/local/libexec/ordivon/ordivon-runtime-pg-reclaim (read-only before qualification)
- Modify: services/runtime/packaging/systemd/ordivon-workspace-retention.json only with evidence of currently installed policy.

**Interface:**
- Input: known owner/consumer, active Job evidence, Git/Artifact outcome, lease expiry, exact workspace source digest.
- Output: deterministic candidate disposition and Runtime workspace.close operation receipt.

Steps:
- [ ] 4.1 RED: demonstrate no-Job disposable, failed/cancelled Job with explicit DISCARD, staged-but-not-merged Git result, active lease, and timed-out observation. Explicitly assert that “last Job succeeded” is not a universal semantic precondition for disposal.
- [ ] 4.2 GREEN: change selection to use real disposition and active-consumer evidence; do not remove source-dependent protections. The four-hour timer triggers evaluation, not arbitrary age-based deletion.
- [ ] 4.3 Replace/retire duplicated operator selection paths after source/provider and actual consumer equivalence are verified. One installed production cleanup owner must remain.
- [ ] 4.4 Run Python focused tests, PG disposable tests, and a read-only dry-run on the actual node before live apply. Do not modify unrelated root paths.

## Task 5 — Minimal external consumer handoff (Host/Artifact/Git)

**Files:**
- Modify only actual consumer API/docs at their natural Owner if current Runtime capability cannot express their release; do not create Host Work per Workspace.
- Test: one real Git change → PR/merge receipt or explicit discard → Runtime Workspace release → re-materialize from exact commit.

Steps:
- [ ] 5.1 Map consumer identities and readsets for exact Git source commit, Host Work objective and Artifact digest.
- [ ] 5.2 Expand only the used wire boundary; test missing/unknown/discarded/published distinctions with consumer-driven schema examples.
- [ ] 5.3 Migrate actual call sites, then Contract by deleting old duplicate fields/paths after both Linux and Windows consumers read the new contract.
- [ ] 5.4 Verify source, merged, installed, executed, consumed separately; don't promote Git merge to domain acceptance.

## Task 6 — Native fulfillment & adversarial engineering checks (not weak-model trials)

**Files:**
- Test: existing services/runtime/crates/ordivon-runtime-mcp/tests/pg_vertical.rs
- Test: existing services/runtime/scripts/tests/test_lifecycle.py
- Verify: services/runtime/formal/WorkspaceConsumerCloseR1.tla, Rust tests, actual Windows provider, GitHub CI.

Steps:
- [ ] 6.1 Demonstrate physical ACTIVE Job cannot be reclaimed, even with malicious/replayed release claims.
- [ ] 6.2 Demonstrate explicit release + source digest + no held Job -> exact close after consumer disposition; replay returns idempotent tombstone.
- [ ] 6.3 Inject a pre-existing failed/lost Job with resolved physical effect and explicit discard; verify eventual cleanup without last-success assumption.
- [ ] 6.4 Inject service restart, concurrent close, trace loss; verify UNKNOWN is not FAIL and pending cleanup eventually converges under stated fairness.
- [ ] 6.5 Verify Windows Native separately. Run consumer review on real provider results, not just compilation.
- [ ] 6.6 Two-axis review: specs/invariants vs source/maintenance quality, as in Matt code-review. Use GitHub checks and protected merge queue, no custom approval service.

## Task 7 — Source retirement, installation, closeout

**Files:**
- Modify: services/runtime/docs/guides/runtime-legos.md, docs/guides/agent-runtime.md, operations.md as needed.
- Remove: superseded in-repo lifecycle/reclaim scripts or inactive legacy adapters only after last real consumer migrated.
- Readback: GitHub PR merge SHA, systemd/SCM installed digest, PG Job/Artifact, Workspace closure receipts.

Steps:
- [ ] 7.1 Publish minimal source delta via GitHub PR, capture CI/merge queue status. No “merged” claim until exact commit is on main.
- [ ] 7.2 Use Runtime Owner's existing qualified deployment path; do not use normal Workspace Job success as deployment evidence.
- [ ] 7.3 On installed Linux/Windows compare contract version, real effect and receipt; if unknown keep deployment standing UNKNOWN.
- [ ] 7.4 Remove old overlapping source/operation instructions and outdated examples, preserve exactly one owner-native reference.
- [ ] 7.5 Verify last consumer accepted published result; close own clean workspace, keep valid Git/Artifact refs; report only consequential open obligations.

## First-slice evidence ledger (2026-11-09)

- TLC RED: liveness CFG missing FairCloseSpec failed with exit 151, naming the absent source contract.
- TLC GREEN: FairCloseSpec with WF_vars(Close), 82 states generated / 28 distinct, no violations in bounded model.
- Independent temporal negative control: fairness removed -> TLC exit 13 and permanent stuttering trace.
- Independent safety-gap counterexample: ExpiredActiveConsumerCannotBeClosed -> TLC exit 12, active consumer + expired age + closed.
- Owner formal check/falsify: PASS after scoped mutation repair; mise run formal:verify: exit 0 on committed source before source rebase.
- Runtime docs: scripts/check_docs.py exit 0. All installed/core-refinement, lease authenticity and real physical acceptance obligations remain unresolved.
- No AI-model comparison was run or proposed. The above is deterministic finite-state contract verification.

## Scope and progress record

Expected first PR (Tasks 1–2): existing formal model has conditional liveness plus named fairness and age-only negative controls. This is specification/model work, not deployed safety closure.
Second PR (Task 3): truthful consumer/disposition contract with source-refined tests.
Third PR (Tasks 4–5): single production GC flow and real consumer handoff.
Fourth PR (Tasks 6–7): physical qualification, versioned deployment and legacy retirement.

No extra metadata registry, test language or role graph is required. For each PR, compare exact current main with the planned source cut before writing. If another Agent already implemented it, keep only unmerged behavior-changing work. End state is tested native capability, not count of documents or new files.


## Pre-implementation independent cross-audit gate — 2026-11-10

The authoritative theory/consumer/review matrix lives in the existing SPEC section 11. Do not create another checklist DSL or cross-owner task database.

**Source currentness:** main SHA 8346863be965da34371944679d063fd9fd0358ac at audit; PR #1981 has already MERGED, #1960 and #1921 already MERGED, #1983 OPEN, and an independent Agent outcome contract PR #1993 is OPEN. Each later implementation task must rebind its own SourceCut and subtract already completed branches.

**Peer collaboration performed:** Host Space messages 25819 (Runtime), 25820 (mathematics/computer science/management/R2.1), and 25821 (independent falsification) were committed by actor:agent:gpt6-runtime-lifecycle-crossaudit-20261110. Sending a message proves only collaboration request; **an actual peer answer, readset and counterexample are required** to mark peer-review PASS. Until then PEER_REVIEW=UNKNOWN, not PASS.

**Gate A — theory, skill, representation, scope (before source behavior mutation):**

- [x] Read native method-router/representation-first and R2.1 formal-model; scoped theory choices: assume–guarantee + source refinement, TLA+/fairness, owner-rooted reachability/leases, TOC/Jidoka/Goodhart.
- [x] Read Matt domain-modeling/TDD/code-review, ECC contract-first/brownfield and Superpowers writing-plans/TDD/verification; use them as advisory thought LEGOs, not Tool authority.
- [x] Recheck exact GitHub source and merged prior PRs; no need to redo #1960 / #1981 / #1921.
- [x] Re-run owner-native formal check on current source: mise run formal:verify exit 0, includes R2 candidate and named negative controls; scripts/check_docs.py exit 0. This is model scope only.
- [x] Publish independent review requests to existing Host Space without assuming a response.
- [ ] Obtain or quote actual independent peer findings for all material objections: correctness of representation, strict theory side conditions, Matt/ECC/Superpowers fit, over-conservative policy, superficial deliverables, proof-to-code bridge, full-system effect, unnecessary duplicate platform.
- [ ] Resolve any FAILED material objection and post corrected exact source cut back to existing Space. Unknown peer replies may not be represented as approval.
- [ ] Authorize Task 3 implementation **only after** the prior two review steps; neither 4h age nor dirty state authorizes destructive action in this preparation phase.

**Gate B — first production behavior slice, natural Runtime Owner:**

- [ ] Test RED through existing WorkspaceCloseRequest/PG workspace.close public seam: an unverified finished-consumer assertion must not create a false source/semantic acceptance claim; concurrently held Job or Runtime continuation blocks physical removal.
- [ ] Implement one minimum owner-scoped consumer/disposition witness with explicit expiry/issuer and exact source-state digest using existing PG/admission fence, not a new global lease store. Permit ordinary disposable sessions to exit with confirmed source outcome.
- [ ] Verify source tests GREEN, negative mutation catches unauthorized close, and Git/PG CAS prevents concurrent renewal/close TOCTOU. Keep outside-owner ambient file readers UNKNOWN.
- [ ] Map actual R2 candidate model states to exact Rust/PG state transitions; no source-refinement claim from TLC alone.

**Gate C — lifecycle and consumer integration:**

- [ ] Consume prior owner PR #1983 as provider evidence or reject with a specific failing native test; do not duplicate its signed-artifact functionality.
- [ ] Fix last-job-success-only and no-Job disposal eligibility through real native source and tests, without allowing unique unresolved data deletion.
- [ ] Integrate actual caller-owned Host/Artifact/Git result handoff. Do not create a Host Work per Workspace and do not give Host physical Close authority.
- [ ] Revalidate existing installed Linux and Windows binaries independently; use current owner release path and physical receipts. Delete superseded SQLite-only/cache/lifecycle adapters only after actual last consumer migration.
- [ ] Perform Matt two-axis review (standards vs spec) and independent falsifier review; verify actual effect, not just test/PR count.

**Stop rule:** a zero-diff/unchanged existing provider result means REUSE, not a new PR. A complete Spec with no executable consumer effect is not the reform's terminal success; however a missing peer reply is transparently UNKNOWN and must not be falsified by self-scoring. No weak-model experiments.
