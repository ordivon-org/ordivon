"""Read-only consumer of existing Host historical checkpoint messages.

The caller supplies an independently selected Work and manifest pin plus
owner readbacks. A verified archive is NOT current business truth, a
retention pin, permission to delete history, or proof of authorization.
No transport, DB connection, snapshot writer or new archive format.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from ordivon_host_v2.canonical_json import canonical_bytes, canonical_digest
from ordivon_host_v2.postgres_bounds import HOST_WIRE_INT_MAX
from ordivon_host_v2.social_message_records import message_content
from ordivon_host_v2.work_inputs import WorkSnapshotInput


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON object key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant {value}")


def parse_object(raw: str) -> dict[str, Any]:
    value = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    require(isinstance(value, dict), "expected JSON object")
    return value


def _digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _ref(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value


def _message(wire: dict[str, Any], ref: str, digest: str) -> dict[str, Any]:
    require(_ref(ref) and _digest(digest), "invalid pinned message identity")
    require(
        type(wire.get("schemaVersion")) is int
        and wire["schemaVersion"] == 1
        and wire.get("kind") == "ordivon.host-message-read"
        and wire.get("messageRef") == ref
        and wire.get("messageDigest") == digest,
        "message pin differs",
    )
    require(
        all(_ref(wire.get(k)) for k in ("spaceRef", "topicRef", "authorActorRef", "messageKind"))
        and isinstance(wire.get("body"), str)
        and type(wire.get("recordedAtMs")) is int
        and 0 <= wire["recordedAtMs"] <= HOST_WIRE_INT_MAX,
        "invalid immutable message fields",
    )
    content = message_content(
        message_ref=wire["messageRef"],
        space_ref=wire["spaceRef"],
        topic_ref=wire["topicRef"],
        author_actor_ref=wire["authorActorRef"],
        message_kind=wire["messageKind"],
        body=wire["body"],
        recorded_at_ms=wire["recordedAtMs"],
    )
    require(canonical_digest(content) == digest, "message content digest differs")
    return parse_object(wire["body"])


def _coordinate(value: dict[str, Any], pin: dict[str, Any]) -> None:
    require(
        value.get("workRef") == pin["workRef"]
        and type(value.get("revision")) is int
        and value["revision"] == pin["revision"]
        and value.get("snapshotDigest") == pin["snapshotDigest"],
        "checkpoint Work coordinate differs",
    )


def _full(
    manifest: dict[str, Any],
    manifest_wire: dict[str, Any],
    parts: list[dict[str, Any]],
    pin: dict[str, Any],
    snapshot: dict[str, Any],
) -> None:
    refs = manifest.get("parts")
    require(isinstance(refs, list) and bool(refs) and len(refs) == len(parts), "part count differs")
    seen: set[str] = set()
    payloads: list[str] = []
    for ordinal, (identity, wire) in enumerate(zip(refs, parts, strict=True), 1):
        require(isinstance(identity, dict), "invalid part pointer")
        ref, digest = identity.get("messageRef"), identity.get("messageDigest")
        require(_ref(ref) and ref not in seen, "duplicate or invalid part reference")
        seen.add(ref)
        body = _message(wire, ref, digest)
        _coordinate(body, pin)
        require(
            wire["spaceRef"] == manifest_wire["spaceRef"]
            and wire["topicRef"] == manifest_wire["topicRef"],
            "part scope differs",
        )
        require(
            body.get("kind") == "work-snapshot-checkpoint-part-v1"
            and type(body.get("part")) is int
            and body["part"] == ordinal
            and type(body.get("total")) is int
            and body["total"] == len(refs)
            and isinstance(body.get("payload"), str),
            "part ordinal or payload differs",
        )
        payloads.append(body["payload"])
    payload = "".join(payloads)
    # The historical manifest writer used ECMAScript String.length, i.e. UTF-16
    # code units, not Python code points or bytes.
    require(
        type(manifest.get("chars")) is int
        and manifest["chars"] == len(payload.encode("utf-16-le")) // 2,
        "checkpoint character count differs",
    )
    require(
        manifest.get("encoding") == "ordered concatenation of part.payload, JSON.parse",
        "unsupported checkpoint encoding",
    )
    require(
        canonical_bytes(parse_object(payload)) == canonical_bytes(snapshot),
        "reconstructed snapshot differs",
    )


def verify_checkpoint(
    pin: dict[str, Any],
    work: dict[str, Any],
    manifest_wire: dict[str, Any],
    parts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify selected historical bytes, not currentness or retention."""
    require(
        _ref(pin.get("workRef"))
        and _digest(pin.get("snapshotDigest"))
        and type(pin.get("revision")) is int
        and 1 <= pin["revision"] <= HOST_WIRE_INT_MAX,
        "invalid pinned Work coordinate",
    )
    require(
        type(work.get("schemaVersion")) is int
        and work["schemaVersion"] == 1
        and work.get("kind") == "ordivon.host-work",
        "invalid Work response",
    )
    _coordinate(work, pin)
    snapshot = work.get("snapshot")
    require(isinstance(snapshot, dict), "invalid Work snapshot")
    typed = WorkSnapshotInput.model_validate(snapshot, strict=True)
    require(
        canonical_bytes(typed.canonical_payload()) == canonical_bytes(snapshot),
        "Work snapshot is not complete canonical payload",
    )
    require(canonical_digest(snapshot) == pin["snapshotDigest"], "Work payload digest differs")
    manifest = _message(manifest_wire, pin.get("manifestRef"), pin.get("manifestDigest"))
    _coordinate(manifest, pin)
    kind = manifest.get("kind")
    result = {
        "kind": kind,
        "workRef": pin["workRef"],
        "revision": pin["revision"],
        "snapshotDigest": pin["snapshotDigest"],
        "manifestRef": pin["manifestRef"],
        "manifestDigest": pin["manifestDigest"],
        "referenceCount": len(snapshot["referenceRefs"]),
        "retentionPinVerified": False,
        "currentnessVerified": False,
    }
    if kind == "work-snapshot-checkpoint-manifest-v1":
        _full(manifest, manifest_wire, parts, pin, snapshot)
        return {**result, "snapshotVerified": True, "partCount": len(parts)}
    if kind == "ordered-reference-checkpoint-v1":
        require(not parts, "unexpected parts for ordered reference archive")
        refs = manifest.get("referenceRefs")
        require(
            isinstance(refs, list)
            and type(manifest.get("count")) is int
            and manifest["count"] == len(refs)
            and refs == snapshot["referenceRefs"],
            "ordered reference archive differs",
        )
        previous_ref = manifest.get("previousFullCheckpoint")
        previous_digest = manifest.get("previousFullCheckpointDigest")
        require(_ref(previous_ref) and _digest(previous_digest), "invalid previous checkpoint pin")
        return {
            **result,
            "snapshotVerified": False,
            "orderedReferencesVerified": True,
            "previousFullCheckpoint": previous_ref,
            "previousFullCheckpointDigest": previous_digest,
            "previousCheckpointVerified": False,
        }
    raise ValueError("unsupported checkpoint kind")


def main() -> None:
    bundle = parse_object(sys.stdin.read())
    print(
        json.dumps(
            verify_checkpoint(bundle["pin"], bundle["work"], bundle["manifest"], bundle["parts"]),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
