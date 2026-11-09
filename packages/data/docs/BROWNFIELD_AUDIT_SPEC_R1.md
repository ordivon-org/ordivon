# Data Brownfield Architecture and Subtractive Modernization — R1

Status: source-audited and implementation-scoped, not release-approved.
Audit SourceCut: GitHub `main@ef17d6879d12faa61fff3bb762b0d500d73c9113`, observed 2026-11-10 01:45 +08.
Parallel pending change: [#1970](https://github.com/ordivon-org/ordivon/pull/1970) head `299978505c1967c965d2fd7ac6ac6ead80a47a08` OPEN at source freeze; it is NOT part of this mainline audit.
Natural Owner: Data interoperability (not Research, Finance/Capital, Runtime, Artifact or Preservation).
Cross-Agent discussion: existing Host Space `space:ordivon-capability-task-forum-r1:20261101` topic `topic:ordivon-data-r21-foundations-skill-crossaudit:20261109`, review request seq 25882. Space comments are coordination, not source or effect authority.

## Outcome, constraints and non-goals

Replace accumulated editorial/architectural duplication with one clear README for the human entrypoint, one scoped AGENTS.md for Agent rules, and one existing formal evidence map for proof boundaries. Preserve the existing runtime behavior and actual consumer accessibility. No new Data features, tests, consumers, services, product formats, Skills, CLI flags, proofs, registries, pipelines, adapters or speculative capabilities. Existing verification is a regression only. Do not expand R2 feature work from unmerged PR #1970 into this branch.

**Success criterion:** every original executable Data entrypoint and declared producer/consumer route remains available at the same interface; tracked owner instructions and formal owner contract remain navigable; redundant standalone Human, Agent and LEGO inventory documents no longer live under packages/data; no historical evidence lost. Less maintenance text without losing unique current use, effect authority or necessary warnings. No new paper architecture with no reader.

## Adopted mature methods and exact limitations

- **Systems engineering / ISO 42010**: define system of interest as the current Data interoperability package, sources and consumer boundaries first. Do not call a Lean model or a Dataset discovery a deployed lifecycle service.
- **Information hiding / modularity / Ousterhout & Parnas**: keep Python modules split by distinct interface/contract responsibility, not arbitrary file count. A 20-line pure predicate with a live CrossHair/formal consumer is not deletable merely because short.
- **Data Mesh / domain ownership (Dehghani, Fowler)**: domains own meaning, production and consumer value. Data supplies an existing narrow metadata projector/inspector; no central truth.
- **Bitol ODPS 1.1, ODCS, W3C DCAT 3, SPDX, PROV, OpenLineage**: prefer standard producer/schema/lineage representation. Do not confuse numerically larger independent open-data-product specs with a compatible bump.
- **Strangler Fig / incremental replacement**: preserve native consumer equivalence before retiring duplication; here only duplicate *instructions* are targeted, not storage engines or product sources.
- **Lean/Hoare/assume–guarantee/three-way epistemic evidence**: proof of abstract states is not installed PG/Iceberg commit or data rights. UNKNOWN does not become negative evidence or admission.
- **Matt to-spec/to-tickets/code-review**: this spec precedes edits and tickets form a blocker DAG; no new issue tracker, extra Agent launcher or mandatory parallel orchestration.
- **ECC verification-loop**: use the owner's existing `mise`, Ruff, Git diff and existing tests; do not run unrelated pnpm/node checks.
- **Superpowers writing-plans, systematic-debugging, code-review and verification-before-completion**: source inventory before restructuring, inspect root causes, verify actual output, require clean independent review. Do not create new test files because scope expressly freezes tests.
- **Organizational cybernetics**: diagnose duplicated Owner instructions and context cost; never instantiate literal five VSM systems.
- **DELETE → REUSE → COMPOSE → CREATE** with external-capability-evaluation and skill-supply-chain-audit; upstream Skills are reference-only and their prose never acquires execution authority.

## Real repository inventory: every package file (main SourceCut)

The 19 Git-tracked files total 2,434 source/document lines. The `packages/data/planning/` R1/R2 specs are on the *open feature PR*, not main. File disposition includes direct and indirect use, not guesswork.

| File | Responsibility, natural consumer and external comparison | Disposition |
|---|---|---|
| `AGENTS.md` | Closest scoped source-owner instructions; Agent navigation, repo startup and audit entry. | **KEEP / CONSOLIDATE** unique Agent contracts from `docs/AGENT.md`, no multi-page workflow. |
| `README.md` | Human/operator canonical entry; real CLI examples and owner overview. | **KEEP / CONSOLIDATE** unique actionable human guidance and bounded capabilities; remove duplicative prose. |
| `docs/AGENT.md` | Second Agent guide, 115 lines; linked only from package Agent/README, overlaps closer AGENTS + README. | **RETIRE** after current practical instructions move to AGENTS/README. |
| `docs/HUMAN.md` | Second human guide, 128 lines; linked only from package README, repeats user outcome and CLI. | **RETIRE** after unique MVCC/retention and operator cautions are retained in README/formal map. |
| `docs/LEGO_CENSUS.md` | 88-line catalogue duplicating README capability table/formal evidence; sole literal caller is README. | **RETIRE** after retaining semantic distinction: theoretical candidate ≠ installed capability. No new register. |
| `docs/FORMAL_VERIFICATION.md` | 203-line proof/implementation/consumer boundary; **tools/repo/dependency_contracts.toml:232** refers to exact path. | **KEEP / TIGHTEN** only redundant narrative, retain all model/physical distinction and consumer-specific unique facts. Do not silently relocate. |
| `formal/DataProduct.lean` | Pure digest three-valued verdict and product version identity; `mise data:formal:verify` direct consumer. | **KEEP**, native Lean, no new theorem. |
| `formal/DataPublication.lean` | Abstract publish-after-commit and reclaim-after-release safety; `mise`, formal doc direct consumers. | **KEEP** explicitly *abstract only*; no Data publish service claimed. |
| `formal/DataMultiVersion.lean` | Distinct abstract two-generation old-reader preservation/reclamation; `mise`, formal doc, Finance PG readback comparison. | **KEEP** separate counterexample property; no installed GC claimed. |
| `mise.toml` | Owner-native Data/Study + Lean/CrossHair verification tasks. | **KEEP** unaltered; baseline regression runner. |
| `scripts/inspect_federation.py` | Frozen/current DCAT inspection and scope gate; README and actual tests. | **KEEP** without altering public CLI; open PR #1970 touches this code and cannot be silently overwritten. |
| `scripts/project_owned_products.py` | Git-tracked producer ODPS discovery wrapper; README and actual tests. | **KEEP** native Git + producer standard; no second catalog registration. |
| `src/ordivon_data/__init__.py` | Python package namespace, import path for task-local consumer. | **KEEP**. |
| `src/ordivon_data/catalog.py` | Bounded DCAT inspector and current local SHA; direct Research and CLI consumers. | **KEEP**, not interchangeable with RDF universal parser or Artifact verifier. |
| `src/ordivon_data/local_evidence.py` | Producer-declared path/digest binding for Research, source-open SHA. | **KEEP**; main version is name-only pending #1970. No expansion this scope. |
| `src/ordivon_data/odps_projection.py` | Deterministic Bitol v1.1→DCAT3 view; Research, CLI and repo dependency consumers. | **KEEP** thin conversion seam; avoid introducing third-party catalog platform to replace ~181 LOC absent actual benefit. |
| `src/ordivon_data/verification.py` | 20-line pure digest three-verdict predicate, input to CrossHair and catalog. | **KEEP** because formal bounded verifier is actual owner task; length is not redundancy evidence. |
| `tests/test_catalog.py` | Existing inspector evidence/regression incl historical catalogue. | **KEEP** unchanged; no new tests this scope. |
| `tests/test_odps_projection.py` | Existing real producer/metadata binding regression, source routes and CLI. | **KEEP** unchanged; no new tests this scope. |

### Adjacent evidence and dependencies reviewed (not owned by Data)

- `studies/data-lifecycle/`: six serial `data-lifecycle-census-r1..r6.json` snapshots, six tests, and 38 evidence files (data-products, temporal, preservation, historical federation). Old-to-new census refs form a versioned provenance chain; `r1` is in Workstation retirement policy, `r2` through `r4` have tests; `r6` is referenced in capability catalogue. **KEEP** existing historic records in this change; no age-based destructive deletion or schema rewrite.
- `studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/deliver_research.py`: actual Python library caller plus independent Research receipt; no feature edits, no new consumer, preserve exact readback.
- `domains/capital/data-products/crypto-public-shadow-r2/`: live producer ODPS/ODCS, Data projection binding. `domains/capital/scripts/consume_crypto_public_shadow_product_r1.py` is Capital-owned independent result; no change.
- `tools/repo/dependency_contracts.toml` and `tools/repo/test_convergence_plan.py`: direct owner boundary and affected-consumer selection; do not replace current contracts.
- `capabilities/artifact/`, `tools/formal/`, `platform/security/`: natural owners of bytes, Lean kernels and privileges; code is outside this disposal scope.
- Frozen evidence `studies/data-lifecycle/evidence/data-products-r2/federated-catalog.dcat.jsonld` has historical malformed file authority; preserve immutable study rather than silently rewriting facts.

## Execution dependency DAG (source-first, no additional test development)

| Step | Depends | Allowed work | Acceptance |
|---|---|---|---|
| S0 Source inventory | none | Freeze main, open PR, every package file and literal/actual consumers; compare mature standards/Skills | 19/19 file decisions; counts and currentness in this spec |
| S1 Cross-Agent critique | S0 | Existing Host Space request seq25882; read old peer source reviews and new current objections; correct plan where disproved | Factually grounded issues or UNKNOWN; Space is not a blocking approval service |
| S2 Canonical entrypoints | S0,S1 | Consolidate unique human/Agent/LEGO editorial information into README + AGENTS + existing formal map; delete exactly three duplicate docs | No surviving reference to removed docs; unique source/currentness warnings remain findable |
| S3 Existing source review | S0,S1 | Inspect all Python/Lean/CLI/tests and direct study/source callers; **no** feature, test, consumer, proof, or public API extension. Only repair a proven pre-existing defect if directly necessary for S2 | No accidental production behavior change; repo remains source-readable |
| S4 Regression | S2,S3 | `mise run data:verify`, `mise run data:formal:verify`, repository documentation/dependency checks where available, Ruff/diff | Existing suites PASS; no new test files; exact failing status explicit |
| S5 Review and Git delivery | S4 | Compare diff to plan, inspect TODO/backlinks, independent objections, commit in isolated branch and PR if qualified | Clean commit, original source/installed separation, no claim of merge/rollout |
| S6 Collision reconciliation | S5 + actual PR #1970 outcome | Keep changes isolated; coordinate with PR owner to port doc deletions/references if overlap, never clobber unmerged work | Correct merge-base and zero lost unique consumer paths |

### Pre-edit falsifiers and scope limits

- False deletion: removing a doc breaks a current non-doc dependency contract, import or canonical Agent navigation; stop that deletion until moved. `FORMAL_VERIFICATION.md` specifically has a real non-document contract ref.
- False modernization: introducing a second loader, registry, lifecycle service, verifier, TLA model or data platform without a consumer violates S3; reject.
- False proof: preserving `DataPublication.lean` does not claim Artifact leases or PG atomicity.
- False progress: changing README prose without deleting redundant docs is insufficient; S2 must materially reduce carriers.
- False regression: accepting local tests without Git status/source diff/current PR record is insufficient; S4 and S5 disjoint.
- External Skill provenance is reference-only; no foreign executable/Skill downloaded, installed, or granted authority.

### Source-level review and rollback

Baseline runs under source-cut isolated Runtime Workspace, not on shared main checkout. Delete only three named owner-doc files, and update every real referrer in the same change. Keep unmerged PR #1970 separate; if its docs overlap, resolve by ordinary Git merge/rebase with consumers on the fresh new base, not by silently dropping the feature PR. Roll back via Git revert, not through deletion of history. After S5, this Spec is a bounded audit record rather than permanent execution policy; AGENTS/README remain canonical, and the spec may be archived or retired when superseded by complete source closure.

## Immediate source references

- Bitol ODPS 1.1 docs: https://github.com/bitol-io/open-data-product-standard/blob/main/docs/product-information.md
- W3C DCAT 3: https://www.w3.org/TR/vocab-dcat-3/
- Data mesh: https://martinfowler.com/articles/data-mesh-principles.html
- Fowler Strangler modernization: https://martinfowler.com/articles/2024-strangler-fig-rewrite.html
- Matt Skills upstream: https://github.com/mattpocock/skills
- ECC Verification Loop: https://github.com/affaan-m/ECC/blob/main/skills/verification-loop/SKILL.md
- Superpowers: https://github.com/obra/superpowers
- Local Skills: `.agents/skills/{recursive-lego-calculus,compositional-contracts,systems-engineering,method-router,external-capability-evaluation,skill-supply-chain-audit,organizational-cybernetics}/SKILL.md`.

## Verified S2–S4 result and bounded S5 decision (2026-11-10)

**Conservation law for this slice:** for each tracked file under
`packages/data/{src,scripts,formal,tests}/` and `packages/data/mise.toml`,
the Git blob of the after-source equals the frozen main SourceCut's blob.
This preserves the code artifacts, native entrypoints and test inputs
byte-for-byte; it is stronger than a test-only regression claim, but says
nothing about the usability of changed human/Agent documentation.

Navigation conservation is checked separately by searching all live repo
Markdown links pointing at retired docs (no active matches) and keeping
`README.md` as human entry, `AGENTS.md` as nearest Agent instructions,
`FORMAL_VERIFICATION.md` at the **unchanged** exact
`tools/repo/dependency_contracts.toml` contract path. Historical references
*inside this audit document* explain removed files, and are not navigation
links. Theoretical models remain distinct from physical installed publishers.

- **S2**: three duplicate owner docs retired, exact active links repaired,
  unique usage/proof/retention boundaries moved to the canonical sources.
  No source, test, consumer, CLI, Lean or native task changed.
- **S3**: all 19 original package files and their adjacent real owners
  individually evaluated against Bitol ODPS, DCAT3, domain ownership and
  the native Git/Lean/Python interface. Code preserved where there is an
  actual independent consumer; no speculative code refactor.
- **S4**: `mise run data:verify` PASS (14 Data, 29 Data Lifecycle,
  23 Research native tests). `mise run data:formal:verify` PASS
  (DataProduct, DataPublication, DataMultiVersion Lean + bounded CrossHair).
  `python3 tools/repo/check_architecture_docs.py` PASS. Targeted repository
  architecture/convergence suite `PYTHONPATH="$PWD" /usr/bin/pytest -q
  tools/repo/test_architecture_docs.py tools/repo/test_convergence_plan.py
  -k 'architecture_docs or DataProducerToConsumerImpact'` PASS
  (200 passed, 60 deselected, 3 subtests). An initial shell-style
  `/usr/bin/pytest` run without project-root Python path FAILED
  with missing `tools` import; rerun with canonical root resolved that
  invocation problem. `git diff --check` PASS.
- **S1/S5 independent review status**: Host Space request #25882
  and cleanup-specific handoff #25912 committed; no independent peer
  reply on this exact document subtraction observed at the last read.
  A social request is not peer approval.
- **S6**: unmerged #1970 separately changes Data README/AGENTS/formal docs.
  A future merge/rebase must reconcile their unique consumer obligations
  rather than restoring three retired docs by accident. Until actual
  GitHub integration, this source-level cleanup is not merged, installed,
  or accepted by an Agent consumer; do not promote it to those standings.
