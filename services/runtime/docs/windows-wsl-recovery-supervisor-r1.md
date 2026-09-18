# Windows WSL Control-Plane Recovery Supervisor R1

## One-line kernel

The Windows-side recovery supervisor is a **mechanical availability shim for the existing WSL-hosted control plane**: it probes the named WSL distro and exact systemd services, no-ops when they are already active, and in explicit ensure mode may issue only `systemctl start` followed by bounded readiness probes.

It is not a second Runtime, not a scheduler, and not a Job/Attempt authority.

## Why it exists

Real destructive R-W5 acceptance proved that the WSL-hosted Runtime can be physically terminated while a Windows-owned continuation survives. That experiment also exposed a separate availability problem: once the distro is gone, an Agent whose only control path is the WSL Runtime cannot repair its own control plane. A Windows-owned recovery shim provides the missing mechanical bootstrap boundary without duplicating Runtime semantics.

## Authority boundary

```text
Windows user session owning the WSL distribution
  |
  +-- windows-wsl-control-plane-supervisor.ps1
        |
        +-- Probe
        |     wsl.exe -d <distro> -u root -- systemctl is-active <services...>
        |
        +-- Ensure  [only after unhealthy probe]
              wsl.exe -d <distro> -u root -- systemctl start <services...>
              bounded is-active probes
```

The supervisor does **not**:

- call `wsl --terminate` or `wsl --shutdown`;
- stop or restart a healthy Runtime/Host service;
- read or write the Runtime Registry;
- inspect Job, Attempt, reservation, or recovery semantics;
- call `task.observe`, redispatch work, or infer semantic completion;
- run release, repair, migration, or destructive acceptance workflows.

Runtime remains authoritative for physical Job/Attempt truth. Host remains authoritative for semantic continuity.

## R1 executable surface

Source: `scripts/windows-wsl-control-plane-supervisor.ps1`.

Modes:

```text
Probe
  healthy services -> status=healthy, exit 0, mutationAttempted=false
  unhealthy/missing -> status=unhealthy, exit 1, mutationAttempted=false

Ensure
  healthy services -> status=healthy, exit 0, mutationAttempted=false
  unhealthy/missing -> systemctl start once, then bounded probes
  convergence       -> status=recovered
  non-convergence   -> status=failed
```

Each native `wsl.exe` client invocation is independently bounded by `NativeTimeoutMilliseconds` (default 5000 ms). A timed-out client process is terminated without terminating the WSL distro. The supervisor does not trust the Win32 `wsl.exe` exit code as the sole systemd truth because real probes showed `wsl.exe` may return 0 while `systemctl is-active` reports `inactive`. Health is therefore derived from the complete per-service state vector.

## Receipt

The default receipt is:

```text
C:\ProgramData\Ordivon\Runtime\RecoverySupervisor\latest.json
```

The receipt records:

- mode and distro;
- exact requested service names;
- `mutationAttempted` and action;
- bounded probe attempts;
- explicit `service -> state` mappings;
- transport exit/stderr evidence;
- final `healthy`, `unhealthy`, `recovered`, or `failed` status.

A receipt is mechanical host-availability evidence only. It is not a Runtime Job receipt and must never be used to infer execution success or semantic Task standing.

## Windows principal boundary

WSL distributions are Windows-user scoped. R1 therefore assumes execution under the Windows user that owns the target distribution. Running this shim as `LocalSystem` and assuming it can see a user's WSL distribution is not an accepted deployment model. A future scheduled-task installation should use that owner identity and must make its credential/logon semantics explicit.

## Activation boundary

R1 source is intentionally **not installed or scheduled** by this checkpoint. The current machine is a shared live control plane with other Agents active, so activation is deferred to a maintenance-safe step. Source validation may use `Probe`; `Ensure` may be exercised only when its target services are already healthy (proving the no-op path) until a maintenance window is available for a real unavailable->recovered acceptance.

## Current acceptance

On the current Windows/WSL host, without stopping or restarting Runtime/Host:

```text
PowerShell parser                         PASS
Probe(runtime + host active)              PASS
  states = active, active
  mutationAttempted = false
Probe(nonexistent test service)           PASS
  state = inactive
  mutationAttempted = false
Ensure(runtime + host already active)     PASS
  status = healthy
  action = none
  mutationAttempted = false
source destructive-vocabulary census      PASS
Runtime service                           active/running, NRestarts=0
Host v2 service                           active/running, NRestarts=0
```

The unavailable->recovered `Ensure` branch remains an explicit future maintenance-window acceptance.

## Relation to Native Runtime Nodes

This shim is **not** R6 of `NATIVE_RUNTIME_NODES_R1`. R6 is a true native Windows Runtime service with Windows-owned Registry, Workspace, Artifacts, MCP endpoint, and Job Object supervision that remains useful with WSL stopped. The recovery supervisor is only a temporary host-side bootstrap mechanism for the existing Linux/WSL node and should become optional once `windows-main` can independently host the control plane.
