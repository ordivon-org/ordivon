# Workstation recovery retention

Date: 2026-09-14

Status: **RETAIN MINIMAL RECOVERY / OPERATIONS OWNS SCHEDULER SUBSTRATE**

## Observed current state

- `ordivon-workstation-backup.timer`: loaded, enabled, active/waiting; daily schedule around 03:30 with randomized delay.
- `ordivon-workstation-backup.service`: oneshot, static, currently inactive between runs, last result `success`.
- execution path: `/opt/ordivon-workstation-recovery/current/bin/workstation-backup`; no systemd unit executes `/root/workstation-lab` source directly.
- current immutable generation: `607f41f57b0de9539859bf87927f3be325603d9c`.
- local recovery-generation store: about 76 MiB across five retained generations at observation time.
- primary Restic repository: `/root/backups/restic-workstation`, about 252 MiB at observation time.
- Restic snapshot census: 14 snapshots; latest observed snapshot timestamp 2026-09-13 03:41:36 +08:00.
- the 2026-09-13 run also emitted a completed semantic-recovery record covering 30 Git repositories plus 12 direct witnesses.

The current generation manifest names `/root/workstation-lab` as its control repository, and its launcher backs up that repository. This is a **data/control input relation**, not mutable source execution: systemd starts the immutable generation launcher. As `/root/workstation-lab` is further decomposed, a future recovery generation should update the protected-source set rather than preserving the historical repository forever.

## Responsibility boundary

Operations owns only generic service/timer realization and scheduling mechanics. The recovery generation continues to own the exact recovery procedure it was built with until a replacement generation is explicitly admitted. Restic owns repository mechanics; Git and owner-native stores remain the source authorities for their content; restore acceptance remains semantic-owner specific.

This capability must not expand back into a general Workstation configuration owner. It survives because disaster recovery has a real current consequence and the installed execution path is immutable.

## Operational note

The most recent observed backup run consumed roughly 11 minutes wall time and reported a 4.6 GiB memory peak while performing backup/prune/semantic recovery work. That cost is worth monitoring on this machine, but it is not evidence that the recovery capability should be deleted. Future optimization should target Restic/prune scheduling or generation contents without weakening recovery evidence.

## Revisit triggers

Rebuild or replace the current generation when:

1. the protected repository/state set changes materially after residual extraction;
2. restore acceptance proves the existing generation incomplete or stale;
3. repeated resource pressure makes the current backup/prune policy operationally unsafe; or
4. a mature replacement provides equal restore evidence with lower total complexity.
