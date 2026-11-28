# REFACTOR_PLAN — exact-source, maintenance-only execution

## 2026-11-28 current-source continuation

This existing plan remains the progress SSOT for the brownfield convergence loop; do not create a parallel entropy backlog or owner registry. The current continuation is source-qualified against remote main 5ccd9fc8144de1a1349b21636a69108068c3ee67 in isolated Runtime Workspace ws-gpt56-architecture-entropy-20261128.

Fresh mechanical baseline on that SourceCut:

- source census observed 336 Rust, 108 TypeScript/TSX and 1,789 Python files; the counts are discovery evidence, not a reason to rewrite by language or line count;
- python3 tools/repo/check_owner_boundaries.py PASS (active_files=3001, 10 public packages, 44 declared seams);
- python3 tools/repo/check_structure_r2.py PASS;
- python3 tools/repo/check_architecture_docs.py PASS;
- exact production-file duplicate scan found only Security package-local tsconfig.json / pnpm-workspace.yaml copies already covered by R10's independent-package boundary;
- production Python import-SCC scan found only the already-known Capital OKX late-binding pair plus the Harness independent_result / run_continuity pair. Neither is a deletion claim.

Consumer-falsified candidates must remain out of implementation until their real seam is migrated:

| Candidate | Current verdict | Consumer / falsifier |
| --- | --- | --- |
| Runtime #1968 SQLite cache / storage-pressure retirement | **HOLD — cross-Owner migration required** | ordivon-runtime-pressure-control still invokes ordivon-runtime-cache; Workstation D-drive compact R3 unconditionally stops/restores ordivon-runtime-storage-pressure.timer and verifies exact enablement. A Runtime-only deletion would break a current maintenance transaction. Evidence was written to issue #1968 on 2026-11-28; no prototype source was retained. |
| Runtime #1871 SQLite concurrent-admission retirement | **HOLD — existing successor in flight** | Native PG identity witness is already being adopted by PR #2992, while Windows PG retirement remains an explicit outstanding consumer/physical gate. Do not create a competing deletion PR. |
| Skills four-tool compatibility surface | **KEEP — real external consumer** | extensions/chatgpt-skills-mcp/docs/chatgpt-skills-mcp-registration.md identifies ChatGPT as the evidence-backed retained consumer and readiness requires exactly skills.list/search/resolve/read; SEP-2640 is canonical standards transport but does not yet erase that consumer contract. |
| Artifact OpenXML/Python tree-digest copies | **KEEP — carrier-local duplication** | Runtime wrappers are copied into immutable generations and intentionally execute without repository package imports. Sharing the helper would add a runtime carrier dependency; duplicate bytes here are not duplicate authority. |

These results are Deletion-Test outcomes, not exemptions from future cleanup: revisit a HOLD/KEEP only when its cited consumer contract changes. Continue by selecting a non-overlapping natural-Owner slice with a behavior-preserving reduction; current open PR paths take precedence over creating parallel implementations.

### Closed loops on the current continuation

The branch was repeatedly rebased onto remote main; the latest verified base for the completed code batches is fa1a8a7496f0c9bfc8f05fb2067fe2d1d233b07a.

| Slice | Result | Verification |
| --- | --- | --- |
| Network VPN recovery finite refinement | Split the 313-line / 139-branch validate() into seven private proof responsibilities while preserving the sole validate() entrypoint and report contract. The orchestrator is now 40 lines / 0 branches; no new module, dependency, registry or proof claim was introduced. | mise run formal-vpn-recovery produced the exact same parsed JSON before/after; targeted Ruff/py_compile/diff checks PASS; full platform/network CI PASS with 654 tests + 4 subtests. Commit 7d774f97983 on the then-current branch. |
| Capital simulated Paper application | Separated caller-artifact binding, Qlib decision refinement, pure Paper replay, native fill economics, simulation identity and the single PostgreSQL effect boundary. Public run_simulated_paper fell from ~294 lines / 61 branches to 55 lines / 1 branch without changing its public API or account-key/effect semantics. | Focused Paper simulation suite remains 27 PASS / 1 environment-dependent PG skip; exception literal multiset unchanged; full Capital mise run verify PASS with 1220 tests, 52 skips, 39 deselected, 243 subtests plus Lean/Z3/CrossHair/Paper/PIT checks. Commit 1ea34bba5b1. |

Additional deletion/substitution candidates reviewed and rejected on current source facts:

| Candidate | Verdict | Reason |
| --- | --- | --- |
| Artifact artifact_software_release.py OCI shadow verifier | **HOLD — profile retirement/migration required first** | No production verification route currently calls the script, but software-release-oci-image-r1 remains a declared SHADOW_PROFILE_LIVE_PROVEN capability with focused verifier tests, shadow binding, taxonomy entry and Artifact skill reference. Deleting the verifier while retaining live-proven standing would create evidence drift. Retire the profile or migrate directory-layout verification to the canonical verification service before deleting executable/test evidence. |
| Host/Gateway social-tool registration similarity | **KEEP — owner projection, not duplicate authority** | Host owns the adapter schema; Gateway owns typed northbound projection/policy. Gateway source-consumer tests deliberately validate allowed schema differences, while host_tool_contracts.py already centralizes read/write class and budget policy. Cross-owner shared registration would increase coupling. |
| Media equipment_plan.compile_operation provider branches | **KEEP — explicit provider dispatch is the canonical rule location** | The function is pure compilation; branches correspond real provider/capability boundaries. Extracting one helper/catalog per provider would spread the same rules without reducing change sites or effects. |


**Phase 3:** complete planning against `ef17d6879d12faa61fff3bb762b0d500d73c9113`, existing `AUDIT_REPORT.md` findings F01–F12.
**Execution:** original/current tests and native source reads, not a new test suite or consumer route. Use the already existing `docs/architecture/REPOSITORY_BROWNFIELD_MODERNIZATION_EXECUTION_SPEC_20261110.md` proposed in PR #2012; this file is the specific Phase 3 execution breakdown, not a new authority registry.
**Explicit prohibition:** new features, tests, new consumer lines, new dependencies or broad cross-Owner migrations.

## 1. Gate: choose existing Owner, freeze source

Current canonical map: `tools/repo/owners.toml`, `tools/repo/dependency_contracts.toml`, root `AGENTS.md`. Each task starts by reading the current changed files, a real caller/consumer and overlapping GitHub PR file list. A current PR covering the same code must be reused or deliberately superseded, not competed with.

`SourceCut` = exact SHA from `git rev-parse HEAD`; compare upstream with `git ls-remote origin refs/heads/main`. Use GitHub protected main PR and existing Merge Queue, never direct reset or stash of the shared primary.

## 2. Source-qualified precedence & task DAG

`R0 baseline -> R1 changed-test contract -> R2 read-only source indexing -> R3 per-Owner semantic reduction -> R4 documentation/asset retirement -> R5 re-audit/merge/readback`.

R1 and R2 are **already source-implemented in PR #2012**; no one should reimplement them from this task graph. R3 has independent Owner slices; R4 requires existing consumer-qualified deletion evidence. R5 source/merge standing is separate from installed/product consumer.

| ID / severity | Exact file(s), observed source deficiency | Concrete small action / acceptance commands | Existing state and rollback |
|---|---|---|---|
| R01 HIGH | `tools/repo/test_exhaustive_coverage.py:110-111` vs `tools/formal/mise.toml:17` | In the existing test only, require `python3 -I verify.py` (not the outdated literal). Run `python3 -m pytest -q tools/repo/test_exhaustive_coverage.py`; old source observed 2 failures, candidate 79 pass. | Already in PR #2012, source implementation; revert its commit if current Formal contract differs. No new test. |
| R02 HIGH | `tools/repo/test_exhaustive_coverage.py:634` missing sparse zero key | In existing assertion read `sourceProblemCounts.get("STRUCTURE_SPLIT_REQUIRES_CONSUMER_WITNESS",0)`, retaining equality to actually computed counts. Run existing pytest module. | Already in PR #2012; same Git revert, not a fresh policy. |
| R03 MEDIUM | `tools/repo/exhaustive_coverage.py:472,482-492` redoes N² prefix search despite exact-cell index | Find longest **proper string** prefix in `cell_by_key`, including empty prefix if present. Preserve output fields and SOURCE identity. Run existing 79-test suite, `check_architecture_docs.py`, `check_structure_r2.py`, `check_owner_boundaries.py`. | Already in PR #2012; source-only behavior-preserving code. Rollback native `git revert <exact-merge-SHA>` if merged; no new adapter. |
| R04 HIGH | `services/harness/src/ordivon_harness/ordivon/loop.py:220-2340` one 2,121-line Run method | First read all `OrdivonAgentLoop._run` code, `run_recovery.py`, `run_continuity.py`; run `git log -8 -- <files>` and inspect active PR #1835. If not already covered, move only an existing already-distinct pure decision/helper into its current natural module and preserve signatures; verify `mise run harness:verify`, no additional tests. | **NOT STARTED** due live overlap and high effect risk; do not invent an extraction target before per-function analysis. |
| R05 HIGH | `services/harness/src/ordivon_harness/ordivon/run_continuity.py:129-3186` EventSourcedRunContinuity | Compare imports and `run_store_port.py` with actual Journal/CAS consumer. Only simplify repeated read/no-effect paths; never move writer authority to another Owner. Verify `mise run harness:verify`. | **NOT STARTED**, requires focus on one existing contract and no parallel PR. |
| R06 MEDIUM | `tools/repo/check_architecture_docs.py:1812-2157` 346-line formal issue census validator | Read checker, owner source currentness and existing `test_architecture_docs.py`; inspect #1978/#1940 first. Split only if an independent existing suite can still consume same entrypoint; avoid creating a second checker or policy. Run `python3 tools/repo/check_architecture_docs.py` and `python3 -m pytest -q tools/repo/test_architecture_docs.py`. | **WAIT ON SOURCE CONFLICT** (not a new human approval): overlap PRs, preserve canonical current gate. |
| R07 MEDIUM | `services/runtime/crates/ordivon-runtime-core/src/runtime/tests.rs` 10,788 lines, `types.rs` 2,097 | Prioritize one actual actor/consumer to isolate. Native Rust modules already exist: do not split just to lower LOC; verify `mise run runtime:verify` if a source slice is changed. | **REVIEW ONLY**. Rust Job/Attempt recovery semantics are safety-critical. |
| R08 MEDIUM | `capabilities/artifact/artifact_operations/providers/direct_python.py:95,439` provider orchestration concentration | Trace `produce` and same-profile verification source in `artifact_core/`, `artifact_verification/`, `artifact_verifiers/`, and active Artifact PR. Remove only duplicated stage logic with identical current API. Verify `mise run artifact:verify`. | **REVIEW ONLY**, no rival implementation to active Artifact Owner. |
| R09 MEDIUM | `domains/capital/src/ordivon_capital/trading/okx_demo_execution.py:399` + `okx_official_cli.py:17` static SCC | Inspect Python import-time and provider effect semantics; top-level official CLI inherits base class, base file imports official CLI only late. This currently does **not** prove runtime import failure. Keep until a real existing test/failure demonstrates cost. Use `mise run capital:verify` after any future refactor. | **KEEP / UNKNOWN** for actual runtime behavior. No external trade action or synthetic model experiment. |
| R10 LOW | Security duplicated OAuth patch/config in two independently shipped source packages | Check `platform/security/contracts/agent-request-verifier-v1/` and `platform/security/labs/agent-admission-rs/` package references before considering one owner-local asset. Preserve pinned dependency, provenance and tests; run `mise run security:verify` after any qualified edit. | **KEEP** until independent packaging/consumer evidence; deletion not assumed. |
| R11 LOW | Media production PNG duplicates and unequal large creative-library JSON catalogs | Check the actual production manifests: `capabilities/media/productions/archive-archipelago-001/`, `live-relay-001/`, source/artifact/render roles and native media validation. If a dependency is intentional, retain independent provenanced copies. | **KEEP**; bare SHA-256 duplicate does not imply safe physical delete. |
| R12 LOW | Harness `sqlite_store.py:154` still read by historical/local scripts, while PG is current production authority | Keep compatible sources until concrete scripts no longer consume; avoid blanket SQLite drop. | **KEEP**, no action authorized. |

## 3. Natural-owner program waves (every Owner is covered as an audit perimeter)

**Source interface / command acceptance per Owner:** root `mise run <native-task>` from `owners.toml`, with an exact normal checkout SourceCut. The following are **audit waves, not instructions to change all owners at once**.

| Wave | Registered current Owners | Initial current-source paths | Exit from this wave |
|---|---|---|---|
| W0 | Repo source mechanics | `tools/repo/exhaustive_coverage.py`, `test_exhaustive_coverage.py`, `check_owner_boundaries.py` | R01–03 and native structure/owner checks qualify at source |
| W1 | Runtime, Host, Harness, Gateway | `services/runtime/crates/`, `services/host/src/`, `services/harness/src/`, `services/gateway/src/` | each real public seam and current consumer inventoried, highest-risk debts bounded |
| W2 | Security, Network, Workstation | `platform/security/contracts/`, `platform/network/substrates/`, `platform/workstation/ansible/` | native auth/transport/OS authority preserved, no extra control service |
| W3 | Artifact, Distribution, Media, Preservation | `capabilities/artifact/artifact_operations/`, `distribution/adapters/`, `media/src/`, `preservation/scripts/` | existing evidence/format/provenance verified, no silent deletion |
| W4 | Capital, Game | `domains/capital/src/`, `domains/game/examples/` | bounded legacy/engine/finance semantics, exact producer/consumer |
| W5 | Composition, Data, Authority Catalog, Capability Catalog | `packages/composition/src/`, `packages/data/src/`, `catalogs/authorities/`, `catalogs/capabilities/` | shared generic logic remains non-authoritative |
| W6 | Skills, Control Plugin, Web, Chaoxing | `extensions/chatgpt-skills-mcp/src/`, `extensions/ordivon-control-plane/`, `apps/web/src/`, `apps/chaoxing-autosign/` | actual clients/entrypoint and application data authority identified |

There are exactly **21** manifest Owners. Standalone `tools/formal` and `.agents/skills` are source regions/packages, not automatically new domain authority.

## 4. Implementation and acceptance of one slice

1. **Observe:** `git log -8 -- <selected path>`; read source body, current caller, native script and relevant README. Record exact code lines.
2. **Specify existing behaviour:** annotate `pre/post/side effect/UNKNOWN` only where a real Owner responsibility has independent contract; never one LEGO per file.
3. **Select change:** prefer delete or current native reuse. For no substantiated issue choose **KEEP**. For incompatible known high-risk PR choose **defer collision only**, not a new permanent blocker.
4. **Execute:** small isolated worktree, no source mutation outside natural Owner; avoid new helper modules unless they replace actual repeated responsibility.
5. **Verify:** existing focused tests and actual Owner task (all optional environment skips disclosed), `git diff --check`, source/consumer diff and GitHub required checks. No new regression test cases under current user freeze.
6. **Review:** Matt Standards and Spec axes separately; ECC source before opinion; Superpowers evidence before completion. Each comment must identify path:line/counterexample and risk.
7. **Publish:** existing GitHub PR/Merge Queue; report SOURCE, MERGED, INSTALLED, EXECUTED and CONSUMED only at their actual observed authority. To undo, `git revert <merge-commit>` or restore isolated branch; never reset shared main.
8. **Continue:** pick next confirmed highest-value issue, not next alphabetical directory or fixed percentage.

## 5. Rollback and finite definition of done

- R01–03 source artifacts are in `PR #2012`, not in a private uncommitted change. No duplicate implementation is allowed.
- Every source patch can be reverted by Git, but rollback of external side effects is **not** implied by Git revert.
- Existing checks cannot prove universal behavioral equivalence. Use precise domain observer, default UNKNOWN for dynamic/installed consumers.
- Phase 3 itself is a completed execution *plan*; the 21-Owner semantic deep audit and all R04–12 are NOT done. Do not claim broad refactor completion from this document.
- The final `BASELINE_AFTER_AUDIT.md` records exact main/PR status, actually executed checks and unresolved risks, not success percentages.
