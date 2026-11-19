"""Topic Cursor is one PG-bound consumption LEGO shared by Social and Attention.

This tests the negative paths and the information-hiding boundary without
requiring an additional service or a second cursor database. The existing
PG18 suite covers concurrency, MVCC and real MCP behaviors.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.topic_cursor_records import (
    ack_topic_cursor_in_tx,
    get_topic_cursor_in_tx,
    list_topic_cursors_in_tx,
    topic_high_sequence_in_tx,
)


class FakeCursorConn:
    def __init__(self, *, high: int = 7, current: int = 3) -> None:
        self.high = high
        self.current = current
        self.queries: list[tuple[str, tuple[Any, ...]]] = []
        self.rows: list[dict[str, Any]] = []

    def execute(self, query: str, params: tuple[Any, ...]) -> FakeCursorConn:
        self.queries.append((query, params))
        if "COALESCE(MAX(sequence),0)" in query:
            self.rows = [{"high": self.high}]
        elif "FROM topic_consumption_cursors" in query and "topic_ref=ANY" in query:
            self.rows = [{"topic_ref": "topic:a", "cursor": self.current}]
        elif "FROM topic_consumption_cursors" in query:
            self.rows = [{"cursor": self.current}]
        elif "INSERT INTO topic_consumption_cursors" in query:
            self.rows = [{"cursor": int(params[2])}]
        else:
            raise AssertionError(f"unexpected SQL: {query}")
        return self

    def fetchone(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows


@pytest.mark.parametrize("invalid", [True, 3.0, -1, 8])
def test_invalid_topic_ack_is_never_written(invalid: object) -> None:
    conn = FakeCursorConn()
    with pytest.raises((ValueError, ConflictError)):
        ack_topic_cursor_in_tx(conn, actor_ref="actor:a", topic_ref="topic:a", cursor=invalid)
    assert all("INSERT INTO topic_consumption_cursors" not in sql for sql, _ in conn.queries)


def test_read_and_ack_share_callers_connection_and_cursor_domain() -> None:
    conn = FakeCursorConn(high=7, current=3)
    assert topic_high_sequence_in_tx(conn, "topic:a") == 7
    before = get_topic_cursor_in_tx(conn, actor_ref="actor:a", topic_ref="topic:a")
    assert before["cursor"] == 3 and before["topicHighSequence"] == 7
    after = ack_topic_cursor_in_tx(conn, actor_ref="actor:a", topic_ref="topic:a", cursor=7)
    assert after["previousCursor"] == 3 and after["cursor"] == 7
    assert after["topicHighSequence"] == 7
    assert all(params[0] == "actor:a" for sql, params in conn.queries if "topic_consumption_cursors" in sql)
    assert any("FOR UPDATE" in sql for sql, _ in conn.queries)
    assert any("WHERE topic_consumption_cursors.cursor<=EXCLUDED.cursor" in sql for sql, _ in conn.queries)


def test_backward_ack_rejected_before_upsert() -> None:
    conn = FakeCursorConn(high=7, current=4)
    with pytest.raises(ConflictError, match="backwards"):
        ack_topic_cursor_in_tx(conn, actor_ref="actor:a", topic_ref="topic:a", cursor=3)
    assert all("INSERT INTO topic_consumption_cursors" not in sql for sql, _ in conn.queries)


def test_attention_bulk_cursor_reads_are_single_snapshot_and_empty_safe() -> None:
    conn = FakeCursorConn(high=7, current=3)
    assert list_topic_cursors_in_tx(conn, actor_ref="actor:a", topic_refs=[]) == {}
    assert conn.queries == []
    assert list_topic_cursors_in_tx(
        conn, actor_ref="actor:a", topic_refs=["topic:a", "topic:b"]
    ) == {"topic:a": 3}
    assert conn.queries == [
        (
            "SELECT topic_ref,cursor FROM topic_consumption_cursors "
            "WHERE actor_ref=%s AND topic_ref=ANY(%s)",
            ("actor:a", ["topic:a", "topic:b"]),
        )
    ]


def test_cursor_sql_is_owned_by_one_module_not_copied_across_consumers() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "ordivon_host_v2"
    truth = (root / "topic_cursor_records.py").read_text(encoding="utf-8")
    assert "INSERT INTO topic_consumption_cursors" in truth
    for filename in (
        "social_topic_commands.py", "social_topic_queries.py", "attention_projections.py"
    ):
        source = (root / filename).read_text(encoding="utf-8")
        assert "FROM topic_consumption_cursors" not in source
        assert "INSERT INTO topic_consumption_cursors" not in source
