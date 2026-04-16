# Project Entry Remediation 2026-04-11

## Scope

Standardize local management entry points for the active projects.

Related policy:

- `[[99 Rules/Machine Policy v2]]`
- `[[03 Systems/Workflows/Project Management Entry Workflow]]`

## Changes Applied

### Hermes Runtime

Added:

- `/home/dev/projects/hermes-runtime/justfile`

Updated:

- `/home/dev/projects/hermes-runtime/README.md`

Result:

- local development on this machine now points to `direnv allow`
- common management commands are discoverable through `just --list`

### Quant Agent

Added:

- `/home/dev/projects/quant-agent/justfile`

Updated:

- `/home/dev/projects/quant-agent/README.md`

Result:

- local project entry is now explicit
- test and help commands are standardized

## Validation

Verified:

```bash
cd /home/dev/projects/hermes-runtime && just --list
cd /home/dev/projects/quant-agent && just --list
```

Both projects now expose a valid local command surface.
