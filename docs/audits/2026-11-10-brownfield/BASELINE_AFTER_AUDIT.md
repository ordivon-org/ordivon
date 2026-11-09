# BASELINE_AFTER_AUDIT — Ordivon Brownfield source closeout (selected verified slices)

**Before SourceCut**: `ef17d6879d12faa61fff3bb762b0d500d73c9113` (2026-11-10). **Reversible code change commit**: `697fa8f59421551db9fbb045f1ccb73b93eb090f`. The audit documentation commit and resulting PR remain the final branch evidence; GitHub merge/installed currentness must be read independently. This is a **source architecture audit and completed subtractive batch**, not 5,002 separate proofs of semantic correctness.

## Phase closure by actual evidence

| Stage | Status | Observed deliverable / limitation |
| --- | --- | --- |
| 0 Scope, criteria | DONE source-only | `AUDIT_SCOPE.md`: 21 natural Owners, 12 checkable `MODERN_CRITERIA.md`; no added runtime mechanism |
| 1 Full file/owner inventory | DONE static | `FILE_CENSUS.tsv` has **5,002** baseline Git files with exact path, byte size, SHA-256, initial Owner and scope; `INVENTORY.md` contains actual top-level counts; 64 binary records carry no invented line count |
| 2 Architecture conformity | DONE prioritized source review | `AUDIT_REPORT.md`: 21-Owner matrix, PASS/PARTIAL/FAIL/UNKNOWN with grounded paths, 9 findings, actual blocker examples. No claim of exhaustive semantic or installed inspection |
| 3 Small-batch plan | DONE | `REFACTOR_PLAN.md`: consumer-rooted dependencies, rollback and STOP conditions; no new features/tests/consumers |
| 4 Code/text subtractive repair | DONE B01–B04b; B05 HOLD | Git `697fa8f59421`: 25 tracked files retired, stale PG/SQLite current-truth corrected, nonexistent ELE research pointer deleted |
| 5 Closure | DONE for selected repaired slice | Capital and Catalog existing native suites, repo:ci, boundary/model/docs checks, real Finance read-only CLI and Git diff; original fixed SourceCut preserved |

## Precise before / after

| Quantity | Before `ef17d...` | After audited code change | Scope |
| --- | ---: | ---: | --- |
| Git-tracked source tree entries excluding new one-time audit artifacts | 5,002 | **4,977** | removed 25 unused historical files |
| Capital tracked files | 399 | **374** | no deletion inside `src/ordivon_capital/` |
| Historical executable files removed | 0 | **22** | 13 LEAN Wave-B, 8 TigerBeetle, 1 obsolete Nautilus M6 caller |
| Self-preserving legacy tests removed | 0 | **1 file / 5 tests** | `test_legacy_replay_surface_isolation.py` |
| Other retired stale objects | 0 | **2** | one historical path registry, one old OKX demo document |
| Added features / test cases / consumer wiring | 0 | **0** | only source removal, correction and one dead list-entry subtraction |
| Root tracked files including seven static audit artifacts | 5,002 | **4,984** | audit files are dated snapshots, not an always-updated registry |
| Finance native non-provider pytest | **870 passed**, 26 skipped, 24 deselected | **865 passed**, 26 skipped, 24 deselected | five obsolete self-tests explicitly removed, 209 existing subtests passed both times |
| Repo owner boundary checker | 2,320 active files, 31 seams, 38 reference bindings | **2,312 active files, 31 seams, 37 bindings** | current source only; no claim all runtime imports are known |

Static audit artifacts increase document storage (FILE_CENSUS.tsv ~1.2 MB) while *executable legacy paths* decrease; do not falsely report that total repository bytes necessarily decreased. The census was generated once from original Git-tracked paths and must remain immutable historical evidence, not a regenerated all-workspace source index.

## Native checks actually executed

At the before SourceCut, both repository boundary/structure/document/composition checks and Capital's original `mise run verify` passed. After the changes, the following existing tasks were observed successful:

- `cd domains/capital && mise run verify`: **865 passed; 26 skipped; 24 deselected; 209 subtests passed**. This includes scoped Lean/Z3/CrossHair formal checks. Skip does **not** mean a local disposable PostgreSQL or provider integration was exercised.
- `mise run repo:ci`: **PASS twice** during the execution, including final post-catalog-change run; grouped pytest **533 passed**, native unit/owner/structure/architecture/GitHub governance checks passed. Known long-running tests in existing repo:ci remained native; no new verifier.
- `mise run capability-catalog:verify`: **PASS** after removing one nonexistent `SOURCES` entry. Its bounded provider composition smoke is not physical execution authorization.
- `python3 tools/repo/check_owner_boundaries.py`, `check_structure_r2.py`, `check_architecture_docs.py`, `check_composition_architecture.py`: **PASS** at the initial source cut, and covered by final repo:ci.
- `domains/capital/scripts/run-strategic-contribution-brief < domains/capital/examples/strategic_contribution_r1.json`: read-only demo still gives `BOND_CORE=10000`, `INDEX_CORE=0`, `cashAfterMinor=40000`, `executionAuthorized=false`.
- `git diff HEAD^ --check`: **PASS**, no whitespace errors in patched tracked sources.

## Exact retire/keep decisions

**RETIRE**: the entire `domains/capital/tools/legacy_replay` and `tools/tigerbeetle_0_17_9` historical replay executable island; transitive `tools/nautilus_rc4/run-m6-differential`; the self-preserving isolation test, historical registry and unconsumed dated OKX demo markdown. Every deleted byte remains retrievable at the pre-change Git commit, not maintained as a fake active deployment.

**RETAIN**: the live `ordivon_capital` seven-Owner source packages and native scripts, PG ledger/Paper source, frozen Wave-B portfolio fixture, scoped current provenance, all formal proofs, extant required Owner verification, independent Portfolio/Risk checks, current Nautilus/QuickFIX/jsonschema candidate branches not included in this batch.

**CORRECT IN PLACE**: Finance architecture + external Owner docs now name PostgreSQL source as current and historical SQLite as historical; `catalogs/capabilities/ele/studies.py` no longer registers an absent Finance document. No added cross-Owner consumer.

**HOLD**: exact source-to-Consumer Risk/Portfolio arithmetic consolidation, large Harness state-machine module depth, root media tracked production outputs, Nautilus rc4 remaining candidate qualification, and dynamic/deployed consumer closure. These need owner-local verified equivalence or physical evidence, not a blanket veto on unrelated deletion.

## Two-axis review (Matt Pocock standards × spec)

**Standards**: native owner placement retained; no Owner contract or new public entrypoint introduced; existing boundary/architecture tests pass; journal/CAS, Task continuity, physical execution and domain acceptance remain distinct. The historical source test was deleted because it enforced a no-longer-useful file existence obligation.

**Spec**: first observation, then consumer-rooted decision, small reversible Git diff, original verification after actual deletion; no tests/features/consumers added. Complete **structural** tracked-file coverage, prioritized module semantic review, accurate limitations and actual source cleanup. Not a claim full dynamic semantics of all 5,002 files have been independently proven.

## Open evidence and collaboration

Space messages for root-wide falsification were committed to `space:ordivon-capability-task-forum-r1:20261101` and `space:ordivon-task-portfolio-and-proof-gates-r1:20261101`, sequences 25954 and 25955. No peer reply was observed during the scope of this closeout. Read-only sibling Codex reviews were attempted but **NOT_RUN** due model usage/access limits; never counted as independent review PASS. Owner-native static acceptance and GitHub required CI remain actual mechanical evidence. GitHub PR/merge may continue separately, and should not be confused with installed system truth.

### Conservative-deletion falsifier

If a named active caller is later proven to depend on `tools/legacy_replay`, retrieve its exact source from `ef17d...` with `git show` or revert commit `697fa8f5`, assess the existing interface and required Owner tests, then choose the smallest supported restoration. Git history is a recovery mechanism, not evidence of a current deployed engine.

### Release standing

Current local branch contains the code commit and the audit artifacts when the documentation commit is made. `MERGED`, `INSTALLED`, `LOADED`, `CONSUMED` and economic outcome are separate and must not be inferred from this document.
