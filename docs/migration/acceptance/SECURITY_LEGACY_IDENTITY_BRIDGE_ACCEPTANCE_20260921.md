# Security legacy-source identity bridge acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

## Purpose

The original Security monorepo import used the first-generation filter-rewrite migration path. Its source content was accepted, but the standalone source commit identity was not retained as a parent in the monorepo DAG.

This acceptance converts Security to the identity-preserving migration model without changing Security semantics.

## Frozen identities

- Standalone source revision: `f5db8508857ee844323f145891fb9cb832b12785`
- Original rewritten import revision: `fd72f6a175c9180606ae0c4638665d5aee91ec77`
- Navigation-overlay retirement commit: `13384ab231fae0164c849bfedfa5f1fdd61c067b`
- Zero-content source-identity attachment commit: `a827c69661b540626735a16fd4d632e4e03751a8`
- Frozen bundle: `/root/ordivon-migration-backups/2026-09-20/security.bundle`
- Bundle SHA-256: `91d92ba84c5c43e970ce86555f6d81b444561e9033e044d023ae45702f2cd329`
- Source tree: `9776ac30c6c54d0ef4931ebb43ace3e7d7adc05f`
- Accepted `platform/security` tree: `9776ac30c6c54d0ef4931ebb43ace3e7d7adc05f`

## Ownership correction

The standalone Security `mise.toml` owns tool versions:

- Python 3.14.7
- uv 0.12.16

The monorepo had appended a `tasks.verify` block to that owner file. That repository-navigation concern is now owned by the monorepo root as `security:verify`; `platform/security/mise.toml` is again byte-identical to the standalone source.

The root continues to include `platform/security` as a mise config root because the tool-version pins remain Security-owned source authority.

## Acceptance from the monorepo owner path

- exact source/worktree comparison after generated-cache cleanup — PASS
- Python tool pin projection — Python 3.14.7 / uv 0.12.16
- root `security:verify` task — PASS
- Ruff — PASS
- Security unittest suite — **57 passed, 0 failed**
- source tree == monorepo subtree tree — PASS
- standalone source commit reachable from monorepo DAG — PASS
- identity attachment content delta — zero

Ignored/generated `__pycache__` files were not treated as source drift and were removed only as disposable test cache before byte-level comparison.

## Boundary

This is a source/history and repository-navigation acceptance only. It does not change Security policy authority, Browser Security evidence authority, live services, external effects, or the retirement status of the standalone Security repository.
