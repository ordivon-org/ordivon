from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .goals import BoardMessageRef


class HostBoardProtocolError(RuntimeError):
    pass


ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]


class HostBoardMcpAdapter:
    """Projection-only provider: Agent Service Goal events -> Host Board messages."""

    def __init__(self, caller: ToolCaller) -> None:
        self._call = caller

    def post(
        self,
        *,
        client_message_id: str,
        author_label: str,
        message: str,
        topic: str,
    ) -> BoardMessageRef:
        value = self._call(
            "board.post",
            {
                "clientMessageId": client_message_id,
                "authorLabel": author_label,
                "message": message,
                "messageKind": "note",
                "topic": topic,
            },
        )
        if value.get("kind") != "ordivon.host-board-post-receipt":
            raise HostBoardProtocolError(
                "Host board.post returned unexpected receipt kind"
            )
        if value.get("admission") not in {"committed", "existing"}:
            raise HostBoardProtocolError(
                "Host board.post returned unexpected admission state"
            )
        board_message = value.get("message")
        if not isinstance(board_message, dict):
            raise HostBoardProtocolError("Host board.post omitted message receipt")
        if board_message.get("clientMessageId") != client_message_id:
            raise HostBoardProtocolError("Host Board message identity mismatch")
        sequence = board_message.get("sequence")
        if not isinstance(sequence, int) or sequence < 1:
            raise HostBoardProtocolError("Host Board receipt omitted valid sequence")
        return BoardMessageRef(
            client_message_id=client_message_id,
            provider_sequence=sequence,
        )
