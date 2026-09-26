# Native S4U WSL Authority R1

Status: accepted live architecture, 2026-09-24.

## Decision

Use Windows Task Scheduler native S4U as the user-context identity carrier for owner-scoped WSL lifecycle operations. Retire the custom local LSA S4U launcher that called `LsaLogonUser`, `DuplicateTokenEx`, and `CreateProcessAsUser`.

This is an authority-factorization decision, not a compact authorization decision.

## Authority split

1. Windows Runtime / LocalSystem owns orchestration, observation, evidence capture, and `Start-ScheduledTask`. It does not own the user WSL distro identity.
2. Windows Task Scheduler native S4U for `zycxfyh\\16663` owns the non-interactive user-context identity carrier.
3. WSL owns distro lifecycle and distro-registration semantics.
4. Hyper-V `Optimize-VHD` owns detached VHD compaction.
5. The D-drive R2/R3 gate owns maintenance admission: zero Runtime capacity holders, healthy Runtime/Doctor, fresh trim, exact ready receipt, short-lived exact authorization, detached/exclusive VHD proof, one bounded compact pass, and post-recovery requalification.

## Live accepted projection

The 2026-09-24 machine migration established:

- `Ordivon WSL Control Plane Recovery`: user `16663`, `LogonType=S4U`, `RunLevel=Limited`, enabled.
- Windows Runtime / LocalSystem successfully triggered this task with `Start-ScheduledTask`.
- The resulting process identity was `zycxfyh\\16663`; WSL substrate reported ready and Runtime/Host/Gateway were active; task result was 0.
- `Ordivon-DDrive-Offline-Compact`: user `16663`, `LogonType=S4U`, `RunLevel=Highest`, disabled by default, action bound to the R2/R3 fenced live runner.
- The bootstrap native-S4U probe and prior temporary Interactive/AtLogOn compact tasks were removed after evidence capture.
- Historical custom `s4u_local_launcher*` binaries/source were removed from the active Recovery path and retained only as retired evidence.

Machine-local evidence paths:

- `C:\\ProgramData\\Ordivon\\Runtime\\RecoverySupervisor\\NATIVE_S4U_WSL_AUTHORITY_R1.md`
- `C:\\ProgramData\\Ordivon\\Runtime\\RecoverySupervisor\\state\\native-s4u-authority-r1\\migration-receipt.json`
- `C:\\ProgramData\\Ordivon\\Runtime\\RecoverySupervisor\\state\\native-s4u-authority-r1\\final-projection.json`
- retired custom implementation: `C:\\ProgramData\\Ordivon\\Recovery\\retired\\custom-s4u-launcher-20260923`

## Trigger semantics

Identity carrier and scheduling trigger are separate LEGO. A task may retain a historical LogonTrigger for continuity while still using `LogonType=S4U`; owner-independent orchestration may trigger it directly. Future liveness work may change startup/event/condition triggers independently. Do not revert identity to Interactive merely to change scheduling behavior.

## Security and architecture constraints

Do not reintroduce any of the following for this capability:

- custom `LsaLogonUser` S4U token brokers;
- `DuplicateTokenEx` against existing user processes;
- token extraction, token injection, or impersonation of ambient user processes;
- password persistence solely to obtain WSL lifecycle authority;
- LocalSystem/service-account WSL registration as a substitute for the owning user distro.

Native S4U is a local-only carrier. It is not a general network-credential mechanism.

## Maintenance invariant

`S4U identity available` does **not** imply `compact authorized`.

Offline VHD maintenance remains fail-closed unless the existing R2/R3 maintenance protocol produces a fresh admission-fenced ready receipt and a matching short-lived authorization. WSL must be offline and the VHD must be detached/exclusively openable before `Optimize-VHD`. Post-maintenance Runtime, Host, Gateway, ext4, workspace headroom guard, and storage-pressure timer must be requalified.

## Migration status

Live machine replacement is complete. Repository materialization of the exact Scheduled Task desired state may be added under the Workstation owner; any such materializer must preserve the authority split above and must not embed credentials or custom token code.
