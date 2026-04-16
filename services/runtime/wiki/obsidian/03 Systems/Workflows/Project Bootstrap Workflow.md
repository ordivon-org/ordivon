# Project Bootstrap Workflow

This workflow defines the standard way to create a new real project on this machine.

## Goal

Every project should start in a state that is reproducible, auditable, and aligned with `[[99 Rules/Machine Policy v2]]`.

## Required Files

Every real project must have:

- `flake.nix`
- `.envrc`
- `README.md`

## Required Entry Flow

```bash
cd /home/dev/projects/<project-name>
direnv allow
```

## Bootstrap Sequence

### 1. Create the repo skeleton

```bash
mkdir -p /home/dev/projects/<project-name>
cd /home/dev/projects/<project-name>
git init
```

### 2. Initialize from the local template repository

```bash
nix flake init -t path:/home/dev/projects/templates/dev-templates#<template-name>
```

Reference:

- `[[03 Systems/Templates/Language Project Templates]]`

### 3. Review `flake.nix`

The flake must define:

- language runtime
- package manager
- build/test tools
- formatters/linters if used

### 4. Review `.envrc`

Minimum content:

```bash
use flake
```

If project state directories are needed, declare them explicitly here.

### 5. Review `README.md`

The README must:

- describe the purpose of the project
- state the standard entry step
- avoid asking for global language installs
- state that project commands run inside the flake environment

### 6. Enter the environment

```bash
direnv allow
```

### 7. Verify runtime

Examples:

```bash
command -v python node uv pnpm cargo go
```

Only the tools declared by the project should appear as required.

## Hard Rules

- do not use `pacman` for project runtimes
- do not use `nix profile` for project runtimes
- do not use `npm -g`
- do not use `pip install --user`
- do not hide project dependencies in shell startup files

## Review Checklist

- `flake.nix` exists
- `.envrc` exists
- `README.md` exists
- README says to enter via `direnv allow`
- runtime commands work after entering the project
- no global install step was introduced

## When A Temporary Shell Is Acceptable

Use `nix shell nixpkgs#...` only for:

- one-off experiments
- short-lived investigations
- non-project scratch work

If the work becomes real, promote it into a proper repo with `flake.nix`.
