"""Pure functional core for Attention re-entry navigation representation.

Input comes from an already-bound Attention delta page and Topic cursor read in
one PG MVCC snapshot. No DB/HTTP/Gateway/clock/effect dependency is allowed
here. A grouped representation may exceed the byte limit of its raw events;
only a complete prefix may be admitted, never an arbitrary subset or an ACK.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .canonical_json import canonical_bytes


def reentry_topic_refs(events: Sequence[dict[str, Any]]) -> list[str]:
    """Return bounded relevant TopicRefs for one read on the caller's transaction."""
    return sorted({
        str(event["navigationRef"])
        for event in events
        if event["navigationKind"] == "topic"
    })


def project_reentry(
    delta: dict[str, Any],
    *,
    actor_ref: str,
    after_sequence: int,
    cursors: Mapping[str, int],
    max_bytes: int,
) -> dict[str, Any]:
    """Fold an exact ordered event prefix into navigation groups and byte-bound it.

    delta is the actual owner projection, not a second event store. This
    pure function does not authorize or infer that any message was processed.
    """
    events = delta["events"]

    def projection(count: int) -> dict[str, Any]:
        prefix = events[:count]
        groups: dict[tuple[str, str], dict[str, Any]] = {}
        for event in prefix:
            key = (event["navigationKind"], event["navigationRef"])
            item = groups.get(key)
            if item is None:
                item = {
                    "navigationKind": key[0],
                    "navigationRef": key[1],
                    "latestChangeSequence": int(event["changeSequence"]),
                    "eventKinds": [],
                    "reasons": [],
                    "eventCount": 0,
                }
                groups[key] = item
            item["latestChangeSequence"] = max(
                int(item["latestChangeSequence"]), int(event["changeSequence"])
            )
            item["eventKinds"] = sorted(set(item["eventKinds"]) | {event["eventKind"]})
            item["reasons"] = sorted(set(item["reasons"]) | set(event["reasons"]))
            item["eventCount"] = int(item["eventCount"]) + 1

        items = list(groups.values())
        for item in items:
            if item["navigationKind"] == "topic":
                item["resumeAfterSequence"] = cursors.get(str(item["navigationRef"]), 0)

        trimmed = count < len(events)
        has_more = trimmed or delta["hasMore"]
        next_sequence = (
            int(prefix[-1]["changeSequence"]) if trimmed else delta["nextAfterSequence"]
        )
        return {
            "schemaVersion": 1,
            "kind": "ordivon.host-attention-reentry-r1",
            "actorRef": actor_ref,
            "afterSequence": after_sequence,
            "snapshotHighSequence": delta["snapshotHighSequence"],
            "items": items,
            "rawEventCount": count,
            "hasMore": has_more,
            "nextAfterSequence": next_sequence,
            "rankingApplied": False,
            "truthBoundary": "rebuildable re-entry navigation only; no score, priority, assignment, scheduling, or foreign truth ownership",
        }

    result = projection(len(events))
    if len(canonical_bytes(result)) <= max_bytes:
        return result

    # Grouped output may exceed the event byte budget. Monotone prefix
    # growth permits binary search without replaying the expensive delta SQL.
    low, high = 1, len(events) - 1
    best: dict[str, Any] | None = None
    while low <= high:
        middle = (low + high) // 2
        candidate = projection(middle)
        if len(canonical_bytes(candidate)) <= max_bytes:
            best = candidate
            low = middle + 1
        else:
            high = middle - 1
    if best is None:
        raise ValueError("max_bytes cannot fit one re-entry navigation item")
    return best
