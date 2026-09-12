# Security v2 deletion / non-migration map R1

Date: 2026-09-12

This map records what the first three old->v2 semantic differentials and the first VM-provider displacement proof have actually shown. It is not permission to delete the old repository wholesale.

## Proven non-migration decisions

### Product scanning and evidence normalization

Do not migrate old generic scanner orchestration or invent a unified Ordivon finding format for the v2 product path.

External owners now cover the product verification substrate:

- Gitleaks: secret detection;
- Semgrep: SAST;
- Trivy: vulnerability/secret scanning;
- Syft: SBOM;
- OSV-Scanner: dependency vulnerability evidence;
- OPA/Rego: admission policy;
- SARIF, CycloneDX, in-toto Statement, SLSA VSA, Sigstore DSSE: evidence interchange and authenticated envelope.

Old research/evidence/docs/fixture material remains research/reproduction material, not v2 product code.

### `RangeSession.admit_effect()` mechanics

Do not migrate the old session/runtime implementation merely to preserve effect admission.

The proven residual semantics are now represented by:

- `policies/effect_admission.rego`: exact actor/authority/zone/capability admission;
- `ReplayBinding`: exact request replay and same-ID changed-content rejection.

The differential proved complete admission-record equivalence for six cases and replay equivalence against old revision `5e3142b92fc5aed3259295b63c0300f01b45e04a`.

Therefore Range backend creation/destruction, checkpoint lifecycle, Range event mechanics, VM lifecycle, Windows fabric mechanics, and effect execution implementation are not prerequisites for preserving admission semantics in v2.

### Execution -> observation -> verified consequence

Do not migrate the old Range event system or AF3 backend merely to preserve the distinction between admission, execution, observation, and verified consequence.

The proven residual semantics are now represented by `policies/consequence_verification.rego`, derived from currently supplied evidence rather than a new persistent Ordivon workflow engine.

The differential proved:

- admission alone is `ADMITTED_NOT_EXECUTED`;
- a valid execution receipt alone is `EXECUTED_UNVERIFIED`;
- the executor cannot self-promote its receipt to world truth;
- a non-authoritative sensor observation does not verify consequence;
- request-binding or state-digest mismatch fails closed;
- only a later `world-truth` observation with the same post-write state digest produces `VERIFIED_CONSEQUENCE`;
- rejected admission cannot advance to consequence.

The final verified-consequence payload exactly matched the old AF3 world-truth observation payload.

Therefore AF3, `RangeSession.poll_backend()`, and the old Range event log are not prerequisites for preserving this consequence-verification semantic in v2.

### Direct QEMU / swtpm lifecycle ownership

A real provider-displacement proof now exists for the basic VM lifecycle.

Current external owners:

- libvirt `12.7.0` / virtqemud;
- QEMU `11.0.3` with KVM;
- swtpm `0.10.1` managed by libvirt;
- virt-install `5.1.0` available;
- Packer `1.16.0` with HashiCorp QEMU plugin `1.1.6`.

A transient, no-network KVM domain was created through libvirt, observed as running, inspected through libvirt-mediated QMP (`query-status` and `query-pci`), destroyed through libvirt, and proven absent afterward. A second transient domain delegated TPM 2.0 to libvirt; QMP observed the emulator-backed `tpm-tis` device, the live swtpm process was libvirt-owned, and bounded post-destroy observation proved both domain and swtpm process absent.

Therefore the following old mechanical responsibilities are no longer justified as Security-owned lifecycle primitives:

- direct QEMU `Popen` ownership;
- QEMU PID lifecycle bookkeeping as the primary authority;
- hand-owned QMP socket lifecycle;
- direct QEMU quit/process terminate as the normal lifecycle API;
- direct swtpm PID/socket/process lifecycle;
- basic VM create/start/inspect/destroy mechanics.

Packer's QEMU plugin is initialized and the v2 template validates only with a caller-supplied exact SHA-256 installation-image digest; `iso_checksum=none` fails closed. This proves provider/toolchain availability, not a real Windows image build.

## Still unresolved / not deletion-authorized

The following old capabilities have not yet been replaced by a complete provider/differential proof:

- real Windows image construction from a frozen authoritative installation source;
- qemu-nbd/partx/mtools/NTFS image manipulation and independent offline readback;
- network namespace/traffic-capture scenarios;
- physical execution provider receipt + independent readback for the actual Windows consumer;
- recovery/compensation semantics under host, daemon, or provider failure;
- world-truth versus sensor/claim epistemic separation for consumers more complex than the closed AF3 consequence path;
- specialized malware/memory-forensics experiments if retained as research artifacts;
- any old consumer whose exact contract has not yet been replayed against v2.

`libguestfs` remains unavailable because the current Arch package database/mirror set attempted to resolve QEMU `11.1.1-1` packages no longer served by the configured mirrors; the failed transaction committed no upgrade and installed QEMU remained `11.0.3-1`. This package/mirror skew must be repaired safely before retrying offline-image displacement.

## Next deletion gate

Select or produce an authoritative, digest-frozen image fixture and prove image construction/offline readback through mature owners. Until then, direct QEMU/swtpm lifecycle code is a proven non-migration candidate, while old image-manipulation and recovery code remains evidence-bearing legacy rather than deletion-authorized code.
