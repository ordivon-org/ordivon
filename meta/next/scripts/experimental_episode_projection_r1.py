"""Deterministic Runtime R5C → Episode R1 projection and structural validation.

This source-only adapter has no database, CLI, batch I/O, or Runtime authority.
All nonclaims and exact canonical digests remain identical to the original.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from ordivon_composition import canonical_digest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "experimental-episode-binding-r1.schema.json"

FORBIDDEN_OUTPUT_KEYS = {
    "workspace_snapshot",
    "execution_plan",
    "launch_token_digest",
    "raw_payload",
    "credential",
    "credentials",
    "api_key",
    "token",
    "cookie",
}


class EpisodeProjectionError(ValueError):
    pass


def _load_schema() -> dict[str, Any]:
    value = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EpisodeProjectionError("Episode schema root must be an object")
    return value


VALIDATOR = Draft202012Validator(_load_schema())


def _normalize_sha256(value: str | None, *, label: str) -> str | None:
    if value is None:
        return None
    body = value[7:] if value.startswith("sha256:") else value
    if len(body) != 64 or any(char not in "0123456789abcdef" for char in body):
        raise EpisodeProjectionError(f"{label} is not a lower-case SHA-256 identity")
    return f"sha256:{body}"


def _validate_no_forbidden_keys(value: Any, path: str = "<root>") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN_OUTPUT_KEYS:
                raise EpisodeProjectionError(
                    f"forbidden projected field at {path}/{key}"
                )
            _validate_no_forbidden_keys(item, f"{path}/{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_no_forbidden_keys(item, f"{path}/{index}")


def _without_projection_digest(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "projectionDigest"}


def validate_episode(value: dict[str, Any]) -> None:
    errors = sorted(
        VALIDATOR.iter_errors(value), key=lambda item: list(item.absolute_path)
    )
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        raise EpisodeProjectionError(
            f"episode schema violation at {location}: {error.message}"
        )
    _validate_no_forbidden_keys(value)
    _unique(value["evidenceBindings"], "kind", "evidence binding")
    _unique(value["dimensions"], "name", "dimension")
    _unique(value["measures"], "name", "measure")
    expected = canonical_digest(_without_projection_digest(value))
    if value["projectionDigest"] != expected:
        raise EpisodeProjectionError(
            "projectionDigest does not match the exact projected Episode bytes"
        )


def _unique(rows: list[dict[str, Any]], field: str, label: str) -> None:
    seen: set[Any] = set()
    for row in rows:
        value = row.get(field)
        if value in seen:
            raise EpisodeProjectionError(f"duplicate {label} {field}: {value}")
        seen.add(value)


def _event_projection(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": event["event_id"],
        "sequence": event["sequence"],
        "eventType": event["event_type"],
        "origin": event["origin"],
        "previousState": event.get("previous_state"),
        "newState": event.get("new_state"),
        "reasonCode": event["reason_code"],
        "dataDigest": _normalize_sha256(
            event["data_digest"], label=f"event {event['event_id']} data_digest"
        ),
        "observedAt": str(event["observed_at"]),
    }


def _artifact_projection(artifact: dict[str, Any]) -> dict[str, Any]:
    byte_length = int(artifact["byte_length"])
    if byte_length < 0:
        raise EpisodeProjectionError(
            f"artifact {artifact['artifact_id']} has negative byte_length"
        )
    return {
        "artifactId": artifact["artifact_id"],
        "kind": artifact["kind"],
        "relativePath": artifact["relative_path"],
        "digest": _normalize_sha256(
            artifact["digest"], label=f"artifact {artifact['artifact_id']} digest"
        ),
        "mediaType": artifact["media_type"],
        "byteLength": byte_length,
        "truncated": bool(artifact["truncated"]),
        "createdAt": str(artifact["created_at"]),
    }


def project_r5c_record(record: dict[str, Any]) -> dict[str, Any]:
    run = record.get("run")
    events = record.get("events")
    artifacts = record.get("artifacts")
    if (
        not isinstance(run, dict)
        or not isinstance(events, list)
        or not isinstance(artifacts, list)
    ):
        raise EpisodeProjectionError("R5C source record requires run/events/artifacts")

    execution_id = run["execution_id"]
    if not isinstance(execution_id, str) or not execution_id:
        raise EpisodeProjectionError("execution_id must be a non-empty string")

    _unique(events, "event_id", "event")
    _unique(events, "sequence", "event")
    _unique(artifacts, "artifact_id", "artifact")

    for event in events:
        if event.get("execution_id") != execution_id:
            raise EpisodeProjectionError(
                f"event {event.get('event_id')} binds another execution"
            )
    for artifact in artifacts:
        if artifact.get("execution_id") != execution_id:
            raise EpisodeProjectionError(
                f"artifact {artifact.get('artifact_id')} binds another execution"
            )

    projected_events = sorted(
        (_event_projection(event) for event in events), key=lambda row: row["sequence"]
    )
    projected_artifacts = sorted(
        (_artifact_projection(artifact) for artifact in artifacts),
        key=lambda row: (row["kind"], row["relativePath"], row["artifactId"]),
    )

    owner_refs: list[dict[str, Any]] = [
        {
            "ownerId": "runtime-historical-r5c",
            "objectKind": "legacy-attempt",
            "objectId": run["legacy_attempt_id"],
            "relation": "legacy-source-attempt",
        },
        {
            "ownerId": "runtime-historical-r5c",
            "objectKind": "workspace",
            "objectId": run["workspace_id"],
            "relation": "executed-in-workspace",
        },
        {
            "ownerId": "runtime-historical-r5c",
            "objectKind": "request",
            "objectId": run["request_digest"],
            "relation": "execution-request",
        },
        {
            "ownerId": "runtime-historical-r5c",
            "objectKind": "operation",
            "objectId": f"operation:{execution_id}",
            "relation": "execution-operation",
            "digest": _normalize_sha256(
                run["operation_digest"], label="operation_digest"
            ),
        },
        {
            "ownerId": "runtime-historical-r5c",
            "objectKind": "execution-plan",
            "objectId": f"execution-plan:{execution_id}",
            "relation": "planned-by",
            "digest": _normalize_sha256(
                run["execution_plan_digest"], label="execution_plan_digest"
            ),
        },
    ]

    optional_digest_refs = [
        ("bundle_digest", "execution-bundle", "materialized-from"),
        ("result_digest", "execution-result", "produced-result"),
        ("infrastructure_error_digest", "infrastructure-error", "observed-error"),
        ("recovery_evidence_digest", "recovery-evidence", "recovery-evidence"),
    ]
    for field, object_kind, relation in optional_digest_refs:
        digest = _normalize_sha256(run.get(field), label=field)
        if digest is not None:
            owner_refs.append(
                {
                    "ownerId": "runtime-historical-r5c",
                    "objectKind": object_kind,
                    "objectId": f"{object_kind}:{execution_id}",
                    "relation": relation,
                    "digest": digest,
                }
            )

    artifact_bytes = sum(row["byteLength"] for row in projected_artifacts)
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-episode-binding",
        "profileId": "runtime-r5c-v1",
        "episodeId": f"episode:runtime-r5c:{execution_id}",
        "dataClass": "EXPERIENCE",
        "anchor": {
            "ownerId": "runtime-historical-r5c",
            "objectKind": "execution",
            "objectId": execution_id,
            "sourceRecordDigest": canonical_digest(run),
        },
        "ownerRefs": owner_refs,
        "evidenceBindings": [
            {
                "kind": "runtime-events",
                "count": len(projected_events),
                "setDigest": canonical_digest(projected_events),
            },
            {
                "kind": "runtime-artifacts",
                "count": len(projected_artifacts),
                "setDigest": canonical_digest(projected_artifacts),
                "totalBytes": artifact_bytes,
                "truncatedCount": sum(
                    1 for row in projected_artifacts if row["truncated"]
                ),
            },
        ],
        "dimensions": [
            {"name": "runtime.desired_state", "value": run["desired_state"]},
            {"name": "runtime.execution_state", "value": run["execution_state"]},
            {"name": "runtime.resolution", "value": run.get("resolution")},
            {"name": "runtime.termination_intent", "value": run["termination_intent"]},
            {
                "name": "runtime.recovery_required",
                "value": run.get("recovery_required"),
            },
        ],
        "measures": [
            {
                "name": "runtime.event_rows",
                "value": len(projected_events),
                "unit": "rows",
            },
            {
                "name": "runtime.artifact_rows",
                "value": len(projected_artifacts),
                "unit": "rows",
            },
            {
                "name": "runtime.artifact_bytes",
                "value": artifact_bytes,
                "unit": "bytes",
            },
        ],
        "evidenceSets": {
            "events": {
                "count": len(projected_events),
                "setDigest": canonical_digest(projected_events),
            },
            "artifacts": {
                "count": len(projected_artifacts),
                "setDigest": canonical_digest(projected_artifacts),
                "totalBytes": artifact_bytes,
                "truncatedCount": sum(
                    1 for row in projected_artifacts if row["truncated"]
                ),
            },
        },
        "executionObservation": {
            "desiredState": run["desired_state"],
            "executionState": run["execution_state"],
            "resolution": run.get("resolution"),
            "terminationIntent": run["termination_intent"],
            "createdAt": str(run["created_at"]),
            "startedAt": None
            if run.get("started_at") is None
            else str(run["started_at"]),
            "finishedAt": (
                None if run.get("finished_at") is None else str(run["finished_at"])
            ),
            "recoveryRequired": run.get("recovery_required"),
        },
        "costObservations": {"artifactBytes": artifact_bytes},
        "unresolved": [
            "Historical R5C does not expose model/token/human-cost observations.",
            "This projection does not establish semantic task success beyond Runtime resolution.",
        ],
        "nonClaims": [
            "Episode is not Runtime execution truth.",
            "Episode does not reproduce raw workspace snapshots, execution plans, event payloads or artifact bytes.",
            "Runtime resolution is not domain acceptance.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    validate_episode(result)
    return result
