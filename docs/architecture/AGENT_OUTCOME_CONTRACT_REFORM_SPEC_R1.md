# Ordivon Agent Outcome Contract Reform — Executable SPEC R1

Date: 2026-11-09
Status: ADOPTED DESIGN / IMPLEMENTATION IN PROGRESS. This file is a bounded implementation contract, not a new runtime, owner, registry, or current deployment claim.
Baseline: `ordivon@3b43977e682d8c7668f6371ffd998c7821e4312a`. Each implementation task must re-read current protected main and its relevant live consumer before acting.

## Problem and desired behavior

A user delegates an outcome to Ordivon. Agents can substitute explanation for implementation, preserve useless historical carriers because a weak textual reference exists, introduce parallel frameworks, overstate completion after tests, or delete active consumers because static references are absent. Longer instructions cannot enforce correct physical effects or evidence claims.

Desired behavior: allow Agent exploration but constrain the effects and completion standing with existing Owner-native, version-bound contracts. A successful result is the consumer-accepted outcome, not a plan, local test, Job exit, PR text, or model assertion. Make erroneous claims and illegal state transitions unrepresentable where native mechanisms allow. Where the semantic target cannot be machine-decided, preserve scoped UNKNOWN, not invented PASS or unlimited blocking.

The reform is deliberately **not** a universal contract engine, a second Host Workflow state machine, a new Agent evaluator or a new Registry. Adopt existing Git, Host, Harness, Runtime, Artifact and natural-Owner surfaces.

## User outcomes and negative cases

1. As the task requester, I want an Agent to act on a feasible goal and distinguish completed work from planned work, so a report cannot impersonate delivery.
2. As a repository consumer, I want obsolete source/docs retired when covered by current authorities, without losing unique source or evidence.
3. As an Owner, I want to use my native acceptance boundary instead of a global reviewer or multiple approval rounds.
4. As a collaborating Agent, I want exact main/branch/installed/source identity so old tests and old documents do not masquerade as current facts.
5. As a Runtime operator, I want idle, eligible Workspaces to be reclaimed by native lifecycle, with live Jobs and unreleased physical state protected.
6. As an analyst, I want unknown dynamic consumers to hold only their affected candidates, not the unrelated certain portion of a batch.
7. As a maintainer, I want known externally mature methods reused in the current workflow, not a fully installed parallel Agent framework.
8. As a final consumer, I want one real end-to-end acceptance for an affected effect; a source build alone is not installation or domain success.

Counterexamples that must be rejected:
- A five-page clean-up report is counted as success despite zero source retirement.
- PR tests are green, but GitHub still reports OPEN; the report calls it merged.
- An old provenance slug is classified as an executed file reader with no evidence.
- One UNKNOWN dynamic caller freezes retirement of dozens of independently classified files.
- A missing static reference authorizes deleting an installed executable or the only retained original bytes.
- A clean Workspace is removed while a durable Job is active; a dirty Workspace is force closed to improve metrics.
- A new bespoke orchestration/registry is admitted when existing Owner-native APIs satisfy the contract.

## Semantic boundaries

- Human/requester: defines the desired goal, authorized scope and risk posture.
- Domain/consumer Owner: owns acceptance of its observable outcome. No tool or Skill can transfer that authority.
- Git + protected merge queue: owns source history, source diff, exact main/head and integrated source state.
- Host: owns durable collaboration Work/Topic/Message CAS, not scheduling or business success.
- Harness: owns bounded Agent Run and cognition/tool continuity; `RunFinished != TaskAccepted`.
- Runtime: owns Jobs/Attempts and physical Workspace lifecycle; `JobSucceeded != EffectAccepted`.
- Artifact: owns retention/verification of selected immutable product evidence, not every scratch file.
- Skills: optional reasoning procedures; read access does not grant effect authority.

An 'Agent Task' here is a semantic request for a consumer outcome, not a newly defined Host or Runtime entity. Source, merged, installed, executed and consumed remain independent evidence predicates.

## Representation and formal obligations

Use existing Recursive LEGO R2.1 where there is an independently contractable responsibility. For this reform, the **thinking LEGO** is an Owner-bound outcome acceptance method, not one LEGO per document.

    ell = (I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)
    I = (goal, sourceCut, owner, consumer, requiredClaims, observedEvidence)
    O = (disposition, supportedClaims, scopedUnknowns, nextNativeAction)
    S = existing Git/Host/Harness/Runtime/Owner facts; no separate persistent store
    pre = exact subject/source, known effect authority and identified acceptance owner
    post = a claim is supported at its exact observed authority level; no invented effect
    inv = UNKNOWN != FALSE; PLAN != ACTION; RUN != TASK; PASS != INSTALLED;
          MERGED != CONSUMED; no unsafe retirement on static absence alone
    eff = read-only qualification; action only via existing Owner-native authorized tool
    c = bounded readset/affected-owner traversal, not mandatory full-repo proof
    epsilon = model/consumer/physical coverage limits remain explicit
    prov = source SHA, exact native result, current installed/consumer readback where needed
    unfold = choose next action -> execute -> read actual effect -> falsify -> accept or repair

Obligation S1 (safety): `ClaimComplete(scope) => VerifiedRequiredReceipts(scope)`; missing evidence is NOT_RUN/UNKNOWN, not PASS.
Obligation S2 (retirement): `Retire(x) => NoRequiredCurrentConsumer(x) AND RequiredEvidenceRetained(x)`, relative to observed roots; unobserved dynamic roots are UNKNOWN.
Obligation S3 (authority): `AuthorizedEffect(x) => NativeOwnerAdmits(x)`; Skill instructions and model declarations are not effect capabilities.
Obligation P1 (conditional progress): for an eligible, supported and authorized action under a fair executor, eventually observe an Owner effect or a concrete blocker; plans and endless analysis are not terminal evidence.
Obligation S4 (identity): `Observation.Subject = Claim.Subject`, including SourceCut/installed node when material.
Obligation S5 (composition): local LEGO verification establishes a system result only after consumer assumptions at seams are discharged.

No global theorem of model correctness or minimal description length is claimed. Prove/check only properties reachable through the current natural Owner. Existing Runtime TLA+/Kani/PG tests and Host model/PG tests are the appropriate native methods for their respective effects.

## Upstream method selection — reference/extraction, no bulk install

Reviewed primary Skill prose, read-only, at these upstream Git HEADs:

- Matt Pocock Skills `mattpocock/skills@4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`: `to-spec` (consumer-facing scope and high-level test seam), `domain-modeling` (distinguish Task/Run/Job/Work and facts), `implement-spec` (dependency frontier and implement/review), `writing-for-agents` (navigation should lead to actual tools). Do not import its issue-tracker setup, user interview gate or subagent orchestration.
- ECC `affaan-m/ECC@d2ef2680594f9a17526a6e1a2e18b3d242c5d17b`: `tdd-workflow` (test -> implementation -> verification with traceable evidence). Do not import its universal 80% coverage rule, shell-approval workflow, package manager scripts, hooks, scoring, memory system or 300+ Skills.
- Superpowers `obra/superpowers@22f0b463e7a5e579904dd6211a520321035526f7`: `writing-plans` (small testable file-specific tasks), TDD and verification-before-completion methodology. Do not add a second Agent dispatch layer, mandated per-step commits, or new docs/superpowers hierarchy.

Exact package installation, executable code execution and generalized supply-chain approval are out of scope. Source prose is untrusted reference material; the canonical local procedure is still the existing method-router, recursive-lego-calculus, consumer-rooted-retirement and each natural Owner's contract. Follow local Skill supply-chain audit if a future task actually vendors external bytes.

## Execution programme (dependency order, no weak-model experiments)

### T0: establish one consumer-readable plan and accurate status [repository documentation]

Files: create this spec; add one scoped pointer from `docs/start/tasks.md` for consequential cross-Owner work. Do not duplicate root `AGENTS.md` policy.

- [ ] Confirm SourceCut and current open PR/installed boundaries.
- [ ] Publish this exact outcome contract and route consumers to it.
- [ ] Run `git diff --check` plus the existing architecture/document checks.
- [ ] Commit, open a protected PR, obtain current GitHub review/check and merge readback.

Acceptance: future Agent can navigate from the current task index to this spec; no new state database, roles or execution permissions.

### T1: complete existing history-retirement delivery [Git + Media/repository]

Existing candidate: GitHub PR #1946, 79 unused history documents and Media foundation consolidation. Do not replace it with another PR.

- [ ] Re-read exact GitHub main/head SHA, full changed paths, current PR checks and potential overlap.
- [ ] Use existing `tools/repo/convergence_plan.py` for bounded SourceCut questions, `tools/repo/affected_owners.py` for impact, and affected native Owner tests.
- [ ] For any newly disputed document, test real static/configured/dynamic/installed consumers and retained unique evidence; hold only disputed candidates.
- [ ] Submit existing PR through protected GitHub integration only; resolve actual CI/merge conflicts instead of adding explanation.
- [ ] Read back merged main, deleted Git entries and current Media navigation. If merge is blocked, preserve exact blocker and continue on an independent ready frontier.

Acceptance: `MERGED` with exact main SHA, scoped Owner tests and no broken live consumer; `OPEN/CLEAN` alone is not completion.

### T2: production Workspace lifecycle [Runtime]

Already integrated: PR #1960 changes default clean retention to four hours. PR #1925 provides PG-native hourly automatic closure and is currently failing `repo-preflight` / `root-verification`.

- [ ] Investigate #1925 exact failed CI logs and identify a reproducible source/environment cause.
- [ ] Repair using the Runtime natural Owner and isolated Git branch, avoiding overlap with active implementers.
- [ ] Verify Runtime's original close fences for active/held Jobs, pinned/dirty/unreleased state and exact source-state CAS; choose only relevant native model/PG/Linux physical checks.
- [ ] Integrate through protected GitHub checks/merge queue.
- [ ] Observe installed service/timer/PG retention policy and actual eligible Workspace closure on the relevant node. Distinguish source integrated, installed and executed.

Acceptance: observed eligible closure or specific truthful blocker; no forced deletion of busy or unintegrated work. A changed 4h JSON alone is insufficient.

### T3: bounded goal-to-consumer completion seam [existing caller / natural Owner]

Do not create a universal Host completion engine. Select an existing Task/PR consumer that already has a machine-observable result. Define the exact required evidence for *that consumer only*.

- [ ] Write failing regression for one real false completion claim (e.g. `PR_OPEN` presented as `MERGED`), in that consumer's existing test suite.
- [ ] Implement smallest change in its existing native integration/readback path.
- [ ] Verify positive and negative cases: exact merged SHA, still-open PR, stale SourceCut, unavailable external readback. `UNKNOWN` must remain non-success.
- [ ] For effects beyond code, include the needed installed/domain readback; do not infer it from PR/CI.
- [ ] Remove any newly made duplicate checker if existing native result already enforces the property.

Acceptance: one concrete illegal success path is rejected by a consumer-bound test, with an actual source diff and independent falsifier. No generalized completion score or universal policy service.

### T4: composition, retirement and evidence closeout [natural Owners]

- [ ] Confirm T1/T2/T3 consumers independently; trace source -> integrated -> installed -> consumed only as applicable.
- [ ] Update current README/Skill entrypoints only where source changes require it.
- [ ] Retire superseded draft plans, scripts and obsolete compatibility paths with Owner-native operations.
- [ ] Close fully integrated clean Workspaces via Runtime, with readback, and record remaining scoped UNKNOWN in existing Git/Host issue or Work.
- [ ] Reassess this spec's utility after integration; if it adds no unique consumer value beyond existing Owner docs, delete it rather than retaining another permanent governance authority.

Acceptance: observable consumer effects, old source debt decreased, no new framework/registry and no permanent redundant process.

## Implementation method per task

Follow Matt's consumer-first domain modeling, then Superpowers' smallest independently reviewable diff, ECC's RED/GREEN only when implementing code, and Owner-native verification. Each task is an actionable branch/frontier, not a new recurring review ceremony. Preserve SourceCut, tested property, counterexample and readback in normal Git commits/PR descriptions rather than another evidence database.

A test can prove the code property it exercises; it cannot prove that a process actually ran, an external side effect occurred, or a domain user accepted the outcome. The method choice stops once it cannot change the next executable action. Do not run weak-model or model-ranking experiments.

## Open questions and exact stop conditions

- Dynamic external consumers of a retirement candidate: UNKNOWN scoped to the candidate until actual consumer observation.
- Installed Runtime lifecycle when source changes are merged: UNKNOWN until service/timer/PG/native close readback.
- #1925 status: currently blocked; CI results and source identity must be re-read before repair.
- Whether a universal Task completion interface is warranted: NOT ADMITTED; only promote on repeated missing consumer contracts with evidence.

The programme is complete only when its named consumer effects are observed, and rejected states cannot be promoted to success by self-report. Publishing this spec alone fulfills T0's planning artifact, not T1–T4.
