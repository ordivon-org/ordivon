"""Natural public Social read consumers retain one native read-only snapshot."""

from __future__ import annotations

import os
from contextlib import nullcontext
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.errors import ActorRefNotFound
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_errors import MessageNotFound, SpaceNotFound, TopicNotFound
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


@pytest.mark.parametrize("pooled", [False, True])
def test_social_reads_compose_native_checkout_and_read_only_snapshot(pooled, monkeypatch):
    assert DSN
    token = uuid4().hex
    actor = f"actor:agent:social-read:{token}"
    space, topic, message = (
        f"{kind}:social-read:{token}" for kind in ("space", "topic", "message")
    )
    subject = f"subject:social-read:{token}"
    ActorReferenceStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )
    writer = SocialStore(DSN)
    writer.create_space(
        SpaceInput(
            space_ref=space,
            purpose="read composition witness",
            actor_ref=actor,
            subject_refs=[subject],
        ),
        client_request_id=f"space:{token}",
    )
    writer.set_participation(
        space_ref=space,
        actor_ref=actor,
        standing=ParticipationStanding.JOINED,
        client_request_id=f"join:{token}",
    )
    writer.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="read composition", actor_ref=actor),
        client_request_id=f"topic:{token}",
    )
    posted = writer.post_message(
        MessageInput(
            message_ref=message,
            client_request_id=f"post:{token}",
            space_ref=space,
            topic_ref=topic,
            author_actor_ref=actor,
            body=f"read composition witness {token}",
            recorded_at_ms=1,
        )
    )
    original_execute = psycopg.Connection.execute
    snapshots = []

    def observed_execute(conn, query, *args, **kwargs):
        result = original_execute(conn, query, *args, **kwargs)
        if isinstance(query, str) and query.startswith("SET TRANSACTION"):
            isolation = original_execute(conn, "SHOW transaction_isolation").fetchone()
            readonly = original_execute(conn, "SHOW transaction_read_only").fetchone()
            snapshots.append(
                (id(conn), isolation["transaction_isolation"], readonly["transaction_read_only"])
            )
        return result

    class CountingCheckout(SocialStore):
        count = 0

        def _connect(self):
            self.count += 1
            return super()._connect()

    pool = (
        ConnectionPool(
            DSN, min_size=1, max_size=1, timeout=5, kwargs={"row_factory": dict_row}, open=False
        )
        if pooled
        else nullcontext(None)
    )
    with pool as native_pool:
        reader = CountingCheckout(DSN, pool=native_pool)
        monkeypatch.setattr(psycopg.Connection, "execute", observed_execute)
        reads = [
            lambda: reader.get_space(space)["spaceRef"] == space,
            lambda: reader.list_space_subjects(space)["subjectRefs"] == [subject],
            lambda: bool(reader.list_participations(space)["participants"]),
            lambda: any(
                row["spaceRef"] == space for row in reader.list_spaces(actor_ref=actor)["spaces"]
            ),
            lambda: any(row["topicRef"] == topic for row in reader.list_topics(space)["topics"]),
            lambda: (
                reader.resume_topic(topic)["messages"][0]["messageDigest"]
                == posted["messageDigest"]
            ),
            lambda: reader.get_topic_cursor(actor_ref=actor, topic_ref=topic)["cursor"] == 0,
            lambda: reader.list_message_relations(message)["relations"] == [],
            lambda: (
                reader.get_message(message, expected_digest=posted["messageDigest"])["messageRef"]
                == message
            ),
            lambda: (
                reader.search_messages(token, space_ref=space, topic_ref=topic)["messages"][0][
                    "messageRef"
                ]
                == message
            ),
        ]
        for i, read in enumerate(reads, 1):
            assert read()
            assert reader.count == i
            assert len(snapshots) == i
            assert snapshots[-1][1:] == ("repeatable read", "on")
        for fn, error in [
            (lambda: reader.list_spaces(actor_ref=f"{actor}:missing"), ActorRefNotFound),
            (lambda: reader.list_topics(f"{space}:missing"), SpaceNotFound),
            (lambda: reader.resume_topic(f"{topic}:missing"), TopicNotFound),
            (lambda: reader.get_message(f"{message}:missing"), MessageNotFound),
        ]:
            before = reader.count
            with pytest.raises(error):
                fn()
            assert reader.count == before + 1
            assert len(snapshots) == reader.count
            assert snapshots[-1][1:] == ("repeatable read", "on")
        # The pooled connection remains usable after the typed failures.
        assert reader.get_message(message)["messageDigest"] == posted["messageDigest"]
        assert len(snapshots) == reader.count
