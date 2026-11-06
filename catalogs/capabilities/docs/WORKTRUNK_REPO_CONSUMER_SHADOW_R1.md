# Worktrunk / Repo Consumer — scoped P2 substitution trial

Consumer: tools/repo/exhaustive_coverage.py::independent_scope_frontier. Owner: repository governance. Scope: read-only checkout metadata; Runtime continues to own all Job/Workspace lifecycle effects.

## Reproduction
Obtain and independently verify the exact official Worktrunk v0.81.0 binary and release archive SHA-256. Run:
    python3 catalogs/capabilities/scripts/compare_worktrunk_owner_consumer.py --binary /path/to/wt --output /tmp/consumer-shadow.json

The script builds two independent temporary Git repositories and a linked worktree. It invokes the **existing consumer code** with native Git, injects candidate-derived read-only porcelain under a scoped Python mock, invokes that *same* consumer, checks full-result parity, then restores and rechecks native behavior. It does not edit the production consumer.

## Observed experimental results
- Candidate/native fixture porcelain bytes: equal; actual consumer output: equal.
- Forged candidate path: detected as non-equivalent.
- Stale linked-worktree metadata: native Git reports prunable; Worktrunk candidate **blocked** because its representation lacks proven prunable equivalence.
- Consumer rollback to native implementation: successful after negative test; all fixture directories retired.
- Independent shadow observation of live Ordivon source: 145 Git worktrees, 107 detached; candidate/native path, branch, detached parity, and repeat native readback all match. Active source may change independently.

Evidence:
- catalogs/capabilities/evidence/worktrunk-repo-owner-consumer-shadow-20261106.json
- catalogs/capabilities/evidence/worktrunk-real-ordivon-git-consumer-20261106.json

## Decision
KEEP_NATIVE_GIT for Repo governance and Runtime. This trial qualifies Worktrunk only as a disposable, gated *read-only* representation for this consumer, not lifecycle replacement or production installation. A permanent adapter that still depends on Git to verify prunable facts cannot count as custom-code elimination. No Owner production path was switched, and verified retired custom LOC remains zero. Do not infer cleanup authority, R2.1 admission, deployment or a system-wide substitution from this report.
