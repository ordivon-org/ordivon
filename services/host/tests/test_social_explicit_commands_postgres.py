"""Public Social commands compose exactly one native transaction and shared refs."""

from __future__ import annotations

import os
from contextlib import nullcontext
from uuid import uuid4

import pytest
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.coordination_inputs import CoordinationIntentInput
from ordivon_host_v2.errors import ActorRefNotFound, WorkNotFound
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_errors import SpaceNotFound, TopicNotFound
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


@pytest.mark.parametrize("pooled", [False, True])
def test_social_commands_compose_single_checkout_and_rollback(pooled):
    assert DSN
    token = uuid4().hex
    actor = f"actor:agent:compose-command:{token}"
    space, topic, message, intent = (
        f"{kind}:compose-command:{token}" for kind in ("space", "topic", "message", "intent")
    )
    ActorReferenceStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )

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
        store = CountingCheckout(DSN, pool=native_pool)

        def one(fn):
            before = store.count
            result = fn()
            assert store.count == before + 1
            return result

        def rejected(fn, error):
            before = store.count
            with pytest.raises(error):
                fn()
            assert store.count == before + 1

        payload = SpaceInput(space_ref=space, purpose="composed commands", actor_ref=actor)
        bad_actor = payload.model_copy(update={"actor_ref": f"{actor}:missing"})
        create = lambda: store.create_space(payload, client_request_id=f"space:{token}")
        rejected(
            lambda: store.create_space(bad_actor, client_request_id=f"space:{token}"),
            ActorRefNotFound,
        )
        first = one(create)
        assert first["admission"] == "committed"
        assert one(create) == {**first, "admission": "existing"}

        join = lambda: store.set_participation(
            space_ref=space,
            actor_ref=actor,
            standing=ParticipationStanding.JOINED,
            client_request_id=f"join:{token}",
        )
        rejected(
            lambda: store.set_participation(
                space_ref=f"{space}:missing",
                actor_ref=actor,
                standing=ParticipationStanding.JOINED,
                client_request_id=f"join:{token}",
            ),
            SpaceNotFound,
        )
        assert one(join)["standing"] == "joined"

        topic_input = TopicInput(
            topic_ref=topic, space_ref=space, title="commands", actor_ref=actor
        )
        create_topic = lambda: store.create_topic(topic_input, client_request_id=f"topic:{token}")
        rejected(
            lambda: store.create_topic(
                topic_input.model_copy(update={"space_ref": f"{space}:missing"}),
                client_request_id=f"topic:{token}",
            ),
            SpaceNotFound,
        )
        first_topic = one(create_topic)
        assert first_topic["admission"] == "committed"
        assert one(create_topic) == {**first_topic, "admission": "existing"}

        msg = MessageInput(
            message_ref=message,
            client_request_id=f"msg:{token}",
            space_ref=space,
            topic_ref=topic,
            author_actor_ref=actor,
            body="one transaction",
            recorded_at_ms=1,
        )
        rejected(
            lambda: store.post_message(msg.model_copy(update={"topic_ref": f"{topic}:missing"})),
            TopicNotFound,
        )
        posted = one(lambda: store.post_message(msg))
        assert one(lambda: store.post_message(msg)) == {**posted, "admission": "existing"}

        relation = MessageRelationInput(
            source_message_ref=message,
            relation=MessageRelationKind.MENTIONS,
            target_ref=actor,
            actor_ref=actor,
        )
        add_relation = lambda: store.add_message_relation(
            relation, client_request_id=f"relation:{token}"
        )
        rejected(
            lambda: store.add_message_relation(
                relation.model_copy(update={"target_ref": f"{actor}:missing"}),
                client_request_id=f"relation:{token}",
            ),
            ActorRefNotFound,
        )
        first_relation = one(add_relation)
        assert one(add_relation) == {**first_relation, "admission": "existing"}

        # Actor mentions require a real ActorRef, but a references edge is
        # intentionally a non-authoritative external reference.
        opaque = f"artifact:external:not-in-host:{token}"
        reference = relation.model_copy(
            update={
                "relation": MessageRelationKind.REFERENCES,
                "target_ref": opaque,
            }
        )
        added = one(
            lambda: store.add_message_relation(reference, client_request_id=f"reference:{token}")
        )
        assert added["targetRef"] == opaque
        relation_rows = one(lambda: store.list_message_relations(message))["relations"]
        assert {(row["relation"], row["targetRef"]) for row in relation_rows} == {
            ("mentions", actor),
            ("references", opaque),
        }

        ack = lambda: store.ack_topic_cursor(
            actor_ref=actor,
            topic_ref=topic,
            cursor=posted["sequence"],
            client_request_id=f"ack:{token}",
        )
        first_ack = one(ack)
        assert first_ack["cursor"] == posted["sequence"]
        assert one(ack) == {**first_ack, "admission": "existing"}

        original_topic = store.resume_topic(topic)["topic"]
        close = lambda: store.set_topic_state(
            topic_ref=topic,
            actor_ref=actor,
            state="closed",
            expected_state="open",
            expected_high_sequence=posted["sequence"],
            expected_change_sequence=original_topic["changeSequence"],
            client_request_id=f"close:{token}",
        )
        closed = one(close)
        assert closed["state"] == "closed"
        assert one(close) == {**closed, "admission": "existing"}

        declared = CoordinationIntentInput(
            intent_ref=intent,
            actor_ref=actor,
            subject_ref="subject:command-composition",
            operation="review",
            observed_at_ms=1,
        )
        declare = lambda: store.declare_intent(declared, client_request_id=f"intent:{token}")
        rejected(
            lambda: store.declare_intent(
                declared.model_copy(update={"work_ref": f"work:missing:{token}"}),
                client_request_id=f"intent:{token}",
            ),
            WorkNotFound,
        )
        first_intent = one(declare)
        assert first_intent["admission"] == "committed"
        assert one(declare) == {**first_intent, "admission": "existing"}
        assert (
            one(lambda: store.get_message(message, expected_digest=posted["messageDigest"]))[
                "messageRef"
            ]
            == message
        )
