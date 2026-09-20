# Harness Current-Source Supersession Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: `services/harness` source/history relocation only. This record does not perform or authorize production cutover, deployment replacement, durable-state migration, or old-repository retirement.

## Source freeze

- Previous imported revision: `109b96c4b113412ad04357bd4fbdca2b374fcc73`
- Previous imported tree: `248e8bbe1dff42d80e08118200ddde0364f321df`
- Common source base: `f747f6d3f513e76530d9777725a6727351c47dc8`
- Frozen current source revision: `b2823f38d1d46360a4df058fb834b99b2d0b34df`
- Frozen current source tree: `d07369af2a8e52746cb9f47ebd48343c1794c4ae`
- Frozen source ref: `refs/heads/migration/monorepo-current-20260921`
- Bundle: `/root/ordivon-migration-backups/2026-09-21-harness-current/harness.bundle`
- Bundle SHA-256: `5fd652b891f6262d2453c83d117903b781096e42efc28d8d011a86c63d433b29`

## Supersession identity

The earlier monorepo import used a migration-only source branch. Current Harness main and that migration branch both descend from `f747f6d3...`, so this is an explicit identity-preserving **supersession**, not a fabricated fast-forward.

- supersession merge: `eddf154af721885022dde97559d2eb6b3471f8a8`
- old imported revision remains reachable in the monorepo DAG;
- frozen current source revision is a second parent of the supersession history;
- `services/harness` at the supersession merge is tree-identical to the frozen current source;
- the original `docs/migration/receipts/harness.md` remained byte-identical;
- the new supersession receipt is additive.

## Canonical-path acceptance

Acceptance was executed from the actual monorepo owner path `services/harness/`, not from the standalone source repository.

First pass:

- Python: 3.14.7
- `uv lock --check`: PASS
- `uv sync --locked`: PASS
- compileall: PASS
- Ruff: PASS
- pytest: **919 passed**
- subtests: **156 passed**
- dependency contract: PASS
- documentation contract: PASS
- evidence contract: PASS (`historical_receipts=89 verified_receipts=1`)
- deterministic demo: PASS
- pip-audit: **0 known vulnerabilities**

Cold-start pass:

- fresh owner environment: PASS
- pytest: **919 passed**
- subtests: **156 passed**
- cold-start result: PASS
- `git diff --check`: PASS

Final canonical-path gate: `overall=0`.

## Evidence-currentness correction

The migration required one semantic portability fix: Harness evidence/currentness code previously assumed owner root equals Git root. It now resolves owner-relative Git paths per revision, so historical standalone commits and current monorepo commits can be compared without treating pure relocation as implementation drift.

The fix is covered by a synthetic identity-preserving relocation regression and by the complete canonical-path acceptance above.

## Boundary

`ACCEPTED_SOURCE_ONLY` means the source/history relocation is accepted. It does not claim that live Harness consumers, deployed services, browser carriers, or production state have been cut over to the monorepo.
