# Artifact Capability Decomposition — Wave A14 R1

## Standing

COMPATIBILITY_RETIREMENT_MAP_FROZEN_PRODUCTION_PYTHON_FACADE_IMPORTS_ZERO

Wave A14 stops opportunistic function moving and freezes an explicit retirement contract for every remaining top-level callable in scripts/artifact_delivery.py.

## One-sentence boundary

A14 distinguishes supported CLI compatibility, legacy Python wrappers, implementations that still need a canonical owner, deprecated compatibility wiring, and proven dead code so future facade reduction is gated by evidence rather than line-count pressure.

## Machine-readable authority

The retirement authority is:

artifact-delivery/compatibility-retirement-manifest-v1.json

The manifest is executable policy, not prose-only guidance.

It contains:

- exact source authority and baseline commit;
- every live top-level Delivery callable exactly once;
- target disposition;
- current owner;
- target owner;
- consumer class;
- explicit retirement gate;
- all current CLI verbs;
- A14-retired symbols with evidence;
- current production consumer classes.

Tests fail if a Delivery callable is added or removed without updating this manifest.

## Disposition census

After the A14 safe cleanup, Delivery contains 51 live top-level callables.

Their target dispositions are:

- KEEP_COMPAT_WRAPPER: 27
- KEEP_CLI: 4
- MOVE_TO_OWNER: 9
- DEPRECATE: 1
- DROP: 10

These are target dispositions, not permission to delete immediately.

A symbol marked DROP may still have standing ACTIVE_BLOCKED until its retirementGate is satisfied.

## KEEP_CLI

The CLI-infrastructure functions remain intentionally owned by scripts/artifact_delivery.py:

- main
- emit
- write_json
- _parse_named_values

The CLI facade remains supported because production tooling still invokes it explicitly.

There are currently 20 parser verbs and the manifest must cover all 20 exactly.

Important current production CLI consumers are:

- scripts/artifact_agent_surface.py
- scripts/artifact_delivery_toolchain_doctor.py
- artifact_operations/providers/delivery_cli.py as an explicit fallback provider

The default Runtime/Temporal operation path does not use the CLI provider.

## KEEP_COMPAT_WRAPPER

Twenty-seven callables remain compatibility wrappers.

Their implementation authorities already live elsewhere, including:

- artifact_core.json_validation
- artifact_capabilities.presentation
- artifact_verifiers.document
- artifact_verifiers.presentation
- artifact_verifiers.pdf
- artifact_verifiers.openxml
- artifact_verifiers.web
- artifact_verification.stage
- artifact_trust.vsa
- artifact_operations.providers.direct_python

Examples include validate_delivery_request, compile_delivery_plan, execute_build_stage, execute_verify_stage, aggregate_vsa_gates, build_presentation_source, inspect_pptx, verify_pdf, verify_openxml_artifact, and verify_html_conformance.

A14 does not claim that legacy tests alone make these permanent APIs.

The governing rule is:

tests alone do not create a production API obligation; production consumers, documented compatibility promises, and explicit migration evidence do.

## MOVE_TO_OWNER

Nine callables still contain implementation that should not remain in the facade.

### Presentation reference / OPC projection

Planned target owner:

artifact_capabilities.presentation.reference_projection

Symbols:

- _normalized_posix_relative
- _normalized_sha256
- project_opc_members
- compose_reference_hybrid_source
- _safe_zip_names
- _relationship_base
- _resolve_relationship_target

The public CLI verbs project-opc-members and compose-reference-hybrid-source should remain compatible while their implementations move.

### Material snapshot

Planned target owner:

artifact_evidence.snapshot

Symbols:

- utc_now
- snapshot_materials

The snapshot CLI verb may remain; the evidence-capture implementation should not be facade-owned.

## DEPRECATE

One private compatibility seam remains explicitly deprecated:

_delivery_trust_toolchain_config

Its purpose is to preserve historical Delivery-local mutable Cosign toolchain constants for legacy compatibility tests/callers.

The target authority is artifact_trust.vsa.default_trust_toolchain_config.

It can retire only after Delivery-local Trust constant mutation compatibility is no longer required.

## DROP after bounded gates

Ten private facade-wiring functions are target-DROP but still ACTIVE_BLOCKED:

- _selected_external_file
- _presentation_build_hooks
- _resolve_request_path
- _admit_presentation_source
- _admit_semantic_svg_source
- _primary_suffix
- _request_output_name
- _document_dependency_hooks
- _document_dependency_stage_verifier
- _verification_stage_hooks

Most become unnecessary once A15 turns build/request/verify public functions into thin DirectPython-provider compatibility wrappers.

## Proven dead symbols removed in A14

A14 removes four functions only after a zero-live-caller proof:

- load_json
- _require_uri
- _cosign_executable
- _cosign_selection_provenance

They remain recorded in retiredSymbols with reason zero-live-callers.

No compatibility shim was retained because no live caller was found.

## Toolchain Doctor authority correction

Before A14, scripts/artifact_delivery_toolchain_doctor.py still imported artifact_delivery as a Python module only to call cosign_tool_fact.

It also read scripts/artifact_delivery.py source text to assert Cosign/Sigstore policy details even though Trust implementation ownership moved to artifact_trust.vsa in A3.

A14 corrects both category errors:

- the Doctor calls artifact_trust.vsa.cosign_tool_fact directly;
- Trust policy source assertions read artifact_trust/vsa.py directly.

The production Python import census now shows zero imports of artifact_delivery outside artifact_delivery.py itself.

## Current dependency boundary

Production Python dependencies:

canonical modules -> canonical owners

Production Delivery dependencies:

Agent Surface -> Delivery CLI path
Toolchain Doctor -> Delivery CLI path
legacy DeliveryCliOperationProvider -> Delivery CLI path

Default Runtime/Temporal:

Temporal -> ArtifactOperation -> DirectPythonOperationProvider -> canonical owners

Therefore Delivery is now an explicit compatibility/CLI edge, not a hidden Python SDK dependency.

## Line-count standing

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
- A14: 1180

The A14 reduction is intentionally small. The primary output is the retirement authority, not aggressive deletion.

## Verification evidence before final gate

A14 decomposition tests: 8 PASS.

Legacy Delivery: 79 tests, 0 failures, 2 conditional skips.

A2–A14 plus OpenXML environment plus OCI targeted bundle: 89 PASS.

Temporal durability contract: 12 PASS.

compileall: PASS.

git diff --check: PASS.

Production Python Delivery-facade imports: zero.

## Next wave

A15 should execute the manifest rather than rediscover the architecture.

The highest-value bounded cuts are:

1. move Presentation OPC/reference projection to its canonical capability owner while preserving both CLI verbs;
2. move snapshot_materials to Artifact Evidence;
3. make validate_delivery_request, compile_delivery_plan, execute_build_stage, and execute_verify_stage thin wrappers over DirectPython owner services;
4. delete the private DROP set only after those wrappers are green;
5. preserve all KEEP_CLI verbs and KEEP_COMPAT_WRAPPER behavior until their explicit retirement gates close.

A15 should not remove a symbol merely because it is old or because tests are inconvenient. It should follow the frozen manifest.
