# Worktrunk: external capability candidate (read-only Git worktree presentation)

**Disposition:** KEEP_NATIVE_GIT for repo governance and Runtime. **Formal R2.1:** NOT_FORMALLY_DECLARED. This tool is a UX provider, not an Ordivon Workspace owner.

- Upstream: https://github.com/max-sixty/worktrunk (observed main 181f17a7942b8e944f9c03c0f81b70e95a3b1a9b).
- Reviewed version: v0.81.0; exact official archive SHA-256 and reviewed binary SHA-256 in catalogs/capabilities/evidence/worktrunk-candidate-20261106.json.
- License: MIT OR Apache-2.0, verified from LICENSE body (the GitHub API returned NOASSERTION).

**Capability:** scoped read-only branch/path/dirty/detached worktree listing. **Method:** branch-centric presentation over an independently authoritative native Git state; do not infer state transition authorization from the display.

**Actual consumer:** tools/repo/exhaustive_coverage.py::independent_scope_frontier. The same existing Repo consumer was replayed in an independent disposable Git fixture with native Git and Worktrunk-derived porcelain. Complete consumer output matched. A forged locator was non-equivalent; Worktrunk lacked proved prunable metadata, so the candidate projection was withheld. Native consumer readback was restored.

A separate read-only real Ordivon source shadow observed 145 worktrees (107 detached), with matching counts, paths, branch and detached state, followed by native readback. This is a fixed observation, not proof of permanent runtime equivalence.

Single currently consumed P2 result: catalogs/capabilities/evidence/worktrunk-repo-owner-consumer-shadow-20261106.json. Reproduction uses catalogs/capabilities/scripts/compare_worktrunk_owner_consumer.py and the pinned executable.

**Decision:** keep native Git, with no global install, Runtime lifecycle switch, code deletion, or formal R2.1 registration. Adding a custom Worktrunk translation adapter that still needs native Git cannot demonstrate maintenance cost reduction. The early redundant fixture/script is available in Git history, not duplicated in the live working tree.
