#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from ordivon_security_v2.attack_coverage import project_attack_coverage
from ordivon_security_v2.subject_exposure import build_subject_exposure_snapshot
from ordivon_security_v2.threat_applicability import fuse_threat_applicability


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_subject(case_id: str) -> dict[str, Any]:
    observed_at = "2021-03-02T00:00:00Z"
    return build_subject_exposure_snapshot(
        case_ref=f"case:dw04:{case_id}",
        epoch_ref=f"epoch:dw04:{case_id}:historical-replay",
        subject_ref=f"historical-subject:{case_id}",
        identity_observations=[
            {
                "id": f"{case_id}:product",
                "ownerId": "historical-replay-owner",
                "sourceRef": "fixture:dw04:exchange-attack-flow-replay-r1",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "POINT_IN_TIME_OBSERVED",
                "observedAt": observed_at,
                "evidenceRefs": ["fixture:dw04:exchange-attack-flow-replay-r1"],
                "dimension": "product",
                "identityRef": {
                    "scheme": "vendor-product-name",
                    "value": "Microsoft Exchange Server historical replay",
                },
            },
            {
                "id": f"{case_id}:version",
                "ownerId": "historical-replay-owner",
                "sourceRef": "fixture:dw04:exchange-attack-flow-replay-r1",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "POINT_IN_TIME_OBSERVED",
                "observedAt": observed_at,
                "evidenceRefs": ["fixture:dw04:exchange-attack-flow-replay-r1"],
                "dimension": "version",
                "identityRef": {
                    "scheme": "historical-replay-class",
                    "value": "affected-build-class",
                },
            },
        ],
        exposure_observations=[
            {
                "id": f"{case_id}:https",
                "ownerId": "historical-replay-owner",
                "sourceRef": "fixture:dw04:exchange-attack-flow-replay-r1",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "POINT_IN_TIME_OBSERVED",
                "observedAt": observed_at,
                "evidenceRefs": ["fixture:dw04:exchange-attack-flow-replay-r1"],
                "surfaceId": "exchange-https",
                "endpointRef": "historical://exchange/https",
                "originScope": "historical-public-replay",
                "transport": "https",
                "reachability": "REACHABLE",
            }
        ],
        required_identity_dimensions=["product", "version"],
        expected_exposure_surfaces=["exchange-https"],
        non_claims=[
            "Historical replay only; not a current live Exchange deployment.",
            "POINT_IN_TIME_OBSERVED is scoped to the frozen historical replay epoch.",
        ],
    )


def replay(case: dict[str, Any], fixture_digest: str) -> dict[str, Any]:
    subject = build_subject(case["id"])
    vulnerability_ref = case["vulnerabilityRefs"][0]
    binding = {
        "subjectRef": subject["subjectRef"],
        "snapshotDigest": subject["snapshotDigest"],
        "evidenceRef": subject["evidenceRef"],
    }
    applicability = fuse_threat_applicability(
        subject=subject,
        vulnerability_ref=vulnerability_ref,
        evidence=[
            {
                "evidenceRef": f"{case['id']}:historical-product-status",
                "sourceKind": "csaf",
                "providerNativeRef": f"fixture://dw04/{case['id']}/product-status",
                "artifactDigest": digest(
                    {"case": case["id"], "vulnerabilityRef": vulnerability_ref, "status": "affected"}
                ),
                "vulnerabilityRef": vulnerability_ref,
                "admission": "ADMITTED",
                "currentness": "CURRENT",
                "subjectBinding": binding,
                "projectedApplicability": "AFFECTED",
            },
            {
                "evidenceRef": f"{case['id']}:historical-known-exploited",
                "sourceKind": "cisa-kev",
                "providerNativeRef": f"fixture://dw04/{case['id']}/known-exploited",
                "artifactDigest": digest(
                    {"case": case["id"], "vulnerabilityRef": vulnerability_ref, "knownExploited": True}
                ),
                "vulnerabilityRef": vulnerability_ref,
                "admission": "ADMITTED",
                "currentness": "CURRENT",
                "knownExploited": True,
            },
        ],
    )
    flow = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-attack-flow-reference",
        "flowRef": f"attack-flow:{case['id']}:historical-r1",
        "sourceRef": "fixture:dw04:exchange-attack-flow-replay-r1",
        "sourceDigest": fixture_digest,
        "attackFlowVersion": "4.0",
        "subjectBinding": {
            "caseRef": subject["caseRef"],
            "epochRef": subject["epochRef"],
            "subjectRef": subject["subjectRef"],
            "snapshotDigest": subject["snapshotDigest"],
            "evidenceRef": subject["evidenceRef"],
        },
        "actions": case["actions"],
        "edges": case["edges"],
        "entryActionRefs": case["entryActionRefs"],
        "objectiveActionRefs": case["objectiveActionRefs"],
    }
    controls = [
        {
            **mapped,
            "ownerRef": "external-mapping-owner",
            "implementationStanding": "UNKNOWN",
            "implementationEvidenceRefs": [],
            "observationStanding": "UNKNOWN",
            "observationEvidenceRefs": [],
            "effectivenessStanding": "UNKNOWN",
            "effectivenessEvidenceRefs": [],
        }
        for mapped in case["mappedDefenses"]
    ]
    return project_attack_coverage(
        subject=subject,
        applicability=applicability,
        flow=flow,
        controls=controls,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    fixture_digest = digest(fixture)
    projections = [replay(case, fixture_digest) for case in fixture["cases"]]

    summary = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dw04-historical-replay-result",
        "fixtureDigest": fixture_digest,
        "cases": [
            {
                "caseRef": item["caseRef"],
                "vulnerabilityRef": item["vulnerabilityRef"],
                "applicabilityClaim": item["applicabilityClaim"],
                "structuralCutActionRefs": item["structuralCutActionRefs"],
                "unmappedActionRefs": item["gaps"]["unmappedActionRefs"],
                "implementedButEffectivenessUnknownActionRefs": item["gaps"][
                    "implementedButEffectivenessUnknownActionRefs"
                ],
                "validationStanding": item["validationStanding"],
                "authorityGranted": item["authorityGranted"],
                "verifiedProtectionEstablished": item["verifiedProtectionEstablished"],
            }
            for item in projections
        ],
        "claimBoundary": (
            "Historical semantic replay only. External mappings remain mapping evidence; "
            "local implementation, observation and effectiveness are UNKNOWN. No exploit "
            "execution, effect authority, verified protection, compromise absence or recovery "
            "standing is established."
        ),
    }

    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for item in projections:
            case_id = item["caseRef"].split(":")[-1]
            (args.output_dir / f"{case_id}.projection.json").write_text(
                json.dumps(item, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        (args.output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
