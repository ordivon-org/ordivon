# Mobile iOS Physical Qualification Spec R1

## Purpose

Close only the real-device frontier that remains after current-main carrier convergence. This spec does not create a Mobile Runtime, Mobile Gateway capability, mobile workflow language, or custom iOS driver.

## Exact source cut

- Ordivon main at planning start: `d067442a26237552910a79e4f06e5d0450553b6f`.
- go-ios carrier: 1.3.2, SHA-256 `c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5`.
- mobilecli carrier: 1.0.20, SHA-256 `018dcec38ee4f39ef24fd0987d85e04914294651b8da770c647f21ca04029aa4`.
- mobilecli source identity: VCS revision `b8bd2f90d2af74b2242f5da79e87055e4056d48d`.
- required DeviceKit runner: 0.0.34, SHA-256 `a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf`.

## Ownership

- Workstation owns exact local carrier materialization/binding.
- Windows Runtime owns Job/Attempt/execution evidence.
- go-ios owns Apple transport, tunnel, signing/install primitives.
- mobilecli owns high-level device/agent/UI automation after the runner is available.
- DeviceKit owns on-device UI automation semantics.
- Harness/domain code owns task suitability and authorization.
- Signing authority is bootstrap-only and must not silently become ordinary Agent authority.

## Gate 2 — physical discovery

PASS requires all of:
1. Windows reports at least one present Apple USB device with VID_05AC.
2. `ios list` succeeds and reports the selected physical device.
3. `mobilecli devices --include-offline --platform ios` succeeds and reports the same device identity.
4. Trust/Developer Mode requirements are satisfied or exposed as an explicit blocker.

A Bluetooth/iAP record alone is not PASS.

## Gate 3 — transport

For iOS 17+, first falsify direct `ios tunnel start --userspace --udid=<UDID>`, then retain the proven steady-state owner. Current-node evidence shows the foreground command consumes the single Windows native execution lane, so the steady-state owner is the Workstation `mobile_ios_tunnel` Scheduled Task adapter.

The control plane may use elevated authority to install/manage the task. The task itself must run the exact go-ios carrier as the existing Runtime service account with Limited run level. Do not copy browser `active_user` authority by analogy.

PASS requires an independent service/limited Runtime Job to read back the selected-device tunnel and RSD state. Process start or Scheduled Task state alone is insufficient.

## Gate 4 — runner bootstrap

The primary runner is the exact DeviceKit iOS 0.0.34 IPA identified above.

The selected Windows bootstrap implementation is go-ios 1.3.2 with an explicit `--path` to that exact artifact. Do not use go-ios's default DeviceKit 0.0.18 download. Do not use mobilecli's Windows `agent install` path while upstream #380 remains unresolved.

Signing material is external bootstrap authority. No signing secret value may be placed in repository state, Runtime arguments, stdout, stderr, or ordinary evidence. If no approved signing-material path is available, return `SIGNING_INPUT_UNAVAILABLE`; do not invent a secret broker.

PASS requires:
1. exact runner digest verified before signing;
2. signed runner installed on the selected UDID;
3. `mobilecli agent status --device=<UDID>` reports version 0.0.34 and the DeviceKit runner bundle;
4. provider-native health/readback succeeds.

## Gate 5 — first reversible UI effect

Read first:
1. `mobilecli snapshot --device=<UDID>`;
2. `mobilecli screenshot --device=<UDID>`.

Then perform one reversible, non-destructive UI effect selected from the observed current screen. Verify the resulting state with a fresh structured snapshot or screenshot. Do not infer success from command exit alone.

## Gate 6 — recovery

Qualify, in order:
1. device lock/unlock;
2. USB disconnect/reconnect;
3. 30-minute idle;
4. DeviceKit process restart;
5. tunnel restart;
6. Windows Runtime/service restart.

Each episode requires readback of device identity, agent status, and a fresh UI observation before declaring recovery.

## Second-provider rule

go-ios and mobilecli already prove a shared carrier-binding seam. Do not introduce a domain-level `mobile.device` capability until both have completed physical-device operations and the actual semantic overlap is observed.

## Stop conditions

Stop rather than improvise when:
- VID_05AC remains zero;
- device identity differs across providers;
- Trust/Developer Mode is unresolved;
- exact 0.0.34 runner digest differs;
- signing authority is unavailable;
- delivery outcome is unknown after a device/tunnel failure.
