#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "profiles/research/scholarly-intelligence/scholarly-intelligence-profile-v1.schema.json"
PROFILES = tuple(sorted((STUDY / "profiles").glob("*-live-r1.json")))
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
    cp = subprocess.run(args, capture_output=True, check=False)
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
        Draft202012Validator(schema).iter_errors(profile), key=lambda e: list(e.path)
    )
    if errors:
        detail = "; ".join(
            f"{'.'.join(map(str, e.path)) or '$'}: {e.message}" for e in errors
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
    dirty = run_text("git", "-C", str(repo), "status", "--porcelain")
    if dirty:
        fail(
            f"{path.name}: Study authority is dirty and live projection would omit bytes"
        )
    run_bytes("git", "-C", str(repo), "cat-file", "-e", revision + "^{commit}")
    ancestry = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", revision, head],
        capture_output=True,
        check=False,
    )
    if ancestry.returncode != 0:
        fail(
            f"{path.name}: bound revision {revision} is not an ancestor of current HEAD {head}"
        )

    ids: set[str] = set()
    verified_refs = 0
    located_refs: set[str] = set()
    for items in profile["semanticRefs"].values():
        for item in items:
            item_id = item["id"]
            if item_id in ids:
                fail(f"{path.name}: duplicate semantic id {item_id}")
            ids.add(item_id)
            location = item.get("location")
            declared = item.get("digest")
            if location is None:
                continue
            located_refs.add(location)
            if not declared:
                fail(f"{path.name}: located ref {item_id} lacks digest")
            bound_bytes = run_bytes(
                "git", "-C", str(repo), "show", f"{revision}:{location}"
            )
            if digest_bytes(bound_bytes) != declared:
                fail(f"{path.name}: bound-revision digest mismatch for {item_id}")
            current_path = repo / location
            if not current_path.is_file():
                fail(f"{path.name}: current file missing for {item_id}: {location}")
            if digest_bytes(current_path.read_bytes()) != declared:
                fail(f"{path.name}: current-file digest drift for {item_id}")
            verified_refs += 1

    subject = authority.get("subjectRef")
    if subject:
        if subject not in located_refs:
            fail(
                f"{path.name}: subjectRef is not covered by a digest-bound semantic ref"
            )
        current_subject = repo / subject
        if not current_subject.is_file():
            fail(f"{path.name}: current subjectRef missing")

    if verified_refs < 1:
        fail(f"{path.name}: live profile must bind at least one exact ref")

    for axis, value in profile["stateAxes"].items():
        if not value.get("owner") or not value.get("state"):
            fail(f"{path.name}: incomplete state axis {axis}")
        for evidence_ref in value.get("evidenceRefs", []):
            if evidence_ref not in ids:
                fail(
                    f"{path.name}: state axis {axis} references unknown semantic id {evidence_ref}"
                )

    return {
        "profileId": profile["profileId"],
        "studyOwner": authority["owner"],
        "sourceRepo": str(repo),
        "boundRevision": revision,
        "currentHeadRevision": head,
        "revisionRelation": "BOUND_REVISION_ANCESTOR_CURRENT_BOUND_BYTES_EXACT",
        "semanticRefCount": len(ids),
        "digestVerifiedRefCount": verified_refs,
        "stateAxisCount": len(profile["stateAxes"]),
        "standing": "PASS_EXACT_LIVE_PROFILE_R3",
    }


def validate_portable_profile(schema: dict[str, Any], path: Path) -> dict[str, Any]:
    profile = load(path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(profile), key=lambda e: list(e.path)
    )
    if errors:
        detail = "; ".join(
            f"{'.'.join(map(str, e.path)) or '$'}: {e.message}" for e in errors
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
    revision = authority.get("sourceRevision")
    if not isinstance(revision, str) or len(revision) != 40:
        fail(f"{path.name}: sourceRevision must be exact 40-hex")
    try:
        int(revision, 16)
    except ValueError as exc:
        raise SystemExit(f"{path.name}: sourceRevision is not hexadecimal") from exc
    if not authority.get("owner") or not authority.get("sourceRepo"):
        fail(f"{path.name}: Study authority owner/sourceRepo missing")

    ids: set[str] = set()
    located_refs = 0
    for items in profile["semanticRefs"].values():
        for item in items:
            item_id = item["id"]
            if item_id in ids:
                fail(f"{path.name}: duplicate semantic id {item_id}")
            ids.add(item_id)
            location = item.get("location")
            if location is None:
                continue
            located_refs += 1
            digest = item.get("digest")
            if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest) != 71:
                fail(f"{path.name}: located ref {item_id} lacks exact sha256 digest")
    if located_refs < 1:
        fail(f"{path.name}: portable profile must declare at least one digest-bound ref")
    for axis, value in profile["stateAxes"].items():
        if not value.get("owner") or not value.get("state"):
            fail(f"{path.name}: incomplete state axis {axis}")
        for evidence_ref in value.get("evidenceRefs", []):
            if evidence_ref not in ids:
                fail(f"{path.name}: state axis {axis} references unknown semantic id {evidence_ref}")

    return {
        "profileId": profile["profileId"],
        "studyOwner": authority["owner"],
        "sourceRepo": authority["sourceRepo"],
        "boundRevision": revision,
        "semanticRefCount": len(ids),
        "declaredDigestBoundRefCount": located_refs,
        "stateAxisCount": len(profile["stateAxes"]),
        "standing": "PASS_PORTABLE_PROFILE_SHAPE_R3",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--portable",
        action="store_true",
        help="validate committed profile structure without claiming external repository currentness",
    )
    args = parser.parse_args()

    schema = load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    if len(PROFILES) < 3:
        fail("expected at least three live Study profiles")
    if args.portable:
        results = [validate_portable_profile(schema, path) for path in PROFILES]
        standing = "PASS_PORTABLE_PROFILE_SHAPES_R3"
        currentness_rule = "external repository currentness is intentionally not evaluated in portable repository CI"
        truth_boundary = (
            "Portable R3 verifies committed profile schema, authority identifiers, semantic-reference closure, and declared digest shape only. "
            "It does not claim that external Study repositories are present, clean, current, or byte-identical; run this verifier without --portable for that live evidence."
        )
    else:
        results = [validate_profile(schema, path) for path in PROFILES]
        standing = "PASS_EXACT_LIVE_PROFILES_R3"
        currentness_rule = "bound revision must be an ancestor of current clean HEAD and every bound current byte must retain its declared digest"
        truth_boundary = (
            "R3 proves current digest-bound Study projections without equating repository HEAD movement with Study semantic movement. "
            "It does not establish scientific truth, review correctness, venue acceptance, or submission authority."
        )
    output = {
        "schemaVersion": 3,
        "kind": "ordivon.research.scholarly-intelligence-live-profile-acceptance",
        "standing": standing,
        "currentnessRule": currentness_rule,
        "profileCount": len(results),
        "distinctStudyOwners": len({r["studyOwner"] for r in results}),
        "distinctSourceRepos": len({r["sourceRepo"] for r in results}),
        "profiles": results,
        "truthBoundary": truth_boundary,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
