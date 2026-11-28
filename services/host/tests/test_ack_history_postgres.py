"""Bounded complete concurrent histories of native ACKs.

The oracle enumerates real-time-compatible serial orders independently of SQL.
Only complete histories with fixed horizons are admitted; not a distributed
fault-tolerance proof or a general-purpose linearizability checker.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import permutations
from threading import Barrier
from time import monotonic_ns
from uuid import uuid4

import psycopg
import pytest
from test_attention_single_snapshot_postgres import DSN, _fixture

from ordivon_host_v2 import attention_store
from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.errors import ConflictError

# Each result distinguishes original effect, historical replay, and conflict.
Outcome = tuple[str, int, int]


@dataclass(frozen=True)
class Op:
    key: str
    cursor: int  # -1 means read


@dataclass(frozen=True)
class Event:
    op: Op
    start: int
    end: int
    result: Outcome


def legal_history(
    events: tuple[Event, ...], high: int, final: int, durable: dict[str, tuple[int, int]]
) -> bool:
    """Finite exhaustive oracle; no implementation calls or SQL."""
    if not 0 < len(events) <= 6 or any(e.start >= e.end for e in events):
        raise ValueError("requires bounded complete history")
    precedence = {
        (i, j)
        for i, a in enumerate(events)
        for j, b in enumerate(events)
        if i != j and a.end <= b.start
    }
    for order in permutations(range(len(events))):
        position = {i: p for p, i in enumerate(order)}
        if any(position[i] > position[j] for i, j in precedence):
            continue
        cursor = 0
        receipts: dict[str, tuple[int, int]] = {}
        for i in order:
            event = events[i]
            key, target = event.op.key, event.op.cursor
            if target == -1:
                expected = ("read", cursor, cursor)
            elif key in receipts:
                previous, committed = receipts[key]
                expected = (
                    ("replay", previous, committed) if committed == target else ("conflict", -1, -1)
                )
            elif cursor <= target <= high:
                expected = ("commit", cursor, target)
                receipts[key] = (cursor, target)
                cursor = target
            else:
                expected = ("conflict", -1, -1)
            if expected != event.result:
                break
        else:
            if cursor == final and receipts == durable:
                return True
    return False


def test_oracle_distinguishes_overlap_real_time_and_replay():
    a = Event(Op("a", 1), 1, 5, ("commit", 0, 1))
    b = Event(Op("b", 2), 2, 4, ("commit", 1, 2))
    replay = Event(Op("a", 1), 6, 7, ("replay", 0, 1))
    durable = {"a": (0, 1), "b": (1, 2)}
    assert legal_history((a, b, replay), 2, 2, durable)
    # B completes before A starts: the same outputs now cannot be serialized.
    assert not legal_history(
        (Event(a.op, 5, 6, a.result), b, Event(replay.op, 7, 8, replay.result)), 2, 2, durable
    )
    assert not legal_history((a, b, Event(replay.op, 6, 7, ("replay", 2, 1))), 2, 2, durable)
    assert not legal_history((a, b, replay), 2, 2, {"a": (0, 1)})
    assert not legal_history((a, Event(b.op, 2, 4, ("commit", 0, 2)), replay), 2, 2, durable)
    with pytest.raises(ValueError):
        legal_history((Event(a.op, 1, 1, a.result),), 2, 1, {"a": (0, 1)})


@pytest.mark.skipif(not DSN, reason="requires isolated native PG")
@pytest.mark.usefixtures("host_test_db_ready")
@pytest.mark.parametrize("domain", ["attention", "topic"])
@pytest.mark.parametrize("variant", [0, 1, 2])
def test_native_ack_complete_histories(domain, variant):
    assert DSN
    actor, topic, sequence, social = _fixture()
    store = AttentionStore(DSN)
    prefix = f"ack-history:{uuid4().hex}:"
    with psycopg.connect(DSN) as conn:
        high = (
            conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[0]
            if domain == "attention"
            else sequence
        )

    def ack(key, target):
        if domain == "attention":
            return store.ack(actor, cursor=target, client_request_id=prefix + key)
        return social.ack_topic_cursor(
            actor_ref=actor, topic_ref=topic, cursor=target, client_request_id=prefix + key
        )

    def current():
        return (
            store.get(actor)["afterSequence"]
            if domain == "attention"
            else social.get_topic_cursor(actor_ref=actor, topic_ref=topic)["cursor"]
        )

    def execute(op, barrier=None):
        if barrier is not None:
            barrier.wait(timeout=10)
        start = monotonic_ns()
        if op.cursor == -1:
            cursor = current()
            outcome = ("read", cursor, cursor)
        else:
            try:
                result = ack(op.key, op.cursor)
            except ConflictError:
                outcome = ("conflict", -1, -1)
            else:
                assert result["actorRef"] == actor
                if domain == "topic":
                    assert result["topicRef"] == topic
                    assert result["topicHighSequence"] == high
                assert result.get("admission") in (None, "existing")
                outcome = (
                    "replay" if result.get("admission") == "existing" else "commit",
                    result["previousCursor"],
                    result["cursor"],
                )
        return Event(op, start, monotonic_ns(), outcome)

    # The first wave contains conflicting same-key requests and a competing
    # fresh key. The second wave includes an exact retry, read and fresh ACK.
    first = (Op("a", 0), Op("a", high), Op("b", high))
    first = first[variant:] + first[:variant]
    second = (Op("a", 0 if variant == 0 else high), Op("read", -1), Op("c", high))
    history = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for wave in (first, second):
            barrier = Barrier(3)
            pending = [pool.submit(execute, op, barrier) for op in wave]
            history.extend(f.result(timeout=20) for f in pending)
    with psycopg.connect(DSN) as conn:
        if domain == "attention":
            final = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor,)
            ).fetchone()[0]
        else:
            final = conn.execute(
                "SELECT cursor FROM topic_consumption_cursors WHERE actor_ref=%s AND topic_ref=%s",
                (actor, topic),
            ).fetchone()[0]
        rows = conn.execute(
            "SELECT client_request_id,response FROM command_receipts WHERE client_request_id LIKE %s",
            (prefix + "%",),
        ).fetchall()
    durable = {
        key.removeprefix(prefix): (response["previousCursor"], response["cursor"])
        for key, response in rows
    }
    assert legal_history(tuple(history), high, final, durable), (history, final, durable)
    assert current() == final


@pytest.mark.skipif(not DSN, reason="requires isolated native PG")
@pytest.mark.usefixtures("host_test_db_ready")
def test_native_ack_sql_failure_after_receipt_rolls_back_both_effects(monkeypatch):
    assert DSN
    actor, _, _, _ = _fixture()
    key = f"ack-fault:{uuid4().hex}"
    store = AttentionStore(DSN)
    original = attention_store.record_command_receipt
    reached = []

    def fail_after_native_receipt(conn, *args, **kwargs):
        original(conn, *args, **kwargs)
        reached.append(True)
        # A real server error after the native cursor UPSERT and receipt UPDATE,
        # before transaction commit. Not a fabricated Python conflict.
        conn.execute("SELECT 1/0")

    with monkeypatch.context() as patch:
        patch.setattr(attention_store, "record_command_receipt", fail_after_native_receipt)
        with pytest.raises(psycopg.errors.DivisionByZero):
            store.ack(actor, cursor=1, client_request_id=key)
    assert reached == [True]
    with psycopg.connect(DSN) as conn:
        assert (
            conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor,)
            ).fetchone()
            is None
        )
        assert (
            conn.execute(
                "SELECT response FROM command_receipts WHERE client_request_id=%s", (key,)
            ).fetchone()
            is None
        )
    result = store.ack(actor, cursor=1, client_request_id=key)
    assert (result["previousCursor"], result["cursor"]) == (0, 1)
    assert store.ack(actor, cursor=1, client_request_id=key) == {**result, "admission": "existing"}
