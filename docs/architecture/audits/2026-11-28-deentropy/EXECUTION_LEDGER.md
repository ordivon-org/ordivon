# Architecture De-entropy Execution Ledger — 2026-11-28

This is the bounded execution ledger for the current repository architecture de-entropy program. It is a coordination/progress artifact, **not** a second architecture authority, runtime registry, approval service, or replacement for Git, Owner manifests, public contracts, tests, or deployment evidence.

- Source baseline at ledger creation: `7d785552786a75bc5fdcfaf61b3d2110f4b3ba83`
- Canonical Owner/boundary sources remain `tools/repo/owners.toml`, `tools/repo/dependency_contracts.toml`, implementation contracts, and each Owner's native verifier.
- Publication remains GitHub protected `main` + existing Merge Queue.
- The historical `docs/architecture/audits/2026-11-10-brownfield/` package remains an immutable dated source audit; current execution state is not appended to that historical snapshot.
- Global architecture decisions remain indexed by `docs/architecture/DECISIONS.md`. The local decisions below do not create new global ADRs because they resolve implementation duplication without changing a public architecture contract.

## Progress

| Batch | Scope | Change | Verification | Publication standing |
| --- | --- | --- | --- | --- |
| B01 | Security | One file-byte SHA-256 implementation with explicit raw-hex and `sha256:` representations; migrated production callers and retained only compatibility aliases | Fresh worktree: Security native verify PASS; 100 unittest, 79/79 OPA, 158 AuthZEN; duplicate file-hash implementation scan = 0 | Composite PR #3021 CLOSED without merge after being superseded. Owner-scoped PR #3017 is the stronger successor (also covers EvidenceRef digest+size authority) and has Merge Queue requested. |
| B02 | Capital | One Binance generated-SDK model/oneOf normalization adapter shared by public/private USDⓈ-M capture; removed duplicated private helpers and representation leakage | Fresh worktree: Capital native verify PASS; 1223 passed, 52 skipped, 39 deselected, 243 subtests; Lean/Z3/CrossHair obligations PASS | Composite PR #3021 CLOSED without merge after being superseded. Owner-scoped PR #3033 extracts the stronger Capital commit on current main and has Merge Queue requested. |
| B03 | Experimental Episode Store | Deleted two local canonical JSON digest implementations and reused existing public `ordivon_composition.canonical_digest` already consumed by sibling projection/backfill code | Fresh worktree: episode-store native verify PASS; 46 passed, 19 skipped; Owner boundary check PASS | PR #3025 OPEN and reported by GitHub CLI as already queued to merge; head `3fa69eb36718627a1642d964de3b1e629fe95b8c` |
| B04 | Gateway source-contract tooling | Removed the undocumented `uv --offline` cache-warmness prerequisite from the Host↔Gateway native source checker while retaining `--locked`; added an execution-contract regression test | Fresh worktree with unique empty `UV_CACHE_DIR`: checker PASS; Gateway native verify PASS; R8/R9 tests 18 PASS; four root architecture gates PASS. Formal model standing remains UNKNOWN because Runtime-owned TLA+ 1.7.4 bootstrap hit upstream TLS EOF. | PR #3034 OPEN; Merge Queue requested; head `6b549420eb7185fba69add7a0c6b594cf156569b` |

A SOURCE/PASS/PR observation is not a MERGED, INSTALLED, EXECUTED, or domain-consumed claim. Update this table only after reading the corresponding authority.

## Decision notes

### D01 — Prefer same-Owner canonicalization; do not create cross-Owner DRY coupling

Exact duplicated mechanics are candidates only after checking deployment and consumer boundaries. Gateway/Host release verifiers were **not** unified merely because some parsing mechanics match: independently shipped verifier packages need failure/deployment isolation. Security file hashing and Capital Binance SDK normalization were unified because the duplicate responsibility lived inside one natural Owner and all known callers were migrated.

### D02 — Preserve distinct representations behind explicit names

Security needs both raw hexadecimal SHA-256 and qualified `sha256:<hex>` values. Canonicalization therefore shares byte hashing while keeping two named representation functions instead of forcing semantically different wire forms into one ambiguous API.

### D03 — Reuse an existing public authority before adding a helper

The Episode Store already depends on Composition and sibling code already consumes `ordivon_composition.canonical_digest`. Its duplicate digest functions were deleted rather than moved into another local utility. The shared Composition implementation preserves the valid-JSON byte identity while adding fail-closed validation for invalid representations.

### D04 — Historical audits stay historical

The 2026-11-10 brownfield audit is source-cut evidence and explicitly warns against becoming an evergreen registry. Current progress is recorded here rather than mutating that historical baseline. This ledger itself must stay small and may be retired when the bounded program closes.

### D05 — Tool availability and cache qualification are different facts

A present executable is not sufficient evidence that a source-observation subprocess can run, and a cold dependency cache is not evidence that the executable or source capability is absent. The Host↔Gateway checker now keeps lockfile qualification while allowing exact locked packages to populate a fresh cache. External formal inputs remain separately qualified by path and digest.

### D06 — Controlled wire asymmetry can be compatibility, not entropy

The Gateway advertises a historically wider `work.list.limit` integer schema while rejecting out-of-range values inside the Tool body to preserve the original structured `OWNER_CALL_FAILED` envelope. Tightening the advertised schema would move rejection into SDK validation and change the public error contract. The asymmetry is therefore retained and explicitly falsified rather than mechanically normalized.

## Optimization task pool

The queue below records only observed candidates. A candidate is **not** permission to refactor and does not imply a defect.

| Priority | Candidate | Current standing | Next falsifier / qualification |
| --- | --- | --- | --- |
| P0 | Security successor PR #3017 integration/readback | IN PROGRESS | Required GitHub checks + Merge Queue final main readback; #3021 is intentionally superseded, not merged |
| P0 | Capital successor PR #3033 integration/readback | IN PROGRESS | Required GitHub checks + Merge Queue final main readback; reject reintroduction of weaker #2993/#3021 parallel variants |
| P0 | Episode Store PR #3025 integration/readback | QUEUED | Merge Queue final main readback |
| P0 | Gateway cold-cache checker PR #3034 integration/readback | IN PROGRESS | Required checks + Merge Queue final main readback; formal status remains independent of external TLA+ JAR acquisition |
| P1 | Harness repeated digest/receipt helpers and large lifecycle modules | DEFER_COLLISION | Multiple active Harness worktrees/jobs observed; re-scan after overlap clears, then use actual callers + `harness:verify` |
| P1 | Artifact repeated file-hash/tree-digest helpers | DEFER_COLLISION | Multiple active Artifact worktrees and current source churn; do not create a competing common utility without package/deployment proof |
| P1 | Runtime backup/restore file-hash duplication | DEFER_HIGH_RISK_COLLISION | Runtime is active physical-effect authority; inspect backup/restore contract and active PRs before any edit; require `runtime:verify` |
| P2 | Workstation duplicated materialization entrypoint mechanics | REVIEW_ONLY | Determine whether provider-specific entrypoints are intentionally independently deployable before extracting anything |
| P2 | Host migration-local version helpers | KEEP_UNLESS_COST_PROVEN | Migration files are immutable/history-oriented; duplicated small helpers alone do not justify shared runtime dependency |
| P2 | Remaining exact/near duplicate production functions in low-conflict Owners | OPEN_SCAN | Continue normalized AST/source + real-caller scan; prioritize deletion/reuse, reject false-positive semantic merges |

## Execution invariants

1. Start every batch from current protected `origin/main` in an isolated Runtime worktree.
2. Inspect active worktrees/PR overlap before mutation; defer hot overlapping Owners rather than create merge conflict entropy.
3. Prefer DELETE-CUSTOM → REUSE → COMPOSE → IMPLEMENT.
4. Do not extract a shared module solely to reduce duplicate lines; require one responsibility, one natural ownership boundary, and real callers.
5. Establish focused behavior tests first, migrate every known caller, delete replaced implementations, then add a bounded anti-regression constraint where it protects an actual canonicalization.
6. Run the affected Owner's native verify task and independent fresh-worktree review before publication.
7. Rebase/replay when protected `main` changes; GitHub Merge Queue mechanical qualification does not substitute for semantic replay.
8. Keep UNKNOWN distinct from FALSE/PASS. PR green is not installed/domain success.
9. Every effective source batch is independently committed and published through normal protected-main flow.
10. Remove or collapse this ledger when it stops reducing coordination cost.
