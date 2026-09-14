# Owner capsule recovery

Status: **Operations/Data Recovery substrate; owner semantics remain external**.

Workstation v2 owns generic scheduling and Restic transport for domain-native recovery capsules. The owner exporter remains the authority for capsule construction and verification; this substrate does not interpret Finance state or become Market Capital authority.

## Daily critical path

`owner-capsule-recovery --owner <owner> --backup` performs only:

1. provider-native stale-lock cleanup with ordinary `restic unlock` (never `--remove-all`);
2. owner exporter `--export` into an isolated staging root;
3. generic byte/topology identity of the resulting capsule;
4. one tagged Restic backup;
5. exact snapshot-ID read-back into an isolated restore target;
6. generic identity comparison plus owner exporter `--verify`;
7. durable success/attempt receipts.

The daily path deliberately does **not** run retention/prune or a full repository check.

## Maintenance paths

Retention is separate: `--retention` runs tagged `restic forget --keep-last ... --prune` under the shared recovery-operation lock. Repository verification is separate: `--check` runs `restic check`. The supplied systemd timers schedule daily backup/read-back, weekly retention/prune, and monthly full check independently.

All three paths serialize on `/run/lock/ordivon-semantic-recovery.lock`, shared with the existing Workstation semantic-recovery job, so one Restic repository maintenance operation cannot overlap another Workstation recovery operation.

## Finance migration

`owner_capsules.finance` in `recovery/recovery.toml` points to the already admitted state-compatible Finance recovery exporter and the existing Restic repository/snapshot tag. No credential contents live in the repository; the config names only the root-only password-file path.

The successor must pass a real backup/read-back and exact isolated restore test before the historical `ordivon-finance-recovery-custody.*` timer/helper/config are retired. Historical snapshots remain in the same Restic repository and are not rewritten.
