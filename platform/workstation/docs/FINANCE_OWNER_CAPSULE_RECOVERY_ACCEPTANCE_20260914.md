# Finance owner-capsule recovery migration acceptance — 2026-09-14

Status: **PASS / LIVE CARRIER CUT OVER TO OPERATIONS DATA RECOVERY**.

## Scope

This acceptance covers only the physical recovery-custody mechanism for the already-retired Finance source owner. Finance/Market Capital semantics remain outside Workstation v2. The Finance exporter remains the owner-native authority for capsule construction and verification; Workstation v2 owns generic scheduling and Restic transport.

## Successor implementation

Canonical source: `ordivon-workstation-v2`.

Accepted implementation commit:

`fbd09f5d7212d179ed78173c07cc774e44524f67`

The current immutable recovery generation is:

`workstation-recovery://git/fbd09f5d7212d179ed78173c07cc774e44524f67`

`recovery/workstation_recovery_generation.py --verify-current` returned PASS. The generation exposes the content-addressed launcher:

`/opt/ordivon-workstation-recovery/current/bin/owner-capsule-recovery`

Owner-capsule semantics are declarative in `recovery/recovery.toml`; `owner_capsules.finance` selects the state-compatible rebound Finance exporter and the existing Restic repository/tag. No credential contents are stored in source.

## Daily critical path consequence proof

A candidate generation from the same source tree performed a real Finance owner-capsule backup and exact Restic read-back before activation.

Accepted successor snapshot:

`72380e00244ca30e0472ca213d31181bd9c52d2bf3c48b1ced00d272031014d6`

Capsule evidence:

- files: `809`;
- bytes: `55,393,082`;
- capsule tree SHA-256: `7a7473e8eb172b91bb67b2171d78e1de9c5c3236689692874e4156070cfdb981`;
- transport manifest SHA-256: `16ba3d6084350fa1a5a80469f5dcc51b65d87e829bc6e48de0cb01c97764928f`;
- backup/read-back: **PASS**;
- owner exporter verification after read-back: **PASS**.

A second, independent `--restore-test --snapshot-id <exact-id>` restored that exact snapshot into an isolated temporary target and reproduced the same capsule tree digest, file count and byte count. Owner exporter verification again passed.

The daily path deliberately contains no `forget --prune` and no full `restic check`.

## Maintenance separation

Operations now schedules three independent generic owner-capsule paths:

- `ordivon-owner-capsule-backup@finance.timer` — daily backup/read-back;
- `ordivon-owner-capsule-retention@finance.timer` — weekly tagged retention/prune;
- `ordivon-owner-capsule-check@finance.timer` — monthly full Restic repository check.

At final acceptance all three were `enabled` and `active`. Observed next activations were:

- backup: `2026-09-15 04:04:44 CST`;
- retention: `2026-09-20 04:48:20 CST`;
- repository check: `2026-10-01 06:42:39 CST`.

All paths serialize through `/run/lock/ordivon-semantic-recovery.lock`. Repository preparation uses ordinary provider-native `restic unlock` for stale-lock reconciliation and never uses `--remove-all`.

## Legacy carrier retirement

The following live installed paths are absent after cutover:

- `/usr/local/libexec/ordivon/finance-recovery-custody`;
- `/etc/ordivon/finance-recovery-custody.json`;
- `/etc/systemd/system/ordivon-finance-recovery-custody.service`;
- `/etc/systemd/system/ordivon-finance-recovery-custody.timer`.

The old systemd unit names resolve `not-found` / inactive.

Historical carrier bytes are retained root-only at:

`/root/.local/state/ordivon-retired/finance-recovery-custody-20260914/`

The historical helper SHA-256 remains:

`03fbfbe2aaab81e8c6dbbdb6fc4bfc6b48ce127b2e7827e8e9659059e2581f0c`

The complete cutover receipt is:

`/root/.local/state/ordivon-retired/receipts/ordivon-finance-recovery-custody-successor-20260914.json`

and is mode `0600`.

## Preserved state/providers

The migration did not delete or recreate the underlying recovery domain:

- Finance state remains `/var/lib/ordivon/finance-state`;
- state-compatible owner exporter remains `/opt/ordivon-finance-recovery-exporter-rebound`;
- Restic repository remains `/mnt/d/wsl-backups/restic-semantic-recovery`;
- historical snapshots and lineage remain in that repository.

No financial order, transfer, withdrawal, account mutation, or other external financial write was authorized or attempted by this migration.
