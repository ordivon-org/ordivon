from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.social_attention import AttentionStore
from ordivon_host_v2.social_graph import (
    CoordinationIntentInput,
    MessageInput,
    MessageKind,
    MessageRelationInput,
    MessageRelationKind,
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.social_work import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkRelationInput,
    WorkRelationKind,
    WorkSnapshotInput,
)
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def refs(label: str) -> tuple[str, str]:
    token = uuid4().hex
    return f"actor:agent:{label}:{token}", f"work:{label}:{token}"


def snapshot(frontier: str) -> WorkSnapshotInput:
    return WorkSnapshotInput(
        objective="exercise Social Work Fabric",
        frontier=frontier,
        established=[],
        unresolved=[],
        rejected=[],
        constraints=["owner boundaries preserved"],
        next_actions=[],
        reference_refs=[],
    )


def declare_actor(store: WorkStore, actor_ref: str) -> None:
    store.declare_actor(
        ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{actor_ref}",
    )


def test_work_snapshot_cas_race_has_one_winner() -> None:
    assert DSN is not None
    store = WorkStore(DSN)
    actor_ref, work_ref = refs("cas")
    declare_actor(store, actor_ref)
    store.create_work(
        WorkCreateInput(
            work_ref=work_ref,
            kind="investigation",
            actor_ref=actor_ref,
            initial_snapshot=snapshot("r1"),
        ),
        client_request_id=f"create:{work_ref}",
    )

    def write(frontier: str) -> str:
        try:
            store.commit_snapshot(
                work_ref,
                expected_revision=1,
                snapshot=snapshot(frontier),
                actor_ref=actor_ref,
                client_request_id=f"commit:{work_ref}:{frontier}",
            )
            return "committed"
        except ConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(write, ("r2-a", "r2-b")))
    assert outcomes == ["committed", "conflict"]
    assert store.get_work(work_ref)["revision"] == 2


def test_work_parent_cycle_fails_closed() -> None:
    assert DSN is not None
    store = WorkStore(DSN)
    actor_ref, first_ref = refs("cycle-a")
    _, second_ref = refs("cycle-b")
    declare_actor(store, actor_ref)
    for work_ref in (first_ref, second_ref):
        store.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="task",
                actor_ref=actor_ref,
                initial_snapshot=snapshot("open"),
            ),
            client_request_id=f"create:{work_ref}",
        )
    store.add_relation(
        WorkRelationInput(
            source_work_ref=first_ref,
            relation=WorkRelationKind.PARENT_OF,
            target_work_ref=second_ref,
            actor_ref=actor_ref,
        ),
        client_request_id=f"rel:{first_ref}:{second_ref}",
    )
    with pytest.raises(ConflictError, match="cycle"):
        store.add_relation(
            WorkRelationInput(
                source_work_ref=second_ref,
                relation=WorkRelationKind.PARENT_OF,
                target_work_ref=first_ref,
                actor_ref=actor_ref,
            ),
            client_request_id=f"rel:{second_ref}:{first_ref}",
        )


def test_space_can_link_multiple_works_without_becoming_work_container() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    actor_ref, work_a = refs("space-a")
    _, work_b = refs("space-b")
    declare_actor(work, actor_ref)
    for work_ref in (work_a, work_b):
        work.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="task",
                actor_ref=actor_ref,
                initial_snapshot=snapshot("open"),
            ),
            client_request_id=f"create:{work_ref}",
        )
    space_ref = f"space:cross-work:{uuid4().hex}"
    created = social.create_space(
        SpaceInput(
            space_ref=space_ref,
            purpose="cross-work collaboration",
            actor_ref=actor_ref,
            subject_refs=[work_a, work_b, "resource:shared"],
        ),
        client_request_id=f"space:{space_ref}",
    )
    assert set(created["subjectRefs"]) == {work_a, work_b, "resource:shared"}


def test_topic_message_reply_and_mention_are_structured() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    actor_a, _ = refs("message-a")
    actor_b, _ = refs("message-b")
    declare_actor(work, actor_a)
    declare_actor(work, actor_b)
    space_ref = f"space:messages:{uuid4().hex}"
    topic_ref = f"topic:messages:{uuid4().hex}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="messages", actor_ref=actor_a),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(
            topic_ref=topic_ref,
            space_ref=space_ref,
            title="matching",
            actor_ref=actor_a,
        ),
        client_request_id=f"topic:{topic_ref}",
    )
    first_ref = f"message:{uuid4().hex}"
    second_ref = f"message:{uuid4().hex}"
    social.post_message(
        MessageInput(
            message_ref=first_ref,
            client_request_id=f"post:{first_ref}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor_a,
            message_kind=MessageKind.NOTE,
            body="first",
            recorded_at_ms=1,
        )
    )
    social.post_message(
        MessageInput(
            message_ref=second_ref,
            client_request_id=f"post:{second_ref}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor_b,
            message_kind=MessageKind.FINDING,
            body="reply",
            recorded_at_ms=2,
        )
    )
    social.add_message_relation(
        MessageRelationInput(
            source_message_ref=second_ref,
            relation=MessageRelationKind.REPLY_TO,
            target_ref=first_ref,
            actor_ref=actor_b,
        ),
        client_request_id=f"reply:{second_ref}",
    )
    social.add_message_relation(
        MessageRelationInput(
            source_message_ref=second_ref,
            relation=MessageRelationKind.MENTIONS,
            target_ref=actor_a,
            actor_ref=actor_b,
        ),
        client_request_id=f"mention:{second_ref}",
    )
    resumed = social.resume_topic(topic_ref)
    assert [row["messageRef"] for row in resumed["messages"]] == [first_ref, second_ref]


def test_attention_routes_follow_mention_reply_and_cursor_without_ranking() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    actor_a, work_ref = refs("attention-a")
    actor_b, _ = refs("attention-b")
    declare_actor(work, actor_a)
    declare_actor(work, actor_b)
    work.create_work(
        WorkCreateInput(
            work_ref=work_ref,
            kind="task",
            actor_ref=actor_a,
            initial_snapshot=snapshot("r1"),
        ),
        client_request_id=f"create:{work_ref}",
    )
    space_ref = f"space:attention:{uuid4().hex}"
    topic_ref = f"topic:attention:{uuid4().hex}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="attention", actor_ref=actor_a),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, title="t", actor_ref=actor_a),
        client_request_id=f"topic:{topic_ref}",
    )
    attention.follow(
        actor_ref=actor_a,
        target_kind="work",
        target_ref=work_ref,
        client_request_id=f"follow:work:{actor_a}",
    )
    attention.follow(
        actor_ref=actor_a,
        target_kind="topic",
        target_ref=topic_ref,
        client_request_id=f"follow:topic:{actor_a}",
    )
    baseline = attention.delta(actor_a, after_sequence=0, limit=500)["snapshotHighSequence"]
    work.commit_snapshot(
        work_ref,
        expected_revision=1,
        snapshot=snapshot("r2"),
        actor_ref=actor_a,
        client_request_id=f"commit:{work_ref}:r2",
    )
    message_ref = f"message:{uuid4().hex}"
    social.post_message(
        MessageInput(
            message_ref=message_ref,
            client_request_id=f"post:{message_ref}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor_b,
            body="please inspect",
            recorded_at_ms=3,
        )
    )
    social.add_message_relation(
        MessageRelationInput(
            source_message_ref=message_ref,
            relation=MessageRelationKind.MENTIONS,
            target_ref=actor_a,
            actor_ref=actor_b,
        ),
        client_request_id=f"mention:{message_ref}",
    )
    delta = attention.delta(actor_a, after_sequence=baseline, limit=100)
    kinds = {row["eventKind"] for row in delta["events"]}
    assert "work_snapshot" in kinds
    assert "message" in kinds
    assert "message_relation" in kinds
    assert delta["rankingApplied"] is False
    attention.ack(
        actor_a,
        cursor=delta["nextAfterSequence"],
        client_request_id=f"ack:{actor_a}:{delta['nextAfterSequence']}",
    )
    with pytest.raises(ConflictError, match="backwards"):
        attention.ack(
            actor_a,
            cursor=max(0, delta["nextAfterSequence"] - 1),
            client_request_id=f"ack-back:{actor_a}",
        )


def test_coordination_intent_is_visible_but_not_exclusive() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    actor_a, work_ref = refs("intent-a")
    actor_b, _ = refs("intent-b")
    declare_actor(work, actor_a)
    declare_actor(work, actor_b)
    work.create_work(
        WorkCreateInput(
            work_ref=work_ref,
            kind="maintenance",
            actor_ref=actor_a,
            initial_snapshot=snapshot("open"),
        ),
        client_request_id=f"create:{work_ref}",
    )
    subject = f"resource:test:{uuid4().hex}"
    for index, actor_ref in enumerate((actor_a, actor_b)):
        social.declare_intent(
            CoordinationIntentInput(
                intent_ref=f"intent:{uuid4().hex}",
                actor_ref=actor_ref,
                subject_ref=subject,
                operation="inspect",
                work_ref=work_ref,
                observed_at_ms=10 + index,
                expires_at_ms=100 + index,
            ),
            client_request_id=f"intent-request:{uuid4().hex}",
        )
    # Both declarations succeed: an intent is intentionally not a lock or lease.


def test_100_actor_dynamic_regrouping_smoke() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    token = uuid4().hex
    actor_refs = [f"actor:agent:swf100:{token}:{index:03d}" for index in range(100)]
    for actor_ref in actor_refs:
        declare_actor(work, actor_ref)

    work_refs = [f"work:swf100:{token}:{index:02d}" for index in range(10)]
    for index, work_ref in enumerate(work_refs):
        actor_ref = actor_refs[index]
        work.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="task",
                actor_ref=actor_ref,
                initial_snapshot=snapshot("open"),
            ),
            client_request_id=f"create:{work_ref}",
        )

    space_ref = f"space:swf100:{token}"
    social.create_space(
        SpaceInput(
            space_ref=space_ref,
            purpose="100-actor regrouping smoke",
            actor_ref=actor_refs[0],
            subject_refs=work_refs[:5],
        ),
        client_request_id=f"space:{space_ref}",
    )
    for actor_ref in actor_refs:
        social.set_participation(
            space_ref=space_ref,
            actor_ref=actor_ref,
            standing=ParticipationStanding.JOINED,
            client_request_id=f"join:{space_ref}:{actor_ref}",
        )
    for actor_ref in actor_refs[:20]:
        social.set_participation(
            space_ref=space_ref,
            actor_ref=actor_ref,
            standing=ParticipationStanding.LEFT,
            client_request_id=f"leave:{space_ref}:{actor_ref}",
        )
    view = social.get_space(space_ref)
    standings = {row["actorRef"]: row["standing"] for row in view["participants"]}
    assert len(standings) == 100
    assert sum(value == "left" for value in standings.values()) == 20
    assert sum(value == "joined" for value in standings.values()) == 80


def test_work_snapshot_response_loss_replay_with_new_request_id_is_existing() -> None:
    assert DSN is not None
    store = WorkStore(DSN)
    actor_ref, work_ref = refs("response-loss")
    declare_actor(store, actor_ref)
    store.create_work(
        WorkCreateInput(
            work_ref=work_ref,
            kind="task",
            actor_ref=actor_ref,
            initial_snapshot=snapshot("r1"),
        ),
        client_request_id=f"create:{work_ref}",
    )
    first = store.commit_snapshot(
        work_ref,
        expected_revision=1,
        snapshot=snapshot("r2"),
        actor_ref=actor_ref,
        client_request_id=f"commit-a:{work_ref}",
    )
    replay = store.commit_snapshot(
        work_ref,
        expected_revision=1,
        snapshot=snapshot("r2"),
        actor_ref=actor_ref,
        client_request_id=f"commit-b:{work_ref}",
    )
    assert first["revision"] == replay["revision"] == 2
    assert replay["admission"] == "existing"


def test_attention_change_clock_serializes_commit_order_and_rollback_has_no_hole() -> None:
    import threading
    import time

    import psycopg

    assert DSN is not None
    conn_a = psycopg.connect(DSN)
    started = threading.Event()
    try:
        seq_a = int(conn_a.execute("SELECT swf_next_change_sequence()").fetchone()[0])

        def allocate_b() -> int:
            with psycopg.connect(DSN) as conn_b:
                started.set()
                value = int(conn_b.execute("SELECT swf_next_change_sequence()").fetchone()[0])
                conn_b.commit()
                return value

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(allocate_b)
            assert started.wait(timeout=2)
            time.sleep(0.05)
            assert future.done() is False
            conn_a.rollback()
            seq_b = future.result(timeout=2)
        assert seq_b == seq_a
    finally:
        conn_a.close()


def test_attention_first_ack_concurrency_cannot_regress_cursor() -> None:
    import threading

    import psycopg

    assert DSN is not None
    actor_ref = f"actor:agent:attention-cursor-race:{uuid4().hex}"
    barrier = threading.Barrier(2)
    low, high = 41, 73

    with psycopg.connect(DSN) as setup:
        setup.execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES (%s,'agent')",
            (actor_ref,),
        )
        setup.commit()

    def ack(cursor: int) -> int | None:
        with psycopg.connect(DSN) as conn:
            current = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s FOR UPDATE",
                (actor_ref,),
            ).fetchone()
            assert current is None
            barrier.wait(timeout=5)
            row = conn.execute(
                "INSERT INTO attention_cursors(actor_ref,cursor) VALUES (%s,%s) "
                "ON CONFLICT (actor_ref) DO UPDATE "
                "SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp() "
                "WHERE attention_cursors.cursor <= EXCLUDED.cursor "
                "RETURNING cursor",
                (actor_ref, cursor),
            ).fetchone()
            conn.commit()
            return None if row is None else int(row[0])

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(ack, (low, high)))
        with psycopg.connect(DSN) as verify:
            final = verify.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s",
                (actor_ref,),
            ).fetchone()
            assert final is not None
            assert int(final[0]) == high
        assert high in outcomes
    finally:
        with psycopg.connect(DSN) as cleanup:
            cleanup.execute("DELETE FROM attention_cursors WHERE actor_ref=%s", (actor_ref,))
            cleanup.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (actor_ref,))
            cleanup.commit()
