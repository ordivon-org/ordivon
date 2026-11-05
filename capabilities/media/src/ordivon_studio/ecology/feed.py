"""Derived feed ordering and presentation with no priority authority."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .board import BOARD_THREAD_TRUTH_ROLE
from .contracts import _canonical_digest, _integer, _string

FEED_TRUTH_ROLE = "derived-activity-view-not-priority-or-domain-truth"



def thread_feed_items(threads: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for thread in threads:
        if thread.get("kind") != "ordivon.media.board-thread-projection":
            raise ValueError("thread feed input is not a Board thread projection")
        if thread.get("rootStatus") != "present":
            continue
        thread_id = _string(thread.get("threadId"), "threadId")
        topics = thread.get("topics")
        if not isinstance(topics, list):
            raise ValueError("thread topics must be a list")
        result.append(
            {
                "kind": "board-thread",
                "sourceIdentity": thread_id,
                "observedAtMs": _integer(thread.get("lastRecordedAtMs"), "lastRecordedAtMs"),
                "title": str(thread.get("rootTopic") or thread_id),
                "summary": (
                    f"{int(thread['messageCount'])} messages; "
                    f"{int(thread['replyCount'])} replies; topics={','.join(map(str, topics)) or 'none'}"
                ),
                "truthRole": BOARD_THREAD_TRUTH_ROLE,
                "sourceDigest": _string(thread.get("projectionDigest"), "projectionDigest"),
            }
        )
    return result


def derive_activity_feed(
    items: Iterable[Mapping[str, object]], *, observed_at_ms: int
) -> dict[str, object]:
    """Build an exhaustive time-ordered projection over the explicitly supplied input set."""

    _integer(observed_at_ms, "observedAtMs")
    normalized: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for raw in items:
        kind = _string(raw.get("kind"), "kind")
        identity = _string(raw.get("sourceIdentity"), "sourceIdentity")
        key = (kind, identity)
        if key in seen:
            raise ValueError("feed input contains duplicate source identity")
        seen.add(key)
        normalized.append(
            {
                "kind": kind,
                "sourceIdentity": identity,
                "observedAtMs": _integer(raw.get("observedAtMs"), "observedAtMs"),
                "title": _string(raw.get("title"), "title"),
                "summary": _string(raw.get("summary"), "summary"),
                "truthRole": _string(raw.get("truthRole"), "truthRole"),
                "sourceDigest": _string(raw.get("sourceDigest"), "sourceDigest"),
            }
        )
    normalized.sort(key=lambda item: (-int(item["observedAtMs"]), str(item["sourceIdentity"])))
    projection: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.activity-feed-projection",
        "observedAtMs": observed_at_ms,
        "ordering": "source-observed-time-descending",
        "inputItemCount": len(normalized),
        "items": normalized,
        "priorityInferred": False,
        "sourceCompletenessClaimed": False,
        "truthRole": FEED_TRUTH_ROLE,
        "truthBoundary": (
            "The feed orders only the explicitly supplied source projections. Presence does not "
            "create priority or truth; absence does not establish that an event, work, message, "
            "Task, Production, or source object does not exist."
        ),
    }
    projection["projectionDigest"] = _canonical_digest(projection)
    return projection
