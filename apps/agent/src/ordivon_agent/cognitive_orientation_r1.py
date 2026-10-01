from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


class AgentOrientationViewError(ValueError):
    """An exact cognitive projection cannot be safely compacted for model orientation."""


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentOrientationViewError(f"{label} must be an object")
    return value


def _digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def project_agent_orientation_view(
    projection: Mapping[str, Any],
) -> dict[str, object]:
    """Compile one exact cognitive proof envelope into a compact model-visible orientation.

    This is progressive disclosure, not relevance ranking. It keeps the current objective,
    frontier, unresolved items, hard constraints, next actions, owner-currentness summaries,
    and exact expansion references while leaving full established history and owner attributes
    behind the exact projection/owner readbacks.
    """

    value = _mapping(projection, "Agent cognitive projection")
    if value.get("kind") != "ordivon.agent-cognitive-projection":
        raise AgentOrientationViewError("unsupported cognitive projection kind")
    if value.get("truthRole") != "derived-read-only-agent-cognitive-projection":
        raise AgentOrientationViewError("cognitive projection truth role differs")

    authority = _mapping(value.get("authority"), "cognitive projection authority")
    if any(
        authority.get(field) is not False
        for field in (
            "effectAuthority",
            "executionAuthority",
            "semanticAcceptanceAuthority",
            "domainTruthAuthority",
        )
    ):
        raise AgentOrientationViewError("orientation source projection carries authority")

    work = _mapping(value.get("work"), "cognitive projection Work")
    observations = value.get("ownerObservations")
    versions = value.get("versionVector")
    if not isinstance(observations, list) or not isinstance(versions, list):
        raise AgentOrientationViewError("projection owner observations/version vector are invalid")

    owner_currentness: list[dict[str, object]] = []
    expansion_refs: set[str] = {str(work["workRef"])}
    for observation in observations:
        item = _mapping(observation, "owner observation")
        owner_ref = item.get("ownerRef")
        subject_ref = item.get("subjectRef")
        standing = item.get("standing")
        observed_at = item.get("observedAt")
        if not all(
            isinstance(x, str) and x for x in (owner_ref, subject_ref, standing, observed_at)
        ):
            raise AgentOrientationViewError("owner observation summary fields are invalid")
        evidence_refs = item.get("evidenceRefs")
        if not isinstance(evidence_refs, list) or any(
            not isinstance(ref, str) or not ref for ref in evidence_refs
        ):
            raise AgentOrientationViewError("owner observation evidenceRefs are invalid")
        expansion_refs.add(subject_ref)
        expansion_refs.update(evidence_refs)
        owner_currentness.append(
            {
                "ownerRef": owner_ref,
                "subjectRef": subject_ref,
                "standing": standing,
                "observedAt": observed_at,
                "evidenceRefs": list(evidence_refs),
                "observationDigest": item.get("observationDigest"),
            }
        )

    owner_currentness.sort(key=lambda row: (str(row["ownerRef"]), str(row["subjectRef"])))

    reference_refs = work.get("referenceRefs")
    if not isinstance(reference_refs, list):
        raise AgentOrientationViewError("Work referenceRefs are invalid")
    expansion_refs.update(str(ref) for ref in reference_refs)

    established = work.get("established")
    if not isinstance(established, list):
        raise AgentOrientationViewError("Work established list is invalid")

    view = {
        "schemaVersion": 1,
        "kind": "ordivon.agent-orientation-view",
        "truthRole": "derived-read-only-model-orientation",
        "work": {
            "workRef": work["workRef"],
            "revision": work["revision"],
            "snapshotDigest": work["snapshotDigest"],
            "objective": work["objective"],
            "frontier": work["frontier"],
            "unresolved": list(work["unresolved"]),
            "constraints": list(work["constraints"]),
            "nextActions": list(work["nextActions"]),
            "establishedCount": len(established),
        },
        "ownerCurrentness": owner_currentness,
        "versionVector": list(versions),
        "expansionRefs": sorted(expansion_refs),
        "authority": {
            "effectAuthority": False,
            "executionAuthority": False,
            "semanticAcceptanceAuthority": False,
            "domainTruthAuthority": False,
        },
        "progressiveDisclosure": {
            "fullWorkEstablishedHistoryIncluded": False,
            "fullOwnerAttributesIncluded": False,
            "exactProjectionDigest": value.get("projectionDigest"),
        },
        "proofBoundary": (
            "This compact view is for first-orientation only. It intentionally omits full Work "
            "established history and owner-native attributes; exact refs/digests remain available "
            "for selective expansion. Omission is not evidence of irrelevance, and this view grants "
            "no execution, effect, acceptance, or domain authority."
        ),
    }
    view["viewDigest"] = _digest(view)
    return view


__all__ = [
    "AgentOrientationViewError",
    "project_agent_orientation_view",
]
