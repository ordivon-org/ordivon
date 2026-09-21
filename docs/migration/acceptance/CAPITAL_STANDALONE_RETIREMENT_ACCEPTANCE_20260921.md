# Capital standalone source-carrier retirement acceptance — 2026-09-21

Standing: RETIRED_ARCHIVED

## Current owner

Current source-of-truth:

/root/projects/ordivon/domains/capital

Retired physical source carrier:

/root/projects/ordivon-market-capital-next

The retired path is physically absent.

The last qualified standalone-source revision remains part of monorepo identity-preserving history:

- revision: 71bf084cc140a210a5ec0ce736afeb82ed03ae69
- tree: 10bec5b631f614987c2e385cc683d21b44f5cc3b

## Claimant closure

Before deletion:

- Runtime standalone-source workspaces found: 2
- non-terminal Host continuity claimants for each: 0
- unique dirty SNDK residuals: one 295-byte LEAN startup log
- active process cwd/exe claimants: 0
- live system-config references: 0

The SNDK residual was archived. Both Runtime workspaces were made clean and compare-and-closed. A complete post-close Runtime inventory returned zero workspaces using the standalone sourceRepo.

Six clean migration-temporary linked worktrees were removed through Git before source-carrier deletion.

## Recovery assets

Backup root:

/root/ordivon-migration-backups/2026-09-21-capital-standalone-retirement-r8/source

- all-refs bundle SHA-256: 2f69f5a8e9d2877afdb832f726633a3f2d9cb2cba74110e0ca589aeff5363ba8
- complete Git-directory archive SHA-256: 98376f7d89e330881805a5b34cb1ee4689daa29ce68bf20890f7365a6fb708eb
- ignored non-venv payload archive SHA-256: 6ce3769ec2e338ffe3d3539f3ce8dba3b2d0717f805550fe014864afea8dbc2b
- SNDK residual archive SHA-256: 7fe9433e6b9583a66c4cdd0305ac2b6476bfdc54becc4bc0055e0f42acdadac4

.venv was intentionally not preserved because it is a 1.3 GB regenerable dependency cache governed by the committed project and lock files.

## Restore proof

The all-refs bundle independently restored:

- 50 / 50 refs
- 94 commits
- qualified R7 revision and tree

The complete Git archive independently restored:

- 50 refs
- 94 reachable commits
- all 30 pre-retirement unreachable objects

The complete working tree recovery procedure was exercised in a temporary path using the Git archive plus the ignored non-venv payload. It restored:

- standalone main at 918fd86a3ebe69bb0e05835d7e4c656731da0833
- qualified R7 branch at 71bf084cc140a210a5ec0ce736afeb82ed03ae69
- all 322 archived ignored non-venv files
- clean Git status

Frozen Research/Paper1 provenance therefore keeps the historical absolute source coordinate as evidence identity without requiring a permanently live duplicate repo. Exact source re-entry is archive-backed and can reconstruct the retired coordinate on demand.

## Safety boundary

This retirement changes source-carrier topology only. It grants no financial effect authority.

Capital remains NON_LIVE and production external financial writes remain blocked.
