# After-Audit Baseline — 2026-11-10 Source-Cut-Bounded Delivery

**Standing:** bounded P0–P5 batch outcome, not a statement that all 5,002 files have finished manual semantic review or that any changes have been installed. This file is a one-time record in the actual audit PR. The original Git SourceCut is ef17d6879d12faa61fff3bb762b0d500d73c9113; subsequent PR commits and live installations are separate identities.

## Before and after: concrete observations

| Property | Before (baseline source/effect) | After this batch (observed or scoped) | Truth level |
| --- | --- | --- | --- |
| Inventory coverage | 5,002 Git-tracked files without this batch's per-file ledger | 5,002 existing files independently read for bytes/hash/path, with 21 Owner mappings and exact initial unreviewed state in FILE_AUDIT.tsv | SOURCE INVENTORIED, not all semantically reviewed |
| Architecture criteria | Existing R3 global Owner programme; no 12-point time-bound module audit in this directory | AUDIT_SCOPE, MODERN_CRITERIA, INVENTORY, AUDIT_REPORT, REFACTOR_PLAN and this baseline reference current SourceCut and one-time scope | SOURCE documentation only |
| Core Owner architecture | Manifest 21 roots; mixed language/technology stacks with existing boundary checks | No new Owner, registry, Nx runner, class hierarchy, shared app state, new test or consumer path | SOURCE diff comparison |
| Application state ownership | Chaoxing CLI used global TMPDIR fixed name and unlinked preexisting file on startup (cli.py:42–45) | Owner-local proposed fix moves demo ledger into an invocation-private TemporaryDirectory with deterministic close; old shared temp file is never touched | actual before/after CLI behavior; source PR separate |
| Chaoxing synthetic output | Fake normal activity confirmed, QR activity requests user verification | Both CLI invocations preserve these same observations and ScanStats(courses=1, activities_seen=2, activities_processed=2, confirmed=1, user_action_required=1, retryable_failures=0, terminal_failures=0) | executed in isolated sandbox |
| Preexisting shared temp file | In sandbox, old demo overwrote a sentinel fixed path (before SHA256=858e35f96f318f88d59f03d96018b66d91e44d65368c85f4c1aaa3855c4ef29b) | Fixed CLI leaves exact sentinel digest unchanged after two complete runs and leaves no new demo files | executed/source effect |
| Existing Chaoxing tests | 11 existing tests PASS before code change | 11 existing tests PASS after code change; no tests added | owner-native |
| Cross-Owner Python graph | Static syntax implies 1 cycle in 331 module subset | Source inspection found conditional import on one edge, not a proved eager runtime cycle; KEEP, no graph-driven refactor | source-logic conclusion, installed UNKNOWN |
| Host history | Live PG schema 13, Doctor unhealthy due to 3 discontinuous Work histories | No Host PG changes; problem remains natural Host Owner | live external observation; unresolved |
| Harness legacy source | SQLite store source calls itself “current”, PG store says PG-only default | No Harness source change here; current installed/caller standing unresolved | source conflict, delegated |
| Artifact witness/Runtime installed schema | Distinct proof and installed gaps | No edits in this batch; current Owner PRs must supply proof and installed acceptance | scoped UNKNOWN |

## Actual changed files for Phase 4 code batch

- apps/chaoxing-autosign/chaoxing_mvp/cli.py (single natural Owner application CLI) — replace global fixed temp DB + unlink with explicit ledger Path supplied from main's TemporaryDirectory. No new test, feature, provider, connector or external client.
- Existing CLI behaviour before modification was reproduced using a fresh isolated TMPDIR and a sentinel file, avoiding destruction of any pre-existing real host file. After modification the sentinel survived unchanged, the app produced equal ScanStats on two invocations, and only that sentinel remained in the temporary sandbox.
- Existing native owner check: mise run chaoxing:verify -> 11 tests PASS before and after.
- Root repo:ci was executed successfully against the existing Owner code change (533 existing tests, native Owner/structure/SQL/GitHub governance); no new tests. Code commit c44d11cd08bb2c418847ab2edc4c871175fc1d48, source-only PR https://github.com/ordivon-org/ordivon/pull/2027 (OPEN / protected auto-merge requested at review time). SOURCE_COMMITTED is not MERGED or INSTALLED.
- Scope of outside direct imports of internal build_demo remains UNKNOWN; tracked source and README have no other callers, and official documented entrypoint is python -m chaoxing_mvp.cli. The change intentionally makes lifetime ownership explicit.

## Phase qualification and actual native checks

- Phase 0: SourceCut ef17d687... and 21 Owner manifest grounded; 12 explicit criteria; **COMPLETE source intake**.
- Phase 1: FILE_AUDIT.tsv exactly reconciled against git ls-tree for that SourceCut: 5,002 unique paths, complete 64-character SHA-256 fields, 12 criterion entries; **COMPLETE mechanical inventory**, not full semantic audit.
- Phase 2: 15 severity-ranked findings grounded in code lines plus 21 Owner scoped summary; an AST-only import SCC was discarded as a misleading dynamic-cycle conclusion after inspecting Capital's conditional import; **PARTIAL semantic review** with exact remaining work.
- Phase 3: B0–B9 execution DAG and actual rollback/current-owner dependencies; **COMPLETE bounded plan**, Owner implementation work remains.
- Phase 4: Chaoxing one-file repair verified above and delivered as separate PR #2027; other Owners' open work not rewritten. **SOURCE VERIFIED, MERGE/INSTALLED not yet claimed**.
- Phase 5: This baseline, exact Native Git diff evidence and handoff delivered; existing audit-carrier root commands mise run repo:ci (**533 tests PASS**) and repo:retirement:verify (**PASS**) plus git diff --check succeeded before protected publication. No new test source or consumer. **Source acceptance only, merge and complete 5,002-file semantic closure pending.**

## Scope of module findings and unresolved work

AUDIT_REPORT.md contains path/line/criteria/action/risk for the highest-evidence findings and a 21-Owner source slice table. A filesystem/hash inventory is not evidence that every function's semantics, dynamic loader and external consumer have been individually audited. Future Owner-specific reviews must continue using the existing source list or a fresh Git projection, not treat this artifact as a permanent code database.

**Owned follow-up:** Host PG snapshot continuity and consumers; Harness legacy store/currentness vs PG transition, huge Run loop only if deletion test passes; Gateway temporary schema drift shim only after current installed Runtime; Artifact claim-specific positive evidence under existing #1974; Distribution and Workstation have parallel valid historical-retirement work; Media/Game/Capital/Network/Security require their own installed/consumer proof, not a broad speculative rewrite.

**Cross-Agent handoff template:** STATUS; OWNER; source SHA; path:line; current consumer; observed defect/counterexample; decision and exact risk; changed PR/sha; native verification; remaining UNKNOWN; next natural Owner action. Space thread is already established; independent peer silence does not count as approval.

## Release/rollback and source vs installed truth

The architecture audit artifact and the Chaoxing app fix belong to **different, independently revertible Git commits/PRs**, not a cross-Owner functional delivery. When each protected PR is merged, its merge SHA can be compared to main; no active package/install is changed merely by merging. For app CLI: revert the one-file source commit to restore former behavior, without pretending Git can reconstruct deleted external filesystem data. No one should revert any actual Host production history based on these docs.

**Exit condition:** The named PRs have original native CI/readback, protected main merge states and explicit residual Owner handoffs; then these audit docs may themselves retire once their unique source evidence is no longer used. No additional approval workflow, test registry, Agent monitor or data-collection job has been installed.
