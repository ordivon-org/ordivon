# Finance source-retirement closeout — 2026-09-14

Status: **SOURCE_RETIRED / PHYSICAL ARCHIVE PRESERVED / LIVE RECOVERY RESIDUAL SEPARATE**.

This record supersedes the current-disposition conclusion in `finance-retention-disposition.md` without rewriting why the earlier migration hold was correct at that time.

## Physical source archive

The former active source path `/root/projects/ordivon-finance` was removed from the active project surface only after current source/worktree/process consumers had been discharged. The source tree was preserved by same-filesystem atomic directory rename at:

`/root/.local/state/ordivon-retired/projects/ordivon-finance-20260914-main-8550128`

Authoritative physical receipt:

`/root/.local/state/ordivon-retired/receipts/ordivon-finance-project-retirement-20260914.json`

Receipt evidence records:

- source main HEAD `8550128da9c18b09ed9371b3ddeca857d134e8b0`;
- main tree `227713e289daa50b13bb98988e10dbb7c38ef95c`;
- `641` retained refs with refs digest `sha256:6bb592783f078e694bf07e16a1bcba01879fc53fa84d1dde81b357fb78f0d355`;
- `git fsck --full` after repair/archive: `PASS`;
- exact inode identity preserved across the same-filesystem rename (`1374553` before and after);
- zero linked Git worktrees, zero process-path references, and zero current systemd/Ordivon-config source references before archival;
- no external financial write attempted by the retirement operation.

The final generic-research-admission retirement work was **not lost** when its Runtime workspace closed. It remains reachable in the archive as:

`refs/ordivon/closed/ws-market-capital-v2-external-first-r0-20260911` -> `e17ab5df8cb076d6e0543888b1224be2dbed7108`

That commit retires the Finance-owned generic `research.result.admit@1..5` writer while preserving historical read/replay compatibility and using the narrower Market Capital `capital.transition-simulation.admit@1` boundary for current transition-simulation admission. Its pre-close validation recorded Node `335/335`, Python sharded `1731/1731`, and Market-Capital-v2 semantic-freeze `29/29`.

The archive also retains historical cross-owner history under `refs/ordivon/retention/p0-cross-owner-history-freeze-20260914` at `1185273b44bad358481183d5bb7fc533acf0cd41`.

## State and recovery are no longer source-tree responsibilities

Finance mutable state was externalized before source retirement to:

`/var/lib/ordivon/finance-state`

The move preserved `839` files, `64,037,397` bytes and tree digest `sha256:12e1c6fc2475f085a926e87388a2f4c02475e47f0765bf02617808b38c3b25b9`. Current StateAuthority configuration binds that external state rather than the archived Git checkout.

Because the preserved live state is schema-compatible with historical exporter source `b03f8abf80f11842d095e4fbee07590c1b497dab`, recovery custody uses the installed rebound exporter:

`/opt/ordivon-finance-recovery-exporter-rebound/current/bin/finance-recovery-capsule`

The exporter passed export -> verify -> restore consequence testing before source retirement. Workstation configuration was cut over to this exporter and the custody timer remains enabled/active.

This live recovery residual is explicitly **separate** from Finance source authority. It remains a bounded migration item for the Operations/Workstation data-recovery owner and must not be used to reclassify `/root/projects/ordivon-finance` as current.

Installed residual receipt:

`/root/.local/state/ordivon-retired/receipts/ordivon-finance-installed-residual-retirement-20260914.json`

Its current classifications include:

- Finance executor service: retired, disabled, inactive, preserved only for rollback evidence;
- Finance MCP service: retired, masked, inactive tombstone;
- Finance recovery custody helper/timer: live recovery carrier/schedule pending successor;
- Network-v2 Finance egress/target: active and Network-v2-provider-owned;
- Finance StateAuthority config: current externalized-state configuration;
- obsolete `/etc/ordivon/finance-research.env`: retired after zero-consumer census.

## Forward ownership

The forward capital-system source carrier is `ordivon-market-capital-next`; generic research belongs Research v2 + Runtime/providers; network egress belongs Network v2; recovery scheduling/state custody is a separate Operations/Workstation residual. No broad Finance source owner remains in `/root/projects`.

Pinned QuestDB/Redpanda prospective-witness closure and future mature trading/effect-commit integration remain Market Capital work. They are not Finance-source-retention gates.

## Active-project consequence

After Finance source retirement, `/root/projects` contains **15** actual project directories (excluding infrastructure such as `.worktrees`). Finance is no longer one of them.
