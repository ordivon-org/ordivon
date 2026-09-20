# Skill MCP R3.1 Contract Ergonomics Implementation Plan

**Goal:** Remove invocation-view snapshot friction without weakening R3 fail-closed content, package, or visibility boundaries.

**Architecture:** Keep the existing four-tool compatibility surface and existing `snapshotRevision` wire field. Make its invocation-view scope explicit in metadata, and let `skills.read` validate an expected snapshot against either current implicit or current explicit view for the same context. Exact resource identity remains fenced independently by instruction digest and package revision.

**Tech Stack:** Python 3.12, unittest, MCP 2.0.0, existing Ordivon SkillCatalog/Skills MCP bridge.

**Global Constraints:**
- No new tool or transport standard.
- Preserve SEP-2640 raw resource semantics.
- Preserve R3 `ADVISORY_SANITIZED` model-facing projection.
- Preserve `instructionAuthority=ADVISORY` and risk gating.
- Preserve stale-snapshot fail-closed behavior.
- Backward-compatible existing `snapshotRevision` inputs/outputs.

### Task 1: Snapshot-view compatibility
- [ ] Add a failing test proving `skills.list` implicit snapshot can fence `skills.read` for the listed Skill.
- [ ] Add a failing test proving an old implicit snapshot is rejected after the visible view changes.
- [ ] Implement a catalog helper that validates read snapshots against current implicit or explicit views only.
- [ ] Keep instruction/package digest fences unchanged.

### Task 2: Contract clarity
- [ ] Add failing assertions for `snapshotInvocationMode` on list/search/resolve responses.
- [ ] Emit `snapshotInvocationMode=implicit` for list/search and the requested mode for resolve.
- [ ] Document that `skills.read` accepts current implicit/explicit view snapshots while resource digests bind exact bytes.

### Task 3: Verification
- [ ] Run focused R3.1 tests and observe RED before implementation.
- [ ] Run focused Skill MCP tests after implementation.
- [ ] Run Ruff and `git diff --check`.
- [ ] Run full repository unittest suite in the composed MCP dependency environment.
- [ ] Review diff for accidental authority/security weakening before commit/release.
