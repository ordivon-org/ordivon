from __future__ import annotations

import json
from collections.abc import Iterable
from hashlib import sha256
from typing import Any

CURRENTNESS_STANDINGS = {
    "CURRENT_DECLARED",
    "POINT_IN_TIME_OBSERVED",
    "HISTORICAL_NOT_CURRENT",
    "CURRENTNESS_UNKNOWN",
}
ADMISSIBLE_CURRENTNESS = {"CURRENT_DECLARED", "POINT_IN_TIME_OBSERVED"}
SOURCE_KINDS = {
    "direct-owner-observation",
    "client-effective-surface",
    "retained-projection",
}
REACHABILITY_STANDINGS = {"REACHABLE", "UNREACHABLE", "UNKNOWN"}


class SubjectExposureError(ValueError):
    """Raised when a DWC subject/exposure projection is mechanically invalid."""


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SubjectExposureError(f"{label} must be a non-empty string")
    return value


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _normalize_common(observation: dict[str, Any], *, label: str) -> dict[str, Any]:
    observation_id = _require_string(observation.get("id"), f"{label}.id")
    owner_id = _require_string(observation.get("ownerId"), f"{label}.ownerId")
    source_ref = _require_string(observation.get("sourceRef"), f"{label}.sourceRef")
    source_kind = _require_string(observation.get("sourceKind"), f"{label}.sourceKind")
    if source_kind not in SOURCE_KINDS:
        raise SubjectExposureError(
            f"{label}.sourceKind must be one of {sorted(SOURCE_KINDS)}"
        )

    currentness = _require_string(
        observation.get("currentnessStanding"),
        f"{label}.currentnessStanding",
    )
    if currentness not in CURRENTNESS_STANDINGS:
        raise SubjectExposureError(
            f"{label}.currentnessStanding must be one of "
            f"{sorted(CURRENTNESS_STANDINGS)}"
        )

    observed_at = observation.get("observedAt")
    if observed_at is not None:
        observed_at = _require_string(observed_at, f"{label}.observedAt")

    evidence_refs = observation.get("evidenceRefs", [])
    if not isinstance(evidence_refs, list):
        raise SubjectExposureError(f"{label}.evidenceRefs must be an array")
    normalized_evidence = sorted(
        {
            _require_string(item, f"{label}.evidenceRefs item")
            for item in evidence_refs
        }
    )

    normalized = {
        "id": observation_id,
        "ownerId": owner_id,
        "sourceRef": source_ref,
        "sourceKind": source_kind,
        "currentnessStanding": currentness,
        "observedAt": observed_at,
        "evidenceRefs": normalized_evidence,
    }
    normalized["observationDigest"] = _canonical_digest(normalized)
    return normalized


def _normalize_identity(observation: dict[str, Any]) -> dict[str, Any]:
    common = _normalize_common(observation, label="identity observation")
    dimension = _require_string(
        observation.get("dimension"),
        "identity observation.dimension",
    )
    identity_ref = observation.get("identityRef")
    if not isinstance(identity_ref, dict):
        raise SubjectExposureError("identity observation.identityRef must be an object")
    scheme = _require_string(identity_ref.get("scheme"), "identityRef.scheme")
    value = _require_string(identity_ref.get("value"), "identityRef.value")

    result = {
        **common,
        "dimension": dimension,
        "identityRef": {"scheme": scheme, "value": value},
    }
    result["observationDigest"] = _canonical_digest(
        {key: value for key, value in result.items() if key != "observationDigest"}
    )
    return result


def _normalize_exposure(observation: dict[str, Any]) -> dict[str, Any]:
    common = _normalize_common(observation, label="exposure observation")
    surface_id = _require_string(
        observation.get("surfaceId"),
        "exposure observation.surfaceId",
    )
    endpoint_ref = _require_string(
        observation.get("endpointRef"),
        "exposure observation.endpointRef",
    )
    origin_scope = _require_string(
        observation.get("originScope"),
        "exposure observation.originScope",
    )
    reachability = _require_string(
        observation.get("reachability"),
        "exposure observation.reachability",
    )
    if reachability not in REACHABILITY_STANDINGS:
        raise SubjectExposureError(
            "exposure observation.reachability must be one of "
            f"{sorted(REACHABILITY_STANDINGS)}"
        )

    transport = observation.get("transport")
    if transport is not None:
        transport = _require_string(transport, "exposure observation.transport")

    result = {
        **common,
        "surfaceId": surface_id,
        "endpointRef": endpoint_ref,
        "originScope": origin_scope,
        "transport": transport,
        "reachability": reachability,
    }
    result["observationDigest"] = _canonical_digest(
        {key: value for key, value in result.items() if key != "observationDigest"}
    )
    return result


def _coverage_standing(
    *,
    required_ids: Iterable[str],
    observations_by_key: dict[str, list[dict[str, Any]]],
) -> tuple[str, dict[str, str]]:
    per_key: dict[str, str] = {}
    for key in sorted(required_ids):
        observations = observations_by_key.get(key, [])
        if not observations:
            per_key[key] = "MISSING"
            continue
        standings = {item["currentnessStanding"] for item in observations}
        if standings & ADMISSIBLE_CURRENTNESS:
            per_key[key] = "OBSERVED"
        elif "CURRENTNESS_UNKNOWN" in standings:
            per_key[key] = "CURRENTNESS_UNKNOWN"
        else:
            per_key[key] = "HISTORICAL_ONLY"

    values = set(per_key.values())
    if "MISSING" in values:
        return "INCOMPLETE", per_key
    if "CURRENTNESS_UNKNOWN" in values:
        return "CURRENTNESS_UNKNOWN", per_key
    if "HISTORICAL_ONLY" in values:
        return "HISTORICAL_ONLY", per_key
    return "COMPLETE", per_key


def _horizon_standing(
    observations: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    horizons = [
        {
            "observationId": item["id"],
            "ownerId": item["ownerId"],
            "sourceRef": item["sourceRef"],
            "sourceKind": item["sourceKind"],
            "currentnessStanding": item["currentnessStanding"],
            "observedAt": item["observedAt"],
        }
        for item in observations
    ]
    horizons.sort(key=lambda item: item["observationId"])

    if not observations:
        return "NO_OBSERVATIONS", horizons

    standings = {item["currentnessStanding"] for item in observations}
    if "HISTORICAL_NOT_CURRENT" in standings:
        return "STALE_PRESENT", horizons
    if "CURRENTNESS_UNKNOWN" in standings:
        return "CURRENTNESS_UNKNOWN", horizons

    shapes = {
        (item["sourceKind"], item["currentnessStanding"], item["observedAt"])
        for item in observations
    }
    if len(shapes) > 1:
        return "MIXED_HORIZON", horizons
    return "COHERENT_HORIZON", horizons


def build_subject_exposure_snapshot(
    *,
    case_ref: str,
    epoch_ref: str,
    subject_ref: str,
    identity_observations: Iterable[dict[str, Any]],
    exposure_observations: Iterable[dict[str, Any]],
    required_identity_dimensions: Iterable[str],
    expected_exposure_surfaces: Iterable[str],
    non_claims: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a task-local, digest-bound DWC subject/exposure projection.

    This function does not discover assets, decide vulnerability applicability, mint
    owner currentness, or infer global exposure from missing observations.
    """

    case_ref = _require_string(case_ref, "case_ref")
    epoch_ref = _require_string(epoch_ref, "epoch_ref")
    subject_ref = _require_string(subject_ref, "subject_ref")

    required_dimensions = sorted(
        {
            _require_string(item, "required_identity_dimensions item")
            for item in required_identity_dimensions
        }
    )
    expected_surfaces = sorted(
        {
            _require_string(item, "expected_exposure_surfaces item")
            for item in expected_exposure_surfaces
        }
    )
    normalized_non_claims = sorted(
        {_require_string(item, "non_claims item") for item in non_claims}
    )

    identities = [_normalize_identity(dict(item)) for item in identity_observations]
    exposures = [_normalize_exposure(dict(item)) for item in exposure_observations]
    all_observations = [*identities, *exposures]

    observation_ids = [item["id"] for item in all_observations]
    if len(observation_ids) != len(set(observation_ids)):
        raise SubjectExposureError("observation ids must be unique across the snapshot")

    identities.sort(key=lambda item: item["id"])
    exposures.sort(key=lambda item: item["id"])

    identities_by_dimension: dict[str, list[dict[str, Any]]] = {}
    for item in identities:
        identities_by_dimension.setdefault(item["dimension"], []).append(item)

    exposures_by_surface: dict[str, list[dict[str, Any]]] = {}
    for item in exposures:
        exposures_by_surface.setdefault(item["surfaceId"], []).append(item)

    identity_coverage, identity_dimensions = _coverage_standing(
        required_ids=required_dimensions,
        observations_by_key=identities_by_dimension,
    )
    exposure_coverage, exposure_surfaces = _coverage_standing(
        required_ids=expected_surfaces,
        observations_by_key=exposures_by_surface,
    )

    horizon_standing, source_horizons = _horizon_standing(all_observations)

    reachable_surfaces = sorted(
        {
            item["surfaceId"]
            for item in exposures
            if item["currentnessStanding"] in ADMISSIBLE_CURRENTNESS
            and item["reachability"] == "REACHABLE"
        }
    )
    unreachable_surfaces = sorted(
        {
            item["surfaceId"]
            for item in exposures
            if item["currentnessStanding"] in ADMISSIBLE_CURRENTNESS
            and item["reachability"] == "UNREACHABLE"
        }
    )
    unknown_reachability_surfaces = sorted(
        {
            item["surfaceId"]
            for item in exposures
            if item["reachability"] == "UNKNOWN"
            or item["currentnessStanding"] == "CURRENTNESS_UNKNOWN"
        }
    )

    mechanical_standing = "COMPLETE"
    for standing in (identity_coverage, exposure_coverage):
        if standing == "INCOMPLETE":
            mechanical_standing = "INCOMPLETE"
            break
        if standing == "CURRENTNESS_UNKNOWN":
            mechanical_standing = "CURRENTNESS_UNKNOWN"
        elif standing == "HISTORICAL_ONLY" and mechanical_standing != "CURRENTNESS_UNKNOWN":
            mechanical_standing = "HISTORICAL_ONLY"

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-subject-exposure-snapshot",
        "caseRef": case_ref,
        "epochRef": epoch_ref,
        "subjectRef": subject_ref,
        "requiredIdentityDimensions": required_dimensions,
        "expectedExposureSurfaces": expected_surfaces,
        "identityObservations": identities,
        "exposureObservations": exposures,
        "identityCoverageStanding": identity_coverage,
        "identityDimensionStanding": identity_dimensions,
        "exposureCoverageStanding": exposure_coverage,
        "exposureSurfaceStanding": exposure_surfaces,
        "observationHorizonStanding": horizon_standing,
        "sourceHorizons": source_horizons,
        "reachableSurfaceIds": reachable_surfaces,
        "unreachableSurfaceIds": unreachable_surfaces,
        "unknownReachabilitySurfaceIds": unknown_reachability_surfaces,
        "mechanicalBindingStanding": mechanical_standing,
        "inputObservationDigests": sorted(
            item["observationDigest"] for item in all_observations
        ),
        "nonClaims": normalized_non_claims,
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "This is a task-local projection over caller-supplied owner observations. "
            "It does not discover a global asset inventory, mint owner currentness, "
            "infer vulnerability applicability, infer global non-exposure from an "
            "UNREACHABLE or missing observation, authorize effects, or establish "
            "domain/security acceptance."
        ),
    }
    snapshot_digest = _canonical_digest(result)
    result["snapshotDigest"] = snapshot_digest
    result["evidenceRef"] = f"dwc-subject-exposure:{snapshot_digest}"
    return result


def build_subject_exposure_snapshot_from_dict(value: dict[str, Any]) -> dict[str, Any]:
    return build_subject_exposure_snapshot(
        case_ref=value["caseRef"],
        epoch_ref=value["epochRef"],
        subject_ref=value["subjectRef"],
        identity_observations=value.get("identityObservations", []),
        exposure_observations=value.get("exposureObservations", []),
        required_identity_dimensions=value.get("requiredIdentityDimensions", []),
        expected_exposure_surfaces=value.get("expectedExposureSurfaces", []),
        non_claims=value.get("nonClaims", []),
    )
