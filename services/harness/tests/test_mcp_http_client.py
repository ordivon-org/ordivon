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
