# Workstation Current-Source Update Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: identity-preserving linear source update of `platform/workstation`. This record does not authorize production cutover, service restart, credential migration, or retirement of `/root/workstation-lab`.

## Source freeze

- Source repository: `/root/projects/ordivon-workstation-v2`
- Previous imported source revision: `1ee414a9fcf40ce69c8fe53235134e3f55a5eee7`
- Current source revision: `add96799759383ea0b5b318d9aa5a7c53c7d00bd`
- Source ref in frozen bundle: `refs/heads/main`
- Frozen bundle: `/root/ordivon-migration-backups/2026-09-21-workstation-current/workstation.bundle`
- Bundle SHA-256: `3ef6daef291ae478c798106de343bff9e5cb35ccad2007c0fe10a11fd4642715`
- Identity-preserving update merge: `34e81229f43ef2bada963970c98d6c9226154a32`
- Target path: `platform/workstation`

The source main was clean at freeze time. Bundle creation changed neither the source working tree nor source refs.

## Append-only migration evidence

The update uses `tools/repo/migration/update-owner-preserve-history.sh`.

The helper was hardened before use so a linear update does not overwrite the original import provenance:

- `docs/migration/receipts/workstation.md` remains byte-identical;
- `docs/migration/receipts/workstation.commit-map` remains byte-identical;
- the update adds `workstation.update.md` and `workstation.update.commit-map`;
- local target-subtree divergence fails closed;
- source revision must descend from the previous source revision;
- the frozen bundle must advertise the exact requested source revision.

## Canonical-path acceptance

Acceptance ran from the actual monorepo path `platform/workstation/`.

### Python / owner contract

- Python 3.14.7 environment: PASS
- `uv lock --check`: PASS
- `uv sync --locked`: PASS
- Ruff: PASS
- pytest: **148 passed**
- owner subtree equals frozen source tree: PASS

### Cloudflare provider

- Node: `v26.7.0`
- pnpm: `10.33.2`
- provider `pnpm install --frozen-lockfile`: PASS
- provider `pnpm run ci`: PASS
- Wrangler dry-run: PASS
- Wrangler observed version: `4.114.0`

### Shell / IaC

- Bash syntax across tracked shell surfaces: PASS
- ShellCheck: PASS
- OpenTofu format check: PASS
- OpenTofu init/validate: PASS
- Cloudflare OpenTofu provider `5.25.0`: installed and validated

OpenTofu init added local cross-platform provider hashes to the working copy of the tracked lockfile during validation. That test-only mutation was explicitly restored from the frozen source revision before acceptance was committed; no source byte drift was admitted.

### Final

- update receipt identity: PASS
- `git diff --check`: PASS
- acceptance gate: `overall=0`

## Workstation-lab boundary

This update does **not** absorb `/root/workstation-lab`.

The current Workstation v2 owner already contains the execution-node desired-state, inventory, exact node-local binding, recovery, and provider-realization responsibilities that survived migration. The remaining lab blockers observed in the same audit are Creative Library / preservation and backup-data custody, not a second Workstation runtime authority.

Retiring the lab therefore requires a separate residual-owner and recovery-custody gate.
