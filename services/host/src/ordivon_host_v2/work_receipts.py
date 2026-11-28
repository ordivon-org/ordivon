"""Work receipt codec; existing WorkStore transaction owns every read and write."""

from __future__ import annotations

from typing import Any

import psycopg

from .canonical_json import canonical_digest
from .postgres_bounds import HOST_WIRE_INT_MAX

_WORK_RECEIPT_REF = "ordivon.host-work-receipt-ref-v1"


def encode_work_receipt(result: dict[str, Any]) -> dict[str, Any]:
    """Preserve the historical response envelope and bind its immutable payload."""
    normalized = {**result, "admission": "existing"}
    envelope = {key: value for key, value in normalized.items() if key != "snapshot"}
    return {
        "kind": _WORK_RECEIPT_REF,
        "envelope": envelope,
        "responseDigest": canonical_digest(normalized),
    }


def replay_work_receipt(
    conn: psycopg.Connection[dict[str, Any]],
    replay: dict[str, Any],
    *,
    work_ref: str,
    work_kind: str | None = None,
    revision: int | None = None,
    snapshot_digest: str | None = None,
    actor_ref: str | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    """Decode a tagged receipt; full legacy receipts keep their existing semantics."""
    if replay.get("kind") == "ordivon.host-work":
        return replay
    envelope = _validated_envelope(
        replay,
        work_ref=work_ref,
        work_kind=work_kind,
        revision=revision,
        snapshot_digest=snapshot_digest,
        actor_ref=actor_ref,
        state=state,
    )
    row = conn.execute(
        "SELECT snapshot_digest,payload,writer_actor_ref FROM work_snapshots "
        "WHERE work_ref=%s AND revision=%s",
        (work_ref, envelope["revision"]),
    ).fetchone()
    return _hydrate(replay, envelope, row)


def replay_pinned_work_receipt(
    replay: dict[str, Any],
    *,
    work_ref: str,
    revision: int,
    target: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate a receipt using the exact native root and joined target."""
    if not isinstance(work_ref, str) or type(revision) is not int:
        raise RuntimeError("invalid native Work receipt root")
    envelope = _validated_envelope(replay, work_ref=work_ref, revision=revision)
    return _hydrate(replay, envelope, target)


def _validated_envelope(
    replay: dict[str, Any],
    *,
    work_ref: str,
    work_kind: str | None = None,
    revision: int | None = None,
    snapshot_digest: str | None = None,
    actor_ref: str | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    if replay.get("kind") != _WORK_RECEIPT_REF:
        raise RuntimeError("unknown Work receipt format")
    envelope = replay.get("envelope")
    if not isinstance(envelope, dict):
        raise RuntimeError("invalid Work receipt envelope")
    rev = envelope.get("revision")
    digest = envelope.get("snapshotDigest")
    writer = envelope.get("writerActorRef")
    if (
        envelope.get("kind") != "ordivon.host-work"
        or type(envelope.get("schemaVersion")) is not int
        or envelope["schemaVersion"] != 1
        or envelope.get("workRef") != work_ref
        or type(rev) is not int
        or not 1 <= rev <= HOST_WIRE_INT_MAX
        or not isinstance(digest, str)
        or not isinstance(writer, str)
        or envelope.get("admission") != "existing"
        or "snapshot" in envelope
        or (work_kind is not None and envelope.get("workKind") != work_kind)
        or (revision is not None and rev != revision)
        or (snapshot_digest is not None and digest != snapshot_digest)
        or (actor_ref is not None and writer != actor_ref)
        or (state is not None and envelope.get("state") != state)
    ):
        raise RuntimeError("Work receipt reference differs from committed request")
    return envelope


def _hydrate(
    replay: dict[str, Any], envelope: dict[str, Any], row: dict[str, Any] | None
) -> dict[str, Any]:
    if (
        row is None
        or row["snapshot_digest"] != envelope["snapshotDigest"]
        or row["writer_actor_ref"] != envelope["writerActorRef"]
        or not isinstance(row["payload"], dict)
        or canonical_digest(row["payload"]) != envelope["snapshotDigest"]
    ):
        raise RuntimeError("committed Work receipt target is missing or changed")
    result = {**envelope, "snapshot": row["payload"]}
    if canonical_digest(result) != replay.get("responseDigest"):
        raise RuntimeError("committed Work receipt response digest differs")
    return result
