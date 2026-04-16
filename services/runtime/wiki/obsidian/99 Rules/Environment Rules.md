# Environment Rules

This note defines the working rules for this machine.

Status:

- superseded by `[[99 Rules/Machine Policy v2]]`
- keep this note as a short compatibility summary
- use `Machine Policy v2` as the normative policy

## Base Platform

- Windows host with WSL2
- Arch Linux guest
- systemd policy is explicit and currently disabled in `/etc/wsl.conf`
- bash shell
- sudo/root available

## Package and Runtime Rules

### System layer

Use the system package manager only for OS-level or low-level utilities.

Examples:

- system services
- networking tools
- media/system libraries
- foundational utilities such as `ffmpeg`, `sqlite`, `openssl`

Do not use the system package manager to install development languages or framework toolchains.

See:

- `[[99 Rules/Machine Policy v2]]`

### User tool layer

Use `nix profile add` only for long-lived general-purpose user tools.

Examples:

- `git`, `gh`
- `ripgrep`, `fd`, `bat`, `eza`
- `fzf`, `tmux`, `jq`
- `obsidian`

Do not use user profile installs for project-specific runtimes.

See:

- `[[99 Rules/Machine Policy v2]]`

### Project layer

All language runtimes and framework toolchains must be project-scoped.

Approved approaches:

- temporary work: `nix shell nixpkgs#...`
- real projects: `flake.nix` + `direnv`

Current example:

- Hermes runtime at `/home/dev/projects/hermes-runtime`
- state stored separately at `/home/dev/state/hermes`

Disallowed approaches for project runtimes:

- `pacman -S` for Python, Node, Rust, Go, Java, etc.
- `npm -g`
- `pip install --user`
- ad hoc global framework installs

Preferred entry:

- `flake.nix`
- `.envrc` with `use flake`
- `direnv allow`

## Terminal Conventions

- `ls` -> `eza`
- `cat` -> `bat`
- `find` -> `fd`
- search should prefer `rg`
- `zoxide`, `starship`, and `direnv` are part of the standard workflow

## Nix Rules

- `flakes` enabled
- `nix-command` enabled
- use `nix profile add`, not `nix profile install`
- do not use Nix profile installs for project runtimes

## AI Collaboration Rules

When using AI coding agents:

- assume project environments come from `flake.nix`
- prefer reading project environment files before suggesting commands
- do not propose global language installation
- do not assume a stock Ubuntu-like environment

For the full current rule set, see:

- `[[99 Rules/Machine Policy v2]]`
