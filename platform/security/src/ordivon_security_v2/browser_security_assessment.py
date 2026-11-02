"""Pure comparison and cross-carrier assessment of browser-security witnesses.

Evidence encoding and validation remain owned by browser_security_witness.
"""

from __future__ import annotations

from .browser_security_witness import (
    BrowserSecurityWitness,
    BrowserSecurityWitnessBundle,
    _required_text,
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


def classify_browser_security_observation_validity(
    observation: object,
) -> dict[str, object]:
    """Classify whether one public observation is usable for subject-drift comparison.

    Collector-side external observer failures are represented inside the public observation rather
    than by changing the witness schema. Security-v2 treats those failure sentinels as observation
    validity, not as browser subject evidence.
    """

    issues: list[dict[str, str]] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, dict):
            standing = value.get("standing")
            if isinstance(standing, str):
                normalized = standing.strip().upper()
                if normalized == "UNAVAILABLE":
                    issue = {
                        "path": path,
                        "standing": "OBSERVER_UNAVAILABLE",
                        "sourceStanding": normalized,
                    }
                    detail = value.get("detail")
                    if isinstance(detail, str) and detail.strip():
                        issue["detail"] = detail.strip()
                    issues.append(issue)
                elif normalized in {"ERROR", "FAILED"}:
                    issue = {
                        "path": path,
                        "standing": "DETECTOR_FAILED",
                        "sourceStanding": normalized,
                    }
                    detail = value.get("detail")
                    if isinstance(detail, str) and detail.strip():
                        issue["detail"] = detail.strip()
                    issues.append(issue)
            for key, child in value.items():
                visit(child, f"{path}.{key}")
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(observation, "$")
    if not issues:
        return {"standing": "VALID", "issues": []}
    standing = (
        "DETECTOR_FAILED"
        if any(issue["standing"] == "DETECTOR_FAILED" for issue in issues)
        else "OBSERVER_UNAVAILABLE"
    )
    return {"standing": standing, "issues": issues}


def _changed_json_paths(left: object, right: object, path: str = "$") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        changed: list[str] = []
        for key in sorted(set(left) | set(right)):
            child_path = f"{path}.{key}"
            if key not in left or key not in right:
                changed.append(child_path)
            else:
                changed.extend(_changed_json_paths(left[key], right[key], child_path))
        return changed
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        changed: list[str] = []
        for index, (a, b) in enumerate(zip(left, right)):
            changed.extend(_changed_json_paths(a, b, f"{path}[{index}]"))
        return changed
    return [] if left == right else [path]


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


def compare_browser_security_pool(
    carriers: dict[str, tuple[BrowserSecurityWitnessBundle, BrowserSecurityWitnessBundle]],
) -> dict[str, object]:
    if not isinstance(carriers, dict) or len(carriers) < 2:
        raise ValueError("browser-security pool comparison requires at least two carriers")

    comparisons: dict[str, dict[str, object]] = {}
    family_changes: dict[str, set[str]] = {}
    infrastructure_changes: dict[str, set[str]] = {}
    detector_drift_carriers: list[str] = []
    observation_invalid_carriers: dict[str, list[str]] = {}
    challenge_change_carriers: list[str] = []

    for carrier_id in sorted(carriers):
        _required_text(carrier_id, "carrierId")
        pair = carriers[carrier_id]
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError(
                f"carrier {carrier_id} must map to one baseline/candidate bundle tuple"
            )
        baseline, candidate = pair
        if not isinstance(baseline, BrowserSecurityWitnessBundle) or not isinstance(
            candidate, BrowserSecurityWitnessBundle
        ):
            raise ValueError(f"carrier {carrier_id} comparison values must be witness bundles")
        result = compare_browser_security_bundles(baseline, candidate)
        comparisons[carrier_id] = result
        family_changes[carrier_id] = set(result["changedFamilies"])
        infrastructure_changes[carrier_id] = {
            key for key, changed in result["infrastructureChanges"].items() if changed
        }
        detector_shape_drift = any(
            row["status"] in {"ADDED", "MISSING", "DETECTOR_DRIFT"} for row in result["detectors"]
        )
        if result["detectorDrift"] or detector_shape_drift:
            detector_drift_carriers.append(carrier_id)
        invalid_observations = result.get("invalidObservationDetectors")
        if isinstance(invalid_observations, list) and invalid_observations:
            observation_invalid_carriers[carrier_id] = list(invalid_observations)
        if result["challengeStandingChanged"]:
            challenge_change_carriers.append(carrier_id)

    carrier_ids = sorted(comparisons)
    if detector_drift_carriers:
        return {
            "schemaVersion": 1,
            "standing": "DETECTOR_DRIFT",
            "carrierIds": carrier_ids,
            "detectorDriftCarriers": detector_drift_carriers,
            "observationInvalidCarriers": observation_invalid_carriers,
            "subjectClassificationSuppressed": True,
            "sharedChangedFamilies": [],
            "carrierLocalChangedFamilies": {},
            "sharedInfrastructureChanges": [],
            "carrierLocalInfrastructureChanges": {},
            "challengeStandingChangedCarriers": challenge_change_carriers,
            "perCarrier": comparisons,
            "repairRoutes": [],
            "rootCauseEstablished": False,
        }

    if observation_invalid_carriers:
        return {
            "schemaVersion": 1,
            "standing": "OBSERVATION_INVALID",
            "carrierIds": carrier_ids,
            "detectorDriftCarriers": [],
            "observationInvalidCarriers": observation_invalid_carriers,
            "subjectClassificationSuppressed": True,
            "sharedChangedFamilies": [],
            "carrierLocalChangedFamilies": {},
            "sharedInfrastructureChanges": [],
            "carrierLocalInfrastructureChanges": {},
            "challengeStandingChangedCarriers": challenge_change_carriers,
            "perCarrier": comparisons,
            "repairRoutes": ["observation-validity"],
            "rootCauseEstablished": False,
        }

    shared_families = set.intersection(*(family_changes[carrier] for carrier in carrier_ids))
    shared_infrastructure = set.intersection(
        *(infrastructure_changes[carrier] for carrier in carrier_ids)
    )
    local_families = {
        carrier: sorted(family_changes[carrier] - shared_families)
        for carrier in carrier_ids
        if family_changes[carrier] - shared_families
    }
    local_infrastructure = {
        carrier: sorted(infrastructure_changes[carrier] - shared_infrastructure)
        for carrier in carrier_ids
        if infrastructure_changes[carrier] - shared_infrastructure
    }
    has_shared = bool(shared_families or shared_infrastructure)
    has_local = bool(local_families or local_infrastructure)
    if not has_shared and not has_local:
        standing = "NO_OBSERVED_DRIFT"
    elif has_shared and has_local:
        standing = "MIXED_DRIFT"
    elif has_shared:
        standing = "GLOBAL_DRIFT"
    else:
        standing = "CARRIER_LOCAL_DRIFT"

    all_changed_families = set(shared_families)
    for families in local_families.values():
        all_changed_families.update(families)

    return {
        "schemaVersion": 1,
        "standing": standing,
        "carrierIds": carrier_ids,
        "detectorDriftCarriers": [],
        "observationInvalidCarriers": {},
        "subjectClassificationSuppressed": False,
        "sharedChangedFamilies": sorted(shared_families),
        "carrierLocalChangedFamilies": local_families,
        "sharedInfrastructureChanges": sorted(shared_infrastructure),
        "carrierLocalInfrastructureChanges": local_infrastructure,
        "challengeStandingChangedCarriers": challenge_change_carriers,
        "perCarrier": comparisons,
        "repairRoutes": [REPAIR_ROUTES[family] for family in sorted(all_changed_families)],
        "rootCauseEstablished": False,
    }
