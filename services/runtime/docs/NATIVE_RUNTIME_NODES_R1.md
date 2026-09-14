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
