# BASELINE_AFTER_AUDIT — source-first brownfield Phase 0–5 bounded result

**Recorded:** 2026-11-10 Asia/Singapore.
**Exact initial Git SourceCut:** `ef17d6879d12faa61fff3bb762b0d500d73c9113` (protected origin/main verified repeatedly during this audit).
**This audit's change perimeter:** six documentation/evidence outputs in `docs/architecture/audits/2026-11-10-brownfield/`. Existing first code repair is a separate already-created PR #2012, SHA `9bda50db4b3413d1a741740613e6383e24c39c83`, sourced from the same base.
**No production schema, Git main, runtime deployment or user data were changed by this audit worktree.**
**Truth boundary:** SOURCE audit and existing-test verdict, NOT full system modernization/installed release/semantic-consumer acceptance.

## 1. Phase delivery and actual scope of completion

| Phase | Evidence location | What was completed | What is not claimed |
|---|---|---|---|
| Phase 0 | `AUDIT_SCOPE.md` + `MODERN_CRITERIA.md` | Frozen current Git source and all 21 registered natural Owners; 11 falsifiable modern architecture criteria; no invented global schema | Installed versions and every Owner's live schema are not derived from README |
| Phase 1 | `INVENTORY.md` | Exact nested SOURCE tree with **5,002 tracked files** / 6,055 tree lines; owner roots, language/entrypoints/schema and candidate experimental paths | Not 5,002 independently qualified dynamic consumer traces |
| Phase 2 | `AUDIT_REPORT.md` | 21 Owner module source review; concrete line evidence, local Python AST bounded SCC graph, F01–F12 findings and risk/disposition | No universal full-file semantic closure, no implicit live business acceptance |
| Phase 3 | `REFACTOR_PLAN.md` | Dependency-ordered small maintenance tasks, actions/risk/rollback, actual existing Owner tests and deferral of conflicting PRs | No authority to approve financial or external side effects |
| Phase 4 | `PR #2012` (SOURCE candidate) | Actual existing-code optimization and two existing stale test fixes, no new tests/features/consumers | PR is OPEN + autoMerge at initial audit; SOURCE PASS ≠ MERGED |
| Phase 5 | this file | Post-audit SOURCE baseline and explicit residual-risk/readback boundaries | Full repo refactor not complete |

## 2. Before/after observed maintenance slice

**Existing main source tests before R01–R03 (same exact source cut):**
`python3 -m pytest -q tools/repo/test_exhaustive_coverage.py` → **77 passed, 2 failed, 18 subtests passed**. The preexisting failures were:

1. `tools/repo/test_exhaustive_coverage.py:110–111` expects `python3 verify.py`, while `tools/formal/mise.toml:17` already executes `python3 -I verify.py`.
2. `tools/repo/test_exhaustive_coverage.py:634` indexes an absent sparse zero-count Structure R2 category, yielding `KeyError`.

**Candidate PR #2012 after R01–R03:** the identical 79-test suite → **79 passed, 18 subtests passed**; `check_architecture_docs.py`, `check_structure_r2.py`, `check_owner_boundaries.py` and `git diff --check` passed. The actual source change `tools/repo/exhaustive_coverage.py:482–492` reuses the existing `(zone,proper_prefix)` map rather than scanning all other cells. It preserves all **proper string** prefixes including the empty string and does not require a directory separator assumption. Complexity improvement is conditional on prefix size; Python slicing costs are accounted for in the original PR Spec.

**Existing root `mise run repo:ci`:** admitted/executed but the local collection process timed out at **250 seconds** without a complete PASS. GitHub required checks/merge queue remain authoritative for integration. Do not upgrade the focused PASS to FULL CI PASS.

**This audit-doc worktree (fresh readback):**
- `python3 tools/repo/check_architecture_docs.py` **PASS**.
- `python3 tools/repo/check_structure_r2.py` **PASS**.
- `python3 tools/repo/check_owner_boundaries.py` **PASS**, active_files=2,320, seams=31, references=38.
- `git diff --check` **PASS**.
- All 21 Owner roots and 5,002 source paths derived from the pinned Git tree. Python AST pass found 1,460/1,460 parseable files.

## 3. Live Host observation, separately identified from source

At observedAtMs `1794250174406` (not inferred from README):
- Host response projection `schemaVersion=3`, live PostgreSQL `journalSchema=13` (different meanings).
- Work=5 (open=1, completed=2, abandoned=2), WorkSnapshots=15, Space=36, Topic=228, Message=25,482, Subscription=86.
- This live readback is operational observation, not proof that historical Work revision continuity is perfect. A prior integrity readback found three history-contiguity violations; no production mutation was performed in this audit.
- **Reason for retaining old Work identity:** independent Host Owner review found real social references, so `terminal` is not proof of 'unused'. No blanket deletion.

## 4. Review decisions that save work

- Static Python code graph: Harness 62 nodes / 265 edges / 0 strongly connected multi-module groups, Gateway 26/60/0, Host 36/101/0; Capital 65/54 with one two-node **syntactic** SCC.
- Direct isolated Python import of both `ordivon_capital.trading.okx_demo_execution.OkxSpotDemoClient` and `okx_official_cli.OkxOfficialSpotDemoClient` returned **exit 0**. This falsifies an automatic 'import-time circular failure' conclusion. Native trading effects have **not** been exercised.
- 20 apparently unused private helpers were checked with source-wide symbols: all had cross-file import/call references. Do **not** remove them based on a file-local AST alone.
- Fourteen byte-identical source-file groups remain candidates, not unconsumed artifacts; separate production/source asset identity and package-local patch consumers require natural-owner evidence.
- Current README/AGENTS relative-link scan on 134 selected entrypoints found 0 proven broken local paths. No shotgun docs rewrite is justified.
- Historical `CURRENT_ARCHITECTURE.md` is already marked non-authoritative and `STRUCTURE_R2.md` partial deployment is explicit; do not 'correct' them into false present-day claims.

## 5. Residual tasks and truth standing

| Severity | Owner / file | Source gap | Standing | Required next native qualification |
|---|---|---|---|---|
| HIGH | Harness `ordivon/loop.py:220-2340` and `run_continuity.py:129-3186` | giant lifecycle and evidence methods; high change cost | SOURCE risk, not independently proven faulty | check current PR #1835, preserve Run/Tool transition semantics, existing `harness:verify` |
| HIGH | Runtime `runtime/{engine.rs,types.rs,tests.rs}` | large physical-execution semantics and tests | current behavior unknown to this audit | source/lifecycle responsibility, `runtime:verify` |
| HIGH | Artifact `artifact_operations/providers/direct_python.py:95-606` | high adapter orchestration concentration | need current Artifact Owner/PR source | `artifact:verify` after specific consumer-backed cut |
| MEDIUM | Repository `check_architecture_docs.py:1812-2157` | large historical evidence checker and ongoing parallel PRs | keep live current authority | avoid PR #1978/#1940 source collision, `check_architecture_docs.py` |
| MEDIUM | Capital `trading/{okx_demo_execution.py,okx_official_cli.py}` | delayed import and direct inheritance form syntactic SCC | normal isolated import PASS, effects UNKNOWN | avoid change without justified native consumer and `capital:verify` |
| LOW | Security/Media copied package assets | identical bytes can have independent provenance | KEEP pending actual consumer proof | source manifest and owner-native verification |

There are **no certified full-file semantic closures for all 5,002 files**; the original requested total remediation remains OPEN across many Owners. This is an honest Phase 5 **bounded source baseline**, not a false success certificate.

## 6. Rollback and handoff

- Code improvement: exact PR #2012/source SHA, GitHub auto-merge requested. Review `git diff ef17d6879d12faa61fff3bb762b0d500d73c9113...9bda50db4b3413d1a741740613e6383e24c39c83`. On an admitted merge, `git revert <merge_commit>` is the standard SOURCE rollback; this does not cancel external effects.
- Audit documents: revert this audit PR when any static observation is disproved; historical assertions remain in immutable Git history.
- Natural Owner controls: no static grep or reviewer can authorize deleting Host Work/Runtime WS or Security credentials. Use each native Owner lifecycle and actual consumer proof.
- Space coordination: `space:ordivon-whole-system-optimization-r1:20261002` topic `repository-operating-model-r1:20261004` requests sequence 25884 / 25929 / handoff 25941; further formal review handoff seq25984 in the existing crossaudit topic.
- Handoff required fields: **state**, exact Git/host SourceCut, **completed code/check**, **open risks**, proof **paths/commands**, **next natural Owner**, **unknown outcome planes**. Space communication is not an extra gate to ordinary low-risk changes.

**Conclusion:** the recorded SOURCE baseline has improved specificity and one real code maintenance candidate passed existing scoped checks. The broad modernization program is not yet complete at deployed/domain or per-file semantic level; future claims must retain these distinctions.

**Cross-Agent file evidence:** reuses exact 5,002-path peer blob ledger `FILE_LEDGER.tsv.gz` (compressed SHA-256 `1274eac9f9c8571854b77b950f025863e1f91a94fa32074358b20be932873d9e`). All rows explicitly retain semantic-review UNKNOWN; this is not a second state authority.


## 7. After-audit duplicate-source retirement (later SourceCut)

At Git main e037af933b66cdfccc7e13e3e6392847e7f84fc8 both this Phase 0–5 package and PR #2021's shorter six-file docs/audits/2026-11-10/ package existed. The latter was retired from the current tree after exact source/consumer comparison, preserving original commit 411774ac7f5dd6b482d6b17fc5780db02682d348 for Git-native rollback. The more comprehensive 5,002-path tree and exact-source compressed file ledger remain here. The Capital Owner's broken documentation reference was repaired in place. This is source-only cleanup, not a production/Finance/Runtime/Host effect. Verification evidence belongs in the associated Git PR; this historical baseline does not independently assert full repo CI PASS.
