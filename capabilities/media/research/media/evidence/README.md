# Media Evidence / Provenance

## Canonical corpus locations

- Detailed MF0–MF9, Round A/B/C/D and final closeout corpus: [`../../expression/foundations/`](../../expression/foundations/README.md).
- M7 / Art & Expression historical-consumer corpus: [`../../expression/`](../../expression/README.md).
- Current navigation/materialization root: `research/media/`.

The materialization root intentionally points to existing evidence rather than copying 138k+ lines into a second mutable authority tree.

## Git durability repair — 2026-08-18

The modern Media research lineage had been present only as a clean detached worktree head:

`59b27bd5ae334e67fc041a7d2fe29e3e4bdb5790`

Revalidation established:

- Studio `main` before repair: `ae1630a1fa3cfa86b34155ab8d9c8c1d84e1e1fc`.
- `main` was an exact ancestor of the research head.
- divergence was `0 behind / 87 ahead` from main to research.
- no named ref contained the research head before repair.

Durability action:

- pinned `refs/heads/research/media-core-20260818` exactly to `59b27bd5ae334e67fc041a7d2fe29e3e4bdb5790`;
- verified ref reachability;
- fast-forwarded Studio `main` to the same head with `--ff-only`;
- no rebase, cherry-pick, replay or merge commit was used.

The research ref is retained as an explicit lineage anchor even after main integration.

## Host continuity

- consolidation control line: `task:ordivon-research-core-consolidation-mainline-20260818`
- Media consolidation capsule: `task:media-research-core-consolidation-branch-20260818` revision 3 completed
- materialization repair: `task:media-research-materialization-repair-20260818`
- canonical Media research continuity: `task:media-foundations-mf2h-20260817`

Host continuity is semantic/provenance navigation; Git refs and repository bytes remain the physical durability proof.
