# Project Management Entry Workflow

This workflow defines the standard local management entry for active projects on this machine.

## Goal

Every active project should expose a short, predictable command surface for common local tasks.

## Standard

For active projects:

- enter with `direnv allow`
- manage common tasks with `just`

## Required Local Entry

At minimum, each active project should provide:

- `just doctor`
- `just test`

Optional commands depend on project type.

## Why

This keeps local project management:

- discoverable
- auditable
- repeatable
- decoupled from shell history

## Current Active Projects

### Hermes Runtime

Path:

- `/home/dev/projects/hermes-runtime`

Current commands:

- `just doctor`
- `just test`
- `just cli-help`
- `just run`
- `just bootstrap-node`
- `just shellcheck`
- `just shfmt`

### Quant Agent

Path:

- `/home/dev/projects/quant-agent`

Current commands:

- `just doctor`
- `just test`
- `just layout`
- `just fetch-help`
- `just backtest-help`
- `just report-help`
- `just shellcheck`
- `just shfmt`

## Rule

When a new active project is created:

1. initialize from the approved template
2. add a `justfile` if the template does not already provide one
3. document the common entry commands in the project README

## Check

Use:

```bash
cd /home/dev/projects/<project>
just --list
```

If `just --list` does not present a minimal command surface, the project is not yet aligned with the local management standard.
