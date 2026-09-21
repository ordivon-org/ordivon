# Capital standalone source-carrier retirement — 2026-09-21

Standing: RETIRED_ARCHIVED

The canonical Capital source owner is now only the monorepo path domains/capital.

The former physical carrier /root/projects/ordivon-market-capital-next has been deleted after proving that no Runtime workspace, Host continuity claimant, active process, system configuration, or current executable consumer required the physical directory.

## Preserved recovery state

Backup root:

/root/ordivon-migration-backups/2026-09-21-capital-standalone-retirement-r8/source

- all-refs bundle SHA-256: 2f69f5a8e9d2877afdb832f726633a3f2d9cb2cba74110e0ca589aeff5363ba8
- complete .git archive SHA-256: 98376f7d89e330881805a5b34cb1ee4689daa29ce68bf20890f7365a6fb708eb
- ignored non-venv payload SHA-256: 6ce3769ec2e338ffe3d3539f3ce8dba3b2d0717f805550fe014864afea8dbc2b
- preserved SNDK workspace residual SHA-256: 7fe9433e6b9583a66c4cdd0305ac2b6476bfdc54becc4bc0055e0f42acdadac4

The Git backup preserves 50 refs, 94 commits, and 30 unreachable objects. The ignored payload archive preserves 322 files. .venv is intentionally excluded as a regenerable dependency cache.

## Workspace closure

Two remaining Runtime workspaces had used the standalone repo as Git common-dir authority:

- ws-market-capital-sndk-r1-20260920
- ws-capital-monorepo-preclean-r1-20260921

Both had zero non-terminal Host continuity claimants. The SNDK workspace's only unique residual was a 295-byte LEAN startup log.txt; it was archived before the workspace was made clean. Both workspaces were then compare-and-closed through Runtime.

A post-close full Runtime workspace inventory returned zero workspaces with the standalone sourceRepo.

## Restore proof

Two independent recovery paths were tested before and after deletion.

The all-refs bundle restored all 50 refs and all 94 reachable commits, including the last qualified external source:

- revision 71bf084cc140a210a5ec0ce736afeb82ed03ae69
- tree 10bec5b631f614987c2e385cc683d21b44f5cc3b

The complete .git archive restored all 30 pre-retirement unreachable objects as well.

A full working tree was reconstructed in a temporary location from the .git archive plus the non-venv payload archive. The restored checkout matched standalone main at 918fd86a3ebe69bb0e05835d7e4c656731da0833, retained the qualified R7 branch, restored all 322 archived ignored files, and had a clean Git status.

Therefore frozen Research/Paper1 records may retain the historical absolute coordinate unchanged. When exact source re-entry is needed, restore the verified archive at that coordinate; do not keep a permanent duplicate source owner or compatibility symlink.
