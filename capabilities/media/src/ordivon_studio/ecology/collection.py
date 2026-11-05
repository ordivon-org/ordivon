"""Collection membership and ordering as source-revision-bound curation."""

from __future__ import annotations

import re
from collections.abc import Mapping

from .contracts import _canonical_digest, _integer, _string

COLLECTION_TRUTH_ROLE = "curation-relation-not-member-truth"



def validate_collection(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a small Media curation relation without minting member truth."""

    allowed = {
        "schemaVersion",
        "kind",
        "id",
        "title",
        "publishedAtMs",
        "curatorLabel",
        "curatorialBoundary",
        "members",
        "truthRole",
    }
    if set(value) != allowed:
        raise ValueError("collection fields differ from the v1 profile")
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.media.collection":
        raise ValueError("collection identity differs")
    if value.get("truthRole") != COLLECTION_TRUTH_ROLE:
        raise ValueError("collection truthRole differs")
    collection_id = _string(value.get("id"), "id")
    if not collection_id.startswith("collection:"):
        raise ValueError("collection id must start with collection:")
    _string(value.get("title"), "title")
    _integer(value.get("publishedAtMs"), "publishedAtMs")
    _string(value.get("curatorLabel"), "curatorLabel")
    _string(value.get("curatorialBoundary"), "curatorialBoundary")
    raw_members = value.get("members")
    if not isinstance(raw_members, list) or not raw_members:
        raise ValueError("collection members must be a non-empty list")

    member_ids: set[str] = set()
    normalized_members: list[dict[str, object]] = []
    member_fields = {
        "memberId",
        "title",
        "sourceOwner",
        "sourceIdentity",
        "sourceRevision",
        "sourceObjects",
        "note",
    }
    for raw in raw_members:
        if not isinstance(raw, Mapping) or set(raw) != member_fields:
            raise ValueError("collection member fields differ from the v1 profile")
        member_id = _string(raw.get("memberId"), "memberId")
        if member_id in member_ids:
            raise ValueError("collection memberId values must be unique")
        member_ids.add(member_id)
        source_revision = _string(raw.get("sourceRevision"), "sourceRevision")
        if source_revision.startswith("turn"):
            raise ValueError("ephemeral conversation citation cannot be a collection source revision")
        source_objects = raw.get("sourceObjects")
        if not isinstance(source_objects, list) or not source_objects:
            raise ValueError("sourceObjects must be a non-empty list")
        normalized_objects: list[dict[str, str]] = []
        seen_paths: set[str] = set()
        for source_object in source_objects:
            if not isinstance(source_object, Mapping) or set(source_object) != {"path", "digest"}:
                raise ValueError("sourceObjects entries must contain exactly path and digest")
            source_path = _string(source_object.get("path"), "sourceObjects.path")
            source_digest = _string(source_object.get("digest"), "sourceObjects.digest")
            if source_path in seen_paths:
                raise ValueError("sourceObjects paths must be unique within one member")
            seen_paths.add(source_path)
            if re.fullmatch(r"sha256:[0-9a-f]{64}", source_digest) is None:
                raise ValueError("sourceObjects.digest must be one canonical lowercase sha256 digest")
            normalized_objects.append({"path": source_path, "digest": source_digest})
        note = raw.get("note")
        if note is not None:
            _string(note, "note", allow_empty=False)
        normalized_members.append(
            {
                "memberId": member_id,
                "title": _string(raw.get("title"), "title"),
                "sourceOwner": _string(raw.get("sourceOwner"), "sourceOwner"),
                "sourceIdentity": _string(raw.get("sourceIdentity"), "sourceIdentity"),
                "sourceRevision": source_revision,
                "sourceObjects": normalized_objects,
                "note": note,
            }
        )

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.media.collection",
        "id": collection_id,
        "title": str(value["title"]),
        "publishedAtMs": int(value["publishedAtMs"]),
        "curatorLabel": str(value["curatorLabel"]),
        "curatorialBoundary": str(value["curatorialBoundary"]),
        "members": normalized_members,
        "truthRole": COLLECTION_TRUTH_ROLE,
    }
    return result


def collection_feed_item(collection: Mapping[str, object]) -> dict[str, object]:
    item = validate_collection(collection)
    return {
        "kind": "collection",
        "sourceIdentity": item["id"],
        "observedAtMs": item["publishedAtMs"],
        "title": item["title"],
        "summary": f"Curated collection with {len(item['members'])} independently sourced members.",
        "truthRole": item["truthRole"],
        "sourceDigest": _canonical_digest(item),
    }
