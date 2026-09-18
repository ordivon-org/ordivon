# Artifact Capability Decomposition — Wave A13 R1

## Standing

DIRECT_PYTHON_OPERATION_PROVIDER_DEFAULT_LEGACY_CLI_PROVIDER_FALLBACK

Wave A13 changes the default ArtifactOperation execution provider from legacy Delivery/OCI CLI subprocess mapping to direct Python owner composition.

## One-sentence boundary

The Direct Python provider composes Artifact Core admission/planning, capability dispatch, verification, trust, and OCI packaging owners directly behind the stable ArtifactOperation socket; the legacy CLI provider remains an explicit compatibility fallback and is no longer the default Temporal execution path.

## Default dependency direction

Before A13:

Temporal -> ArtifactOperation -> DeliveryCliOperationProvider -> artifact_delivery.py / artifact_oci_package.py CLI.

After A13:

Temporal -> ArtifactOperation -> DirectPythonOperationProvider -> Core / Capability / Verification / Trust / OCI owners.

The stable ArtifactOperation envelope and ReceiptFence introduced in A12 are unchanged.

## Direct provider

New owner:

artifact_operations/providers/direct_python.py

It directly composes:

- artifact_core.admission
- artifact_core.build_bindings
- artifact_core.build_planning
- artifact_core.contracts
- artifact_core.json_validation
- artifact_core.profile_v1
- artifact_capabilities.dispatch
- artifact_capabilities.presentation
- artifact_verification
- artifact_verifiers.document
- artifact_verifiers.openxml
- artifact_verifiers.pdf
- artifact_verifiers.presentation
- artifact_verifiers.web
- artifact_trust.vsa
- scripts.artifact_oci_package.execute_oci_package_stage

The source contains no artifact_delivery import, no delivery_cli import, and no subprocess usage.

External processes are still allowed inside their owning capability/verifier/trust/OCI modules. The Direct provider itself does not recreate those effects.

## Build path

Direct build execution now performs:

exact request commitment -> Core request admission -> build binding registry -> derived build plan -> capability dispatch -> provider-owned primary artifact.

Presentation build hooks use Presentation-owned admission, inspection, semantics, and canonicalization.

Document build uses the existing Pandoc capability and Document toolchain selector.

Build-stage result shape remains compatible with the historical artifact-delivery-build-stage contract.

## Verification path

Direct verification composes artifact_verification.execute_verify_stage with explicit hooks to the concrete verifier owners.

The provider does not implement verifier semantics.

## Trust path

Direct trust execution calls artifact_trust.vsa.aggregate_vsa_gates with the default Trust toolchain configuration and exact gate/bundle commitments.

The provider only wires inputs and persists the operation result.

## Package path

Direct package execution calls the A11-decoupled OCI package owner directly through execute_oci_package_stage.

The provider does not invoke artifact_oci_package.py as a CLI subprocess.

## Presentation canonicalization ownership

A13 also removes the remaining Presentation build-mechanics implementation from Delivery.

New owner:

artifact_capabilities/presentation/canonicalization.py

It owns:

- deterministic ZIP DOS timestamp normalization;
- deterministic PPT creation ID allocation;
- OPC core created/modified timestamp normalization;
- deterministic generated OOXML repacking;
- recursively bounded generated embedded Office canonicalization.

Delivery retains thin compatibility wrappers for:

- normalize_zip_member_timestamps — 4 lines;
- _canonicalize_ppt_creation_ids — 4 lines, retained because legacy tests/callers directly consume the historical private helper;
- canonicalize_generated_ooxml_metadata — 2 lines.

The lower-level implementation helpers no longer exist in Delivery.

## Temporal default provider

scripts/artifact_delivery_temporal_support.py now defaults to DirectPythonOperationProvider.

DeliveryCliOperationProvider is selected only when an explicit legacy artifact_cli or artifact_oci_cli override is supplied.

Existing Temporal activity names and workflow history identifiers remain unchanged.

## Legacy CLI fallback

artifact_operations/providers/delivery_cli.py remains available as a replaceable compatibility provider.

It continues to contain legacy CLI vocabulary and subprocess invocation by design, but it is not the default provider.

PreparedOperation shared provider state moved to artifact_operations/providers/common.py so the Direct provider has no dependency on the CLI provider module.

## Behavior evidence

A13 direct provider smoke exercised a real presentation build followed by direct verification with a bounded profile.

The result produced:

- build operation PASS;
- exact artifact role;
- verify operation PASS;
- profileVerificationComplete true;
- verifyReport role;
- no Delivery CLI routing.

Legacy Delivery compatibility remains covered separately.

## Regression evidence

A13 decomposition tests: 5 PASS.

Legacy Delivery: 79 tests, 0 failures, 2 conditional skips.

Temporal durability contract with DirectPython as default: 12 PASS.

A2–A13 plus OpenXML environment plus OCI targeted bundle: 81 PASS.

Full Artifact candidate: 382 tests, 0 failures, 4 conditional skips.

Candidate full-regression Runtime Job:

job-01a0b3d6-0acf-7e60-90d5-d2cce6fe435f

## Monolith reduction

Artifact Delivery line trajectory:

- decomposition start: approximately 3922
- A2: 3458
- A3: 2822
- A4: 2242
- A5: 2028
- A6: 1737
- A7: 1616
- A8: 1546
- A9: 1520
- A10: 1442
- A11: 1408
- A12: 1408
- A13: 1197

A13 removes another 211 lines from Delivery, mainly by relocating canonicalization mechanics to the Presentation capability owner.

## Architectural standing after A13

The runtime backbone no longer requires artifact_delivery.py CLI execution.

artifact_delivery.py still contains significant compatibility facade logic and some cross-format CLI wiring, but it is no longer the default operation execution authority for Temporal.

The next bounded wave should therefore focus on A14 compatibility-retirement mapping and facade reduction: identify which Delivery functions are public compatibility obligations, which can become wrappers over DirectPython owner services, and which can be removed after explicit deprecation evidence.
