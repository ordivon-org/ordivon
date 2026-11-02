# Contributing to Ordivon

Ordivon is a modular monorepo. Source co-location does not merge Runtime,
Host, Harness, Security, Platform or Domain truth boundaries.

## Start

1. Read [README](README.md), [AGENTS](AGENTS.md) and
   [Current Architecture](docs/architecture/CURRENT_ARCHITECTURE.md).
2. Find the natural owner and read its README and public contracts.
3. Bind the exact Git revision and actual consumers. Work in an isolated
   worktree; never reset, clean or force-update someone else's workspace.
4. Prefer DELETE → REUSE → COMPOSE → EXTEND → CREATE. Do not create
   a registry, service or compatibility layer without a real consumer.
5. Discuss changes affecting multiple owners or persistent data before
   broad implementation.

## Verification

Run the root repository mechanics with: mise run repo:ci

For affected owners run the corresponding tasks in root mise.toml, e.g.
mise run harness:verify, mise run runtime:verify, mise run host:verify.
Use unit, contract, integration, Formal, differential/replay and physical
consumer tests as the change demands. Compilation, model checking and an
exit code are not evidence of installed or domain success.

## Pull requests

Use the [PR template](.github/pull_request_template.md). Include exact
source revisions, owner boundaries, real consumers, executed validation,
remaining UNKNOWN findings and migration/rollback considerations.
Separate behavior changes from file relocation. Respect the protected
main Merge Queue and root-verification check.

Owner guides: [Runtime](services/runtime/CONTRIBUTING.md) and
[Harness](services/harness/CONTRIBUTING.md).

## Security and licensing

Do not put credentials or private content in public tests or PRs.
Report vulnerabilities through [SECURITY](SECURITY.md).
Some packages carry their own LICENSE; the repository currently has no
root-level license declaration. Do not infer a uniform monorepo license
or redistribute unlicensed root source without maintainer clarification.
