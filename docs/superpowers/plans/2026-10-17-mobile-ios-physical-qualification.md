# Mobile iOS Physical Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify one real iPhone/iPad from USB discovery through reversible UI automation and recovery using current mature Windows providers without creating a new Ordivon mobile subsystem.

**Architecture:** Workstation supplies exact go-ios/mobilecli carriers; Windows Runtime supplies execution evidence; go-ios owns bootstrap/tunnel; mobilecli + DeviceKit own high-level UI automation. Signing is an explicit bootstrap authority and is not promoted into ordinary Agent authority.

**Tech Stack:** Windows Runtime, Workstation managed_equipment, go-ios 1.3.2, mobilecli 1.0.20, DeviceKit iOS 0.0.34.

**Spec:** `docs/retro/mobile-ios-integration/physical-gate-spec.md`

## Global Constraints

- go-ios exact SHA-256: `c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5`.
- mobilecli exact SHA-256: `018dcec38ee4f39ef24fd0987d85e04914294651b8da770c647f21ca04029aa4`.
- DeviceKit runner version: `0.0.34`.
- DeviceKit runner SHA-256: `a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf`.
- No mobile-specific Runtime/Gateway capability.
- No mobilecli Windows agent installer while upstream #380 remains unresolved.
- No signing secret value in repository state, Runtime arguments, stdout, stderr, or ordinary evidence.
- Unknown outcome is not success.

---

### Task 1: Physical identity parity

**Files:**
- Modify after evidence exists: `docs/retro/mobile-ios-integration/verification.md`
- Modify after evidence exists: `docs/retro/mobile-ios-integration/gap-register.md`

**Interfaces:**
- Consumes: Windows PnP, exact go-ios list, exact mobilecli devices.
- Produces: one selected provider-native UDID or a bounded blocker.

- [ ] Connect one iPhone/iPad over a USB data path and complete the device-side Trust prompt.
- [ ] Read Windows PnP and require `VID_05AC > 0`.
- [ ] Run exact `ios.exe list`.
- [ ] Run exact `mobilecli.exe devices --include-offline --platform ios`.
- [ ] Compare provider-native device identities. If they differ, stop with `DEVICE_IDENTITY_MISMATCH`.
- [ ] Repeat both provider reads once; require stable identity before Task 2.

### Task 2: Least-authority iOS 17+ tunnel

**Files:**
- Evidence-only updates to the same verification/gap documents.

**Interfaces:**
- Consumes: selected UDID from Task 1.
- Produces: a provider-read healthy tunnel and minimum required Windows authority.

- [ ] Submit `ios.exe tunnel start --userspace --udid=<selected-udid>` with the lowest current Windows authority.
- [ ] Run `ios.exe tunnel ls` and require the selected device tunnel to be present.
- [ ] If the first authority fails for an authority reason, repeat once with active-user limited authority.
- [ ] Record the lower passing authority; do not copy browser authority by analogy.
- [ ] Re-run `ios.exe list` and `mobilecli.exe devices --include-offline --platform ios`.

### Task 3: Exact DeviceKit bootstrap

**Files:**
- Evidence-only updates unless a real missing integration seam is discovered.

**Interfaces:**
- Consumes: selected UDID, exact DeviceKit 0.0.34 IPA, operator-authorized signing inputs.
- Produces: installed runner accepted by mobilecli.

- [ ] Fetch/reuse DeviceKit 0.0.34 and verify SHA-256 `a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf`.
- [ ] If no approved signing input path exists, stop with `SIGNING_INPUT_UNAVAILABLE`; do not build a credential subsystem in this task.
- [ ] Use go-ios `ui install devicekit` with `--path` pointing at the exact 0.0.34 IPA and the selected UDID.
- [ ] Run `mobilecli.exe agent status --device <selected-udid>`.
- [ ] Require reported agent version `0.0.34` and a DeviceKit runner bundle ID.

### Task 4: Read-only semantic E2E

**Files:**
- Evidence-only updates.

**Interfaces:**
- Consumes: healthy installed DeviceKit 0.0.34.
- Produces: structured UI plus screenshot evidence.

- [ ] Run `mobilecli.exe snapshot --device <selected-udid>`; require a non-empty structured tree.
- [ ] Run `mobilecli.exe screenshot --device <selected-udid> -o <bounded-output-path>`; require a valid non-empty image.
- [ ] Re-run `mobilecli.exe agent status --device <selected-udid>`; require 0.0.34 after both observations.

### Task 5: One reversible effect with readback

**Files:**
- Evidence-only updates.

**Interfaces:**
- Consumes: current UI tree from Task 4.
- Produces: one effect receipt plus independent resulting-state observation.

- [ ] Select one explicitly non-destructive target from the fresh UI tree.
- [ ] Execute exactly one HOME/button/navigation/tap effect through mobilecli.
- [ ] Immediately run a fresh snapshot and screenshot.
- [ ] Require a state transition consistent with the intended effect; command exit alone is insufficient.
- [ ] If delivery becomes unknown, stop and read back before any retry.

### Task 6: Recovery qualification

**Files:**
- Modify: `docs/retro/mobile-ios-integration/verification.md`
- Modify: `docs/retro/mobile-ios-integration/gap-register.md`

**Interfaces:**
- Consumes: known-good physical E2E from Task 5.
- Produces: recovery standing for six bounded episodes.

- [ ] Qualify lock/unlock.
- [ ] Qualify USB disconnect/reconnect.
- [ ] Qualify 30-minute idle.
- [ ] Qualify DeviceKit runner restart.
- [ ] Qualify tunnel restart.
- [ ] Qualify Windows Runtime/service restart.
- [ ] After every episode, require identity + agent status + UI readback before PASS.
- [ ] Run the final current-main owner verification and `git diff --check` before recording closure.
