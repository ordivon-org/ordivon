# Machine Policy v2

## Status

This note is the current intended machine policy.

Use this note as the normative rule set.

Use `Current Environment Audit` and dated alignment reports as observations, not as permanent truth.

## Platform Baseline

- Windows host
- WSL2 guest
- Arch Linux inside WSL
- bash as the standard shell
- development workspace lives under `/home/dev`
- canonical vault path is `/home/dev/Documents/Obsidian Vault`

## Layer Model

The machine is managed in four layers.

### 1. System Layer

Managed by:

- `pacman`

Allowed here:

- OS components
- networking tools
- low-level libraries
- system utilities
- hardware/media/system packages

Examples:

- `openssl`
- `sqlite`
- `ffmpeg`
- `iproute2`
- `dnsutils`
- `tcpdump`

Not allowed here:

- project language runtimes
- framework toolchains
- global development package managers

Disallowed examples:

- `pacman -S python`
- `pacman -S nodejs npm`
- `pacman -S rust go`

### 2. User Tool Layer

Managed by:

- `nix profile add`

Purpose:

- long-lived general-purpose tools used across many projects

Allowed here:

- editor-adjacent tools
- navigation/search tools
- git and GitHub tooling
- terminal UX tools
- general utilities

Examples:

- `git`, `gh`
- `rg`, `fd`, `bat`, `eza`
- `jq`, `fzf`, `tmux`
- `direnv`, `zoxide`, `starship`, `atuin`
- `obsidian`

Not allowed here:

- project runtimes
- framework SDKs
- one-project-only tooling

### 3. Project Layer

Managed by:

- `flake.nix`
- `.envrc`
- `direnv`

This is the only approved place for:

- Python
- Node
- pnpm
- uv
- Rust
- Go
- Java
- test tools
- build tools
- formatters
- linters
- project-specific CLIs

Rules:

1. Every real project must have `flake.nix`
2. Every real project must have `.envrc` with `use flake`
3. Standard entry is `direnv allow`
4. Project commands are assumed to run inside the flake environment
5. READMEs must not require global language installs

Allowed exception for temporary work:

- `nix shell nixpkgs#...`

### 4. State Layer

Mutable runtime state must be separated from source code when practical.

Examples:

- `/home/dev/state/hermes`

Use this layer for:

- agent state
- runtime caches that must persist
- local databases
- local credentials/config directories where project design requires separation

Do not:

- hide long-lived runtime state in retired private app directories
- reintroduce global installer-managed runtime trees

## Strict Prohibitions

The following are prohibited by default:

- `npm -g`
- `pnpm add -g`
- `pip install --user`
- ad hoc language installs into the user environment
- reviving app-private runtime trees such as `~/.hermes` as the normal model
- introducing project dependencies through shell startup files

These are also prohibited unless explicitly documented as an exception:

- global Python package bootstrapping outside project shells
- global Node package bootstrapping outside project shells
- using README instructions that assume a stock Ubuntu-like machine

## Nix Rules

- `flakes` must be enabled
- `nix-command` must be enabled
- prefer `nix profile add`
- do not use Nix profile installs for project runtimes
- if a tool is not broadly useful across projects, it does not belong in the user profile

## Shell Rules

- shell startup must stay minimal and deterministic
- shell startup must not source missing files
- shell startup must not install runtimes
- shell startup must not append duplicate PATH entries
- prefer aliases only for stable ergonomic replacements

Current standard conventions:

- `ls` -> `eza`
- `cat` -> `bat`
- `find` -> `fd`
- search via `rg`
- environment entry via `direnv`

## Documentation Rules

- policy notes describe intended rules
- audit notes describe observed machine state at a point in time
- exception notes describe temporary deviations and their exit conditions
- workflow notes describe how to operate within the policy

Do not mix these roles.

In particular:

- do not mark stale audits as verified
- do not leave undocumented exceptions alive
- do not let README onboarding contradict machine policy

## Exception Policy

Exceptions are allowed only when all of the following are documented:

1. reason
2. scope
3. owner
4. exit condition
5. review date

Default rule:

- undocumented exceptions are invalid

## Project Entry Standard

For every real repo:

1. create `flake.nix`
2. create `.envrc` containing `use flake`
3. run `direnv allow`
4. keep runtime commands inside that environment

Minimum README expectation:

```bash
cd /path/to/project
direnv allow
```

If additional commands are needed, the README must make clear they are run after entering the flake shell.

## Hermes-Specific Rule

- Hermes runtime stays at `/home/dev/projects/hermes-runtime`
- Hermes state stays at `/home/dev/state/hermes`
- Hermes is not a globally installed runtime
- optional extras such as browser or messaging support must remain opt-in
- optional extras must not block the base CLI runtime

## Network And Machine Policy

The following machine-level settings must be explicit and documented, not implicit:

- systemd policy
- DNS policy
- VPN interaction model
- PATH injection policy from Windows into WSL

If one of these differs from the baseline, document it as an exception or update the baseline.

## AI Agent Rule

When using coding agents or assistants:

- assume project environments come from `flake.nix`
- inspect project environment files before suggesting installs
- do not suggest global language installation by default
- do not assume Ubuntu defaults
- prefer project-scoped fixes over machine-wide runtime changes

## Enforcement Rule

When a new tool is introduced, decide in this order:

1. Is it OS-level? If yes, system layer.
2. Is it a long-lived general CLI used across projects? If yes, user tool layer.
3. Is it a language runtime, framework, or project dependency? If yes, project layer.
4. Does it only store mutable runtime data? If yes, state layer.

If it does not fit clearly, do not install it until the rule is written down.
