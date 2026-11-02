"""Concrete CEGAR: Host Work readbacks must preserve durable digest identities."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.work_store import WorkStore

_TIME = datetime(2026, 10, 25, tzinfo=UTC)
_PAYLOAD = {
    "objective": "retain source-bound evidence",
    "frontier": "native Host Work readback",
    "established": [],
    "unresolved": [],
    "constraints": [],
    "nextActions": [],
    "referenceRefs": [],
}


class _Rows:
    def __init__(self, payload_digest: str, current_digest: str, revision: int = 2) -> None:
        self.payload_digest = payload_digest
        self.current_digest = current_digest
        self.revision = revision
        self.calls: list[str] = []

    def execute(self, statement: str, args: tuple[object, ...]):
        self.calls.append(statement)
        return self

    def fetchone(self):
        last = self.calls[-1]
        if "FROM works" in last:
            return {
                "work_ref": "work:verification",
                "kind": "investigation",
                "state": "open",
                "current_revision": self.revision,
                "current_snapshot_digest": self.current_digest,
                "created_by_actor_ref": "actor:agent:observer",
                "created_at": _TIME,
                "updated_at": _TIME,
            }
        if "FROM work_snapshots" in last:
            return {
                "snapshot_digest": self.payload_digest,
                "payload": dict(_PAYLOAD),
                "writer_actor_ref": "actor:agent:writer",
                "created_at": _TIME,
            }
        raise AssertionError("Unexpected source read")


def test_host_work_read_rejects_payload_digest_corruption_before_projection() -> None:
    conn = _Rows("sha256:" + "0" * 64, "sha256:" + "0" * 64)
    with pytest.raises(RuntimeError, match="snapshot.*digest"):
        WorkStore("postgresql://never-used")._get_work_in_tx(conn, "work:verification", None)


def test_host_work_read_rejects_current_pointer_digest_corruption() -> None:
    conn = _Rows(canonical_digest(_PAYLOAD), "sha256:" + "0" * 64)
    with pytest.raises(RuntimeError, match="current.*digest"):
        WorkStore("postgresql://never-used")._get_work_in_tx(conn, "work:verification", None)


def test_host_work_read_accepts_integrity_preserving_current_snapshot() -> None:
    correct = canonical_digest(_PAYLOAD)
    conn = _Rows(correct, correct)
    result = WorkStore("postgresql://never-used")._get_work_in_tx(conn, "work:verification", None)
    assert result["snapshotDigest"] == correct
    assert canonical_digest(result["snapshot"]) == correct
    assert result["revision"] == 2
    assert result["state"] == "open"


def test_host_historical_work_read_does_not_require_current_pointer_match() -> None:
    historical = canonical_digest(_PAYLOAD)
    conn = _Rows(historical, "sha256:" + "1" * 64)
    result = WorkStore("postgresql://never-used")._get_work_in_tx(conn, "work:verification", 1)
    assert result["snapshotDigest"] == historical
    assert result["state"] == "historical_state_unknown"
