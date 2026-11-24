from pathlib import Path

import pytest

from ordivon_host_v2 import attention_store
from ordivon_host_v2.attention_sql import ATTENTION_DELTA_SQL
from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.collection_pagination import validate_max_bytes

ROOT = Path(__file__).parents[1]
ATTENTION = ROOT / "src" / "ordivon_host_v2" / "attention_store.py"
ATTENTION_QUERY = ROOT / "src" / "ordivon_host_v2" / "attention_sql.py"
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


def test_bounded_subscription_lateral_uses_existing_topic_space_change_indexes() -> None:
    # Each message has one immutable topic/space and subscriptions have a
    # natural-key uniqueness constraint, so the first K per followed target
    # cannot exclude any of the first K globally distinct message identities.
    sql = ATTENTION_DELTA_SQL
    assert sql.count("CROSS JOIN LATERAL") == 2
    assert sql.count("LIMIT %(limit)s") == 5  # 2 inner, 2 branch, 1 final
    assert "WHERE m.topic_ref=s.target_ref" in sql
    assert "WHERE m.space_ref=s.target_ref" in sql
    assert sql.count("m.change_sequence > s.change_sequence") >= 2
    # No replacement of the message identity GROUP BY or multi-reason fold.
    assert "GROUP BY mc.change_sequence,mc.message_ref,mc.topic_ref" in sql
    assert "bool_or(mc.mentioned)" in sql
    assert "bool_or(mc.replied_to_me)" in sql


class _Result:
    def __init__(self, *, one=None, all_rows=()):
        self.one = one
        self.all_rows = all_rows

    def fetchone(self):
        return self.one

    def fetchall(self):
        return list(self.all_rows)


class _AttentionConnection:
    """Minimal deterministic storage evidence for public-boundary unit tests.

    The disposable PG suite separately verifies actual SQL and MVCC behavior.
    """

    def __init__(self):
        self.inserted_cursors = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def transaction(self):
        return self

    def execute(self, query, params=None):
        if query.startswith("SET TRANSACTION"):
            return _Result()
        if "SELECT value FROM swf_change_clock" in query:
            return _Result(one={"value": 10})
        if "SELECT cursor FROM attention_cursors" in query:
            return _Result(one={"cursor": 7})
        if "INSERT INTO attention_cursors" in query:
            if params[1] < 7:
                return _Result()
            self.inserted_cursors.append(params[1])
            return _Result(one={"previous_cursor": 7, "cursor": params[1]})
        if query == ATTENTION_DELTA_SQL:
            return _Result(all_rows=[{
                "change_sequence": 8,
                "event_kind": "message",
                "source_ref": "message:example",
                "context_ref": "topic:example",
                "followed_work": False,
                "followed_space": False,
                "followed_topic": True,
                "mentioned": False,
                "replied_to_me": False,
                "own_participation": False,
                "own_coordination_intent": False,
                "navigation_kind": "topic",
                "navigation_ref": "topic:example",
            }])
        raise AssertionError(f"unexpected SQL operation: {str(query)[:90]}")


def test_attention_cursor_is_monotonic_and_horizon_bounded(monkeypatch) -> None:
    from ordivon_host_v2 import attention_store as module
    from ordivon_host_v2.errors import ConflictError

    db = _AttentionConnection()
    monkeypatch.setattr(AttentionStore, "_connect", lambda self: db)
    monkeypatch.setattr(AttentionStore, "_require_actor", staticmethod(lambda _db, _actor: None))
    monkeypatch.setattr(module, "claim_command_receipt", lambda *_: None)
    monkeypatch.setattr(module, "record_command_receipt", lambda *_: None)
    store = AttentionStore("postgresql://unused.invalid/host")
    with pytest.raises(ConflictError, match="beyond current change horizon"):
        store.ack("actor:agent:test", cursor=11, client_request_id="test-ahead")
    with pytest.raises(ConflictError, match="cannot move backwards"):
        store.ack("actor:agent:test", cursor=6, client_request_id="test-rewind")
    assert db.inserted_cursors == []
    committed = store.ack("actor:agent:test", cursor=8, client_request_id="test-valid")
    assert committed["previousCursor"] == 7
    assert committed["cursor"] == 8
    assert db.inserted_cursors == [8]


def test_attention_never_ranks(monkeypatch) -> None:
    db = _AttentionConnection()
    monkeypatch.setattr(AttentionStore, "_connect", lambda self: db)
    monkeypatch.setattr(AttentionStore, "_require_actor", staticmethod(lambda _db, _actor: None))
    projection = AttentionStore("postgresql://unused.invalid/host").delta(
        "actor:agent:test", after_sequence=7
    )
    assert projection["snapshotHighSequence"] == 10
    assert projection["rankingApplied"] is False
    assert projection["events"][0]["navigationRef"] == "topic:example"
    assert "priority" not in projection["events"][0]
    assert "ORDER BY change_sequence,event_kind,source_ref" in ATTENTION_DELTA_SQL


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

    monkeypatch.setattr(attention_store.psycopg, "connect", forbid_connection)
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

    monkeypatch.setattr(attention_store.psycopg, "connect", forbid_connection)
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

    monkeypatch.setattr(attention_store.psycopg, "connect", witnessed_connection)
    store = AttentionStore("postgresql://unused.invalid/host")
    kwargs = {"after_sequence": 1} if operation in {"delta", "reentry"} else {}
    with pytest.raises(ConnectionReached):
        getattr(store, operation)("actor:agent:test", limit=100, **kwargs)


def test_exact_valid_collection_byte_budget_is_accepted() -> None:
    validate_max_bytes(262144)
