from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from .attestations import STATEMENT_TYPE

SLSA_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_build_provenance(
    statement: dict[str, Any],
    *,
    artifact: Path,
    expected_source_revision: str,
    expected_builder_id: str,
    expected_build_type: str,
    expected_source_uri: str | None = None,
) -> dict[str, Any]:
    """Verify statement content, NOT an issuer's identity or signed attestation."""
    if not expected_builder_id or not expected_build_type:
        raise ValueError("expected builder and build type must be independently provided")
    if len(expected_source_revision) not in (40, 64) or any(
        char not in "0123456789abcdef" for char in expected_source_revision
    ):
        raise ValueError("expected source revision must be a full lowercase Git digest")
    if statement.get("_type") != STATEMENT_TYPE:
        raise ValueError("not an in-toto Statement v1")
    if statement.get("predicateType") != SLSA_PROVENANCE_PREDICATE:
        raise ValueError("not SLSA provenance v1")
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or len(subjects) != 1:
        raise ValueError("exactly one artifact subject is required")
    subject = subjects[0]
    if not isinstance(subject, dict) or subject.get("name") != artifact.name:
        raise ValueError("artifact subject name mismatch")
    actual_sha = _sha256(artifact)
    if subject.get("digest") != {"sha256": actual_sha}:
        raise ValueError("artifact digest mismatch")
    predicate = statement.get("predicate")
    if not isinstance(predicate, dict):
        raise ValueError("missing provenance predicate")
    definition = predicate.get("buildDefinition")
    details = predicate.get("runDetails")
    if not isinstance(definition, dict) or not isinstance(details, dict):
        raise ValueError("buildDefinition and runDetails are required")
    if definition.get("buildType") != expected_build_type:
        raise ValueError("buildType mismatch")
    dependencies = definition.get("resolvedDependencies")
    if not isinstance(dependencies, list):
        raise ValueError("resolvedDependencies are required")
    source_matches = [
        dep
        for dep in dependencies
        if isinstance(dep, dict)
        and isinstance(dep.get("digest"), dict)
        and dep["digest"].get("gitCommit") == expected_source_revision
        and (expected_source_uri is None or dep.get("uri") == expected_source_uri)
    ]
    if len(source_matches) != 1:
        raise ValueError("exact source revision/URI is not uniquely bound")
    builder = details.get("builder")
    if not isinstance(builder, dict) or builder.get("id") != expected_builder_id:
        raise ValueError("builder identity mismatch")
    metadata = details.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("build metadata is required")
    for field in ("invocationId", "startedOn", "finishedOn"):
        if not isinstance(metadata.get(field), str) or not metadata[field]:
            raise ValueError(f"build metadata {field} is required")
    return {
        "standing": "PROVENANCE_CONTENT_BOUND",
        "artifact": artifact.name,
        "artifactSha256": "sha256:" + actual_sha,
        "sourceRevision": expected_source_revision,
        "builderId": expected_builder_id,
        "buildType": expected_build_type,
        "authenticated": False,
    }
