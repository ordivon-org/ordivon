"""Work continuity requires a sound current snapshot, not a complete archival timeline."""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest

from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
)
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def test_missing_historical_revisions_do_not_break_healthy_current_work() -> None:
    assert DSN is not None
    token = uuid4().hex
    actor_ref = f"actor:agent:history-diagnostic:{token}"
    work_ref = f"work:history-diagnostic:{token}"
    store = WorkStore(DSN)
    store.declare_actor(
        ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )
    snapshot = WorkSnapshotInput(objective="verify current snapshot", frontier="current")
    try:
        store.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="diagnostic",
                actor_ref=actor_ref,
                initial_snapshot=snapshot,
            ),
            client_request_id=f"create:{token}",
        )
        store.commit_snapshot(
            work_ref,
            expected_revision=1,
            snapshot=WorkSnapshotInput(objective="verify current snapshot", frontier="r2"),
            actor_ref=actor_ref,
            client_request_id=f"commit:{token}",
        )
        # Corrupt only an isolated disposable TEST_DSN Work history.
        with psycopg.connect(DSN) as connection:
            connection.execute(
                "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=1",
                (work_ref,),
            )
        assert store.get_work(work_ref)["revision"] == 2
        # Historical reads must never manufacture a removed revision.
        with pytest.raises(ConflictError, match="no revision 1"):
            store.get_work(work_ref, 1)

        for detail in ("integrity", "history"):
            doctor = HostV2(DSN).status(detail=detail)["doctor"]
            assert doctor is not None
            checks = {item["name"]: item for item in doctor["checks"]}
            assert checks["work.current_snapshot"]["status"] == "ok"
            assert "work.snapshot_history_contiguous" not in checks
            assert doctor["healthy"] is True
    finally:
        with psycopg.connect(DSN) as connection:
            connection.execute("DELETE FROM work_snapshots WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM works WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (actor_ref,))


def test_current_snapshot_payload_corruption_is_a_doctor_failure() -> None:
    assert DSN is not None
    token = uuid4().hex
    actor_ref = f"actor:agent:current-diagnostic:{token}"
    work_ref = f"work:current-diagnostic:{token}"
    store = WorkStore(DSN)
    store.declare_actor(
        ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )
    try:
        store.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="diagnostic",
                actor_ref=actor_ref,
                initial_snapshot=WorkSnapshotInput(objective="current-digest", frontier="original"),
            ),
            client_request_id=f"create:{token}",
        )
        with psycopg.connect(DSN) as connection:
            connection.execute(
                "UPDATE work_snapshots SET payload=jsonb_set(payload,'{frontier}',"
                "'\"changed-without-digest\"'::jsonb) WHERE work_ref=%s AND revision=1",
                (work_ref,),
            )
        for detail in ("integrity", "history"):
            doctor = HostV2(DSN).status(detail=detail)["doctor"]
            assert doctor is not None
            checks = {item["name"]: item for item in doctor["checks"]}
            assert checks["work.current_snapshot_payload_digest"]["status"] == "error"
            assert doctor["healthy"] is False
    finally:
        with psycopg.connect(DSN) as connection:
            connection.execute("DELETE FROM work_snapshots WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM works WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (actor_ref,))
