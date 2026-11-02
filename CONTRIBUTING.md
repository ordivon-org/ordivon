# Contributing to Ordivon

Ordivon is a modular Monorepo with independent natural owners. The repository is a shared source-location and Git integration boundary; it is not a universal Runtime, database, workflow, evidence or domain owner.

## Find the right change boundary

Start with [README.md](README.md) and [AGENTS.md](AGENTS.md). Choose the actual service or capability that owns the fact or effect being changed. Owner-specific guidance takes precedence for its source and verification boundary, including [Runtime](services/runtime/CONTRIBUTING.md) and [Harness](services/harness/CONTRIBUTING.md).

Before changing files, identify the actual consumers and public contract. Use [owners.toml](tools/repo/owners.toml) and [dependency_contracts.toml](tools/repo/dependency_contracts.toml) for repository navigation and permitted cross-owner source seams, not as permission to reach into another owner's internals.

## Prepare an isolated change

Record the Git source revision you inspected and work in an isolated branch or worktree. The shared `main` checkout is an integration surface; do not use it as a scratch workspace. Preserve unrelated local changes and ongoing jobs.

Prefer deleting provably unnecessary code, reusing maintained upstream/native components, and composing existing public interfaces. Introduce a new module only when a verified consumer or contract benefits. Do not create another generic registry, persistence owner, orchestration engine or hidden compatibility path.

## Verify

Use the affected owner's native `mise` task rather than assuming one root command proves every deployed component. Examples from the repository root:

```sh
mise run repo:ci
mise run runtime:verify
mise run harness:queue
mise run host:queue
mise run gateway:verify
mise run web:verify
```

Only run the tasks relevant to the changed owner and its actual consumers. A change to repository-wide boundaries also requires `mise run repo:ci`. Native verification may install declared tools; inspect the task first if operating in a restricted environment.

A CI result is not proof of Windows native execution, PostgreSQL readback, a production release or any externally effected semantic completion. When those contracts change, attach separate owner/provider-qualified evidence. Mark tests that were not run or were environment-blocked as such; never convert them into PASS.

## Submit

A PR should state the objective, SourceCut, changed contract, known consumers, verification commands/results, relevant negative or differential tests, and any deployment or rollback implications. Link an existing Work, issue, or ADR when applicable. Keep mechanical source movement separate from semantic refactoring.

Security issues must follow [SECURITY.md](SECURITY.md), not a public Issue. Licensing is source-specific; see [license scope](docs/LICENSE_SCOPE.md) before publishing or redistributing a component.

## Architecture decisions

Use [Architecture Decision Index](docs/architecture/ADR_INDEX.md) for existing decisions and the distinction between proposed layout and current deployed evidence. A passing source-level validation does not supersede current physical and provider truth.
