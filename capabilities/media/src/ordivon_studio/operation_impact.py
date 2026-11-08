"""Bounded, read-only Production operation dependency impact projection.

Like a Nix derivation/Bazel action declaration only in *shape*: this file never
constructs a complete action digest or grants a cache hit. Historical receipts
remain distinct from present file observations and from execution policy.
"""

from __future__ import annotations

import hashlib
import json
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .assets import hash_file

_KIND = "ordivon.media.operation-lineage"
_NAME = "operation-lineage.json"


def _read_production_file(root: Path, relative: str) -> Path:
    """No absolute paths, .., Windows separators or Production symlink escape."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("invalid operation lineage relative path")
    path = Path(relative)
    if (
        path.is_absolute()
        or ":" in path.parts[0]
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise ValueError(f"operation lineage path is not safely relative: {relative}")
    resolved_root = root.resolve()
    candidate = (resolved_root / path).resolve()
    if candidate == resolved_root or not candidate.is_relative_to(resolved_root):
        raise ValueError(f"operation lineage path escapes Production root: {relative}")
    return candidate


def _file_observation(root: Path, record: dict[str, str]) -> dict[str, Any]:
    path = _read_production_file(root, record["path"])
    expected = record["digest"]
    result: dict[str, Any] = {
        "path": record["path"],
        "declaredDigest": expected,
        "observedDigest": None,
        "relation": "UNKNOWN_FILE_UNAVAILABLE",
    }
    try:
        blob = hash_file(path)
    except OSError, ValueError:
        return result
    result["observedDigest"] = blob.digest
    result["relation"] = (
        "MATCHES_DECLARED_DIGEST" if blob.digest == expected else "DIFFERS_FROM_DECLARED_DIGEST"
    )
    return result


def _order(steps: list[dict[str, Any]]) -> list[str]:
    """Use Python's native graphlib, not a hand-rolled dependency walker."""
    by_id = {step["id"]: step for step in steps}
    if len(by_id) != len(steps):
        raise ValueError("operation lineage has duplicate step ids")
    graph: dict[str, list[str]] = {}
    for step_id in sorted(by_id):
        dependencies = by_id[step_id]["dependsOn"]
        if len(dependencies) != len(set(dependencies)):
            raise ValueError(f"operation lineage repeats a dependency: {step_id}")
        for dependency in dependencies:
            if dependency not in by_id:
                raise ValueError(f"operation lineage references unknown step: {dependency}")
        graph[step_id] = sorted(dependencies)
    try:
        return list(TopologicalSorter(graph).static_order())
    except CycleError as exc:
        raise ValueError(f"operation lineage has a dependency cycle: {exc}") from exc


def project_operation_impact(
    root: Path,
    production: dict[str, Any],
    byte_observations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Compare actual local bytes with declared snapshots, then close dependencies.

    A changed upstream input requires downstream *revalidation*, not necessarily
    recomputation. UNKNOWN propagates without becoming a false assertion.
    This is no action cache, scheduler, deterministic-execution proof or CAS.
    """
    source_documents = production.get("sources", {}).get("sourceDocuments", [])
    if _NAME not in source_documents:
        return None
    lineage_path = _read_production_file(root, _NAME)
    source_bytes = lineage_path.read_bytes()
    lineage = json.loads(source_bytes)
    schema = json.loads(
        (Path(__file__).resolve().parents[2] / "schemas/operation-lineage.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(lineage)
    if lineage["kind"] != _KIND or lineage["productionId"] != production["id"]:
        raise ValueError("operation lineage does not match selected Production identity")
    steps = lineage["operations"]
    ordered = _order(steps)
    by_id = {step["id"]: step for step in steps}
    declared_outputs = {row["id"]: row for row in production["outputs"]}
    observations = {row["outputId"]: row for row in byte_observations}
    owned_outputs: set[str] = set()
    results: dict[str, dict[str, Any]] = {}

    for step_id in ordered:
        step = by_id[step_id]
        output_ids = step["outputIds"]
        if not output_ids and "retainedFile" not in step:
            raise ValueError(f"operation lineage step has no declared output: {step_id}")
        for output_id in output_ids:
            if output_id not in declared_outputs:
                raise ValueError(f"operation lineage names unknown output: {output_id}")
            if output_id in owned_outputs:
                raise ValueError(f"operation lineage claims output twice: {output_id}")
            owned_outputs.add(output_id)
        observed_files = [_file_observation(root, record) for record in step["inputFiles"]]
        if "retainedFile" in step:
            observed_files.append(_file_observation(root, step["retainedFile"]))
        output_relations = [
            {"outputId": output_id, "relation": observations[output_id]["relation"]}
            for output_id in output_ids
        ]
        relations = [row["relation"] for row in (*observed_files, *output_relations)]
        if any(relation.startswith("INVALID_") for relation in relations):
            own_standing = "UNKNOWN_INVALID_BYTE_BINDING"
        elif any(relation.startswith("DIFFERS_") for relation in relations):
            own_standing = "BYTE_DRIFT_OBSERVED"
        elif any(relation.startswith("UNKNOWN_") for relation in relations):
            own_standing = "UNKNOWN_BYTE_EVIDENCE"
        else:
            own_standing = "MATCHES_DECLARED_BYTES"
        upstream = [results[dep]["impactStanding"] for dep in step["dependsOn"]]
        if own_standing == "BYTE_DRIFT_OBSERVED" or "REVALIDATE_REQUIRED" in upstream:
            impact = "REVALIDATE_REQUIRED"
        elif own_standing.startswith("UNKNOWN_") or "UNKNOWN_UPSTREAM" in upstream:
            impact = "UNKNOWN_UPSTREAM"
        else:
            impact = "NO_BYTE_DRIFT_OBSERVED"
        results[step_id] = {
            "stepId": step_id,
            "dependsOn": step["dependsOn"],
            "toolFamily": step["toolFamily"],
            "directByteStanding": own_standing,
            "impactStanding": impact,
            "fileObservations": observed_files,
            "outputObservations": output_relations,
            "actionKey": None,
            "cacheReuseAuthorized": False,
            "toolAndEnvironmentQualification": "UNKNOWN",
            "recipeQualification": "UNKNOWN",
        }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.operation-impact-projection",
        "productionId": production["id"],
        "sourceManifestSha256": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
        "truthRole": "bounded-point-in-time-local-dependency-observation",
        "actionCachePresent": False,
        "cacheReuseAuthorized": False,
        "executionOrPublicationAuthorized": False,
        "rule": (
            "Dependency impacts are revalidation candidates, not build/rebuild obligations. "
            "A matching byte cut is not an action cache hit; unknown inputs never imply unchanged."
        ),
        "steps": [results[step_id] for step_id in ordered],
        "revalidateStepIds": [
            step_id
            for step_id in ordered
            if results[step_id]["impactStanding"] == "REVALIDATE_REQUIRED"
        ],
        "unresolvedStepIds": [
            step_id
            for step_id in ordered
            if results[step_id]["impactStanding"] == "UNKNOWN_UPSTREAM"
        ],
    }
