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


def test_official_client_lists_all_mcp_tool_pages(monkeypatch):
    """MCP 2.3.0 Client.list_tools() returns only one pagination page."""
    from types import SimpleNamespace

    seen = []

    class FakeTool:
        def __init__(self, name):
            self.name = name

        def model_dump(self, **kwargs):
            return {"name": self.name, "inputSchema": {"type": "object"}}

    class HTTP:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class MCPClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def list_tools(self, *, cursor=None):
            seen.append(cursor)
            if cursor is None:
                return SimpleNamespace(tools=(FakeTool("system.describe"),), next_cursor="next")
            assert cursor == "next"
            return SimpleNamespace(tools=(FakeTool("capability.describe"),), next_cursor=None)

    monkeypatch.setattr(
        OfficialMcpClient,
        "_sdk",
        staticmethod(lambda: (MCPClient, lambda **kwargs: HTTP(), lambda *args, **kwargs: object())),
    )
    client = OfficialMcpClient(LoopbackMcpEndpoint("http://127.0.0.1:8899/mcp"))
    names = tuple(tool["name"] for tool in client.list_tools())
    assert names == ("system.describe", "capability.describe")
    assert seen == [None, "next"]


def test_official_client_rejects_repeated_mcp_page_cursor(monkeypatch):
    from types import SimpleNamespace
    from ordivon_harness.ordivon.tool_errors import ToolBridgeError

    seen = []

    class HTTP:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class MCPClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def list_tools(self, *, cursor=None):
            seen.append(cursor)
            return SimpleNamespace(tools=(), next_cursor="repeat")

    monkeypatch.setattr(
        OfficialMcpClient,
        "_sdk",
        staticmethod(lambda: (MCPClient, lambda **kwargs: HTTP(), lambda *args, **kwargs: object())),
    )
    client = OfficialMcpClient(LoopbackMcpEndpoint("http://127.0.0.1:8899/mcp"))
    with pytest.raises(ToolBridgeError, match="repeated"):
        client.list_tools()
    assert seen == [None, "repeat"]


def test_official_client_reads_two_pages_from_real_mcp_http_server():
    """Actual MCP 2.3.0 wire, unlike mocked page-returning Client objects."""
    import asyncio
    import socket
    import threading
    import time

    import uvicorn
    from mcp import types
    from mcp.server import MCPServer

    owner = MCPServer("ordivon-mcp-paged-list-consumer")

    @owner.tool()
    def system_describe() -> dict[str, str]:
        return {"role": "first"}

    @owner.tool()
    def capability_describe() -> dict[str, str]:
        return {"role": "second"}

    pages = []
    bad_output = [False]
    hide_second = [False]

    async def paged_tools(context, params: types.PaginatedRequestParams):
        pages.append(params.cursor)
        all_tools = await owner.list_tools()
        assert len(all_tools) == 2
        by_name = {tool.name: tool for tool in all_tools}
        if params.cursor is None:
            return types.ListToolsResult(
                tools=[by_name["system_describe"]],
                next_cursor=None if hide_second[0] else "page-two",
            )
        if params.cursor == "page-two":
            return types.ListToolsResult(tools=[by_name["capability_describe"]])
        raise AssertionError("unexpected tools/list cursor")

    # Official SDK Server's public request-handler API is exercised on a local
    # in-process HTTP owner. The MCPServer adapter normally serves a one-page
    # list, so the test fixture splits that list at the *actual protocol layer*.
    owner._lowlevel_server.add_request_handler(
        "tools/list", types.PaginatedRequestParams, paged_tools
    )
    invoked = []

    async def malformed_second_page_result(context, params: types.CallToolRequestParams):
        invoked.append(params.name)
        # The actual second-page Tool schema requires str values, not bool.
        result = {"wrong": True} if bad_output[0] else {"role": "second"}
        return types.CallToolResult(
            is_error=False,
            content=[types.TextContent(type="text", text="owner result")],
            structured_content=result,
        )

    owner._lowlevel_server.add_request_handler(
        "tools/call", types.CallToolRequestParams, malformed_second_page_result
    )
    app = owner.streamable_http_app(stateless_http=True, json_response=True)
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
        names = tuple(tool["name"] for tool in client.list_tools())
        assert names == ("system_describe", "capability_describe")
        assert pages == [None, "page-two"]
        # A new MCP ClientSession must learn second-page schema BEFORE calling.
        # Ordinary valid results still pass SDK-native output-schema validation.
        assert client.call_tool("capability_describe", {}) == (
            False, {"role": "second"}
        )
        bad_output[0] = True
        # Without preflight, high-level SDK lists only the first page AFTER
        # tools/call, logs that the tool is missing, and silently returns the
        # malformed boolean output as success. On actual HTTP transports,
        # session cleanup wraps the source RuntimeError in an ExceptionGroup.
        with pytest.raises(BaseExceptionGroup) as caught:
            client.call_tool("capability_describe", {})
        assert "Invalid structured content returned" in repr(
            caught.value.subgroup(RuntimeError)
        )
        assert invoked == ["capability_describe", "capability_describe"]

        # A previously visible second-page tool may disappear before a later
        # call: reject before any physical call, never trust the old listing.
        from ordivon_harness.ordivon.tool_errors import ToolBridgeError
        hide_second[0] = True
        with pytest.raises(ToolBridgeError, match="missing from tools/list"):
            client.call_tool("capability_describe", {})
        assert invoked == ["capability_describe", "capability_describe"]
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive()


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
