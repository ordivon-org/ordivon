from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest

from ordivon_host_v2.canonical import canonical_digest
from ordivon_host_v2.social_attention import AttentionStore
from ordivon_host_v2.social_graph import ParticipationStanding, SpaceInput, TopicInput
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.social_work import ActorKind, ActorRefInput, WorkCreateInput, WorkSnapshotInput
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def snap(frontier: str) -> WorkSnapshotInput:
    return WorkSnapshotInput(objective="100-agent society acceptance", frontier=frontier)


def test_100_agent_30_work_15_space_100_topic_10k_message_society() -> None:
    assert DSN is not None
    token = uuid4().hex
    work_store = WorkStore(DSN)
    social = SocialStore(DSN)
    attention = AttentionStore(DSN)

    actors = [f"actor:agent:society:{token}:{i:03d}" for i in range(100)]
    for actor in actors:
        work_store.declare_actor(
            ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
            client_request_id=f"society:actor:{actor}",
        )

    works = [f"work:society:{token}:{i:02d}" for i in range(30)]
    for i, work_ref in enumerate(works):
        work_store.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind="task",
                actor_ref=actors[i % len(actors)],
                initial_snapshot=snap("open"),
            ),
            client_request_id=f"society:create:{work_ref}",
        )

    spaces = [f"space:society:{token}:{i:02d}" for i in range(15)]
    # Space 0 is the five-Agent long-Work collaboration surface.
    for i, space_ref in enumerate(spaces):
        subjects = [works[0]] if i == 0 else [works[(i * 2) % 30], works[(i * 2 + 1) % 30]]
        if i == 1:
            # Explicit cross-Work temporary team: three unrelated Work items, no inferred relation.
            subjects = [works[1], works[7], works[19]]
        social.create_space(
            SpaceInput(
                space_ref=space_ref,
                purpose=f"society-space-{i}",
                actor_ref=actors[i],
                subject_refs=subjects,
            ),
            client_request_id=f"society:space:{space_ref}",
        )

    for actor in actors[:5]:
        social.set_participation(
            space_ref=spaces[0],
            actor_ref=actor,
            standing=ParticipationStanding.JOINED,
            client_request_id=f"society:join:{spaces[0]}:{actor}",
        )
    # Dynamic regrouping: one member leaves the long-Work Space and joins the cross-Work Space.
    social.set_participation(
        space_ref=spaces[0],
        actor_ref=actors[4],
        standing=ParticipationStanding.LEFT,
        client_request_id=f"society:leave:{spaces[0]}:{actors[4]}",
    )
    social.set_participation(
        space_ref=spaces[1],
        actor_ref=actors[4],
        standing=ParticipationStanding.JOINED,
        client_request_id=f"society:regroup:{spaces[1]}:{actors[4]}",
    )

    topics: list[str] = []
    for i in range(100):
        space_ref = spaces[i % len(spaces)]
        topic_ref = f"topic:society:{token}:{i:03d}"
        topics.append(topic_ref)
        social.create_topic(
            TopicInput(
                topic_ref=topic_ref,
                space_ref=space_ref,
                title=f"topic-{i:03d}",
                actor_ref=actors[i % len(actors)],
            ),
            client_request_id=f"society:topic:{topic_ref}",
        )

    # Follow exactly one topic before bulk traffic. The inbox should project only that axis.
    watched_topic = topics[0]
    attention.follow(
        actor_ref=actors[0],
        target_kind="topic",
        target_ref=watched_topic,
        client_request_id=f"society:follow:{actors[0]}:{watched_topic}",
    )
    baseline = attention.delta(actors[0], after_sequence=0, limit=500)["snapshotHighSequence"]

    topic_space = {row["topic_ref"]: row["space_ref"] for row in _topic_rows(DSN, topics)}
    rows = []
    for i in range(10_000):
        topic_ref = topics[i % 100]
        message_ref = f"message:society:{token}:{i:05d}"
        author = actors[i % 100]
        body = f"society-message-{i:05d}"
        recorded = i + 1
        digest = canonical_digest(
            {
                "messageRef": message_ref,
                "spaceRef": topic_space[topic_ref],
                "topicRef": topic_ref,
                "authorActorRef": author,
                "messageKind": "note",
                "body": body,
                "recordedAtMs": recorded,
            }
        )
        rows.append(
            (
                message_ref,
                f"society:post:{token}:{i:05d}",
                topic_space[topic_ref],
                topic_ref,
                author,
                "note",
                body,
                digest,
                recorded,
            )
        )
    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO messages(message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,"
                "message_kind,body,message_digest,recorded_at_ms) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                rows,
            )
        conn.commit()

    delta = attention.delta(actors[0], after_sequence=baseline, limit=500)
    message_events = [row for row in delta["events"] if row["eventKind"] == "message"]
    assert len(message_events) == 100
    assert all(row["contextRef"] == watched_topic for row in message_events)
    assert delta["hasMore"] is False
    assert delta["rankingApplied"] is False

    long_space = social.get_space(spaces[0])
    standings = {row["actorRef"]: row["standing"] for row in long_space["participants"]}
    assert [standings[actors[i]] for i in range(4)] == ["joined"] * 4
    assert standings[actors[4]] == "left"
    regrouped = social.get_space(spaces[1])
    assert {works[1], works[7], works[19]} <= set(regrouped["subjectRefs"])
    assert not work_store.list_relations(works[1])["relations"]


def _topic_rows(dsn: str, topic_refs: list[str]) -> list[dict[str, str]]:
    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row) as conn:
        return conn.execute(
            "SELECT topic_ref,space_ref FROM topics WHERE topic_ref = ANY(%s) ORDER BY topic_ref",
            (topic_refs,),
        ).fetchall()
