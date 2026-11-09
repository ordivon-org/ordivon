# Ordivon Agent Contract Admission — Execution Spec R1

Status: IMPLEMENTATION SPEC; source-qualified baseline 05fec3688cf1ae1f091a2dd080784249becbc18a (2026-11-09).
Owner: repository mechanics for source verification, with all domain and effect truth retained by natural Owners.
Consumer: contributors/Agents generating candidate changes, GitHub root-verification, each affected Owner's native tests, installed consumers.
Supersession: does not replace docs/architecture/STRUCTURE_R2.md, Recursive LEGO R2.1, any Owner contract, or existing CI/GitHub governance.

## 1. Problem and success condition

A model can correctly describe Ordivon principles while producing a candidate that violates them, or avoid valuable work through over-caution. Prompt instructions alone cannot make an irreversible claim or external effect true. The engineering objective is model-independent admission of candidate *claims and changes* at the highest already-existing public boundary, while enabling low-risk reversible work without new approval machinery.

The end-user outcome is working capabilities, not more plans, workflows or governance objects. A change is SOURCE-qualified only by exact Git evidence and affected native checks; a merged PR is not an installed release; a Runtime terminal Job is not domain success.

## 2. Grounded upstream methods

Pinned source inputs (read as external methods, not blindly installed or executed):
- Matt Pocock skills at 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d: to-spec, to-tickets, implement-spec, tdd, code-review, writing-for-agents. Adopt spec synthesis without repeated interviews, dependency-aware tracer bullets, public seam tests, fixed-point reviews, and concise pointers.
- affaan-m/ECC at d2ef2680594f9a17526a6e1a2e18b3d242c5d17b: search-first, change-impact, module-governance, context-and-decisions, verification-loop. Adopt mature-supplier discovery, domain terms separated from decisions, impact-first verification, and evidence. Reject wholesale installation of hundreds of overlapping skills and generic one-size-fits-all tooling/coverage thresholds.
- obra/superpowers at 22f0b463e7a5e579904dd6211a520321035526f7: writing-plans, executing-plans, test-driven-development, verification-before-completion. Adopt precise paths, observed RED/GREEN for behavioral changes, immutable fixed-point reviews, verified completion. Do not impose heavy TDD rituals on pure cleanup or an extra Agent workflow runtime.

Use local .agents/skills/method-router and recursive-lego-calculus; do not create new universal Agent Skill/Task/Policy registries.

## 3. Existing natural seams (no new authority)

1. Git commit/tree and PR merge queue establish source identity and integration.
2. tools/repo/owners.toml and affected_owners.py select Owner-native tests. This is source verification routing, not domain truth.
3. tools/repo/dependency_contracts.toml and check_owner_boundaries.py enforce observed literal public seams with explicit limitations.
4. .github/workflows/ci.yml and root-verification require native preflight, repo mechanics, and selected Owner jobs. GitHub ruleset is external policy authority.
5. Owner public API and real consuming tests determine semantic acceptance; Runtime/Host/Workstation/Domain provide different observed facts.
6. README/AGENTS/Skills explain how to work. Their text alone cannot authorize an effect or declare correctness.

## 4. Formal/LEGO model

Notation uses R2.1 ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold) for one *independently contractable responsibility*. Files, tests, Agents, Skills and workflow stages are NOT each separate LEGOs.

Source-change qualification LEGO:
- I: (base Git commit, candidate Git commit, changed paths, current Owner manifest, public seam declarations).
- O: typed source-selection witness (selection basis, pinned source revision(s), affected Owner native tasks, and applicable static boundary standing).
- S: finite immutable qualification observation, not mutable domain state or a new registry.
- pre: base and candidate resolve to commits; Git DAG is read without replacement/grafts; executor has an exact source tree.
- post: Git-derived paths are bound to resolved source revisions; caller-supplied paths never impersonate Git-derived proof; every admitted execution path is registered or rejected.
- inv: unregistered source path cannot be silently admitted; UNKNOWN cannot be promoted to PASS; static boundary PASS cannot assert installed or domain correctness.
- eff: read-only source projection; no Git push, installation, external transaction or business effect.
- c: native Git and bounded stdlib execution costs; no new daemon.
- epsilon: explicit residual uncertainties for dynamic imports, installed identity and real consumers.
- prov: Git SHA, verifier version/source revision, exact checks and outputs.
- unfold: delegate mechanical checks to the existing Git/Owner/CI tools, then independently accept in each actual Owner.

Assume-guarantee:
- Repo qualifier guarantees only (Q1) exact source-change lineage, (Q2) correctly selected declared Owner-native checks, (Q3) bounded source-seam checks, conditional on trusted Git inputs and current manifest.
- Each Owner guarantees only its own public contract after relevant native verification, subject to actual provider/runtime assumptions.
- Installed/consumer verdict requires corresponding owner observations. Source PASS does not imply installed/consumed PASS.

Proof obligations:
I1. In SOURCECUT comparison mode, the reported base/head are exact immutable commit IDs used for selecting changed paths.
I2. In CALLER_DECLARED mode, an input path is not represented as verified source identity.
I3. In ALL_OWNERS mode, no source-change or semantic-completion proof is fabricated.
I4. Owner selection and registered execution-path rejection remain unchanged.
I5. Invalid, missing, skipped and contradictory evidence cannot become VERIFIED solely by generating a report.
I6. Governance checker changes cannot self-certify: independent historical/base verification must be considered; GitHub required-check protection alone is not complete verifier independence.
I7. Consumer-native acceptance is required for claims of semantic completion.

Liveness: low-risk reversible changes can proceed in isolated worktrees without a new universal approval gate. Refusal requires an applicable violated contract or consequential UNKNOWN; not generic caution.

## 5. Tracer-bullet execution graph

T0 [READY]: Snapshot current upstream methods, repo SourceCut, existing proof/verification owner; publish this spec in existing architecture docs. Acceptance: source references pin exact commits, scope and non-goals are explicit.

T1 [BLOCKED_BY T0]: Make the existing affected_owners JSON source-qualification witness explicit, without introducing a task store. Extend its public JSON projection with selectionBasis and Git-backed immutable source revision(s). CLI modes retain backwards compatibility. In Git-range mode, resolve base/head to exact commit objects before diff; reject invalid refs. In caller-changed-file and --all modes, do not claim an exact source-cut witness. Acceptance: positive and negative tests exercise public CLI, capture RED before code change and GREEN afterward; repository mechanics remain green. This is the first implementation slice.

T2 [BLOCKED_BY T1]: Bind affected Owner and existing source-graph impact views to a compact on-demand Agent handoff in existing documentation/Skill routing. No new daemon, registry, forced read or permanent per-task capsule. Acceptance: the Owner/path/CI commands are directly executable and no false installed/domain claims appear.

T3 [BLOCKED_BY T1]: Strengthen verification-governance change handling at the actual GitHub admission authority. Audit whether default-branch protected workflows or independent baseline tests are possible without unnecessary human reviews; if not, retain explicit UNKNOWN and a narrowly scoped contract. Acceptance: a candidate that weakens its own verifier cannot be reported as independently verified solely by passing candidate-owned tests; unchanged routine Owner changes keep current fast merge path. Do not assert GitHub protection without live ruleset observation.

T4 [BLOCKED_BY T2,T3]: Add source-bound formal/refinement obligations only where current owner code exposes a provable property. Prefer existing tools/formal, Lean/TLA+, Hypothesis and consumer-native state-machine tests. A model proof and executable implementation refinement are separate standing. Acceptance: property, assumptions, source-to-model mapping, test and counterexample are reproducible from exact commit; no duplicate generic prover or registry.

T5 [BLOCKED_BY T4]: Roll out reusable methodology by linking existing method-router, appropriate Owner instructions and real consumer native tests. Do not install all Matt/ECC/Superpowers skills globally or create an alternative Skill store. Acceptance: AGENTS remains short, low-risk work remains direct, no duplicate compulsory workflow.

T6 [BLOCKED_BY T1]: Integrate using existing GitHub PR/merge queue with independent review of spec-vs-diff and standards-vs-diff. Track SOURCE, MERGED, INSTALLED, EXECUTED and CONSUMED as distinct observations. Acceptance: exact PR/head/CI status and actual consumer verdict, not a completion percentage.

Concurrency: T3 may progress alongside T2 once T1 lands. T4 only depends on both. Each ticket is a separate useful vertical slice and must not accumulate speculative scaffolding.

## 6. Concrete first-slice files and commands

T1:
- MODIFY tools/repo/affected_owners.py (existing --format json only).
- MODIFY tools/repo/test_affected_owners.py (public CLI tests; use native Python unittest and temporary Git repositories).
- KEEP .github/workflows/ci.yml, tools/repo/owners.toml, and runtime unchanged.
- VERIFY python3 -m unittest tools/repo/test_affected_owners.py, python3 tools/repo/check_owner_boundaries.py, python3 tools/repo/check_architecture_docs.py, and applicable root native checks.
- REVIEW git diff BASE...HEAD; inspect claims against both spec and repository standards.

## 7. Non-goals and removal rules

- No weak-model evaluation or benchmark suite.
- No global contract broker, new project-management subsystem, mandatory new status DB, general proof engine, or parallel CI framework.
- No requirement that every ordinary file or document carry eleven LEGO fields.
- No unnecessary interviews, work approvals, artificial stage-gates, or week-long deferral of reversible work.
- No ungrounded claim that static checks prove all dynamic dependents or that a successful job proves user value.
- Delete duplicate machinery when an existing owner/native provider already fulfills the same contract; use Git history for retired superseded prose.

## 8. Acceptance matrix

SOURCE: exact Git commit/tree and an honest selection basis, required checks passed.
MERGED: GitHub authoritative merge result and required check; not implied by local commit.
INSTALLED: corresponding release/artifact/node identity observed by deployment Owner.
EXECUTED: actual runtime effect/receipt with bounded uncertainty.
CONSUMED: domain/application consumer's independently observed acceptance.
UNKNOWN: remains explicit and cannot be treated as FAILURE or SUCCESS.

Spec success is not the number of files added. It is fewer agent-dependent judgment steps at core admission boundaries, preserved forward progress on reversible work, and correct independent evidence at each real Owner consumer.
