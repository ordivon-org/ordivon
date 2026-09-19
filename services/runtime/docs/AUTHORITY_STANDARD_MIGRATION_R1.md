# Authority / Standard Replacement Ratchet R1

Status: active migration contract
Scope: Runtime + Execution Fabric + native Windows control plane

## Rule

An Ordivon-specific mechanism is provisional unless it is irreducible after comparison with an
authoritative platform/protocol primitive. Every provisional mechanism MUST record:

1. authoritative owner / standard,
2. the current compatibility carrier,
3. acceptance evidence required for replacement,
4. the exact retirement condition for the compatibility carrier,
5. any semantics that remain genuinely Ordivon-owned after replacement.

Passing tests is not enough to retain a custom primitive when the host platform already owns the
same concern.

## Replacement matrix

| Concern | Authoritative primitive | Current compatibility carrier | Migration gate | Retirement condition |
|---|---|---|---|---|
| Windows daemon lifecycle | Windows Service Control Manager (SCM): StartServiceCtrlDispatcherW, ServiceMain, RegisterServiceCtrlHandlerExW, SetServiceStatus | Linux systemd Runtime plus WSL-hosted Windows provider | Native service reports START_PENDING/RUNNING/STOP_PENDING/STOPPED correctly and survives cold restart | Windows-main no longer needs WSL/systemd for its own lifecycle |
| Windows service identity | SCM virtual account NT SERVICE\\OrdivonRuntime + SERVICE_CONFIG_SERVICE_SID_INFO | interactive/admin/limited launcher token identity | Service token contains service SID; Runtime state ACL resolves only approved service/system/admin identities | no generic user identity required for Windows-main |
| Windows process-tree ownership | Windows Job Objects | repository-owned Windows Job launcher, sometimes reached through WSL | native dispatch/observe/cancel/recovery evidence under Windows-main | WSL transport is removed from native branch; launcher stays only as the Job Object provider |
| Windows private state | Windows security descriptors / protected DACLs | POSIX mode assumptions or fail-closed Windows stubs | Registry/store/token ACL read-back matches machine policy and rejects inherited/unexpected principals | no chmod/Unix ACL semantics on Windows paths |
| Machine-wide Windows state root | Known Folder FOLDERID_ProgramData / ProgramData | literal paths and Linux store defaults | native config resolves machine data root and all state remains beneath it | no Linux /var/lib defaults in Windows node startup |
| Windows recovery | SCM failure actions + Runtime durable Job reconciliation | external watchdog/supervisor scripts | crash restart plus Registry reconciliation passes without duplicate dispatch | custom Windows watchdog is deleted |
| Windows stop/control | SCM control handler | shell/task/process termination | stop/shutdown control reaches Runtime cancellation/drain path and reports status | no Task Scheduler/process polling as service-control owner |
| WSL distribution termination | Microsoft WSL command surface: wsl.exe --terminate / --shutdown | ad-hoc shell wrappers | provider receipts exact command, distribution and postcondition | custom terminate implementation deleted |
| Linux daemon lifecycle | systemd service manager | Runtime wrapper scripts where still present | unit state/restart/cgroup behavior represented through systemd contracts | duplicate process supervisors deleted |
| Linux process-tree ownership | systemd/cgroup v2 | Runtime Linux provider | current acceptance retained | no second home-grown process tree |
| durable workflow scheduling | Temporal where durable orchestration is actually required | bespoke wake/retry chains | workflow/activity replay and cancellation evidence | custom durable scheduler deleted |
| tool boundary | MCP | bespoke direct agent RPC seams | exact MCP contracts cover required actions | duplicate RPC façade deleted |
| source/change authority | Git | bespoke revision identity | Git object/worktree identity is sufficient | duplicate revision database deleted |
| structured state | SQLite / established DB transaction semantics | custom file ledgers where duplicated | transaction/recovery equivalence | redundant ledger deleted |

## Windows R5 acceptance

R5 is complete only when all of these are true:

- complete Runtime MCP binary cross-compiles for x86_64-pc-windows-msvc with warnings denied;
- native Windows node does not advertise local_linux;
- Linux runner is optional on Windows;
- Windows path lists use Windows path-list semantics;
- Workspace source-state commitment has a native Windows race/semantic witness;
- Registry, Runtime store, Artifact/Attempt state and token files have protected native DACLs;
- private ACL validation rejects inherited DACLs and unexpected principals;
- no Linux execve, UID/GID, POSIX mode, /var/lib, /run or WSL-mount semantic is required for
  native Windows node startup;
- Linux regression remains green.

## Windows R6 acceptance

R6 is complete only when a repository-owned SCM service contract proves:

- SERVICE_WIN32_OWN_PROCESS;
- service account NT SERVICE\\OrdivonRuntime (virtual account, no stored password);
- SERVICE_SID_TYPE_UNRESTRICTED initially; RESTRICTED is a later hardening option only after
  compatibility evidence;
- ServiceMain registers its handler immediately;
- START_PENDING/RUNNING/STOP_PENDING/STOPPED transitions are reported with valid wait hints and
  checkpoints;
- STOP and system shutdown controls trigger bounded Runtime shutdown rather than arbitrary process
  killing;
- SCM failure actions perform bounded restart for crashes/non-success failure according to explicit
  policy;
- durable Registry reconciliation prevents restart from becoming duplicate execution;
- state lives below ProgramData and is ACL-bound to the service identity/system administrators;
- cold boot and WSL-absent startup pass;
- stopping or terminating WSL does not stop Windows-main.

## Deletion principle

Compatibility code is deleted only after its replacement has runtime evidence. Once replacement
evidence exists, compatibility is not retained merely because it already works.

The intended terminal condition is not an Ordivon-specific kernel. It is a small composition layer
over standard authorities with explicit domain semantics and evidence.
