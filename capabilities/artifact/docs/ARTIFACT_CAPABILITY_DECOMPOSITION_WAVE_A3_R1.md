# Artifact Capability Decomposition — Wave A3 R1

## Standing

`TRUST_GATE_OWNER_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A3 removes the production VSA/Sigstore/Cosign trust implementation from the historical `scripts/artifact_delivery.py` monolith and gives it one explicit owner: `artifact_trust.vsa`.

The wave is deliberately narrow. It does not move presentation authoring, format verification, verify-stage orchestration, Runtime/Temporal durability, or OCI mechanics.

## One-sentence boundary

Artifact Trust owns verification-summary semantics, signer/trust policy, Sigstore bundle binding, Cosign verifier provenance, cryptographic verification, and production VSA gate aggregation; Artifact Delivery may generate local gate evidence and retain compatibility wrappers but no longer owns trust implementation.

## New trust owner

New module:

`artifact_trust/vsa.py`

It owns:

- SLSA Verification Summary v1 statement construction and exact artifact/profile binding;
- RFC 6920 `ni` subject identity;
- VSA semantic verification;
- VSA trust-policy validation and exact public-key/trusted-root digest binding;
- Sigstore bundle v0.3 / DSSE statement-shape verification;
- Cosign executable selection and digest/version lock validation;
- Arch package-signature provenance for the selected Cosign bytes;
- public-key and keyless Cosign verification policy;
- production VSA gate aggregation;
- separation of VSA gates from assembly/provenance gates.

## Explicit toolchain configuration

`TrustToolchainConfig` makes mutable/external trust inputs explicit:

- toolchain lock path;
- selected Cosign binary;
- signed Arch package;
- detached Arch package signature.

The native trust API accepts an optional explicit config. Default callers use the current local toolchain authority.

This exists partly to preserve historical compatibility correctly rather than by accidental module-global coupling.

## Delivery compatibility surface

Existing callers and tests historically import trust names from `scripts/artifact_delivery.py`. Some also temporarily replace `COSIGN_ARCH_PACKAGE` and `COSIGN_ARCH_PACKAGE_SIGNATURE` to exercise fail-closed provenance behavior.

Wave A3 therefore retains a bounded compatibility surface:

- pure aliases for immutable VSA primitives such as `verification_summary_statement` and `verify_verification_summary`;
- thin wrappers for `cosign_tool_fact`, `verify_signed_verification_summary`, and `aggregate_vsa_gates`;
- `_delivery_trust_toolchain_config()` converts the legacy delivery-level path variables into explicit `TrustToolchainConfig` on every wrapped call.

The wrappers contain no trust-policy or cryptographic implementation. This preserves legacy monkeypatch semantics without making Delivery the trust authority.

`execute_verify_stage()` and `_write_raw_and_vsa()` remain in Delivery in this wave. They may create unsigned local VSA statements, but external authenticity and production aggregation are delegated to Artifact Trust.

## OCI cut

`scripts/artifact_oci_package.py` now imports these directly from `artifact_trust.vsa`:

- `LOCAL_VSA_VERIFIER_ID`;
- `SIGSTORE_BUNDLE_V03`;
- `aggregate_vsa_gates`;
- `cosign_tool_fact`.

OCI no longer obtains those trust capabilities from `artifact_delivery`.

Residual imports from `artifact_delivery` are now limited to compatibility-era build/verification orchestration:

- `build_presentation_source`;
- `execute_verify_stage`;
- `validate_delivery_request`;
- `write_json`.

Those are separate future decomposition seams, not trust dependencies.

## Monolith reduction

Measured after the A3 cut:

```text
artifact_delivery.py at decomposition start: ~3922 lines
artifact_delivery.py after A2:               3458 lines
artifact_delivery.py after A3:               ~2823 lines
artifact_trust/vsa.py:                        ~808 lines
```

Line count is only a secondary witness. The relevant authority change is that trust policy and cryptographic verification are no longer implemented inside Delivery.

## TDD / compatibility evidence

A3 ownership tests were written first and observed RED before `artifact_trust.vsa` existed / while trust implementation remained in Delivery.

Targeted post-cut compatibility run:

- `test_artifact_decomposition_a3`: 5 PASS;
- legacy Artifact Delivery + OCI + A2 + A3 bundle: 100 tests, 0 failures, 2 conditional skips.

A final mechanical gate initially caught one migration-boundary defect: the trust-constant replacement range had accidentally removed the adjacent `DEFAULT_WINDOWS_FONTS` CLI default. Temporal's real CLI-driven build tests failed with `NameError`, proving that the full compatibility gate was useful. The constant was restored and Temporal then returned 12/12 PASS.

The final commit gate must use fresh post-fix full Artifact regression, Temporal regression, compileall, and `git diff --check`; earlier passing runs are not treated as final evidence after the fix.

## Current dependency direction

```text
Artifact Delivery / verify-stage
          |
          | local VSA construction aliases / compatibility wrappers
          v
    artifact_trust.vsa
          |
          +--> artifact_core.contracts
          +--> artifact_core.profile_v1
          +--> artifact_trust.provenance
          +--> Sigstore/Cosign + pinned package provenance

OCI package adapter
          |
          +-------> artifact_trust.vsa   (direct trust dependency)
          |
          +-------> artifact_delivery    (residual build/verify compatibility only)
```

## Non-claims / remaining decomposition

Wave A3 does **not** claim Artifact decomposition complete.

The largest remaining knots are:

1. **Presentation capability package** — concrete python-pptx and PPT Master implementation/provider-specific material handling still live mainly in `artifact_delivery.py`.
2. **Verify-stage orchestration** — format-specific routing and local VSA emission remain co-located in Delivery.
3. **Document semantic/dependency verification** — still coupled to Delivery orchestration.
4. **OCI residual Delivery imports** — build/verify/request compatibility remains.
5. **Temporal adapter** — still knows Delivery CLI verbs and stage/output layout rather than a fully stable generic operation contract.
6. **CLI facade** — `artifact_delivery.py` is smaller but is not yet a true thin facade.

The next wave should target Presentation as an independent capability package, while keeping authoring separate from OpenXML/PowerPoint acceptance evidence.
