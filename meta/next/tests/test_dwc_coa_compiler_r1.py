from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dwc_coa_compiler_r1.py"
SPEC = importlib.util.spec_from_file_location("dwc_coa_compiler_r1", SCRIPT)
assert SPEC and SPEC.loader
dw06 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dw06)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64
D5 = "sha256:" + "5" * 64
D6 = "sha256:" + "6" * 64


def bundle(*, validation_triggered=False, include_validation=False):
    validation_standing = (
        "OPTIONAL_MAY_CHANGE_DOWNSTREAM_DECISION"
        if validation_triggered
        else "NOT_TRIGGERED_BY_DW04"
    )
    candidates = ["control:test"] if validation_triggered else []
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-coa-source-bundle-r1",
        "caseBinding": {
            "caseRef": "case:test",
            "epochRef": "epoch:test",
            "subjectRef": "subject:test",
            "subjectSnapshotDigest": D1,
        },
        "responseDecision": {
            "schemaVersion": 1,
            "kind": "ordivon.security.response-policy-decision",
            "caseRef": "case:test",
            "subject": {"subjectRef": "subject:test", "snapshotDigest": D1},
            "standing": "ACTION_ONLY",
            "actionClass": "out-of-cycle",
            "deadlineStatus": "UNSET",
            "deadlineBudget": None,
            "authorityGranted": False,
        },
        "coverageProjection": {
            "schemaVersion": 1,
            "kind": "ordivon.security.dwc-attack-coverage-projection",
            "caseRef": "case:test",
            "subject": {"subjectRef": "subject:test", "snapshotDigest": D1},
            "validationStanding": validation_standing,
            "authorizedValidationCandidateControlRefs": candidates,
            "authorityGranted": False,
            "effectExecuted": False,
            "verifiedProtectionEstablished": False,
        },
        "validationEvidence": None,
        "moduleBindings": [
            {"id": "dw01", "ownerId": "security.dw01", "digest": D2, "standing": "QUALIFIED"},
            {"id": "dw02", "ownerId": "security.dw02", "digest": D3, "standing": "QUALIFIED"},
            {"id": "dw03", "ownerId": "security.dw03", "digest": D4, "standing": "QUALIFIED"},
            {"id": "dw04", "ownerId": "security.dw04", "digest": D5, "standing": "QUALIFIED"},
        ],
        "nonClaims": ["test-only"],
    }
    if include_validation:
        value["validationEvidence"] = {
            "schemaVersion": 1,
            "kind": "ordivon.security.dwc-authorized-validation-evidence",
            "caseRef": "case:test",
            "controlRef": "control:test",
            "productionSecurityStandingEstablished": False,
            "verifiedProtectionEstablished": False,
        }
        value["moduleBindings"].append(
            {"id": "dw05", "ownerId": "security.dw05", "digest": D6, "standing": "QUALIFIED"}
        )
    return value


def contracts():
    return {
        "effectAdmission": {"id": "security:effect-admission-r1", "digest": D2},
        "consequenceVerification": {"id": "security:consequence-verification-r1", "digest": D3},
        "incidentCaseProfile": {"id": "profile:incident-case-r1", "digest": D4},
    }


def test_lowering_compiles_existing_circuit_and_leaves_gates_open():
    result = dw06.lower_dwc_coa(bundle(), contracts())
    compiled = result["compiledCircuit"]
    assert compiled["stageOrder"][0] == "stage:dw06-protection-plan"
    assert set(compiled["stageOrder"]) == {
        "stage:dw06-protection-plan",
        "stage:dw07-effect-execution",
        "stage:dw08-consequence-verification",
        "stage:dw09-compromise-hunt",
    }
    assert compiled["stageOrder"].index("stage:dw07-effect-execution") < compiled[
        "stageOrder"
    ].index("stage:dw08-consequence-verification")
    assert result["gateProjection"]["standing"] == "COMPOSITION_GATES_OPEN"
    assert result["gateProjection"]["missingGateIds"] == [
        "gate:dw06-dw07-effect-proposal",
        "gate:dw06-dw09-compromise-hunt",
        "gate:dw07-dw08-effect-receipt",
    ]
    assert result["domainAcceptanceEstablished"] is False


def test_authority_requirement_is_exact_but_grants_nothing():
    result = dw06.lower_dwc_coa(bundle(), contracts())
    obligations = result["authorityObligationSet"]
    assert obligations["requiredObligationIds"] == ["authority:dw07-effect-execution"]
    assert obligations["mechanicalBindingEstablished"] is True
    assert obligations["effectCoverageEstablished"] is False
    assert obligations["authorityGranted"] is False
    assert obligations["executionAuthorityGranted"] is False
    assert result["authorityGranted"] is False
    assert result["executionAuthorityGranted"] is False


def test_verifier_bindings_resolve_without_executing_or_closing_gates():
    result = dw06.lower_dwc_coa(bundle(), contracts())
    resolution = result["verifierResolution"]
    assert resolution["standing"] == "VERIFIER_BINDINGS_RESOLVED"
    assert resolution["mechanicalResolution"] is True
    assert resolution["executionAuthorityGranted"] is False
    assert resolution["domainAcceptanceEstablished"] is False
    assert result["verifierExecutionPerformed"] is False
    assert result["gateProjection"]["mechanicalClosure"] is False


def test_parallelism_is_structural_and_scheduler_stays_external():
    result = dw06.lower_dwc_coa(bundle(), contracts())
    workflow = result["workflowProjection"]
    assert workflow["structuralConcurrencyGroups"] == [
        ["stage:dw07-effect-execution", "stage:dw09-compromise-hunt"]
    ]
    assert workflow["durableWorkflowOwner"] == "external:temporal-or-cacao-compatible"
    assert workflow["schedulerDecisionIncluded"] is False
    assert workflow["retryPolicyOwnedHere"] is False
    assert workflow["waitTimerPolicyOwnedHere"] is False
    assert workflow["loopPolicyOwnedHere"] is False


def test_missing_decision_relevant_validation_stays_unresolved():
    result = dw06.lower_dwc_coa(bundle(validation_triggered=True), contracts())
    assert result["manifest"]["unresolvedAssumptions"]
    assert "DW05 validation evidence is pending" in result["manifest"]["unresolvedAssumptions"][0]
    assert result["gateProjection"]["standing"] == "COMPOSITION_GATES_OPEN"


def test_supplied_dw05_study_evidence_clears_only_the_pending_assumption():
    result = dw06.lower_dwc_coa(
        bundle(validation_triggered=True, include_validation=True), contracts()
    )
    assert result["manifest"]["unresolvedAssumptions"] == []
    assert result["verifiedProtectionEstablished"] is False
    assert result["manifest"]["unresolvedAssumptions"] == []


def test_response_subject_mismatch_fails_closed():
    value = bundle()
    value["responseDecision"]["subject"]["snapshotDigest"] = D2
    try:
        dw06.lower_dwc_coa(value, contracts())
    except dw06.DwcCoaLoweringError as exc:
        assert "responseDecision subject binding mismatch" in str(exc)
    else:
        raise AssertionError("mismatch should fail")


def test_coverage_subject_mismatch_fails_closed():
    value = bundle()
    value["coverageProjection"]["subject"]["subjectRef"] = "subject:other"
    try:
        dw06.lower_dwc_coa(value, contracts())
    except dw06.DwcCoaLoweringError as exc:
        assert "coverageProjection subject binding mismatch" in str(exc)
    else:
        raise AssertionError("mismatch should fail")


def test_unknown_or_not_applicable_response_does_not_compile_effect_plan():
    value = bundle()
    value["responseDecision"]["standing"] = "UNKNOWN_INPUT"
    try:
        dw06.lower_dwc_coa(value, contracts())
    except dw06.DwcCoaLoweringError as exc:
        assert "actionable DW03" in str(exc)
    else:
        raise AssertionError("non-actionable response should fail")


def test_upstream_authority_or_verified_protection_cannot_be_smuggled_in():
    value = bundle()
    value["responseDecision"]["authorityGranted"] = True
    try:
        dw06.lower_dwc_coa(value, contracts())
    except dw06.DwcCoaLoweringError as exc:
        assert "must not grant effect authority" in str(exc)
    else:
        raise AssertionError("authority smuggling should fail")

    value = bundle()
    value["coverageProjection"]["verifiedProtectionEstablished"] = True
    try:
        dw06.lower_dwc_coa(value, contracts())
    except dw06.DwcCoaLoweringError as exc:
        assert "verifiedProtectionEstablished" in str(exc)
    else:
        raise AssertionError("protection smuggling should fail")
