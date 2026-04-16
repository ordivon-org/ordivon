# Current Environment Audit

Status:

- historical snapshot only
- not the normative machine policy
- see `[[99 Rules/Machine Policy v2]]` for current rules
- see `[[04 WSL/WSL Alignment Report 2026-04-11]]` and `[[04 WSL/WSL Remediation 2026-04-11]]` for recent corrections

## Verified Base State

- WSL2: yes
- Arch Linux: yes
- systemd: no longer verified; current policy is explicit `systemd = false`
- Nix daemon: no longer verified as a running daemon; Nix with flakes is available
- `experimental-features = nix-command flakes`: enabled in `/etc/nix/nix.conf`

## Verified Modern CLI Setup

Configured in shell:

- `ls` aliased to `eza`
- `cat` aliased to `bat`
- `find` aliased to `fd`
- `zoxide` enabled
- `starship` enabled
- `direnv` enabled
- `atuin` enabled

## Current Tooling Model

The machine is currently operating under a layered model:

- OS/base tools from the system package manager
- long-lived user tools from `nix profile add`
- project runtimes from `flake.nix` + `direnv`

This is the current intended model.

## Current Deviations From Target Policy

- not every note has been updated to `Machine Policy v2`
- some older notes still reflect pre-remediation assumptions
- tool and skill documentation is not yet fully systematized in the vault
- root-run local-store Nix commands can still reintroduce `/nix` ownership drift if used carelessly

## Safe Fixes Already Applied

- removed duplicate `~/.local/bin` PATH export from shell startup files
- guarded shell startup against sourcing missing files
- moved retired `~/.hermes` state out of the active home directory into `/home/dev/state/legacy/hermes-home-2026-04-11`
- validated the new project-scoped Hermes runtime
- recovered `/nix` ownership back to `dev:dev` after a root-run Nix session reintroduced permission drift

## Current Long-Lived User Tools

Examples currently present through Nix profile:

- `git`, `gh`
- `ripgrep`, `fd`, `bat`, `eza`
- `fzf`, `tmux`, `jq`
- `starship`, `zoxide`, `atuin`
- `obsidian`

## Current Project Runtime Example

- Hermes now runs from `/home/dev/projects/hermes-runtime`
- shell entry is `nix develop .`
- runtime entry is `./bin/hermes-runtime`
- mutable state is stored in `/home/dev/state/hermes`
- optional Node/browser/WhatsApp dependencies are bootstrapped manually with `./bin/bootstrap-node`

## Reset Action on 2026-04-09

A discipline reset was applied.

Removed:

- `~/.hermes`
- `~/.local/share/uv`
- private runtime entry points from `~/.local/bin`

Result:

- old Hermes-managed global runtime paths were retired from the active home directory
- `hermes`, `uv`, `node`, `npm`, `npx`, and `python3.11` are no longer globally available from the old private install model
- clean login shell PATH now resolves to Nix profile paths and system paths only

This aligns the machine with the flakes-first policy and the projectized Hermes model.
