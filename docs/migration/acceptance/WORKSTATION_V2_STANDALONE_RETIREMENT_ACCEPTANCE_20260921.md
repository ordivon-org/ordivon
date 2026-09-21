# Workstation v2 standalone retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: retire the legacy standalone Workstation v2 source carrier after monorepo source migration, live Edge carrier cutover, immutable recovery cutover, Runtime worktree drainage, current-metadata cutover, complete Git recovery proof, and post-delete owner verification.

## Canonical owner

- canonical repository: /root/projects/ordivon
- owner path: platform/workstation
- current-metadata cutover revision: 25919bea458ff04fe0a7282c15472499f3080a3c
- standalone source path before deletion: /root/projects/ordivon-workstation-v2
- standalone source HEAD: add96799759383ea0b5b318d9aa5a7c53c7d00bd
- standalone source tree: 7213d91d97359beb87bc0acd2a4355db10f9357a

The monorepo owner had intentionally evolved beyond the standalone tree. Retirement therefore proves source/history preservation and current-owner behavior independently rather than requiring final subtree equality.

## Recovery authority cutover

The active immutable Workstation recovery generation was moved to the monorepo before standalone retirement.

Current generation:

/opt/ordivon-workstation-recovery/aefdb6871b27d2141ae4d94bc314857caa850cbd

It binds:

- sourceRepository: /root/projects/ordivon
- ownerRelativePath: platform/workstation
- controlRepository: /root/projects/ordivon
- control snapshot tag: ordivon-monorepo-control.

The production current symlink was atomically switched after detached and production no-activate verification. No manual backup was invoked during the cutover. The pre-existing failed state of the backup oneshot from the separate semantic-maintenance/prune problem was preserved and is not claimed fixed by this retirement.

## Edge provider cutover

The live Cloudflare Edge provider had already moved to platform/workstation/providers/cloudflare.

Installed GC and release controllers resolve the monorepo provider root. The GC service WorkingDirectory is the monorepo provider path; the timer remained active/waiting/enabled. A non-destructive GC dry-run completed successfully without remote deletion.

## Runtime worktree drainage

Three linked Runtime worktrees remained on the standalone Git authority.

Two clean workspaces were closed through Runtime compare-and-close using exact sourceStateDigest values:

- agent-birth-cloudflare-tofu-20260921
- ws-workstation-agent-automation-retire-r1-20260920.

The final workspace, ws-workstation-windows-cloudflare-r1-20260920, had no tracked changes but contained 24 untracked .playwright-cli page snapshots and console logs.

Those residual files were not discarded as cache. A recovery capsule records:

- detached HEAD c6dd3362bd245bc4bebb028a79dbe81e87682ed2
- exact Git status
- 24 paths and SHA-256 digests
- deterministic untracked tar
- a self-contained Git base bundle for the detached revision.

A fresh clone from the base bundle plus residual tar reproduced the exact Git status and all 24 file digests. Only then was the dirty Runtime workspace force-closed with the exact unchanged sourceStateDigest.

Recovery capsule:

/root/ordivon-migration-backups/2026-09-21-workstation-retirement/windows-cloudflare-playwright-residual

## Complete Git preservation

After worktree drainage the standalone root had one physical worktree and 47 ordinary refs, including refs/ordivon/closed identities for the former detached workspaces.

Full bundle:

/root/ordivon-migration-backups/2026-09-21-workstation-retirement/workstation-all-refs.bundle

Bundle SHA-256:

007757c42dc56c698b0b736d004e636dee89b4c91ab0b5801616ccf5c23bd5a2

Before deletion, source refs versus bundle heads reported:

- source ordinary refs: 47
- missing or digest mismatch: 0.

A fresh mirror cloned from the bundle resolved all 47 refs exactly. After physical deletion, the same fresh-mirror proof was repeated: 47 refs, zero missing or mismatch.

## Non-Git state

The standalone root contained ten ignored entries. File-level classification found only:

- pytest caches
- Ruff cache
- Python __pycache__ bytecode.

Non-cache unique payload count: 0.

No standalone-root database, credential, scientific dataset, media payload, or other unique non-Git state required preservation. The separate dirty Playwright worktree residual is covered by its restore-proven capsule.

## Current metadata and historical references

Before deletion, current Workstation provider/package metadata and the active Nix README were rebound to the canonical monorepo owner.

A strict archived-source reference policy now distinguishes historical provenance from current source authority:

docs/migration/retirement/workstation-v2-standalone-policy.json

Before physical deletion the policy reported 19 tracked historical references, 19 allowed, zero forbidden. Historical migration receipts, dated topology snapshots, planning records, one explicitly historical Temporal observation, and the Cloudflare negative regression are retained; current provider/package/readme surfaces no longer name the standalone root.

## Compatibility alias retirement

The former alias:

/root/projects/ordivon-operations-v2 -> /root/projects/ordivon-workstation-v2

had no Runtime workspace, systemd, cron, process, cwd, or active configuration consumer at the final gate. It was removed before the standalone source directory.

No compatibility alias was created after retirement.

## Physical retirement gate

Immediately before deletion:

- canonical monorepo worktree: clean
- archived-source policy: PASS
- standalone root: clean
- standalone worktrees: one root only
- Git bundle verify: PASS
- all-refs restore proof: PASS
- dirty Playwright residual restore proof: PASS
- non-Git unique payload count: 0
- current recovery uses standalone source: false
- current Edge provider uses standalone source: false
- systemd/cron/process/cwd/open-fd references to source or alias: 0.

Pre-delete receipt:

/root/ordivon-migration-backups/2026-09-21-workstation-retirement/workstation-physical-retirement-predelete.json

The alias was then unlinked and /root/projects/ordivon-workstation-v2 was physically removed.

## Post-delete proof

With the standalone path physically absent:

- the 47-ref bundle was cloned again and every ref resolved exactly
- canonical Workstation owner verification: PASS
- current immutable recovery generation verification: PASS
- Edge provider WorkingDirectory verification: PASS
- old standalone source path: absent
- Operations compatibility alias: absent.

Post-delete proof:

/root/ordivon-migration-backups/2026-09-21-workstation-retirement/workstation-post-retirement-proof.json

## Disposition

- active Workstation source owner: /root/projects/ordivon, owner path platform/workstation
- standalone Workstation source carrier: physically absent
- compatibility alias: absent
- complete Git history/refs: archived and restore-proven
- dirty browser-observation residual: archived and restore-proven
- standalone ignored state: rebuildable cache only
- recovery authority: monorepo-bound immutable generation v1
- Edge provider live carrier: monorepo-bound
- external provider mutation caused by retirement: none.

Historical receipts and frozen topology snapshots continue to name the old repository when that is the truth of the recorded observation. Retirement does not rewrite provenance.
