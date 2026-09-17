# Artifact Capability Decomposition — Wave A2 R1

## Standing

`BUILD_ADMISSION_EVIDENCE_TRUST_SEAMS_IMPLEMENTED_REGRESSION_GREEN`

Wave A2 continues the A1 registry split by moving build admission, build selection/dispatch, bounded providers, delivery evidence, legacy profile validation, and release provenance out of the historical `artifact_delivery.py` monolith while preserving its CLI/function surface as a compatibility facade.

## Kernel direction

```text
request bytes
   |
   v
Request Admission (artifact_core)
   |
   v
Build Binding Registry (data)
   |
   v
Build Planning (artifact_core)
   |
   v
Capability Dispatch
   +--> presentation providers (legacy implementation adapters for now)
   +--> Pandoc document provider
   +--> exact native pass-through
   |
   v
artifact bytes
   |
   +--> independent evidence package
   +--> trust/provenance package
```

The monolith remains a compatibility facade and still owns several mature format-specific implementations; Wave A2 does not claim full Artifact decomposition.

## Implemented seams

### A2.1 — Request Admission

New: `artifact_core/admission.py`.

It owns generic exact request/profile/source/material admission:

- request envelope validation orchestration;
- exact SHA-256 binding of referenced inputs;
- exact material de-duplication;
- fail-closed reference errors;
- no provider execution;
- no artifact acceptance claim.

Family-specific presentation-source validation remains supplied through explicit `AdmissionHooks`. `artifact_delivery.validate_delivery_request()` is retained as a compatibility composition function over this core seam.

### A2.2 — Build Capability Binding Registry

New authority: `artifact-delivery/build-capability-bindings-v1.json`.

It owns:

`artifactClass + sourceKind -> adapterId + capabilityId + builderId + buildType`

The inline `adapter_map` was removed from `artifact_delivery.py`.

Current bounded bindings include:

- native presentation source -> python-pptx;
- semantic SVG presentation source -> PPT Master;
- Markdown document -> Pandoc DOCX;
- HTML source -> exact source-copy capability;
- native-file pass-through for existing production classes.

### A2.3 — Build Planning

New: `artifact_core/build_planning.py`.

It consumes admitted request/profile facts plus the build binding registry and emits the legacy-compatible derived plan, now including explicit `buildCapabilityId`.

Planning does not execute providers and does not own Runtime/Temporal durability.

### A2.4 — Capability Dispatch

New: `artifact_capabilities/dispatch.py`.

It owns execution dispatch after a build capability has already been selected. `artifact_delivery.execute_build_stage()` no longer contains the presentation/document/pass-through `if adapter == ...` decision tree.

Concrete presentation builder implementations are still injected from the compatibility module and are a deliberate residual seam for the next wave.

### A2.5 — Document Provider

New: `artifact_capabilities/document.py`.

`build_pandoc_docx()` now owns:

- Pandoc invocation;
- `SOURCE_DATE_EPOCH` observation and propagation;
- invalid epoch fail-before-provider behavior;
- provider execution receipt.

The historical build-stage return shape remains compatible.

### A2.6 — Native Pass-through Provider

New: `artifact_capabilities/passthrough.py`.

It copies already-native bytes and proves exact SHA-256 equality. It does not promote pass-through to semantic acceptance.

### A2.7 — Delivery / Target Evidence

New: `artifact_evidence/delivery.py`.

Moved from the monolith:

- `verify_file_fact`;
- render evidence verification;
- PowerPoint target evidence verification;
- visual-review binding;
- delivery read-back verification;
- multi-destination delivery evidence aggregation.

This separates evidence judgment from authoring/build execution.

### A2.8 — Legacy Profile-v1 Contract

New: `artifact_core/profile_v1.py`.

The old production profile-v1 validator and minimal cross-format checks now have one explicit owner. Its default schema path preserves the historical `validate_profile(profile_path)` call contract.

### A2.9 — Release Provenance

New: `artifact_trust/provenance.py`.

It owns:

- SLSA Provenance v1 statement construction;
- in-toto Statement v1 release subject verification;
- exact subject/material/profile digest binding;
- builder/build-type URI validation.

Sigstore/VSA aggregation remains a separate residual trust seam and is not falsely claimed as migrated.

## OCI dependency reduction

`scripts/artifact_oci_package.py` no longer routes these responsibilities through `artifact_delivery`:

- SHA-256 identity;
- file facts;
- file-fact verification;
- profile-v1 validation;
- SLSA statement generation;
- release provenance verification.

The broad `import artifact_delivery as artifact` production dependency was removed.

Two actual runtime compatibility dependencies remain explicit:

- `aggregate_vsa_gates`;
- `validate_delivery_request`.

A `SimpleNamespace` named `artifact` is retained only as a compatibility projection for historical callers/tests that consumed selected helpers/constants from the OCI module. OCI production logic does not use that object for identity/profile/provenance/evidence decisions.

## Monolith reduction

At A2 measurement:

```text
artifact_delivery.py: 3922 lines at decomposition start
artifact_delivery.py: 3458 lines after A2
```

Line count is not the acceptance criterion; the relevant change is authority movement. The remaining large clusters are now easier to identify:

- concrete presentation authoring/provider mechanics;
- document semantic/dependency verification;
- OOXML/PDF/Web verification;
- VSA/Sigstore/trust aggregation;
- verify-stage orchestration;
- presentation final gate;
- CLI compatibility surface.

## TDD evidence collected during the wave

Tests were written/extended before each production seam and observed failing for the intended missing responsibility:

- missing build binding/capability/evidence packages;
- old inline adapter map;
- old build-stage dispatch tree;
- missing profile-v1/trust modules;
- OCI broad monolith dependency;
- one compatibility defect where extracted profile validation lost the old default-schema call shape.

The compatibility defect was reproduced by the pre-existing OCI regression before the profile-v1 API was corrected.

Targeted green evidence before the final full regression:

- A2 decomposition tests: 12 PASS;
- legacy `test_artifact_delivery.py`: 79 tests, 0 failures, 2 conditional skips;
- `test_artifact_oci_package.py`: 4 PASS;
- Temporal delivery contract: 12 PASS.
- full `test_artifact*.py` regression: 324 tests, 0 failures, 4 conditional skips; Runtime job `job-01a0b038-24ee-7632-9cd4-62f7bf4e5b5c`.
- `compileall` across new packages plus delivery/OCI compatibility modules: PASS.
- `git diff --check`: PASS before final evidence-document update.

## Residual coupling / next wave

Wave A3 should target the two largest remaining architectural knots rather than continue arbitrary file splitting:

1. **Presentation Capability Package**
   - move python-pptx and PPT Master concrete builder implementations plus provider-specific source/material handling behind presentation capability contracts;
   - keep OOXML/PowerPoint acceptance independent from authoring.

2. **Trust Gate Package**
   - move VSA/Sigstore verification and `aggregate_vsa_gates` out of `artifact_delivery.py`;
   - let OCI depend on trust contracts instead of the delivery compatibility module.

After those cuts, `artifact_delivery.py` can begin shrinking toward a true CLI/compatibility facade and Temporal can consume stable operation contracts instead of Artifact-internal stage/file-layout knowledge.
