from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_service.host_board import HostBoardMcpAdapter, HostBoardMcpHttpClient, HostBoardProtocolError


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

    def test_http_client_factory_derives_loopback_endpoint_from_host_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / "host.env"
            env.write_text(
                "ORDIVON_HOST_V2_TRANSPORT=streamable-http\n"
                "ORDIVON_HOST_V2_HOST=127.0.0.1\n"
                "ORDIVON_HOST_V2_PORT=8898\n"
                "ORDIVON_HOST_V2_PATH=/mcp\n",
                encoding="utf-8",
            )

            client = HostBoardMcpHttpClient.from_host_env(env)

            self.assertEqual(client.endpoint, "http://127.0.0.1:8898/mcp")
            self.assertNotIn("token", repr(client).lower())

    def test_http_client_factory_rejects_non_http_or_non_loopback_config(self) -> None:
        cases = (
            "ORDIVON_HOST_V2_TRANSPORT=stdio\nORDIVON_HOST_V2_HOST=127.0.0.1\nORDIVON_HOST_V2_PORT=8898\nORDIVON_HOST_V2_PATH=/mcp\n",
            "ORDIVON_HOST_V2_TRANSPORT=streamable-http\nORDIVON_HOST_V2_HOST=0.0.0.0\nORDIVON_HOST_V2_PORT=8898\nORDIVON_HOST_V2_PATH=/mcp\n",
            "ORDIVON_HOST_V2_TRANSPORT=streamable-http\nORDIVON_HOST_V2_HOST=127.0.0.1\nORDIVON_HOST_V2_PORT=8898\nORDIVON_HOST_V2_PATH=mcp\n",
        )
        for content in cases:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as tmp:
                    env = Path(tmp) / "host.env"
                    env.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        HostBoardMcpHttpClient.from_host_env(env)


if __name__ == "__main__":
    unittest.main()
