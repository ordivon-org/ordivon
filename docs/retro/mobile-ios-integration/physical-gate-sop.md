# Mobile iOS Physical Qualification SOP R1

This SOP executes `physical-gate-spec.md`. It is intentionally provider-native and narrow.

## 0. Preconditions

Read:
- `docs/retro/mobile-ios-integration/physical-gate-spec.md`;
- `docs/retro/mobile-ios-integration/gap-register.md`;
- `docs/retro/mobile-ios-integration/verification.md`.

Resolve the current Workstation bindings for `go-ios-1-3-2` and `mobilecli-1-0-20`. Reject drift before touching a device.

## 1. USB discovery

On Windows, read present PnP devices and require at least one `VID_05AC` instance.

Then run the exact admitted carriers:

```text
ios.exe list
mobilecli.exe devices --include-offline --platform ios
```

Select one physical UDID only when both providers identify the same device. Record provider-native identifiers; do not invent an Ordivon device ID.

If the lists are empty, stop with `NO_USB_DEVICE`.

## 2. Trust and Developer Mode

Use provider readback to distinguish:
- untrusted device;
- Developer Mode disabled;
- paired and ready.

Any required user confirmation on the iPhone/iPad is a device-side authorization step, not a failure of Runtime.

Do not proceed until discovery is stable across two consecutive reads.

## 3. Tunnel

For iOS 17+:

```text
ios.exe tunnel start --userspace --udid=<selected-udid>
ios.exe tunnel ls
```

Start with the lowest current Windows execution authority. Escalate only on observed authority failure.

PASS requires the selected UDID to have a provider-read tunnel. Keep the tunnel process identity/evidence; do not infer health from a launched process.

## 4. Exact runner

Fetch or reuse:

```text
https://github.com/mobile-next/devicekit-ios/releases/download/0.0.34/devicekit-ios-runner.ipa
```

Require:

```text
SHA-256 = a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf
```

Reject any other runner.

## 5. Signing/bootstrap

Do not use `mobilecli agent install` on Windows while upstream mobile-next/mobilecli#380 remains open.

Use go-ios 1.3.2 with the exact runner:

```text
ios.exe ui install devicekit --udid=<selected-udid> --path=<exact-0.0.34-ipa> --p12file=<operator-p12> --profile=<operator-mobileprovision>
```

If a P12 password would need to appear in a durable Runtime argument, do not submit the Job. Use an approved bootstrap channel or stop with `SIGNING_INPUT_UNAVAILABLE`.

After install:

```text
mobilecli.exe agent status --device <selected-udid>
```

Require agent version `0.0.34`.

## 6. Read-only E2E

```text
mobilecli.exe snapshot --device <selected-udid>
mobilecli.exe screenshot --device <selected-udid> -o <bounded-output-path>
```

Require a non-empty structured UI snapshot and a valid image artifact.

## 7. Reversible effect

Choose one non-destructive target from the fresh snapshot. Perform exactly one effect, then immediately re-read state.

Preferred first effects:
1. HOME button if it changes current state safely;
2. a non-destructive navigation control visible in the snapshot;
3. a coordinate tap only after the target is identified from current evidence.

Never select delete, purchase, submit, send, account, security, or destructive controls for qualification.

## 8. Recovery

For each recovery episode:
1. record pre-episode identity/agent/UI state;
2. induce exactly one failure;
3. reconnect/restart through provider-native mechanisms;
4. re-read device identity;
5. re-read agent status;
6. re-read UI state.

Unknown outcome is not PASS.

## 9. Completion

Gate 2-6 may be marked complete only from fresh physical evidence. Update `gap-register.md` and `verification.md`; do not add a new mobile abstraction solely because the experiment succeeded.
