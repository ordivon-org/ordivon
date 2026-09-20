# Native Windows Runtime R6c Acceptance Evidence R1

Status: historical R6c acceptance ledger. C1-C4 are accepted; C5 live-topology cutover and WSL-carrier retirement are complete, while promotion of the latest Runtime source remains subject to the structured-release Git authority gate.
Date: 2026-09-19; status amended 2026-09-20
Workspace: `ws-runtime-fabric-final-r1-20260919`
Historical source revision: a367dbc2c903ab0cd792bd5968628425ebb1da18
Current accepted candidate release: 00ae7525ff0d444f91f6250d5f055c635c0e092e

## Candidate identity

- service: `OrdivonRuntimeR6Candidate`
- display name: `Ordivon Runtime R6 Candidate`
- node id: `windows-main-r6-candidate`
- bind: `127.0.0.1:18997`
- state root: `C:\ProgramData\Ordivon\RuntimeCandidateR6`
- staging root: `C:\ProgramData\Ordivon\RuntimeCandidateR6Stage`
- Runtime executable SHA-256:
  0c84fb699fbff453c0c3dbf1559bb5d2da066b56519cf4c87ad8c893d218c857
- Windows Job launcher SHA-256:
  bf356744461c13d61dced95b922bceb081521a4b521db4826222b2266b63b35b
- Windows privileged broker SHA-256:
  24cc9f2c9a3758f53fc407cdcc12bbcfb28e620975a7e9b5b52c366718e2d92b

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

This evidence proves the default least-privilege execution carrier only. It is not complete
Windows authority acceptance. The native control plane should not expose ambient administrator
authority, but explicit `windows/elevated` requests may be admitted through a distinct local
privileged broker after that broker independently passes its authority/evidence gate. Direct
limited dispatch and broker-backed elevated dispatch must both bind the same authoritative launcher
PID + process-creation FILETIME before Runtime commits supervisor ownership.

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

## Superseding C1/C2 evidence — 2026-09-20

The earlier failure-injection section above is retained as historical evidence. It was superseded
by native candidate-controlled experiments after structured Windows release
00ae7525ff0d444f91f6250d5f055c635c0e092e was deployed.

### C1 crash / SCM recovery — PASS

Dedicated crash harness Job:
job-01a0bd5c-d89e-7e31-9db5-7e331c9bfa67

Observed:
- candidate PID 18528 -> 13248;
- old PID absent;
- SCM returned Running;
- authenticated runtime.describe succeeded before and after the crash;
- node identity remained windows-main-r6-candidate, native Windows.

Repeated acceptance faults exposed the configured SCM sequence 5s / 15s / 60s with a
86400s reset period. The harness now uses a 90-second recovery window so third and later
faults cannot produce a false negative.

### C2 active Job reconciliation — PASS

Final harness Job:
job-01a0bd75-b54d-78a2-b6f6-1197f29c0007

Target:
- Workspace ws-r6c-native-recovery-1aaa4fb800bd424f;
- Job job-01a0bd75-b93e-7a91-a921-2887b415179d;
- Attempt attempt-01a0bd75-b93e-7a91-a921-289b1a392b9b.

The acceptance fixture was created by the real limited service token instead of being fabricated
by LocalSystem and then re-owned. The Runtime was crashed while the target was working.
SCM recovery changed PID 5180 -> 7032; the target completed as succeeded/committed with
R6C_ACTIVE_JOB_DONE; exact replay returned the same Job and Attempt; replaySameJob=true.

Post-fault Doctor Job:
job-01a0bd77-0258-7153-81ae-77d1d655757a

Doctor reported:
- integrityCheck = ok;
- violationCount = 0;
- recoveryRequiredAttempts = 0;
- migration version 6.

The acceptance harness itself was corrected in two places exposed by this run:
1. fixture Git authority now stays with the real limited service identity; LocalSystem no longer
   simulates that identity by changing repository ownership;
2. working-state observation uses job.observe, while job.get remains projection-only.

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
| R6c crash/failure-action restart | PASS |
| R6c active-Job reconciliation | PASS |
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

## C3 WSL independence — PASS

Exact release: 00ae7525ff0d444f91f6250d5f055c635c0e092e.

The accepted destructive run used the interactive Windows identity that owns the archlinux
registration to execute exact wsl.exe --terminate archlinux. The fault returned exit code 0 and
the post-fault user-side observation no longer listed archlinux as running.

The native candidate did not restart or disappear: OrdivonRuntimeR6Candidate remained Running/Auto
at PID 7032 before and after the fault. The now-native Cloudflare ingress also remained
Running/Auto at PID 7464 with four provider-native HA connections. While archlinux was still
offline, the external Windows Runtime connector successfully served authenticated runtime.describe
and admitted a fresh native Windows Runtime read Job.

Evidence:
- docs/evidence/windows-r6c-c3-pass-20260920.json;
- fault witness SHA-256:
  75c1b06c9b649ea46f78732e1f8d8a8be724455e22784867ff3fd3957f982d83.

After acceptance, Workstation retired ordivon-cloudflare-canary.service on WSL. Linux production
Cloudflare A/B remained active and the Windows Runtime connector remained remotely reachable.
This retirement concerns only the Windows Runtime ingress carrier; it does not yet retire the
separate Linux-hosted windows_native execution compatibility carrier required until C5.

## C3/C4 preflight authority correction — 2026-09-20

Frozen evidence:
- file: 00ae7525ff0d444f91f6250d5f055c635c0e092e-c3-c4-preflight-v3.json;
- digest: sha256:dfa42acb7aa34ad98cfd0addbd796ccd5ef29ccb0488e87818d29f582156e41a.

The WSL ownership boundary was clarified without terminating WSL:
- archlinux is a WSL2 distribution registered in an interactive-user hive;
- limited candidate service authority sees no user-owned running distributions;
- elevated Runtime authority is LocalSystem;
- direct elevated wsl.exe probe failed with WSL_E_LOCAL_SYSTEM_NOT_SUPPORTED;
- read-only probe Job job-01a0bd7d-7e9d-7003-b3a9-1be52ee7a433 proved the existing
  linux-local/windows-native carrier runs under the interactive Windows user identity and sees
  archlinux as running.

Therefore C3 must not be implemented by broadening Runtime service authority. The native Runtime
service is the independent observation carrier; the destructive wsl.exe fault belongs to the
interactive user identity that owns the distribution.

The same preflight freezes the exact-00ae release receipt, candidate manifest, six artifact digests,
env-file digest, SCM AutoStart identity, boot timestamp, and Runtime PID. It is the before-reboot
half of C4 only; a future real reboot is still required for the after-reboot witness.

## Next evidence gates

1. obtain an exact-00ae7525 cold-boot automatic-start witness from the frozen preflight baseline;
2. after C4 passes, perform C5 production cutover and delete the remaining Linux-hosted Windows
   execution compatibility carrier;
3. optionally run a broader wsl.exe --shutdown workstation fault after all unrelated WSL-dependent
   work has an explicit disposition; this is no longer a blocker for C3.

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
