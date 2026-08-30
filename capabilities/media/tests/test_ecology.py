from __future__ import annotations

import pytest

from ordivon_studio.ecology import (
    BOARD_THREAD_TRUTH_ROLE,
    COLLECTION_TRUTH_ROLE,
    FEED_TRUTH_ROLE,
    collection_feed_item,
    derive_activity_feed,
    derive_board_threads,
    thread_feed_items,
    validate_collection,
)


def _message(
    sequence: int,
    client_id: str,
    *,
    topic: str | None = "media",
    reply_to: str | None = None,
    recorded_at_ms: int | None = None,
) -> dict[str, object]:
    return {
        "sequence": sequence,
        "clientMessageId": client_id,
        "authorLabel": f"agent:{sequence % 2}",
        "messageKind": "reply" if reply_to else "note",
        "topic": topic,
        "message": f"message {client_id}",
        "replyToClientMessageId": reply_to,
        "recordedAtMs": recorded_at_ms if recorded_at_ms is not None else sequence * 1000,
        "messageDigest": "sha256:" + f"{sequence:064x}",
        "truthRole": "coordination-message-not-domain-truth",
    }


def _collection() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.collection",
        "id": "collection:daily-cabinet:test",
        "title": "Daily Cabinet Test",
        "publishedAtMs": 9000,
        "curatorLabel": "media-owner",
        "curatorialBoundary": (
            "Membership and ordering are curatorial facts only; member truth remains source-owned."
        ),
        "members": [
            {
                "memberId": "work:a",
                "title": "A",
                "sourceOwner": "Media",
                "sourceIdentity": "production:a",
                "sourceRevision": "a" * 40,
                "sourceObjects": [
                    {"path": "productions/a/output.png", "digest": "sha256:" + "1" * 64},
                    {"path": "productions/a/README.md", "digest": "sha256:" + "3" * 64},
                ],
                "note": None,
            },
            {
                "memberId": "work:b",
                "title": "B",
                "sourceOwner": "Game",
                "sourceIdentity": "artifact:b",
                "sourceRevision": "b" * 40,
                "sourceObjects": [
                    {"path": "play/b.py", "digest": "sha256:" + "2" * 64},
                ],
                "note": "A second independent work.",
            },
        ],
        "truthRole": COLLECTION_TRUTH_ROLE,
    }


def test_board_thread_identity_is_derived_from_root_not_topic() -> None:
    threads = derive_board_threads(
        [
            _message(1, "root", topic="alpha"),
            _message(2, "r1", topic="alpha", reply_to="root"),
            _message(3, "r2", topic="beta", reply_to="r1"),
        ]
    )
    assert len(threads) == 1
    thread = threads[0]
    assert thread["threadId"] == "board-thread:root"
    assert thread["rootStatus"] == "present"
    assert thread["messageCount"] == 3
    assert thread["replyCount"] == 2
    assert thread["maxDepth"] == 2
    assert thread["topics"] == ["alpha", "beta"]
    assert thread["truthRole"] == BOARD_THREAD_TRUTH_ROLE


def test_bounded_board_snapshot_does_not_invent_missing_root() -> None:
    threads = derive_board_threads(
        [
            _message(8, "local-r1", reply_to="outside-root"),
            _message(9, "local-r2", reply_to="local-r1"),
        ]
    )
    assert len(threads) == 1
    thread = threads[0]
    assert thread["threadId"] is None
    assert thread["rootStatus"] == "outside-snapshot"
    assert thread["externalAncestorClientMessageId"] == "outside-root"
    assert thread["messageCount"] == 2


def test_board_thread_cycle_fails_closed() -> None:
    with pytest.raises(ValueError, match="cycle"):
        derive_board_threads(
            [
                _message(1, "a", reply_to="b"),
                _message(2, "b", reply_to="a"),
            ]
        )


def test_collection_is_only_a_curation_relation() -> None:
    collection = validate_collection(_collection())
    assert collection["truthRole"] == COLLECTION_TRUTH_ROLE
    assert len(collection["members"]) == 2
    assert collection["members"][0]["sourceRevision"] == "a" * 40


def test_collection_rejects_ephemeral_conversation_source_revision() -> None:
    value = _collection()
    value["members"][0]["sourceRevision"] = "turn9news1"
    with pytest.raises(ValueError, match="ephemeral conversation citation"):
        validate_collection(value)


def test_collection_rejects_duplicate_member_identity() -> None:
    value = _collection()
    value["members"][1]["memberId"] = "work:a"
    with pytest.raises(ValueError, match="unique"):
        validate_collection(value)


def test_feed_orders_supplied_sources_without_priority_claim() -> None:
    threads = derive_board_threads(
        [
            _message(1, "root-a", recorded_at_ms=1000),
            _message(2, "reply-a", reply_to="root-a", recorded_at_ms=7000),
            _message(3, "root-b", recorded_at_ms=4000),
        ]
    )
    items = thread_feed_items(threads)
    items.append(collection_feed_item(_collection()))
    feed = derive_activity_feed(items, observed_at_ms=10000)
    assert feed["truthRole"] == FEED_TRUTH_ROLE
    assert feed["priorityInferred"] is False
    assert feed["sourceCompletenessClaimed"] is False
    assert [item["kind"] for item in feed["items"]] == [
        "collection",
        "board-thread",
        "board-thread",
    ]
    assert feed["items"][0]["sourceIdentity"] == "collection:daily-cabinet:test"
    assert "absence does not establish" in feed["truthBoundary"]


def test_feed_rejects_duplicate_source_identity() -> None:
    item = {
        "kind": "board-thread",
        "sourceIdentity": "board-thread:x",
        "observedAtMs": 100,
        "title": "x",
        "summary": "x",
        "truthRole": BOARD_THREAD_TRUTH_ROLE,
        "sourceDigest": "sha256:" + "0" * 64,
    }
    with pytest.raises(ValueError, match="duplicate"):
        derive_activity_feed([item, dict(item)], observed_at_ms=101)
