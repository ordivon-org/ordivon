# Artifact Capability Decomposition — Wave A11 R1

## Standing

OCI_DECOUPLED_FROM_DELIVERY_FACADE_CORE_JSON_VALIDATION_OWNED

Wave A11 removes the remaining direct dependency from scripts/artifact_oci_package.py to the historical artifact_delivery.py compatibility facade.

OCI now consumes Core admission/identity, Evidence, and Trust owners directly.

## One-sentence boundary

OCI Packaging owns standards-based OCI 1.1 packaging/referrer assembly and release-policy evaluation; it consumes exact Artifact admission/evidence/trust facts but does not own Artifact build, verification orchestration, generic facade behavior, or a second package registry/model.

## Pre-A11 coupling

Before A11, OCI imported four symbols from Delivery: build_presentation_source, execute_verify_stage, validate_delivery_request, and write_json.

Three existed only to populate an internal compatibility SimpleNamespace artifact used by tests/historical callers. validate_delivery_request was the only production-path dependency.

## A11 result

OCI now consumes:

- artifact_core.admission
- artifact_core.contracts
- artifact_core.json_validation
- artifact_core.profile_v1
- artifact_capabilities.presentation admission
- artifact_evidence.delivery
- artifact_trust

There is no import of artifact_delivery in artifact_oci_package.py. There is no OCI-owned SimpleNamespace artifact facade.

## Core JSON validation owner

A11 adds artifact_core/json_validation.py. It owns the generic JSON Schema Draft 2020-12 document validator used for request/source admission.

The API preserves the historical behavior: JSON object requirement, optional exact kind binding, Draft 2020-12 schema validation, FormatChecker, explicit jsonschema-unavailable standing, bounded failure reporting, and schema-path evidence.

Delivery retains only a four-line validate_json_document compatibility wrapper.

## OCI request admission

OCI composes Core admission directly through AdmissionHooks using Core JSON validation, profile_v1 validation, Presentation source admission, exact file facts, and SHA-256 binding. The local OCI validate_delivery_request function is wiring only; it does not duplicate the request-admission algorithm.

## Fake Artifact facade retirement

The former OCI SimpleNamespace artifact projection has been removed. OCI is not an Artifact SDK/facade and should not pretend to be one.

OCI tests now explicitly use Delivery only as fixture preparation for build/verify outputs, while testing OCI production behavior through the OCI module itself. Trust constants/functions are consumed from their actual owner.

## Historical decomposition-test correction

Two older tests encoded pre-A11 assumptions. A2 expected a Delivery request-admission import to remain. A3 parsed a Delivery import block to prove Trust symbols were absent. A11 updates those tests to assert the stronger property: OCI imports Core/Trust directly and has zero artifact_delivery imports.

## Behavior retained

Covered unchanged paths include local unsigned OCI layout, signed VSA release-ready packaging, OPA fail-closed policy, evidence drift failure before layout creation, exact subject/layer digest binding, OCI 1.1 referrers, release provenance generation from a validated request, assembly-gate accounting, and output-directory fail-closed behavior.

## Coupling census

On the A11 candidate, searches for Delivery imports, SimpleNamespace, and a top-level artifact facade return no matches in scripts/artifact_oci_package.py.

## Monolith reduction

Artifact Delivery line trajectory: start about 3922; A2 3458; A3 2822; A4 2242; A5 2028; A6 1737; A7 1616; A8 1546; A9 1520; A10 1442; A11 1408.

A11 removes another approximately 34 lines from Delivery by transferring generic JSON validation ownership to Core.

## TDD / verification evidence

A11 tests were written before implementation and observed RED because Core did not own generic JSON validation, Delivery still implemented the validator, OCI still imported Delivery, OCI still exposed a fake artifact facade, and OCI tests depended on that facade.

Implementation then exposed two stale architecture-test assumptions: the first A11 string test incorrectly matched the local report_artifact variable, and A3 assumed a Delivery import block must exist. Both tests were corrected to assert semantic/AST ownership rather than obsolete textual structure.

Current candidate evidence: A11 decomposition 5 PASS; OCI behavior 4 PASS; A2–A11 plus OpenXML environment plus OCI targeted bundle 70 PASS; Temporal contract 12 PASS; full Artifact regression 371 tests with 0 failures and 4 conditional skips; compileall PASS; git diff --check PASS before the final commit gate.

Candidate full-regression Runtime Job: job-01a0b3a5-5b89-7d03-b39f-29c39c29f9e7.

## Architectural standing after A11

The major residual dependency direction is no longer OCI -> Delivery. The next significant coupling is Temporal/runtime orchestration speaking Delivery CLI/stage vocabulary.

The next bounded wave should therefore be A12 = Generic ArtifactOperation / Temporal Adapter. A12 should create a stable operation-facing contract that composes existing owners without turning Runtime/Temporal into Artifact semantic authority.
