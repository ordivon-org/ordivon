"""Actual Gateway business-consumer contracts through upstream typed MCP SDK."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp import types

from ordivon_gateway import upstream
from ordivon_gateway.service import GatewayService
from ordivon_gateway.upstream import McpOwnerCaller, OwnerCallError, OwnerEndpoint

REPORT = json.dumps({"kind": "real-job-deliverable", "accepted": True}, sort_keys=True)
JOB_ID = "job-actual-fixture"
ATTEMPT_ID = "attempt-actual-fixture"
ARTIFACT_ID = ATTEMPT_ID + ".stdout"
SHA = "sha256:" + hashlib.sha256(REPORT.encode()).hexdigest()


def _fixtures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, owner_error=False):
    events: list[tuple[str, str]] = []

    class Pool:
        async def aclose(self) -> None:
            pass

    class Client:
        def __init__(self, transport, *, mode, raise_exceptions):
            assert not raise_exceptions
            self.session = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def call_tool(self, name, arguments, *, meta=None):
            events.append(("high-level", name))
            return SimpleNamespace(
                is_error=False, structured_content={"owner": "other"}, content=[]
            )

        async def send_request(self, request, result_type):
            assert isinstance(request, types.CallToolRequest)
            assert result_type is types.CallToolResult
            name = request.params.name
            events.append(("typed-sdk", name))
            if owner_error:
                return SimpleNamespace(
                    is_error=True,
                    structured_content={"error": {"code": "OWNER_FAILED"}},
                    content=[],
                )
            data = {
                "workspace.exec": {
                    "jobId": JOB_ID,
                    "status": "accepted",
                    "executionTerminal": False,
                    "deliveryDisposition": "committed",
                    "scheduling": {"state": "allocated"},
                },
                "job.list": {
                    "jobs": [
                        {
                            "jobId": JOB_ID,
                            "workspaceId": "ws-existing",
                            "clientRequestId": "unique-request",
                            "scheduling": {"state": "released"},
                        }
                    ],
                    "nextCursor": None,
                },
                "job.observe": {
                    "jobId": JOB_ID,
                    "status": "succeeded",
                    "attemptState": "succeeded",
                    "executionTerminal": True,
                    "executionDisposition": "succeeded",
                    "deliveryDisposition": "committed",
                    "exitCode": 0,
                    "artifactsAvailable": True,
                    "artifacts": [{"artifactId": ARTIFACT_ID}],
                    "scheduling": {"state": "released"},
                },
                "job.get": {
                    "job": {"jobId": JOB_ID, "scheduling": {"state": "released"}},
                    "artifacts": {"count": 1},
                    "scheduling": {"state": "released"},
                },
                "artifact.read": {
                    "jobId": JOB_ID,
                    "artifactId": ARTIFACT_ID,
                    "content": REPORT,
                    "offset": 0,
                    "nextOffset": len(REPORT.encode()),
                    "eof": True,
                    "digest": SHA,
                    "scheduling": {"state": "released"},
                },
                "job.cancel": {
                    "jobId": JOB_ID,
                    "status": "cancelled",
                    "executionTerminal": True,
                    "scheduling": {"state": "released"},
                },
            }[name]
            return SimpleNamespace(is_error=False, structured_content=data, content=[])

    monkeypatch.setattr(upstream, "create_mcp_http_client", lambda **kwargs: Pool())
    monkeypatch.setattr(upstream, "streamable_http_client", lambda url, http_client: object())
    monkeypatch.setattr(upstream, "Client", Client)
    token = tmp_path / "fixture-token"
    token.write_text("not-a-real-credential", encoding="utf-8")
    os.chmod(token, 0o600)
    caller = McpOwnerCaller(
        {
            "runtime.linux": OwnerEndpoint("http://linux.test/mcp", bearer_token_file=str(token)),
            "runtime.windows": OwnerEndpoint(
                "http://windows.test/mcp", bearer_token_file=str(token)
            ),
            "host": OwnerEndpoint("http://host.test/mcp", bearer_token_file=str(token)),
        }
    )
    return caller, events


def test_runtime_business_submit_resolve_observe_artifact_delivers_real_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caller, events = _fixtures(tmp_path, monkeypatch)

    async def run() -> None:
        gw = GatewayService(caller)
        submitted = await gw.execution_submit(
            capability="execution.linux",
            request_id="unique-request",
            workspace_id="ws-existing",
            executable="/usr/bin/python3",
            args=["-V"],
        )
        assert submitted.native_id == JOB_ID
        resolved = await gw.execution_resolve(
            capability="execution.linux",
            request_id="unique-request",
        )
        assert resolved.resolution == "found"
        assert resolved.operation_ref == submitted.operation_ref
        observed = await gw.execution_get(resolved.operation_ref)
        assert observed.terminal and observed.exit_code == 0
        assert observed.artifact_projection_complete is True
        assert observed.artifact_ids == [ARTIFACT_ID]
        chunk = await gw.artifact_read(resolved.operation_ref, ARTIFACT_ID)
        assert chunk.content == REPORT and chunk.digest == SHA and chunk.eof
        assert "sha256:" + hashlib.sha256(chunk.content.encode()).hexdigest() == chunk.digest
        assert json.loads(chunk.content)["accepted"] is True
        await caller.aclose()

    asyncio.run(run())
    assert events == [
        ("typed-sdk", "workspace.exec"),
        ("typed-sdk", "job.list"),
        ("typed-sdk", "job.observe"),
        ("typed-sdk", "job.get"),
        ("typed-sdk", "artifact.read"),
    ]


def test_other_owners_still_use_full_official_sdk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caller, events = _fixtures(tmp_path, monkeypatch)

    async def run() -> None:
        assert (await caller.call_tool("host", "host.status", {}))["owner"] == "other"
        assert (await caller.call_tool("runtime.windows", "job.get", {}))["owner"] == "other"
        assert (await caller.call_tool("runtime.linux", "job.cancel", {"jobId": JOB_ID}))[
            "jobId"
        ] == JOB_ID
        await caller.aclose()

    asyncio.run(run())
    assert events == [
        ("high-level", "host.status"),
        ("high-level", "job.get"),
        ("typed-sdk", "job.cancel"),
    ]


def test_owner_error_remains_error_and_is_not_retried(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caller, events = _fixtures(tmp_path, monkeypatch, owner_error=True)

    async def run() -> None:
        with pytest.raises(OwnerCallError, match="owner tool returned error"):
            await caller.call_tool("runtime.linux", "workspace.exec", {"clientRequestId": "x"})
        await caller.aclose()

    asyncio.run(run())
    assert events == [("typed-sdk", "workspace.exec")]
