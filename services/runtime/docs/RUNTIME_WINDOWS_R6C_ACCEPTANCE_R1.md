# Native Windows Runtime R6c Acceptance Evidence R1

Status: partial acceptance; no production cutover
Date: 2026-09-19
Workspace: `ws-runtime-fabric-final-r1-20260919`
Source revision: `a367dbc2c903ab0cd792bd5968628425ebb1da18`

## Candidate identity

- service: `OrdivonRuntimeR6Candidate`
- display name: `Ordivon Runtime R6 Candidate`
- node id: `windows-main-r6-candidate`
- bind: `127.0.0.1:18997`
- state root: `C:\ProgramData\Ordivon\RuntimeCandidateR6`
- staging root: `C:\ProgramData\Ordivon\RuntimeCandidateR6Stage`
- Runtime executable SHA-256:
  `fb7095fbbd2d72214204770632583b7fc74209fe516fb3418866d9d8d3c9b66d`
- Windows Job launcher SHA-256:
  `a14ea554c4aa4df8c3ebdab2d49ba9d8f0fd071a75194d0c4ddb7bab8b4cde5f`

The candidate is side-by-side and does not own the live `8897/windows-main` identity.

## R6c-1 materialization

Windows-native preview job:
`job-01a0b822-f947-76c2-8145-547f0c383a57`

Result: PASS.

The preview projected:

- `WIN32_OWN_PROCESS`
- automatic start
- account `NT SERVICE\OrdivonRuntimeR6Candidate`
- service SID type `UNRESTRICTED`
- restart failure actions 5s / 15s / 60s
- no predeclared required-privilege broadening
- independent root, bind and node identity.

Windows-native materialization job:
`job-01a0b823-1c04-7ef1-a87a-100afc940947`

Result: PASS.

SCM read-back from the materializer confirmed:

- TYPE = `WIN32_OWN_PROCESS`
- START_TYPE = `AUTO_START`
- SERVICE_START_NAME = `NT SERVICE\OrdivonRuntimeR6Candidate`
- SERVICE_SID_TYPE = `UNRESTRICTED`
- failure reset = 86400 seconds
- restart delays = 5000 / 15000 / 60000 ms
- failure actions on non-crash failures = TRUE.

The materializer did not start the service.

## ACL evidence

Limited-token ACL read-back was denied, which is consistent with the protected candidate tree.

Elevated read-back job:
`job-01a0b823-c7f6-7333-ac59-68069a2d97b4`

Service SID:
`S-1-5-80-2030400495-3314078154-3096635645-441634556-3298015213`

Every inspected ACL was protected and every inspected ACE was non-inherited.

Observed service access masks:

| Resource class | Observed service mask | Meaning |
|---|---:|---|
| candidate root / executable | 1179817 | ReadAndExecute + Synchronize |
| store / registry | 2032127 | FullControl |
| env config / bearer token | 1179785 | Read + Synchronize / Win32 FILE_GENERIC_READ |

SYSTEM and Builtin Administrators retained FullControl.

This matches the R6b resource-class split.

## SCM lifecycle evidence

Start job:
`job-01a0b823-ffaf-7fb1-903f-03a929ca4534`

Result: PASS.

Observed:
- Status = Running
- CanStop = true
- ServiceType = Win32OwnProcess

Authenticated MCP self-probe before failure injection:
`job-01a0b824-a9c0-7fd2-9835-0aa88390d031`

Result: PASS.

Observed Runtime projection:

- nodeId = `windows-main-r6-candidate`
- platform = `windows`
- native = true
- `local_linux.available = false`
- `local_linux.configured = false`
- `windows_native.available = true`
- `windows_native.configured = true`
- Execution Fabric authority contexts = `windows/limited`
- provider = `provider/windows-main-r6-candidate/windows-native-launcher-v1`.

This is the desired least-privilege direction: the native control plane does not advertise Linux
execution or ambient elevated Windows authority.

Graceful stop job:
`job-01a0b824-ec4b-7bd0-936e-89bf572f9b20`

Result: PASS; SCM reached Stopped.

Restart job:
`job-01a0b825-0c10-7390-a2ac-0ecbbe004e7d`

Result: PASS; SCM returned Running, observed process id 27784.

## Failure injection / WSL interop separation

Crash-recovery probe:
`job-01a0b825-2fac-7160-b2a3-d4f4eecf58db`

The live Linux-hosted Windows provider lost the probe Attempt as
`DISPATCH_OUTCOME_UNKNOWN`; therefore this run does **not** prove that the candidate process was
actually terminated and recovered. The failure is classified as inconclusive, not PASS.

A subsequent live Windows-provider query failed before dispatch with:

`UtilAcceptVsock:273: accept4 failed 110`

This is evidence that the existing WSL-hosted Windows provider still depends on an interop/vsock
path that can fail independently of the candidate.

After that interop failure, an unauthenticated liveness probe to the candidate endpoint returned
HTTP 401:

job:
`job-01a0b826-4d41-76e0-97a8-6a4c6c076e78`

Result: PASS.

Interpretation: the candidate HTTP/MCP listener remained reachable while the old WSL-to-Windows
provider path was unavailable. This is useful independence evidence, but it is not equivalent to a
full `wsl.exe --shutdown` acceptance.

## Current verdict by LEGO

| LEGO | Status |
|---|---|
| W1 KnownFolder/ProgramData root | PASS |
| W2 env-file carrier | PASS |
| W3 token-file carrier | PASS |
| W4 virtual service identity | PASS |
| W5 resource ACL classes | PASS |
| W6 SCM lifecycle materialization | PASS |
| W7 SCM/ACL read-back | PASS |
| R6c start/readiness | PASS |
| R6c graceful stop | PASS |
| R6c restart | PASS |
| R6c crash/failure-action restart | INCONCLUSIVE |
| R6c active-Job reconciliation | NOT YET PROVEN |
| R6c actual WSL terminate/shutdown independence | NOT YET PROVEN |
| R6c cold boot auto-start | NOT YET PROVEN |
| production cutover | NOT PERFORMED |

## Newly exposed compatibility debt

The current live Linux node still exposes Windows execution through a WSL-hosted provider whose
runtime-context probe can fail on the WSL interop/vsock path.

This is now a separate LEGO:

`compat/windows-via-wsl-interop`

It must not be repaired into another permanent custom control plane. Its acceptable end states are:

1. native `windows-main` becomes primary and the carrier is deleted; or
2. it remains a temporary fallback with explicit degraded-state evidence.

## Next evidence gates

1. obtain an unambiguous SCM crash/restart witness that does not depend on the failing live
   WSL-to-Windows provider;
2. run a real Job under the candidate, inject service failure, and verify Registry reconciliation
   without duplicate dispatch;
3. perform Windows-owned WSL terminate/shutdown witness only after observation itself no longer
   depends on WSL;
4. test cold boot automatic start;
5. only then promote the exact accepted build to production and delete the compatibility carrier.

## C2 parent-owned launcher identity correction

Source correction completed on 2026-09-19; native acceptance remains pending.

The C2 failure was localized to the boundary after durable DISPATCH_ISSUED and before
windows-launcher-start.json. Registry truth showed a starting Attempt with an active
reservation, no attempt_supervisor_owners row, and no launcher/target/result evidence. The
installed launcher digest matched the committed execution-provider digest exactly.

The native Runtime now uses the Windows process handle returned by the parent CreateProcess
boundary to read the launcher PID and process creation FILETIME immediately after spawn. Runtime
publishes the first-stage launcher evidence and binds the existing windows_launcher_v1
Supervisor Owner before waiting for target-start evidence. The launcher no longer races the parent
to self-publish that first-stage evidence in native-control-plane mode.

windows-start.json remains a second, launcher-owned witness that the launcher/Job Object/target
path progressed far enough to establish target-start identity. If an owner was already bound from
the parent observation, target-start identity must match PID, process creation time, launcher image
digest, and Job name; it does not create a second owner.

This does not introduce a new lifecycle state, Registry, routing layer, workflow, Lens, or retry
mechanism. It narrows the unknown window by using the OS-native process identity already held by
the parent Runtime. Existing no-redrive semantics remain in force for ambiguous committed
dispatches.

Validation completed for the source correction:

- Runtime Core: 236/236 tests PASS;
- Runtime MCP library: 57/57 PASS;
- Runtime MCP binary/auth: 10/10 PASS;
- Windows MCP cross-compile with RUSTFLAGS=-D warnings: PASS;
- R6c acceptance harness static tests: 6/6 PASS.

The correction has not been installed into OrdivonRuntimeR6Candidate and is not production
acceptance evidence. C2 must be rerun in the final native acceptance window before the native
Windows Runtime can be promoted.
