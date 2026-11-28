"""Cross-carrier aggregation of separately validated browser comparisons.

Pool classification cannot promote detector/observer failure to subject drift.
"""

from __future__ import annotations

from .browser_security_comparison import REPAIR_ROUTES, compare_browser_security_bundles
from .browser_security_witness import BrowserSecurityWitnessBundle, _required_text


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
