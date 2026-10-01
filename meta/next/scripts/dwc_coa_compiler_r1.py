#!/usr/bin/env python3
"""DWC R2.1 DW06 lowering into existing public Composition contracts.

This is a DWC-specific consumer adapter. It does not modify Composition, schedule work,
authorize effects, execute verifiers, or establish domain/security completion.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSITION_SRC = REPO_ROOT / "packages" / "composition" / "src"
if str(COMPOSITION_SRC) not in sys.path:
    sys.path.insert(0, str(COMPOSITION_SRC))

from ordivon_composition import (  # noqa: E402
    canonical_digest,
    compile_authority_obligations,
    compile_manifest,
    compile_verification_obligations,
    evaluate_gate_results,
    resolve_verifier_bindings,
)

SOURCE_KIND = "ordivon.security.dwc-coa-source-bundle-r1"
LOWERING_KIND = "ordivon.security.dwc-coa-lowering-r1"


class DwcCoaLoweringError(ValueError):
    pass


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DwcCoaLoweringError(f"{label} is required")
    return value


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DwcCoaLoweringError(f"{label} must be an object")
    return value


def _sha(value: object, label: str) -> str:
    text = _text(value, label)
    if not text.startswith("sha256:") or len(text) != 71:
        raise DwcCoaLoweringError(f"{label} must be sha256:<64 hex>")
    return text


def _bound_ref(value: object, label: str) -> dict[str, str]:
    row = _mapping(value, label)
    return {
        "id": _text(row.get("id"), f"{label}.id"),
        "digest": _sha(row.get("digest"), f"{label}.digest"),
    }


def _case_binding(value: object, label: str) -> dict[str, str]:
    row = _mapping(value, label)
    return {
        "caseRef": _text(row.get("caseRef"), f"{label}.caseRef"),
        "epochRef": _text(row.get("epochRef"), f"{label}.epochRef"),
        "subjectRef": _text(row.get("subjectRef"), f"{label}.subjectRef"),
        "subjectSnapshotDigest": _sha(
            row.get("subjectSnapshotDigest"), f"{label}.subjectSnapshotDigest"
        ),
    }


def _validate_source_bundle(bundle: Mapping[str, Any]) -> tuple[dict[str, str], list[str]]:
    if bundle.get("schemaVersion") != 1 or bundle.get("kind") != SOURCE_KIND:
        raise DwcCoaLoweringError("unsupported DWC CoA source bundle")
    case = _case_binding(bundle.get("caseBinding"), "caseBinding")

    response = _mapping(bundle.get("responseDecision"), "responseDecision")
    if response.get("kind") != "ordivon.security.response-policy-decision":
        raise DwcCoaLoweringError("responseDecision kind mismatch")
    if _text(response.get("caseRef"), "responseDecision.caseRef") != case["caseRef"]:
        raise DwcCoaLoweringError("responseDecision case binding mismatch")
    response_subject = _mapping(response.get("subject"), "responseDecision.subject")
    if (
        _text(response_subject.get("subjectRef"), "responseDecision.subject.subjectRef")
        != case["subjectRef"]
        or _sha(
            response_subject.get("snapshotDigest"),
            "responseDecision.subject.snapshotDigest",
        )
        != case["subjectSnapshotDigest"]
    ):
        raise DwcCoaLoweringError("responseDecision subject binding mismatch")
    if response.get("standing") not in {"ACTION_ONLY", "DECIDED"}:
        raise DwcCoaLoweringError("DW06 requires an actionable DW03 response decision")
    _text(response.get("actionClass"), "responseDecision.actionClass")
    if response.get("authorityGranted") is not False:
        raise DwcCoaLoweringError("DW03 responseDecision must not grant effect authority")

    coverage = _mapping(bundle.get("coverageProjection"), "coverageProjection")
    if coverage.get("kind") != "ordivon.security.dwc-attack-coverage-projection":
        raise DwcCoaLoweringError("coverageProjection kind mismatch")
    if _text(coverage.get("caseRef"), "coverageProjection.caseRef") != case["caseRef"]:
        raise DwcCoaLoweringError("coverageProjection case binding mismatch")
    coverage_subject = _mapping(coverage.get("subject"), "coverageProjection.subject")
    if (
        _text(coverage_subject.get("subjectRef"), "coverageProjection.subject.subjectRef")
        != case["subjectRef"]
        or _sha(
            coverage_subject.get("snapshotDigest"),
            "coverageProjection.subject.snapshotDigest",
        )
        != case["subjectSnapshotDigest"]
    ):
        raise DwcCoaLoweringError("coverageProjection subject binding mismatch")
    for key in ("authorityGranted", "effectExecuted", "verifiedProtectionEstablished"):
        if coverage.get(key) is not False:
            raise DwcCoaLoweringError(f"coverageProjection.{key} must remain false at DW06 input")

    validation_standing = _text(
        coverage.get("validationStanding"), "coverageProjection.validationStanding"
    )
    candidates = coverage.get("authorizedValidationCandidateControlRefs", [])
    if not isinstance(candidates, list) or any(not isinstance(item, str) or not item for item in candidates):
        raise DwcCoaLoweringError("coverage validation candidate refs must be strings")

    validation = bundle.get("validationEvidence")
    unresolved: list[str] = []
    if validation_standing == "OPTIONAL_MAY_CHANGE_DOWNSTREAM_DECISION":
        if validation is None:
            unresolved.append(
                "Decision-relevant DW05 validation evidence is pending; the effect branch must not be treated as ready."
            )
        else:
            validation_row = _mapping(validation, "validationEvidence")
            if validation_row.get("kind") != "ordivon.security.dwc-authorized-validation-evidence":
                raise DwcCoaLoweringError("validationEvidence kind mismatch")
            if validation_row.get("caseRef") != case["caseRef"]:
                raise DwcCoaLoweringError("validationEvidence case binding mismatch")
            if validation_row.get("controlRef") not in candidates:
                raise DwcCoaLoweringError("validationEvidence does not bind a DW04 candidate control")
            if validation_row.get("productionSecurityStandingEstablished") is not False:
                raise DwcCoaLoweringError("DW05 study evidence cannot establish production Security standing")
            if validation_row.get("verifiedProtectionEstablished") is not False:
                raise DwcCoaLoweringError("DW05 study evidence cannot establish verified protection")
    elif validation_standing == "NOT_TRIGGERED_BY_DW04":
        if validation is not None:
            raise DwcCoaLoweringError("validationEvidence supplied even though DW04 did not trigger validation")
    else:
        raise DwcCoaLoweringError("unsupported DW04 validationStanding")

    modules = bundle.get("moduleBindings")
    if not isinstance(modules, list) or not modules:
        raise DwcCoaLoweringError("moduleBindings must be a non-empty array")
    seen: set[str] = set()
    for index, raw in enumerate(modules):
        row = _mapping(raw, f"moduleBindings[{index}]")
        module_id = _text(row.get("id"), f"moduleBindings[{index}].id")
        if module_id in seen:
            raise DwcCoaLoweringError(f"duplicate module binding: {module_id}")
        seen.add(module_id)
        _sha(row.get("digest"), f"moduleBindings[{index}].digest")
        _text(row.get("standing"), f"moduleBindings[{index}].standing")
        _text(row.get("ownerId"), f"moduleBindings[{index}].ownerId")

    return case, unresolved


def _manifest(
    bundle: Mapping[str, Any],
    case: Mapping[str, str],
    contracts: Mapping[str, Any],
    unresolved: list[str],
) -> dict[str, Any]:
    effect_contract = _bound_ref(contracts.get("effectAdmission"), "contracts.effectAdmission")
    consequence_contract = _bound_ref(
        contracts.get("consequenceVerification"), "contracts.consequenceVerification"
    )
    incident_contract = _bound_ref(
        contracts.get("incidentCaseProfile"), "contracts.incidentCaseProfile"
    )

    source_digest = canonical_digest(bundle)
    capabilities = [
        {
            "id": "capability:dw07-effect-execution",
            "capability": "security.effect.execution",
            "ownerId": "security.dw07",
            "sourceKind": "direct-owner",
            "bindingDigest": effect_contract["digest"],
            "truthBoundary": (
                "DW07 remains the future effect/admission owner. This binding names its current "
                "effect-admission contract only; it does not prove provider availability or authority."
            ),
        },
        {
            "id": "capability:dw08-consequence-verification",
            "capability": "security.consequence.verification",
            "ownerId": "security.dw08",
            "sourceKind": "direct-owner",
            "bindingDigest": consequence_contract["digest"],
            "truthBoundary": (
                "DW08 owns independent consequence verification semantics; an execution receipt "
                "alone is never world truth."
            ),
        },
        {
            "id": "capability:dw09-compromise-observation",
            "capability": "security.incident.compromise-observation",
            "ownerId": "security.dw09",
            "sourceKind": "direct-owner",
            "bindingDigest": incident_contract["digest"],
            "truthBoundary": (
                "DW09/incident natural owners retain compromise and recovery truth; this binding "
                "does not infer detection coverage or absence of compromise."
            ),
        },
    ]
    stages = [
        {
            "id": "stage:dw06-protection-plan",
            "ownerId": "security.dw06",
            "responsibility": (
                "Lower exact response/coverage/optional-study evidence into a bounded proposed "
                "protection branch and an independent compromise-hunt request."
            ),
            "dependsOn": [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": ["source-bundle"],
            "outputs": ["effect-proposal", "compromise-hunt-request"],
        },
        {
            "id": "stage:dw07-effect-execution",
            "ownerId": "security.dw07",
            "responsibility": (
                "Future natural owner may admit and execute one exact proposed effect only after "
                "its external authority prerequisite is independently satisfied."
            ),
            "dependsOn": ["stage:dw06-protection-plan"],
            "methodBindings": [],
            "capabilityBindings": ["capability:dw07-effect-execution"],
            "inputs": ["effect-proposal"],
            "outputs": ["effect-receipt"],
        },
        {
            "id": "stage:dw08-consequence-verification",
            "ownerId": "security.dw08",
            "responsibility": (
                "Independently verify the post-effect protection consequence from authoritative "
                "world observation rather than trusting the executor receipt."
            ),
            "dependsOn": ["stage:dw07-effect-execution"],
            "methodBindings": [],
            "capabilityBindings": ["capability:dw08-consequence-verification"],
            "inputs": ["effect-receipt"],
            "outputs": ["protection-observation"],
        },
        {
            "id": "stage:dw09-compromise-hunt",
            "ownerId": "security.dw09",
            "responsibility": (
                "Investigate compromise/persistence/recovery independently of whether the protection "
                "branch eventually verifies a mitigation consequence."
            ),
            "dependsOn": ["stage:dw06-protection-plan"],
            "methodBindings": [],
            "capabilityBindings": ["capability:dw09-compromise-observation"],
            "inputs": ["compromise-hunt-request"],
            "outputs": ["compromise-observation"],
        },
    ]
    edges = [
        {
            "id": "edge:dw06-dw07-effect-proposal",
            "from": {"stageId": "stage:dw06-protection-plan", "port": "effect-proposal"},
            "to": {"stageId": "stage:dw07-effect-execution", "port": "effect-proposal"},
            "contractRef": "contract:dwc-effect-proposal-r1",
        },
        {
            "id": "edge:dw07-dw08-effect-receipt",
            "from": {"stageId": "stage:dw07-effect-execution", "port": "effect-receipt"},
            "to": {
                "stageId": "stage:dw08-consequence-verification",
                "port": "effect-receipt",
            },
            "contractRef": "contract:security-consequence-input-r1",
        },
        {
            "id": "edge:dw06-dw09-compromise-hunt",
            "from": {
                "stageId": "stage:dw06-protection-plan",
                "port": "compromise-hunt-request",
            },
            "to": {"stageId": "stage:dw09-compromise-hunt", "port": "compromise-hunt-request"},
            "contractRef": "contract:incident-case-profile-r1",
        },
    ]
    gates = [
        {
            "id": "gate:dw06-dw07-effect-proposal",
            "producerStageId": "stage:dw06-protection-plan",
            "consumerStageId": "stage:dw07-effect-execution",
            "assumption": "DW07 receives one exact effect proposal bound to this defense epoch.",
            "guarantee": "DW06 emits only a non-authoritative proposed effect; no grant or execution is implied.",
            "verifierOwnerId": "security.dw07",
            "supportScope": "DW06->DW07 exact effect-proposal contract seam only",
            "required": True,
        },
        {
            "id": "gate:dw07-dw08-effect-receipt",
            "producerStageId": "stage:dw07-effect-execution",
            "consumerStageId": "stage:dw08-consequence-verification",
            "assumption": "DW08 receives an executor receipt bound to the exact admitted request identity.",
            "guarantee": "Receipt binding is checked without treating receipt content as authoritative world truth.",
            "verifierOwnerId": "security.dw08",
            "supportScope": "DW07->DW08 exact receipt/consequence-input seam only",
            "required": True,
        },
        {
            "id": "gate:dw06-dw09-compromise-hunt",
            "producerStageId": "stage:dw06-protection-plan",
            "consumerStageId": "stage:dw09-compromise-hunt",
            "assumption": "DW09 receives the exact bounded case/subject evidence needed for compromise investigation.",
            "guarantee": "Protection planning does not close compromise/persistence/recovery standing.",
            "verifierOwnerId": "security.dw09",
            "supportScope": "DW06->DW09 incident-case admission seam only",
            "required": True,
        },
    ]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": f"circuit:dwc-coa:{case['caseRef']}",
        "objectiveRef": {"id": "objective:dwc-coa-r1", "digest": source_digest},
        "methodBindings": [],
        "capabilityBindings": capabilities,
        "stages": stages,
        "edges": edges,
        "gateRequirements": gates,
        "unresolvedAssumptions": sorted(unresolved),
        "nonClaims": [
            "This Circuit is a task-local non-authoritative DWC plan projection.",
            "Circuit compilation does not schedule, authorize, execute, retry, or verify an effect.",
            "Protection and compromise/recovery remain independent branches.",
            "Mechanical Composition closure is not Security/domain acceptance.",
        ],
    }


def _authority_requirements(
    manifest: Mapping[str, Any], contracts: Mapping[str, Any]
) -> dict[str, Any]:
    compiled = compile_manifest(dict(manifest))
    effect_contract = _bound_ref(contracts.get("effectAdmission"), "contracts.effectAdmission")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.authority-requirement-set",
        "circuitRef": {
            "id": manifest["circuitId"],
            "digest": compiled["manifestDigest"],
        },
        "requirements": [
            {
                "id": "authority:dw07-effect-execution",
                "stageId": "stage:dw07-effect-execution",
                "capabilityBindingId": "capability:dw07-effect-execution",
                "authorityOwnerId": "security.effect-authority",
                "authorityContractRef": effect_contract,
                "required": True,
                "nonClaims": [
                    "This declares the external authority prerequisite for a future effect stage.",
                    "It is not an ALLOW decision, credential, Grant, or execution permission.",
                ],
            }
        ],
        "nonClaims": [
            "DW06 authors one explicit task-local authority prerequisite and does not decide it.",
            "Composition does not infer complete effect coverage or grant execution authority.",
        ],
    }


def _verifier_binding_set(
    obligation_set: Mapping[str, Any], contracts: Mapping[str, Any]
) -> dict[str, Any]:
    by_gate = {row["gateId"]: row for row in obligation_set["obligations"]}
    mapping = {
        "gate:dw06-dw07-effect-proposal": (
            "security.dw07",
            "owner-native-contract",
            _bound_ref(contracts.get("effectAdmission"), "contracts.effectAdmission"),
        ),
        "gate:dw07-dw08-effect-receipt": (
            "security.dw08",
            "owner-native-contract",
            _bound_ref(
                contracts.get("consequenceVerification"),
                "contracts.consequenceVerification",
            ),
        ),
        "gate:dw06-dw09-compromise-hunt": (
            "security.dw09",
            "owner-native-profile",
            _bound_ref(
                contracts.get("incidentCaseProfile"), "contracts.incidentCaseProfile"
            ),
        ),
    }
    bindings = []
    for gate_id in sorted(by_gate):
        obligation = by_gate[gate_id]
        owner, verifier_class, verifier_ref = mapping[gate_id]
        bindings.append(
            {
                "gateId": gate_id,
                "obligationDigest": obligation["obligationDigest"],
                "verifierOwnerId": owner,
                "verifierRef": verifier_ref,
                "verifierClass": verifier_class,
                "nativeSpecificationRef": copy.deepcopy(verifier_ref),
                "supportScope": obligation["supportScope"],
                "nonClaims": [
                    "Binding names an exact natural-owner contract/profile; it does not execute or certify the verifier."
                ],
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.task-local-verifier-binding-set",
        "circuitRef": copy.deepcopy(obligation_set["circuitRef"]),
        "obligationSetDigest": obligation_set["obligationSetDigest"],
        "bindings": bindings,
        "nonClaims": [
            "Bindings are exact and task-local, not a verifier registry or ranking.",
            "Resolved bindings do not discharge gates or establish domain acceptance.",
        ],
    }


def lower_dwc_coa(
    source_bundle: Mapping[str, Any], contracts: Mapping[str, Any]
) -> dict[str, Any]:
    case, unresolved = _validate_source_bundle(source_bundle)
    manifest = _manifest(source_bundle, case, contracts, unresolved)
    compiled = compile_manifest(manifest)
    authority_requirements = _authority_requirements(manifest, contracts)
    authority_obligations = compile_authority_obligations(
        manifest, authority_requirements
    )
    verification_obligations = compile_verification_obligations(manifest)
    verifier_bindings = _verifier_binding_set(verification_obligations, contracts)
    verifier_resolution = resolve_verifier_bindings(
        verification_obligations, verifier_bindings
    )
    gate_projection = evaluate_gate_results(manifest, [])

    response = _mapping(source_bundle["responseDecision"], "responseDecision")
    workflow_projection = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-workflow-boundary-projection-r1",
        "structuralConcurrencyGroups": [
            ["stage:dw07-effect-execution", "stage:dw09-compromise-hunt"]
        ],
        "durableWorkflowOwner": "external:temporal-or-cacao-compatible",
        "policyActionClass": response["actionClass"],
        "deadlineStanding": response.get("deadlineStatus", "UNSET"),
        "deadlineBudget": response.get("deadlineBudget"),
        "schedulerDecisionIncluded": False,
        "retryPolicyOwnedHere": False,
        "waitTimerPolicyOwnedHere": False,
        "loopPolicyOwnedHere": False,
        "truthBoundary": (
            "This sidecar describes structural concurrency and the external durable-workflow "
            "ownership boundary. It is not part of the Cognitive Circuit manifest and does "
            "not schedule, retry, wait, or loop."
        ),
    }

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": LOWERING_KIND,
        "caseBinding": dict(case),
        "sourceBundleDigest": canonical_digest(source_bundle),
        "manifest": manifest,
        "compiledCircuit": compiled,
        "authorityRequirementSet": authority_requirements,
        "authorityObligationSet": authority_obligations,
        "verificationObligationSet": verification_obligations,
        "verifierBindingSet": verifier_bindings,
        "verifierResolution": verifier_resolution,
        "gateProjection": gate_projection,
        "workflowProjection": workflow_projection,
        "authorityGranted": False,
        "executionAuthorityGranted": False,
        "verifierExecutionPerformed": False,
        "effectExecuted": False,
        "verifiedProtectionEstablished": False,
        "compromiseAbsenceEstablished": False,
        "domainAcceptanceEstablished": False,
        "truthBoundary": (
            "DW06 lowers exact already-selected DWC evidence into existing public Composition "
            "contracts. Authority obligations remain prerequisites, verifier bindings remain "
            "bindings, and empty gate results intentionally leave Composition Gates open. "
            "No workflow, effect, verifier execution, Security verdict, or domain acceptance "
            "is performed here."
        ),
    }
    result["loweringDigest"] = canonical_digest(result)
    return result


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source_bundle", type=Path)
    parser.add_argument("contracts", type=Path)
    args = parser.parse_args()
    bundle = json.loads(args.source_bundle.read_text(encoding="utf-8"))
    contracts = json.loads(args.contracts.read_text(encoding="utf-8"))
    print(json.dumps(lower_dwc_coa(bundle, contracts), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
