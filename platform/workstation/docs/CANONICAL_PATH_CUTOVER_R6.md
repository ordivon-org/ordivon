# Workstation v2 canonical repository path cutover — R6

Date: 2026-09-14

Canonical physical repository: `/root/projects/ordivon-workstation-v2`.

The former path `/root/projects/ordivon-operations-v2` is retained only as a temporary filesystem symlink compatibility alias because older open Ordivon Runtime Git worktrees contain absolute `.git/worktrees/...` references into that path. New source/config/recovery/provider coordinates must use the Workstation v2 path. The alias is not an owner or canonical source and can be removed after the older Runtime workspaces are closed or repaired.

The cutover includes the Cloudflare provider default/release/GC working path and the Workstation recovery `control_repository`. Immutable historical research/evidence snapshots that recorded the old path are provenance and are deliberately not rewritten.
## Executed cutover receipt

The physical cutover completed on 2026-09-14. `/root/projects/ordivon-workstation-v2` is the real repository and `/root/projects/ordivon-operations-v2` is a symlink to it for older open Runtime worktrees only. A fresh Runtime workspace was successfully opened directly from the new canonical path.

Cloudflare live realization was reinstalled from the new provider path: `ordivon-edge-gc.service` now has `WorkingDirectory=/root/projects/ordivon-workstation-v2/providers/cloudflare`, and the installed GC/release tools use that same provider root. The timer remained enabled and active.

Recovery generation `workstation-recovery://git/938915ae4f83d20fdd2ea374abc21ca33d3e277c` was provisioned detached, inspected, then atomically activated. Its recovery contract digest is `sha256:2c2a2979b51afe1bbbaf535218a7e66da893209c57db289feeb9bdc023e6b4c1`; `--verify-current` returned PASS with `controlRepository=/root/projects/ordivon-workstation-v2`.

A post-cutover scan over live systemd units, installed operational tools, and the active recovery surface found zero references to the former path. Historical immutable evidence and older inactive recovery generations are intentionally not rewritten.
