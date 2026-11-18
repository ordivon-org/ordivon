"""R59: share Host Work/Space/Topic PG lookups without duplicating R58 ActorRef."""

from __future__ import annotations

from typing import Any

import pytest

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.errors import WorkNotFound
from ordivon_host_v2.references.actor_refs import ActorReferenceLookup, ActorReferenceRegistry
from ordivon_host_v2.references.record_refs import RecordReferenceLookup
from ordivon_host_v2.social_errors import SpaceNotFound, TopicNotFound
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_store import WorkStore


class FakeConnection:
    def __init__(self, row: dict[str, Any] | None):
        self.row = row
        self.query = ""
        self.params = ()

    def execute(self, query: str, params: tuple[str, ...]) -> FakeConnection:
        self.query, self.params = query, params
        return self

    def fetchone(self):
        return self.row


@pytest.mark.parametrize(
    ("method", "ref", "sql", "error"),
    [
        ("_require_work", "work:other", "works WHERE work_ref=%s", WorkNotFound),
        ("_require_space", "space:other", "spaces WHERE space_ref=%s", SpaceNotFound),
    ],
)
def test_shared_missing_record_errors_are_precise_and_parameterized(
    method: str, ref: str, sql: str, error: type[Exception]
) -> None:
    lookup = getattr(RecordReferenceLookup, method)
    exists = FakeConnection({"one": 1})
    assert lookup(exists, ref) is None
    assert sql in exists.query
    assert exists.params == (ref,)
    missing = FakeConnection(None)
    with pytest.raises(error):
        lookup(missing, ref)
    assert missing.params == (ref,)


def test_topic_lock_preserved_before_native_message_sequence() -> None:
    row = {"topic_ref": "topic:test", "space_ref": "space:test"}
    plain = FakeConnection(row)
    assert RecordReferenceLookup._require_topic(plain, "topic:test") == row
    assert "FOR NO KEY UPDATE" not in plain.query
    locked = FakeConnection(row)
    assert RecordReferenceLookup._require_topic(locked, "topic:test", for_no_key_update=True) == row
    assert locked.query.endswith("FOR NO KEY UPDATE")
    assert "FOR UPDATE" not in locked.query
    assert locked.params == ("topic:test",)
    with pytest.raises(TopicNotFound):
        RecordReferenceLookup._require_topic(FakeConnection(None), "topic:missing")


@pytest.mark.parametrize(
    ("kind", "target_sql", "missing"),
    [
        ("work", "works WHERE work_ref=%s", WorkNotFound),
        ("space", "spaces WHERE space_ref=%s", SpaceNotFound),
        ("topic", "topics WHERE topic_ref=%s", TopicNotFound),
    ],
)
def test_attention_target_sql_identifiers_are_constant_and_values_bound(
    kind: str, target_sql: str, missing: type[Exception]
) -> None:
    fake = FakeConnection(None)
    target = "ref:'; DROP TABLE works; --"
    with pytest.raises(missing):
        RecordReferenceLookup._require_target(fake, kind, target)
    assert target_sql in fake.query
    assert "DROP TABLE" not in fake.query
    assert fake.params == (target,)


def test_unknown_attention_target_cannot_construct_sql() -> None:
    fake = FakeConnection(None)
    with pytest.raises(ValueError, match="unsupported Host attention target kind"):
        RecordReferenceLookup._require_target(fake, "principal", "actor:user")
    assert fake.query == ""


def test_shared_record_lookup_preserves_r58_actorref_and_public_facades() -> None:
    assert WorkStore._require_work is SocialStore._require_work
    assert SocialStore._require_topic is RecordReferenceLookup._require_topic
    assert AttentionStore._require_target is RecordReferenceLookup._require_target
    assert WorkStore._require_actor is ActorReferenceLookup._require_actor
    assert SocialStore._require_actor is ActorReferenceLookup._require_actor
    assert AttentionStore._require_actor is ActorReferenceLookup._require_actor
    assert WorkStore.declare_actor is ActorReferenceRegistry.declare_actor
