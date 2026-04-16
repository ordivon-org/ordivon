# Flakes First Development Workflow

## Goal

Use Nix flakes as the default way to enter development environments.

## Rules

1. Every real project should have `flake.nix`.
2. Every real project should have `.envrc` with `use flake`.
3. `direnv allow` is the standard entry step.
4. README files should not tell users to globally install runtimes.

## Temporary Work

Use `nix shell nixpkgs#...` for ad hoc tasks.

## Real Project Work

Use project-defined flake environments for:

- language runtime
- package manager
- build tools
- formatters
- linters
- test commands

## Benefit

This keeps the system layer stable and the project layer reproducible.
