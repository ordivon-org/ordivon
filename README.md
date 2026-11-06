# Ordivon

Ordivon is a modular, human-directed and Agent-assisted system for verified
research, engineering and other practical work. Specialized owners handle
execution, collaboration, domain facts and controlled effects; agents combine
their capabilities without inheriting authority from the repository.

**New here?** Start with [the two audience-specific entry paths](docs/start/README.md):
[for people](docs/start/human-first-run.md) (a runnable, read-only example) and
[for Agents](docs/start/agent-first-run.md) (owner discovery, evidence and
native verification). Find a concrete task in the
[task/owner guide](docs/start/tasks.md). The web product is a tested canary,
not a generally available production application.

## Engineering repository and ownership

This repository is the primary source monorepo for Ordivon.

Repository co-location does not merge authority. Runtime, Host, Harness, platform capabilities, domain owners, and scientific studies retain their own state, environment, release, and semantic acceptance boundaries.

The root owns repository mechanics only. It does not define a Universal Task, State, Evidence, Gate, Registry, Workflow, or Domain Model.

The physical primary checkout at /root/projects/ordivon is a shared integration surface, not an agent scratch workspace. Candidate work belongs in detached/branch worktrees. Main integration must be serialized through tools/repo/migration/integrate-main.sh; the helper fails closed if the primary index/worktree is stale or dirty and never auto-stashes or resets shared bytes. Owner-native verification remains outside this Git integration helper.

The dated `docs/architecture/CURRENT_ARCHITECTURE.md` preserves the **2026-09-28 historical deployment snapshot**, not current production truth. The source migration record is `docs/migration/acceptance/SOURCE_MIGRATION_STANDING.md`.

The non-deployed source-layout transition target is `docs/architecture/STRUCTURE_R2.md`. It does not override current owner paths until each relocation wave is independently accepted.

## Where to start

Choose the **current natural owner** by the fact or effect it controls; the repository path is a navigation aid, not a new authority or a permanent LEGO identity.

| Real consumer problem | Current natural Owner | Authority boundary |
| --- | --- | --- |
| Workspace/Job/Attempt and execution Artifacts | [runtime](services/runtime/README.md) | Execution truth; not Host Work |
| Work/Space/Topic/Message/Attention | [host](services/host/README.md) | PostgreSQL continuity and collaboration |
| Agent turn, provider/tool and trace continuity | [harness](services/harness/README.md) | Agent cognition; not a second Runtime |
| Northbound capability routing | [gateway](services/gateway/README.md) | Adapter, never domain truth |
| DNS/VPN/tunnel/proxy/route | [network](platform/network/README.md) | Physical network and connection |
| Principals/credentials/security policy | [security](platform/security/README.md) | Platform enforcement |
| Host service deployment/recovery | [workstation](platform/workstation/README.md) | Windows/Linux realization |
| External evidence and authority currentness | [authority-catalog](catalogs/authorities/README.md) | Discovery, not execution |
| Provider capability discovery | [capability-catalog](catalogs/capabilities/README.md) | Metadata, not authorization |
| Durable artifact identity/content/read | [artifact](capabilities/artifact/README.md) | Artifact bytes and integrity |
| Package and deliver products | [distribution](capabilities/distribution/README.md) | Destination receipts |
| Retention/archive/restore | [preservation](capabilities/preservation/README.md) | Preservation and recoverability |
| Media input/assets/render/encode | [media](capabilities/media/README.md) | Media output |
| Financial research/portfolio/risk/simulation | [capital](domains/capital/README.md) | Financial domain, paper and live separated |
| ECS, gameplay, Agent play and replay | [game](domains/game/README.md) | Playable game state |
| Contracts, LEGO ports and composition | [composition](packages/composition/README.md) | Portable combination semantics |
| Product Web interface | [web](apps/web/README.md) | UI projection only |
| Control-plane plugin packaging | [control-plugin](extensions/ordivon-control-plane/) | Thin Tool carrier |
| ChatGPT Skill MCP compatibility | [skills](extensions/chatgpt-skills-mcp/README.md) | Not Skill source authority |
| Attendance session and browser action | [chaoxing-autosign](apps/chaoxing-autosign/README.md) | Application outcome |

The table is a human navigation view, not a new registry. The source of truth for ownership paths and verification tasks is [owners.toml](tools/repo/owners.toml). The canonical advisory [method router](.agents/skills/method-router/SKILL.md) and [Recursive LEGO R2.1](.agents/skills/recursive-lego-calculus/SKILL.md) are separate from executable owner tools.

### For Humans: from a goal to a verified outcome

1. State the desired outcome, current evidence and **final consumer**; choose the Owner that owns the fact or effect, then open the Owner README and its actual Tools.
2. Distinguish a source commit, a merged PR, a running installed release, a Runtime Job, a Host Work and the actual user/domain outcome. One is not a substitute for another. Prefer live Owner observations to dates in historical plans.
3. For improvements, first check whether the OS, Git, PostgreSQL, uv, pnpm, Cargo, native provider API or current Ordivon Owner already supplies the needed operation. Treat a Skill as method guidance, not authority to execute an effect.
4. For removal, trace real downstream consumers and replay/recovery obligations. Use Owner-native close, Git worktree removal, native cache prune or PostgreSQL/Alembic rather than deleting files and rows with guessed path or age rules.

Existing commands to start with:

~~~bash
mise tasks ls --all                       # Discover real Owner verification entrypoints
mise run host:queue                        # Host native queue; live PG tests require a test DSN
mise run gateway:verify                    # Gateway native source/contract verification
mise run repo:ci                           # Repository mechanics, not domain acceptance
git worktree list --porcelain              # Inspect live and closed Git worktree registrations
git worktree prune --dry-run --verbose     # Stale Git metadata only
~~~

### For Agents: no second playbook

Read [AGENTS.md](AGENTS.md), then the selected Owner README and any closer scoped AGENTS.md. For architecture, use the existing [DSM Skill](.agents/skills/design-structure-matrix/SKILL.md). For external Skill candidates, use the existing [supply-chain audit Skill](.agents/skills/skill-supply-chain-audit/SKILL.md); for a declared LEGO use the complete [R2.1 contract](.agents/skills/recursive-lego-calculus/SKILL.md). A Tool, Skill, code file or Agent is **not** automatically an independently admitted LEGO. Reuse source/native methods before composing or inventing an adapter.

A useful handoff is brief and concrete: current SourceCut, selected Owner, final consumer, verified invariant/contract, commit and published/deployed state, removed redundant bytes if any, and remaining UNKNOWN. Avoid duplicate report files when native receipts or the PR already record the evidence.

For historical source-vs-deployment context, use [`CURRENT_ARCHITECTURE.md`](docs/architecture/CURRENT_ARCHITECTURE.md). For the **proposed, only partially deployed** physical package layout and migration gates, read [`STRUCTURE_R2.md`](docs/architecture/STRUCTURE_R2.md). Do not move source solely to match that target: first identify its real consumers, public seam, deployment files and native verification, and keep source relocation separate from semantic changes.

## Verify, contribute, report

- Verify repository mechanics with `mise install && mise run repo:ci`; CI runs the same tasks (see `mise.toml`).
- Contributing: [`CONTRIBUTING.md`](CONTRIBUTING.md).
- License: [Apache-2.0](LICENSE).
- Security: [private vulnerability reporting and policy](SECURITY.md).
- Architecture decisions: [current and superseded decision index](docs/architecture/DECISIONS.md).
