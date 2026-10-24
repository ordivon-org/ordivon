from __future__ import annotations

import pytest

from ordivon_harness.agent_plugin import AgentPluginMcpComponent
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.plugin_mcp import OfficialMcpClient as PluginOfficialMcpClient


def test_loopback_endpoint_is_internal_http_only():
    endpoint = LoopbackMcpEndpoint('http://127.0.0.1:8899/mcp')
    assert endpoint.url == 'http://127.0.0.1:8899/mcp'
    for bad in (
        'https://127.0.0.1:8899/mcp',
        'http://localhost:8899/mcp',
        'http://192.168.1.2:8899/mcp',
        'http://127.0.0.1:8899/other',
    ):
        with pytest.raises(ValueError):
            LoopbackMcpEndpoint(bad)


def test_agent_plugin_https_policy_is_unchanged_and_client_is_shared():
    with pytest.raises(Exception):
        AgentPluginMcpComponent(name='gateway', transport='streamable-http', url='http://127.0.0.1:8899/mcp')
    assert PluginOfficialMcpClient is OfficialMcpClient

def test_official_client_reads_private_bearer_at_call_time(tmp_path):
    credential = tmp_path / 'gateway-local-bearer'
    credential.write_text('z' * 64)
    credential.chmod(0o600)
    client = OfficialMcpClient(
        LoopbackMcpEndpoint('http://127.0.0.1:8899/mcp'),
        bearer_token_file=credential,
    )
    assert client._request_headers() == {'Authorization': 'Bearer ' + 'z' * 64}
    credential.write_text('y' * 64)
    assert client._request_headers() == {'Authorization': 'Bearer ' + 'y' * 64}
    credential.chmod(0o644)
    with pytest.raises(ValueError):
        client._request_headers()


def test_official_mcp_http_client_preserves_unstructured_native_tool_error():
    """Real official MCP HTTP owner->client contract, including later recovery."""
    import asyncio
    import socket
    import threading
    import time

    import uvicorn
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError

    server_owner = MCPServer("ordivon-mcp-text-error-consumer")

    @server_owner.tool()
    def unavailable(item: str) -> dict[str, str]:
        raise ToolError(f"expected missing item: {item}")

    @server_owner.tool()
    def healthy(item: str) -> dict[str, str]:
        return {"item": item}

    app = server_owner.streamable_http_app(stateless_http=True, json_response=True)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", log_level="error"))
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(8)
    port = sock.getsockname()[1]
    thread = threading.Thread(
        target=lambda: asyncio.run(server.serve(sockets=[sock])), daemon=True
    )
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started, "MCP server failed to start"
        client = OfficialMcpClient(LoopbackMcpEndpoint(f"http://127.0.0.1:{port}/mcp"))
        failed, payload = client.call_tool("unavailable", {"item": "sample"})
        assert failed is True
        assert payload["isError"] is True
        assert payload["content"][0]["type"] == "text"
        assert "expected missing item" in payload["content"][0]["text"]
        assert client.call_tool("healthy", {"item": "recovered"}) == (
            False,
            {"item": "recovered"},
        )
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive()
