# Environment Audit Workflow

This workflow defines how to audit the machine so each pass is traceable, comparable, and reviewable.

## Purpose

Use this workflow when:

- machine policy changes
- WSL networking changes
- shell startup changes
- a new runtime model is introduced
- debugging points to machine-level drift

## Required Outputs

Every audit pass must produce or update:

1. a dated audit note
2. a dated remediation note if changes were applied
3. links to the governing policy note
4. exact commands used for verification when practical

## Source Of Truth Order

1. `[[99 Rules/Machine Policy v2]]`
2. dated remediation notes
3. dated alignment reports
4. dated audits

Do not treat old audit notes as timeless truth.

## Audit Sequence

### 1. Confirm scope

State which layer is under review:

- system layer
- user tool layer
- project layer
- state layer
- network/machine policy

### 2. Read the governing notes first

Read before touching the machine:

- `[[99 Rules/Machine Policy v2]]`
- `[[99 Rules/Exceptions and Reset Policy]]`
- latest remediation note
- latest alignment report if relevant

### 3. Collect current state

Examples:

```bash
uname -a
cat /etc/os-release
cat /etc/wsl.conf
cat /etc/resolv.conf
echo "$PATH"
systemctl is-system-running || true
command -v nix direnv git rg fd bat eza
find /home/dev/projects -maxdepth 2 \( -name flake.nix -o -name .envrc \)
```

### 4. Compare against policy

For each mismatch, classify it as one of:

- policy violation
- stale documentation
- approved exception
- unreviewed drift

### 5. Apply minimal corrective change

Rules:

- prefer the smallest change that restores alignment
- document before/after state
- do not fold project-layer fixes into unrelated machine-layer work

### 6. Record the result

Create or update:

- `99 Rules/Current Environment Audit`
- a dated alignment report if analysis was needed
- a dated remediation note if changes were applied

## Minimum Audit Checklist

- WSL policy explicit in `/etc/wsl.conf`
- DNS policy matches the intended baseline
- PATH policy matches the intended baseline
- shell startup does not source missing files
- Nix flakes are enabled
- project runtime entry is `flake.nix + .envrc + direnv`
- retired runtime models are not active in the home directory
- exceptions are documented with owner and exit condition

## Naming Convention

Use dated notes:

- `WSL Alignment Report YYYY-MM-DD`
- `WSL Remediation YYYY-MM-DD`
- `Environment Audit YYYY-MM-DD` if a fresh snapshot is needed

## Review Rule

If a machine change cannot be tied back to a policy note or exception record, do not keep it.
