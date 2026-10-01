from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class AgentCognitiveDeltaError(ValueError):
    """Two derived cognitive projections cannot be compared safely."""


def _projection(value: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    if value.get("kind") != "ordivon.agent-cognitive-projection":
        raise AgentCognitiveDeltaError(f"{label} is not an Agent cognitive projection")
    if value.get("truthRole") != "derived-read-only-agent-cognitive-projection":
        raise AgentCognitiveDeltaError(f"{label} truth role differs")
    return value


def _version_key(value: Mapping[str, Any]) -> tuple[str, str, str]:
    try:
        owner = value["ownerRef"]
        subject = value["subjectRef"]
        kind = value["versionKind"]
    except KeyError as error:
        raise AgentCognitiveDeltaError("version vector component is incomplete") from error
    if not all(isinstance(item, str) and item for item in (owner, subject, kind)):
        raise AgentCognitiveDeltaError("version vector key fields must be non-empty strings")
    return owner, subject, kind


def _version_value(value: Mapping[str, Any]) -> str:
    version = value.get("version")
    if not isinstance(version, str) or not version:
        raise AgentCognitiveDeltaError("version vector component version is invalid")
    return version


def _index(value: Mapping[str, Any]) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    raw = value.get("versionVector")
    if not isinstance(raw, list):
        raise AgentCognitiveDeltaError("projection versionVector must be a list")
    indexed: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise AgentCognitiveDeltaError("version vector component must be an object")
        key = _version_key(item)
        if key in indexed:
            raise AgentCognitiveDeltaError("version vector contains duplicate owner/subject/kind")
        indexed[key] = item
    return indexed


def _slice_for(key: tuple[str, str, str]) -> str:
    owner, subject, kind = key
    if owner == "ordivon.host" and kind == "work-revision":
        return "work-semantic-continuity"
    if owner == "ordivon.harness" and kind == "harness-run-revision":
        return "agent-run-cognition"
    return f"owner-observation:{owner}:{subject}"


def project_agent_cognitive_delta(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> dict[str, object]:
    """Compare two exact derived projections without inventing a global clock.

    The result says only which owner-qualified components changed. It deliberately does not
    infer causal/domain impact, execution authority, or whether a changed component matters
    to some objective beyond the already-selected projection.
    """

    before = _projection(previous, "previous projection")
    after = _projection(current, "current projection")

    before_work = before.get("work")
    after_work = after.get("work")
    if not isinstance(before_work, Mapping) or not isinstance(after_work, Mapping):
        raise AgentCognitiveDeltaError("projection Work binding is missing")
    if before_work.get("workRef") != after_work.get("workRef"):
        raise AgentCognitiveDeltaError("cognitive delta requires one stable Host Work identity")

    before_index = _index(before)
    after_index = _index(after)

    rows: list[dict[str, object]] = []
    invalidated_slices: set[str] = set()

    for key in sorted(set(before_index) | set(after_index)):
        old = before_index.get(key)
        new = after_index.get(key)
        if old is None:
            disposition = "added"
        elif new is None:
            disposition = "removed"
        elif _version_value(old) != _version_value(new):
            disposition = "changed"
        else:
            continue

        owner, subject, kind = key
        slice_ref = _slice_for(key)
        invalidated_slices.add(slice_ref)
        rows.append(
            {
                "ownerRef": owner,
                "subjectRef": subject,
                "versionKind": kind,
                "disposition": disposition,
                "previousVersion": None if old is None else _version_value(old),
                "currentVersion": None if new is None else _version_value(new),
                "projectionSlice": slice_ref,
            }
        )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.agent-cognitive-delta",
        "truthRole": "derived-read-only-owner-version-delta",
        "workRef": before_work["workRef"],
        "previousProjectionDigest": before.get("projectionDigest"),
        "currentProjectionDigest": after.get("projectionDigest"),
        "changedComponents": rows,
        "invalidatedProjectionSlices": sorted(invalidated_slices),
        "hasChanges": bool(rows),
        "fullRediscoveryRequired": False,
        "authority": {
            "effectAuthority": False,
            "executionAuthority": False,
            "semanticImpactAuthority": False,
        },
        "proofBoundary": (
            "This delta compares owner-qualified projection versions only. It does not infer "
            "causal/domain impact, rank importance, authorize effects, or replace owner-native "
            "delta/invalidation logic such as Living Recursive LEGO View."
        ),
    }


__all__ = [
    "AgentCognitiveDeltaError",
    "project_agent_cognitive_delta",
]
