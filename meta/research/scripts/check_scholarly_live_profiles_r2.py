#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

META = Path(__file__).resolve().parents[2]
SCHEMA = META / "research/schemas/scholarly-intelligence-profile-v1.schema.json"
PROFILES = tuple(sorted((META / "research/profiles").glob("*-live-r1.json")))
EXPECTED_AXES = {
    "requirements",
    "evidence",
    "inference",
    "claims",
    "argument",
    "venue",
    "review",
    "publication",
    "learning",
}
EXPECTED_REF_ROLES = {"requirements", "claims", "evidence", "concerns", "resolutions"}
FORBIDDEN_TOP_LEVEL = {
    "manuscript",
    "dataset",
    "scores",
    "modelFits",
    "reviewText",
    "decision",
    "acceptanceProbability",
    "experimentAuthorized",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected object: {path}")
    return value


def run_bytes(*args: str) -> bytes:
    cp = subprocess.run(args, capture_output=True)
    if cp.returncode:
        fail(
            f"command failed ({cp.returncode}): {' '.join(args)}\n"
            + cp.stderr.decode("utf-8", errors="replace")
        )
    return cp.stdout


def run_text(*args: str) -> str:
    return run_bytes(*args).decode("utf-8").strip()


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def validate_profile(schema: dict[str, Any], path: Path) -> dict[str, Any]:
    profile = load(path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(profile),
        key=lambda error: list(error.path),
    )
    if errors:
        detail = "; ".join(
            f"{'.'.join(map(str, error.path)) or '$'}: {error.message}"
            for error in errors
        )
        fail(f"{path.name}: schema validation failed: {detail}")

    if profile.get("truthRole") != "non-authoritative-study-projection":
        fail(f"{path.name}: authority laundering risk")
    leaked = FORBIDDEN_TOP_LEVEL.intersection(profile)
    if leaked:
        fail(f"{path.name}: Study payload leaked: {sorted(leaked)}")
    if set(profile.get("stateAxes", {})) != EXPECTED_AXES:
        fail(f"{path.name}: state axes drifted")
    if set(profile.get("semanticRefs", {})) != EXPECTED_REF_ROLES:
        fail(f"{path.name}: semantic ref roles drifted")

    authority = profile["studyAuthority"]
    repo = Path(authority["sourceRepo"])
    revision = authority["sourceRevision"]
    head = run_text("git", "-C", str(repo), "rev-parse", "HEAD")
    if head != revision:
        fail(f"{path.name}: bound revision {revision} != current HEAD {head}")
    dirty = run_text("git", "-C", str(repo), "status", "--porcelain")
    if dirty:
        fail(f"{path.name}: Study authority is dirty and live projection would omit bytes")
    run_bytes("git", "-C", str(repo), "cat-file", "-e", revision + "^{commit}")

    subject = authority.get("subjectRef")
    if subject:
        run_bytes("git", "-C", str(repo), "cat-file", "-e", f"{revision}:{subject}")

    ids: set[str] = set()
    verified_refs = 0
    for role, items in profile["semanticRefs"].items():
        for item in items:
            item_id = item["id"]
            if item_id in ids:
                fail(f"{path.name}: duplicate semantic id {item_id}")
            ids.add(item_id)
            location = item.get("location")
            declared = item.get("digest")
            if location is None:
                continue
            if not declared:
                fail(f"{path.name}: located ref {item_id} lacks digest")
            committed = run_bytes("git", "-C", str(repo), "show", f"{revision}:{location}")
            if digest_bytes(committed) != declared:
                fail(f"{path.name}: committed digest mismatch for {item_id}")
            current_path = repo / location
            if not current_path.is_file():
                fail(f"{path.name}: current file missing for {item_id}: {location}")
            if digest_bytes(current_path.read_bytes()) != declared:
                fail(f"{path.name}: current-file digest mismatch for {item_id}")
            verified_refs += 1

    for axis, value in profile["stateAxes"].items():
        if not value.get("owner") or not value.get("state"):
            fail(f"{path.name}: incomplete state axis {axis}")
        for evidence_ref in value.get("evidenceRefs", []):
            if evidence_ref not in ids:
                fail(
                    f"{path.name}: state axis {axis} references unknown semantic id "
                    f"{evidence_ref}"
                )

    return {
        "profileId": profile["profileId"],
        "studyOwner": authority["owner"],
        "sourceRepo": str(repo),
        "sourceRevision": revision,
        "semanticRefCount": len(ids),
        "digestVerifiedRefCount": verified_refs,
        "stateAxisCount": len(profile["stateAxes"]),
        "standing": "PASS_EXACT_LIVE_PROFILE",
    }


def main() -> int:
    schema = load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    if len(PROFILES) < 3:
        fail("expected at least three live Study profiles")
    results = [validate_profile(schema, path) for path in PROFILES]
    output = {
        "schemaVersion": 1,
        "kind": "ordivon.research.scholarly-intelligence-live-profile-acceptance",
        "standing": "PASS_EXACT_LIVE_PROFILES",
        "profileCount": len(results),
        "distinctStudyOwners": len({row["studyOwner"] for row in results}),
        "distinctSourceRepos": len({row["sourceRepo"] for row in results}),
        "profiles": results,
        "truthBoundary": (
            "This proves exact current Study/revision/ref bindings for the shared projection. "
            "It does not establish scientific truth, venue acceptance, review correctness, "
            "or submission authority."
        ),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
