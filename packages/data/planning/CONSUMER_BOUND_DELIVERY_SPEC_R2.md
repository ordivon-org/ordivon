# Data R2.1 Consumer Evidence — Formal-First Execution and Cross-Audit Spec

Status: **PRE-IMPLEMENTATION / CROSS-OWNER AUDIT**. Date 2026-11-09.
Branch under revision: \`feat/data-consumer-scoped-evidence-20261109-r1\`, PR [#1970](https://github.com/ordivon-org/ordivon/pull/1970), head \`78b70db5093c52f7df7053531993a8b2af325b50\`.
Fresh protected \`main\` SourceCut at review outset: \`a7d70e83945b7418f41b9636f0803d1544e84355\`; recheck immediately before implementation or publication.
Natural Owner: \`packages/data\`; final factual consumers: actual Research \`deliver_research.py\` and existing Capital shadow consumer. Data cannot own their scientific/financial conclusions.
Cross-agent review: Host \`space:ordivon-capability-task-forum-r1:20261101\` / \`topic:ordivon-data-r21-foundations-skill-crossaudit:20261109\`. Messages are requests/evidence, not proof or delegated authority.

## 1. Outcome, not artifact count

Enable a current, specifically named domain consumer to use the exact qualified data-product output it requires, without unrelated missing/corrupt outputs becoming unjustified blockers, while preventing unsupported source/digest/identity or Research-outcome claims. Preserve the smallest stable interface, strengthen the real model-to-implementation correspondence, and remove rather than add custom machinery that has no independent consumer.

This is NOT: building a universal data service, migrating storage, adding a new LEGO registry, making a model good at research, creating a new agent-runner/approval board, or measuring weak-model performance.

**Contrary evidence / top finding:** R1 PR #1970 changes \`inspect_federation.py --require-port\` but the existing Research consumer \`studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/deliver_research.py\` does not call that CLI. It calls \`project_odps\` and \`inspect_distribution\` directly. Therefore R1 CLI tests establish CLI behavior, not new Research business value. The R1 Lean \`selectedAdmissible (selected : List Verdict)\` proves an abstract aggregator property assuming selection was already correct, not the real exact product/version/port lookup. Previous R1 successes must not be inflated. A successful R2 must expose and address these limits without inventing an unnecessary facade.

## 2. Grounded source and consumer map

- \`packages/data/src/ordivon_data/local_evidence.py\`: bound owner root, product ID, port name, exact declared relative path, SHA-256, regular-file read.
- \`packages/data/src/ordivon_data/odps_projection.py\`: existing bounded Bitol ODPS 1.1 -> DCAT 3 projection, no fabricated file access.
- \`packages/data/src/ordivon_data/catalog.py\`: selected distribution local observation; \`inspect_catalog\` inspects full projection, some unrelated malformed checksum shapes reject whole catalog.
- \`packages/data/scripts/inspect_federation.py\`: separate CLI consumer for human/automation inspection; no traced non-test internal call by Research. In R1, selected-port CLI admission uses only selected verdicts but parses all catalog entries before selection.
- \`studies/experimental-episodes/experiments/evidence-consumer-pilot-r1/deliver_research.py\`: real task-local Research consumer, independent re-open and receipt checks, current outcome \`ACCEPTED/HOLD\` (qualified input, no causal generalization evidence).
- \`domains/capital/scripts/consume_crypto_public_shadow_product_r1.py\`: Capital native independent shadow consumer, not automatic financial execution.
- Existing \`packages/data/formal/{DataProduct,DataPublication,DataMultiVersion}.lean\`: abstract laws, no automatic Python or installed-filesystem refinement.
- Existing \`mise run data:verify\` = Data unit + lifecycle pytest + Research task-local suite. \`mise run data:formal:verify\` = Lean + bounded CrossHair.

## 3. Mature theoretical kernels, exact adaptation

| Kernel | Theory/standard | Relevant obligation | Not proved by using the name |
|---|---|---|---|
| Systems engineering | NASA verification vs validation / ISO 42010 | Separate Data integrity from Research acceptance | A unit test is not domain validation |
| Design by contract / Hoare logic | Meyer, Hoare; assume–guarantee | Precondition exact identifiers, owner root, read scope; guarantee only selected digest observation | Model assumptions do not discharge themselves |
| Local reasoning / noninterference | Separation logic frame reasoning (semantic analogy only) | \`selected(k, C ++ unrelated) = selected(k, C)\` when unrelated entries cannot match k, and the catalog is structurally well-formed | Physical files, duplicate IDs and global parse failures still need concrete evidence |
| 3-valued evidence | Abstract interpretation / partial information | UNKNOWN for absent/unavailable, VERIFIED for exact observed digest match, FALSIFIED for observed mismatch | UNKNOWN is not a third authority granting admission |
| Refinement and compositionality | Lamport TLA+ specification refinement, CMU assume–guarantee | Lean selection algebra -> Python exact-key matching -> source-byte check -> domain receipt | A tautological Lean theorem alone says nothing about Python |
| Immutable identity and provenance | Git SourceCut, content digest, W3C DCAT/PROV, Iceberg snapshots (as analogy) | Distinguish source version, content digest, local mutable locator and consumer read time | Hash of an old pathname does not prove future bytes / access rights |
| Engineering process | Matt to-spec/to-tickets + two-axis review; ECC search-first/contract-first/verification-loop; Superpowers TDD and verification-before-completion | Verify one narrow vertical consumer seam, improve then retire superseded scaffolding | Loading or copying Skills is not engineering acceptance |

Upstream procedure is reference-only, not Skill installation. Source-qualified references: \`mattpocock/skills\`, \`affaan-m/ECC\`, \`obra/superpowers\`; for exact pinned upstream review consult \`docs/architecture/AGENT_OUTCOME_CONTRACT_REFORM_SPEC_R1.md\` and its recorded revisions. If actually installing foreign skill bytes, the separate canonical \`skill-supply-chain-audit\` applies; this programme will not install them.

### Mathematical profile of the target

Let \`Key=(ProductId, Version, PortId)\`. \`Obs=(key, verdict, sourceCut?, declaredDigest?, observedDigest?, provenance?)\`. The immutable identity is the entire key, not a port name or filename.

Let \`matches(C,k)=[o in C | o.key=k]\`. An *exact observation* is defined only when the matched list has **exactly one** element. Missing or multiple matches do not equal success. \`Admit(C,k) = VERIFIED\` iff the unique observed verdict for \`k\` is VERIFIED, after source binding and actual byte read. A matched FALSIFIED rejects selection, a missing/unbound match is UNKNOWN, and duplicated matching identities are structurally ambiguous.

**Frame obligation:** for an extension \`U\` such that \`forall o in U, o.key != k\`, and assuming valid catalog construction/observation, \`Admit(C ++ U, k)=Admit(C,k)\`. This obligation applies to selected-port semantic admission, NOT to unrestricted whole-catalog validation, malicious malformed documents or unqualified external rights.

**Assume/guarantee chain:** \`Producer declares qualified output\` + \`Data checks bytes at read\` + \`Research re-reads bound bytes, receipt and scientific analysis\` => \`Research may make its OWN bounded ACCEPTED/HOLD decision\`. Neither the upstream schema nor Data may directly conclude Research scientific merit.

Temporal safety: \`[] (ConsumerAccepted(d) => ExactConsumerEvidence(d))\`. Conditional progress: only after an authorized, feasible, consumer-bound action with available native executor; no invented global liveness guarantee. Source \`PR_OPEN\` is not \`MERGED\`, \`MERGED\` not \`INSTALLED\`, \`INSTALLED\` not \`CONSUMED\`.

## 4. One R2.1 responsibility and honest proof standing

Responsibility \`L_DataSelectedEvidence\` is a **provisional independent contractual LEGO**, NOT a new runtime or registry.

- I: qualified \`Key\`, owner-declared ODPS and bound source manifest, allowed local root, observation context, source revision.
- O: scoped verdict/typed failure, exact per-port digest observations, provenance; does not contain Research conclusion.
- S: no durable mutable registry; temporary read/projection state, native Git SourceCut and producer-owned artifacts.
- pre: uniquely identified key, qualified producer metadata, explicit read root and valid structural catalog; current authority known to the caller.
- post: \`VERIFIED\` iff selected digest matches actual read bytes under these assumptions; result scoped to observed file/instant. No claim about any unselected port.
- inv: \`UNKNOWN != FALSIFIED\`; absent/duplicate selection is not PASS; unrelated well-formed ports cannot change selected standing; no claimed domain acceptance.
- eff: selected read/check/hash only, no deletion, publication, data rights, finance/Research decision, and no extra service.
- c: \`UNKNOWN[scope=I/O/analysis cost; obligation=measure if workload makes it relevant]\`.
- epsilon: \`UNKNOWN[scope=hash collision and timestamp/path race/rights; obligation=separate physical readback and authority checks]\`.
- prov: \`main@a7d70e\` + \`PR#1970@78b70db\` + exact producer ODPS + Lean artifact + Python native test + Research receipt; refresh at implementation.
- unfold: select exact key -> producer binding -> local evidence -> physical read -> domain consumer readback -> explicit business verdict.

Declaration is not formal admission. Lean kernel passing = \`MODEL_PROVED\` on named theorem only; tests and consumer integration are independently required; installed production remains UNKNOWN.

## 5. Candidate solution and zero-base deletion review

**P0 — keep and strengthen existing library rather than creating a new facade.** Model the real exact key selection and uniqueness in \`DataProduct.lean\`, including noninterference from unrelated observations. Add one focused Python property/negative check linking the selected key used by Data's native existing path to producer identity and Research readback; do not assert that Research uses the CLI. Use the earliest actual consumer seam and the existing test entrypoint.

**P1 — reconcile R1 CLI value honestly.** Treat \`inspect_federation.py --require-port\` as an independent optional inspector consumer, not a Research prerequisite. Preserve it only if it provides a real inspectable decision beyond \`inspect_distribution\` or current user CLI documentation; otherwise explicitly consider retiring speculative selection-only scaffolding. Keep global errors visible. Do not weaken malformed catalog rejection merely to make synthetic tests pass.

**P2 — source/claim hygiene and regression.** Update R1 spec/README/formal map to state exact scope and SourceCut/PR standing; remove duplicated prescription after true delivery. Do not announce R2 proof refines installed physical code without actual file/consumer evidence.

**P3 — defer cross-Owner expansion.** Do NOT build generalized DataRef, DAG Engine, Iceberg, Dagster, global verifier or automated approval service for hypothetical consumers. Finance's already existing independent Capital consumer owns its business readback. Make cross-owner amendments only for an observed unmet contract with current owner involvement.

## 6. Tracer-bullet implementation DAG (not a horizontal checklist)

| ID | Blockers | Concrete source / consumer | First red or falsifier | Exit |
|---|---|---|---|---|
| A0 Source + spec | none | Latest \`main\`, PR #1970, live Data/Research/Capital files; this R2 spec | Existing PR path not actually used by Research | Exact current source and honest gap |
| A1 External theory + Skill qualified | A0 | Canonical local Skills: recursive-lego, compositional-contracts, skill-supply-chain-audit, external-capability-evaluation; official upstream source | Mistaken ODPS 4.x as version-compatible Bitol 1.1; Skill prose as authority | No new registry/provider/install; derivation tied to exact contract |
| A2 Independent cross-audit | A0,A1 | Existing Host Space + source-qualified reviewers; ten-question matrix below | 'LGTM', vague math, no consumer, no real failure; preserve UNKNOWN if no external response | Every candidate assessed; independent findings documented before code |
| A3 Concrete selection/refinement | A2 | Existing \`formal/DataProduct.lean\`, existing \`test_odps_projection.py\` and \`test_deliver_research.py\` | Duplicate/mismatched exact key or unrelated well-formed observation changes selected decision; a proof that accepts an already-selected list only | Lean exact-key frame/uniqueness theorem + real Python/Research matching behavior, without new API |
| A4 Integration/retirement | A3 | Existing Data/Research owner native tasks; R1 PR review/CI, Git | A passing Lean theorem but failing owner consumer; a branch PR called merged; unnecessary docs retained | \`data:verify\`, \`data:formal:verify\`, affected Owner checks, Ruff + diff, GitHub PR, correct standing |
| A5 Contingent domain expansion | A4 + actual new consumer | Capital/Research/Artifact natural interfaces | Generic product registry created for hypothetical future demand | Only if verified cross-domain unmet consumer; otherwise DELETE ticket |

A3 is one vertical proof-to-consumer slice; no weak-model A/B, no one-file-per-LEGO, no extra test runner. A4 may remain blocked by remote CI and does not justify pretending deployment occurred.

## 7. Mandatory ten-question cross-audit for EACH candidate A0–A5

Evidence verdict is \`ACCEPT\`, \`REVISE\`, \`REJECT\` or scoped \`UNKNOWN\`; provide at least one exact path/theorem/test, or say NOT_PROVED. Do not create a new database or checklist engine.

1. **Theory:** Is the representation licensed by the named mature logic/standard, with assumptions and formal versus physical limitations explicit?
2. **Skill:** Does this satisfy Matt's consumer-led spec/deep module/ticket dependency, ECC search-first/contract-first/verification, Superpowers isolated execution/TDD? Or are we ritualistically copying procedures?
3. **Conservatism:** Are we blocking a known-good eligible consumer because of unrelated UNKNOWN/FALSIFIED? Are we asking for unnecessary approvals or verification?
4. **Superficiality:** Is this only a document, tautological proof or test of an unused CLI while real consumer behavior is unchanged?
5. **Representation-first:** Can the responsibility be eliminated/quotiented to an existing interface? Is the natural boundary selected right?
6. **Refinement:** Does each proved property map to a real Python conditional, executable command and consumer assumption; are there omitted identity/TOCTOU/authority cases?
7. **Falsifier:** Which exact mutation or counterexample would disprove the proposal? Was the negative tested at the natural seam?
8. **Subtraction:** Is any new code/contract duplicated with a mature or current-native implementation? What will be retired and when?
9. **Owner/evidence:** Who owns facts and effects? What is observed vs declared, current vs stale, model vs installed/domain truth?
10. **Selection:** Accept/revise/reject/unknown, with next actual implementation or deletion action and bounded stop condition.

### Review of each proposed candidate before A3

| Candidate | Main danger | Review required before implementing |
|---|---|---|
| A0 source/spec | stale PR/head; doc-only value | source/consumer parity, newest main, no duplicate global outcome spec |
| A1 theory/Skills | cargo-culting academic terms and untrusted Skill | exact assumption/side condition, Skill supply-chain handling, no new authority |
| A2 review | simulated independent reviewer; ceremonial ten-question PASS | actual Host author and reply provenance, independently checkable counterexample |
| A3 formal+consumer | tautology/proof not refined; test-only fake target | exact key selection + uniqueness + unrelated frame + consumer readback, red/green when needed |
| A4 integration | test PASS presented as merged/deployed | GitHub PR status, targeted native checks, actual domain outcome |
| A5 extension | speculative platform/over-conservative admission | named Finance/Artifact consumer, natural owner, measured unmet contract |

## 8. Acceptance, evidence and decision gates

- R2 specific **formal acceptance**: Lean kernel checks the *selection* function, rejects duplicate/missing exact keys, and proves a bounded frame lemma about unrelated observations. No \`sorryAx\`; any \`propext\`/\`Quot.sound\` use reported as kernel axioms, not custom admitted theorems.
- **Source refinement**: exact-key Python matches model for named good, bad, missing, duplicate and unrelated cases; owner-native executable tests exercise live source bytes and fail correctly on tampering.
- **Consumer**: existing Research \`deliver()\` uses the actual selected output via library, reopens bytes and verifies its Research receipt, returning \`ACCEPTED/HOLD\`. A deliberately invalid receipt must be rejected even if Data input is VERIFIED. No claim that CLI changes are consumed by Research.
- **External review**: Host Space questions sent before implementation. If peers reply, record concrete findings and repair. If no independent reply arrives, disclose \`PEER_REVIEW_NOT_OBSERVED\`; do not invent reviewers or represent self-audit as independent peer approval. The local audit skill assessment and native validation can still produce real engineering output.
- **Subtraction**: no second contract registry, optional provider upgrade, redundant per-file LEGO document or another audit engine. Any doc created for implementation must have an explicit consumer and retirement condition.
- **Release**: the exact PR/source/integration/installed/consumer statuses must remain distinct; no unsupported merge/deployment claim.

## 9. Implementation stop / rollback / retained UNKNOWN

STOP before code if a candidate duplicates an already current proof/consumer seam, if the required exact-key property is not a new useful obligation, or if cross-owner peer evidence demonstrates a stronger simpler replacement. Repair the spec and use DELETE rather than adding novelty. After code, use \`mise run data:verify\`, \`mise run data:formal:verify\`, relevant Research native tests, \`ruff check\`, \`ruff format --check\`, \`git diff --check\`; investigate failures instead of summarizing them.

Rollback via normal Git PR/revert if a consumer breaks. Keep the original R1 source commit and independent Research receipt unchanged unless current Owner tests justify a compatible revision. UNKNOWN remains for physical race windows, network/external access rights, and broad Domain adoption; none implies that the bounded key-selection proof failed.

## 10. Primary sources / reproducible references

- Ordivon source: \`main@a7d70e83945b\`, Data PR #1970 \`78b70db5093c\`, native Python/Lean code paths above.
- Matt official: https://github.com/mattpocock/skills ; \`to-spec\`, \`to-tickets\`, \`code-review\`.
- ECC official: https://github.com/affaan-m/ECC ; \`search-first\`, \`contract-first\`, \`verification-loop\`.
- Superpowers official: https://github.com/obra/superpowers ; \`test-driven-development\`, \`writing-plans\`, \`verification-before-completion\`.
- NASA systems engineering: https://www.nasa.gov/reference/system-engineering-handbook-appendix/
- CMU assume–guarantee: https://www.cs.cmu.edu/~emc/papers/Conference%20Papers/Compositional%20Reasoning%20in%20Model%20Checking.pdf (theorem/paper reference only; no PDF tool proof)
- Lamport compositional specification: https://www.microsoft.com/en-us/research/publication/implementing-combining-specifications/
- Bitol ODPS 1.1: https://github.com/bitol-io/open-data-product-standard ; NOT numerically continuous with OpenDataProducts.org's independent 4.2 family.
- Apache Iceberg snapshots: https://iceberg.apache.org/spec/ (comparison/reference only, no adoption warranted).
- Existing local method source: \`.agents/skills/{recursive-lego-calculus,compositional-contracts,skill-supply-chain-audit,external-capability-evaluation,method-router}/SKILL.md\`.

Review closure criteria: one independently falsifiable property at the real consumer seam; no extra control plane; positive and negative tests; clean SourceCut; transparent PR status. This SPEC itself does **not** count as implementation success.
