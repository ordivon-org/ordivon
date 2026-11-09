"""History health must expose gaps even when the current Work pointer is valid."""

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


def test_history_hole_is_visible_to_both_history_and_integrity_doctor() -> None:
    assert DSN is not None
    token = uuid4().hex
    actor_ref = f"actor:agent:history-diagnostic:{token}"
    work_ref = f"work:history-diagnostic:{token}"
    store = WorkStore(DSN)
    store.declare_actor(
        ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )
    snapshot = WorkSnapshotInput(objective="verify retained history", frontier="current")
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
            snapshot=WorkSnapshotInput(objective="verify retained history", frontier="r2"),
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
            assert checks["work.snapshot_history_contiguous"]["status"] == "error"
            assert doctor["healthy"] is False
    finally:
        with psycopg.connect(DSN) as connection:
            connection.execute("DELETE FROM work_snapshots WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM works WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (actor_ref,))
