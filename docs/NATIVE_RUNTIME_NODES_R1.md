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

## WSL control-plane recovery shim

Real WSL cold-restart acceptance exposed a narrower availability requirement before native Windows Runtime R6 exists: a Windows-owned process must be able to bootstrap the current WSL-hosted Runtime/Host services after the WSL control path disappears. `scripts/windows-wsl-control-plane-supervisor.ps1` provides that one-shot mechanical shim. It may probe service state and, only in explicit ensure mode after an unhealthy probe, issue `systemctl start` plus bounded readiness probes. It owns no Runtime Registry, Job/Attempt semantics, scheduling, redispatch, or semantic recovery.

This shim is deliberately **not** the Windows service target below. It is a migration bridge and may be retired once `windows-main` is a real independent control plane. See [`windows-wsl-recovery-supervisor-r1.md`](windows-wsl-recovery-supervisor-r1.md).

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

## R3d progress — platform-bound secure FS and execution payload admission

Shared filesystem utilities no longer unconditionally compile Linux raw-fd/openat2/sysconf primitives. Linux retains the exact no-follow/beneath-root implementation and execve admission boundaries. Other platforms fail closed for secure beneath-root resolution until a native implementation exists; no ordinary `File::open` fallback is used. Storage-capacity classification now uses Rust's cross-platform `ErrorKind::StorageFull`.

Execution payload admission is now target-aware. `local_linux` retains Linux execve per-string/aggregate limits. `windows_native` validates the actual launcher/CreateProcessW command-line shape in UTF-16, including launcher-compatible quoting and the documented 32,767-code-unit command-line ceiling, and separately validates Windows environment entry bounds. Durable plan validation uses the same target-specific rule.

With cargo-xwin + LLVM 22 as a real MSVC compile gate, this slice reduced native-Windows Core compile errors from 71 to 53 while Linux Core 231/231 and MCP 55/55 remained green. The remaining failures are concentrated in Runtime private-state permissions and Universal Workspace Unix identity semantics.

## R3e progress — Windows-compilable transactional Core closure

The remaining 53 MSVC compile failures were one ownership cluster rather than 53 independent
features: POSIX permission modes, UID/GID ownership, no-follow/open flags, Unix symlink metadata,
Linux executable-bit observation, and Workspace inode/time race witnesses were still imported by
shared modules.

R3e moves those assumptions back behind their owning platform boundaries without inventing Windows
equivalents:

- input-authority root opening reuses the existing secure no-follow abstraction; non-Unix remains
  fail-closed until a native implementation exists;
- immutable-input and Attempt-bundle POSIX mode enforcement is isolated from shared request/state
  semantics;
- trusted-local temporary symlink presentation remains Unix-native and returns TOOL_UNAVAILABLE on
  non-Unix rather than silently weakening its ownership/mode invariant;
- Registry private-state POSIX permissions remain exact on Unix, while native Windows startup
  deliberately fails closed until R5 supplies an ACL realization;
- Workspace source-state inode/time identity and UID/GID transfer remain Unix-native; the non-Unix
  paths expose an explicit unavailable boundary instead of substituting weaker pathname checks;
- Linux provider executable-bit semantics stay Linux-owned.

Acceptance on the integration candidate:

- RUSTFLAGS=-D warnings cargo xwin check -p ordivon-runtime-core --lib --target
  x86_64-pc-windows-msvc: PASS, **0 errors / 0 warnings**;
- Linux Runtime Core fast regression: **231/231 PASS**, with only the known long-running Registry
  reference-model property explicitly filtered;
- Runtime MCP library: **60/60 PASS**;
- Runtime MCP binary/auth tests: **8/8 PASS**;
- cargo fmt --all -- --check and git diff --check: PASS.

This closes the R3 compile boundary only. It does **not** claim R4 native Windows dispatch ownership,
R5 Windows Registry/Workspace/Artifact ACL/state semantics, or R6 SCM service acceptance.

## R4a progress — native binary and direct-launch compile boundary

The same Runtime MCP/binary now cross-compiles for x86_64-pc-windows-msvc with warnings denied.
The committed WindowsNative dispatch branch already distinguishes the control-plane locality by
configuration:

- wsl_distribution=None binds directly to dispatch_windows_native and the repository-owned Windows
  Job launcher;
- a configured WSL distribution remains the Linux/WSL-hosted transport and crosses
  dispatch_windows_via_wsl;
- the native spawn path rejects a WSL distribution, canonicalizes the launcher, emits launcher-start
  evidence, and does not introduce systemd identity into the native branch.

Bearer-token POSIX mode validation was also separated from shared binary compilation. Native Windows
startup remains deliberately fail-closed until a Windows ACL validator exists; this avoids treating
the successful cross-compile as service-readiness evidence.

Acceptance:

- RUSTFLAGS=-D warnings cargo xwin check -p ordivon-runtime-mcp --target
  x86_64-pc-windows-msvc: PASS;
- Linux Runtime MCP library: **60/60 PASS**;
- Linux Runtime MCP binary/auth tests: **8/8 PASS**.

R4a proves the native direct-launch code and complete Runtime MCP binary compile together. R4 is not
yet live-accepted: R5 native state/ACL remains a startup prerequisite and R6 owns SCM/restart
acceptance.

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
