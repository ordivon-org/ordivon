# Workstation v2 canonical repository path cutover — R6

Date: 2026-09-14

Canonical physical repository: `/root/projects/ordivon-workstation-v2`.

The former path `/root/projects/ordivon-operations-v2` is retained only as a temporary filesystem symlink compatibility alias because older open Ordivon Runtime Git worktrees contain absolute `.git/worktrees/...` references into that path. New source/config/recovery/provider coordinates must use the Workstation v2 path. The alias is not an owner or canonical source and can be removed after the older Runtime workspaces are closed or repaired.

The cutover includes the Cloudflare provider default/release/GC working path and the Workstation recovery `control_repository`. Immutable historical research/evidence snapshots that recorded the old path are provenance and are deliberately not rewritten.
