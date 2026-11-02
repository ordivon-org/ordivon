# Ordivon

This repository is the primary source monorepo for Ordivon.

Repository co-location does not merge authority. Runtime, Host, Harness, platform capabilities, domain owners, and scientific studies retain their own state, environment, release, and semantic acceptance boundaries.

The root owns repository mechanics only. It does not define a Universal Task, State, Evidence, Gate, Registry, Workflow, or Domain Model.

The physical primary checkout at /root/projects/ordivon is a shared integration surface, not an agent scratch workspace. Candidate work belongs in detached/branch worktrees. Main integration must be serialized through tools/repo/migration/integrate-main.sh; the helper fails closed if the primary index/worktree is stale or dirty and never auto-stashes or resets shared bytes. Owner-native verification remains outside this Git integration helper.

See `docs/architecture/CURRENT_ARCHITECTURE.md` for the canonical deployed architecture, `meta/next/docs/MONOREPO_M0_ARCHITECTURE.md` for the imported M0 design, and `docs/migration/acceptance/SOURCE_MIGRATION_STANDING.md` for current source standing.

The non-deployed source-layout transition target is `docs/architecture/STRUCTURE_R2.md`. It does not override current owner paths until each relocation wave is independently accepted.

Contributing? Start with [CONTRIBUTING](CONTRIBUTING.md). Report security
issues privately via [SECURITY](SECURITY.md). See the
[decision index](docs/architecture/DECISIONS_INDEX.md) for current architecture records.

## Where to start

Choose the **current natural owner** by the fact or effect it controls; the repository path is a navigation aid, not a new authority or a permanent LEGO identity.

| Question / responsibility | Current owner entry | Boundary |
| --- | --- | --- |
| Execute a Workspace, Job or Attempt; inspect a Runtime artifact | [`services/runtime/`](services/runtime/README.md) | Runtime execution and artifact truth |
| Read or commit external Work, Space, Topic, Message or attention state | [`services/host/`](services/host/README.md) | Host PostgreSQL semantic continuity |
| Route an authenticated external capability to an owner | [`services/gateway/`](services/gateway/README.md) | Gateway routing, not domain truth |
| Run a bounded Agent turn, tool call or browser session | [`services/harness/`](services/harness/README.md) | Harness cognition/tool continuity |
| Evaluate generic Cognitive Circuit and composition contracts | [`packages/composition/`](packages/composition/README.md) | Portable composition mechanics |
| Work on the product-facing web application | [`apps/web/`](apps/web/README.md) | Application surface |
| Select a method or reusable Agent Skill | [`.agents/skills/method-router/`](.agents/skills/method-router/SKILL.md) | Advisory method, not execution authorization |
| Check dependency ownership and allowed cross-owner seams | [`tools/repo/owners.toml`](tools/repo/owners.toml), [`dependency_contracts.toml`](tools/repo/dependency_contracts.toml) | Repository mechanics; owner-native contracts remain authoritative |

For source vs deployed state, start with [`CURRENT_ARCHITECTURE.md`](docs/architecture/CURRENT_ARCHITECTURE.md). For the **proposed, only partially deployed** physical package layout and migration gates, read [`STRUCTURE_R2.md`](docs/architecture/STRUCTURE_R2.md). Do not move source solely to match that target: first identify its real consumers, public seam, deployment files and native verification, and keep source relocation separate from semantic changes.
