# WSL Final Acceptance 2026-04-11

## Scope

Final acceptance of the WSL cleanup, policy alignment, workflow standardization, and workspace layout pass completed on 2026-04-11.

Related notes:

- `[[99 Rules/Machine Policy v2]]`
- `[[04 WSL/WSL Alignment Report 2026-04-11]]`
- `[[04 WSL/WSL Remediation 2026-04-11]]`

## Acceptance Summary

The machine is accepted against the current policy baseline with the remaining behavior understood and documented.

## Verified Machine State

### WSL Policy

Verified in `/etc/wsl.conf`:

- `generateResolvConf = true`
- `appendWindowsPath = false`
- `systemd = false`

### Resolver Behavior

Verified in `/etc/resolv.conf` after restart:

- WSL now auto-generates the resolver file
- resolver is no longer the previously pinned manual public DNS file

### Network Baseline

Verified:

- default WSL2 NAT route present
- DNS resolution works
- HTTPS connectivity works

Observed:

- `api.openai.com` returned an HTTP response through Cloudflare

Interpretation:

- network and TLS are functioning
- HTTP-layer behavior should not be misdiagnosed as base network failure

### User Environment

Verified for `dev`:

- user: `dev`
- home: `/home/dev`
- shell: `/bin/bash`
- PATH: `/home/dev/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/usr/local/sbin:/usr/local/bin:/usr/bin`

This is acceptable.

Windows path injection is no longer present in the default `dev` shell PATH.

### Tool Baseline

Verified for `dev`:

- `nix`
- `direnv`
- `git`
- `rg`
- `fd`
- `bat`
- `eza`
- `zoxide`
- `atuin`

These resolve cleanly through the expected Nix profile or system paths.

## Verified Workspace Layout

### Knowledge

- `/home/dev/Documents/Obsidian Vault`

### Active Projects

- `/home/dev/projects/hermes-runtime`
- `/home/dev/projects/quant-agent`

### Template Repository

- `/home/dev/projects/templates/dev-templates`

### Archived Project

- `/home/dev/projects/archive/trading-agent-system`

### Runtime State

- `/home/dev/state/hermes`

### Legacy State

- `/home/dev/state/legacy/hermes-home-2026-04-11`

### System State

- `/home/dev/state/system/resolv.conf.backup`

## Verified Process Assets

The following process assets now exist and are part of the operating baseline:

- `[[03 Systems/Workflows/Environment Audit Workflow]]`
- `[[03 Systems/Workflows/Project Bootstrap Workflow]]`
- `[[03 Systems/Workflows/Template Maintenance Workflow]]`
- `[[03 Systems/Templates/Language Project Templates]]`
- `[[03 Systems/Templates/Exception Record Template]]`
- `[[03 Systems/Tools/Workspace Layout]]`

## Remaining Known Realities

These are not blockers, but they are part of the current accepted state:

- root shells may still show extra IDE-related PATH entries
- active project repos still contain their own local caches and virtual environments
- hidden application directories under `/home/dev` still exist where they belong to user-level tools

## Final Rule

From this point forward:

- machine policy changes must be documented first or alongside the change
- project initialization must use the approved template flow
- exceptions must be recorded explicitly
- audits must be dated
- loose top-level project or state paths must be cleaned up before they become normal

## Acceptance Decision

Accepted.
