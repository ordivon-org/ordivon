# Tool Layer Inventory 2026-04-11

## Scope

Inventory of the current tool layer under the machine policy.

Policy source:

- `[[99 Rules/Machine Policy v2]]`

## Method

The inventory was checked from the `dev` user environment using:

- effective `PATH`
- `command -v`
- selected `--version` checks
- `nix profile list`
- current project environment files

## Effective `dev` PATH

```text
/home/dev/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/usr/local/sbin:/usr/local/bin:/usr/bin
```

This is acceptable.

## Current User Tool Layer

These are globally available and fit the current user-tool model:

### Core CLI

- `git`
- `gh`
- `rg`
- `fd`
- `bat`
- `eza`
- `jq`
- `fzf`
- `tmux`
- `direnv`
- `zoxide`
- `atuin`
- `just`

### Additional General Tools Present Through Nix Profile

- `delta`
- `doggo`
- `duf`
- `dust`
- `glow`
- `hyperfine`
- `lazygit`
- `neovim`
- `procs`
- `shellcheck`
- `shfmt`
- `strace`
- `lsof`
- `tldr`
- `tokei`
- `tree`
- `unzip`
- `yazi`
- `openssh`
- `obsidian`
- `btop`

### System/Base Utilities Present

- `curl`
- `wget`
- `openssl`
- `sqlite3`
- `ffmpeg`
- `gpg`

## Current Missing Global Tools

These are not currently available in the global environment:

### Containers

- `docker`
- `podman`

### Python Packaging

- `uv`
- `pip`
- `pip3`

### Node Tooling

- `node`
- `npm`
- `pnpm`
- `bun`
- `deno`

### Compiled Language Toolchains

- `go`
- `rustc`
- `cargo`
- `java`
- `javac`
- `mvn`
- `gradle`

### Build Chain

- `make`
- `gcc`
- `g++`
- `cmake`

### Infra And Utility

- `terraform`
- `kubectl`
- `helm`
- `ncdu`
- `htop`
- `yq`
- `age`

## Interpretation

This is not automatically a problem.

Under the current policy, many of these tools should not exist globally.

## Project Layer Coverage

Current active projects:

- `/home/dev/projects/hermes-runtime`
- `/home/dev/projects/quant-agent`

Current project environment signals:

- `hermes-runtime` has `flake.nix` and `.envrc`
- `quant-agent` has `flake.nix` and `.envrc`

This means language runtimes should continue to be supplied per project where possible.

## Classification

### Correctly Global

These fit the machine policy and should remain in the user tool layer:

- git/GitHub tools
- search and file tools
- terminal UX tools
- generic observability and utility tools
- Obsidian

### Should Usually Stay Project-Scoped

These should not be added globally by default:

- `uv`
- `node`
- `npm`
- `pnpm`
- `go`
- `rustc`
- `cargo`
- `java`
- `mvn`

### Good Candidates For User Tool Layer

These are reasonable additions if wanted across many projects:

- `yq`
- `ncdu`
- `htop`
- `age`

Possible optional additions:

- `kubectl`
- `helm`
- `terraform`

## Recommended Next Step

Applied on 2026-04-11:

- `yq`
- `ncdu`
- `htop`
- `age`
- `shellcheck`
- `shfmt`
- `strace`
- `lsof`
- `tree`

These are now present in the user tool layer.

If the goal is to extend the user tool layer further without violating policy, add only general-purpose tools first.

Suggested command:

```bash
su - dev -c 'nix profile add nixpkgs#yq nixpkgs#ncdu nixpkgs#htop nixpkgs#age'
```

Optional cloud/infrastructure tools:

```bash
su - dev -c 'nix profile add nixpkgs#kubectl nixpkgs#helm nixpkgs#terraform'
```

## Rule

Do not treat missing global language runtimes as a machine defect until the relevant project flake has been reviewed.
