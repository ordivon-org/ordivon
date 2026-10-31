from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from time import sleep
from uuid import uuid4

import psycopg
import pytest
from psycopg.types.json import Jsonb

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
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


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


def test_work_create_same_semantics_is_linearizable_under_parallel_requests() -> None:
    """One WorkRef, one durable winner: response loss or parallel retries cannot leak SQL."""
    assert DSN is not None
    store = WorkStore(DSN)
    actor, work = refs("create-cas")
    declare_actor(store, actor)
    payload = WorkCreateInput(
        work_ref=work,
        kind="investigation",
        actor_ref=actor,
        initial_snapshot=snapshot("same-semantics"),
    )
    barrier = Barrier(12)

    def create(index: int) -> str:
        barrier.wait(timeout=15)
        try:
            return store.create_work(
                payload, client_request_id=f"create:{work}:{index}"
            )["admission"]
        except Exception as error:
            return type(error).__name__

    with ThreadPoolExecutor(max_workers=12) as pool:
        actual = list(pool.map(create, range(12)))
    assert sorted(actual) == ["committed", *(["existing"] * 11)], actual
    assert store.get_work(work)["revision"] == 1


def test_work_create_parallel_incompatible_snapshots_conflict_as_domain_errors() -> None:
    """Different first snapshots have exactly one winner, no DB error leakage."""
    assert DSN is not None
    store = WorkStore(DSN)
    actor, work = refs("create-incompatible")
    declare_actor(store, actor)
    barrier = Barrier(2)

    def create(frontier: str) -> str:
        barrier.wait(timeout=15)
        try:
            result = store.create_work(
                WorkCreateInput(
                    work_ref=work,
                    kind="investigation",
                    actor_ref=actor,
                    initial_snapshot=snapshot(frontier),
                ),
                client_request_id=f"create:{work}:{frontier}",
            )
            return result["admission"]
        except ConflictError:
            return "conflict"
        except Exception as error:
            return type(error).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        actual = list(pool.map(create, ("first", "second")))
    assert sorted(actual) == ["committed", "conflict"], actual


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



def test_concurrent_reciprocal_work_relations_cannot_commit_cycle() -> None:
    """Two Agent writers cannot each validate on a stale graph then commit a cycle."""
    assert DSN is not None
    actor, a = refs("concurrent-cycle-a")
    _, b = refs("concurrent-cycle-b")

    class DelayedAfterCycleCheck(WorkStore):
        def _reject_cycle(self, conn, relation):
            super()._reject_cycle(conn, relation)
            # Two independent requests race after reading the same empty DAG.
            # The sleep is deliberately after the real SQL cycle check, not
            # a mock of the storage transaction or its visible contract.
            sleep(0.35)

    store = DelayedAfterCycleCheck(DSN)
    declare_actor(store, actor)
    for ref in (a, b):
        store.create_work(
            WorkCreateInput(
                work_ref=ref,
                kind="task",
                actor_ref=actor,
                initial_snapshot=snapshot("open"),
            ),
            client_request_id=f"create:{ref}",
        )
    barrier = Barrier(2)

    def add_edge(edge):
        source, target = edge
        barrier.wait(timeout=5)
        try:
            store.add_relation(
                WorkRelationInput(
                    source_work_ref=source,
                    relation=WorkRelationKind.PARENT_OF,
                    target_work_ref=target,
                    actor_ref=actor,
                ),
                client_request_id=f"rel:{source}:{target}",
            )
            return "committed"
        except ConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(add_edge, ((a, b), (b, a))))
    assert outcomes == ["committed", "conflict"]

    # Query the native persistent relation directly: do not prove the graph
    # with a production read facade that has no real consumer.
    with psycopg.connect(DSN) as conn:
        edges = conn.execute(
            "SELECT source_work_ref,target_work_ref FROM work_relations "
            "WHERE source_work_ref=%s OR target_work_ref=%s",
            (a, a),
        ).fetchall()
    assert len(edges) == 1

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

    second = resumed["messages"][1]
    exact = social.get_message(second_ref, expected_digest=second["messageDigest"])
    assert exact["messageRef"] == second_ref
    assert exact["body"] == "reply"
    assert exact["messageDigest"] == second["messageDigest"]
    assert exact["truthBoundary"].startswith("exact durable Host message projection")

    with pytest.raises(ConflictError, match="message digest mismatch"):
        social.get_message(second_ref, expected_digest="sha256:" + ("0" * 64))


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


def test_topic_message_identity_waits_for_real_pg_topic_no_key_update_lock() -> None:
    """A real independent PG writer cannot allocate a visible topic message early.

    The lock held here is intentionally FOR NO KEY UPDATE, compatible with
    messages' FK KEY SHARE. Without the Host's explicit same-topic row fence,
    the post can commit while the other transaction still owns the topic.
    """
    import threading
    from time import monotonic

    assert DSN is not None
    token = uuid4().hex
    actor = f"actor:agent:topic-prefix:{token}"
    space_ref = f"space:topic-prefix:{token}"
    topic_ref = f"topic:topic-prefix:{token}"
    msg_ref = f"message:topic-prefix:{token}"
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    declare_actor(work, actor)
    social.create_space(
        SpaceInput(space_ref=space_ref, actor_ref=actor, purpose="topic prefix lock"),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, actor_ref=actor, title="race"),
        client_request_id=f"topic:{topic_ref}",
    )
    payload = MessageInput(
        message_ref=msg_ref,
        client_request_id=f"message:{msg_ref}",
        space_ref=space_ref,
        topic_ref=topic_ref,
        author_actor_ref=actor,
        message_kind=MessageKind.FINDING,
        body="topic lock source-level consumer witness",
        recorded_at_ms=123,
    )
    started = threading.Event()

    def post_message() -> dict:
        started.set()
        return social.post_message(payload)

    with psycopg.connect(DSN) as blocker, psycopg.connect(DSN) as observer:
        # Keep the independent topic owner transaction open. This lock does
        # NOT block ordinary FK KEY SHARE on message insertion.
        blocker.execute(
            "SELECT topic_ref FROM topics WHERE topic_ref=%s FOR NO KEY UPDATE",
            (topic_ref,),
        ).fetchone()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(post_message)
            assert started.wait(timeout=5)
            saw_blocked_actual_sql = False
            deadline = monotonic() + 6
            while monotonic() < deadline:
                if future.done():
                    break
                row = observer.execute(
                    "SELECT EXISTS("
                    "SELECT 1 FROM pg_stat_activity "
                    "WHERE pid <> pg_backend_pid() AND datname=current_database() "
                    "AND wait_event_type='Lock' AND query LIKE %s)",
                    ("%FROM topics WHERE topic_ref=% FOR NO KEY UPDATE%",),
                ).fetchone()
                if row is not None and row[0]:
                    saw_blocked_actual_sql = True
                    break
                sleep(0.03)
            assert saw_blocked_actual_sql, "real Host writer did not wait on the topic row fence"
            assert not future.done(), "message was admitted before topic owner released its lock"
            blocker.commit()
            admitted = future.result(timeout=6)

    assert admitted["admission"] == "committed"
    assert social.get_message(msg_ref)["messageRef"] == msg_ref
    assert [m["messageRef"] for m in social.resume_topic(topic_ref)["messages"]] == [msg_ref]


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


def test_desired_state_membership_can_be_reasserted_after_inverse_transition() -> None:
    """Same logical SET payload must work again after an intervening inverse state change."""
    import psycopg

    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    actor_ref, _ = refs("desired-state-cycle")
    declare_actor(work, actor_ref)
    token = uuid4().hex
    space_ref = f"space:desired-state-cycle:{token}"
    topic_ref = f"topic:desired-state-cycle:{token}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="desired-state cycle", actor_ref=actor_ref),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, title="cycle", actor_ref=actor_ref),
        client_request_id=f"topic:{topic_ref}",
    )

    same_join_request = f"join:{space_ref}:{actor_ref}"
    social.set_participation(
        space_ref=space_ref,
        actor_ref=actor_ref,
        standing=ParticipationStanding.JOINED,
        client_request_id=same_join_request,
    )
    with psycopg.connect(DSN) as conn:
        first_participation_sequence = int(
            conn.execute(
                "SELECT change_sequence FROM participations WHERE space_ref=%s AND actor_ref=%s",
                (space_ref, actor_ref),
            ).fetchone()[0]
        )
    social.set_participation(
        space_ref=space_ref,
        actor_ref=actor_ref,
        standing=ParticipationStanding.JOINED,
        client_request_id=same_join_request,
    )
    with psycopg.connect(DSN) as conn:
        assert int(
            conn.execute(
                "SELECT change_sequence FROM participations WHERE space_ref=%s AND actor_ref=%s",
                (space_ref, actor_ref),
            ).fetchone()[0]
        ) == first_participation_sequence
    social.set_participation(
        space_ref=space_ref,
        actor_ref=actor_ref,
        standing=ParticipationStanding.LEFT,
        client_request_id=f"leave:{space_ref}:{actor_ref}",
    )
    social.set_participation(
        space_ref=space_ref,
        actor_ref=actor_ref,
        standing=ParticipationStanding.JOINED,
        client_request_id=same_join_request,
    )
    participation = next(
        row for row in social.get_space(space_ref)["participants"] if row["actorRef"] == actor_ref
    )
    assert participation["standing"] == "joined"

    same_follow_request = f"follow:{topic_ref}:{actor_ref}"
    first_follow = attention.follow(
        actor_ref=actor_ref,
        target_kind="topic",
        target_ref=topic_ref,
        client_request_id=same_follow_request,
    )
    replay_follow = attention.follow(
        actor_ref=actor_ref,
        target_kind="topic",
        target_ref=topic_ref,
        client_request_id=same_follow_request,
    )
    assert first_follow["admission"] == "committed"
    assert replay_follow["admission"] == "existing"
    assert replay_follow["changeSequence"] == first_follow["changeSequence"]
    attention.unfollow(
        actor_ref=actor_ref,
        target_kind="topic",
        target_ref=topic_ref,
        client_request_id=f"unfollow:{topic_ref}:{actor_ref}",
    )
    refollow = attention.follow(
        actor_ref=actor_ref,
        target_kind="topic",
        target_ref=topic_ref,
        client_request_id=same_follow_request,
    )
    assert refollow["admission"] == "committed"
    assert refollow["changeSequence"] > first_follow["changeSequence"]
    listed = attention.list_subscriptions(actor_ref, target_kind="topic")
    assert [row["targetRef"] for row in listed["subscriptions"]] == [topic_ref]


def test_r2_attention_empty_interval_advances_to_snapshot_horizon() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    actor_a, _ = refs("r2-horizon-a")
    actor_b, _ = refs("r2-horizon-b")
    declare_actor(work, actor_a)
    declare_actor(work, actor_b)
    baseline = attention.delta(actor_a, after_sequence=0, limit=500)["snapshotHighSequence"]

    space_ref = f"space:r2-unrelated:{uuid4().hex}"
    topic_ref = f"topic:r2-unrelated:{uuid4().hex}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="unrelated", actor_ref=actor_b),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, title="unrelated", actor_ref=actor_b),
        client_request_id=f"topic:{topic_ref}",
    )
    message_ref = f"message:{uuid4().hex}"
    social.post_message(
        MessageInput(
            message_ref=message_ref,
            client_request_id=f"post:{message_ref}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor_b,
            body="not for actor a",
            recorded_at_ms=1,
        )
    )

    delta = attention.delta(actor_a, after_sequence=baseline, limit=100)
    assert delta["events"] == []
    assert delta["hasMore"] is False
    assert delta["snapshotHighSequence"] > baseline
    assert delta["nextAfterSequence"] == delta["snapshotHighSequence"]


def test_r2_attention_nonfinal_page_never_jumps_over_relevant_event() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    actor, _ = refs("r2-page")
    declare_actor(work, actor)
    space_ref = f"space:r2-page:{uuid4().hex}"
    topic_ref = f"topic:r2-page:{uuid4().hex}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="paging", actor_ref=actor),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, title="paging", actor_ref=actor),
        client_request_id=f"topic:{topic_ref}",
    )
    attention.follow(
        actor_ref=actor,
        target_kind="topic",
        target_ref=topic_ref,
        client_request_id=f"follow:{actor}:{topic_ref}",
    )
    baseline = attention.delta(actor, after_sequence=0, limit=500)["snapshotHighSequence"]
    for index in range(2):
        message_ref = f"message:{uuid4().hex}"
        social.post_message(
            MessageInput(
                message_ref=message_ref,
                client_request_id=f"post:{message_ref}",
                space_ref=space_ref,
                topic_ref=topic_ref,
                author_actor_ref=actor,
                body=f"page {index}",
                recorded_at_ms=index + 1,
            )
        )

    first = attention.delta(actor, after_sequence=baseline, limit=1)
    assert first["hasMore"] is True
    assert len(first["events"]) == 1
    assert first["nextAfterSequence"] == first["events"][0]["changeSequence"]
    assert first["nextAfterSequence"] < first["snapshotHighSequence"]

    second = attention.delta(actor, after_sequence=first["nextAfterSequence"], limit=1)
    assert len(second["events"]) == 1
    assert second["events"][0]["changeSequence"] > first["nextAfterSequence"]
    assert second["hasMore"] is False
    assert second["nextAfterSequence"] == second["snapshotHighSequence"]


def test_r2_topic_cursor_relation_readback_reasons_and_reentry() -> None:
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)
    actor_a, _ = refs("r2-reentry-a")
    actor_b, _ = refs("r2-reentry-b")
    declare_actor(work, actor_a)
    declare_actor(work, actor_b)
    space_ref = f"space:r2-reentry:{uuid4().hex}"
    topic_ref = f"topic:r2-reentry:{uuid4().hex}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="reentry", actor_ref=actor_a),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, title="reentry", actor_ref=actor_a),
        client_request_id=f"topic:{topic_ref}",
    )
    attention.follow(
        actor_ref=actor_a,
        target_kind="topic",
        target_ref=topic_ref,
        client_request_id=f"follow:{actor_a}:{topic_ref}",
    )
    parent_ref = f"message:{uuid4().hex}"
    parent = social.post_message(
        MessageInput(
            message_ref=parent_ref,
            client_request_id=f"post:{parent_ref}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor_a,
            body="parent",
            recorded_at_ms=1,
        )
    )
    cursor0 = social.get_topic_cursor(actor_ref=actor_a, topic_ref=topic_ref)
    assert cursor0["cursor"] == 0
    ack_parent = social.ack_topic_cursor(
        actor_ref=actor_a,
        topic_ref=topic_ref,
        cursor=parent["sequence"],
        client_request_id=f"topic-ack:{actor_a}:{parent['sequence']}",
    )
    assert ack_parent["cursor"] == parent["sequence"]
    baseline = attention.delta(actor_a, after_sequence=0, limit=500)["snapshotHighSequence"]

    reply_ref = f"message:{uuid4().hex}"
    reply = social.post_message(
        MessageInput(
            message_ref=reply_ref,
            client_request_id=f"post:{reply_ref}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor_b,
            message_kind=MessageKind.FINDING,
            body="reply with mention",
            recorded_at_ms=2,
        )
    )
    social.add_message_relation(
        MessageRelationInput(
            source_message_ref=reply_ref,
            relation=MessageRelationKind.REPLY_TO,
            target_ref=parent_ref,
            actor_ref=actor_b,
        ),
        client_request_id=f"reply:{reply_ref}",
    )
    social.add_message_relation(
        MessageRelationInput(
            source_message_ref=reply_ref,
            relation=MessageRelationKind.MENTIONS,
            target_ref=actor_a,
            actor_ref=actor_b,
        ),
        client_request_id=f"mention:{reply_ref}",
    )

    outgoing = social.list_message_relations(reply_ref, direction="outgoing")
    assert {row["relation"] for row in outgoing["relations"]} == {"reply_to", "mentions"}
    incoming = social.list_message_relations(parent_ref, direction="incoming")
    assert any(
        row["sourceMessageRef"] == reply_ref and row["relation"] == "reply_to"
        for row in incoming["relations"]
    )

    delta = attention.delta(actor_a, after_sequence=baseline, limit=100)
    message_events = [row for row in delta["events"] if row["eventKind"] == "message"]
    assert message_events
    reasons = set(message_events[0]["reasons"])
    assert {"followed_topic", "mentioned", "replied_to_me"} <= reasons
    assert message_events[0]["navigationKind"] == "topic"
    assert message_events[0]["navigationRef"] == topic_ref

    reentry = attention.reentry(actor_a, after_sequence=baseline, limit=100)
    item = next(row for row in reentry["items"] if row["navigationRef"] == topic_ref)
    assert reentry["rankingApplied"] is False
    assert item["resumeAfterSequence"] == parent["sequence"]
    assert {"followed_topic", "mentioned", "replied_to_me"} <= set(item["reasons"])

    resumed = social.resume_topic(topic_ref, after_sequence=item["resumeAfterSequence"])
    assert [row["messageRef"] for row in resumed["messages"]] == [reply_ref]
    social.ack_topic_cursor(
        actor_ref=actor_a,
        topic_ref=topic_ref,
        cursor=reply["sequence"],
        client_request_id=f"topic-ack:{actor_a}:{reply['sequence']}",
    )
    assert (
        SocialStore(DSN).get_topic_cursor(actor_ref=actor_a, topic_ref=topic_ref)["cursor"]
        == reply["sequence"]
    )
    with pytest.raises(ConflictError, match="backwards"):
        social.ack_topic_cursor(
            actor_ref=actor_a,
            topic_ref=topic_ref,
            cursor=parent["sequence"],
            client_request_id=f"topic-back:{uuid4().hex}",
        )
    with pytest.raises(ConflictError, match="beyond"):
        social.ack_topic_cursor(
            actor_ref=actor_a,
            topic_ref=topic_ref,
            cursor=reply["sequence"] + 1,
            client_request_id=f"topic-beyond:{uuid4().hex}",
        )


def test_r2_message_page_respects_canonical_byte_budget() -> None:
    assert DSN is not None
    from ordivon_host_v2.canonical import canonical_bytes

    work = WorkStore(DSN)
    social = SocialStore(DSN)
    actor, _ = refs("r2-bytes")
    declare_actor(work, actor)
    space_ref = f"space:r2-bytes:{uuid4().hex}"
    topic_ref = f"topic:r2-bytes:{uuid4().hex}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="bytes", actor_ref=actor),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, title="bytes", actor_ref=actor),
        client_request_id=f"topic:{topic_ref}",
    )
    for index in range(2):
        message_ref = f"message:{uuid4().hex}"
        social.post_message(
            MessageInput(
                message_ref=message_ref,
                client_request_id=f"post:{message_ref}",
                space_ref=space_ref,
                topic_ref=topic_ref,
                author_actor_ref=actor,
                body=("x" * 65_500) + str(index),
                recorded_at_ms=index + 1,
            )
        )
    page = social.resume_topic(topic_ref, limit=2, max_bytes=131_072)
    assert len(page["messages"]) == 1
    assert page["hasMore"] is True
    assert len(canonical_bytes(page)) <= 131_072


def test_r2_schema_indexes_and_cursor_table_exist() -> None:
    assert DSN is not None
    import psycopg

    expected_indexes = {
        "work_snapshot_target_change_idx",
        "work_relation_source_change_idx",
        "work_relation_target_change_idx",
        "participation_actor_change_idx",
        "topic_space_change_idx",
        "message_topic_change_idx",
        "message_space_change_idx",
        "message_author_ref_idx",
        "message_relation_target_change_idx",
    }
    with psycopg.connect(DSN) as conn:
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT indexname FROM pg_indexes WHERE schemaname=current_schema()"
            ).fetchall()
        }
        assert expected_indexes <= indexes
        assert conn.execute(
            "SELECT to_regclass('topic_consumption_cursors') IS NOT NULL"
        ).fetchone()[0]
        assert (
            conn.execute("SELECT schema_version FROM host_v2_schema WHERE singleton").fetchone()[0]
            == 10
        )

def test_work_read_rejects_postgres_modified_snapshot_payload() -> None:
    """A persisted Work payload edit must be rejected at each native read, not at doctor."""
    assert DSN is not None
    store = WorkStore(DSN)
    actor, work = refs("snapshot-digest-corrupt")
    declare_actor(store, actor)
    store.create_work(
        WorkCreateInput(work_ref=work, kind="investigation", actor_ref=actor,
                        initial_snapshot=snapshot("prior-attested")),
        client_request_id=f"create:{work}",
    )
    expected = store.get_work(work)
    forged = dict(expected["snapshot"])
    forged["objective"] = "unattested hostile or disk-corrupted snapshot"
    with psycopg.connect(DSN) as conn:
        conn.execute(
            "UPDATE work_snapshots SET payload=%s WHERE work_ref=%s AND revision=1",
            (Jsonb(forged), work),
        )
    with pytest.raises(RuntimeError, match="snapshot payload digest differs"):
        store.get_work(work)


def test_work_read_rejects_postgres_modified_current_pointer_digest() -> None:
    """An inconsistent current Work digest pointer cannot pass through readback."""
    assert DSN is not None
    store = WorkStore(DSN)
    actor, work = refs("work-current-pointer-corrupt")
    declare_actor(store, actor)
    store.create_work(
        WorkCreateInput(work_ref=work, kind="investigation", actor_ref=actor,
                        initial_snapshot=snapshot("prior-pointer")),
        client_request_id=f"create:{work}",
    )
    assert store.get_work(work)["revision"] == 1
    with psycopg.connect(DSN) as conn:
        conn.execute(
            "UPDATE works SET current_snapshot_digest=%s WHERE work_ref=%s",
            ("sha256:" + "0" * 64, work),
        )
    with pytest.raises(RuntimeError, match="current Work snapshot pointer digest differs"):
        store.get_work(work)



def test_reply_relation_must_point_to_earlier_committed_message() -> None:
    """A later reply is causal; self/backward replies must not form loops."""
    assert DSN is not None
    work = WorkStore(DSN)
    social = SocialStore(DSN)
    actor, _ = refs("reply-order")
    declare_actor(work, actor)
    space_ref = f"space:reply-order:{uuid4().hex}"
    topic_ref = f"topic:reply-order:{uuid4().hex}"
    social.create_space(
        SpaceInput(space_ref=space_ref, purpose="causal-replies", actor_ref=actor),
        client_request_id=f"space:{space_ref}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic_ref, space_ref=space_ref, title="causal", actor_ref=actor),
        client_request_id=f"topic:{topic_ref}",
    )
    earlier = f"message:{uuid4().hex}"
    later = f"message:{uuid4().hex}"
    first = social.post_message(
        MessageInput(
            message_ref=earlier,
            client_request_id=f"post:{earlier}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor,
            body="original",
            recorded_at_ms=2,
        )
    )
    second = social.post_message(
        MessageInput(
            message_ref=later,
            client_request_id=f"post:{later}",
            space_ref=space_ref,
            topic_ref=topic_ref,
            author_actor_ref=actor,
            body="reply",
            recorded_at_ms=1,  # client clock order is irrelevant
        )
    )
    assert second["sequence"] > first["sequence"]
    valid = social.add_message_relation(
        MessageRelationInput(
            source_message_ref=later,
            relation=MessageRelationKind.REPLY_TO,
            target_ref=earlier,
            actor_ref=actor,
        ),
        client_request_id=f"valid-reply:{later}",
    )
    assert valid["admission"] == "committed"

    for source, target in ((earlier, earlier), (earlier, later), (later, later)):
        with pytest.raises(ConflictError, match="earlier message"):
            social.add_message_relation(
                MessageRelationInput(
                    source_message_ref=source,
                    relation=MessageRelationKind.REPLY_TO,
                    target_ref=target,
                    actor_ref=actor,
                ),
                client_request_id=f"invalid-reply:{source}:{target}",
            )

    # References are deliberately NOT a causal reply relation.
    retro_reference = social.add_message_relation(
        MessageRelationInput(
            source_message_ref=earlier,
            relation=MessageRelationKind.REFERENCES,
            target_ref=later,
            actor_ref=actor,
        ),
        client_request_id=f"backward-reference:{earlier}",
    )
    assert retro_reference["admission"] == "committed"
    actual = social.list_message_relations(earlier, direction="outgoing")
    assert not any(row["relation"] == "reply_to" for row in actual["relations"])
    assert any(row["relation"] == "references" for row in actual["relations"])
