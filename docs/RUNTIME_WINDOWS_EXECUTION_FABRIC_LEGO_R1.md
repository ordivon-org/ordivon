# Runtime Windows / Execution Fabric LEGO Decomposition R1

Status: active execution plan
Parent: `docs/AUTHORITY_STANDARD_MIGRATION_R1.md`
Integration workspace: `ws-runtime-fabric-final-r1-20260919`

## 0. Decomposition rule

A LEGO is valid only when it has:

- one authoritative owner,
- one narrow contract,
- explicit inputs and outputs,
- observable evidence,
- an acceptance gate,
- a retirement/deletion rule for any compatibility carrier.

No LEGO may silently own another LEGO's authority.

## 1. Authority map

| LEGO | Authoritative owner | Ordivon-owned semantics |
|---|---|---|
| service.lifecycle | Windows SCM | Runtime readiness and graceful cancellation mapping |
| service.identity | SCM virtual account + service SID | canonical principal label only |
| filesystem.authorization | Windows security descriptor / DACL | Runtime resource classes |
| machine.state.root | Windows CommonApplicationData / ProgramData | relative Runtime layout |
| process.tree | Windows Job Object | Job/Attempt binding and evidence |
| protocol.surface | MCP | Runtime tool semantics |
| durable.execution.truth | SQLite transaction semantics + Runtime schema | Job/Attempt/reconciliation domain model |
| source.identity | Git | Workspace source commitment |
| wsl.lifecycle | Microsoft WSL command surface | postcondition evidence only |
| durable.workflow | Temporal when cross-step durability is required | workflow domain payloads, not scheduling kernel |

The intended terminal architecture is composition over these owners, not a competing Ordivon
implementation of the same authority.

## 2. R6b — service materialization LEGO graph

```text
KnownFolder(CommonApplicationData)
        |
        v
[W1 state-root resolver]
        |
        +------------------+
        |                  |
        v                  v
[W2 env-file]         [W3 secret-file]
 read-only              read-only
        |                  |
        +--------+---------+
                 |
                 v
[W4 SCM service identity]
 NT SERVICE\OrdivonRuntime
 SERVICE_SID_TYPE_UNRESTRICTED
                 |
          +------+------+
          |             |
          v             v
[W5 resource ACL]   [W6 SCM lifecycle config]
 state=RW           own-process / auto
 bin=RX             failure actions
 config/token=R
          |             |
          +------+------+
                 |
                 v
[W7 read-back evidence]
 qc / qsidtype / qfailure / qfailureflag
 ACL descriptor validation
```

### W1 — state-root resolver

**Owner:** Windows Known Folder / `CommonApplicationData`.

Input: optional explicit absolute root.
Output: machine-level Runtime root.

Gate:
- default is derived from the Windows known-folder API surface;
- no assumption that the system drive is `C:`;
- all machine-owned Runtime files remain below this root.

Delete:
- literal-machine-root assumptions.

### W2 — configuration carrier

**Owner:** ordinary file semantics + Windows DACL.

Input: `--env-file <absolute path>`.
Output: allow-listed `RUST_LOG` / `ORDIVON_*` process environment.

Gate:
- unknown process arguments fail closed;
- duplicate keys fail closed;
- inline local/remote bearer values fail closed;
- native Windows file must have a protected read-only service DACL;
- parser has no shell evaluation semantics.

Delete:
- machine-global environment as the service configuration source.

### W3 — bearer secret carrier

**Owner:** file + protected Windows DACL.

Input: token file path.
Output: one bounded non-whitespace token.

Gate:
- service identity receives read only;
- SYSTEM and Builtin Administrators retain administrative control;
- inherited or unexpected principals fail closed.

Delete:
- bearer material in SCM ImagePath, env file, registry values or command-line arguments.

### W4 — service identity

**Owner:** SCM virtual account and service SID.

Contract:
- service account `NT SERVICE\OrdivonRuntime`;
- service SID enabled initially as `UNRESTRICTED`;
- no stored password;
- do not broaden required privileges before native evidence identifies the minimum set.

Gate:
- service token contains the expected service SID;
- no LocalSystem dependency is required merely to obtain file access.

Delete:
- generic interactive/admin user identity as Windows-main authority.

### W5 — resource ACL classes

Three separate contracts:

1. writable state: service=FullControl;
2. executable material: service=ReadAndExecute;
3. config/secrets: service=Read.

SYSTEM and Builtin Administrators retain FullControl.

Gate:
- DACL is protected;
- no unexpected explicit trustee;
- access mask matches the resource class exactly.

Delete:
- one-size-fits-all FullControl ACLs;
- POSIX chmod semantics on Windows resources.

### W6 — SCM lifecycle configuration

**Owner:** SCM.

Contract:
- `SERVICE_WIN32_OWN_PROCESS`;
- automatic start;
- native ServiceMain/HandlerEx/SetServiceStatus host;
- bounded restart actions are SCM failure actions;
- STOP/SHUTDOWN maps to Runtime cancellation, not arbitrary process killing.

Gate:
- install/update is idempotent;
- materializer does not start the service;
- service startup/recovery is tested separately in R6c.

Delete:
- Task Scheduler and custom watchdog as Windows-main lifecycle owner.

### W7 — configuration evidence

**Owner:** SCM query APIs / Windows security descriptor read-back.

Evidence:
- service config;
- SID type;
- failure actions + failure flag;
- service account;
- ImagePath;
- ACL resource-class checks.

Gate:
- desired-state materialization is not accepted merely because mutation commands returned zero;
- read-back must equal the desired contract.

## 3. R6c — native acceptance state machine

```text
STAGED
  |
  v
INSTALLED --readback--> CONFIG_VERIFIED
  |                         |
  | start                   |
  v                         |
START_PENDING               |
  | socket+Runtime ready    |
  v                         |
RUNNING <-------------------+
  |
  +--STOP----------> STOP_PENDING --> STOPPED
  |
  +--CRASH---------> SCM_RESTART --> RECONCILED --> RUNNING
  |
  +--WSL_TERMINATE-> RUNNING
  |
  +--WSL_SHUTDOWN--> RUNNING
  |
  +--COLD_BOOT-----> AUTO_START --> RECONCILED --> RUNNING
```

Acceptance evidence is intentionally split:

- **R6c-1 side-by-side candidate:** isolated service name/root/port; no live MCP replacement.
- **R6c-2 authority minimization:** observe actual service-token privilege requirements, then lock
  them down.
- **R6c-3 restart/reconciliation:** prove no duplicate Runtime dispatch after service crash/restart.
- **R6c-4 WSL independence:** terminate/shutdown WSL only after the candidate Windows Runtime can
  carry the acceptance observation independently.
- **R6c-5 final cutover:** exact accepted build becomes `windows-main`; only then retire the WSL
  control-plane bridge.

No R6c step may destroy the only currently reachable Runtime control plane.

## 4. EF6–EF8 — missing capability LEGO set

Current D-drive/VHD forcing workflow exposes exactly seven unresolved action capabilities.

| LEGO | Capability | Authority | Actuator | Required evidence |
|---|---|---|---|---|
| E1 | runtime/drain | Runtime admission | Runtime control provider | admission fenced + active-job projection |
| E2 | runtime/recover | Runtime reconciliation | Runtime control provider | MCP ready + doctor + reconciliation |
| E3 | storage/trim | Linux filesystem | Linux storage provider | trim command receipt + freed-block/postcondition |
| E4 | wsl/terminate | Microsoft WSL | Windows WSL provider | exact distro + terminated postcondition |
| E5 | storage/exclusive-open | Windows filesystem/VHD | Windows VHD provider | exclusive handle evidence |
| E6 | storage/compact | Windows VHD stack | Windows VHD provider | exact VHD identity + operation receipt |
| E7 | storage/verify-non-growth | filesystem observation | Windows VHD sensor/provider | before/after identity and byte-size evidence |

These seven are providers/capabilities, not new Runtime Kernel concepts.

## 5. EF execution composition

```text
Workflow
  |
  +--> observe
  +--> gate
  +--> act
  +--> verify
  +--> recover
  +--> compensate
          |
          v
Controller proposal
          |
          v
Authority check / lease
          |
          v
Provider
          |
          v
Platform authority
          |
          v
Evidence
          |
          v
Runtime durable execution truth
```

Ownership rules:

- Workflow owns ordering/time.
- Controller owns convergence.
- Authority owns permission to cause effects.
- Provider owns the effect adapter.
- Platform owns the primitive.
- Runtime owns durable physical execution truth.
- Host owns semantic continuity.
- Agent/Harness owns reasoning and route selection.

## 6. Migration ratchet

A compatibility carrier moves only through:

```text
CUSTOM
  -> SHADOWED_BY_STANDARD
  -> STANDARD_ACCEPTED_SIDE_BY_SIDE
  -> STANDARD_PRIMARY
  -> CUSTOM_UNREACHABLE
  -> CUSTOM_DELETED
```

Regression rule: a deleted custom authority may not be reintroduced without a new explicit
irreducibility argument and acceptance evidence.

## 7. Immediate execution order

1. finish R6b least-privilege ACL validation;
2. rerun Windows `-D warnings`, Linux MCP/Core and materializer tests;
3. commit R6b as one atomic service-materialization cut;
4. build an isolated R6c candidate service on a non-live port/root/name;
5. collect service identity, ACL, lifecycle and recovery evidence;
6. implement E1–E7 one provider at a time;
7. rerun the D-drive workflow resolver until unresolved capabilities = 0;
8. only after full acceptance, perform one final Runtime deployment/cutover;
9. delete superseded WSL/Task-Scheduler/watchdog compatibility carriers.
