"""Compare one browser subject and its public observations without effects."""

from __future__ import annotations

from .browser_security_observation import (
    _changed_json_paths,
    classify_browser_security_observation_validity,
)
from .browser_security_witness import (
    BrowserSecurityWitness,
    BrowserSecurityWitnessBundle,
)

REPAIR_ROUTES = {
    "CF02": "network/provider-path",
    "CF03": "http-request-presentation",
    "CF04": "browser-launch-js-presentation",
    "CF05": "automation-control-layer",
    "CF06": "cross-layer-consistency",
    "CF07": "profile-session-lifecycle",
    "CF08": "provider-policy-drift-attribution-only",
}


def compare_browser_security_witnesses(
    baseline: BrowserSecurityWitness, candidate: BrowserSecurityWitness
) -> dict[str, object]:
    before = baseline.observation_map()
    after = candidate.observation_map()
    rows: list[dict[str, object]] = []
    changed_families: set[str] = set()
    detector_drift: set[str] = set()

    for detector_id in sorted(set(before) | set(after)):
        left = before.get(detector_id)
        right = after.get(detector_id)
        if left is None:
            rows.append({"detectorId": detector_id, "status": "ADDED", "family": right.family})
            continue
        if right is None:
            rows.append({"detectorId": detector_id, "status": "MISSING", "family": left.family})
            continue
        if left.family != right.family:
            raise ValueError(f"detector family changed for {detector_id}")
        if left.detector_version != right.detector_version or left.coverage != right.coverage:
            detector_drift.add(detector_id)
            row = {
                "detectorId": detector_id,
                "family": left.family,
                "status": "DETECTOR_DRIFT",
                "baselineVersion": left.detector_version,
                "candidateVersion": right.detector_version,
            }
            if left.coverage != right.coverage:
                row["baselineCoverage"] = left.coverage
                row["candidateCoverage"] = right.coverage
            rows.append(row)
            continue
        status = "UNCHANGED" if left.observation_digest == right.observation_digest else "CHANGED"
        if status == "CHANGED":
            changed_families.add(left.family)
        rows.append({"detectorId": detector_id, "family": left.family, "status": status})

    infrastructure_changes = {
        "browserBinary": baseline.browser_binary_digest != candidate.browser_binary_digest,
        "controlLayer": baseline.control_layer_digest != candidate.control_layer_digest,
        "networkAuthority": baseline.network_authority_digest != candidate.network_authority_digest,
    }

    return {
        "schemaVersion": 1,
        "baselineWitnessId": baseline.witness_id,
        "candidateWitnessId": candidate.witness_id,
        "infrastructureChanges": infrastructure_changes,
        "detectors": rows,
        "changedFamilies": sorted(changed_families),
        "detectorDrift": sorted(detector_drift),
        "repairRoutes": [REPAIR_ROUTES[f] for f in sorted(changed_families)],
        "challengeStandingChanged": baseline.challenge_standing != candidate.challenge_standing,
        "rootCauseEstablished": False,
    }


def compare_browser_security_bundles(
    baseline: BrowserSecurityWitnessBundle, candidate: BrowserSecurityWitnessBundle
) -> dict[str, object]:
    result = compare_browser_security_witnesses(baseline.witness, candidate.witness)
    baseline_public = baseline.public_observation_map()
    candidate_public = candidate.public_observation_map()
    drift_ids = set(result["detectorDrift"])
    invalid_ids: set[str] = set()
    validity_rows: list[dict[str, object]] = []

    detector_rows = {row["detectorId"]: row for row in result["detectors"]}
    for detector_id in sorted(set(baseline_public) | set(candidate_public)):
        row = detector_rows.get(detector_id)
        family = row.get("family") if isinstance(row, dict) else None
        before = (
            classify_browser_security_observation_validity(baseline_public[detector_id])
            if detector_id in baseline_public
            else {"standing": "MISSING", "issues": []}
        )
        after = (
            classify_browser_security_observation_validity(candidate_public[detector_id])
            if detector_id in candidate_public
            else {"standing": "MISSING", "issues": []}
        )
        validity_rows.append(
            {
                "detectorId": detector_id,
                "family": family,
                "baseline": before,
                "candidate": after,
            }
        )
        if before["standing"] != "VALID" or after["standing"] != "VALID":
            invalid_ids.add(detector_id)
            if isinstance(row, dict) and row.get("status") not in {
                "ADDED",
                "MISSING",
                "DETECTOR_DRIFT",
            }:
                row["status"] = "OBSERVATION_INVALID"

    valid_changed_families = {
        row["family"]
        for row in result["detectors"]
        if row.get("status") == "CHANGED" and isinstance(row.get("family"), str)
    }
    result["changedFamilies"] = sorted(valid_changed_families)
    result["repairRoutes"] = [REPAIR_ROUTES[family] for family in sorted(valid_changed_families)]

    changes: list[dict[str, object]] = []
    for row in result["detectors"]:
        detector_id = row["detectorId"]
        if row["status"] != "CHANGED" or detector_id in drift_ids or detector_id in invalid_ids:
            continue
        changes.append(
            {
                "detectorId": detector_id,
                "changedPaths": _changed_json_paths(
                    baseline_public[detector_id], candidate_public[detector_id]
                ),
            }
        )
    result["publicObservationChanges"] = changes
    result["observationValidity"] = validity_rows
    result["invalidObservationDetectors"] = sorted(invalid_ids)
    result["observationClassificationSuppressed"] = bool(invalid_ids)
    return result
