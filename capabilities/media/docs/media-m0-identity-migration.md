# Ordivon Media M0 — Owner Identity Migration

## Goal

Align the repository/project identity with the already-recognized Media semantic owner while preserving Studio as a production capability and preserving all Git/research provenance.

Target physical identity:

```text
/root/projects/ordivon-studio
→ /root/projects/ordivon-media
```

This document is a migration gate, not authorization for an unguarded directory move.

## Live preflight — 2026-08-18

Observed from isolated Runtime Workspace `media-m0-preflight-20260818` opened from local `main`:

- local `main` = `35f69b3fa2865febee7e83dddbe43fcb498e5ffd`;
- source state is clean;
- no Git remote is configured;
- durable `repair/media-materialization-20260818` also points to `35f69b3...`;
- durable `research/media-core-20260818` points to historical research head `59b27bd5ae334e67fc041a7d2fe29e3e4bdb5790`;
- `59b27bd5...` and the older Studio main `ae1630a1...` are both ancestors of `35f69b3...`.

Four worktrees were present during preflight:

1. `/root/projects/ordivon-studio` — branch `main`, `35f69b3...`;
2. Runtime historical Media research worktree — detached `59b27bd5...`;
3. Runtime M0 preflight worktree — detached `35f69b3...`;
4. Runtime Media materialization-repair worktree — detached `35f69b3...`.

Because linked-worktree metadata records physical locations, the repository root must not be moved blindly while these relationships are live. The installed Git exposes `git worktree repair [<path>...]`; any physical move must be followed by exact worktree revalidation/repair rather than relying on path coincidence.

## Identity classification

`ordivon-studio` strings fall into different truth roles and must not be globally replaced.

### Keep as Studio capability identity

Examples include:

- Python package/module `ordivon_studio`;
- CLI program `ordivon-studio`;
- package names such as `ordivon-studio-tools`;
- Studio-specific review/equipment/archive/R2 receipt kinds;
- Studio production manifests and historical Production evidence;
- Art & Expression / production language where Studio is genuinely the consumer.

These describe the retained Studio capability plane.

### Migrate as current project/repository identity

Examples include:

- repository root path used as a current navigation/consumer location;
- top-level project naming and Media owner entrypoint;
- live cross-project references that mean "current repository containing Media/Studio authority" rather than historical evidence.

### Preserve as historical evidence

Cross-project research/evidence records in World and Computing contain exact historical `/root/projects/ordivon-studio` paths. Those observations must remain byte/provenance history rather than being rewritten to make the past look current.

### Rebind as live external consumers

Current Web design references include `/root/projects/ordivon-studio` as an upstream expression/research repository. Those must be revalidated and rebound to `/root/projects/ordivon-media` after the physical migration; Web remains autonomous.

## M0 acceptance gates

A physical migration is admitted only if all of the following hold immediately before execution:

1. **Source fence** — live Studio/Media root is clean and exact HEAD/ref topology is re-read.
2. **Worktree safety** — all linked worktrees are inventoried; obsolete disposable worktrees are closed only when clean and durably reachable; retained worktrees have an explicit repair/rebind plan.
3. **History** — no rebase/cherry-pick/replay or source-history rewrite is used merely for the rename.
4. **Path consumers** — current operational/live path consumers are separated from historical evidence references.
5. **Research integrity** — `research/media/`, detailed historical corpus, M7, Art & Expression, negative results and bridge links remain resolvable.
6. **Studio continuity** — CLI/package/tool identities keep working unless a separate consumer-driven rename is independently justified.
7. **Web/Game boundary** — neither repository is moved or semantically reassigned.
8. **Remote discipline** — absence of a configured remote does not authorize inventing a new GitHub repository during M0.
9. **Recovery map** — old `/root/projects/ordivon-studio` identity remains documented as a historical/recovery alias after migration.
10. **Post-move proof** — run Git status/ref/ancestry/worktree/link checks from the new root and verify any required `git worktree repair` result.

## Minimal execution order

```text
re-read live source truth
→ classify/close only safe disposable worktrees
→ pin durable refs
→ enumerate live current-path consumers
→ move repository root once
→ repair/revalidate Git worktrees
→ update only current project/path references
→ keep historical evidence unchanged
→ verify Studio CLI/package behavior
→ verify Media research links
→ refresh Host/Atlas recovery pointers
```

M0 ends when project identity and recovery navigation agree on Ordivon Media. It does not require a directory beautification campaign or a Media SDK.
