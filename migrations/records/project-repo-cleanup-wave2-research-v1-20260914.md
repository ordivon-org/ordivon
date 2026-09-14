# Project repository cleanup — Wave 2 / Research v1 — 2026-09-14

Status: **COMPLETED**.

## Result

The archived `ordivon-research` v1 source has been physically removed from the active `/root/projects` surface and moved to:

`/var/lib/ordivon/retired/source-repos/2026-09-14/ordivon-research`

Final Research-v1 main HEAD:

`533ae2fc82ba5ffd92edc09ba4a0706275d1ce48`

The archive movement is recorded in `/var/lib/ordivon/retired/source-repos/2026-09-14/MANIFEST.tsv`.

This completes the distinction recorded in Wave 1:

- `RESEARCH_V1_ARCHITECTURAL_RETIREMENT = COMPLETE`
- `RESEARCH_V1_PHYSICAL_LOCAL_EVICTION = COMPLETE`

Forward Research E2E authority remains `ordivon-research-v2`.

## Runtime workspace preservation and closure

Research-v1 still had a large set of detached Runtime workspaces carrying Paper-1 lanes and older research experiments. Before closure, all **41 dirty Research-v1 workspaces** were preserved under:

`/var/lib/ordivon/retired/workspace-residuals/2026-09-14/research-v1/<workspaceId>/`

For each dirty workspace the preservation boundary records the source HEAD, pre-close Git status, binary tracked patch and a manifest. Untracked paths were **moved** into the preservation tree rather than copied, avoiding a second copy of the approximately 1.45 GB external-comparative vendor tree. The preserved Research-v1 workspace-residual root was approximately 1.5 GB at capture time.

After preservation, clean workspaces were closed normally. The two learner-randomness workspaces retaining only already-preserved tracked queue-progress diffs were force-closed after their exact patches had been captured. No unique uncommitted Research-v1 content was intentionally discarded.

## Paper-1 canonical-source cutover

The current Paper-1 publication corpus was not restored to Research v1. Instead, the exact current post-external-review corpus was cut over to the accepted forward Research-v2 main line.

Canonical manuscript path now:

`/root/projects/ordivon-research-v2/papers/first_paper_r2_finite_family/publication_r2/EMSE_PUBLICATION_SOURCE_R2.md`

Current manuscript SHA-256 at cutover:

`86f06e7fc6e3f1cb3f9d5a7d537390c941787110ea0c24cf074b011ecb97329b`

Research-v2 main commits produced by the cutover sequence:

- Paper-1 publication/manuscript/submission corpus cutover: main reached `f030bd25a823ac0b271355c502a329c981b8b0ca`.
- R4 frozen research object cutover: main reached `983fdaa866db9615c602787708f7841ae3adf6e8`.
- Manifest-listed ignored robustness result correction: main reached `ab743ba97cc52c4f6375810b2cedc7f59b7779a7`.

The R4 frozen object is canonical under:

`research_objects/first_paper_r2_r4_frozen/`

Manifest SHA-256:

`cb17654c5cf03689d809fed2b2ca925e7028a17f209ef63b66ac031dd7de931c`

The final canonical object contains all **140 manifest-listed files with zero missing files and zero digest mismatches**, plus the manifest itself. Four Python bytecode-cache files present in the source workspace were intentionally not made canonical. One manifest-listed robustness JSONL result was hidden by the repository's `results/` ignore rule and therefore had to be force-added explicitly before closure.

The pre-cutover detached-workspace status and binary patch are preserved under:

`/var/lib/ordivon/retired/paper1-cutover/2026-09-14/`

A large `scratch/` tree from the repair workspace, not part of the canonical Paper-1 corpus, was moved to:

`/var/lib/ordivon/retired/paper1-cutover/2026-09-14/source-workspace-extra/scratch`

The old external-review repair workspace and temporary cutover workspaces were closed after the canonical Research-v2 main was verified clean.

## Active `/root/projects` count after Wave 2

There are now **16 active project directories** under `/root/projects` (excluding `.worktrees`):

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

The compatibility symlink `/root/projects/workstation -> /root/workstation-lab` is not counted as a project directory and remains a separate cleanup candidate pending exact current-consumer census. `/root/workstation-lab` itself remains a live residual repository and is not retired by this record.
