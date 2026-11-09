# BASELINE_AFTER_AUDIT — 2026-11-10

## Source and scope
- Source baseline: ef17d6879d12faa61fff3bb762b0d500d73c9113 (GitHub main and local origin/main observed at Phase 0).
- Audit owner scope: 21 source Owners under tools/repo/owners.toml, root mechanics only at root. Historical files and former Owners are not current state.
- Before audit: 5,002 Git tracked paths. Full before-file manifest: INVENTORY_FILES.tsv (5,003 TSV rows including header), no false claim all files were read line by line.
- Code/runtime mutation limited to one existing Python source preflight guard. No new feature, public API, schema, PG table, source consumer, or tests.
- Current source diff includes deletion of 5 expired Runtime planning files, repair of historical cross-references and current navigation, plus 7 new **audit artifacts** requested by the user. If all 7 are committed: 5,002 - 5 + 7 = 5,004 tracked paths. The per-file inventory represents the BEFORE state intentionally.

## Concrete stock change
- DELETE: services/runtime/planning/EXECUTION_FABRIC_R1_ROADMAP.md, WINDOWS_AUTHORITY_FACTORIZATION_EXECUTION_PLAN_R1.md, WINDOWS_AUTHORITY_FACTORIZATION_LEGO_R1.json, WORKSPACE_CONSUMER_LIFECYCLE_R21_SPEC.md, WORKSPACE_CONSUMER_LIFECYCLE_R21_EXECUTION_PLAN.md.
- MODIFY: services/runtime/planning/lego-plan-r1.json removes stale retired roadmap sourceEvidence; services/runtime/formal/README.md and docs/guides/runtime-legos.md now reference current audit in real source tree.
- REPAIR: services/runtime/scripts/ordivon-runtime-pg-reclaim must reject either nonzero Git status returncode or dirty stdout before invoking native workspace.close; existing rejection outcome remains git_changed_at_close.
- KEEP: Runtime Core/MCP, Linux native PG reclaimer, active deploy/status/pressure call paths, Windows native implementation, current TLA+ models, tests, research provenance.

## Fresh source-bound verification
| Actual command | Result | Contract |
| --- | --- | --- |
| python3 tools/repo/check_owner_boundaries.py | exit 0; active=2320; seams=31; refs=38 | static owner-literal/Python import policy, not all dynamic imports |
| python3 tools/repo/check_architecture_docs.py | exit 0 | registered architecture docs only |
| python3 tools/repo/check_composition_architecture.py | exit 0 | existing Composition source evidence |
| (from services/runtime) python3 scripts/check_docs.py | exit 0 | owner documentation |
| (from services/runtime) python3 -m unittest discover -s scripts/tests -p test_pg_workspace_reclaim.py -v | 7/7 PASS | existing PG reclaim input eligibility |
| (from services/runtime) ORDIVON_RUNTIME_INSPECT=/usr/local/libexec/ordivon/ordivon-runtime-inspect python3 -m unittest discover -s scripts/tests -p test_deploy_reclaim.py -q | 75/75 PASS | existing Deploy/Reclaim with current installed test prerequisite |
| git diff --check and git diff --cached --check | exit 0 before commit | source formatting |
| Python AST parse of modified PG reclaimer | PASS | syntax only |

The first deployment suite run in a separate earlier Workspace failed due missing ORDIVON_RUNTIME_INSPECT. It was rerun with an existing native binary, not altered to pass. The successful 75 tests do not prove a changed Linux daemon has been installed.

## Installation authority remains independent
- Existing installed Linux PG reclaim SHA256: 09ee7234cc16ac68463c113018f60a6b70be734151b89f3bfcf3cc2029f85907.
- Modified Workspace source PG reclaim SHA256: bb526acff1f7a7b3de196bc95560c80e182369b04fbe166604a77968ba34c870.
- Those differ. Therefore SOURCE_PATCHED (after Git commit) may be true; INSTALLED_CURRENT and PHYSICAL_CONSUMER_ACCEPTED are NOT established. Neither Windows deployment nor production GC policy was modified by this audit.
- A bounded native checker PASS cannot be generalized to all 5,002 files or a production claim.

## Outcome against twelve criteria
- PASS scoped: natural 21 Owner mapping; existing root boundary rule at its actual literal/Python import scope; documentation/Composition checkers; Git-based reversible retirement; tests remain unchanged; no extra framework.
- PARTIAL: root layout remains partially deployed STRUCTURE_R2; GC legacy maintenance still has consumers; Harness/Web/Artifact oversized units require a later owner-native internal reduction; general TS/Rust dynamic dependency absence remains unproven.
- FAIL repair candidate A01: one Git-status preflight error path was corrected in source, tests passed; installed update not claimed.
- UNKNOWN: independent peer review until actual Agent replies; live Windows source truth; every unreviewed file’s detailed semantic compliance.

## Cross-agent handoff
Host Space requests seq 25965, 25966 include SOURCE and exact finding requests. They prove only message admission, not that another Agent reviewed/approved code. The eventual PR/merge/production status must be read back separately and recorded in its source-linked GitHub record. No new audit process is created.

## GitHub and collaboration status readback for this source publication

- Implemented/refactor source commit: 3468c5f28f5efd28fbc3043140e2d41bec840615.
- Actual-source-graph audit follow-up: 7913be69b6c61bdd5f504259f04725ff129ffb1f.
- GitHub PR #2028: https://github.com/ordivon-org/ordivon/pull/2028, OPEN / MERGEABLE with gated auto-merge enabled; external CodeQL jobs were QUEUED at last read-back. No claim of merge or install.
- Superseded additive Draft PR #1998: CLOSED with GitHub confirmation; historical branch/data remains accessible.
- Host Space final handoff #25988 (whole-system audit) and #25989 (Runtime) committed; independent peer reply was still absent in these two topics after #25989.
