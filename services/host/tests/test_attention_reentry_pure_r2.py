"""Pure Attention re-entry grouping and bounded lossless-prefix refinement.

The native PostgreSQL single-snapshot and concurrency tests remain separate.
No new Attention database, scoring, or scheduler is introduced.
"""
from __future__ import annotations

from copy import deepcopy

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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


# Normative behavior at the pure consumer seam, not a replica of the
# production binary search or of the database's relevance selection.
def _expected_prefix(delta, count, actor, after, cursors):
    prefix = delta["events"][:count]
    keys = list(dict.fromkeys((e["navigationKind"], e["navigationRef"]) for e in prefix))
    items = []
    for kind, ref in keys:
        members = [e for e in prefix if (e["navigationKind"], e["navigationRef"]) == (kind, ref)]
        item = {
            "navigationKind": kind,
            "navigationRef": ref,
            "latestChangeSequence": max(e["changeSequence"] for e in members),
            "eventCount": len(members),
            "eventKinds": sorted({e["eventKind"] for e in members}),
            "reasons": sorted({reason for e in members for reason in e["reasons"]}),
        }
        if kind == "topic":
            item["resumeAfterSequence"] = cursors.get(ref, 0)
        items.append(item)
    trimmed = count != len(delta["events"])
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-attention-reentry-r1",
        "actorRef": actor,
        "afterSequence": after,
        "snapshotHighSequence": delta["snapshotHighSequence"],
        "items": items,
        "rawEventCount": count,
        "hasMore": trimmed or delta["hasMore"],
        "nextAfterSequence": prefix[-1]["changeSequence"] if trimmed else delta["nextAfterSequence"],
        "rankingApplied": False,
        "truthBoundary": "rebuildable re-entry navigation only; no score, priority, assignment, scheduling, or foreign truth ownership",
    }


@st.composite
def _ordered_delta(draw):
    count = draw(st.integers(0, 16))
    after = draw(st.sampled_from([0, 8, 98, 998, 2**53 - 100]))
    gaps = draw(st.lists(st.integers(1, 4), min_size=count, max_size=count))
    events = []
    coordinate = after
    for gap in gaps:
        coordinate += gap
        event = _event(
            coordinate,
            kind=draw(st.sampled_from(["topic", "work", "space", "subject"])),
            ref=draw(st.sampled_from(["r:a", "r:b", "r:汉字", "r:𠀀", "r:" + "x" * 80])),
            reason="mentioned",
        )
        event["eventKind"] = draw(st.sampled_from(["message", "work", "relation", "participation"]))
        event["reasons"] = draw(
            st.lists(st.sampled_from(["mentioned", "followed_topic", "replied_to_me", "own_participation"]),
                     min_size=1, max_size=4, unique=True)
        )
        events.append(event)
    has_more = draw(st.booleans()) if count else False
    high = coordinate + draw(st.integers(1, 5))
    delta = {
        "events": events,
        "hasMore": has_more,
        "nextAfterSequence": coordinate if has_more else high,
        "snapshotHighSequence": high,
    }
    cursors = draw(st.dictionaries(
        st.sampled_from(["r:a", "r:b", "r:汉字", "r:𠀀"]),
        st.integers(0, 2**53 - 1),
    ))
    return delta, after, cursors


@settings(max_examples=120, deadline=None)
@given(_ordered_delta(), st.integers(0, 10000))
def test_reentry_is_maximal_lossless_prefix_under_exact_wire_budget(case, sampled_budget):
    delta, after, cursors = case
    actor = "actor:agent:独立消费者"
    before = deepcopy((delta, cursors))
    counts = range(1, len(delta["events"]) + 1) if delta["events"] else [0]
    alternatives = [_expected_prefix(delta, n, actor, after, cursors) for n in counts]
    lengths = [len(canonical_bytes(candidate)) for candidate in alternatives]
    # Every exact byte boundary and its immediate neighbors; not just one
    # conveniently chosen budget. The oracle enumerates rather than assumes
    # that encoded prefixes are monotone.
    for budget in sorted({sampled_budget, *(size + step for size in lengths for step in (-1, 0, 1))}):
        fits = [candidate for candidate, size in zip(alternatives, lengths) if size <= budget]
        if not fits:
            with pytest.raises(ValueError, match="cannot fit"):
                project_reentry(delta, actor_ref=actor, after_sequence=after, cursors=cursors, max_bytes=budget)
        else:
            result = project_reentry(delta, actor_ref=actor, after_sequence=after, cursors=cursors, max_bytes=budget)
            assert result == fits[-1]
            assert len(canonical_bytes(result)) <= budget
        assert (delta, cursors) == before
