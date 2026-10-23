from pathlib import Path

import pytest

from ordivon_host_v2.social_graph import (
    CoordinationIntentInput,
    MessageInput,
    MessageKind,
    MessageRelationKind,
    SpaceInput,
)

ROOT = Path(__file__).parents[1]


def test_space_is_not_nested_under_work() -> None:
    value = SpaceInput(
        space_ref="space:storage-incident",
        purpose="cross-work storage incident collaboration",
        actor_ref="actor:agent:a17",
        subject_refs=["work:runtime", "work:storage", "resource:ext4.vhdx"],
    )
    dumped = value.model_dump(mode="json")
    assert "work_ref" not in dumped
    assert len(dumped["subject_refs"]) == 3


def test_space_subjects_are_unique() -> None:
    with pytest.raises(ValueError):
        SpaceInput(
            space_ref="space:x",
            purpose="x",
            actor_ref="actor:agent:a17",
            subject_refs=["work:x", "work:x"],
        )


def test_message_reply_is_relation_not_message_kind() -> None:
    assert "reply" not in {item.value for item in MessageKind}
    assert MessageRelationKind.REPLY_TO.value == "reply_to"


def test_message_has_explicit_space_topic_and_actor() -> None:
    message = MessageInput(
        message_ref="message:1",
        client_request_id="req:1",
        space_ref="space:paper2",
        topic_ref="topic:paper2:matching",
        author_actor_ref="actor:agent:a17",
        body="matching cut materialized",
        recorded_at_ms=1,
    )
    assert message.space_ref == "space:paper2"
    assert message.topic_ref == "topic:paper2:matching"


def test_coordination_intent_is_explicitly_bounded() -> None:
    intent = CoordinationIntentInput(
        intent_ref="intent:1",
        actor_ref="actor:agent:a17",
        subject_ref="resource:ext4.vhdx",
        operation="inspect",
        observed_at_ms=10,
        expires_at_ms=20,
    )
    intent.validate_window()
    with pytest.raises(ValueError):
        bad = intent.model_copy(update={"expires_at_ms": 10})
        bad.validate_window()


def test_social_graph_migration_does_not_reference_legacy_board_or_tasks() -> None:
    text = (
        ROOT / "migrations" / "versions" / "0007_social_work_fabric_social_graph.py"
    ).read_text()
    schema = text.split('_SCHEMA_V7_DELTA = r"""', 1)[1].split('"""', 1)[0]
    assert "REFERENCES tasks" not in schema
    assert "REFERENCES board_messages" not in schema
    assert "CREATE TABLE spaces" in schema
    assert "CREATE TABLE topics" in schema
    assert "CREATE TABLE messages" in schema
    assert "CREATE TABLE coordination_intents" in schema


def test_social_graph_schema_has_no_authority_priority_or_lock_fields() -> None:
    text = (
        (ROOT / "migrations" / "versions" / "0007_social_work_fabric_social_graph.py")
        .read_text()
        .lower()
    )
    for forbidden in (
        "priority",
        "winner",
        "vote_count",
        "effect_authority",
        "lock_owner",
        "lease_owner",
    ):
        assert forbidden not in text
