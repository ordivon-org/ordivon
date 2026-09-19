# Project repository cleanup — Wave 1 — 2026-09-14

Status: **COMPLETED** for non-Research retired repositories selected by `migrations/records/project-repo-census-20260914.md`.

## Result

The active `/root/projects` surface was reduced from 30 Git project directories to 17 project directories (excluding `.worktrees` and the `workstation` compatibility symlink).

Thirteen repositories with explicit retired/archived standing were moved, not deleted, to:

`/var/lib/ordivon/retired/source-repos/2026-09-14/`

Moved repositories:

- `ordivon-host`
- `ordivon-market-capital-v2`
- `ordivon-security`
- `ordivon-workstation-v2`
- `codex-harness-mcp`
- `ordivon-atlas`
- `ordivon-computational-possibility`
- `ordivon-computing`
- `ordivon-human`
- `ordivon-interlocus`
- `ordivon-normative`
- `ordivon-scd`
- `ordivon-world`

The archive root contains `MANIFEST.tsv` with original path, archive path, exact HEAD, remote (when configured), and archive timestamp.

## Workspace cleanup

Clean Runtime workspaces sourced from retired repositories were closed first using Runtime's workspace close boundary. No dirty workspace was discarded directly.

Seven non-Research dirty residual workspaces were preserved before force-close under:

`/var/lib/ordivon/retired/workspace-residuals/2026-09-14/<workspaceId>/`

Each preservation directory contains the exact base HEAD, porcelain status, binary tracked patch, untracked-file archive when present, diff statistics, and SHA-256 manifest values.

Preserved residuals:

- `ws-host-pg-r33-integration-latest-20260911`
- `ws-host-task-adopt-serializer-r1-20260911`
- `ws-close-computational-possibility-20260913`
- `ws-human-social-adoption-archaeology-human-r1-20260911`
- `ws-close-interlocus-20260913`
- `ws-close-normative-20260913`
- `ws-tech-selection-r2-world-do-probe-20260910`

The two Host v1 residuals and the Human residual contained tracked source/document modifications. The Computational Possibility, Interlocus and Normative closeout residuals were untracked Python cache material; the World residual contained untracked experiment material. Preservation was still performed uniformly before closure.

A clean ordinary Git worktree at `/root/worktrees/ordivon-security-harness-tool-observation-a02-20260909` was removed through Git worktree removal before Security v1 was archived.

Stale missing Git-worktree metadata for the retired repositories was pruned before physical movement.

## Why `ordivon-research` remains under `/root/projects`

`ordivon-research` is architecturally retired as the forward Research E2E authority, but it still has multiple physical Runtime workspaces containing Paper-1 and historical research residuals. Several are dirty, including current 2026-09-14 Paper-1 reentry/reconciliation workspaces.

Therefore:

`RESEARCH_V1_ARCHITECTURAL_RETIREMENT = COMPLETE`

but

`RESEARCH_V1_PHYSICAL_LOCAL_EVICTION = BLOCKED_BY_WORKSPACE_RESIDUALS`

Research v1 must remain physically available until those workspaces are migrated/preserved/reconciled. This does not restore Research v1's forward authority; forward Research E2E remains `ordivon-research-v2`.

## Remaining active project directories after Wave 1

- `ordivon-artifact-v2`
- `ordivon-distribution-v2`
- `ordivon-finance`
- `ordivon-game`
- `ordivon-harness`
- `ordivon-host-v2`
- `ordivon-market-capital-next`
- `ordivon-media`
- `ordivon-network-v2`
- `ordivon-next`
- `ordivon-operations-v2`
- `ordivon-paper2`
- `ordivon-research`
- `ordivon-research-v2`
- `ordivon-runtime`
- `ordivon-security-v2`
- `ordivon-web`

This physical list is intentionally broader than the three Ordivon core primitives. Domain owners, research projects and external/product carriers remain separate while they have real current responsibilities.

## Remaining cleanup work

1. Reconcile and preserve old dirty `ordivon-research` workspaces without interrupting current Paper-1 work.
2. Move Research v1 out of `/root/projects` once its physical workspace count reaches zero.
3. Census consumers of `/root/projects/workstation -> /root/workstation-lab`; remove that compatibility symlink only after zero-current-consumer proof.
4. Reassess `ordivon-finance` only after Market Capital Next and other mature/provider-native owners prove complete consumer cutover; Finance remains explicitly `DO NOT ARCHIVE YET`.

No current architectural authority is granted by local archive location.