from pathlib import Path

import pytest

from ordivon_host_v2 import social_attention
from ordivon_host_v2.attention_queries import ATTENTION_DELTA_SQL
from ordivon_host_v2.collection_pagination import validate_max_bytes
from ordivon_host_v2.social_attention import AttentionStore

ROOT = Path(__file__).parents[1]
ATTENTION = ROOT / "src" / "ordivon_host_v2" / "social_attention.py"
ATTENTION_QUERY = ROOT / "src" / "ordivon_host_v2" / "attention_queries.py"
MIGRATION = ROOT / "migrations" / "versions" / "0008_social_work_fabric_attention.py"


def test_attention_uses_owner_rows_not_attention_event_bus() -> None:
    migration = MIGRATION.read_text().lower()
    query = ATTENTION_DELTA_SQL.lower()
    assert "create table attention_events" not in migration
    assert "from work_snapshots" in query
    assert "from messages" in query
    assert "from coordination_intents" in query


def test_attention_is_actor_scoped_and_subscription_bounded() -> None:
    sql = ATTENTION_DELTA_SQL
    assert "subscriptions" in sql
    assert "actor_ref=%(actor_ref)s" in sql
    assert "target_kind='work'" in sql
    assert "target_kind='space'" in sql
    assert "target_kind='topic'" in sql


def test_attention_mentions_and_replies_route_without_global_scan() -> None:
    sql = ATTENTION_DELTA_SQL
    assert "mr.relation='mentions'" in sql
    assert "reply.relation='reply_to'" in sql
    assert "parent.author_actor_ref=%(actor_ref)s" in sql


def test_attention_cursor_is_monotonic_and_horizon_bounded() -> None:
    source = ATTENTION.read_text()
    assert "attention cursor cannot move backwards" in source
    assert "cannot acknowledge beyond current change horizon" in source
    assert "WHERE attention_cursors.cursor <= EXCLUDED.cursor" in source
    assert "RETURNING cursor" in source
    assert '"snapshotHighSequence"' in source


def test_attention_never_ranks() -> None:
    source = ATTENTION.read_text()
    assert '"rankingApplied": False' in source
    assert "ORDER BY change_sequence,event_kind,source_ref" in ATTENTION_DELTA_SQL
    assert "ORDER BY priority" not in source
    assert "ORDER BY score" not in source


def test_subscription_is_routing_preference_not_assignment() -> None:
    source = ATTENTION.read_text().lower()
    assert (
        "attention routing preference only; not assignment, priority, ownership, or authorization"
        in source
    )


def test_attention_change_clock_is_transactional_not_postgres_sequence() -> None:
    migration = MIGRATION.read_text().lower()
    source = ATTENTION.read_text().lower()
    assert "create sequence swf_change_sequence" not in migration
    assert "create table swf_change_clock" in migration
    assert "create function swf_next_change_sequence" in migration
    assert "update swf_change_clock" in migration
    assert "select value from swf_change_clock where singleton" in source


def test_subscription_horizon_does_not_replay_pre_follow_history() -> None:
    sql = ATTENTION_DELTA_SQL
    compact = "".join(sql.split())
    assert compact.count("change_sequence>s.change_sequence") >= 6


@pytest.mark.parametrize("limit", [True, False, 1.0, 100.0, "100"])
@pytest.mark.parametrize("operation", ["list_subscriptions", "delta", "reentry"])
def test_attention_limit_is_exact_integer_before_store_effect(
    monkeypatch, operation: str, limit: object
) -> None:
    def forbid_connection(*args, **kwargs):
        raise AssertionError("invalid limit must never reach PostgreSQL")

    monkeypatch.setattr(social_attention.psycopg, "connect", forbid_connection)
    store = AttentionStore("postgresql://unused.invalid/host")
    method = getattr(store, operation)
    extras = {"after_sequence": 1} if operation == "delta" else {}
    with pytest.raises(ValueError, match="limit"):
        method("actor:agent:test", limit=limit, **extras)


@pytest.mark.parametrize("sequence", [True, False, 1.0, 2.0, "1"])
@pytest.mark.parametrize("operation", ["delta", "reentry"])
def test_attention_cursor_is_exact_integer_before_store_effect(
    monkeypatch, operation: str, sequence: object
) -> None:
    def forbid_connection(*args, **kwargs):
        raise AssertionError("invalid attention cursor must never reach PostgreSQL")

    monkeypatch.setattr(social_attention.psycopg, "connect", forbid_connection)
    store = AttentionStore("postgresql://unused.invalid/host")
    with pytest.raises(ValueError, match="after_sequence"):
        getattr(store, operation)("actor:agent:test", after_sequence=sequence)


@pytest.mark.parametrize("invalid_max_bytes", [262144.0, 65536.0, "262144"])
def test_collection_byte_budget_requires_exact_integer(invalid_max_bytes: object) -> None:
    with pytest.raises(ValueError, match="max_bytes"):
        validate_max_bytes(invalid_max_bytes)


@pytest.mark.parametrize("operation", ["list_subscriptions", "delta", "reentry"])
def test_exact_valid_attention_limit_retains_native_owner_db_path(
    monkeypatch, operation: str
) -> None:
    class ConnectionReached(Exception):
        pass

    def witnessed_connection(*args, **kwargs):
        raise ConnectionReached("legal typed attention request reached natural owner")

    monkeypatch.setattr(social_attention.psycopg, "connect", witnessed_connection)
    store = AttentionStore("postgresql://unused.invalid/host")
    kwargs = {"after_sequence": 1} if operation in {"delta", "reentry"} else {}
    with pytest.raises(ConnectionReached):
        getattr(store, operation)("actor:agent:test", limit=100, **kwargs)


def test_exact_valid_collection_byte_budget_is_accepted() -> None:
    validate_max_bytes(262144)
