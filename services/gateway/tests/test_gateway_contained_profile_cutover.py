"""Original Gateway consumer: restricted Native Runtime cutover without replay drift.

These tests model only the HTTP Owner contract and preserve the real Runtime
permission boundary. The separate Native PostgreSQL integration test qualifies
the actual Runtime denial/replay/contained systemd effects.
"""

from __future__ import annotations

import asyncio
import json
import socket
from typing import Any

import pytest

from ordivon_gateway.service import GatewayService
from ordivon_gateway.transport.upstream import OwnerCallError


class ProfileCutoverOwner:
    def __init__(self, *, contained_only: bool = False) -> None:
        self.contained_only = contained_only
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.committed: dict[str, tuple[dict[str, Any], str]] = {}
        self.description: dict[str, Any] = {
            "schemaVersion": 1,
            "node": {"nodeId": "linux-pg", "platform": "linux", "native": True},
            "targets": [
                {
                    "target": "local_linux",
                    "configured": True,
                    "available": True,
                    "executionProfiles": ["contained_local"],
                }
            ],
        }
        self.denial_override: dict[str, Any] | None = None

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name, arguments))
        assert owner_id == "runtime.linux"
        if tool_name == "runtime.describe":
            return self.description
        assert tool_name == "workspace.exec"
        request_id = arguments["clientRequestId"]
        existing = self.committed.get(request_id)
        if existing is not None:
            request, job_id = existing
            if request != arguments:
                raise OwnerCallError(
                    "original committed proposal identity differs",
                    owner_id=owner_id,
                    tool_name=tool_name,
                    error={
                        "origin": "runtime_core",
                        "code": "IDEMPOTENCY_CONFLICT",
                        # The existing native PG IdempotencyConflict mapping
                        # intentionally omits 'field'; it is an exact-key
                        # durable identity conflict, not a new admission.
                        "commitState": "not_committed",
                        "retryClass": "never",
                        "retryable": False,
                        "message": "original content differs",
                    },
                )
            return {"jobId": job_id, "status": "succeeded", "executionTerminal": True}
        if self.contained_only and arguments["execution"]["executionProfile"] != "contained_local":
            raise OwnerCallError(
                "original native profile admission denied",
                owner_id=owner_id,
                tool_name=tool_name,
                error=self.denial_override
                or {
                    "origin": "runtime_core",
                    "code": "AUTHORIZATION_DENIED",
                    "field": "execution.executionProfile",
                    "commitState": "not_committed",
                    "retryClass": "never",
                    "retryable": False,
                    "message": "authenticated ingress does not authorize this executionProfile",
                },
            )
        job_id = f"job-original-{len(self.committed) + 1}"
        self.committed[request_id] = (arguments, job_id)
        return {"jobId": job_id, "status": "succeeded", "executionTerminal": True}


def _submit(service: GatewayService, request_id: str, **kwargs: Any):
    return service.execution_submit(
        capability="execution.linux",
        request_id=request_id,
        workspace_id="ws-original",
        executable="/usr/bin/printf",
        args=["original"],
        **kwargs,
    )


def test_legacy_default_is_exactly_one_trusted_owner_call() -> None:
    owner = ProfileCutoverOwner()
    receipt = asyncio.run(_submit(GatewayService(owner), "original-key"))
    assert receipt.native_id == "job-original-1"
    assert [tool for _, tool, _ in owner.calls] == ["workspace.exec"]
    assert owner.calls[0][2]["execution"]["executionProfile"] == "trusted_local"


def test_old_committed_trusted_job_recovered_before_new_policy_change() -> None:
    owner = ProfileCutoverOwner()
    service = GatewayService(owner)
    old = asyncio.run(_submit(service, "original-key"))
    original_request = owner.calls[-1][2]
    owner.contained_only = True
    after = asyncio.run(_submit(service, "original-key"))
    assert old.native_id == after.native_id
    assert len(owner.committed) == 1
    assert [tool for _, tool, _ in owner.calls] == ["workspace.exec", "workspace.exec"]
    assert owner.calls[-1][2] == original_request


def test_new_uncommitted_denial_selects_only_qualified_owner_contained_profile() -> None:
    owner = ProfileCutoverOwner(contained_only=True)
    receipt = asyncio.run(
        _submit(
            GatewayService(owner),
            "new-key",
            env={"ARTIFACT_SOURCE": "original"},
            timeout_ms=15000,
            stdout_limit_bytes=2048,
            stderr_limit_bytes=1024,
        )
    )
    assert receipt.native_id == "job-original-1"
    assert [tool for _, tool, _ in owner.calls] == [
        "workspace.exec",
        "runtime.describe",
        "workspace.exec",
    ]
    first = owner.calls[0][2]
    second = owner.calls[-1][2]
    assert first["clientRequestId"] == second["clientRequestId"] == "new-key"
    assert first["execution"]["executionProfile"] == "trusted_local"
    assert second["execution"]["executionProfile"] == "contained_local"
    assert {k: v for k, v in first["execution"].items() if k != "executionProfile"} == {
        k: v for k, v in second["execution"].items() if k != "executionProfile"
    }
    assert first["stdoutTailBytes"] == second["stdoutTailBytes"]
    assert first["stderrTailBytes"] == second["stderrTailBytes"]
    assert len(owner.committed) == 1


def test_new_contained_job_replays_same_original_key_after_gateway_restart() -> None:
    owner = ProfileCutoverOwner(contained_only=True)
    first = asyncio.run(_submit(GatewayService(owner), "new-contained-original-key"))
    assert first.native_id == "job-original-1"
    first_committed = owner.committed["new-contained-original-key"][0]
    assert first_committed["execution"]["executionProfile"] == "contained_local"
    # No Gateway cache or shadow Job Registry survives this new façade.
    again = asyncio.run(_submit(GatewayService(owner), "new-contained-original-key"))
    assert again.native_id == first.native_id
    assert len(owner.committed) == 1
    assert [tool for _, tool, _ in owner.calls] == [
        "workspace.exec",
        "runtime.describe",
        "workspace.exec",
        "workspace.exec",
        "runtime.describe",
        "workspace.exec",
    ]
    assert owner.calls[-1][2] == first_committed


def test_explicit_privileged_context_is_not_automatically_downgraded() -> None:
    owner = ProfileCutoverOwner(contained_only=True)
    with pytest.raises(OwnerCallError) as exc:
        asyncio.run(_submit(GatewayService(owner), "new-privileged", context="trusted_local"))
    assert exc.value.error is not None
    assert exc.value.error["code"] == "AUTHORIZATION_DENIED"
    assert len(owner.calls) == 1
    assert owner.committed == {}


@pytest.mark.parametrize(
    "override",
    [
        {"commitState": "unknown"},
        {"commitState": "committed"},
        {"retryClass": "reconcile_first"},
        {"retryable": True},
        {"field": "execution.workspaceId"},
        {"origin": "gateway_adapter"},
        {"code": "REGISTRY_BUSY"},
        {"code": "IDEMPOTENCY_CONFLICT", "field": "clientRequestId"},
    ],
)
def test_ambiguous_or_other_denial_never_dispatches_second_physical_effect(
    override: dict[str, Any],
) -> None:
    owner = ProfileCutoverOwner(contained_only=True)
    owner.denial_override = {
        "origin": "runtime_core",
        "code": "AUTHORIZATION_DENIED",
        "field": "execution.executionProfile",
        "commitState": "not_committed",
        "retryClass": "never",
        "retryable": False,
        "message": "denied",
        **override,
    }
    with pytest.raises(OwnerCallError):
        asyncio.run(_submit(GatewayService(owner), "no-safe-mutation"))
    assert [tool for _, tool, _ in owner.calls] == ["workspace.exec"]
    assert owner.committed == {}


@pytest.mark.parametrize(
    "targets",
    [
        [
            {
                "target": "local_linux",
                "configured": True,
                "available": True,
                "executionProfiles": ["trusted_local", "contained_local"],
            }
        ],
        [
            {
                "target": "local_linux",
                "configured": True,
                "available": False,
                "executionProfiles": ["contained_local"],
            }
        ],
        [
            {
                "target": "local_linux",
                "configured": True,
                "available": True,
                "executionProfiles": "contained_local",
            }
        ],
        [
            {
                "target": "local_linux",
                "configured": True,
                "available": True,
                "executionProfiles": ["contained_local", 7],
            }
        ],
        [
            {
                "target": "local_linux",
                "configured": True,
                "available": True,
                "executionProfiles": ["contained_local", "contained_local"],
            }
        ],
        [
            {
                "target": "local_linux",
                "configured": True,
                "available": True,
                "executionProfiles": ["contained_local"],
            },
            {
                "target": "local_linux",
                "configured": True,
                "available": True,
                "executionProfiles": ["contained_local"],
            },
        ],
    ],
)
def test_bad_or_ambiguous_runtime_description_preserves_denial(targets: list[Any]) -> None:
    owner = ProfileCutoverOwner(contained_only=True)
    owner.description["targets"] = targets
    with pytest.raises(OwnerCallError) as exc:
        asyncio.run(_submit(GatewayService(owner), "unqualified-describe"))
    assert exc.value.error is not None
    assert exc.value.error["code"] == "AUTHORIZATION_DENIED"
    assert [tool for _, tool, _ in owner.calls] == ["workspace.exec", "runtime.describe"]
    assert owner.committed == {}


def test_old_request_with_different_bytes_must_not_be_reinterpreted() -> None:
    owner = ProfileCutoverOwner()
    service = GatewayService(owner)
    asyncio.run(_submit(service, "original-key"))
    owner.contained_only = True
    with pytest.raises(OwnerCallError) as exc:
        asyncio.run(
            service.execution_submit(
                capability="execution.linux",
                request_id="original-key",
                workspace_id="ws-original",
                executable="/usr/bin/printf",
                args=["CHANGED"],
            )
        )
    assert exc.value.error is not None
    assert exc.value.error["code"] == "IDEMPOTENCY_CONFLICT"
    assert [tool for _, tool, _ in owner.calls] == [
        "workspace.exec",
        "workspace.exec",
        "runtime.describe",
        "workspace.exec",
    ]
    assert len(owner.committed) == 1


@pytest.mark.parametrize(
    "variant", ["structured-conflict", "text-conflict", "duplicate", "congruent"]
)
def test_native_sdk_error_carriers_preserve_profile_switch_boundary(tmp_path, variant):
    import uvicorn
    from mcp import types
    from mcp.server import MCPServer

    from ordivon_gateway.transport.upstream import McpOwnerCaller, OwnerEndpoint

    calls = []
    negative = {
        "origin": "runtime_core",
        "code": "AUTHORIZATION_DENIED",
        "field": "execution.executionProfile",
        "commitState": "not_committed",
        "retryClass": "never",
        "retryable": False,
        "message": "fixture denial",
    }
    uncertain = dict(negative, commitState="unknown")

    def wire(e):
        return json.dumps({"error": e})

    server = MCPServer("isolated-runtime-fixture", version="fixture")

    @server.tool(name="workspace.exec")
    async def execute(
        schemaVersion: int,
        clientRequestId: str,
        execution: dict,
        waitMs: int,
        stdoutTailBytes: int,
        stderrTailBytes: int,
    ):
        calls.append(("workspace.exec", clientRequestId, execution["executionProfile"]))
        if execution["executionProfile"] == "contained_local":
            return types.CallToolResult(
                content=[],
                structuredContent={
                    "jobId": "fixture-job",
                    "status": "succeeded",
                    "executionTerminal": True,
                },
            )
        structured = {"error": negative}
        texts = [wire(negative)]
        if variant == "structured-conflict":
            texts = [wire(uncertain)]
        elif variant == "text-conflict":
            structured = None
            texts = [wire(negative), wire(uncertain)]
        elif variant == "duplicate":
            texts = [
                wire(negative).replace(
                    '"commitState": "not_committed"',
                    '"commitState": "unknown", "commitState": "not_committed"',
                )
            ]
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=t) for t in texts],
            structuredContent=structured,
            isError=True,
        )

    @server.tool(name="runtime.describe")
    async def describe(schemaVersion: int) -> dict:
        calls.append(("runtime.describe", None, None))
        return ProfileCutoverOwner().description

    token = tmp_path / "fixture-token"
    token.write_text("fixture-only-not-a-real-secret")
    token.chmod(0o600)
    app = server.streamable_http_app(streamable_http_path="/mcp", stateless_http=True)

    async def scenario():
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        uv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical"))
        serving = asyncio.create_task(uv.serve())
        try:
            for _ in range(150):
                if uv.started:
                    break
                await asyncio.sleep(0.02)
            assert uv.started
            caller = McpOwnerCaller(
                {
                    "runtime.linux": OwnerEndpoint(
                        f"http://127.0.0.1:{port}/mcp", bearer_token_file=str(token)
                    )
                }
            )
            try:
                service = GatewayService(caller)
                if variant == "congruent":
                    receipt = await _submit(service, "fixture-key")
                    assert receipt.native_id == "fixture-job"
                    assert calls == [
                        ("workspace.exec", "fixture-key", "trusted_local"),
                        ("runtime.describe", None, None),
                        ("workspace.exec", "fixture-key", "contained_local"),
                    ]
                else:
                    with pytest.raises(OwnerCallError) as exc:
                        await _submit(service, "fixture-key")
                    assert exc.value.error is None
                    assert calls == [("workspace.exec", "fixture-key", "trusted_local")]
            finally:
                await caller.aclose()
        finally:
            uv.should_exit = True
            await asyncio.wait_for(serving, timeout=12)

    asyncio.run(scenario())
