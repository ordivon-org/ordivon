"""Pure Attention re-entry grouping and bounded lossless-prefix refinement.

The native PostgreSQL single-snapshot and concurrency tests remain separate.
No new Attention database, scoring, or scheduler is introduced.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_host_v2.attention_reentry import project_reentry, reentry_topic_refs
from ordivon_host_v2.canonical_json import canonical_bytes


def _event(sequence: int, *, kind: str, ref: str, reason: str) -> dict:
    return {
        "changeSequence": sequence,
        "eventKind": "message",
        "sourceRef": f"message:e:{sequence}",
        "contextRef": ref,
        "reasons": [reason],
        "navigationKind": kind,
        "navigationRef": ref,
    }


def _delta(events: list[dict], *, has_more: bool = False) -> dict:
    return {
        "events": events,
        "hasMore": has_more,
        "nextAfterSequence": 100,
        "snapshotHighSequence": 200,
    }


def test_projection_is_pure_grouped_navigation_not_completion_or_priority() -> None:
    events = [
        _event(3, kind="topic", ref="topic:a", reason="mentioned"),
        _event(4, kind="work", ref="work:a", reason="followed_work"),
        _event(5, kind="topic", ref="topic:a", reason="replied_to_me"),
        _event(6, kind="topic", ref="topic:b", reason="followed_topic"),
    ]
    delta = _delta(events)
    original = deepcopy(delta)
    cursors = {"topic:a": 3}
    result = project_reentry(
        delta, actor_ref="actor:a", after_sequence=2, cursors=cursors, max_bytes=100000
    )
    assert delta == original
    assert result["items"] == [
        {
            "navigationKind": "topic",
            "navigationRef": "topic:a",
            "latestChangeSequence": 5,
            "eventKinds": ["message"],
            "reasons": ["mentioned", "replied_to_me"],
            "eventCount": 2,
            "resumeAfterSequence": 3,
        },
        {
            "navigationKind": "work",
            "navigationRef": "work:a",
            "latestChangeSequence": 4,
            "eventKinds": ["message"],
            "reasons": ["followed_work"],
            "eventCount": 1,
        },
        {
            "navigationKind": "topic",
            "navigationRef": "topic:b",
            "latestChangeSequence": 6,
            "eventKinds": ["message"],
            "reasons": ["followed_topic"],
            "eventCount": 1,
            "resumeAfterSequence": 0,
        },
    ]
    assert result["rawEventCount"] == 4
    assert result["nextAfterSequence"] == 100
    assert result["hasMore"] is False
    assert result["rankingApplied"] is False
    assert reentry_topic_refs(events) == ["topic:a", "topic:b"]


def test_trimming_preserves_exact_prefix_and_never_forgets_more_events() -> None:
    events = [
        _event(i, kind="topic", ref=f"topic:{i}:" + ("x" * 90), reason="followed_topic")
        for i in range(1, 9)
    ]
    delta = _delta(events)
    full = project_reentry(
        delta, actor_ref="actor:a", after_sequence=0, cursors={}, max_bytes=100000
    )
    first = project_reentry(
        _delta(events[:1], has_more=True),
        actor_ref="actor:a", after_sequence=0, cursors={}, max_bytes=100000,
    )
    assert len(canonical_bytes(first)) < len(canonical_bytes(full))
    budget = len(canonical_bytes(first)) + 10
    trimmed = project_reentry(
        delta, actor_ref="actor:a", after_sequence=0, cursors={}, max_bytes=budget
    )
    assert 1 <= trimmed["rawEventCount"] < len(events)
    assert trimmed["hasMore"] is True
    assert trimmed["nextAfterSequence"] == events[trimmed["rawEventCount"] - 1]["changeSequence"]
    assert len(canonical_bytes(trimmed)) <= budget
    assert [i["navigationRef"] for i in trimmed["items"]] == [
        e["navigationRef"] for e in events[:trimmed["rawEventCount"]]
    ]


def test_too_small_byte_budget_refuses_to_drop_first_navigation_event() -> None:
    delta = _delta([_event(1, kind="topic", ref="topic:a", reason="mentioned")])
    with pytest.raises(ValueError, match="cannot fit one re-entry navigation item"):
        project_reentry(
            delta, actor_ref="actor:a", after_sequence=0, cursors={}, max_bytes=10
        )


def test_zero_events_do_not_invent_ack_or_advance_beyond_owner_horizon() -> None:
    result = project_reentry(
        _delta([]), actor_ref="actor:a", after_sequence=99, cursors={}, max_bytes=100000
    )
    assert result["items"] == []
    assert result["rawEventCount"] == 0
    assert result["nextAfterSequence"] == 100
    assert result["snapshotHighSequence"] == 200
    assert result["hasMore"] is False
    assert reentry_topic_refs([]) == []
