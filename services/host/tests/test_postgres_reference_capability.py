"""Canonical Host references: a PG integrity capability, never an IAM grant."""

from __future__ import annotations

from typing import Any

import pytest

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.capabilities.postgres_references import PostgresReferenceIntegrity
from ordivon_host_v2.domain.actor_reference_commands import ActorReferenceCommands
from ordivon_host_v2.errors import ActorRefNotFound, WorkNotFound
from ordivon_host_v2.social_errors import SpaceNotFound, TopicNotFound
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_store import WorkStore


class FakeConnection:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row
        self.sql = ""
        self.params: tuple[str, ...] = ()

    def execute(self, sql: str, params: tuple[str, ...]) -> FakeConnection:
        self.sql = sql
        self.params = params
        return self

    def fetchone(self) -> dict[str, Any] | None:
        return self.row


@pytest.mark.parametrize(
    ("name", "value", "sql", "missing"),
    [
        ("_require_actor", "actor:existing", "actor_refs WHERE actor_ref=%s", ActorRefNotFound),
        ("_require_work", "work:existing", "works WHERE work_ref=%s", WorkNotFound),
        ("_require_space", "space:existing", "spaces WHERE space_ref=%s", SpaceNotFound),
    ],
)
def test_semantic_reference_checks_share_pg_lookup_without_grant(
    name: str, value: str, sql: str, missing: type[Exception]
) -> None:
    check = getattr(PostgresReferenceIntegrity, name)
    present = FakeConnection({"exists": 1})
    assert check(present, value) is None
    assert sql in present.sql
    assert present.params == (value,)

    absent = FakeConnection(None)
    with pytest.raises(missing):
        check(absent, value)
    assert absent.params == (value,)


def test_topic_lock_is_exact_and_opt_in_before_message_sequence_allocation() -> None:
    row = {"topic_ref": "topic:one", "space_ref": "space:one"}
    ordinary = FakeConnection(row)
    assert PostgresReferenceIntegrity._require_topic(ordinary, "topic:one") == row
    assert "FOR NO KEY UPDATE" not in ordinary.sql
    locked = FakeConnection(row)
    assert (
        PostgresReferenceIntegrity._require_topic(locked, "topic:one", for_no_key_update=True)
        == row
    )
    assert locked.sql.endswith("FOR NO KEY UPDATE")
    assert "FOR UPDATE" not in locked.sql
    assert locked.params == ("topic:one",)
    with pytest.raises(TopicNotFound):
        PostgresReferenceIntegrity._require_topic(FakeConnection(None), "topic:missing")


@pytest.mark.parametrize(
    ("kind", "column", "missing"),
    [
        ("work", "works WHERE work_ref=%s", WorkNotFound),
        ("space", "spaces WHERE space_ref=%s", SpaceNotFound),
        ("topic", "topics WHERE topic_ref=%s", TopicNotFound),
    ],
)
def test_attention_target_lookup_preserves_exact_error_and_bounded_sql(
    kind: str, column: str, missing: type[Exception]
) -> None:
    fake = FakeConnection(None)
    with pytest.raises(missing):
        PostgresReferenceIntegrity._require_target(fake, kind, "opaque:'; DROP TABLE x; --")
    assert column in fake.sql
    assert fake.params == ("opaque:'; DROP TABLE x; --",)
    assert "DROP TABLE" not in fake.sql


def test_bad_target_kind_never_constructs_sql() -> None:
    fake = FakeConnection(None)
    with pytest.raises(ValueError, match="unsupported Host attention target kind"):
        PostgresReferenceIntegrity._require_target(fake, "principal", "actor:owner")
    assert fake.sql == ""


def test_all_three_domain_stores_reuse_same_reference_capability() -> None:
    for owner in (WorkStore, SocialStore, AttentionStore):
        assert owner._require_actor is PostgresReferenceIntegrity._require_actor
    assert WorkStore._require_work is SocialStore._require_work
    assert SocialStore._require_topic is PostgresReferenceIntegrity._require_topic
    assert AttentionStore._require_target is PostgresReferenceIntegrity._require_target


def test_actor_ref_domain_command_retains_legacy_work_store_surface() -> None:
    # ActorRef remains a social reference even though legacy MCP exposes it
    # through WorkStore; this makes no claim about authenticated principals.
    assert WorkStore.declare_actor is ActorReferenceCommands.declare_actor
