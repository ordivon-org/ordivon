# Security v2 deletion / non-migration map R1

Date: 2026-09-12

This map records what the first three old->v2 differentials have actually shown. It is not permission to delete the old repository wholesale.

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

## Still unresolved / not deletion-authorized

The following old capabilities have not yet been replaced by a v2 differential and must not be deleted solely on the basis of R1-R3:

- how physical execution providers expose exact immutable receipts and independent readback evidence in production;
- world-truth versus sensor/claim epistemic separation for consumers more complex than the closed AF3 consequence path;
- physical/recovery semantics that remain after mature VM/tool delegation;
- specialized malware/memory-forensics experiments if retained as research artifacts;
- any old consumer whose exact contract has not yet been replayed against v2.

## Next deletion gate

The next high-value gate is provider displacement: determine whether mature VM/image owners such as libvirt, QEMU tooling, Packer, and related native provider mechanisms can own physical lifecycle while Security v2 retains only authority and evidence bindings. No old QEMU/KVM scaffold should migrate until this gate proves a residual requirement.
