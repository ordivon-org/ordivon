# Artifact Capability Decomposition — Wave A1 R1

## Standing

`COMPATIBILITY_SEAM_IMPLEMENTED_REGRESSION_GREEN`

This wave reduces Artifact runtime coupling without replacing the accepted Artifact v2 source authority, production Office/Web delivery path, Temporal workflow, OCI packaging, or family-specific verifiers.

The architectural objective is to make Artifact a thin semantic/acceptance kernel whose family mechanics remain replaceable capabilities.

## One-sentence kernel

Artifact resolves one exact profile, selects an admitted capability, binds exact inputs/evidence, and decides profile-scoped standing without owning the underlying authoring, validation, target, workflow, package, or distribution engines.

## Implemented seams

### A1 — Core commitments

New package: `artifact_core/`.

`contracts.py` owns only cross-family exact-file identity primitives:

- SHA-256 file identity;
- path/name/size commitment;
- fail-closed drift verification.

It does not execute providers or judge family semantics.

### A2 — Profile Registry

`artifact_core.profiles.ProfileRegistry` supplies one canonical v2-shaped semantic view across current Artifact profiles.

Important boundary:

- existing production profile-v1 bytes remain source authority for the existing Office/Web paths;
- current profile-v2 files supply the common semantic projection;
- standards-first families use their v2 profile bytes directly;
- runtime resolution no longer depends on `shadow-v2/profile-v2-mapping-manifest-r1.json`.

The generated mapping manifest remains migration/equivalence evidence, not runtime registry truth.

### A3 — Capability Binding Registry

New authority: `artifact-delivery/capability-bindings-v1.json`.

It maps:

`profile + operation -> capability id + provider entrypoint + object-contract requirement + standing reference`.

The verification service no longer owns a Python `ROUTES` table. The current 19 verification routes are represented as data and their existing `LOCAL_LIVE_PROVEN` standing records remain independently checked.

### A4 — Operation planning seam

`artifact_core.operations.OperationPlanner` introduces the first family-neutral operation contract for verification planning:

- operation identity;
- resolved profile;
- resolved capability binding;
- exact subject commitment;
- optional/required object-contract commitment.

This is intentionally a semantic planning seam, not a workflow engine and not a Runtime replacement.

## Runtime cutovers completed in this wave

### `scripts/artifact_verify.py`

Before:

- owned `ROUTES` in Python source;
- scanned `shadow-bindings/` itself;
- combined service routing with capability discovery.

After:

- reads `ProfileRegistry` and `CapabilityBindingRegistry`;
- retains the existing request envelope and family-verifier delegation;
- retains exact profile/subject/object-contract digest fencing;
- keeps family verifier output untouched;
- adds capability identity to verifier evidence.

### `scripts/artifact_agent_surface.py`

Before:

- parsed `artifact_verify.py` with Python AST to recover `ROUTES`;
- read the generated profile-v2 mapping manifest at runtime;
- read the donor manifest at runtime to infer capability standing.

After:

- verification route discovery reads `CapabilityBindingRegistry`;
- profile coverage reads current taxonomy + `ProfileRegistry` + `CapabilityBindingRegistry`;
- no verifier-source AST parsing;
- no runtime dependency on profile-v2 mapping or donor migration manifests.

## Deliberately not moved yet

The following remain compatibility-era composite nodes and are the next decomposition targets:

1. `scripts/artifact_delivery.py` — request admission, presentation/document build, format verification, target/visual/read-back evidence, VSA/Sigstore/SLSA and CLI remain co-located.
2. `scripts/artifact_oci_package.py` — still imports Artifact delivery semantics directly.
3. `scripts/artifact_delivery_temporal_support.py` — still knows Artifact CLI verbs and output-directory layout.
4. target providers — PowerPoint/browser/native-consumer paths are not yet behind one target-capability contract.
5. package/trust — OCI/ORAS, OPA and Sigstore are not yet fully isolated behind capability interfaces.
6. `OperationPlanner` — introduced and tested, but not yet the sole operation contract used by every legacy build/package/Temporal consumer.

No claim is made that Artifact decomposition is complete.

## Evidence

TDD seam tests were introduced before implementation and observed failing because the new kernel/registry did not exist or the old source-owned routing remained.

Post-change verification:

- `test_artifact_core_registry.py`: 6 PASS;
- `test_artifact_verify.py`: 14 PASS;
- `test_artifact_agent_surface.py`: 9 PASS;
- full `test_artifact*.py` regression: 312 tests, 4 conditional skips, 0 failures;
- `test_temporal_artifact_delivery_contract.py`: 12 PASS;
- `compileall` for `artifact_core`, `artifact_verify.py`, and `artifact_agent_surface.py`: PASS.

Full Artifact regression Runtime job:

`job-01a0b01d-e837-7fe3-ad60-b5a46303ce9a`

Temporal contract Runtime job:

`job-01a0b01f-8480-7800-9027-d895020a1409`

## Resulting dependency direction

```text
artifact-work / Agent
        |
        v
Artifact semantic surface
        |
        +--> ProfileRegistry
        +--> CapabilityBindingRegistry
        +--> OperationPlanner
        +--> exact commitments
                  |
                  v
        family/provider capability
                  |
                  v
               Runtime
                  |
                  v
               evidence
```

Migration/export manifests are now off the live Agent-surface query path.

## Next wave

Wave A2 should split the first high-value provider seams out of `artifact_delivery.py` while retaining its CLI as a compatibility facade:

1. `artifact_core/request_admission`;
2. `artifact_capabilities/presentation` author/build adapter;
3. `artifact_capabilities/document` author/build adapter;
4. `artifact_evidence/` target/visual/read-back contracts;
5. replace direct imports from `artifact_oci_package.py` with stable core/evidence contracts;
6. only after those seams are green, reduce `artifact_delivery.py` to dispatch/facade responsibilities.

The first cross-family acceptance slice for Wave A2 should remain PNG verification + PPTX build/PowerPoint acceptance so the common kernel is pressured by both a simple static format and the most mature native-target workflow.
