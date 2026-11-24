"""Pure original Journal and CAS row codecs.

Original PostgreSQL connection and existing transaction authority are retained.
"""

from __future__ import annotations
from anc_canonical import JsonValue, canonical_bytes, canonical_digest, loads_strict
from .store_errors import (
    HarnessJournalCorruption,
    HarnessObjectCorrupt,
    HarnessObjectMissing,
)
from .store import (
    HARNESS_STORE_EVENT_KINDS,
    HarnessRunEventRecord,
    HarnessRunProjection,
    HarnessRunStatus,
)


_EVENT_PAYLOAD_KIND = "ordivon.harness-run-event-payload"

_CONTRACT_OBJECT_KIND = "harness-run-contract"

_MAX_EVENT_BATCH = 256

def event_payload(event_kind: str, data: dict[str, JsonValue]) -> dict[str, JsonValue]:
    if event_kind not in HARNESS_STORE_EVENT_KINDS:
        raise ValueError("unsupported Harness store event kind")
    return {
        "schemaVersion": 1,
        "kind": _EVENT_PAYLOAD_KIND,
        "eventKind": event_kind,
        "data": data,
    }

def decode_object_row(
    digest: str, row: dict | None, *, expected_kind: str | None = None
) -> JsonValue:
    """Verify one already-fetched CAS object without another SQL round trip."""
    if row is None:
        raise HarnessObjectMissing(f"Harness PostgreSQL object missing: {digest}")
    if expected_kind is not None and row["kind"] != expected_kind:
        raise HarnessObjectCorrupt("Harness PostgreSQL object kind differs")
    raw = bytes(row["content"])
    try:
        value = loads_strict(raw)
    except ValueError as error:
        raise HarnessObjectCorrupt("Harness PostgreSQL object is invalid JSON") from error
    if (
        len(raw) != int(row["byte_length"])
        or canonical_digest(value) != digest
        or canonical_bytes(value) != raw
    ):
        raise HarnessObjectCorrupt("Harness PostgreSQL object hash/size differs")
    return value

def decode_event_rows(rows: list[dict]) -> tuple[HarnessRunEventRecord, ...]:
    result = []
    for row in rows:
        payload = decode_object_row(
            row["payload_digest"],
            None
            if row["object_kind"] is None
            else {
                "kind": row["object_kind"],
                "byte_length": row["object_byte_length"],
                "content": row["object_content"],
            },
            expected_kind=_EVENT_PAYLOAD_KIND,
        )
        if (
            not isinstance(payload, dict)
            or set(payload) != {"schemaVersion", "kind", "eventKind", "data"}
            or payload["schemaVersion"] != 1
            or payload["kind"] != _EVENT_PAYLOAD_KIND
            or payload["eventKind"] != row["event_kind"]
            or not isinstance(payload["data"], dict)
        ):
            raise HarnessJournalCorruption("Harness event payload differs from metadata")
        result.append(
            HarnessRunEventRecord(
                sequence=int(row["sequence"]),
                event_id=row["event_id"],
                harness_run_id=row["harness_run_id"],
                run_revision=int(row["run_revision"]),
                event_kind=row["event_kind"],
                payload_digest=row["payload_digest"],
                data=dict(payload["data"]),
                caused_by_event_id=row["caused_by_event_id"],
                recorded_at_ms=int(row["recorded_at_ms"]),
            )
        )
    return tuple(result)

def run_projection(harness_run_id: str, row: dict) -> HarnessRunProjection:
    try:
        return HarnessRunProjection(
            harness_run_id=harness_run_id,
            contract_digest=row["contract_digest"],
            contract_object_digest=row["contract_object_digest"],
            caller_id=row["caller_id"],
            caller_run_ref=row["caller_run_ref"],
            status=HarnessRunStatus(row["status"]),
            revision=int(row["revision"]),
            created_at_ms=int(row["created_at_ms"]),
            updated_at_ms=int(row["updated_at_ms"]),
            terminal_event_id=row["terminal_event_id"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HarnessJournalCorruption("Harness PostgreSQL Run projection is invalid") from error
