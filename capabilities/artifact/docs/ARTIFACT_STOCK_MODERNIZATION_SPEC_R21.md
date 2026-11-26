# Artifact R2.1 — Whole-Stock Modernization, Subtraction and Repair

**SourceCut:** GitHub main ef17d6879d12faa61fff3bb762b0d500d73c9113 (2026-11-10 +08).
**Scope:** capabilities/artifact/ and its exact current parent/consumer links. All current 425 tracked files in this SourceCut are inventoried in ARTIFACT_STOCK_BASELINE_LEDGER_20261110.tsv.
**Owner:** Artifact. Git/Runtime/Workstation/Network/Media/Game/Research/Finance retain natural authority for their own source, effects and domain quality.
**Mode:** Brownfield stock audit and subtraction. No new user-facing features, tests, consumer workflows, registries, schedulers, adapter layers, or mandatory governance gates.
**Existing concurrent work:** PR #1974 (bounded Standing convergence, still OPEN at audit start). Do not modify its verification modules or rewrite competing plans during this stock cleanup.

## 1. Problem statement / observable desired outcome

Artifact has accumulated 14 substantial top-level areas, format-specific verifier implementations, two historical verification backbones, a large delivery/provider hub, OCI packaging, trust, registry/transport tools, installed Temporal orchestration, 28 documentation carriers, and test-only prototype models. File presence and historical qualifications obscure which responsibilities are currently owned and consumed. Previous changes repeatedly added safeguards, Plans and pressure models without subtracting obsolete carriers.

Goal: one coherent owner-native inventory, smaller actual source tree, accurate CURRENT vs HISTORICAL navigation, source-owning rather than duplicated transport decisions, and no change to existing native format outputs or deployed workers.

The objective is a maintainable, substitutable Artifact system; a smaller line count alone is not the objective. Do not create a new LEGO registry, automatic audit framework, universal gate or artificial cross-format ontology.

## 2. Actual audited topology

Original root files: 425 = artifact-delivery 180; tests 72; scripts 43; docs 28; artifact_capabilities 22; artifact_verifiers 21; artifact_core 11; planning 10; artifact_verification 9; artifact_operations 8; artifact_trust 7; root 7; artifact_evidence 3; config 2; systemd 2. Among these, Python 195, JSON 174, Markdown 30, other 26. All 195 Python syntax trees and 174 JSON files parsed on current main. This proves parseability, NOT semantic correctness or code style. Current native Owner baseline: mise run verify = 566 passed, 3 skipped, 42 deselected, 115 subtests, Ruff and existing finite models PASS.

Full per-file baseline: ledger has exact original path, SHA-256, bytes, line count, content-parse summary, directory role, tracked-basename mention count and an explicit tentative disposition. The basename-reference count is NOT a complete consumer graph; imports, service configs, CLI invocation, runtime dynamic clients and externally held source links must be checked separately. This ledger is frozen audit evidence, NOT a new living inventory authority.

## 3. The responsibility map (not 14 new LEGOs)

- Subject and Profile commitments: artifact_core, canonical Profile schemas/bindings.
- Native output construction: artifact_capabilities and format-native mature tools.
- Operation materialization: artifact_operations and bounded direct Python provider.
- Evidence observation and scoped validation: artifact_verifiers, artifact_verification, artifact_evidence.
- Optional trust qualification: artifact_trust, in-toto/SLSA/Cosign/OPA wrappers.
- Format-specific CLI and optional adapter carriers: scripts; exact artifact-delivery schemas, locks and fixtures.
- Actual persistent execution/recovery: Runtime and installed Temporal owner. Artifact Temporal worker is a real service with active process; do not retire or relocate under this cleanup.
- Actual OCI distribution: installed Zot and selected ORAS/OCI tooling. Registry/Distribution is NOT a generic Artifact standing responsibility.
- Cloudflare R2 transport: Network/Provider-owned external effect. The historical custom R2 mailbox implementation is specifically DO_NOT_PROMOTE in planning/lego-plan-r2.json; no production source consumer/service was found in the audited local state.
- Actual end-use quality: Game, Media, Publication, Research/Finance and other domain consumers. No new consumer path is within scope.

The existing README still declares a registry/ directory that does not exist. This is inaccurate CURRENT navigation and must be corrected.

## 4. Adopt mature theory and projects, with explicit limits

| Lens | Real diagnostic question | Adopted rule | Non-claim |
| --- | --- | --- | --- |
| Parnas information hiding (CACM 1972) | What requirement change forces simultaneous edits? | Own volatility behind deep existing format or qualification modules; no line-count-driven splits | module names are not architecture proofs |
| ISO/IEC/IEEE 42010 and INCOSE | Which actor or deployment owns each effect and observation? | Separate Artifact content standing from Runtime execution, Network transfer and Domain acceptance | a diagram does not prove execution |
| MIT Design Structure Matrix / CMU SEI | Which actual Python/import/config edge creates cycles and hubs? | Read AST imports and source-specific consumer edges; propose only owner-valid coupling changes | lexical co-occurrence is not a dependency |
| Cousot abstract interpretation + A/G refinement | Does a local PASS or a historical snapshot exceed its evidence? | Keep provenance, three-valued incompleteness and explicit proof assumptions, reuse native profile checkers | finite abstract checks do not prove physical tools |
| Goldratt TOC + Lean waste reduction | Is the bottleneck a duplicate Owner, unused code or an absent consumer? | Retire unconsumed custom code and conflicting historical guidance before building anything | no arbitrary efficiency metric or WIP threshold |
| Nix derivations + BuildKit LLB/Bazel | Are source, input closure, dependent outputs and execution effects clear? | Borrow exact input/graph/closure semantics, do not build another CAS or build scheduler | source hash alone is not hermetic execution |
| OCI Image/Distribution, ORAS, Zot | Do we need homegrown object packaging and registry mechanics? | Keep standard OCI artifacts and actual installed registry, restrict custom code to justified thin adapters | installed registry does not prove publication |
| in-toto/SLSA/Sigstore/OPA | Is native evidence authenticated and scoped? | Trust remains an optional existing independent overlay | a signature does not imply domain correctness |
| Cloudflare official R2 S3 + rclone | Does bespoke 520-line SigV4/temporary-credential code have a current consumer? | Retire unconsumed custom mailbox rather than transfer ownership of unused code; re-admit mature provider on actual demand | local rclone presence is not configured remote access; temporary credentials and SigV4 are not proved equivalent |

Primary sources: https://doi.org/10.1145/361598.361623 ;
https://www.sei.cmu.edu/library/optimization-of-software-release-planning-considering-architectural-dependencies-cost-and-value/ ;
https://docs.docker.com/build/buildkit ;
https://releases.nixos.org/nix/nix-2.29.3/manual/store/derivation/index.html ;
https://oras.land/docs/ ;
https://developers.cloudflare.com/r2/examples/rclone/ .

## 5. Engineering methods from installed Skills (selection, not bulk installation)

- Ordivon recursive-lego-calculus and compositional-contracts: delete, reuse, compose; explicit assumptions/guarantees and current owner, 11 typed coordinates only for independently declared responsibilities, not per file. UNKNOWN does not imply FALSE; classification does not establish proof.
- Ordivon systems-engineering and design-structure-matrix: first source owner/boundary and actual directed dependencies; then select a minimally invasive change.
- Ordivon skill-supply-chain-audit and external-capability-evaluation: third-party Skill/source is untrusted guidance. Compare one actual incumbent/consumer contract; never import foreign execution authority.
- Matt to-spec and to-tickets: source-backed problem statement, acceptance, dependency DAG and review of Spec vs Standards. This is a cleanup: existing seams and no new test suite.
- Superpowers worktree, writing-plans, executing-plans, verification-before-completion: isolate changes, inspect actual diff, run existing native checks, do not infer success from narration.
- ECC: reference only for change-impact, contract-first and peer review; do NOT install foreign hook bundles, prompt router, or duplicate agent roles.

## 6. Full R2.1 contract for one actual responsibility: Artifact Stock Convergence

ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)

- I: immutable Git SourceCut; tracked files and SHA ledger; current imports/CLI/binding/systemd facts; current consumer evidence; approved deletion scope.
- O: source tree minus obsolete carriers; clarified current navigation; verified unaffected native interfaces; release-ready ordinary Git diff.
- S: Git tracked state; no new persistent runtime state or product database.
- pre: the named SourceCut is available, every candidate has a bounded static/dynamic consumer investigation, and actual active services are excluded.
- post: deleted source no longer appears as an actionable CURRENT interface; no broken tracked references introduced; existing active owner verification remains green.
- inv: no changes to installed Temporal/Zot services; no new semantic evaluator or Schema; no weakened Profile assertions; no new functionality/tests/consumer paths; preserved historical Git provenance; no local PASS promoted to DOMAIN_ACCEPTED.
- eff: Git source and documentation edits, GitHub PR; no actual credential, provider, remote bucket or production service mutations.
- c: metadata/AST audit O(total tracked bytes + observed edges); exact native verification execution cost bounded by actual jobs, not invented a constant.
- epsilon: static consumer closure completeness UNKNOWN; candidate-deletion certainty explicitly limited to inspected current tracked sources, services and processes.
- prov: Git SHA, per-file hashes, actual systemctl/ps observations, repo tests, existing Host Space collaboration messages, PR review and native CI output.
- unfold: L0 owner/goal/decision; L1 module responsibility; L2 individual ledger row + observed references; L3 source and exact test/exec evidence.

Delete admissibility is not a per-file proof ceremony: when a class of files is generated from one obsolete responsibility, retire that group as a whole after checking real common entrypoints and unique consumers. Git history preserves the removed source.

## 7. Candidate decisions from exact baseline

**KEEP ACTIVE:** all current format builders/verifiers, exact Profile schemas and bindings, live Temporal adapter/config, OCI/Zot-carrier code, actual Toolchain Doctor, Trust, readback, Game/Media/Publication-qualified scripts and existing tests. Keep archive assets required by exact SHA and licensing; do not rewrite historical receipt hashes.

**REVIEW / SHRINK LATER, NOT FIRST BATCH:** direct_python.py (606 lines; several operation responsibilities), artifact_oci_package.py (637), artifact_delivery_toolchain_doctor.py (641), artifact_r2-related dated planning and additional experiment prototypes. Only move/split if a real caller-facing responsibility and current stable API justify that change. Do not reimplement Bazel/Nix/OCI.

**RETIRE, historic standalone docs with no tracked filename inbound links (11):** CAD admission boundary; Aseprite, Tiled, EDA, Internet Message, ELF, SVG, WARC standalone family reports; two R2 S1 pressure documents; the unlinked original v1 authoring/orchestration study. Existing native script/Schema/Skill and separate cross-family docs are the current technical contract. Preserve source bytes in Git history; avoid pretending zero lexical links proves no historical human reader.

**RETIRE, custom R2 mailbox source set (4):** mailbox Python script, old operator config, transport-intent schema and mailbox-only test. Exact tracked refs include historical READMEs, dated R2 plan (X01 DO_NOT_PROMOTE), and self-test. No current artifact operation provider uses the mailbox. Runtime observed Temporal/Zot active but no mailbox worker; rclone installed. Do not access credentials, issue signed URLs, or touch R2 content. Future actual transport demand belongs to Network/Provider via mature S3/rclone/ORAS.

**RETIRE, test-only evidence-observation prototype pair (2):** planning/prototypes/evidence_observation_r1.py and tests/test_artifact_evidence_observation_lossless_r1.py; this pair asserts the experimental wrapper's own representation, while production native verifier/consumer tests reside elsewhere. Remove as a whole, not as a partial import break. Keep dated R2 plan JSON as explicitly historical rather than giving it CURRENT authority.

**REPAIR:** README navigation: remove fictional registry/ directory, describe the retired historic carriers and route current work to existing source/bindings and live owner systems. Keep ARCHIVE references distinct from CURRENT, and leave exact source/consumer provenance intact.

## 8. Complete dependency-bound execution plan

| Ticket | Blocked by | Work (no new features/tests/consumers) | Evidence / exit |
| --- | --- | --- | --- |
| S0 Source and theory audit | none | exact main, all 425 file hash/structure/role ledger, current service and external methods | parsed 195 Python/174 JSON, ledger 425 rows, native baseline recorded |
| S1 Peer challenge | S0 | Host Space independent argument about R2 mailbox, historical docs and test-only prototype, specific contrary caller/installed evidence | record actual replies or explicit unresolved external uncertainty, not invented approvals |
| S2 Historical document retirement | S0,S1 | delete 11 unlinked obsolete reports in one class operation | zero remaining tracked broken path references; Git history intact |
| S3 Experimental prototype retirement | S0,S1 | remove unused evidence_observation prototype with self-test only | no other imports; native verification still green |
| S4 R2 transport subtraction | S0,S1 | retire 4-file dead-end custom R2 mailbox, preserve active Temporal/Zot | no active native consumer found; scripts/config/schema/test gone; unchanged provider state |
| S5 Canonical CURRENT navigation | S2,S3,S4 | correct README and distinguish historical plans from active source | active paths resolve; no stale registry/runtime claim |
| S6 Native verified cleanup | S5 | existing mise run verify and repo checks; file diff/branch hygiene; no tests added | regression outcomes relative to original 566 passed/3 skipped/42 deselected |
| S7 Source-only independent review | S6 | Matt Standards and Spec axes + R2.1 claims; peer Space counterexamples | note all concrete disagreement; do not self-claim second opinion |
| S8 Protected delivery | S7 | commit/push/PR and external merge checks; no production effects | source commit and CI state independently reported, no invented merge or deployment |

## 9. Peer-review adversarial questions (for every actual proposed deletion class)

1. Is the named problem the underlying owner/consumer mismatch, rather than a surface text smell?
2. Does the decision satisfy Parnas/DSM/A-G assumptions and R2.1 non-claims, or infer too much from static edges?
3. Does Matt Spec-vs-Standards review find a real public contract changed?
4. Has ECC-style brownfield change-impact review inspected actual producers, readers, service units, JSON and current tool versions?
5. Is Superpowers planning/verification real (exact SourceCut, native command, output), not procedural theater?
6. Is retaining the code just undue conservatism, or deleting it ungrounded recklessness? Name an actual consumer to justify either claim.
7. Could a mature existing tool replace the entire unwanted responsibility without importing an unnecessary framework?
8. Would this introduce a new functionality, test, consumer path, registry, service or second source of authority? Reject if yes.

## 10. Acceptance and explicit limits

Success is a smaller genuinely operable production source tree with unconsumed historical material removed, no change to qualified native outputs and no new architecture layer; the exact counted Git deletions, current paths and existing Owner-native test results constitute delivery evidence. This is NOT proof that every unseen external user/process is absent. Unresolved external consumer hypotheses remain named UNKNOWN, not fabricated blocked work; if future evidence shows a live consumer, restore from Git and migrate deliberately.

Space discussion is collaboration only. Git/Runtime/Workstation and natural Domain owners remain authoritative. Any independent review response must cite SourceCut and exact consumer/source fact. No weak-model experiments, no new test suite or consumer workflows.

## Execution reality (not inferred from the plan)

Source-only subtraction performed in a dedicated Artifact Git worktree: 17 tracked files retired as coherent historical/unconsumed classes. Repository state and installed Temporal/Zot were not changed. The baseline Owner check was 566 passed, 3 skipped, 42 deselected, 115 subtests. Post-change acceptance requires fresh mise run verify and the original repo checks. Remaining active high-coupling code is kept and marked REVIEW, not declared fully modernized.

### Verified stock reduction (same worktree)

- Original SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113, 425 tracked Artifact files.
- Changed: 17 existing tracked files deleted in coherent obsolete/dead-end classes; original paths remain reconstructible with Git show on SourceCut. The file ledger is frozen before-state, not a current file count.
- Native pre-change Artifact verify: 566 passed, 3 skipped, 42 deselected, 115 subtests. Post-change current source native verify: **540 passed, 3 skipped, 36 deselected, 115 subtests, exit 0**. The decrease is expected from retiring two obsolete test modules and their integration cases; no new tests created or retained test failures.
- Existing repository guards on changed source: check_owner_boundaries.py PASS (2315 active files, 31 seams, 38 references), check_structure_r2.py PASS, check_architecture_docs.py PASS; git diff --cached --check PASS.
- Running Temporal worker and Zot service were observed active and left unchanged. No new package, CLI, verifier, consumer or deployment was added. No remote Cloudflare API/mutation or original Artifact data accessed.
- Independent peer finding in Host Space seq25909 is included: rclone generic S3 work is not a demonstrated replacement for the removed unconsumed temporary-credential or SigV4 capability.
- This clean change is still source-only until an ordinary GitHub PR is accepted; never call a native suite PASS equivalent to installed/deployed or domain-consumer acceptance.
