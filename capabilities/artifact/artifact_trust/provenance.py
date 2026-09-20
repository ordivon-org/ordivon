from __future__ import annotations

import datetime as dt
import json
import urllib.parse
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact, sha256_file

IN_TOTO_STATEMENT_V1 = "https://in-toto.io/Statement/v1"
SLSA_PROVENANCE_V1 = "https://slsa.dev/provenance/v1"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


def _require_uri(value: str, field: str) -> str:
    if not urllib.parse.urlparse(value).scheme:
        raise RuntimeError(f"{field} must be a URI")
    return value


def slsa_statement(
    subjects: Iterable[Path],
    materials: Iterable[Path],
    profile_path: Path,
    builder_id: str,
    build_type: str,
    *,
    invocation_id: str | None = None,
) -> dict[str, Any]:
    builder_id = _require_uri(builder_id, "builder-id")
    build_type = _require_uri(build_type, "build-type")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    subject_values = [{"name": path.name, "digest": {"sha256": sha256_file(path)}} for path in subjects]
    dependencies = [
        {"uri": path.resolve().as_uri(), "digest": {"sha256": sha256_file(path)}}
        for path in materials
    ]
    dependencies.append({"uri": profile_path.resolve().as_uri(), "digest": {"sha256": sha256_file(profile_path)}})
    return {
        "_type": IN_TOTO_STATEMENT_V1,
        "subject": subject_values,
        "predicateType": SLSA_PROVENANCE_V1,
        "predicate": {
            "buildDefinition": {
                "buildType": build_type,
                "externalParameters": {"deliveryProfile": profile.get("id")},
                "internalParameters": {},
                "resolvedDependencies": dependencies,
            },
            "runDetails": {
                "builder": {"id": builder_id},
                "metadata": {"invocationId": invocation_id or f"artifact-build-{utc_now()}"},
                "byproducts": [],
            },
        },
    }


def verify_release_provenance(provenance_path: Path, subjects: Iterable[Path]) -> dict[str, Any]:
    failures: list[str] = []
    value = json.loads(provenance_path.read_text(encoding="utf-8"))
    expected = {path.name: sha256_file(path) for path in subjects}
    if value.get("_type") != IN_TOTO_STATEMENT_V1:
        failures.append("provenance is not an in-toto Statement v1")
    if value.get("predicateType") != SLSA_PROVENANCE_V1:
        failures.append("provenance predicateType is not SLSA Provenance v1")
    observed: dict[str, str] = {}
    for item in value.get("subject", []) if isinstance(value.get("subject"), list) else []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            digest = item.get("digest", {}).get("sha256") if isinstance(item.get("digest"), dict) else None
            if isinstance(digest, str):
                observed[item["name"]] = digest
    if observed != expected:
        failures.append("provenance subjects do not exactly bind the release primary/companions")
    builder = value.get("predicate", {}).get("runDetails", {}).get("builder", {}).get("id")
    if not isinstance(builder, str) or not urllib.parse.urlparse(builder).scheme:
        failures.append("provenance builder.id is absent or not a URI")
    return {
        "status": "PASS" if not failures else "FAIL",
        "statement": file_fact(provenance_path),
        "expectedSubjects": expected,
        "observedSubjects": observed,
        "builderId": builder,
        "failures": failures,
    }
