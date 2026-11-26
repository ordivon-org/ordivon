"""Pure functional core for Attention re-entry navigation representation.

Input comes from an already-bound Attention delta page and Topic cursor read in
one PG MVCC snapshot. No DB/HTTP/Gateway/clock/effect dependency is allowed
here. A grouped representation may exceed the byte limit of its raw events;
only a complete prefix may be admitted, never an arbitrary subset or an ACK.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .canonical_json import canonical_bytes


def reentry_topic_refs(events: Sequence[dict[str, Any]]) -> list[str]:
    """Return bounded relevant TopicRefs for one read on the caller's transaction."""
    return sorted({
        str(event["navigationRef"])
        for event in events
        if event["navigationKind"] == "topic"
    })


@dataclass(slots=True)
class _NavigationGroup:
    kind: str
    ref: str
    latest: int
    count: int = 0
    kinds: set[str] = field(default_factory=set)
    reasons: set[str] = field(default_factory=set)

    def add(self, event: dict[str, Any]) -> None:
        self.latest = max(self.latest, int(event["changeSequence"]))
        self.count += 1
        self.kinds.add(event["eventKind"])
        self.reasons.update(event["reasons"])

    def wire(self, cursors: Mapping[str, int]) -> dict[str, Any]:
        item = {
            "navigationKind": self.kind,
            "navigationRef": self.ref,
            "latestChangeSequence": self.latest,
            "eventKinds": sorted(self.kinds),
            "reasons": sorted(self.reasons),
            "eventCount": self.count,
        }
        if self.kind == "topic":
            item["resumeAfterSequence"] = cursors.get(self.ref, 0)
        return item


def _accumulate(
    groups: dict[tuple[str, str], _NavigationGroup], event: dict[str, Any]
) -> _NavigationGroup:
    key = (event["navigationKind"], event["navigationRef"])
    group = groups.get(key)
    if group is None:
        group = _NavigationGroup(*key, int(event["changeSequence"]))
        groups[key] = group
    group.add(event)
    return group


def project_reentry(
    delta: dict[str, Any],
    *,
    actor_ref: str,
    after_sequence: int,
    cursors: Mapping[str, int],
    max_bytes: int,
) -> dict[str, Any]:
    """Select the longest complete event prefix whose grouped wire bytes fit.

    Requires the caller's exact, strictly ordered Attention delta and its
    same-snapshot Topic cursor readback. A nonempty delta may not return an
    empty prefix. Groups retain first-occurrence order, counts, maximum
    change sequence and sorted unions. Only Topics carry message cursors.
    A trimmed page preserves continuation at its last included change;
    a complete page preserves the owner's continuation and hasMore.
    Neither result acknowledges, assigns, ranks, authorizes or proves effects.
    """
    events = delta["events"]

    def envelope(count: int) -> dict[str, Any]:
        trimmed = count < len(events)
        return {
            "schemaVersion": 1,
            "kind": "ordivon.host-attention-reentry-r1",
            "actorRef": actor_ref,
            "afterSequence": after_sequence,
            "snapshotHighSequence": delta["snapshotHighSequence"],
            "items": [],
            "rawEventCount": count,
            "hasMore": trimmed or delta["hasMore"],
            "nextAfterSequence": (
                int(events[count - 1]["changeSequence"]) if trimmed else delta["nextAfterSequence"]
            ),
            "rankingApplied": False,
            "truthBoundary": "rebuildable re-entry navigation only; no score, priority, assignment, scheduling, or foreign truth ownership",
        }

    def projection(count: int) -> dict[str, Any]:
        groups: dict[tuple[str, str], _NavigationGroup] = {}
        for event in events[:count]:
            _accumulate(groups, event)
        return {**envelope(count), "items": [group.wire(cursors) for group in groups.values()]}

    # Common case: one grouping pass, sort each union only at materialization.
    result = projection(len(events))
    if len(canonical_bytes(result)) <= max_bytes:
        return result

    # RFC 8785 array size = sum of independently encoded items + separators.
    # Only the group changed by the new event needs to be re-encoded.
    # The owner supplies increasing nonnegative coordinates and a terminal
    # continuation >= its last event. Group counts, unions, coordinate digit
    # lengths, and the envelope therefore cannot shrink as a prefix grows.
    # A terminal false hasMore is one byte longer than true.
    groups: dict[tuple[str, str], _NavigationGroup] = {}
    sizes: dict[tuple[str, str], int] = {}
    array_bytes = 0
    accepted = 0
    for count, event in enumerate(events, 1):
        group = _accumulate(groups, event)
        key = (group.kind, group.ref)
        item_bytes = len(canonical_bytes(group.wire(cursors)))
        if key in sizes:
            array_bytes += item_bytes - sizes[key]
        else:
            array_bytes += item_bytes + int(bool(sizes))
        sizes[key] = item_bytes
        if len(canonical_bytes(envelope(count))) + array_bytes > max_bytes:
            break
        accepted = count

    if not accepted:
        raise ValueError("max_bytes cannot fit one re-entry navigation item")
    # Rebuild only the accepted prefix, excluding the overflowing event.
    return projection(accepted)
