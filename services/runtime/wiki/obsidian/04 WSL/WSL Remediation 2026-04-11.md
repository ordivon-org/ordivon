# WSL Remediation 2026-04-11

## Objective

Apply the current machine policy to the WSL environment with minimal, explicit changes.

Policy source:

- `99 Rules/Machine Policy v2`

## Changes Applied

### 1. WSL policy made explicit in `/etc/wsl.conf`

New state:

```ini
[network]
generateResolvConf = true

[interop]
appendWindowsPath = false

[boot]
systemd = false
```

Reason:

- resolver behavior should follow WSL host integration by default
- Windows PATH injection should not pollute the Linux environment
- systemd policy should be explicit rather than implicit

### 2. Broken shell startup references removed

Updated files:

- `/home/dev/.profile`
- `/home/dev/.zshrc`

Applied fix:

- replaced unconditional `. "$HOME/.local/bin/env"` with a guarded existence check

Reason:

- shell startup must not source missing files

### 3. Retired Hermes home moved out of the active home directory

Moved:

- from `/home/dev/.hermes`
- to `/home/dev/state/legacy/hermes-home-2026-04-11`

Reason:

- the old global private runtime model should not remain in the active home directory
- historical state was preserved instead of being deleted

## Current Result

Aligned now:

- explicit WSL policy file
- no active `~/.hermes` path in the home directory
- shell startup no longer depends on a missing file
- login shell PATH is reduced and cleaner

Still pending:

- `/etc/resolv.conf` still shows the old manual DNS values until WSL is restarted
- any documentation that still says `systemd enabled` or `Nix daemon enabled` needs to be updated

## Required Next Step

To apply the new WSL settings fully, restart WSL from Windows:

```powershell
wsl --shutdown
```

Then reopen the distro and verify:

```bash
cat /etc/wsl.conf
cat /etc/resolv.conf
echo "$PATH"
```

## Verification Targets After Restart

- `/etc/resolv.conf` should no longer be the manually pinned static file unless WSL regenerates the same values
- Windows paths should not be injected into the default Linux PATH
- systemd should remain disabled unless explicitly changed later

## Follow-up Documentation Work

Update or supersede:

- `99 Rules/Current Environment Audit`
- `99 Rules/Environment Rules`

Reason:

- those notes still contain stale statements relative to the machine state and the new policy baseline
