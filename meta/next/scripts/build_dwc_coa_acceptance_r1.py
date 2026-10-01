#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dwc_coa_compiler_r1 import lower_dwc_coa  # noqa: E402


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    dw01_path = REPO_ROOT / "platform/security/evidence/acceptance/dwc-subject-exposure-r1-20261001.json"
    dw02_path = REPO_ROOT / "platform/security/evidence/acceptance/dwc-threat-applicability-r1-20261001.json"
    dw03_path = REPO_ROOT / "platform/security/evidence/acceptance/dw03-response-policy-r1-20261001.json"
    dw04_accept_path = REPO_ROOT / "platform/security/evidence/acceptance/dw04-attack-coverage-r1-20261001.json"
    dw04_case_path = REPO_ROOT / "platform/security/evidence/acceptance/dwc-attack-coverage-r1/exchange-proxylogon-2021.projection.json"
    dw05_path = REPO_ROOT / "studies/security/dwc-r21-dw05-authorized-validation/evidence/acceptance/dw05-authorized-validation-r1-20261001.json"
    effect_path = REPO_ROOT / "platform/security/docs/EFFECT-ADMISSION-DIFFERENTIAL.md"
    consequence_path = REPO_ROOT / "platform/security/docs/CONSEQUENCE-VERIFICATION-DIFFERENTIAL.md"
    incident_path = REPO_ROOT / "meta/next/docs/INCIDENT_CASE_PROFILE_R1.md"

    dw01 = load(dw01_path)
    dw02 = load(dw02_path)
    dw03 = load(dw03_path)
    dw04_accept = load(dw04_accept_path)
    dw04_case = load(dw04_case_path)
    dw05 = load(dw05_path)

    subject = dw04_case["subject"]
    source_bundle = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-coa-source-bundle-r1",
        "caseBinding": {
            "caseRef": dw04_case["caseRef"],
            "epochRef": dw04_case["epochRef"],
            "subjectRef": subject["subjectRef"],
            "subjectSnapshotDigest": subject["snapshotDigest"],
        },
        "responseDecision": {
            "schemaVersion": 1,
            "kind": "ordivon.security.response-policy-decision",
            "decisionRef": "qualification:dw03:proxylogon:dw04-bound-r1",
            "caseRef": dw04_case["caseRef"],
            "subject": {
                "subjectRef": subject["subjectRef"],
                "snapshotDigest": subject["snapshotDigest"],
            },
            "standing": "ACTION_ONLY",
            "actionClass": "immediate",
            "deadlineStatus": "UNSET",
            "deadlineBudget": None,
            "authorityGranted": False,
            "policyScope": "qualification-only-representative-SSVC-row",
            "sourceRef": str(dw03_path.relative_to(REPO_ROOT)),
            "sourceDigest": file_digest(dw03_path),
            "truthBoundary": (
                "Qualification-only response carrier rebound to the exact DW04 historical "
                "subject. 'immediate' mirrors the already-qualified representative DW03 test "
                "row for known-exploited/open/automatable/very-high conditions. It is not a "
                "production organization policy, SLE, deadline, grant, or live Exchange decision."
            ),
        },
        "coverageProjection": dw04_case,
        "validationEvidence": None,
        "moduleBindings": [
            {
                "id": "dw01",
                "ownerId": "security.dw01",
                "digest": file_digest(dw01_path),
                "standing": dw01["standing"],
            },
            {
                "id": "dw02",
                "ownerId": "security.dw02",
                "digest": file_digest(dw02_path),
                "standing": dw02["standing"],
            },
            {
                "id": "dw03",
                "ownerId": "security.dw03",
                "digest": file_digest(dw03_path),
                "standing": dw03["standing"],
            },
            {
                "id": "dw04",
                "ownerId": "security.dw04",
                "digest": file_digest(dw04_accept_path),
                "standing": dw04_accept["standing"],
            },
            {
                "id": "dw05",
                "ownerId": "security.dw05",
                "digest": file_digest(dw05_path),
                "standing": dw05["standing"],
            },
        ],
        "nonClaims": [
            "Module acceptance bindings establish mechanics availability only, not case truth.",
            "The exact DW04 projection is the bounded case carrier for this historical qualification.",
            "DW05 is mechanically available but not case-triggered because DW04 validationStanding is NOT_TRIGGERED_BY_DW04.",
            "The response carrier is qualification-only and is not production policy or authority.",
        ],
    }
    contracts = {
        "effectAdmission": {
            "id": "security:effect-admission-differential-r1",
            "digest": file_digest(effect_path),
        },
        "consequenceVerification": {
            "id": "security:consequence-verification-differential-r1",
            "digest": file_digest(consequence_path),
        },
        "incidentCaseProfile": {
            "id": "profile:incident-case-r1",
            "digest": file_digest(incident_path),
        },
    }

    result = lower_dwc_coa(source_bundle, contracts)
    assert result["authorityGranted"] is False
    assert result["executionAuthorityGranted"] is False
    assert result["effectExecuted"] is False
    assert result["verifiedProtectionEstablished"] is False
    assert result["compromiseAbsenceEstablished"] is False
    assert result["domainAcceptanceEstablished"] is False
    assert result["authorityObligationSet"]["authorityGranted"] is False
    assert result["verifierResolution"]["standing"] == "VERIFIER_BINDINGS_RESOLVED"
    assert result["gateProjection"]["standing"] == "COMPOSITION_GATES_OPEN"
    assert result["gateProjection"]["mechanicalClosure"] is False
    assert result["workflowProjection"]["schedulerDecisionIncluded"] is False

    out = REPO_ROOT / "meta/next/evidence/acceptance"
    source_path = out / "dwc-coa-r1-source-bundle-20261001.json"
    contracts_path = out / "dwc-coa-r1-contract-bindings-20261001.json"
    lowering_path = out / "dwc-coa-r1-lowering-20261001.json"
    source_path.write_text(json.dumps(source_bundle, indent=2, sort_keys=True) + "\n")
    contracts_path.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n")
    lowering_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    summary = {
        "sourceBundleDigest": result["sourceBundleDigest"],
        "manifestDigest": result["compiledCircuit"]["manifestDigest"],
        "compiledDigest": result["compiledCircuit"]["compiledDigest"],
        "authorityObligationSetDigest": result["authorityObligationSet"]["obligationSetDigest"],
        "verificationObligationSetDigest": result["verificationObligationSet"]["obligationSetDigest"],
        "verifierResolution": result["verifierResolution"]["standing"],
        "gateStanding": result["gateProjection"]["standing"],
        "missingGateIds": result["gateProjection"]["missingGateIds"],
        "authorityGranted": result["authorityGranted"],
        "executionAuthorityGranted": result["executionAuthorityGranted"],
        "effectExecuted": result["effectExecuted"],
        "verifiedProtectionEstablished": result["verifiedProtectionEstablished"],
        "compromiseAbsenceEstablished": result["compromiseAbsenceEstablished"],
        "schedulerDecisionIncluded": result["workflowProjection"]["schedulerDecisionIncluded"],
        "loweringDigest": result["loweringDigest"],
        "output": str(lowering_path.relative_to(REPO_ROOT)),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
