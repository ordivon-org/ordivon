# Data Consumer-Bound Delivery R1 — implementation specification

Status: IMPLEMENTATION IN PROGRESS. SourceCut: `3b43977e682d8c7668f6371ffd998c7821e4312a` (GitHub main, 2026-11-09). Owner: Data; independent final consumer: Research; adjacent owners: Artifact, Finance, Runtime, repository CI.

## Problem statement

A domain consumer needs one exact, compatible and currently verified output, not a global declaration that every historical product in a catalog is available. In the existing inspection CLI, a FALSIFIED unrelated distribution globally forces process exit 2 even when the explicitly selected product/version/port is VERIFIED. This is a *scope mismatch*: a local counterexample vetoes a different, consumer-scoped guarantee. At the same time, treating a selected integrity PASS as Research outcome acceptance would be unsound. The owner cannot solve either defect by stronger natural-language Agent prompts.

## Outcome and solution

The consumer can request the exact product ID, version and distribution identity, inspect current source bytes, and receive a scoped integrity decision. Evidence for other ports remains visible, but only selected-port evidence governs selected-port admission; a global integrity request still evaluates the entire catalog. Structural catalog ambiguity or invalid metadata always fails; invalid selected bytes always fail. A Research handoff independently validates its source and analysis receipt before any business decision. Existing GitHub CI and owner-native tools are the only authorities for code changes. No new Data registry, scheduler, broker, policy engine, speculative data materializer or second verifier is authorized.

### Acceptance stories

1. As Research, I can consume a verified JSON port while an unrelated Parquet port is UNKNOWN.
2. As Research, I can consume a verified exact port when a separate unrelated distribution has a detected digest mismatch; the mismatch remains reported, but cannot veto the selected port.
3. As an inspector of the entire catalog, I still receive a failed global gate on any observed FALSIFIED distribution.
4. As a consumer of a FALSIFIED selected port, I cannot pass the selected gate by changing another port's evidence.
5. As a consumer of an UNKNOWN/missing/wrong-version selected port, I cannot obtain a verified admission.
6. As a maintainer, I cannot obtain a success from an empty selection or duplicate/ambiguous identity.
7. As Research, I receive a business ACCEPTED/HOLD decision only after independent source and analytical receipt read-back. A Data gate alone cannot return that decision.
8. As a maintainer, I can reproduce proof, native tests and the concrete consumer using existing `mise` and Python tooling.
9. As a successor Agent, I can recover the problem, decisions, task DAG, exact source revision, acceptance evidence and retirement criteria without a long conversational transcript.

### Contract / representation

Use the existing producer ODPS 1.1 and bounded DCAT 3 projection; no conversion to a different ODPS 4.x family, no invented file location or access grant. Distinguish three independent predicates:
- `GlobalIntegrity(C)`: nonempty catalog distributions, all current local integrity observations VERIFIED.
- `SelectedIntegrity(C,R)`: nonempty, unambiguous requested identities R; every requested distribution VERIFIED by current local read, independent of unrelated distribution verdicts.
- `DomainAccepted(D,X)`: the natural domain consumer's independently executed contract, not inferred from either Data predicate.

`FALSIFIED` stays a negative observation within its own identity/scope and is never turned into PASS; `UNKNOWN` is neither FALSE nor PASS. Structural catalog errors, product duplicate IDs, malformed checksum binding and conflicting digests on the same distribution remain rejection conditions *before* deciding the selected subset. A selected-only CLI result must expose both global and selected verdicts.

One independent responsibility (LEGO candidate) is **Selected Data-Product Integrity Admission**. R2.1 instantiation at this boundary:
- I: list of product/version/distribution identity requests and catalog observations under qualified local allowed roots;
- O: typed selected admission result, observed per-port verdicts and global context;
- S: read-only in-memory discovery projection; no durable registry;
- pre: exact, nonempty, unique selected identities and structurally valid catalog;
- post: selected PASS iff every exact selected port is currently VERIFIED; global observations preserved;
- inv: missing/unbound is UNKNOWN; unrelated observations do not modify selection standing; selected FALSIFIED cannot pass;
- eff: local file reads, hashing, CLI output and exit status only; no publishing, deletion or domain authorization;
- c: UNKNOWN(scope=per-run I/O and catalog-size cost, obligation=measure only if relevant);
- epsilon: UNKNOWN(scope=hash collision resistance, source-path continuity and external semantic uncertainty; no universal byte/rights proof);
- prov: exact Git SourceCut, producing ODPS, Python implementation, Lean abstract model and independent Research receipt;
- unfold: Data catalog/inspection CLI -> producer evidence adapter -> selected consumer read-back; external domain truth and artifact effect are separate.

This is an R2.1 *declared semantic boundary*, not an admission claim of installed universal Data service. Lean proofs cover abstract selection invariants, not Python refinement or filesystem/TOCTOU behavior; native tests and consumer read-back discharge those additional obligations.

### Explicit implementation decisions

- Preserve `inspect_federation.py --require-port PRODUCT_ID PRODUCT_VERSION DISTRIBUTION_URN` and its schema. Do not introduce a second endpoint or result registry.
- Keep the global `inspection.integrityGate` and all falsified/unknown counts visible in scoped mode.
- In selected mode only, decide process exit from selected observations: selected FALSIFIED => 2, any selected UNKNOWN => 3, all selected VERIFIED => 0. Unrelated FALSIFIED remains in the report but is not a selected refusal.
- In global `--require-verified` or ungated discovery, preserve the existing global mismatch exit 2 and global unknown requirements.
- Keep malformed catalog and ambiguous identity error => 2 in all modes.
- Model selected gate safety with the existing Lean kernel, not a new calculus or symbolic state engine.
- Reuse existing test seams and the real Research consumer; no weak-model experiments.
- Avoid copying all Matt/ECC/Superpowers skills. Adopt their engineering mechanisms in existing project workflow: requirements/spec -> blocker DAG -> test-first native implementation -> two-axis diff review -> verified integration.
- No production deletion or migration in R1. Later retirement must prove actual consumers are no longer reachable.

### Implementation task graph (tracer bullets)

| Ticket | Depends on | Concrete change / test seam | Acceptance |
|---|---|---|---|
| D0 baseline/spec | none | `packages/data/planning/CONSUMER_BOUND_DELIVERY_SPEC_R1.md`; exact main SourceCut, external reuse choices | Spec and task graph traceable to current consumers |
| D1 executable scope | D0 | `packages/data/tests/test_odps_projection.py` new negative control; `packages/data/scripts/inspect_federation.py` scoped exit | RED before fix, GREEN after; global gate unchanged; selected mismatch remains rejected |
| D2 formal scope | D1 | `packages/data/formal/DataProduct.lean` named exact-selection invariant; `packages/data/docs/FORMAL_VERIFICATION.md` scoped proof/implementation separation | Lean 4.35 kernel PASS, no sorry, native behavior matching model |
| D3 independent consumer | D1,D2 | `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/test_deliver_research.py` and its pre-existing producer-to-Research boundary | Exact Research ACCEPTED/HOLD, negative source/receipt tests still reject; no unrelated veto |
| D4 production review/integration | D1,D2,D3 | Run `mise run data:verify`, `mise run data:formal:verify`, Research consumer; verify diff; review against spec and owner standards; commit | Real tests PASS; clean commit, no shadow registry |
| D5 later cross-owner adoption | D4 | Reuse exact seam in Capital consumer when an explicit Finance integration requirement is demonstrated; consider provider substitution by contract | Native Finance test and independent domain read-back; no premature universal platform |
| D6 later subtraction | D4,D5 | Retire redundant documentation/old stale consumer-less projections only after repo and actual consumer closure | No current consumer regression; cleaner working tree |

D0-D4 are one independently shippable vertical slice. D5-D6 are subsequent dependent scope, not R1 completion claims.

### Tests and falsifiers

- Known-good target + unrelated UNKNOWN => selected exit 0, global NOT_ESTABLISHED.
- Known-good target + unrelated FALSIFIED => selected exit 0, global FALSIFIED count retained, global inspector exit 2.
- Bad target + unrelated good => selected exit 2.
- Selected missing ID / wrong version / UNKNOWN => exit 3.
- Duplicate selection, malformed checksum/identity => exit 2.
- No selected file verified => global never PASS; no claim about domain use rights.
- Research outcome read-back remains independent of the CLI and refuses modified manifest, forged receipt, unsupported promotion claims.
- CI/readiness evidence: explicit source revision + native tests + Lean proofs + consumer outcome; no claim of installed production rollout without observed installation.

### Native validation / review

1. `python3 -m unittest discover -s packages/data/tests -p 'test_*.py' -v`.
2. `python3 -m unittest discover -s studies/experimental-episodes/experiments/evidence-consumer-pilot-r1 -p 'test_*.py' -v`.
3. `mise run data:verify` (includes data-lifecycle and Research tests).
4. `mise run data:formal:verify` (Lean + bounded CrossHair; SKIP/ENV_BLOCKED remain explicit).
5. `git diff --check`, exact changed-file/source review, owner and spec review. Preserve separate standings: source committed, PR merged, installed, consumed.

### Adoption sources and limitations

- Matt Pocock `to-spec` / `to-tickets` / `implement` / `code-review`: https://github.com/mattpocock/skills (spec synthesis, blocking ticket graph, two-axis review, deep modules).
- ECC `verification-loop`: https://github.com/affaan-m/ECC (owner-native compile/type/lint/tests/diff and target standing, not blanket npm scripts).
- Superpowers `writing-plans` / `test-driven-development` / `using-git-worktrees` / `verification-before-completion`: https://github.com/obra/superpowers (isolated branch, test-first, executable steps).
- Existing canonical Ordivon `.agents/skills/recursive-lego-calculus/SKILL.md`, `compositional-contracts`, `tools/repo/owners.toml`, Data and Research natives are authoritative locally.
- No fresh interviews, mandatory external issue tracker setup, full upstream skill copies, extra oversight Agent or model A/B trial. This spec is consumed by D0-D4 and should be superseded/retired after acceptance and next-slice handoff.

### Done versus not done

D0-D4 complete only when the code change is committed, tests/Lean/consumer pass, and local/source standing is reported honestly. D5/D6 require their own concrete consumers and may be deleted from future scope if those consumers do not exist. No rollout, merge or installed provider success can be inferred from a branch commit.
### R1 execution evidence (2026-11-09)

- D0: SourceCut recorded as `3b43977e682d8c7668f6371ffd998c7821e4312a`; dedicated isolated Runtime Git worktree and branch.
- D1: Added real negative-control CLI test; RED observed (`AssertionError: 2 != 0` for verified selected manifest with unrelated falsified port); after scoped-exit refinement Data tests GREEN. Global falsification still exits 2, selected falsification exits 2, selected UNKNOWN exits 3.
- D2: Lean 4.35 checked `DataProduct.lean`, `DataPublication.lean`, `DataMultiVersion.lean`, with no `sorryAx` in printed axioms. `mise run data:formal:verify` returned 0 including bounded CrossHair; this is not proof of installed filesystem refinements.
- D3: Research consumer independently accepts source-backed `HOLD`; explicitly added verification of good Data input preceding deliberate corrupt analysis/receipt rejection.
- D4: `mise run data:verify` exit 0 (Data 14, Data Lifecycle 29, Research 23); `mise run data:formal:verify` exit 0; scoped Python Ruff lint/format PASS; `git diff --check` PASS. Source review checked that no global gate, malformed catalog handling or true selected falsification was relaxed.
- D5/D6: not executed; no claim of Finance/domain adoption, production install, data deletion or consumer-driven historical retirement.
