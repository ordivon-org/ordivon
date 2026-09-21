# Host legacy-source identity bridge acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

## Purpose

The original Host monorepo import used the first-generation rewritten-history path. The accepted owner subtree already matched the current standalone Host source exactly, but the standalone source commit identity was not reachable in the monorepo DAG.

This acceptance attaches that exact source identity without changing Host content.

## Frozen identities

- Standalone source revision: a95a8e112edfbe85582ff8e6fa25bb268038ea48
- Original rewritten import revision: ba7e33b5784e5a1699f27786fad27e5b1d7e9157
- Zero-content source-identity attachment commit: 0415ecfce6552b899c4ec1d2a5981a8314b4e502
- Frozen bundle: /root/ordivon-migration-backups/2026-09-20/host.bundle
- Bundle SHA-256: 21af43c3d139a2e1ebfe8215f59ba239de943583c716f574ad5d23fbab0db256
- Source tree: 9c2ea9690d790b9dbe83b57eae34f0a53062f79f
- Accepted services/host tree: 9c2ea9690d790b9dbe83b57eae34f0a53062f79f

## Monorepo-path acceptance

The ordinary Host CI-equivalent path executed from services/host:

- uv lock --check — PASS
- uv sync --locked — PASS
- Ruff — PASS
- pytest — **18 passed, 18 skipped**

The skipped tests are PostgreSQL integration tests guarded by ORDIVON_HOST_V2_TEST_DSN; they were not treated as full integration acceptance.

A fresh isolated PostgreSQL **18.6 / UTF-8** cluster was then created under a disposable migration path. The empty database had zero public tables, Alembic advanced through 0001→0002→0003→0004→0005, and:

- Alembic current — 0005 (head)
- complete pytest suite — **36 passed, 0 skipped**
- Ruff — PASS
- git diff --check — PASS

The disposable cluster was stopped and removed after the run. No production Host database was read or mutated.

## History acceptance

- source tree == monorepo Host subtree tree — PASS
- standalone source commit reachable from monorepo DAG — PASS
- identity-attachment content delta — zero

## Boundary

This is source/history migration acceptance only. It does not change Host database authority, production deployment state, Task/Board semantics, or standalone repository retirement status.
