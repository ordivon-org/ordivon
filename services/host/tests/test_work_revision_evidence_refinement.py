"""Evidence-driven Work revision absence, not a generic UNKNOWN or retry guess."""

from __future__ import annotations

import asyncio
import json
import os
from uuid import uuid4

import psycopg
import pytest
from mcp import Client
from psycopg.types.json import Jsonb

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.errors import ConflictError, WorkRevisionUnavailable
from ordivon_host_v2.mcp_domain_errors import _domain_error_payload
from ordivon_host_v2.mcp_server import build_server
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput, WorkCreateInput, WorkSnapshotInput
from ordivon_host_v2.work_queries import read_work_in_tx
from ordivon_host_v2.work_store import WorkStore

TEST_DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
CASES = (
    (3, 2, "revision_ahead_of_current", "reread-current-work-before-waiting-for-revision"),
    (1, 2, "historical_snapshot_absent", "inspect-retention-and-archive-before-recovery"),
    (2, 2, "current_snapshot_missing", "stop-current-work-consumption-and-check-host-integrity"),
)


class MissingSnapshotConnection:
    def __init__(self, current_revision: int = 2) -> None:
        self.current_revision = current_revision
        self.query = ""

    def execute(self, query: str, args: tuple[object, ...]) -> MissingSnapshotConnection:
        self.query = query
        assert args[0] == "work:evidence"
        return self

    def fetchone(self):
        if "FROM works" in self.query:
            return {
                "work_ref": "work:evidence",
                "kind": "review",
                "state": "open",
                "current_revision": self.current_revision,
                "current_snapshot_digest": "sha256:" + "1" * 64,
                "created_by_actor_ref": "actor:writer",
                "created_at": None,
                "updated_at": None,
            }
        assert "FROM work_snapshots" in self.query
        return None


@pytest.mark.parametrize(("requested", "current", "reason", "action"), CASES)
def test_source_read_refines_exact_missing_revision_without_claiming_history(
    requested: int, current: int, reason: str, action: str
) -> None:
    with pytest.raises(WorkRevisionUnavailable, match=f"no revision {requested}") as info:
        read_work_in_tx(MissingSnapshotConnection(current), "work:evidence", requested)
    exc = info.value
    assert isinstance(exc, ConflictError)  # Backward-compatible exception family.
    assert (exc.requested_revision, exc.current_revision, exc.reason) == (
        requested,
        current,
        reason,
    )
    payload = _domain_error_payload(exc)
    assert payload == {
        "schemaVersion": 1,
        "kind": "ordivon.host-domain-error",
        "retryable": False,
        "code": "CONFLICT",
        "detail": f"work work:evidence has no revision {requested}",
        "reason": reason,
        "resourceKind": "work",
        "resourceRef": "work:evidence",
        "requestedRevision": requested,
        "observedCurrentRevision": current,
        "evidenceBoundary": "same-transaction-host-work-and-snapshot-read",
        "suggestedAction": action,
    }


def test_existing_generic_conflict_keeps_original_wire_contract() -> None:
    assert _domain_error_payload(ConflictError("incompatible CAS")) == {
        "schemaVersion": 1,
        "kind": "ordivon.host-domain-error",
        "retryable": False,
        "code": "CONFLICT",
        "detail": "incompatible CAS",
        "suggestedAction": "reread-current-state-and-reconcile",
    }


def test_mcp_client_receives_specific_forward_and_reverse_evidence(monkeypatch) -> None:
    def witness(self, work_ref: str, revision: int | None = None):
        _ = self
        assert work_ref == "work:evidence"
        assert revision is not None
        raise WorkRevisionUnavailable(work_ref, revision, 2)

    monkeypatch.setattr(WorkStore, "get_work", witness)

    async def run() -> None:
        async with Client(
            build_server("postgresql://unused.invalid/host"), raise_exceptions=False
        ) as client:
            for requested, current, reason, action in CASES:
                result = await client.call_tool(
                    "work.get", {"workRef": "work:evidence", "revision": requested}
                )
                assert result.is_error
                content = "".join(getattr(item, "text", "") for item in result.content)
                assert content.startswith("Error executing tool work.get: ")
                payload = json.loads(content.split(": ", 1)[1])
                assert payload["reason"] == reason
                assert payload["observedCurrentRevision"] == current
                assert payload["requestedRevision"] == requested
                assert payload["suggestedAction"] == action
                assert payload["retryable"] is False

    asyncio.run(run())


@pytest.mark.skipif(not TEST_DSN, reason="disposable PostgreSQL TEST_DSN is required")
@pytest.mark.usefixtures("host_test_db_ready")
def test_pg18_work_revision_absence_three_distinct_facts() -> None:
    """Real PostgreSQL: test forward absent, retained history loss, current corruption.

    The initial Work and damage are created in this test's own random fixture.
    This test must run only in the existing isolated Host test database.
    """
    assert TEST_DSN is not None
    token = uuid4().hex
    actor = f"actor:agent:revision-evidence:{token}"
    work_ref = f"work:revision-evidence:{token}"
    store = WorkStore(TEST_DSN)
    ActorReferenceStore(store.dsn).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor-evidence:{token}",
    )
    try:
        store.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="evidence",
                actor_ref=actor,
                initial_snapshot=WorkSnapshotInput(objective="revision evidence", frontier="r1"),
            ),
            client_request_id=f"create-evidence:{token}",
        )
        assert store.get_work(work_ref, 1)["state"] == "open"

        # Inverse falsifier: the SQL schema permits an orphan Snapshot revision
        # above works.current_revision. A row's existence alone must not make
        # that uncommitted revision observable as committed Work state.
        ghost_payload = WorkSnapshotInput(
            objective="revision evidence", frontier="uncommitted-ghost"
        ).canonical_payload()
        with psycopg.connect(TEST_DSN) as conn:
            conn.execute(
                "INSERT INTO work_snapshots("
                "work_ref,revision,snapshot_digest,payload,writer_actor_ref"
                ") VALUES (%s,%s,%s,%s,%s)",
                (work_ref, 3, canonical_digest(ghost_payload), Jsonb(ghost_payload), actor),
            )
        with pytest.raises(WorkRevisionUnavailable) as ghost:
            store.get_work(work_ref, 3)
        assert ghost.value.reason == "revision_ahead_of_current"
        assert ghost.value.current_revision == 1

        with pytest.raises(WorkRevisionUnavailable) as future:
            store.get_work(work_ref, 2)
        assert future.value.reason == "revision_ahead_of_current"
        assert future.value.current_revision == 1

        store.commit_snapshot(
            work_ref,
            expected_revision=1,
            snapshot=WorkSnapshotInput(objective="revision evidence", frontier="r2"),
            actor_ref=actor,
            client_request_id=f"commit-evidence:{token}",
        )

        with psycopg.connect(TEST_DSN) as conn:
            conn.execute("DELETE FROM work_snapshots WHERE work_ref=%s AND revision=1", (work_ref,))
        with pytest.raises(WorkRevisionUnavailable) as historical:
            store.get_work(work_ref, 1)
        assert historical.value.reason == "historical_snapshot_absent"
        assert historical.value.current_revision == 2
        assert store.get_work(work_ref)["revision"] == 2

        with psycopg.connect(TEST_DSN) as conn:
            conn.execute("DELETE FROM work_snapshots WHERE work_ref=%s AND revision=2", (work_ref,))
        with pytest.raises(WorkRevisionUnavailable) as current:
            store.get_work(work_ref)
        assert current.value.reason == "current_snapshot_missing"
        assert current.value.current_revision == 2
    finally:
        with psycopg.connect(TEST_DSN) as conn:
            conn.execute("DELETE FROM work_snapshots WHERE work_ref=%s", (work_ref,))
            conn.execute("DELETE FROM works WHERE work_ref=%s", (work_ref,))
            conn.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (actor,))
