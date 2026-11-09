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

## 9. Mathematical foundations and why these representations are chosen (2026-11-09 addendum)

This section is the bounded formal argument for T1–T6, not an additional authority or mandatory read on routine changes. The source-of-truth remains the concrete Git/Owner/domain implementation and actual consumer evidence.

### 9.1 Typed transition relation, Hoare logic and refinement

For an independently contractable, stateful R2.1 LEGO `ell` with I/O and state S, a useful semantic interpretation is a relation:

`R_ell ⊆ (I × S) × (O × S × Trace(Eff))`

The eleven R2.1 coordinates are not replaced by this relation: `pre`, `post`, `inv`, `eff`, cost `c`, equivalence/approximation `epsilon`, provenance `prov`, and bounded unfolding `unfold` constrain how it may be used. Unobserved cost, error, authority, or actual implementation standing must remain typed UNKNOWN.

A Hoare-style proof obligation `{P} impl {Q}` establishes only its stated pre/post property under the implementation's actual operational assumptions. For an implementation to refine a specification at a named observation boundary:

`Obs_C(Traces(Impl | A)) ⊆ Obs_C(Traces(Spec | A))`

where `A` names environment assumptions, and `Obs_C` is the concrete consumer's observation function. A finite TLA+/TLC model and a passing test are distinct evidence types; neither, without an explicit code-to-model bridge, discharges this implementation refinement.

For a candidate package or adapter, the public contract is the seam. A source-local implementation detail is not automatically a public contract or a distinct LEGO. Prefer externally supplied contract/proof systems (language type checkers, Lean/TLC, Hypothesis, native test suites) to a custom Ordivon calculus.

Grounding: Dijkstra/Morgan refinement calculus, Bertrand Meyer's Design by Contract, Abadi–Lamport compositional specifications, Pnueli–Siegel–Shtrichman translation validation.

### 9.2 Assume–guarantee composition, not local model greenwashing

A producer has assumptions `A_p` and guarantees `G_p`; a consumer requires `A_c` and offers `G_c`. The usual schematic composition prerequisite is `G_p ⇒ A_c` plus compatible type, authority, side effects, state and consumer observations. This is NOT a universal proof rule for circular/temporal systems. In an open reactive system, naive classical implication `A ⇒ G` can admit unrealistic traces when an environment violates assumptions later; use the appropriate temporal assume–guarantee semantics when necessary.

In Ordivon:
- Git provides exact source identity, not deployment identity.
- Runtime provides physical execution/recovery facts, not the user's goal.
- Host provides Work/Space/Topic continuity, not domain or Git proof.
- Gateway routing, Tool discovery and Skill reading grant no business authority.
- Source/model checks that do not read installed bytes cannot certify installed effects.
- Each consumer supplies the final semantic oracle appropriate to its own domain.

A public seam is admitted only after producer guarantees cover the consuming assumptions **under the assumptions actually checked**. Unchecked environment assumptions are UNKNOWN, never converted to FALSE or PASS.

### 9.3 Exact Git SourceCut DAG proof obligation (T1 implementation)

Let `b = resolve_commit(base_ref)` and `h = resolve_commit(head_ref)` under Git's real object DAG, with replacement overlays and grafts suppressed. Let `m = unique_merge_base(b,h)`. The qualified changed-path observation is:

`Delta(b,h) = ChangedPaths(Tree(m), Tree(h))`.

`b` is not necessarily `m`: if the branches diverged, claiming the diff starts at `b` is a false witness. Emit `sourceCut = {base:b, head:h, diffBase:m}` for exact Git-difference qualification and reject absent/ambiguous merge-bases; emit `null` for caller-declared paths and ALL_OWNERS selection.

This is a *source-selection* witness only. It does not certify code quality, dependency completeness, GitHub policy, provenance of a human task, or application-level behavior. Invalidation: if `b`, `h`, `m`, Owner routing, or a consumed verifier readset changes, recompute the affected qualification.

### 9.4 Proof graph, incremental recomputation and epistemic standing

For a qualified claim `q`, let `D(q)` be the precise source, model, contract, verifier and environment readset needed by its real consumer. A previous proof may be reused only when those relevant inputs remain valid, or when a checked independence/refinement argument establishes that the changed inputs cannot alter the claim.

`Reuse(q, t_2) ⇒ Current(D(q), t_2) ∨ VerifiedNoninterference(Delta, D(q))`

This is a necessary admission obligation, not a complete algorithm. It resembles build dependency and cache-key semantics in Bazel but must not equate hash equality of a file with semantic equivalence or copy a build cache into an evidence authority.

Evidence status is typed and scoped: OBSERVED, DECLARED, DERIVED, MODEL_CHECKED / VERIFIED (named property and verifier), FALSIFIED, UNKNOWN, and NOT_RUN. In particular `UNKNOWN ≠ FALSE`; not knowing whether a domain consumer exists does not prove deletion safe, and a static path scan does not prove absence of dynamically loaded consumers.

### 9.5 Counterexamples, sound abstractions and independent validation

Use mature CEGAR principles for formal models: deliberately abstract only the property-relevant state; when a counterexample appears, classify whether it is concrete or spurious and refine the minimal abstraction. No generic model-wide state explosion or independent Ordivon model-checker.

Use translation validation for Agent candidates: validate each meaningful candidate at an existing *independent* source/Owner/consumer seam rather than attempting to prove every Agent correct. Test/verifier edits and implementation edits in the same candidate may share errors; compare the affected verifier against a pinned baseline and independent consumer before claiming contract continuity.

Negative tests are required *where an actual invariant changes*. They are ordinary engineering regression/falsification tests, NOT weak-model trials.

### 9.6 Design objective: allow safe action, block false admission

The hard feasible set `F = {x | I_1(x) ∧ ... ∧ I_n(x)}` contains only mechanically enforceable, cost-justified invariants. Within F, compare candidate consumer value, total lifetime cost, recovery and reversibility. DELETE→REUSE→COMPOSE→CREATE is a default search order, NOT a mathematical theorem that deletion or reuse is always optimal. Liveness of low-risk reversible work must not be traded away to maximize the count of safety gates.

For a new requirement: identify goal → actual consumer → Owner source/effect truth → public contract → mature supplier → focused verification → result readback. If no consumer needs a new layer, omit it.

## 10. Execution dependency graph and concrete natural owners

| Slice | Natural owner / current interface | Dependency | Acceptance / falsifier |
| --- | --- | --- | --- |
| T0 | repo docs and current SourceCut, same spec | none | Spec bound to verified upstream commits, real current Owner |
| T1 | `tools/repo/affected_owners.py` + existing unittest | T0 | Exact b/h/m Git witness; diverged branches cannot misstate the diff basis; caller-declared source is not Git proof |
| T2 | existing `.agents/skills/method-router/`, Owner README, Host explicit Work view | T1 | Goal→actual Owner/consumer can be navigated without a second Skill or Task registry; inspect merged #1980 before editing |
| T3 | GitHub existing required check and repo-native governance tests | T1 | Verifier weakening cannot self-certify; protected rules observed from GitHub, not guessed from YAML; retain fast reversible workflow |
| T4 | `tools/formal/` plus targeted Owner formal and native tests | T2 and T3 | Explicit assumptions and model↔implementation bridge; a TLC/Lean model PASS alone is never an installed/domain claim |
| T5 | existing method-router, recursive-lego-calculus, Owner-local documentation | T4 | One usable thin method entry; no new global mandatory process, no duplicated upstream full skill install |
| T6 | existing GitHub PR/Merge Queue, Owner installation/readback, domain consumer | per-slice | Separate SOURCE, MERGED, INSTALLED, EXECUTED, CONSUMED statuses |

For execution, take the smallest currently unblocked *nonduplicative* slice. Inspect merged/open GitHub PRs and the existing Host Space before creating a new branch. Prefer extending a related existing PR when its proof/consumer frontier is the same. Changes to a root verifier are high consequence and need independent baseline/source qualification; changing a doc is not automatically a domain release.

### 10.1 Exact test-and-deliver procedure for each runnable slice

1. Capture `git ls-remote origin refs/heads/main` and one detached/branch Runtime Workspace; inspect current PRs and contract.
2. Fix the public seam, its input/output types, exact property, and one likely counterexample. Follow Matt's spec/vertical-slice method and ECC's search-first/change-impact; do not interview the user again for already-known constraints.
3. Add the smallest native regression proving that the current implementation fails the new intended property (RED) when modifying behavior. Prefer the actual public CLI or owner consumer over private mocks.
4. Implement the smallest native change (GREEN). Avoid new cross-cutting registry and avoid changing unrelated Owner implementations.
5. Run native verification, Git diff/format, a negative case and an independent consumer where material. Adhere to Superpowers' evidence-before-completion, but do not turn source-only cleanup into a mandatory full-stack test suite.
6. Review the exact `merge-base...head` diff on two axes: spec/consumer fulfillment and repo/Owner standards.
7. Commit in the isolated workspace. Rebase on freshly observed current main, rerun affected native checks, publish an ordinary PR, and use the existing protected merge queue.
8. Post exact SHA/PR/commands and remaining UNKNOWN into the existing Space topic; do not mistake a Host Message for collaborator acceptance or a Git push for production deployment.

### 10.2 Acceptance ledger without a new database

A task is not done until the *claimed* level has evidence:
- SOURCE: exact Git object and native source tests.
- MERGED: remote PR/merge evidence.
- INSTALLED: producer-owned active deployment and read-back.
- EXECUTED: execution/effect receipt and recovery disposition.
- CONSUMED: domain/customer-visible acceptance.

If only the first two have been verified, report SOURCE/MERGED and mark the others UNKNOWN/NOT_APPLICABLE as appropriate. Keep this in existing PR, Git and native Owner outputs; do not persist it in a new global authority table.

## 11. Primary research / upstream references

These are methodological sources, not automatic current implementation or deployment authorities:
- Abadi & Lamport, *Conjoining Specifications* (1995): https://www.microsoft.com/en-us/research/publication/conjoining-specifications/
- Abadi & Lamport, *Composing Specifications* (1993): https://www.microsoft.com/en-us/research/publication/composing-specifications/
- Chilton, Jonsson & Kwiatkowska, compositional assume–guarantee I/O contracts: https://doi.org/10.1016/j.scico.2013.12.010
- Morgan, *Programming from Specifications*: https://www.cs.ox.ac.uk/publications/books/PfS/
- Eiffel, Design by Contract: https://www.eiffel.com/values/design-by-contract/
- Pnueli, Siegel & Shtrichman, translation validation: https://cs.nyu.edu/home/people/in_memoriam/pnueli/transval-icalp98.html
- Clarke et al., counterexample-guided abstraction refinement: https://web.stanford.edu/class/cs357/cegar.pdf
- Necula & Schneck, proof-carrying code: https://people.eecs.berkeley.edu/~necula/ISSS02/
- Iris concurrent separation logic: https://iris-project.org/
- Bazel action graph/readset: https://bazel.googlesource.com/bazel/+/015f586fcb2e127ed13691b573de42cd9dba8508/site/docs/glossary.md
- Matt Pocock pinned Skills: https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
- ECC pinned Skills: https://github.com/affaan-m/ECC/tree/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b
- Superpowers pinned Skills: https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7

Research is adopted selectively when a real Ordivon Owner can state the transferred invariant and the native evidence to check it. Do not convert the references into mandatory global onboarding, a hidden super-Owner, or a second R2.1 calculus.
