# Contributing to Ordivon

Ordivon is a monorepo of independent owners (`services/`, `platform/`, `capabilities/`, `domains/`, `packages/`, `apps/`). Repository co-location does not merge authority, so most of contributing is picking the right owner and verifying inside it.

Before a non-trivial change, read [`README.md`](README.md) and [`AGENTS.md`](AGENTS.md). They apply to human and automated contributors alike.

## Workflow

1. Reuse an existing Issue, Host Work or source-bound task; open a new Issue when it materially helps discovery or coordination.
2. Work in the natural owner directory in an isolated Runtime Workspace or Git worktree based on current `main`. External contributors may fork; never edit the shared primary checkout as scratch.
3. Run that owner's native verification (`mise tasks ls` in the owner directory lists it).
4. For changes that touch repository mechanics, also run `mise run repo:ci` from the repository root.
5. Open a pull request against main and fill in the existing PR template's
   consumer/acceptance and engineering-resource review. Use brief, reasoned
   N/A entries where a dimension is immaterial to the actual change.
6. Before merging each PR, obtain an actual independent review by at least
   one other participating Agent, not the author using a different branch or
   merely a shared GitHub login. Record the reviewing Agent, exact HEAD,
   concrete counterexample or consumer readback, and its GitHub review or
   existing Host Topic / Runtime Job evidence. PENDING and CHANGES_REQUESTED
   are not approvals: repair all material findings, and require a fresh
   independent PASS on the updated HEAD. Author self-review or CI PASS
   cannot substitute for that independent audit.
   Reuse GitHub native reviews and the existing Host Space rather than a
   custom review registry, a fabricated Owner Agent, or a new CI gate.

## Ground rules

- Do not import another owner's internals; cross-owner effects go through the owners' explicit contracts (`tools/repo/owners.toml`, `tools/repo/dependency_contracts.toml`).
- Keep source relocation separate from semantic changes, in separate pull requests.
- Prefer the smallest verified contribution. Delete or reuse before creating new custom machinery.
- Do not unify lockfiles, environments or releases across owners as a cleanup shortcut.
- Report verification honestly: SKIP, NOT_RUN and ENV_BLOCKED are not PASS.
- Never commit secrets. CI runs gitleaks and a tracked-secrets check.
- Keep large generated binaries outside Git; preserve only Owner-qualified source assets or test fixtures with a real consumer, license and repository policy. Media, Artifact or Distribution own their output and delivery.

## Dependency updates

Dependabot owns GitHub Actions, npm, Cargo and Nix manifests. Renovate owns Python (PEP 621) manifests, `uv.lock` and `mise` tool versions. Do not add an ecosystem to both; `tools/repo/test_dependency_update_ownership.py` enforces the split.

## License

By submitting a contribution you agree that it is licensed under the [Apache License 2.0](LICENSE), as provided in Section 5 of that license.
