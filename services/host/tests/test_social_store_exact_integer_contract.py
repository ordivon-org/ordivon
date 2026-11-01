"""Host R3 K03 typed SocialStore boundary: only exact bounded int reaches SQL.

Consumer-side CEGAR oracle, reusing existing WorkStore and AttentionStore
validation semantics. No separate schema registry, dispatch engine or solver.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest

from ordivon_host_v2 import social_store
from ordivon_host_v2.social_store import SocialStore

INVALID_INTEGERS = (
    True, False, 1.0, 100.0, float("nan"), float("inf"),
    Decimal("1"), Decimal("NaN"), Fraction(1, 1), "1",
)
# Each request exercises one public SQL/projection boundary, without a database.
LIMIT_CONSUMERS = (
    ("list_message_relations", ("message:test",), {}, "limit"),
    ("get_space", ("space:test",), {}, "participant_limit"),
    ("get_space", ("space:test",), {}, "topic_limit"),
    ("list_space_subjects", ("space:test",), {}, "limit"),
    ("list_participations", ("space:test",), {}, "limit"),
    ("list_topics", ("space:test",), {}, "limit"),
    ("list_spaces", (), {}, "limit"),
    ("search_messages", ("needle",), {}, "limit"),
    ("resume_topic", ("topic:test",), {}, "limit"),
)
CURSOR_CONSUMERS = (
    ("list_message_relations", ("message:test",), "after_change_sequence"),
    ("search_messages", ("needle",), "before_sequence"),
    ("resume_topic", ("topic:test",), "after_sequence"),
)


@pytest.mark.parametrize("invalid", INVALID_INTEGERS)
@pytest.mark.parametrize("operation,args,extras,parameter", LIMIT_CONSUMERS)
def test_social_query_budget_must_be_exact_integer_before_sql(
    monkeypatch, invalid: object, operation: str, args: tuple[str, ...],
    extras: dict[str, object], parameter: str,
) -> None:
    def unexpected_connection(*_args, **_kwargs):
        raise AssertionError("invalid bounded query reached PostgreSQL")

    monkeypatch.setattr(social_store.psycopg, "connect", unexpected_connection)
    with pytest.raises(ValueError, match="limit"):
        getattr(SocialStore("postgresql://not-used/host"), operation)(
            *args, **extras, **{parameter: invalid}
        )


@pytest.mark.parametrize("invalid", INVALID_INTEGERS)
@pytest.mark.parametrize("operation,args,parameter", CURSOR_CONSUMERS)
def test_social_sequence_cursor_must_be_exact_integer_before_sql(
    monkeypatch, invalid: object, operation: str, args: tuple[str, ...],
    parameter: str,
) -> None:
    def unexpected_connection(*_args, **_kwargs):
        raise AssertionError("invalid query cursor reached PostgreSQL")

    monkeypatch.setattr(social_store.psycopg, "connect", unexpected_connection)
    with pytest.raises(ValueError, match=parameter):
        getattr(SocialStore("postgresql://not-used/host"), operation)(
            *args, **{parameter: invalid}
        )


@pytest.mark.parametrize("operation,args,extras,parameter", LIMIT_CONSUMERS)
def test_social_exact_integer_budget_reaches_normal_sql_boundary(
    monkeypatch, operation: str, args: tuple[str, ...],
    extras: dict[str, object], parameter: str,
) -> None:
    def expected_connection(*_args, **_kwargs):
        raise RuntimeError("SQL boundary reached with validated integer")

    monkeypatch.setattr(social_store.psycopg, "connect", expected_connection)
    with pytest.raises(RuntimeError, match="SQL boundary reached"):
        getattr(SocialStore("postgresql://not-used/host"), operation)(
            *args, **extras, **{parameter: 1}
        )


@pytest.mark.parametrize("operation,args,parameter", CURSOR_CONSUMERS)
def test_social_exact_integer_cursor_reaches_normal_sql_boundary(
    monkeypatch, operation: str, args: tuple[str, ...], parameter: str,
) -> None:
    def expected_connection(*_args, **_kwargs):
        raise RuntimeError("SQL boundary reached with validated integer")

    monkeypatch.setattr(social_store.psycopg, "connect", expected_connection)
    with pytest.raises(RuntimeError, match="SQL boundary reached"):
        getattr(SocialStore("postgresql://not-used/host"), operation)(
            *args, **{parameter: 1}
        )


@pytest.mark.parametrize("invalid", INVALID_INTEGERS)
def test_ack_topic_cursor_requires_exact_integer_before_receipt_or_sql(
    monkeypatch, invalid: object,
) -> None:
    def unexpected_connection(*_args, **_kwargs):
        raise AssertionError("invalid mutation cursor reached SQL/receipt")

    monkeypatch.setattr(social_store.psycopg, "connect", unexpected_connection)
    store = SocialStore("postgresql://not-used/host")
    with pytest.raises(ValueError, match="cursor"):
        store.ack_topic_cursor(
            actor_ref="actor:agent:test",
            topic_ref="topic:test",
            cursor=invalid,
            client_request_id="host-int-contract:invalid-ack",
        )


def test_ack_topic_cursor_accepts_exact_integer_to_sql_boundary(monkeypatch) -> None:
    def expected_connection(*_args, **_kwargs):
        raise RuntimeError("SQL boundary reached with validated integer")

    monkeypatch.setattr(social_store.psycopg, "connect", expected_connection)
    with pytest.raises(RuntimeError, match="SQL boundary reached"):
        SocialStore("postgresql://not-used/host").ack_topic_cursor(
            actor_ref="actor:agent:test",
            topic_ref="topic:test",
            cursor=0,
            client_request_id="host-int-contract:valid-ack",
        )


def test_host_search_preserves_cjk_literal_substring_and_english_fts(monkeypatch) -> None:
    """Agent retrieval must find a Chinese phrase embedded in a larger token.

    No test database is needed for checking the SQL and bound argument; a
    separate PostgreSQL consumer test checks the actual substring behavior.
    """
    observed: list[tuple[str, tuple[object, ...]]] = []

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def transaction(self):
            return self

        def execute(self, statement, parameters=None):
            if parameters is not None:
                observed.append((statement, parameters))
            return self

        def fetchall(self):
            return []

    monkeypatch.setattr(social_store.psycopg, "connect", lambda *_args, **_kw: FakeConnection())
    store = SocialStore("postgresql://not-used/host")
    for query, cjk in (("终端消费", True), ("LEGO", False), ("中文 LEGO", False)):
        observed.clear()
        result = store.search_messages(query)
        assert result["messages"] == []
        assert len(observed) == 1
        sql, args = observed[0]
        assert args[0] == query
        assert "strpos(body,%s)>0" in sql if cjk else "websearch_to_tsquery" in sql
        assert query not in sql  # No user query is interpolated into SQL text.
