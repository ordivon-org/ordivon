# Harness Brownfield Architecture & Subtractive Reform — Execution Spec R1

Status: **source-grounded, in execution; no blanket refactor accepted**.
SourceCut: `ordivon-org/ordivon@ef17d6879d12faa61fff3bb762b0d500d73c9113` (2026-11-10 Asia/Shanghai); rerun source/PR comparison before integration.
Natural Owner: `services/harness`. This is **not** a second Agent governance spec; the existing `HARNESS_AGENT_TASK_REFINEMENT_SPEC_R1.md` and its PR #1991 cover task-to-run/source refinement. This spec is **only** for source-tree inventory, inherited-code architecture, subtraction and in-place maintenance.
Exact file register: [HARNESS_FILE_CENSUS_SOURCECUT_20261110.csv](HARNESS_FILE_CENSUS_SOURCECUT_20261110.csv). **731** tracked files read and hashed, including 62 `src` Python files. A machine-read file register is not 731 completed semantic reviews.

## 1. Decision, goal and hard exclusions

The aim is a smaller, more understandable, replaceable Harness with the **same already admitted behavior**, lower maintenance and fewer competing sources of truth, not a larger Agent platform. Freeze **new features, added tests, new consumer wiring, weak-model experiments, new Agent/registry/evaluator/scheduler and speculative compatibility layers**. Existing native tests, formal checks, docs and release/wheel checks may be *run*, not multiplied.

Owner boundary:
- Harness: bounded Agent Run cognition/loop/continuity, Provider/Tool intent, private Run journal, source-bound receipts and candidate result.
- Runtime: Job/Attempt, physical process/tool effects and Workspace lifetime; Gateway: routing; Host: collaboration/Work; domain caller: task acceptance.
- PostgreSQL: current Harness Run writer. A successful Provider call, Runtime Job or test is not a domain-success statement.
- Treat source code, tests, release-wheel, deployed process and final consumer as **distinct evidence layers**, not grades inherited automatically.

Never transform this audit into one file per LEGO. Formally declared responsibilities may use the complete typed Recursive LEGO R2.1 tuple `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`, with `UNKNOWN(reason,scope,obligation)` when evidence is missing. A physical file, class, test or PR is not thereby a LEGO.

## 2. Better representation: responsibility-and-authority graph

Represent the maintenance subject as a **typed, source-bound graph of existing obligations**, not a flat directory cleanup:
- `V`: stable behavioral responsibilities and versioned files/packages (different node kinds).
- `E_call`: real import, invoke, entrypoint, configured or dynamic call.
- `E_state`: which implementation writes which durable state, and under whose authority.
- `E_effect`: external Provider/Runtime and recovery/replay seams.
- `E_evidence`: verifier/CI/doc/binary/readback links, scoped by exact revision.
- `E_history`: research, preregistrations and old evidence that are uniquely historical, not today's production truth.

Do not infer a live consumer from a mere test that only exercises retired code, or infer no consumer from zero AST imports / zero literal grep matches. Question a source item by its final observed behavior, unique historical contents, executable/imported packaging and external input contract. An unknown on one deletion does **not** stop independent safe maintenance elsewhere.

**Classification**: KEEP (needed as-is); SIMPLIFY (local complexity); COMPOSE/REUSE (existing native implementation); RETIRE (no surviving current consumer, unique value recoverable in Git/Artifact); WAIT (specific active PR/consumer); UNKNOWN (a named missing witness). Each decision records source path and explicit falsifier.

## 3. Mature foundations — adopt the mechanism, not new ceremony

| Source theory / precedent | Decision-changing idea | Current Harness application / what not to do |
| --- | --- | --- |
| Parnas 1972, information hiding | Modules hide changeable decisions behind stable contracts | Group by invariants/authority/change-coupling; **never** split just because `loop.py` is long |
| Jackson/Alloy, DSM, strongly connected components | Distinguish dependency from textual similarity, identify cycles and misplaced boundaries | Extract observed `E_call` and affected SourceCut; don't treat graph clustering as semantic proof |
| Hoare/weakest precondition, assume–guarantee, refinement | Require exact assumptions and observable guarantees, under the same interface/traces | API replacement isn't proved by method names, model or SQLite/PG test counts |
| TLA+/TLC + concrete witness | Bounded safety model does not prove source↔model simulation or liveness without fairness | Keep existing ProviderClaim model and source checks, not a new prover or universal formal gate |
| Lean / Theory of Constraints / Google SRE toil elimination | Eliminate the actual maintenance bottleneck and repeated causes of toil | Retire duplicate writers/abandoned experiments once their actual obligations are discharged |
| STPA, FMEA/FTA, ATAM | Model unsafe interactions and concrete design trade-offs | Evaluate false retention, data loss, duplicate effect, recovery and maintenance cost with real negative examples |
| OpenHands SDK / Pydantic AI / Temporal | Separate agent behavior from execution/workspaces, persistence from durable execution | No second Runtime/Host/Workflow engine or overlapping durability journal |
| Matt `to-spec`, `to-tickets`, `code-review` | One inspectable spec; only real blockers; review **Spec** and **Standards** separately | No one-file-per-ticket, no default compulsory subagents or approvals |
| ECC engineering loop + Superpowers debugging/verify | Research-first, isolate one root cause, use fresh native verification before claims | Reuse `mise run queue`, do not install all upstream hooks/agents or add tests against user instruction |

Official/upstream anchors:
- Parnas, CACM: https://doi.org/10.1145/361598.361623
- Martin Fowler, legacy modernization: https://martinfowler.com/bliki/StranglerFigApplication.html
- Matt: https://github.com/mattpocock/skills ; ECC: https://github.com/affaan-m/ECC ; Superpowers: https://github.com/obra/superpowers
- OpenHands: https://github.com/OpenHands/software-agent-sdk
- Pydantic AI: https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/
- Google SRE: https://sre.google/workbook/eliminating-toil/
- Ordivon native methods: `.agents/skills/{recursive-lego-calculus,compositional-contracts,systems-engineering,design-structure-matrix,minimum-sufficient-representation,organizational-cybernetics,stpa,fmea-fta,feedback-grounded-repair,skill-supply-chain-audit}`.

## 4. Complete file-family inventory and observed structural hotspots

The attached CSV gives every path, byte count, line count, SHA-256 and **static source-import examples** (not complete runtime reachability); its `initial_status` is a queue for **further** semantic review, not a pass/fail verdict.

| Tracked group | Files | Initial audit questions |
| --- | ---: | --- |
| `src` | 62 | Authority, state/write boundary, Provider/Runtime coupling, duplicate concepts |
| `tests` | 182 | Which actual current behavior is covered vs fixture-only historical carryover? |
| `scripts` | 87 | Which script is actually installed, invoked by `mise`, CI, node or live workflow? |
| `evidence` | 139 | Immutable provenance, currentness vs historical status, indexed readset |
| `research` | 97 | Unique evidence vs obsolete experimental workflow; move/retire only by consumer |
| `evals` | 48 | Retire nonconsumed weak-model campaigns; preserve unique historical results in Git |
| `docs` | 42 | Current authority vs rationale/decision archive; merge and remove duplicate navigation |
| `formal` | 13 | Existing model assumptions, exact code bridge, no false general proof |
| `systemd` | 14 | Installed unit/liveness evidence rather than source-only existence |
| `config` | 11 | Exact operator/corpus consumer; large JSON is not automatically garbage |
| `fixtures` | 10 | Only retained when referenced by an actual test/tool or unrecoverable evidence |
| `.github` | 6 | Native CI/automation reachability; overlap with root repo workflows |
| `planning` | 4 | Historical vs actionable; avoid another global execution truth |
| All other root/support paths | 16 | Package/lock/schema/containers/canonical guide and scaffolding |
| **Total** | **731** | Counts as at SourceCut; new spec/register themselves are outside this frozen set |

### Source responsibilities to examine as coherent clusters

1. **Public admission and packaging**: `api.py`, `agent_run.py`, `cli.py`, `independent_cli.py`, `core_contracts.py`, `store.py`, `runtime_port.py`.
2. **Cognition, state and continuity**: `ordivon/loop.py` (2366 lines), `ordivon/run_continuity.py` (3186), `ordivon/run_recovery.py`, `ordivon/continuity_guards.py`, `ordivon/continuity_records.py`, `working_view.py`, `run_state.py`.
3. **Persistence**: `postgres_store.py` (758), `sqlite_store.py` (1065), `object_store.py`, `ordivon/run_store_port.py`, `store_errors.py`. Preserve single PG production writer.
4. **Effects**: `ordivon/runtime_bridge.py` (1492), `ordivon/runtime_lowering.py`, `plugin_gateway_effect.py`, `gateway_execution_port.py`, `ordivon/agent_bridge.py`, `tool_program*.py`.
5. **Provider/external adapters**: `ordivon/deepseek.py` (1154), `ordivon/deepseek_protocol.py`, `mcp_http_client.py`, `agent_plugin.py`, `plugin_mcp.py`, `dap_provider_port.py`, `lsp_provider_port.py`, `lsp_workspace_edit.py`, `user_browser_gateway.py`, `adaptive_edit.py` and `ordivon/adaptive_edit_bridge.py`.
6. **Result and other supporting contracts**: `protocol.py` (956), `independent_result.py` (902), `completion.py`, `structured_result_conformance.py`, `agent_tool_observation.py`, `ordivon/model.py` (804), `ordivon/run_contract.py`, `ordivon/turn_projection.py`, `anc_canonical`.

Some apparent zero-import modules are normal public entrypoints, tests-only adapters or loaded dynamically. Static inbound count must not license deletion.

## 5. Proven / conditional findings and deletion decisions (first pass)

| ID | Source-backed evidence | Decision / invalidating counterexample |
| --- | --- | --- |
| BF01 | Public Run #1859 **MERGED**; `sqlite_store.py` still referenced directly in existing scale and adaptive edit scripts plus many historical tests | **WAIT** on existing #1867/#1875 work; do not add a parallel migration or remove Store before actual script closure |
| BF02 | Large `run_continuity`, `loop`, `runtime_bridge` are authority hotspots | **REVIEW** by mixed responsibility and coupling; line count by itself is not a split proposal |
| BF03 | `evals/fresh_agent_ab/` has 14 files (~886 KB), no tracked inbound literal directory references. Peer readback: `run_live_v1.py` and `run_live_v2_currentness.py` import a now-absent `ordivon_harness.capability_discovery`; the other 12 contain historical preregistrations, corpora, results and closeout records | **YIELD/WAIT**: existing whole-repo peer owns retirement of the TWO broken runners; KEEP twelve unique historical evidence files. No blanket 14-file deletion. A current dynamic runner consumer falsifies the narrow retirement |
| BF04 | Three large `config/*browser-decision-corpus*.json` corpora have named research/test readers | **KEEP pending consumer-specific retirement**; large files are not necessarily duplicate data |
| BF05 | `evidence/index.json` and `scripts/check_evidence.py` bind evidence/currentness; historical rows are not current production authority | **KEEP** the currentness distinction; evaluate old evidence only as archival material |
| BF06 | `dap_provider_port.py`, `lsp_provider_port.py`, `adaptive_edit_bridge.py` may have zero `src` AST importers | **UNKNOWN** until installed/public/tests and dynamic call sites checked; do not auto-delete |
| BF07 | T1 CLI/Wheel correction #1979 and PG-only API #1859 merged; R2.1 task Spec #1991 remains an independent PR | **REUSE** committed source; do not repeat CLI, PG-only or write competing formal Spec |
| BF08 | `tests` and `research` include old SQLite-based behavior checks; some retain a distinct compatibility/recovery property, others may only keep dead paths alive | **REVIEW** current decision/behavior first; no arbitrary percentage or deletion quota |
| BF09 | AST parse of 367 tracked Python files finds imports of absent `ordivon_harness.capability_discovery`, `ordivon.sqlite_agent_bridge`, and `ordivon.sqlite_run_store`. Two old standalone drivers — `evals/capability_environment_owner_dogfood.py` and `research/experiments/harness_temporal_needs_input_segment.py` — have no current tracked basename inbound references or native `mise` task entry, and fail normal import against present source | **RETIRED in this candidate branch** only those two dead drivers (189 + 171 = 360 lines); preserved fixtures/historical evidence. Native Harness Queue on an isolated PG 18.6 cluster **PASS** (1498 passed, 2 deselected, 386 subtests), docs/evidence PASS, isolated wheel v0.6.0 PASS with ten CLI commands |

## 6. Execution tickets — brownfield only, no feature/test/consumer growth

The tasks form a partial order. The purpose is changing existing code/retiring dead files and documenting decisions, not filling a project board.

| Task | Existing seam / exact output | Dependencies | Acceptance and falsifier |
| --- | --- | --- | --- |
| B0 — Freeze SourceCut | Existing Git `origin/main`, PR/branch inventory, 731-file manifest | none | Source hash, count, file bytes, old/new PR collision recorded; stale refs invalidate affected conclusions |
| B1 — Source+authority decomposition | Existing Python AST, imports, `api.py`, CLI, Store and Runtime seams; group 62 source files | B0 | Identify state ownership and false dual writer; reject split-by-line-count |
| B2 — Existing script/evidence ownership | Audit 87 scripts, 139 evidence, 97 research, 48 evals and installed/CI routes | B0 | Each deletion has source-bound user or historical retention counterexample; static 0-reference is not proof |
| B3 — Independent **Spec × Standards** review | Existing Host Space/Code Review, no approval service | B1/B2 | Review actual source paths on nine questions below; disagreement recorded and acted on |
| B4 — Retire bounded nonconsumed historical packages | Existing Git rm, Git historical object recoverability, root owner checks | B2/B3 for contested cases | No active named consumer, no loss of unique last recoverable bytes, current `mise`/docs unchanged |
| B5 — Simplify existing core | Refactor **within** existing natural Owner APIs; first real duplicated invariant/effect state | B1/B3, not all B4 | No new feature/entrypoint/State owner; existing tests/wheel/queue still pass and complexity demonstrably falls |
| B6 — Converge docs/scripts and old SQLite obligations | Existing #1867/#1875 lineage and current docs | relevant pending PRs | Remove obsolete claims without adding compatibility shims; don't edit peers' live branches |
| B7 — Publish and stop | Native `mise run queue`, `scripts/check_docs.py`, evidence checks, GitHub root/Owner CI | changed-task checks only | Actual diff, deletion inventory, present source/CI standing; no invented installed/domain success |

Do not impose B5 on unrelated B4 work. No new tests are authored; existing native tests are used for regression and behavior preservation. When a risk cannot be assessed with current tooling, do not invent a checker: mark only that specific deletion/refactor UNKNOWN.

### Nine non-ceremonial questions for EACH contested file/cluster

1. What actual present outcome and Owner owns this responsibility?
2. Which imports, entrypoints, installed workloads, dynamic readers, historical evidence and external effects use it?
3. Does its retention or change strictly preserve typed state/authority/assumptions and guarantees?
4. Does Parnas/DSM/contract calculus support the **actual** grouping, or is this file-size/label cargo cult?
5. Does Matt Spec/Standards, ECC research-first or Superpowers root-cause/verification **materially** help? Which upstream steps should **not** be adopted?
6. Is the proposed cleanup too conservative (keeping stale work) or too aggressive (losing unique value)?
7. Is it surface polish instead of eliminating the actual duplicated implementation or owner confusion?
8. Which mature native/external mechanism already provides the required behavior, and what can be deleted rather than wrapped?
9. What is one concrete falsifier and the smallest owner-native readback to decide KEEP, RETIRE, SIMPLIFY, REUSE or UNKNOWN?

## 7. Progress discipline and scope lock

- Record findings in the **existing** Host `space:ordivon-capability-task-forum-r1:20261101`, topic `05-cleanup`. Space is coordination, not source/proof/owner truth.
- Don't modify concurrently owned #1991 task Spec, #1867 scale, #1875 Adaptive or production installation in this branch.
- An outside project's broad hook, approval, memory or orchestration system is never automatically imported by reading Matt/ECC/Superpowers.
- Proposed deletion should remove old tracked files, not quietly bury them in `archive/current`. Exact Git history is the normal recoverability record when nothing depends on an installed historical file.
- Check present docs/SourceCut/CI and report **SOURCE / MERGED / INSTALLED / CONSUMED** separately; no model-only proof upgrades.
- Stop the method effort when an analysis no longer changes a real cleanup/refactor decision; do not create a permanent audit registry or governance Owner.

## 8. Execution standing at first cut

**DONE**: source-frozen 731-file machine census, 62-source-file AST/import inventory, AST import resolution of 367 Python files, main/PR overlap, exact named experiment references, official theory/provider comparison, Host Space cross-audit refuting blanket 14-file retirement (peer seq25917; our response seq25925), and scoped two-driver retirement candidate BF09 (Host seq25928). **NOT YET PROVED**: per-file semantic validation of all 731 files, live external consumers of historical experiment data, installed-source qualification, complete data-retirement closure, independent Host-peer verdict. These are named limits; the file manifest's presence is not a review completion badge.

The immediate brownfield frontier is: publish BF09 as a reviewed source-only subtraction; allow the existing whole-repo brownfield peer to retire the two broken `fresh_agent_ab` runners while preserving twelve unique historical files; this branch must not edit those peer-owned paths. Next audit PostgreSQL/SQLite last production script users **after** upstream PR integration; reduce actual mixed responsibilities in continuity/loop/bridge only after a dependency graph identifies one proven change-worthy seam.

## 9. This branch's actual first maintenance effect and verification

- Exact SourceCut before the change: `ef17d6879d12faa61fff3bb762b0d500d73c9113`. Deleted only the two broken, unreferenced historical execution scripts under BF09; **no** `src/`, test, CI consumer, runtime service, feature or schema changes. The Git history retains their exact original bytes.
- Python AST parse (source-bound) covered **367** tracked Python paths, zero syntax failures; missing module references include `capability_discovery` (three historical eval runners) and `sqlite_agent_bridge`/`sqlite_run_store` (one historical Temporal pilot). The two `fresh_agent_ab` files are **not** modified here because a peer is handling them; twelve historical records should remain. This AST observation is not whole-world dynamic import closure.
- Native `check_docs.py` **PASS**; native `check_evidence.py` **PASS** with 94 historical receipts and zero presently verified receipts.
- Initial `mise run queue` without `HARNESS_PG_TEST_DSN` reached the installed wheel check and **FAILED** for missing required real PostgreSQL authority; do not call that a code defect or a passing check. An initial rerun shell contained an invocation typo, corrected before qualification.
- Re-ran the unchanged `mise run queue` with an isolated PostgreSQL 18.6 socket-only test cluster/five disposable test databases. **Exit 0: 1498 passed, 2 deselected, 386 subtests passed in 52.90s**. Existing bounded formal, dependency, documentation/evidence, wheel build/isolation, Host-free PG, MCP extra and ten current CLI command checks completed. Cluster/database discarded after qualification. This is SOURCE/TEST/WHEEL evidence, not installed production or domain acceptance.
- Peer cross-audit: the Host cleanup Topic received other brownfield Agent's concrete contradiction to blanket `fresh_agent_ab` deletion (seq25917), and this Agent yielded those exact paths (seq25925). No direct peer response about BF09 has yet been received; publication should request a source-path counterexample rather than pretend peer agreement.
