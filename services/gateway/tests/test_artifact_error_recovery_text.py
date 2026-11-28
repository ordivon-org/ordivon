from __future__ import annotations

import asyncio

import pytest
from mcp import Client

from ordivon_gateway.logic.owner_protocol import OwnerCallError
from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService
from ordivon_gateway.transport.owner_error_projection import owner_error_result


def artifact_error(code: str, **overrides):
    return {
        "code": code,
        "message": "PRIVATE_OWNER_DETAIL_DO_NOT_PROJECT",
        "origin": "runtime_core",
        "retryable": False,
        "retryClass": "never",
        "commitState": "not_committed",
        "field": "artifactId",
        **overrides,
    }


@pytest.mark.parametrize(
    ("code", "action"),
    [
        ("ARTIFACT_NOT_UTF8", "authorized-binary-owner-path"),
        ("ARTIFACT_NOT_FOUND", "reobserve-original-operation"),
        ("ARTIFACT_IDENTITY_CONFLICT", "stop-consumption"),
    ],
)
def test_runtime_artifact_recovery_survives_text_only_mcp_consumer(code, action):
    error = artifact_error(code)

    class Owner:
        def is_configured(self, owner_id):
            return owner_id == "runtime.linux"

        async def call_tool(self, owner_id, tool_name, arguments):
            assert owner_id == "runtime.linux"
            assert tool_name == "artifact.read"
            raise OwnerCallError(
                "owner tool returned error: runtime.linux/artifact.read",
                owner_id=owner_id,
                tool_name=tool_name,
                error=error,
            )

    async def run():
        async with Client(build_server(GatewayService(Owner())), raise_exceptions=False) as client:
            result = await client.call_tool(
                "artifact.read",
                {
                    "operationRef": "ordivon-exec:v1:runtime.linux:job-test",
                    "artifactId": "artifact-test",
                },
            )
            assert result.is_error is True
            assert result.structured_content["error"] == error
            visible = result.content[0].text
            assert code in visible
            assert action in visible
            assert "retryable=false" in visible
            assert "PRIVATE_OWNER_DETAIL" not in visible
            assert len(visible) < 350

    asyncio.run(run())


@pytest.mark.parametrize(
    ("owner", "tool", "overrides"),
    [
        ("runtime.linux", "artifact.read", {"code": "REGISTRY_UNAVAILABLE"}),
        ("runtime.linux", "artifact.read", {"code": ["ARTIFACT_NOT_UTF8"]}),
        ("runtime.linux", "artifact.read", {"retryable": 0}),
        ("runtime.linux", "artifact.read", {"retryClass": "retry"}),
        ("runtime.linux", "artifact.read", {"commitState": "committed"}),
        ("runtime.linux", "artifact.read", {"origin": "gateway_adapter"}),
        ("runtime.linux", "artifact.read", {"field": "private"}),
        ("runtime.linux", "workspace.exec", {}),
        ("host", "artifact.read", {}),
    ],
)
def test_unqualified_error_does_not_gain_recovery_authority(owner, tool, overrides):
    error = artifact_error("ARTIFACT_NOT_UTF8")
    error.update(overrides)
    result = owner_error_result(
        OwnerCallError("safe generic", owner_id=owner, tool_name=tool, error=error)
    )
    assert result.is_error is True
    assert result.content[0].text == "safe generic"
