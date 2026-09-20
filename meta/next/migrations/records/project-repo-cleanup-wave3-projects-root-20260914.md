# Project repository cleanup — Wave 3 / projects-root hygiene — 2026-09-14

Status: **COMPLETED**.

## Workstation compatibility symlink

The compatibility path:

`/root/projects/workstation -> /root/workstation-lab`

was removed after an exact current-consumer census found:

- zero active process references;
- zero systemd/cron references;
- no active code/config consumers.

Remaining textual references were historical/migration documentation and the frozen Research-v2 P0 source-scope registry. That registry explicitly classifies `/root/projects/workstation` as `ALIAS_OF_INCLUDED_WORKSTATION_LAB`, with canonical realpath `/root/workstation-lab`, and is frozen historical evidence rather than a runtime dependency.

Only the symlink was removed. `/root/workstation-lab` remains an independent live residual repository and was verified intact after the operation.

## Stray private browser-state file

A top-level file named `新建 文本文档.txt` was found under `/root/projects`. It was not an empty placeholder: it was a 15,893-byte JSON browser/session-state residual and therefore potentially credential-sensitive.

An exact consumer census found zero active process, systemd, cron or repository references. The file was not deleted and its contents were not promoted into any project. It was moved to the root-only private retirement area:

`/var/lib/ordivon/retired/private-residuals/2026-09-14/browser-session-state-18d2bb2b.json`

with mode `0600`; the containing private directory is mode `0700`. Its SHA-256 is recorded privately in the adjacent manifest. No cookie/session values are copied into this migration record.

## `/root/projects` standing after Wave 3

The top-level surface now contains only:

- `.worktrees` infrastructure; and
- 16 actual project directories.

The 16 current project directories are:

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
- `ordivon-research-v2`
- `ordivon-runtime`
- `ordivon-security-v2`
- `ordivon-web`

No compatibility symlink or stray regular file remains at `/root/projects` top level.

This record does not claim that all 16 repositories are permanent Ordivon core primitives. The core remains Host v2 / Runtime / Harness; the other repositories remain domain owners, products, research projects or transitional carriers while they have demonstrated current responsibilities.
