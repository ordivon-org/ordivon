# Security v2 deletion / non-migration map R1

Date: 2026-09-12

This map records what the first two old->v2 differentials have actually shown. It is not permission to delete the old repository wholesale.

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

Therefore the following are **not prerequisites** for preserving admission semantics in v2:

- Range backend creation/destruction;
- checkpoint lifecycle;
- Range event log mechanics;
- QEMU/KVM lifecycle;
- Windows fabric mechanics;
- effect execution implementation.

## Still unresolved / not deletion-authorized

The following old capabilities have not yet been replaced by a v2 differential and must not be deleted solely on the basis of R1/R2:

- execution-to-observation-to-verified-consequence binding;
- world-truth versus sensor/claim epistemic separation where a real consumer still requires it;
- physical/recovery semantics that remain after mature VM/tool delegation;
- specialized malware/memory-forensics experiments if retained as research artifacts;
- any old consumer whose exact contract has not yet been replayed against v2.

## Next deletion gate

The next high-value differential should target `admitted != executed != observed != verified consequence`. If that residual can be represented as standard execution/evidence receipts plus a thin Ordivon binding, the large Range execution/event apparatus can be split further into external mechanics versus small semantic state transitions.
