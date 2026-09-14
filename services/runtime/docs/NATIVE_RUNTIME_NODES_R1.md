# Native Runtime Nodes R1

Status: active migration design

## Decision

Ordivon Runtime is one protocol/core with one native Runtime node per physical execution authority. A node owns only its local Workspace, Registry, Job, Attempt, Artifact, input materialization, process supervision, and reconciliation truth.

```text
Host / Harness
      |
      | MCP capability discovery + routing
      v
+----------------------+   +----------------------+
| runtime:windows-main |   | runtime:linux-wsl    |
| native Windows node  |   | native Linux node    |
+----------+-----------+   +----------+-----------+
           |                          |
    Windows supervisor          Linux supervisor
      Job Objects              systemd + cgroup
```

A Windows node must remain available when WSL is stopped. A Linux/WSL node may be independently offline without taking the Windows node or the wider capability catalog offline.

## Ownership laws

1. Runtime nodes do not share a mutable Registry.
2. Runtime nodes do not share a mutable Workspace.
3. Cross-node transfer uses immutable identity: Git revision, digest-bound Artifact/Input, or provider-native object identity.
4. Host/Harness owns capability discovery and routing. Runtime does not grow a distributed scheduler, cluster registry, consensus layer, or Runtime-to-Runtime mesh.
5. MCP is the interoperability surface, not the execution owner.
6. Temporal or another mature workflow provider owns durable distributed orchestration when a workload actually requires queues, timers, replay, retries, or Worker failover.
7. Workstation/Operations owns machine substrate lifecycle such as starting/stopping WSL; Runtime owns admitted physical execution only.

## Node identity

Every Runtime process projects an operator-owned stable node identity distinct from execution targets. R1 adds `RuntimeNodeIdentity` to `runtime.describe` and Core capability projection. `ORDIVON_NODE_ID` configures the identity; platform-specific defaults exist only for backward-compatible deployment migration.

```json
{
  "node": {
    "nodeId": "windows-main",
    "platform": "windows",
    "native": true
  }
}
```

`platform` names the control-plane host OS, not every execution target the node may temporarily expose. A WSL-hosted Runtime is therefore a Linux node even if it can currently reach a Windows launcher through WSL interop.

## Platform supervisor boundary

Runtime Core should depend on a narrow platform-supervisor interface rather than treating systemd/cgroup as universal execution truth. The existing `runtime/supervisor.rs` already contains platform-neutral recovery classifications plus an explicit Windows launcher owner identity. R2 should continue this extraction rather than introduce a new scheduler.

The boundary must cover only physical mechanics Runtime already owns:

- dispatch one committed Attempt;
- observe exact process-tree ownership/liveness;
- stop the owned process tree;
- project resource-limit evidence;
- project identity-bound start/terminal evidence;
- recover/reconcile after Runtime restart.

Linux realization remains systemd/cgroup. Windows realization remains Windows Job Object + native process identity/handles. Platform-specific evidence remains explicit instead of being normalized into false equivalence.

## Windows service target

```text
Windows SCM
  -> Ordivon Runtime service
      -> MCP endpoint
      -> Runtime Core
      -> Windows-owned Registry/Workspace/Artifacts
      -> Windows supervisor
          -> Job Object
```

Suggested durable root: `%ProgramData%\Ordivon\Runtime`.

The native Windows node must not require WSL, `WSL_INTEROP`, `\\wsl.localhost`, Linux systemd, Linux cgroups, `/proc`, or a WSL-resident SQLite Registry for its ordinary control plane.

## Linux service target

The existing Linux node remains a systemd-hosted Runtime MCP service with Linux-owned Registry/Workspace/Artifacts and systemd/cgroup process-tree supervision. Its existing physical commitments remain authoritative for Linux Jobs.

## Routing

Harness/provider discovery treats nodes as independent capability providers. Availability is not authorization.

```text
available node
  -> Run capability binding
  -> turn Tool projection
  -> exact node-local admission
```

A stopped WSL distribution therefore yields `linux-archlinux=unavailable` while `windows-main` can remain ready.

## Migration order

1. **R1 — explicit node identity:** config -> Core -> `runtime.describe` -> MCP schema. Preserve all existing Job/Attempt/Registry semantics.
2. **R2 — platform seam:** move Linux-specific process supervision behind a platform boundary while preserving Linux behavior.
3. **R3 — Windows-compilable Core:** remove unconditional Unix imports from shared Core and move Linux filesystem/process primitives behind Linux modules.
4. **R4 — native Windows control plane:** reuse the existing Windows launcher/Job Object contract directly, without systemd/WSL transport.
5. **R5 — native Windows state:** Windows-owned Workspace/Registry/Artifact roots and native path semantics.
6. **R6 — Windows Service:** run the MCP adapter under SCM and verify restart/replay/cancel/reconciliation with WSL stopped.
7. **R7 — provider routing:** Harness/Workstation discover and route between `windows-main` and `linux-archlinux` without Runtime cluster semantics.

## R2 progress — Linux platform ownership seam

R2 begins with ownership, not abstraction inflation. The existing `runtime/systemd.rs` implementation moves to `runtime/platform/linux.rs`; shared Engine imports Linux physical mechanics through `runtime::platform` and no longer invokes `systemctl stop` directly. This deliberately preserves the existing systemd/cgroup evidence model while creating a concrete location for a later independent Windows realization.

R2b moves the WSL-hosted Windows `systemd-run` wrapper and its `WindowsSystemdRunSpec` into `runtime/platform/linux`. `windows.rs` retains the provider-owned launcher argument contract, token/environment probing, Windows process-owner observation and native direct-launch path; Linux now owns the fact that a WSL-hosted invocation is wrapped by systemd.

This still does **not** claim Windows-compilable Core. WSL interop discovery used by Windows provider probes remains in `windows.rs`, and shared Core still contains unconditional Unix filesystem/process primitives. Those are explicit subsequent R2/R3 cuts rather than reasons to invent a broad cross-platform supervisor trait prematurely.

R2 acceptance for this slice:

- Linux systemd/cgroup implementation lives under `runtime/platform/linux`;
- shared Engine has no direct `Command::new("systemctl")`;
- existing Linux execution/reconciliation behavior and tests remain unchanged;
- no generic distributed scheduling or false Windows/Linux evidence equivalence is introduced.

## R3 progress — shared Runtime host primitives

R3 starts by deleting avoidable Unix-only glue from shared Runtime state mechanics. Admission fences and immutable-input staging leases now use Rust standard-library `File::try_lock_shared` / `File::try_lock` rather than direct `libc::flock` and raw file descriptors. This preserves non-blocking lock semantics while giving the shared control plane one cross-platform primitive with no new dependency.

The remaining Unix-specific work is intentionally narrower and semantically meaningful: secure directory/file creation modes, no-follow authority opening, Linux UID ownership checks, `/proc` process identity, and the Linux Universal Runner (`openat2`, inotify, setuid/setgid). Those must move behind platform/runner boundaries rather than be weakened for portability.

## R3b progress — Linux Runner compilation ownership

The Universal Runner implementation is Linux/Unix-native (`openat2`, inotify, process groups, setuid/setgid, `/proc`), while its durable Runner request/result types remain platform-neutral. The runner module and `run_task_runner` export are therefore compiled only on Unix. Windows native Runtime continues to share the request/result model without compiling Linux process-realization code.

A real `cargo xwin check -p ordivon-runtime-core --lib --target x86_64-pc-windows-msvc` gate is now available through cargo-xwin + LLVM 22. After this ownership correction, Windows compile errors fell from 131 to 71 while Linux Core 228/228 and MCP 55/55 remained green.

## R1 acceptance

- `RuntimeCapabilities` includes node identity.
- `runtime.describe` includes the same identity.
- operator can set `ORDIVON_NODE_ID`.
- the identity is validated at Runtime construction.
- Linux Core and MCP unit suites remain green.
- no Job, Attempt, Registry, retry, or execution semantics change.

## Non-goals

- shared cross-OS SQLite Registry;
- cross-node mutable Workspace;
- distributed Runtime scheduler;
- leader election or consensus;
- custom Ordivon transport replacing MCP;
- Windows emulation of cgroup semantics or Linux emulation of Job Object semantics;
- preserving the WSL-hosted Windows execution path as the long-term primary Windows authority.
