from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


class AgentCognitiveProjectionError(ValueError):
    """Exact owner projections cannot be safely composed into one cognitive view."""


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentCognitiveProjectionError(f"{label} must be an object")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise AgentCognitiveProjectionError(f"{label} must be a non-empty trimmed string")
    return value


def _positive_int(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise AgentCognitiveProjectionError(f"{label} must be a positive integer")
    return value


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise AgentCognitiveProjectionError(f"{label} must be a list")
    if any(not isinstance(item, str) or not item or item != item.strip() for item in value):
        raise AgentCognitiveProjectionError(f"{label} must contain non-empty trimmed strings")
    if len(value) != len(set(value)):
        raise AgentCognitiveProjectionError(f"{label} must not contain duplicates")
    return list(value)


def _canonical_digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _work_projection(work_value: Mapping[str, Any]) -> tuple[dict[str, object], dict[str, object]]:
    work = _mapping(work_value, "Host Work")
    work_ref = _text(work.get("workRef"), "Host WorkRef")
    revision = _positive_int(work.get("revision"), "Host Work revision")
    snapshot_digest = _text(work.get("snapshotDigest"), "Host Work snapshot digest")
    if not snapshot_digest.startswith("sha256:"):
        raise AgentCognitiveProjectionError("Host Work snapshot digest must be sha256-prefixed")

    snapshot = _mapping(work.get("snapshot"), "Host Work snapshot")
    objective = _text(snapshot.get("objective"), "Host Work objective")
    frontier = _text(snapshot.get("frontier"), "Host Work frontier")
    established = _string_list(snapshot.get("established", []), "Host Work established")
    unresolved = _string_list(snapshot.get("unresolved", []), "Host Work unresolved")
    constraints = _string_list(snapshot.get("constraints", []), "Host Work constraints")
    next_actions = _string_list(snapshot.get("nextActions", []), "Host Work nextActions")
    reference_refs = _string_list(snapshot.get("referenceRefs", []), "Host Work referenceRefs")

    projection = {
        "workRef": work_ref,
        "revision": revision,
        "snapshotDigest": snapshot_digest,
        "objective": objective,
        "frontier": frontier,
        "established": established,
        "unresolved": unresolved,
        "constraints": constraints,
        "nextActions": next_actions,
        "referenceRefs": reference_refs,
        "truthBoundary": (
            "Host Work is semantic continuity only. Snapshot prose is not automatically "
            "present-tense Git/Runtime/provider/domain truth."
        ),
    }
    version = {
        "ownerRef": "ordivon.host",
        "subjectRef": work_ref,
        "versionKind": "work-revision",
        "version": str(revision),
        "digest": snapshot_digest,
    }
    return projection, version


def _owner_observation_projection(
    value: Mapping[str, Any],
) -> tuple[dict[str, object], dict[str, object]]:
    observation = _mapping(value, "Living owner observation")
    if observation.get("kind") != "ordivon.living-owner-observation":
        raise AgentCognitiveProjectionError("unsupported owner observation kind")

    subject_ref = _text(observation.get("subjectRef"), "observation subjectRef")
    owner_ref = _text(observation.get("ownerRef"), "observation ownerRef")
    observed_at = _text(observation.get("observedAt"), "observation observedAt")
    operation = _text(observation.get("operation"), "observation operation")
    standing = _text(observation.get("standing"), "observation standing")
    evidence_refs = _string_list(observation.get("evidenceRefs"), "observation evidenceRefs")
    attributes = _mapping(observation.get("attributes"), "observation attributes")
    truth_boundary = _text(observation.get("truthBoundary"), "observation truthBoundary")

    source_revision = observation.get("sourceRevision")
    if source_revision is not None:
        source_revision = _text(source_revision, "observation sourceRevision")
    source_digest = observation.get("sourceDigest")
    if source_digest is not None:
        source_digest = _text(source_digest, "observation sourceDigest")
        if not source_digest.startswith("sha256:"):
            raise AgentCognitiveProjectionError(
                "observation sourceDigest must be sha256-prefixed when supplied"
            )

    exact = {
        "schemaVersion": observation.get("schemaVersion"),
        "kind": observation.get("kind"),
        "subjectRef": subject_ref,
        "ownerRef": owner_ref,
        "observedAt": observed_at,
        "operation": operation,
        "standing": standing,
        "evidenceRefs": evidence_refs,
        "attributes": dict(attributes),
        "sourceRevision": source_revision,
        "sourceDigest": source_digest,
        "truthBoundary": truth_boundary,
    }
    digest = _canonical_digest(exact)
    projection = {
        **exact,
        "observationDigest": digest,
    }
    version = {
        "ownerRef": owner_ref,
        "subjectRef": subject_ref,
        "versionKind": "owner-observation",
        "version": digest,
        "observedAt": observed_at,
        "sourceRevision": source_revision,
        "sourceDigest": source_digest,
    }
    return projection, version


def _run_projection(value: Mapping[str, Any]) -> tuple[dict[str, object], dict[str, object]]:
    run = _mapping(value, "Agent Run view")
    if run.get("kind") != "ordivon.agent-run-view":
        raise AgentCognitiveProjectionError("unsupported Agent Run view kind")
    if run.get("truthRole") != "derived-read-only-product-projection":
        raise AgentCognitiveProjectionError("Agent Run view truth role differs")

    harness_run_id = _text(run.get("harnessRunId"), "Harness Run identity")
    revision = _positive_int(run.get("revision"), "Harness Run revision")
    contract_digest = _text(run.get("contractDigest"), "Harness Run contract digest")

    semantic_acceptance = _mapping(run.get("semanticAcceptance"), "Agent Run semanticAcceptance")
    if semantic_acceptance.get("establishedByHarness") is not False:
        raise AgentCognitiveProjectionError(
            "Agent Run view must not claim Harness-established semantic acceptance"
        )

    projection = dict(run)
    version = {
        "ownerRef": "ordivon.harness",
        "subjectRef": f"harness:run:{harness_run_id}",
        "versionKind": "harness-run-revision",
        "version": str(revision),
        "digest": contract_digest,
    }
    return projection, version


def _reentry_projection(value: Mapping[str, Any]) -> dict[str, object]:
    reentry = _mapping(value, "cross-owner re-entry projection")
    if reentry.get("kind") != "ordivon.agent-cross-owner-reentry-projection":
        raise AgentCognitiveProjectionError("unsupported cross-owner re-entry kind")
    if reentry.get("truthRole") != "derived-read-only-cross-owner-navigation-projection":
        raise AgentCognitiveProjectionError("cross-owner re-entry truth role differs")

    continuation = _mapping(reentry.get("continuation"), "re-entry continuation")
    if continuation.get("effectRedispatchAllowed") is not False:
        raise AgentCognitiveProjectionError(
            "cross-owner re-entry must never authorize effect redispatch"
        )
    if reentry.get("physicalRevalidationRequired") is not True:
        raise AgentCognitiveProjectionError(
            "cross-owner re-entry must require physical revalidation"
        )
    return dict(reentry)


def project_agent_cognitive_environment(
    host_work: Mapping[str, Any],
    *,
    owner_observations: Sequence[Mapping[str, Any]] = (),
    agent_run_view: Mapping[str, Any] | None = None,
    cross_owner_reentry: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Compose exact owner projections into one bounded non-authoritative Agent view.

    This function performs no owner reads, discovery, ranking, relevance inference,
    authorization, execution, persistence, or semantic acceptance. All inputs must have
    already crossed their natural owner boundaries.
    """

    work_projection, work_version = _work_projection(host_work)

    observations: list[dict[str, object]] = []
    versions: list[dict[str, object]] = [work_version]
    seen_observation_keys: set[tuple[str, str]] = set()
    for raw in owner_observations:
        projection, version = _owner_observation_projection(raw)
        key = (str(projection["ownerRef"]), str(projection["subjectRef"]))
        if key in seen_observation_keys:
            raise AgentCognitiveProjectionError(
                "owner observations must contain at most one current observation per owner/subject"
            )
        seen_observation_keys.add(key)
        observations.append(projection)
        versions.append(version)

    run_projection = None
    if agent_run_view is not None:
        run_projection, run_version = _run_projection(agent_run_view)
        versions.append(run_version)

    reentry_projection = None
    if cross_owner_reentry is not None:
        reentry_projection = _reentry_projection(cross_owner_reentry)
        reentry_work = _mapping(reentry_projection.get("work"), "re-entry Work")
        if reentry_work.get("workRef") != work_projection["workRef"]:
            raise AgentCognitiveProjectionError(
                "cross-owner re-entry belongs to a different Host Work"
            )

    versions.sort(
        key=lambda item: (
            str(item["ownerRef"]),
            str(item["subjectRef"]),
            str(item["versionKind"]),
        )
    )

    projection = {
        "schemaVersion": 1,
        "kind": "ordivon.agent-cognitive-projection",
        "truthRole": "derived-read-only-agent-cognitive-projection",
        "work": work_projection,
        "ownerObservations": observations,
        "agentRun": run_projection,
        "reentry": reentry_projection,
        "versionVector": versions,
        "authority": {
            "effectAuthority": False,
            "executionAuthority": False,
            "semanticAcceptanceAuthority": False,
            "domainTruthAuthority": False,
        },
        "currentness": {
            "presentTenseClaimsRequireOwnerReadback": True,
            "missingOwnerObservationMeansUnknown": True,
        },
        "proofBoundary": (
            "This projection composes exact owner outputs for model cognition only. It stores "
            "no new truth, performs no owner read, does not rank relevance, and cannot authorize "
            "execution, effect redispatch, semantic acceptance, or domain claims."
        ),
    }
    projection["projectionDigest"] = _canonical_digest(projection)
    return projection


__all__ = [
    "AgentCognitiveProjectionError",
    "project_agent_cognitive_environment",
]
