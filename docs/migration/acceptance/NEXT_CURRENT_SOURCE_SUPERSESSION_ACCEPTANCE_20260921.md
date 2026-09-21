# Next current-source supersession acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: source/history synchronization of `meta/next` to the current accepted `ordivon-next/main`. This record does not authorize production deployment changes, live consumer cutover, deletion of the standalone source repository, or scientific/domain authority changes.

## Frozen identities

- Previous imported source revision: `a119ccb11d32edebe08f197a4af8f8a67f8c086f`
- Current source revision: `5e556869df0617a7da09e39ae57f646f11061689`
- Common base: `ae1ac43130f95b264d908f7c73f268809300c0ea`
- Navigation-overlay retirement commit: `cdd0fe5c3e38020feecff0c8632a4d4908e28bf5`
- Legacy source-identity attachment commit: `591487573153700c5b6953882be49931e09af31f`
- Identity-preserving supersession commit: `db750acdb1b233ab85c19c49a770c30e1d3c29b3`
- Frozen bundle: `/root/ordivon-migration-backups/2026-09-21-next-current/next.bundle`
- Bundle SHA-256: `fdd1409d7303c70a6c3be17b0e5c8fcc3edde7e1bb4f2ac5aeed7b6bed21e824`
- Current source tree: `d29ac5ff648efa790613023344fca64f12ce4ad3`
- Accepted `meta/next` tree: `d29ac5ff648efa790613023344fca64f12ce4ad3`

## Legacy import reconciliation

The original Next canary used the first-generation filter-repo import path, so the standalone source revision `a119ccb11d32edebe08f197a4af8f8a67f8c086f` was represented through a rewritten commit rather than retained as an identity-preserving parent in the monorepo DAG.

Before supersession:

1. the only monorepo-local divergence from the old source tree was `meta/next/mise.toml`;
2. that repository-navigation task was moved to the root `mise.toml`, leaving the owner subtree byte/tree-identical to the previous source;
3. a zero-content merge parent attached the exact legacy source revision to the monorepo DAG;
4. the existing tested `supersede-owner-preserve-history.sh` path then attached the current source revision and replaced `meta/next` with its exact source tree.

This converts Next from the legacy rewritten-history canary into the same identity-preserving update model already used by current Harness/Runtime migration work.

## Acceptance

Executed from the actual monorepo owner path `meta/next/`:

- `uv lock --check` — PASS
- `uv sync --locked` — PASS
- `python -m pytest` — **102 passed**
- Ruff check — PASS
- Ruff format check — PASS
- external authority catalog acceptance — PASS
- standard-native enterprise R2 acceptance — PASS
- reasoning-waist smoke on Python 3.14.7 — PASS
- Bandit scoped security gate — PASS
- governance-persistence ratchet — PASS

The accepted monorepo subtree is tree-identical to `ordivon-next@5e556869df0617a7da09e39ae57f646f11061689`.

## Boundary

`ACCEPTED_SOURCE_ONLY` means source/history synchronization is accepted. Runtime, Host, Harness, domain owners, live services, external effects, durable state, and Study scientific truth remain under their existing authorities. The standalone Next repository remains a recoverable source carrier until its retirement gate is separately accepted.
