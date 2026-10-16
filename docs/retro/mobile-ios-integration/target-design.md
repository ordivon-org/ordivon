# Mobile iOS Integration Target Design

## Target shape

Consumer/domain semantics
  -> existing Harness/Gateway execution seam
  -> Runtime execution.windows
  -> exact Workstation-bound Windows native tool
  -> mobilecli 1.0.20 for high-level device automation
  -> DeviceKit iOS 0.0.34
  -> physical Apple device

Bootstrap-only path:

operator-authorized Apple signing material
  -> go-ios 1.3.2
  -> exact DeviceKit iOS 0.0.34 runner
  -> sign/install on the selected device

Transport/fallback path:

go-ios 1.3.2
  -> pairing / iOS 17+ tunnel / low-level diagnostics
  -> DeviceKit or WDA fallback

## This slice

Deepen existing mature seams rather than add a mobile subsystem.

Desired binding behavior:
1. A declaration names an exact executable, execution target, and expected SHA-256.
2. local_linux keeps the existing pathlib behavior.
3. windows_native reuses the existing Windows drive-path projection used by professional software.
4. Binding verifies exact bytes before returning AVAILABLE.
5. Binding remains non-semantic: no device authority, no task success, no Runtime admission claim.

Two real Windows-native carriers now prove the existing managed-equipment seam. That is sufficient evidence for carrier binding; it is still not evidence for a new domain-level mobile capability.

## Carrier policy

Do not broaden Runtime to C:\ProgramData\Ordivon.
Use the already admitted, ACL-controlled, versioned native-tools subtree of the current Windows Runtime root.

Current live carriers:
- C:\ProgramData\Ordivon\RuntimeCandidateR6\native-tools\go-ios\v1.3.2\ios.exe
- C:\ProgramData\Ordivon\RuntimeCandidateR6\native-tools\mobilecli\v1.0.20\mobilecli.exe

Promotion/cutover path naming remains an operator/deployment concern and must not be inferred as a universal mobile abstraction.

## Provider roles

- `mobilecli 1.0.20`: preferred high-level provider after the on-device agent exists. It owns device discovery, daemon/tunnel continuity, agent status, accessibility/UI tree, gestures, screenshots, app operations, and its JSON-RPC surface.
- `DeviceKit iOS 0.0.34`: exact on-device runner expected by mobilecli 1.0.20. The official runner IPA SHA-256 is `a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf`.
- `go-ios 1.3.2`: Windows-native bootstrap and low-level Apple transport provider. It owns pairing/tunnel primitives and can sign/install an explicitly supplied DeviceKit/WDA artifact using provider-native P12/profile semantics.
- Workstation `managed_equipment`: exact executable/digest binding for go-ios and mobilecli.
- Runtime `execution.windows`: execution truth for admitted carrier Jobs.

The high-level and bootstrap roles are intentionally different. mobilecli 1.0.20's own real-iOS installer is not the Windows bootstrap owner because its resign path still invokes macOS `/usr/bin/security` and `codesign` (upstream issue #380).

## Signing authority boundary

Signing is required only to bootstrap or upgrade the on-device runner. It is not required for ordinary source/screenshot/tap/app operations after a compatible runner is installed.

Therefore:
- do not grant Harness or ordinary Agent execution a long-lived Apple developer private key merely to support daily device control;
- do not put P12 passwords, p8 contents, or other signing secret values into Runtime arguments, source files, stdout, stderr, or ordinary evidence;
- do not generalize the existing Jev DPAPI materializer into an Apple secret subsystem without a repeated real operational need;
- if automated bootstrap later becomes necessary, bind it to a separately approved secret authority and exact go-ios carrier instead of adding signing semantics to Harness.

Until such an authority exists, initial runner signing/install remains an explicit operator-authorized bootstrap effect. This is a bounded gap, not a reason to add a Mobile Runtime.

## Native-tool carrier realization

`native-tool-carriers.json` owns source/archive/member/executable/target commitments; `materialize-native-tool-carrier.ps1` owns the common staged transaction. Provider-specific mobile behavior is deliberately absent. Runtime remains the execution owner and the managed-equipment catalog remains the exact node-local binding projection.

The materializer is explicit rather than a daemon or workflow system. Existing exact target bytes return unchanged without network access; mismatched versioned targets fail closed rather than being overwritten.

## Persistent tunnel lifecycle ownership

Fresh physical qualification proved that the iOS 17+ userspace tunnel is long-lived provider state, not one Runtime command result. A direct `ios tunnel start --userspace` under Windows Runtime limited authority negotiated successfully, but it occupied the current single native execution lane and prevented the independent readback command needed by later mobile work.

The retained seam is Workstation-owned process lifecycle, reusing the repository's existing Windows Scheduled Task pattern:

- elevated Workstation control plane installs/starts/stops/removes one exact task;
- the task runs the exact digest-fenced go-ios carrier as `NT SERVICE\\OrdivonRuntimeR6Candidate` with `RunLevel Limited`;
- pair-record/self-identity state lives under that service identity's provider-owned LocalAppData, not under a Runtime Workspace;
- short Runtime Jobs remain service/limited and independently execute `tunnel ls`, RSD reads, discovery, and later provider commands;
- the tunnel-owner receipt explicitly does not grant device-control authority, runner readiness, or domain success.

This is a lifecycle adapter at an already-proven Workstation seam. It is not a Mobile Runtime, workflow engine, or domain-level `mobile.device` capability.

## Bootstrap artifact ingress

The current node's GitHub route is owned by the interactive Windows user/VPN session: service/Linux downloads timed out while the same `curl.exe` under `active_user` fetched the exact public DeviceKit 0.0.34 runner. Public artifact ingress may therefore use active-user networking, but the bytes are SHA-256 fenced before and after elevated promotion into service-owned provider state. This network ownership does not transfer device-control authority to the active user.
