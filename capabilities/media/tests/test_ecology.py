from __future__ import annotations

import unittest

from ordivon_studio.ecology import (
    BOARD_THREAD_TRUTH_ROLE,
    COLLECTION_TRUTH_ROLE,
    FEED_TRUTH_ROLE,
    collection_feed_item,
    compose_board_source_set,
    compose_board_sources,
    derive_activity_feed,
    derive_board_threads,
    normalize_board_source,
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


class EcologyTests(unittest.TestCase):
    def test_current_host_board_response_preserves_latest_window_fence(self) -> None:
        document = {
            "schemaVersion": 1,
            "kind": "ordivon.host-board-list",
            "scope": "host-global-coordination-messages",
            "selectionMode": "latest-window",
            "requestedAfterSequence": None,
            "requestedLimit": 100,
            "messages": [_message(2520, "recent-root", topic="busy")],
            "messageCount": 3320,
            "lastSequence": 3320,
            "nextAfterSequence": 3320,
            "hasMore": False,
            "topic": "busy",
            "truthBoundary": "board messages are coordination only",
        }
        messages, fence = normalize_board_source(document)
        self.assertEqual(len(messages), 1)
        self.assertIsNotNone(fence)
        assert fence is not None
        self.assertEqual(fence["selectionMode"], "latest-window")
        self.assertEqual(fence["requestedLimit"], 100)
        self.assertIsNone(fence["requestedAfterSequence"])
        self.assertEqual(fence["globalMessageCount"], 3320)
        self.assertEqual(fence["returnedMessageCount"], 1)
        self.assertFalse(fence["sourceCompletenessClaimed"])

    def test_current_host_incremental_page_requires_preserved_cursor(self) -> None:
        document = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "incremental-page",
            "requestedAfterSequence": 0,
            "requestedLimit": 100,
            "messages": [_message(507, "historical-root", topic="busy")],
            "messageCount": 3320,
            "lastSequence": 3320,
            "nextAfterSequence": 663,
            "hasMore": True,
            "topic": "busy",
        }
        _, fence = normalize_board_source(document)
        assert fence is not None
        self.assertEqual(fence["selectionMode"], "incremental-page")
        self.assertEqual(fence["requestedAfterSequence"], 0)
        self.assertTrue(fence["hasMore"])
        self.assertFalse(fence["sourceCompletenessClaimed"])

    def test_legacy_host_board_response_does_not_infer_selection_mode(self) -> None:
        document = {
            "schemaVersion": 1,
            "kind": "ordivon.host-board-list",
            "messages": [_message(10, "legacy-root")],
            "messageCount": 10,
            "lastSequence": 10,
            "nextAfterSequence": 10,
            "hasMore": False,
            "topic": "media",
        }
        _, fence = normalize_board_source(document)
        assert fence is not None
        self.assertEqual(fence["selectionMode"], "unknown-legacy-response")
        self.assertIsNone(fence["requestedAfterSequence"])
        self.assertIsNone(fence["requestedLimit"])
        self.assertFalse(fence["sourceCompletenessClaimed"])

    def test_bare_board_message_list_has_no_acquisition_fence(self) -> None:
        messages, fence = normalize_board_source([_message(1, "root")])
        self.assertEqual(len(messages), 1)
        self.assertIsNone(fence)

    def test_board_source_fence_rejects_incoherent_selection_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "latest-window"):
            normalize_board_source(
                {
                    "kind": "ordivon.host-board-list",
                    "selectionMode": "latest-window",
                    "requestedAfterSequence": 0,
                    "requestedLimit": 10,
                    "messages": [_message(1, "root")],
                }
            )

    def test_cursor_linked_board_pages_compose_without_losing_fences(self) -> None:
        pages = [
            {
                "kind": "ordivon.host-board-list",
                "selectionMode": "incremental-page",
                "requestedAfterSequence": 0,
                "requestedLimit": 2,
                "messages": [_message(5, "a", topic="busy"), _message(8, "b", topic="busy")],
                "messageCount": 20,
                "lastSequence": 20,
                "nextAfterSequence": 8,
                "hasMore": True,
                "topic": "busy",
            },
            {
                "kind": "ordivon.host-board-list",
                "selectionMode": "incremental-page",
                "requestedAfterSequence": 8,
                "requestedLimit": 2,
                "messages": [_message(11, "c", topic="busy")],
                "messageCount": 20,
                "lastSequence": 20,
                "nextAfterSequence": 20,
                "hasMore": False,
                "topic": "busy",
            },
        ]
        messages, scan = compose_board_sources(pages)
        self.assertEqual([item["sequence"] for item in messages], [5, 8, 11])
        self.assertIsNotNone(scan)
        assert scan is not None
        self.assertEqual(scan["kind"], "ordivon.media.host-board-source-scan")
        self.assertEqual(scan["selectionMode"], "incremental-page-chain")
        self.assertEqual(scan["pageCount"], 2)
        self.assertEqual(scan["returnedMessageCount"], 3)
        self.assertTrue(scan["scanExhaustedAtFinalRead"])
        self.assertFalse(scan["sourceCompletenessClaimed"])
        self.assertEqual(len(scan["pageFences"]), 2)

    def test_board_page_composition_rejects_cursor_gap(self) -> None:
        pages = [
            {
                "kind": "ordivon.host-board-list",
                "selectionMode": "incremental-page",
                "requestedAfterSequence": 0,
                "requestedLimit": 1,
                "messages": [_message(5, "a")],
                "nextAfterSequence": 5,
                "hasMore": True,
            },
            {
                "kind": "ordivon.host-board-list",
                "selectionMode": "incremental-page",
                "requestedAfterSequence": 6,
                "requestedLimit": 1,
                "messages": [_message(7, "b")],
                "nextAfterSequence": 7,
                "hasMore": False,
            },
        ]
        with self.assertRaisesRegex(ValueError, "cursor chain"):
            compose_board_sources(pages)

    def test_board_page_composition_rejects_mixed_filters_and_latest_windows(self) -> None:
        first = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "incremental-page",
            "requestedAfterSequence": 0,
            "requestedLimit": 1,
            "messages": [_message(5, "a", topic="alpha")],
            "nextAfterSequence": 5,
            "hasMore": True,
            "topic": "alpha",
        }
        second = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "incremental-page",
            "requestedAfterSequence": 5,
            "requestedLimit": 1,
            "messages": [_message(7, "b", topic="beta")],
            "nextAfterSequence": 7,
            "hasMore": False,
            "topic": "beta",
        }
        with self.assertRaisesRegex(ValueError, "filters differ"):
            compose_board_sources([first, second])
        latest = dict(second)
        latest["selectionMode"] = "latest-window"
        latest["requestedAfterSequence"] = None
        with self.assertRaisesRegex(ValueError, "incremental-page chain"):
            compose_board_sources([first, latest])

    def test_independent_latest_windows_compose_as_source_set(self) -> None:
        alpha = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "latest-window",
            "requestedAfterSequence": None,
            "requestedLimit": 100,
            "messages": [_message(5, "alpha-root", topic="alpha")],
            "messageCount": 20,
            "lastSequence": 20,
            "nextAfterSequence": 20,
            "hasMore": False,
            "topic": "alpha",
        }
        beta = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "latest-window",
            "requestedAfterSequence": None,
            "requestedLimit": 100,
            "messages": [_message(8, "beta-reply", topic="beta", reply_to="alpha-root")],
            "messageCount": 20,
            "lastSequence": 20,
            "nextAfterSequence": 20,
            "hasMore": False,
            "topic": "beta",
        }
        messages, source_set = compose_board_source_set([alpha, beta])
        self.assertEqual([item["clientMessageId"] for item in messages], ["alpha-root", "beta-reply"])
        assert source_set is not None
        self.assertEqual(source_set["kind"], "ordivon.media.host-board-source-set")
        self.assertEqual(source_set["scopeCount"], 2)
        self.assertEqual(source_set["returnedMessageCount"], 2)
        self.assertEqual(source_set["overlapMessageCount"], 0)
        self.assertFalse(source_set["sourceCompletenessClaimed"])
        threads = derive_board_threads(messages)
        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0]["topics"], ["alpha", "beta"])
        self.assertEqual(threads[0]["rootStatus"], "present")

    def test_source_set_groups_incremental_pages_by_exact_filters(self) -> None:
        alpha_page_1 = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "incremental-page",
            "requestedAfterSequence": 0,
            "requestedLimit": 1,
            "messages": [_message(5, "a1", topic="alpha")],
            "lastSequence": 20,
            "nextAfterSequence": 5,
            "hasMore": True,
            "topic": "alpha",
        }
        beta = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "latest-window",
            "requestedAfterSequence": None,
            "requestedLimit": 100,
            "messages": [_message(7, "b1", topic="beta")],
            "lastSequence": 20,
            "nextAfterSequence": 20,
            "hasMore": False,
            "topic": "beta",
        }
        alpha_page_2 = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "incremental-page",
            "requestedAfterSequence": 5,
            "requestedLimit": 1,
            "messages": [_message(9, "a2", topic="alpha")],
            "lastSequence": 20,
            "nextAfterSequence": 20,
            "hasMore": False,
            "topic": "alpha",
        }
        messages, source_set = compose_board_source_set([alpha_page_1, beta, alpha_page_2])
        self.assertEqual([item["sequence"] for item in messages], [5, 7, 9])
        assert source_set is not None
        self.assertEqual(source_set["scopeCount"], 2)
        self.assertEqual(source_set["scopes"][0]["kind"], "ordivon.media.host-board-source-scan")
        self.assertEqual(source_set["scopes"][0]["pageCount"], 2)
        self.assertEqual(source_set["scopes"][1]["selectionMode"], "latest-window")

    def test_source_set_rejects_multiple_latest_windows_for_same_scope(self) -> None:
        first = {
            "kind": "ordivon.host-board-list",
            "selectionMode": "latest-window",
            "requestedAfterSequence": None,
            "requestedLimit": 1,
            "messages": [_message(5, "a1", topic="alpha")],
            "lastSequence": 20,
            "nextAfterSequence": 20,
            "hasMore": False,
            "topic": "alpha",
        }
        second = dict(first)
        second["messages"] = [_message(6, "a2", topic="alpha")]
        with self.assertRaisesRegex(ValueError, "same filters"):
            compose_board_source_set([first, second])

    def test_board_thread_identity_is_derived_from_root_not_topic(self) -> None:
        threads = derive_board_threads(
            [
                _message(1, "root", topic="alpha"),
                _message(2, "r1", topic="alpha", reply_to="root"),
                _message(3, "r2", topic="beta", reply_to="r1"),
            ]
        )
        self.assertEqual(len(threads), 1)
        thread = threads[0]
        self.assertEqual(thread["threadId"], "board-thread:root")
        self.assertEqual(thread["rootStatus"], "present")
        self.assertEqual(thread["messageCount"], 3)
        self.assertEqual(thread["replyCount"], 2)
        self.assertEqual(thread["maxDepth"], 2)
        self.assertEqual(thread["topics"], ["alpha", "beta"])
        self.assertEqual(thread["truthRole"], BOARD_THREAD_TRUTH_ROLE)

    def test_bounded_board_snapshot_does_not_invent_missing_root(self) -> None:
        threads = derive_board_threads(
            [
                _message(8, "local-r1", reply_to="outside-root"),
                _message(9, "local-r2", reply_to="local-r1"),
            ]
        )
        self.assertEqual(len(threads), 1)
        thread = threads[0]
        self.assertIsNone(thread["threadId"])
        self.assertEqual(thread["rootStatus"], "outside-snapshot")
        self.assertEqual(thread["externalAncestorClientMessageId"], "outside-root")
        self.assertEqual(thread["messageCount"], 2)

    def test_board_thread_cycle_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "cycle"):
            derive_board_threads(
                [
                    _message(1, "a", reply_to="b"),
                    _message(2, "b", reply_to="a"),
                ]
            )

    def test_collection_is_only_a_curation_relation(self) -> None:
        collection = validate_collection(_collection())
        self.assertEqual(collection["truthRole"], COLLECTION_TRUTH_ROLE)
        self.assertEqual(len(collection["members"]), 2)
        self.assertEqual(collection["members"][0]["sourceRevision"], "a" * 40)

    def test_collection_rejects_ephemeral_conversation_source_revision(self) -> None:
        value = _collection()
        value["members"][0]["sourceRevision"] = "turn9news1"
        with self.assertRaisesRegex(ValueError, "ephemeral conversation citation"):
            validate_collection(value)

    def test_collection_rejects_duplicate_member_identity(self) -> None:
        value = _collection()
        value["members"][1]["memberId"] = "work:a"
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_collection(value)

    def test_feed_orders_supplied_sources_without_priority_claim(self) -> None:
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
        self.assertEqual(feed["truthRole"], FEED_TRUTH_ROLE)
        self.assertFalse(feed["priorityInferred"])
        self.assertFalse(feed["sourceCompletenessClaimed"])
        self.assertEqual([item["kind"] for item in feed["items"]], [
            "collection",
            "board-thread",
            "board-thread",
        ])
        self.assertEqual(feed["items"][0]["sourceIdentity"], "collection:daily-cabinet:test")
        self.assertIn("absence does not establish", feed["truthBoundary"])

    def test_feed_rejects_duplicate_source_identity(self) -> None:
        item = {
            "kind": "board-thread",
            "sourceIdentity": "board-thread:x",
            "observedAtMs": 100,
            "title": "x",
            "summary": "x",
            "truthRole": BOARD_THREAD_TRUTH_ROLE,
            "sourceDigest": "sha256:" + "0" * 64,
        }
        with self.assertRaisesRegex(ValueError, "duplicate"):
            derive_activity_feed([item, dict(item)], observed_at_ms=101)
