# Workspace Layout

This note defines the intended directory layout for `/home/dev`.

## Root Principle

The home directory should expose only stable entry points.

Everything else should live under a clear category.

## Standard Layout

### Knowledge

- `/home/dev/Documents/Obsidian Vault`

Purpose:

- rules
- workflows
- templates
- durable notes
- operating documentation

### Active Projects

- `/home/dev/projects/hermes-runtime`
- `/home/dev/projects/quant-agent`

Purpose:

- active code repositories
- project-local runtimes via `flake.nix`

### Project Templates

- `/home/dev/projects/templates/dev-templates`

Purpose:

- local flake templates for new repositories

### Archived Or Legacy Projects

- `/home/dev/projects/archive/trading-agent-system`

Purpose:

- inactive or legacy repos preserved for reference

### Runtime State

- `/home/dev/state/hermes`

Purpose:

- mutable runtime state separated from source code

### Legacy State

- `/home/dev/state/legacy`

Purpose:

- retired state preserved for traceability

### System State

- `/home/dev/state/system`

Purpose:

- machine-level backups or migration artifacts

Current example:

- `/home/dev/state/system/resolv.conf.backup`

## What Should Not Live At `/home/dev` Root

- loose project folders
- retired runtime homes
- machine backup files
- scratch repos that have become long-lived

## Review Rule

When a new top-level path appears under `/home/dev`, decide whether it belongs in:

- `Documents`
- `projects`
- `state`
- hidden user config

If not, move it before it becomes a habit.
