# Workstation recovery retention

- Current immutable generation: `607f41f57b0de9539859bf87927f3be325603d9c`
- Operations documentation commit: `144eae1f4ed7ef556e4bc78db540a5299ee06c63`
- Assessed: 2026-09-14
- Disposition: **RETAIN_MINIMAL_RECOVERY**

## Decision

The scheduled Workstation recovery capability survives the Workstation E2E retirement because it has a concrete current consequence: disaster-recovery snapshots of source/state plus semantic recovery material. It is not a general workstation configuration owner.

The current systemd timer is loaded, enabled and active/waiting with a daily ~03:30 schedule. The oneshot service executes an immutable generation launcher under `/opt/ordivon-workstation-recovery/current`; systemd does not execute the mutable `/root/workstation-lab` source tree. The latest observed completed run succeeded.

At assessment time the primary Restic repository held 14 snapshots, with latest timestamp 2026-09-13 03:41:36 +08:00. The same run produced a completed semantic-recovery record covering 30 Git repositories and 12 direct witnesses.

## Boundary

Operations owns the generic systemd scheduling substrate only. The immutable generation owns its exact backup/recovery procedure until explicitly replaced. Restic owns repository mechanics; source repositories and owner-native stores remain semantic authorities; restore acceptance remains owner-specific.

The generation currently names `/root/workstation-lab` as a protected control repository. That is a backup/control-data relationship, not source-code execution. As workstation-lab residuals are extracted, a future generation should revise the protected-source set rather than preserve the repository forever.

## Cost note

The latest observed run took roughly 11 minutes wall-clock time and reported a 4.6 GiB memory peak while performing backup/prune/semantic recovery. Monitor and optimize that policy if it creates machine pressure, but do not delete a proven recovery capability merely to reduce project count.
