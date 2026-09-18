from __future__ import annotations

import json
import shlex
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .goals import BoardAdapter, BoardMessageRef


HOST_MCP_PROTOCOL_VERSION = "2025-11-25"


class HostBoardProtocolError(RuntimeError):
    pass


class HostBoardToolError(RuntimeError):
    def __init__(self, tool_name: str, error: object) -> None:
        super().__init__(f"Host Board tool {tool_name} failed")
        self.tool_name = tool_name
        self.error = error


def _parse_http_response(content_type: str, body: bytes) -> dict[str, Any]:
    if not body:
        raise HostBoardProtocolError("Host MCP returned an empty response")
    text = body.decode("utf-8")
    if "text/event-stream" in content_type:
        data_lines = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
        if not data_lines:
            raise HostBoardProtocolError("Host MCP SSE response contained no data event")
        value = json.loads(data_lines[-1])
    else:
        value = json.loads(text)
    if not isinstance(value, dict):
        raise HostBoardProtocolError("Host MCP response must be a JSON object")
    return value


def _env_value(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    try:
        values = shlex.split(raw, posix=True)
    except ValueError as error:
        raise ValueError("invalid Host environment value") from error
    if len(values) != 1:
        raise ValueError("Host environment value must resolve to one token")
    return values[0]


class HostBoardMcpHttpClient:
    """Narrow local stateless MCP client used only by the Host Board adapter."""

    def __init__(self, endpoint: str, *, timeout_seconds: float = 10.0) -> None:
        if not endpoint.startswith("http://"):
            raise ValueError("local Host Board endpoint must use http:// loopback transport")
        self.endpoint = endpoint
        self.timeout_seconds = float(timeout_seconds)
        self._request_id = 0

    def __repr__(self) -> str:
        return f"HostBoardMcpHttpClient(endpoint={self.endpoint!r})"

    @classmethod
    def from_host_env(
        cls,
        env_file: str | Path = "/etc/ordivon/host-v2.env",
        *,
        timeout_seconds: float = 10.0,
    ) -> "HostBoardMcpHttpClient":
        values: dict[str, str] = {}
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, raw = stripped.split("=", 1)
            values[key.strip()] = _env_value(raw)
        if values.get("ORDIVON_HOST_V2_TRANSPORT") != "streamable-http":
            raise ValueError("Host Board adapter requires streamable-http transport")
        host = values.get("ORDIVON_HOST_V2_HOST", "127.0.0.1")
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Host Board adapter requires loopback Host v2 binding")
        port_raw = values.get("ORDIVON_HOST_V2_PORT", "8898")
        try:
            port = int(port_raw)
        except ValueError as error:
            raise ValueError("Host v2 port must be an integer") from error
        if port < 1 or port > 65535:
            raise ValueError("Host v2 port is outside TCP range")
        path = values.get("ORDIVON_HOST_V2_PATH", "/mcp")
        if not path.startswith("/"):
            raise ValueError("Host v2 MCP path must start with /")
        display_host = f"[{host}]" if host == "::1" else host
        return cls(f"http://{display_host}:{port}{path}", timeout_seconds=timeout_seconds)

    def _tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        request_id = self._request_id
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": HOST_MCP_PROTOCOL_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                status = int(response.status)
                message = _parse_http_response(
                    response.headers.get("Content-Type", ""), response.read()
                )
        except urllib.error.HTTPError as error:
            status = int(error.code)
            message = _parse_http_response(error.headers.get("Content-Type", ""), error.read())
        if message.get("id") != request_id:
            raise HostBoardProtocolError("Host MCP response id mismatch")
        rpc_error = message.get("error")
        if status >= 400 or isinstance(rpc_error, dict):
            raise HostBoardToolError(name, rpc_error if isinstance(rpc_error, dict) else message)
        result = message.get("result")
        if not isinstance(result, dict):
            raise HostBoardProtocolError("Host MCP tools/call omitted result object")
        if result.get("isError") is True:
            raise HostBoardToolError(name, result.get("structuredContent", result))
        structured = result.get("structuredContent")
        if not isinstance(structured, dict):
            raise HostBoardProtocolError("Host MCP tool omitted structuredContent")
        return structured


ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]


class HostBoardMcpAdapter(BoardAdapter):
    """Projection-only provider: Agent Service Goal events -> Host Board messages."""

    def __init__(self, caller: ToolCaller | HostBoardMcpHttpClient) -> None:
        self._call: ToolCaller = caller._tool if isinstance(caller, HostBoardMcpHttpClient) else caller

    @classmethod
    def from_local_host_env(
        cls,
        env_file: str | Path = "/etc/ordivon/host-v2.env",
    ) -> "HostBoardMcpAdapter":
        return cls(HostBoardMcpHttpClient.from_host_env(env_file))

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
            raise HostBoardProtocolError("Host board.post returned unexpected receipt kind")
        if value.get("admission") not in {"committed", "existing"}:
            raise HostBoardProtocolError("Host board.post returned unexpected admission state")
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
