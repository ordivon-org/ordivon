"""Artifact cursor types must survive the native MCP wire boundary."""

from __future__ import annotations

import asyncio

import pytest
from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService


class _ArtifactOwner:
    def __init__(self):
        self.calls = []

    def is_configured(self, owner_id):
        return owner_id == "runtime.linux"

    async def call_tool(self, owner_id, tool_name, arguments):
        self.calls.append((owner_id, tool_name, arguments))
        assert owner_id == "runtime.linux" and tool_name == "artifact.read"
        return {
            "jobId": arguments["jobId"],
            "artifactId": arguments["artifactId"],
            "offset": arguments["offset"],
            "nextOffset": arguments["offset"] + 1,
            "eof": True,
            "digest": "sha256:" + "a" * 64,
            "content": "x",
        }


@pytest.mark.parametrize(
    ("offset", "max_bytes"),
    [
        (True, 1),
        (False, 1),
        (0, True),
        (0, False),
        ("1", 1),
        (0, "1"),
        (1.0, 1),
        (0, 1.0),
        (1.5, 1),
        (-1, 1),
        (0, 0),
        (0, 1_048_577),
    ],
)
def test_artifact_read_native_wire_rejects_invalid_cursors(offset, max_bytes):
    owner = _ArtifactOwner()

    async def run():
        async with Client(build_server(GatewayService(owner)), raise_exceptions=False) as client:
            result = await client.call_tool(
                "artifact.read",
                {
                    "operationRef": "ordivon-exec:v1:runtime.linux:job-fixture",
                    "artifactId": "artifact-fixture",
                    "offset": offset,
                    "maxBytes": max_bytes,
                },
            )
            assert result.is_error

    asyncio.run(run())
    assert owner.calls == []


@pytest.mark.parametrize(("offset", "max_bytes"), [(0, 1), (7, 1_048_576)])
def test_artifact_read_native_wire_preserves_valid_cursors(offset, max_bytes):
    owner = _ArtifactOwner()

    async def run():
        async with Client(build_server(GatewayService(owner)), raise_exceptions=False) as client:
            result = await client.call_tool(
                "artifact.read",
                {
                    "operationRef": "ordivon-exec:v1:runtime.linux:job-fixture",
                    "artifactId": "artifact-fixture",
                    "offset": offset,
                    "maxBytes": max_bytes,
                },
            )
            assert not result.is_error

    asyncio.run(run())
    assert len(owner.calls) == 1
    assert owner.calls[0][2]["offset"] == offset
    assert owner.calls[0][2]["maxBytes"] == max_bytes
