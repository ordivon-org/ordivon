# Contributing to Ordivon

Ordivon is a monorepo with independent natural owners. Repository colocation does **not** transfer state, effect authority, release ownership, or semantic acceptance. Start with [README.md](README.md) and [AGENTS.md](AGENTS.md), including when contributing without an Agent.

## Find the responsible code

1. Identify the **observable property** or failure and the real consumers before choosing a directory.
2. Find the natural owner using [README.md](README.md) and [tools/repo/owners.toml](tools/repo/owners.toml). For cross-owner work, check [dependency_contracts.toml](tools/repo/dependency_contracts.toml).
3. Read that owner's README, local contribution/security guidance when present, and `mise tasks ls` in the owner directory.
4. Use an isolated branch/worktree. The shared primary checkout is an integration surface, not a scratch directory.

Repository paths are navigation, not LEGO identities. Follow the existing [Structure R2](docs/architecture/STRUCTURE_R2.md) migration rules; do not move source merely to make the directory tree symmetrical.

## Change and verification

- Capture the exact Git commit (SourceCut), affected consumers, intended contract, counterexample, and rollback/retirement plan.
- Prefer DELETE unnecessary custom behavior, then REUSE existing mature libraries or native owner capabilities, then COMPOSE. Create new mechanisms only for a demonstrated unmet contract.
- Keep source relocation distinct from semantic changes. Use public owner seams instead of importing another owner's implementation.
- Execute a focused owner-native test and the relevant owner verification task (`mise run <owner>:verify` from the root, or `mise run verify` in the owner). Use the actual task from `mise tasks ls` when the owner differs.
- For high-consequence effects, add negative tests, recovery/replay or fault-injection checks, and real consumer read-back. A model check, unit test, CI check, installed package, and real-world outcome are separate evidence claims.
- Include the source revision, executed commands, results, current environment, remaining UNKNOWN, and impact on lockfiles, deployments and consumers in the pull request. Never report SKIP, NOT_RUN, or ENV_BLOCKED as PASS.

The root's `mise run repo:ci` checks repository mechanics; owner-native tests remain authoritative for their implementations. CI selects affected owner verification; that selection must be challenged if a dynamic consumer is missing.

## Collaboration

Use the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) for auditable changes. Existing Ordivon Host Work and Space discussions can coordinate larger work, but they are not a replacement for Git review, executable source verification, or natural owner approval. Prefer one independently verifiable semantic change per pull request.

**Security:** report vulnerabilities privately under [SECURITY.md](SECURITY.md), never in a public issue or PR.

**Licensing:** this monorepo has no repository-wide `LICENSE` file as of this document's creation. Do not assume a uniform license across all subdirectories; license selection and any contributor rights policy require an explicit maintainer decision.
