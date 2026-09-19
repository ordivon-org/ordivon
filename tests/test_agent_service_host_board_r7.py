from __future__ import annotations

import unittest

from agent_service.host_board import HostBoardMcpAdapter, HostBoardProtocolError


class FakeToolCaller:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, name: str, arguments: dict) -> dict:
        self.calls.append((name, arguments))
        if not self.responses:
            raise AssertionError(f"unexpected tool call {name}")
        return self.responses.pop(0)


class HostBoardMcpAdapterTests(unittest.TestCase):
    def test_post_calls_only_board_post_and_preserves_exact_identity(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "schemaVersion": 2,
                    "kind": "ordivon.host-board-post-receipt",
                    "admission": "committed",
                    "message": {
                        "sequence": 42,
                        "clientMessageId": "goal-event:abc",
                        "authorLabel": "agent-service-board-projector-v1",
                        "messageKind": "note",
                        "topic": "agent-service-goal-projection",
                        "message": "projection",
                        "replyToClientMessageId": None,
                        "recordedAtMs": 1,
                        "messageDigest": "sha256:" + "a" * 64,
                        "truthRole": "coordination-message-not-domain-truth",
                    },
                    "replyOccupancy": None,
                    "truthBoundary": "collaboration only",
                }
            ]
        )
        adapter = HostBoardMcpAdapter(caller)

        ref = adapter.post(
            client_message_id="goal-event:abc",
            author_label="agent-service-board-projector-v1",
            message="projection",
            topic="agent-service-goal-projection",
        )

        self.assertEqual(ref.client_message_id, "goal-event:abc")
        self.assertEqual(ref.provider_sequence, 42)
        self.assertEqual(caller.calls[0][0], "board.post")
        self.assertEqual(
            caller.calls[0][1],
            {
                "clientMessageId": "goal-event:abc",
                "authorLabel": "agent-service-board-projector-v1",
                "message": "projection",
                "messageKind": "note",
                "topic": "agent-service-goal-projection",
            },
        )

    def test_existing_replay_is_accepted_as_same_board_identity(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "schemaVersion": 2,
                    "kind": "ordivon.host-board-post-receipt",
                    "admission": "existing",
                    "message": {
                        "sequence": 99,
                        "clientMessageId": "goal-event:abc",
                        "authorLabel": "agent-service-board-projector-v1",
                        "messageKind": "note",
                        "topic": "agent-service-goal-projection",
                        "message": "projection",
                        "replyToClientMessageId": None,
                        "recordedAtMs": 1,
                        "messageDigest": "sha256:" + "a" * 64,
                        "truthRole": "coordination-message-not-domain-truth",
                    },
                    "replyOccupancy": None,
                    "truthBoundary": "collaboration only",
                }
            ]
        )
        adapter = HostBoardMcpAdapter(caller)

        ref = adapter.post(
            client_message_id="goal-event:abc",
            author_label="agent-service-board-projector-v1",
            message="projection",
            topic="agent-service-goal-projection",
        )

        self.assertEqual(ref.provider_sequence, 99)

    def test_mismatched_provider_message_identity_fails_closed(self) -> None:
        caller = FakeToolCaller(
            [
                {
                    "schemaVersion": 2,
                    "kind": "ordivon.host-board-post-receipt",
                    "admission": "committed",
                    "message": {
                        "sequence": 1,
                        "clientMessageId": "other",
                    },
                }
            ]
        )
        adapter = HostBoardMcpAdapter(caller)

        with self.assertRaises(HostBoardProtocolError):
            adapter.post(
                client_message_id="expected",
                author_label="agent-service-board-projector-v1",
                message="projection",
                topic="agent-service-goal-projection",
            )

    def test_adapter_rejects_unexpected_receipt_kind_or_admission(self) -> None:
        for response in (
            {"schemaVersion": 2, "kind": "wrong", "admission": "committed", "message": {}},
            {
                "schemaVersion": 2,
                "kind": "ordivon.host-board-post-receipt",
                "admission": "mystery",
                "message": {},
            },
        ):
            with self.subTest(response=response):
                adapter = HostBoardMcpAdapter(FakeToolCaller([response]))
                with self.assertRaises(HostBoardProtocolError):
                    adapter.post(
                        client_message_id="expected",
                        author_label="agent-service-board-projector-v1",
                        message="projection",
                        topic="agent-service-goal-projection",
                    )

if __name__ == "__main__":
    unittest.main()
