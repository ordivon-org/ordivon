from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService


class PrincipalScopedOwner:
    """A fake of the existing Runtime idempotency and list surfaces."""

    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name, dict(arguments)))
        if owner_id != "runtime.linux":
            raise AssertionError(owner_id)
        if tool_name == "workspace.exec":
            request_id = arguments["clientRequestId"]
            workspace = arguments["execution"]["workspaceId"]
            job = self.jobs.setdefault(
                request_id,
                {
                    "jobId": f"job-namespace-{len(self.jobs) + 1}",
                    "clientRequestId": request_id,
                    "workspaceId": workspace,
                },
            )
            return {
                "jobId": job["jobId"],
                "status": "working",
                "executionTerminal": False,
                "deliveryDisposition": "in_progress",
            }
        if tool_name == "job.list":
            job = self.jobs.get(arguments["clientRequestId"])
            return {"jobs": [job] if job else [], "nextCursor": None}
        if tool_name == "job.observe":
            return {
                "jobId": arguments["jobId"],
                "status": "working",
                "executionTerminal": False,
                "deliveryDisposition": "in_progress",
                "artifacts": [],
            }
        if tool_name == "artifact.read":
            return {
                "jobId": arguments["jobId"],
                "artifactId": arguments["artifactId"],
                "offset": arguments["offset"],
                "nextOffset": arguments["offset"] + 3,
                "eof": True,
                "digest": "sha256:artifact-owner",
                "content": "abc",
            }
        if tool_name == "job.cancel":
            return {
                "jobId": arguments["jobId"],
                "status": "cancelled",
                "executionTerminal": True,
                "deliveryDisposition": "committed",
            }
        raise AssertionError(tool_name)


def _context(server: Any, principal: str) -> Context:
    context = SimpleNamespace(
        request=SimpleNamespace(
            scope={
                "state": {
                    "ordivon_access_principal": principal,
                    "ordivon_access_issuer": "https://team.cloudflareaccess.com",
                }
            }
        )
    )
    return Context(request_context=context, mcp_server=server)


def test_verified_principals_cannot_reattach_each_others_request_id() -> None:
    owner = PrincipalScopedOwner()
    server = build_server(GatewayService(owner))
    a = _context(server, "principal:cf-access:A")
    b = _context(server, "principal:cf-access:B")
    req = "request:shared-by-attacker"

    async def scenario() -> None:
        submission = await server.call_tool(
            "execution.submit",
            {
                "capability": "execution.linux",
                "requestId": req,
                "workspaceId": "ws-shared",
                "executable": "/usr/bin/true",
                "args": [],
            },
            a,
        )
        assert not submission.is_error
        owner_req_a = owner.calls[-1][2]["clientRequestId"]
        assert owner_req_a != req
        assert owner_req_a.startswith("request:gw-principal:")

        resolved_a = await server.call_tool(
            "execution.resolve", {"capability": "execution.linux", "requestId": req}, a
        )
        assert not resolved_a.is_error
        assert resolved_a.structured_content["resolution"] == "found"
        assert resolved_a.structured_content["request_id"] == req
        assert owner.calls[-1][2]["clientRequestId"] == owner_req_a

        resolved_b = await server.call_tool(
            "execution.resolve", {"capability": "execution.linux", "requestId": req}, b
        )
        assert not resolved_b.is_error
        assert resolved_b.structured_content["resolution"] == "absent"
        assert resolved_b.structured_content["request_id"] == req
        assert owner.calls[-1][2]["clientRequestId"] != owner_req_a

        operation_ref = "ordivon-exec:v1:runtime.linux:job-namespace-1"
        qualified = {
            "operationRef": operation_ref,
            "requestId": req,
            "capability": "execution.linux",
        }
        for operation in ("execution.get", "execution.cancel"):
            before = len(owner.calls)
            with pytest.raises(ToolError, match="cannot be qualified"):
                await server.call_tool(operation, qualified, b)
            assert all(
                name not in {"job.observe", "job.cancel"} for _, name, _ in owner.calls[before:]
            )
            with pytest.raises(ToolError, match="requires original requestId"):
                await server.call_tool(operation, {"operationRef": operation_ref}, b)

        own_observation = await server.call_tool("execution.get", qualified, a)
        assert not own_observation.is_error
        assert own_observation.structured_content["native_id"] == "job-namespace-1"
        own_cancellation = await server.call_tool("execution.cancel", qualified, a)
        assert not own_cancellation.is_error

        submit_b = await server.call_tool(
            "execution.submit",
            {
                "capability": "execution.linux",
                "requestId": req,
                "workspaceId": "ws-shared",
                "executable": "/usr/bin/true",
                "args": [],
            },
            b,
        )
        assert not submit_b.is_error
        assert len(owner.jobs) == 2
        assert owner.calls[-1][2]["clientRequestId"] != owner_req_a

    asyncio.run(scenario())


def test_verified_external_execution_preserves_owner_capability_and_identity() -> None:
    from ordivon_gateway.contracts import (
        ArtifactChunk,
        ExecutionObservation,
        ExecutionReceipt,
        ExecutionResolution,
    )
    from ordivon_gateway.mcp_server import _verified_execution_request_id

    capability = "muse.shell.echo"
    public_request = "same-original-external-request"
    operation_ref = "ordivon-exec:v1:external.pull:op-01"

    class ExternalCapability:
        def __init__(self) -> None:
            self.operations: dict[str, str] = {}
            self.observe_count = 0
            self.cancel_count = 0
            self.artifact_count = 0

        async def execution_resolve(self, *, capability: str, request_id: str):
            matched = self.operations.get(request_id)
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id="external.pull",
                resolution="found" if matched else "absent",
                operation_ref=matched,
                native_id="op-01" if matched else None,
                workspace_id="ws-external" if matched else None,
            )

        async def execution_get(self, operation_ref: str, *, event_limit=10, wait_ms=0):
            self.observe_count += 1
            return ExecutionObservation(
                operation_ref=operation_ref,
                capability=capability,
                owner_id="external.pull",
                native_id="op-01",
                state="working",
                terminal=False,
            )

        async def execution_cancel(self, operation_ref: str):
            self.cancel_count += 1
            return ExecutionReceipt(
                operation_ref=operation_ref,
                capability=capability,
                owner_id="external.pull",
                native_id="op-01",
                state="cancelled",
                terminal=True,
            )

        async def artifact_read(
            self, operation_ref: str, artifact_id: str, *, offset=0, max_bytes=1_048_576
        ):
            self.artifact_count += 1
            return ArtifactChunk(
                operation_ref=operation_ref,
                owner_id="external.pull",
                native_id="op-01",
                artifact_id=artifact_id,
                offset=offset,
                next_offset=offset + 3,
                eof=True,
                digest="sha256:external-test-byte-witness",
                content="abc",
            )

    owner = ExternalCapability()
    server = build_server(owner)  # type: ignore[arg-type]
    a = _context(server, "principal:cf-access:A")
    b = _context(server, "principal:cf-access:B")
    owner.operations[_verified_execution_request_id(public_request, capability, a)] = operation_ref
    arguments = {
        "operationRef": operation_ref,
        "capability": capability,
        "requestId": public_request,
    }

    async def run():
        assert not (await server.call_tool("execution.get", arguments, a)).is_error
        assert not (await server.call_tool("execution.cancel", arguments, a)).is_error
        for action in ("execution.get", "execution.cancel"):
            with pytest.raises(ToolError, match="cannot be qualified"):
                await server.call_tool(action, arguments, b)
        read_args = {**arguments, "artifactId": "stdout"}
        own_bytes = await server.call_tool("artifact.read", read_args, a)
        assert not own_bytes.is_error
        assert own_bytes.structured_content["content"] == "abc"
        with pytest.raises(ToolError, match="cannot be qualified"):
            await server.call_tool("artifact.read", read_args, b)
        assert owner.observe_count == 1
        assert owner.cancel_count == 1
        assert owner.artifact_count == 1

    asyncio.run(run())


def test_different_capability_namespace_and_unqualified_legacy() -> None:
    from ordivon_gateway.mcp_server import _verified_execution_request_id

    server = build_server(service=object())  # type: ignore[arg-type]
    a = _context(server, "principal:cf-access:A")
    principal_input = _verified_execution_request_id("req", "execution.linux", a)
    assert principal_input == _verified_execution_request_id("req", "execution.linux", a)
    assert principal_input != _verified_execution_request_id("req", "execution.windows", a)
    assert principal_input != _verified_execution_request_id(
        "req", "execution.linux", _context(server, "principal:cf-access:B")
    )
    # No verified ingress is NOT an attested continuity claim.
    unqualified = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(scope={})), mcp_server=server
    )
    assert _verified_execution_request_id("req", "execution.linux", unqualified) == "req"
    other_issuer = Context(
        request_context=SimpleNamespace(
            request=SimpleNamespace(
                scope={
                    "state": {
                        "ordivon_access_principal": "principal:cf-access:A",
                        "ordivon_access_issuer": "https://different-issuer.example",
                    }
                }
            )
        ),
        mcp_server=server,
    )
    assert _verified_execution_request_id("req", "execution.linux", other_issuer) != principal_input

    tools = asyncio.run(server.list_tools())
    for tool in tools:
        if tool.name in {"execution.submit", "execution.resolve"}:
            assert "ctx" not in tool.input_schema.get("properties", {})
            assert "ctx" not in tool.input_schema.get("required", [])


def test_verified_http_artifact_read_requires_original_owner_request_identity() -> None:
    """An operationRef alone must not reveal another verified principal's bytes."""
    owner = PrincipalScopedOwner()
    server = build_server(GatewayService(owner))
    a = _context(server, "principal:cf-access:A")
    b = _context(server, "principal:cf-access:B")
    public_request_id = "request:artifact-A"

    async def scenario() -> None:
        submitted = await server.call_tool(
            "execution.submit",
            {
                "capability": "execution.linux",
                "requestId": public_request_id,
                "workspaceId": "ws-same",
                "executable": "/usr/bin/true",
                "args": [],
            },
            a,
        )
        assert not submitted.is_error
        ref = "ordivon-exec:v1:runtime.linux:job-namespace-1"
        qualified = {
            "operationRef": ref,
            "artifactId": "stdout",
            "requestId": public_request_id,
            "capability": "execution.linux",
        }
        denied = [
            (b, qualified),
            (b, {"operationRef": ref, "artifactId": "stdout"}),
            (a, {**qualified, "requestId": "request:wrong"}),
            (a, {**qualified, "capability": "execution.windows"}),
        ]
        for context, args in denied:
            before = len(owner.calls)
            with pytest.raises(ToolError):
                await server.call_tool("artifact.read", args, context)
            assert all(name != "artifact.read" for _, name, _ in owner.calls[before:])
        good = await server.call_tool("artifact.read", qualified, a)
        assert not good.is_error
        assert good.structured_content["content"] == "abc"
        assert owner.calls[-1][1] == "artifact.read"

    asyncio.run(scenario())
