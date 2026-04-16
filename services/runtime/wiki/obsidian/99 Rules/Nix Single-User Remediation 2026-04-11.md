# Nix Single-User Remediation 2026-04-11

## Objective

Convert the machine from a broken hybrid Nix state into a working single-user Nix model for `dev`.

Related notes:

- `[[99 Rules/Nix Mode Diagnosis 2026-04-11]]`
- `[[99 Rules/Machine Policy v2]]`

## Changes Applied

### 1. System Nix config simplified

Updated:

- `/etc/nix/nix.conf`

Result:

- removed daemon-oriented clutter from the active system config
- kept:
  - `experimental-features = nix-command flakes`
  - `substituters = https://mirrors.ustc.edu.cn/nix-channels/store https://cache.nixos.org/`
  - `trusted-public-keys = cache.nixos.org-1:...`

### 2. User-level Nix config created for `dev`

Created:

- `/home/dev/.config/nix/nix.conf`

Result:

- explicit `store = local`
- user environment now forces local store mode

### 3. Stale daemon socket removed

Removed:

- `/nix/var/nix/daemon-socket/socket`

### 4. `/nix` ownership moved to `dev`

Applied:

- recursive ownership change under `/nix` to `dev:dev`

Reason:

- single-user mode requires `dev` to own the local Nix store state and database paths

## Validation

Validated:

- `nix config show` for `dev` reports `store = local`
- `nix profile add` works again
- profile updates are writable from the `dev` user

## Follow-up Recovery

Later on 2026-04-11, a root-run `nix develop` session reintroduced local drift:

- root-owned store entries appeared under `/nix/store`
- root-owned temp roots appeared under `/nix/var/nix/temproots`
- `direnv` and `nix develop` for `dev` started failing again with permission errors under `/nix/store`

Recovery applied:

- stopped the lingering root-run `nix develop` processes
- reapplied recursive ownership under `/nix` to `dev:dev`

Interpretation:

- the single-user model itself was still correct
- the breakage came from using root shells to drive local-store Nix operations
- this machine should treat root-run Nix activity as a recovery risk unless the machine policy is intentionally changed

## Result

Nix now operates as:

- single-user
- local store mode
- `dev`-owned profile workflow

## Rule Going Forward

- do not reintroduce daemon-mode assumptions unless machine policy changes
- do not use a root-run Nix daemon model on this WSL machine
- do not use root-run `nix develop`, `direnv`, or other local-store Nix workflows on this machine unless the goal is explicit repair work
