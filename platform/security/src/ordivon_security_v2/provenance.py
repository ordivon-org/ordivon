from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from .attestations import STATEMENT_TYPE

SLSA_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"
LOCAL_BUILDER_ID = "https://ordivon.local/security-v2/builders/local-python-wheel/v1"
PYTHON_WHEEL_BUILD_TYPE = "https://ordivon.local/security-v2/build-types/uv-python-wheel/v1"


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build_provenance_statement(
    *,
    artifact: Path,
    source_uri: str,
    source_revision: str,
    invocation_id: str,
    started_on: str,
    finished_on: str,
    builder_versions: dict[str, str],
) -> dict[str, Any]:
    if len(source_revision) != 40 or any(c not in "0123456789abcdef" for c in source_revision):
        raise ValueError("source_revision must be a lowercase SHA-1 Git commit")
    return {
        "_type": STATEMENT_TYPE,
        "subject": [{"name": artifact.name, "digest": {"sha256": _sha256(artifact)}}],
        "predicateType": SLSA_PROVENANCE_PREDICATE,
        "predicate": {
            "buildDefinition": {
                "buildType": PYTHON_WHEEL_BUILD_TYPE,
                "externalParameters": {
                    "artifactKind": "python-wheel",
                    "pythonRequirement": ">=3.12,<3.13",
                },
                "resolvedDependencies": [
                    {"uri": source_uri, "digest": {"gitCommit": source_revision}}
                ],
            },
            "runDetails": {
                "builder": {"id": LOCAL_BUILDER_ID, "version": dict(builder_versions)},
                "metadata": {
                    "invocationId": invocation_id,
                    "startedOn": started_on,
                    "finishedOn": finished_on,
                },
            },
        },
    }


def verify_build_provenance(
    statement: dict[str, Any],
    *,
    artifact: Path,
    expected_source_revision: str,
    expected_builder_id: str = LOCAL_BUILDER_ID,
    expected_build_type: str = PYTHON_WHEEL_BUILD_TYPE,
) -> dict[str, Any]:
    if statement.get("_type") != STATEMENT_TYPE:
        raise ValueError("not an in-toto Statement v1")
    if statement.get("predicateType") != SLSA_PROVENANCE_PREDICATE:
        raise ValueError("not SLSA provenance v1")
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or len(subjects) != 1:
        raise ValueError("exactly one artifact subject is required")
    subject = subjects[0]
    if subject.get("name") != artifact.name:
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
        and dep.get("digest", {}).get("gitCommit") == expected_source_revision
    ]
    if len(source_matches) != 1:
        raise ValueError("exact source revision is not uniquely bound")

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
        "standing": "BUILD_PROVENANCE_VERIFIED",
        "artifact": artifact.name,
        "artifactSha256": "sha256:" + actual_sha,
        "sourceRevision": expected_source_revision,
        "builderId": expected_builder_id,
        "buildType": expected_build_type,
    }
