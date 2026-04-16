# WSL Alignment Report 2026-04-11

## Scope

This report reviews the current vault rules and workflow notes against the actual WSL environment as observed on 2026-04-11.

Purpose:

- preserve the parts of the current machine model that are coherent
- identify statements in the vault that are now inaccurate
- identify actual WSL state that no longer matches the agreed operating model
- separate documentation fixes from system fixes

## Reviewed Notes

- `99 Rules/Current Environment Audit`
- `99 Rules/Environment Rules`
- `99 Rules/Exceptions and Reset Policy`
- `03 Systems/Hermes + Obsidian Workflow`
- `03 Systems/Workflows/Flakes First Development Workflow`
- `Home`

## Agreed Model Recovered From The Vault

The current documented consensus is:

1. Windows host + WSL2 + Arch Linux
2. bash shell
3. Nix flakes first for real project environments
4. long-lived user CLI tools via `nix profile add`
5. project runtimes must stay project-scoped
6. Hermes runtime is project-scoped at `/home/dev/projects/hermes-runtime`
7. Hermes state is separated at `/home/dev/state/hermes`
8. optional extras such as Node/browser support remain opt-in
9. canonical vault path is `/home/dev/Documents/Obsidian Vault`
10. no return to app-private global runtime installs

This model is internally coherent and should remain the baseline.

## What Should Be Preserved

These parts of the current model are correct and should be retained:

- WSL2 + Arch as the base platform
- canonical vault path at `/home/dev/Documents/Obsidian Vault`
- Hermes runtime path at `/home/dev/projects/hermes-runtime`
- Hermes state outside the repo at `/home/dev/state/hermes`
- flakes-first development workflow
- `.envrc` + `use flake` as the normal project entry
- Nix profile for evergreen user CLI tools
- optional Node/browser support kept out of the base runtime path
- shell conventions around `rg`, `fd`, `bat`, `eza`, `direnv`, `zoxide`, `starship`

## What Needs To Be Modified In The Vault

### 1. `systemd: enabled` is no longer true

Current docs state:

- `99 Rules/Current Environment Audit`
- `99 Rules/Environment Rules`

Observed state:

- `systemctl is-system-running` returned `offline`
- `/run/systemd/system` is missing

Required change:

- replace "systemd enabled" with the actual current state
- either document systemd as disabled, or re-enable it and keep the note as-is

### 2. `Nix daemon: enabled` is no longer true as written

Current docs state:

- `99 Rules/Current Environment Audit`

Observed state:

- `nix` works
- `experimental-features = nix-command flakes` is present in `/etc/nix/nix.conf`
- no `nix-daemon` process was found

Required change:

- document the actual Nix mode precisely
- avoid saying "daemon enabled" unless multi-user daemon mode is actually running

### 3. Reset result is overstated

Current docs state:

- `~/.hermes` was removed
- retired private runtime directories were removed

Observed state:

- `/home/dev/.hermes` still exists

Required change:

- update the note to say the reset is incomplete, or finish the cleanup and then keep the statement

### 4. Current environment audit is stale relative to the machine

Observed mismatch:

- the note presents a verified state, but several claims are no longer verified

Required change:

- turn `Current Environment Audit` into a timestamped audit log
- avoid using it as a standing truth document unless it is refreshed after each change

## Actual WSL State That Does Match The Agreed Model

These items are aligned:

- WSL2 kernel present
- Arch Linux present
- `/home/dev/Documents/Obsidian Vault` is the only vault path found
- `hermes-runtime` has both `flake.nix` and `.envrc`
- `quant-agent` also has both `flake.nix` and `.envrc`
- `/etc/nix/nix.conf` has `experimental-features = nix-command flakes`
- user CLI tools from the Nix profile are present:
  - `gh`, `rg`, `fd`, `bat`, `eza`, `fzf`, `tmux`, `jq`, `obsidian`, `direnv`, `zoxide`, `atuin`
- Hermes state directory exists at `/home/dev/state/hermes`

## Actual WSL State That Does Not Match The Agreed Model

### 1. systemd is disabled

This is the largest machine-policy mismatch because multiple notes assume systemd as part of the base platform.

Impact:

- systemd service assumptions are invalid
- multi-user service management expectations are invalid
- any documentation built on `systemctl` as normal workflow is unreliable

### 2. DNS policy is not documented and conflicts with a maintainable WSL model

Observed state:

- `/etc/wsl.conf` has `generateResolvConf = false`
- `/etc/resolv.conf` is manually pinned to `1.1.1.1` and `8.8.8.8`

Why this matters:

- this bypasses Windows-provided DNS
- this can bypass VPN DNS behavior
- this can produce different results between browser and CLI
- this conflicts with a stable "WSL should follow host networking policy" approach

### 3. shell startup still references a missing file

Observed state:

- `/home/dev/.profile` sources `$HOME/.local/bin/env`
- `/home/dev/.zshrc` sources `$HOME/.local/bin/env`
- `/home/dev/.local/bin/env` is missing

Impact:

- login behavior is not clean
- shell startup rules are partially broken
- the reset did not fully normalize the user shell environment

### 4. actual runtime availability differs from implied expectations

Observed state outside flakes:

- no global `node`
- no global `npm`
- no global `pnpm`
- no global `pip`
- no global `docker`
- no global `uv`

This is not automatically a problem.

It is only a problem where docs or project onboarding still assume these tools exist outside `nix develop`.

### 5. Hermes cleanup residue remains

Observed state:

- `/home/dev/.hermes` still exists

Impact:

- historical state is ambiguous
- future audits cannot confidently say the retired model is gone

## Project-Level Review Against The Rules

### Hermes Runtime

Good:

- `flake.nix` exists
- `.envrc` exists
- state path is externalized
- optional extras are documented separately

Needs review:

- `README.md` still contains `uv pip install -e ...` instructions

This may be acceptable inside the flake shell, but it should be explicit that the command is expected to run inside `nix develop`, not as a global bootstrap model.

### Quant Agent

Good:

- `flake.nix` exists
- `.envrc` exists
- Python runtime is provisioned through the flake shell

Observation:

- the flake shell still auto-creates `.venv` and installs dependencies

This is compatible with the current project-scoped model.

## Keep vs Change Summary

### Keep

- WSL2 + Arch
- canonical vault location
- projectized Hermes layout
- external Hermes state directory
- flakes-first as the main development policy
- Nix profile for evergreen CLI tools
- project-local language runtimes
- opt-in optional browser/Node support

### Change In Documentation

- systemd status
- Nix daemon status
- reset completion status
- any note that implies the environment audit is timeless
- any onboarding text that does not clearly say "enter `nix develop` first"

### Change In WSL

- decide whether systemd should truly be enabled or officially retired from the baseline
- fix DNS policy so it is deliberate and documented
- remove stale shell startup references to missing files
- complete or document the remaining Hermes cleanup residue

## Recommended Consensus Update

The cleanest version of the machine policy is:

1. WSL2 + Arch stays
2. bash stays
3. Nix flakes remain the default project model
4. Nix profile remains the evergreen user tool layer
5. systemd must be either explicitly re-enabled or removed from the baseline docs
6. WSL networking should follow a documented DNS policy instead of an undocumented manual override
7. shell startup must not source missing files
8. reset notes must describe completed reality, not intended reality

## Concrete Remediation Plan

### Documentation fixes first

1. update `99 Rules/Current Environment Audit`
2. update `99 Rules/Environment Rules`
3. add a short note documenting the current DNS choice and exit condition
4. update `hermes-runtime/README.md` to make flake-shell assumptions explicit

### Machine fixes second

1. choose one of:
   - re-enable systemd
   - or rewrite the baseline docs to "systemd not required"
2. choose one of:
   - restore WSL-generated resolver behavior
   - or keep manual resolver settings and document why
3. remove broken shell startup references to `$HOME/.local/bin/env`
4. inspect and either remove or document `/home/dev/.hermes`

## Command Set For The Next Pass

If the goal is to align the machine to the current documented rules, the likely command set is:

```bash
# inspect current shell files
sed -n '1,200p' /home/dev/.bashrc /home/dev/.profile /home/dev/.zshrc

# inspect WSL DNS policy
cat /etc/wsl.conf
cat /etc/resolv.conf

# inspect residual Hermes state
ls -la /home/dev/.hermes

# inspect actual systemd state
systemctl is-system-running
test -d /run/systemd/system && echo yes || echo no
```

If the goal is to align the documentation to the current machine instead, modify the notes first and defer the system changes.

## Bottom Line

The core architecture is still sound.

The main issue is not that the machine model is wrong. The main issue is that the vault now mixes:

- a strong target policy
- a partially completed reset
- stale verification statements

The next step should be to decide whether the source of truth is:

- the current machine as it exists now
- or the intended target model after one more cleanup pass

Until that is decided, do not keep marking the environment as "verified".
