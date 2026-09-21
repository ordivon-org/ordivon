# Network legacy-source identity bridge acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

## Authority reconstruction

The original Network import receipt selected `9aec70bbfa3c8847dbd52c03a939c61f45e2f338`, not the then-current standalone `main`. Source-DAG inspection showed that:

`869b73a7859bead08dc9aaadb70a74e12ee59b2f` → `9aec70bbfa3c8847dbd52c03a939c61f45e2f338`

and the selected commit is the single source commit:

`decouple Network Browserless from Agent Automation lifecycle`

The four apparent semantic differences between the old standalone `main` and the monorepo were therefore not monorepo-private patches. They were already source-owned by `9aec70bbfa3c8847dbd52c03a939c61f45e2f338`: Network owns the Browserless provider/path lifecycle but does not restart, require, or own upper-layer Agent Automation / Temporal consumer services.

After validating that source revision from both the monorepo path and standalone repository, standalone `main` was fast-forwarded to `9aec70bbfa3c8847dbd52c03a939c61f45e2f338`. No history rewrite or force update was used.

## Repository-navigation correction

The original monorepo import had added `platform/network/mise.toml` containing only a `verify` task. Standalone Network has no `mise.toml`; therefore this was pure monorepo navigation leakage.

The task is now root-owned as `network:verify` with `dir = "platform/network"`, and the monorepo root no longer lists `platform/network` as a mise config root.

After removal, `platform/network` is tree-identical to `ordivon-network-v2@9aec70bbfa3c8847dbd52c03a939c61f45e2f338`.

## Frozen identities

- Previous standalone main: `869b73a7859bead08dc9aaadb70a74e12ee59b2f`
- Accepted/current source revision: `9aec70bbfa3c8847dbd52c03a939c61f45e2f338`
- Original rewritten import revision: `ffd138649e1c9719c26238cf940fc7f2c03b56ff`
- Navigation-overlay retirement commit: `1365f45cf93ec0b568930ec47d149d144f0ab908`
- Zero-content source-identity attachment commit: `4c2be991fbe24ec953b5971cea33dd8c1a581224`
- Frozen bundle: `/root/ordivon-migration-backups/2026-09-20/network.bundle`
- Bundle SHA-256: `4033ac574b7d9bc0215014bb6a2879dbcef49675977160900ec16df690bdaa06`
- Source tree: `ba601ac2cce2e7ac88a960cfc4d4c3edd534a533`
- Accepted `platform/network` tree: `ba601ac2cce2e7ac88a960cfc4d4c3edd534a533`

## Acceptance

From the actual monorepo owner path, root `network:verify` ran `task all:validate` and passed:

- generic sing-box configuration validation
- Surfshark provider profile validation
- Finance consumer graph/authority validation
- systemd unit verification
- blackbox exporter configuration validation
- Prometheus configuration validation

The same `task all:validate` passed again after standalone `main` was fast-forwarded to the accepted source revision.

Additional gates:

- exact source/worktree comparison — PASS
- source tree == monorepo subtree tree — PASS
- source commit identity reachable from monorepo DAG — PASS
- identity-attachment content delta — zero
- standalone main update — ff-only

## Boundary

This acceptance covers source/history and repository-navigation convergence only. It does not authorize a Network production cutover, provider rotation, Browserless cutover, Finance cutover, external effect, or standalone-repository retirement.
