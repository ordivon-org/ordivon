# Contributing to Ordivon

Ordivon is a monorepo of independent owners (`services/`, `platform/`, `capabilities/`, `domains/`, `packages/`, `apps/`). Repository co-location does not merge authority, so most of contributing is picking the right owner and verifying inside it.

Before a non-trivial change, read [`README.md`](README.md) and [`AGENTS.md`](AGENTS.md). They apply to human and automated contributors alike.

## Workflow

1. Open an issue first for anything beyond a small fix.
2. Fork, branch from `main`, and make the change inside the natural owner directory.
3. Run that owner's native verification (`mise tasks ls` in the owner directory lists it).
4. For changes that touch repository mechanics, also run `mise run repo:ci` from the repository root.
5. Open a pull request against `main` and fill in the template.

## Ground rules

- Do not import another owner's internals; cross-owner effects go through the owners' explicit contracts (`tools/repo/owners.toml`, `tools/repo/dependency_contracts.toml`).
- Keep source relocation separate from semantic changes, in separate pull requests.
- Prefer the smallest verified contribution. Delete or reuse before creating new custom machinery.
- Do not unify lockfiles, environments or releases across owners as a cleanup shortcut.
- Report verification honestly: SKIP, NOT_RUN and ENV_BLOCKED are not PASS.
- Never commit secrets. CI runs gitleaks and a tracked-secrets check.
- Do not add large binaries (video, archives, rendered media) to Git. Ask in the issue where they should live.

## Dependency updates

Dependabot owns GitHub Actions, npm, Cargo and Nix manifests. Renovate owns Python (PEP 621) manifests, `uv.lock` and `mise` tool versions. Do not add an ecosystem to both; `tools/repo/test_dependency_update_ownership.py` enforces the split.

## License

By submitting a contribution you agree that it is licensed under the [Apache License 2.0](LICENSE), as provided in Section 5 of that license.
