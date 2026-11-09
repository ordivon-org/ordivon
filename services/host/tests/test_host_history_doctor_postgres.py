"""History health must expose gaps even when the current Work pointer is valid."""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest

from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
    WorkState,
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


def test_terminal_work_identity_remains_navigable_with_partial_history() -> None:
    """Pruned revisions do not erase an actually consumed Work identity.

    This is a preservation contract, not proof that historical pruning was authorized.
    It exercises real Work, Social and Doctor public seams on disposable PostgreSQL.
    """
    assert DSN is not None
    token = uuid4().hex
    actor_ref = f"actor:agent:history-navigation:{token}"
    work_ref = f"work:history-navigation:{token}"
    space_ref = f"space:history-navigation:{token}"
    topic_ref = f"topic:history-navigation:{token}"
    message_ref = f"message:history-navigation:{token}"
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    work.declare_actor(
        ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )
    try:
        work.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="history-navigation",
                actor_ref=actor_ref,
                initial_snapshot=WorkSnapshotInput(
                    objective="retain navigable Host identity",
                    frontier="r1",
                ),
            ),
            client_request_id=f"create:{token}",
        )
        work.commit_snapshot(
            work_ref,
            expected_revision=1,
            snapshot=WorkSnapshotInput(
                objective="retain navigable Host identity",
                frontier="r2",
            ),
            actor_ref=actor_ref,
            state=WorkState.COMPLETED,
            client_request_id=f"commit:{token}",
        )
        social.create_space(
            SpaceInput(
                space_ref=space_ref,
                purpose="real Work navigation consumer",
                actor_ref=actor_ref,
                subject_refs=[work_ref],
            ),
            client_request_id=f"space:{token}",
        )
        social.create_topic(
            TopicInput(
                topic_ref=topic_ref,
                space_ref=space_ref,
                title="history consumer",
                actor_ref=actor_ref,
            ),
            client_request_id=f"topic:{token}",
        )
        social.post_message(
            MessageInput(
                message_ref=message_ref,
                client_request_id=f"message:{token}",
                space_ref=space_ref,
                topic_ref=topic_ref,
                author_actor_ref=actor_ref,
                body=f"Historical handoff about {work_ref}",
                recorded_at_ms=1,
            )
        )
        social.add_message_relation(
            MessageRelationInput(
                source_message_ref=message_ref,
                relation=MessageRelationKind.REFERENCES,
                target_ref=work_ref,
                actor_ref=actor_ref,
            ),
            client_request_id=f"relation:{token}",
        )
        # Simulate the actual production shape: revision 2 exists, revision 1 is gone.
        with psycopg.connect(DSN) as connection:
            connection.execute(
                "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=1",
                (work_ref,),
            )

        current = work.get_work(work_ref)
        assert current["state"] == "completed"
        assert current["revision"] == 2
        assert current["snapshot"]["frontier"] == "r2"
        with pytest.raises(ConflictError, match="no revision 1"):
            work.get_work(work_ref, 1)

        assert [row["spaceRef"] for row in social.list_spaces(subject_ref=work_ref)["spaces"]] == [
            space_ref
        ]
        assert work_ref in social.list_space_subjects(space_ref)["subjectRefs"]
        relation_rows = social.list_message_relations(message_ref)["relations"]
        assert [(row["relation"], row["targetRef"]) for row in relation_rows] == [
            ("references", work_ref)
        ]
        assert work_ref in social.get_message(message_ref)["body"]

        for detail in ("integrity", "history"):
            doctor = HostV2(DSN).status(detail=detail)["doctor"]
            assert doctor is not None
            checks = {item["name"]: item["status"] for item in doctor["checks"]}
            assert checks["work.current_snapshot"] == "ok"
            assert checks["work.snapshot_history_contiguous"] == "error"
            assert doctor["healthy"] is False
    finally:
        with psycopg.connect(DSN) as connection:
            connection.execute(
                "DELETE FROM message_relations WHERE source_message_ref=%s",
                (message_ref,),
            )
            connection.execute("DELETE FROM messages WHERE message_ref=%s", (message_ref,))
            connection.execute("DELETE FROM topics WHERE topic_ref=%s", (topic_ref,))
            connection.execute("DELETE FROM space_subjects WHERE space_ref=%s", (space_ref,))
            connection.execute("DELETE FROM spaces WHERE space_ref=%s", (space_ref,))
            connection.execute("DELETE FROM work_snapshots WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM works WHERE work_ref=%s", (work_ref,))
            connection.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (actor_ref,))
