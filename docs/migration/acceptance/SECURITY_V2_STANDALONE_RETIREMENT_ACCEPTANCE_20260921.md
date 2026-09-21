# Security v2 standalone source-carrier retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: physically retire the legacy standalone Security-v2 source carrier at /root/projects/ordivon-security-v2 after Security source authority and all live Harness Browser Security consumers moved to the canonical monorepo owner at /root/projects/ordivon/platform/security.

This retirement does not remove Security capability, change Security policy, deploy a Browserless image, restart a production service, mutate provider state, or discard Git history.

## Legacy carrier identity

Immediately before removal:

- path: /root/projects/ordivon-security-v2
- branch: main
- head: f5db8508857ee844323f145891fb9cb832b12785
- tree: 9776ac30c6c54d0ef4931ebb43ace3e7d7adc05f
- tracked status: clean
- tracked files: 118
- linked Git worktrees: one, the repository root itself
- linked external Git worktrees: 0
- configured Git remote: none

The standalone carrier no longer represented current Security development. Canonical Security had already evolved in the monorepo with Agent Admission and delegated resource-server laboratory work.

## Live-consumer gate

A fresh bounded census immediately before physical removal established:

- Runtime Workspaces rooted at the standalone Security repository: 0
- process cwd/exe/fd references: 0
- systemd references: 0
- /etc and /root/.config references: 0
- live executable/source references after Harness cutover: 0
- external linked Git worktrees: 0

The prior Harness consumer cutover acceptance records the removal of the four real Browser Security consumers that had previously bound the standalone path.

Surviving literal references are historical/provenance material such as migration receipts, frozen migration plans, and the 2026-09-15 System Constellation Atlas source snapshot. Those bytes intentionally preserve creation-time paths and are not runtime authorities.

## Non-Git bytes

The old directory contained only rebuildable ignored state outside Git:

- .venv
- pytest cache
- Ruff cache
- Python bytecode caches
- setuptools egg-info

No Git submodules, Git LFS payload authority, DVC datasets, untracked research evidence, or other non-Git source authority was found.

The ignored-state inventories were retained before deletion:

- /root/ordivon-migration-backups/2026-09-21-security-retirement/security-v2-status-ignored.txt
- /root/ordivon-migration-backups/2026-09-21-security-retirement/security-v2-ignored-files.tsv

## Archive and restore proof

A complete all-refs Git bundle was created before deletion:

- bundle: /root/ordivon-migration-backups/2026-09-21-security-retirement/security-v2-all-refs.bundle
- bundle SHA-256: e7bc98b64d42f1f724f4710a44a0e787ead48f93cd583b72139feccaf799bc70
- refs manifest SHA-256: 246f6776f4b7a64b01cfecf6c891446db249b89c54c4493b73c8bba32c8d4856
- bundle-heads manifest SHA-256: 6c2cd73ee0794d54376c07bd40b9782d98a71b3c8c9cc864b8dac3a0e86026a4
- recorded refs: 22
- restore mismatches before deletion: 0

After the standalone directory had been physically removed, the bundle was cloned into a temporary mirror repository. The restored main ref exactly reproduced f5db8508857ee844323f145891fb9cb832b12785 and all 22 recorded refs reproduced with missing=0 and mismatch=0. The temporary restore clone was then removed.

The durable pre-delete physical-retirement receipt is:

/root/ordivon-migration-backups/2026-09-21-security-retirement/security-v2-physical-retirement.json

with SHA-256:

c4cafbeb50e0d79dc0f513285861c90ebd9199437f23df878eb01fc61c2fdd37

## Canonical authority after retirement

At the physical-removal transaction boundary:

- canonical source root: /root/projects/ordivon/platform/security
- canonical Security path-scoped revision: ae0d18a94244d968731529e98a2fe7ce95e04d9d
- canonical Security tree: b5d2d81213f0066738a6cb8e0b6c69663d4c06a7
- canonical Harness tree: 47f7b476b74b8578da715310375a4094403d80db
- transaction-observed monorepo head: e052ebdbd5cd45c2833f74d0a51825fb2565d1b9

After deletion, Harness locator/revision regression ran against the real canonical owner with the old directory absent:

- Security owner locator tests: 3/3 PASS
- release / pool / canary / promotion default Security roots: canonical
- pool/canary/promotion Security revision values: identical path-scoped owner revision
- live executable old-root references: 0
- all-refs bundle verification: PASS

## Disposition

- active Security source owner: /root/projects/ordivon/platform/security
- standalone Security-v2 path: physically absent
- standalone source history: archived and restore-proven
- old standalone location compatibility alias: NONE
- production cutover by this retirement: NONE
- provider mutation by this retirement: NONE

Reopening the legacy standalone repository, if ever necessary, must materialize from the recorded archive into a new bounded recovery path. Do not recreate /root/projects/ordivon-security-v2 as a compatibility alias.
