#!/usr/bin/env python3
"""Projection-only Agent views over Social Work Fabric owner-native reads.

This compiler deliberately does not read PostgreSQL, mutate Host, infer authority from
participation, rank attention, schedule work, or perform effects. The caller must first
obtain exact Host owner reads and any explicit natural-owner authority bindings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
BUNDLE_KIND = "ordivon.social-work-fabric-owner-bundle-r1"
VIEW_KINDS = {
    "current": "ordivon.social-work-fabric-current-view-r1",
    "attention": "ordivon.social-work-fabric-attention-view-r1",
    "coordination": "ordivon.social-work-fabric-coordination-view-r1",
    "authority": "ordivon.social-work-fabric-authority-view-r1",
}
FORBIDDEN_CONTROL_FIELDS = {
    "priority",
    "rank",
    "score",
    "weight",
    "voteCount",
    "winner",
    "winnerSelected",
    "allow",
    "deny",
    "authorized",
    "authorizationGranted",
}


class ProjectionError(ValueError):
    pass


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectionError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProjectionError(f"{label} must be a list")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProjectionError(f"{label} must be a non-empty string")
    return value


def _assert_no_control_fields(value: Any, label: str = "input") -> None:
    if isinstance(value, dict):
        bad = sorted(FORBIDDEN_CONTROL_FIELDS & set(value))
        if bad:
            raise ProjectionError(f"{label} contains forbidden control fields: {bad}")
        for key, item in value.items():
            _assert_no_control_fields(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_control_fields(item, f"{label}[{index}]")


def validate_bundle(bundle: dict[str, Any]) -> None:
    if (
        bundle.get("schemaVersion") != SCHEMA_VERSION
        or bundle.get("kind") != BUNDLE_KIND
    ):
        raise ProjectionError("unsupported Social Work Fabric owner bundle")
    works = _list(bundle.get("works"), "works")
    spaces = _list(bundle.get("spaces"), "spaces")
    relations = _list(bundle.get("workRelations"), "workRelations")
    intents = _list(bundle.get("coordinationIntents"), "coordinationIntents")
    bindings = _list(bundle.get("authorityBindings"), "authorityBindings")
    attention = _obj(bundle.get("attention"), "attention")
    if attention.get("kind") != "ordivon.host-attention-delta-r1":
        raise ProjectionError(
            "attention must be Host Social Work Fabric attention delta"
        )
    if attention.get("rankingApplied") is not False:
        raise ProjectionError("attention source must remain unranked")
    seen_work: set[str] = set()
    for index, raw in enumerate(works):
        row = _obj(raw, f"works[{index}]")
        work_ref = _text(row.get("workRef"), f"works[{index}].workRef")
        if row.get("kind") != "ordivon.host-work":
            raise ProjectionError(f"works[{index}] has unexpected kind")
        if work_ref in seen_work:
            raise ProjectionError(f"duplicate workRef: {work_ref}")
        seen_work.add(work_ref)
        if not isinstance(row.get("revision"), int) or row["revision"] < 1:
            raise ProjectionError(f"works[{index}].revision must be positive")
        _obj(row.get("snapshot"), f"works[{index}].snapshot")
    seen_space: set[str] = set()
    for index, raw in enumerate(spaces):
        row = _obj(raw, f"spaces[{index}]")
        space_ref = _text(row.get("spaceRef"), f"spaces[{index}].spaceRef")
        if row.get("kind") != "ordivon.host-space":
            raise ProjectionError(f"spaces[{index}] has unexpected kind")
        if space_ref in seen_space:
            raise ProjectionError(f"duplicate spaceRef: {space_ref}")
        seen_space.add(space_ref)
        _list(row.get("participants"), f"spaces[{index}].participants")
        _list(row.get("topics"), f"spaces[{index}].topics")
        _list(row.get("subjectRefs"), f"spaces[{index}].subjectRefs")
    for index, raw in enumerate(relations):
        row = _obj(raw, f"workRelations[{index}]")
        if row.get("relation") not in {
            "parent_of",
            "depends_on",
            "blocks",
            "relates_to",
        }:
            raise ProjectionError(f"workRelations[{index}] has unknown relation")
        _text(row.get("sourceWorkRef"), f"workRelations[{index}].sourceWorkRef")
        _text(row.get("targetWorkRef"), f"workRelations[{index}].targetWorkRef")
    for index, raw in enumerate(intents):
        row = _obj(raw, f"coordinationIntents[{index}]")
        if row.get("kind") != "ordivon.host-coordination-intent":
            raise ProjectionError(f"coordinationIntents[{index}] has unexpected kind")
        _text(row.get("intentRef"), f"coordinationIntents[{index}].intentRef")
        _text(row.get("actorRef"), f"coordinationIntents[{index}].actorRef")
        _text(row.get("subjectRef"), f"coordinationIntents[{index}].subjectRef")
        if row.get("standing") not in {"active", "released"}:
            raise ProjectionError(f"coordinationIntents[{index}] has invalid standing")
    for index, raw in enumerate(bindings):
        row = _obj(raw, f"authorityBindings[{index}]")
        _text(row.get("subjectRef"), f"authorityBindings[{index}].subjectRef")
        _text(row.get("relation"), f"authorityBindings[{index}].relation")
        _text(row.get("principalRef"), f"authorityBindings[{index}].principalRef")
        _text(row.get("sourceRef"), f"authorityBindings[{index}].sourceRef")
    _assert_no_control_fields(bundle)


def _base(bundle: dict[str, Any], view: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": VIEW_KINDS[view],
        "truthRole": "rebuildable-agent-projection-not-owner-authority",
        "view": view.upper(),
        "ownerBundleDigest": canonical_digest(bundle),
    }


def compile_current(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    result = _base(bundle, "current")
    works = []
    for row in bundle["works"]:
        works.append(
            {
                "workRef": row["workRef"],
                "workKind": row.get("workKind"),
                "state": row.get("state"),
                "revision": row["revision"],
                "snapshotDigest": row.get("snapshotDigest"),
                "frontier": row["snapshot"].get("frontier"),
                "unresolvedCount": len(row["snapshot"].get("unresolved", [])),
            }
        )
    spaces = []
    for row in bundle["spaces"]:
        spaces.append(
            {
                "spaceRef": row["spaceRef"],
                "subjectRefs": sorted(row.get("subjectRefs", [])),
                "participantCount": len(row.get("participants", [])),
                "topicCount": len(row.get("topics", [])),
            }
        )
    result["works"] = sorted(works, key=lambda row: row["workRef"])
    result["spaces"] = sorted(spaces, key=lambda row: row["spaceRef"])
    result["workRelations"] = sorted(
        bundle["workRelations"],
        key=lambda row: (row["sourceWorkRef"], row["relation"], row["targetWorkRef"]),
    )
    result["nonClaims"] = [
        "CURRENT preserves Host Work/Social records and does not promote them to Runtime, Git, or domain truth.",
        "A WorkSnapshot is a semantic continuity claim, not proof of physical execution or domain completion.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def compile_attention(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    source = bundle["attention"]
    result = _base(bundle, "attention")
    events = _list(source.get("events"), "attention.events")
    result["actorRef"] = source.get("actorRef")
    result["afterSequence"] = source.get("afterSequence")
    result["snapshotHighSequence"] = source.get("snapshotHighSequence")
    result["events"] = events
    result["hasMore"] = source.get("hasMore")
    result["nextAfterSequence"] = source.get("nextAfterSequence")
    result["rankingApplied"] = False
    result["nonClaims"] = [
        "ATTENTION is actor-scoped change navigation and does not rank, prioritize, assign, or suppress work.",
        "Explicit history re-entry remains work.get/topic.resume rather than replaying all history through Inbox.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def compile_coordination(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    result = _base(bundle, "coordination")
    active_intents = [
        row for row in bundle["coordinationIntents"] if row.get("standing") == "active"
    ]
    by_subject: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in active_intents:
        by_subject[row["subjectRef"]].append(
            {
                "intentRef": row["intentRef"],
                "actorRef": row["actorRef"],
                "operation": row.get("operation"),
                "workRef": row.get("workRef"),
                "spaceRef": row.get("spaceRef"),
                "expiresAtMs": row.get("expiresAtMs"),
            }
        )
    result["spaces"] = [
        {
            "spaceRef": row["spaceRef"],
            "subjectRefs": sorted(row.get("subjectRefs", [])),
            "participants": sorted(
                (
                    {
                        "actorRef": p.get("actorRef"),
                        "standing": p.get("standing"),
                    }
                    for p in row.get("participants", [])
                    if isinstance(p, dict)
                ),
                key=lambda p: (str(p["actorRef"]), str(p["standing"])),
            ),
            "topics": sorted(
                (
                    {"topicRef": t.get("topicRef"), "state": t.get("state")}
                    for t in row.get("topics", [])
                    if isinstance(t, dict)
                ),
                key=lambda t: str(t["topicRef"]),
            ),
        }
        for row in sorted(bundle["spaces"], key=lambda row: row["spaceRef"])
    ]
    result["activeIntentsBySubject"] = [
        {
            "subjectRef": subject_ref,
            "intents": sorted(rows, key=lambda row: row["intentRef"]),
            "simultaneousIntentCount": len(rows),
        }
        for subject_ref, rows in sorted(by_subject.items())
    ]
    result["nonClaims"] = [
        "Multiple same-subject intents expose coordination pressure but do not imply conflict, lock, lease, assignment, or winner.",
        "Participation exposes social presence only and cannot mint ownership, identity, authorization, or EffectAuthority.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def compile_authority(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    result = _base(bundle, "authority")
    bindings = sorted(
        bundle["authorityBindings"],
        key=lambda row: (
            row["subjectRef"],
            row["relation"],
            row["principalRef"],
            row["sourceRef"],
        ),
    )
    result["bindings"] = bindings
    result["bindingCount"] = len(bindings)
    result["inferredFromParticipants"] = False
    result["inferredFromIntentActors"] = False
    result["authorizationDecisionIncluded"] = False
    result["nonClaims"] = [
        "AUTHORITY contains explicit owner/verifier/effect-owner locators only.",
        "Actor participation, message authorship, Work creation, and CoordinationIntent never infer authority.",
        "Bindings are navigation coordinates; authentication, authorization, and effects remain with natural owners.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def compile_view(bundle: dict[str, Any], view: str) -> dict[str, Any]:
    if view == "current":
        result = compile_current(bundle)
    elif view == "attention":
        result = compile_attention(bundle)
    elif view == "coordination":
        result = compile_coordination(bundle)
    elif view == "authority":
        result = compile_authority(bundle)
    else:
        raise ProjectionError(f"unsupported view: {view}")
    _assert_no_control_fields(result, "view")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("view", choices=tuple(VIEW_KINDS))
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        bundle = _obj(
            json.loads(args.bundle.read_text(encoding="utf-8")), str(args.bundle)
        )
        result = compile_view(bundle, args.view)
    except (OSError, json.JSONDecodeError, ProjectionError) as exc:
        raise SystemExit(f"Social Work Fabric projection failed: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
