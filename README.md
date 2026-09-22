# Ordivon

This repository is the primary source monorepo for Ordivon.

Repository co-location does not merge authority. Runtime, Host, Harness, platform capabilities, domain owners, and scientific studies retain their own state, environment, release, and semantic acceptance boundaries.

The root owns repository mechanics only. It does not define a Universal Task, State, Evidence, Gate, Registry, Workflow, or Domain Model.

The physical primary checkout at /root/projects/ordivon is a shared integration surface, not an agent scratch workspace. Candidate work belongs in detached/branch worktrees. Main integration must be serialized through tools/repo/migration/integrate-main.sh; the helper fails closed if the primary index/worktree is stale or dirty and never auto-stashes or resets shared bytes. Owner-native verification remains outside this Git integration helper.

See `docs/architecture/CURRENT_ARCHITECTURE.md` for the canonical deployed architecture, `meta/next/docs/MONOREPO_M0_ARCHITECTURE.md` for the imported M0 design, and `docs/migration/acceptance/SOURCE_MIGRATION_STANDING.md` for current source standing.

The non-deployed source-layout transition target is `docs/architecture/STRUCTURE_R2.md`. It does not override current owner paths until each relocation wave is independently accepted.
