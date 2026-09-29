#!/usr/bin/env python3
"""Task-local Evaluation Boundary R1 extraction for Experimental Episode RW6."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.cross_domain_binding_r3 import resolve_repo_file

NEXT_ROOT = Path(__file__).resolve().parents[1]
BINDING_SCHEMA = NEXT_ROOT / "schemas" / "evaluation-boundary-binding-r1.schema.json"
PROFILE_SCHEMA = NEXT_ROOT / "schemas" / "evaluation-boundary-profile-r1.schema.json"
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class EvaluationBoundaryError(ValueError):
    """Fail-closed task-local evaluation-boundary error."""


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvaluationBoundaryError(f"{path}: root must be an object")
    return value


def _validate(value: dict[str, Any], schema_path: Path, label: str) -> None:
    schema = _load_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: [str(part) for part in item.absolute_path],
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise EvaluationBoundaryError(
            f"{label} schema violation at {location}: {first.message}"
        )


def validate_binding(value: dict[str, Any]) -> None:
    _validate(value, BINDING_SCHEMA, "evaluation-boundary binding")


def validate_profile(value: dict[str, Any]) -> None:
    _validate(value, PROFILE_SCHEMA, "evaluation-boundary profile")


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _json_pointer(value: Any, pointer: str) -> Any:
    current = value
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            try:
                current = current[int(token)]
            except (ValueError, IndexError) as exc:
                raise EvaluationBoundaryError(
                    f"invalid JSON pointer {pointer}"
                ) from exc
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise EvaluationBoundaryError(f"missing JSON pointer {pointer}")
    return current


def _verify_source(repo_root: Path, source: dict[str, Any]) -> str:
    path = resolve_repo_file(repo_root, source["repoRelativePath"])
    observed_digest = _digest(path)
    if observed_digest != source["sha256"]:
        raise EvaluationBoundaryError(
            f"source digest mismatch for role={source['role']}: "
            f"expected={source['sha256']} observed={observed_digest}"
        )

    if source["mediaType"] == "text/markdown":
        text = path.read_text(encoding="utf-8")
        for fragment in source.get("requiredTextFragments", []):
            if fragment not in text:
                raise EvaluationBoundaryError(
                    f"missing required owner text fragment for role={source['role']}"
                )
    elif source["mediaType"] == "application/json":
        value = _load_json(path)
        for assertion in source.get("jsonAssertions", []):
            observed = _json_pointer(value, assertion["pointer"])
            if assertion["operator"] == "equals":
                if observed != assertion["expected"]:
                    raise EvaluationBoundaryError(
                        f"JSON assertion failed at {assertion['pointer']}: "
                        f"expected={assertion['expected']!r} observed={observed!r}"
                    )
            elif assertion["operator"] == "sha256":
                if not isinstance(observed, str) or _SHA256.fullmatch(observed) is None:
                    raise EvaluationBoundaryError(
                        f"expected SHA-256 identity at {assertion['pointer']}"
                    )
            else:  # schema already prevents this; retain fail-closed runtime semantics.
                raise EvaluationBoundaryError(
                    f"unknown assertion operator {assertion['operator']}"
                )
    else:
        raise EvaluationBoundaryError(f"unsupported media type {source['mediaType']}")

    return observed_digest


def compile_profile(repo_root: Path, binding: dict[str, Any]) -> dict[str, Any]:
    validate_binding(binding)
    donors: list[dict[str, Any]] = []
    owners: set[str] = set()
    for donor in binding["donors"]:
        owners.add(donor["ownerId"])
        source_digests = [
            _verify_source(repo_root, source) for source in donor["sources"]
        ]
        donors.append(
            {
                "donorId": donor["donorId"],
                "ownerId": donor["ownerId"],
                "standing": donor["standing"],
                "sourceDigests": source_digests,
            }
        )

    executed = any(item["standing"] == "EXECUTED" for item in donors)
    if len(owners) < 2:
        raise EvaluationBoundaryError(
            "at least two distinct natural owners are required"
        )
    if not executed:
        raise EvaluationBoundaryError("at least one executed donor is required")

    profile = {
        "schemaVersion": 1,
        "kind": "ordivon.evaluation-boundary-profile-r1",
        "profileId": "experimental-episode-rw6-media-game-r1",
        "truthRole": "task-local-non-authoritative-evaluation-boundary",
        "laws": {
            "exactSourceIdentityRequired": True,
            "freezePrecedesHoldoutExposure": True,
            "postExposureMutationPreservesStanding": False,
            "thresholdRetuningAfterUnblindingAllowed": False,
            "holdoutEvidenceSeparateFromDevelopmentEvidence": True,
            "evaluatorSemanticsRemainOwnerNative": True,
        },
        "donors": donors,
        "closure": {
            "distinctOwnerCount": len(owners),
            "executedDonorPresent": executed,
            "mechanicalClosure": True,
            "empiricalClosure": all(item["standing"] == "EXECUTED" for item in donors),
        },
        "nonClaims": binding["nonClaims"],
    }
    validate_profile(profile)
    return profile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    profile = compile_profile(args.repo_root, _load_json(args.binding))
    payload = json.dumps(profile, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
