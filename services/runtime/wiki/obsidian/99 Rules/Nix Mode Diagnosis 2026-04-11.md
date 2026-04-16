# Nix Mode Diagnosis 2026-04-11

## Scope

Diagnose why `nix profile add` failed on the current WSL machine.

## Symptom

Observed failure:

```text
error: cannot connect to socket at '/nix/var/nix/daemon-socket/socket': Connection refused
```

## Findings

### 1. Daemon-style socket path existed

- `/nix/var/nix/daemon-socket/socket` existed

### 2. No daemon process was running

- no active `nix-daemon` process was found

### 3. `dev` profile existed and was readable

- `nix profile list` worked
- `dev` profile links existed under `/home/dev/.local/state/nix/profiles`

### 4. Local store access initially failed

When tested with local store mode:

```text
error: opening lock file "/nix/var/nix/db/big-lock": Permission denied
```

Interpretation:

- the machine was not in a clean daemon mode
- the machine was not in a clean single-user mode either
- default behavior was drifting toward daemon access because of the socket path
- local store access failed because `/nix` ownership still reflected the previous root-owned installation state

## Diagnosis

The machine was in a hybrid state:

- user-level profiles existed
- daemon socket path existed
- no daemon was running
- local store writes were blocked by ownership

This is why read operations looked healthy while write operations failed.

## Decision

Chosen target mode:

- single-user Nix for `dev`

Reason:

- single-user WSL development machine
- `systemd = false`
- lower operational complexity
- closer fit to the machine policy
