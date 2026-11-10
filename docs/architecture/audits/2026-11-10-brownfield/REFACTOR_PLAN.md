# REFACTOR_PLAN — exact-source, maintenance-only execution

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

## R2 — Existing duplicate audit artifact convergence (2026-11-10)

**Decision, SourceCut `e037af933b66cdfccc7e13e3e6392847e7f84fc8`:** four separately-authored 2026-11-10 repo-wide audit directories contain the same 5,002-source pre-audit census. `docs/audits/2026-11-10-brownfield/` alone adds seven parallel files (1,248,072 bytes), of which `FILE_CENSUS.tsv` is a 1,200,476-byte second full index. Current repo already has this Owner-local canonical evidence directory with `FILE_LEDGER.tsv.gz` (5,002 exact Git blobs, 204,713 compressed bytes), and the complete current tree in `INVENTORY.md`.

**Smallest consumer-rooted task:** import the distinct, already-merged Finance #2040 implementation/verification disposition into existing `AUDIT_REPORT.md` and `BASELINE_AFTER_AUDIT.md`, update `domains/capital/docs/FINANCE_DIRECTORY_OWNER_AUDIT_R1.md` to the surviving evidence path, then physically retire only the seven redundant `docs/audits/2026-11-10-brownfield/` files. Source-only historical SHA-256/owner data are recoverable from `git show 41c896da3f9b:docs/audits/2026-11-10-brownfield/FILE_CENSUS.tsv`. No dynamic product consumers of that directory were found; the one current literal path reference is in Finance Owner audit.

**Ruling, after the original HOLD:** a fresh GitHub readback found both PR #2031 and #2039 CLOSED without merge. For `docs/architecture/audits/2026-11-10/`, only two active Runtime *documentation pointers* existed; both can be redirected to the already-existing canonical `AUDIT_SCOPE.md`, with no Runtime implementation change. The other `docs/audits/2026-11-10/` directory has zero outside literal source/path consumers. Original archived facts on Web #2019 and Runtime #2028 are preserved by scoped additions to the current canonical `AUDIT_REPORT.md` and `BASELINE_AFTER_AUDIT.md`. Therefore RETIRE these two remaining duplicate groups in the same source-only document consolidation, while preserving original Git contents. Do not claim that a historical external bookmark is impossible. Existing `runtime/scripts/check_docs.py`, Web/Capital Owner-native tests, root `repo:ci`, and path/currentness checks are the acceptance rails.

**Acceptance / rollback:** current Git grep has zero unexplained references to the retired directory, existing Owner boundaries, architecture/doc checks, Capital and repo native verifiers stay green. `git revert <source-commit>` restores its exact contents; no database, installed Runtime or external effects change. No new test/consumer/registry is needed.
