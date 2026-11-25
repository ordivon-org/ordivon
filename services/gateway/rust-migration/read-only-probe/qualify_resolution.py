"""Independent protected SDK producer for the native reattachment recipient.

The test owns only synthetic jobs; no submission, execution or production credentials.
"""

from __future__ import annotations

import asyncio
import json
import secrets
import socket
import tempfile
from pathlib import Path

import uvicorn
from mcp.server import MCPServer
from starlette.responses import PlainTextResponse

REQUEST = "original-operation"
ROW = {"clientRequestId": REQUEST, "jobId": "job-a", "workspaceId": "ws-original", "createdAtMs": 2}
OTHER = {**ROW, "jobId": "job-b", "createdAtMs": 1}
FOUND = {
    "resolution": "found",
    "operation_ref": "ordivon-exec:v1:runtime.linux:job-a",
    "native_id": "job-a",
    "workspace_id": "ws-original",
}


def unknown(reason: str) -> dict:
    return {"resolution": "unobserved", "reason": reason}


async def qualify_mode(binary: Path, legacy: bool) -> None:
    server = MCPServer("native-reattachment-fixture")
    bearer = secrets.token_urlsafe(32)
    calls: list[tuple] = []
    wire: list[dict] = []
    requests: list[bool] = []
    faults: list[str] = []
    page: dict = {}
    case = "found"

    @server.tool(name="job.list", structured_output=True)
    async def list_jobs(limit: int, clientRequestId: str) -> dict[str, object]:
        calls.append((limit, clientRequestId))
        if case == "error":
            raise ValueError("synthetic read failure")
        return page

    app = server.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=not legacy, json_response=True, host="127.0.0.1"
    )

    async def controlled(scope, receive, send):
        if scope["type"] != "http":
            await app(scope, receive, send)
            return
        ok = secrets.compare_digest(
            dict(scope["headers"]).get(b"authorization", b""), ("Bearer " + bearer).encode()
        )
        requests.append(ok)
        if not ok:
            await PlainTextResponse("denied", status_code=401)(scope, receive, send)
            return
        if scope["method"] != "POST":
            await app(scope, receive, send)
            return
        chunks = []
        while True:
            part = await receive()
            assert part["type"] == "http.request"
            chunks.append(part.get("body", b""))
            if not part.get("more_body"):
                break
        body = b"".join(chunks)
        request = json.loads(body)
        wire.append(request)
        delivered = False

        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        if request.get("method") == "tools/call" and case in ("http404", "http503"):

            async def discard(_message):
                pass

            await app(scope, replay, discard)
            faults.append(case)
            await PlainTextResponse("lost reply", status_code=int(case[4:]))(scope, replay, send)
        else:
            await app(scope, replay, send)

    cases = [
        ("found", {"jobs": [ROW], "nextCursor": None}, FOUND),
        ("absent", {"jobs": [], "nextCursor": None}, {"resolution": "absent"}),
        ("legacy_absent_cursor", {"jobs": [ROW]}, FOUND),
        ("multiple", {"jobs": [ROW, OTHER]}, {"resolution": "ambiguous"}),
        (
            "continuation",
            {"jobs": [ROW, OTHER], "nextCursor": {"jobId": "job-b", "createdAtMs": 1}},
            {"resolution": "ambiguous"},
        ),
        (
            "foreign",
            {"jobs": [{**ROW, "clientRequestId": "foreign"}]},
            unknown("mismatched_request_identity"),
        ),
        ("duplicate", {"jobs": [ROW, ROW]}, unknown("invalid_job_identity")),
        ("workspace", {"jobs": [{**ROW, "workspaceId": None}]}, unknown("invalid_job_identity")),
        ("colon", {"jobs": [{**ROW, "jobId": "job:a"}]}, unknown("invalid_job_identity")),
        ("malformed", {"jobs": {}}, unknown("invalid_job_page")),
        (
            "too_many",
            {"jobs": [ROW, OTHER, {**OTHER, "jobId": "job-c"}]},
            unknown("invalid_job_page"),
        ),
        ("empty_continuation", {"jobs": [], "nextCursor": {}}, unknown("invalid_job_cursor")),
        (
            "cursor_mismatch",
            {"jobs": [ROW, OTHER], "nextCursor": {"jobId": "job-a", "createdAtMs": 2}},
            unknown("invalid_job_cursor"),
        ),
        (
            "cursor_float",
            {"jobs": [ROW, OTHER], "nextCursor": {"jobId": "job-b", "createdAtMs": 1.0}},
            unknown("invalid_job_cursor"),
        ),
        ("error", {"jobs": [ROW]}, unknown("owner_tool_error")),
        ("http404", {"jobs": [ROW]}, None),
        ("http503", {"jobs": [ROW]}, None),
        ("wrong", {"jobs": [ROW]}, None),
        ("missing", {"jobs": [ROW]}, unknown("unqualified_fixture_credential")),
        ("found_again", {"jobs": [ROW]}, FOUND),
    ]
    with tempfile.TemporaryDirectory(prefix="gateway-reattach-") as tmp, socket.socket() as sock:
        credential = Path(tmp) / "bearer"
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        endpoint = f"http://127.0.0.1:{sock.getsockname()[1]}/mcp"
        uv = uvicorn.Server(uvicorn.Config(controlled, log_level="critical"))
        serving = asyncio.create_task(uv.serve(sockets=[sock]))
        try:
            for _ in range(250):
                if uv.started:
                    break
                await asyncio.sleep(0.02)
            assert uv.started
            for case, page, expected in cases:
                if case == "missing":
                    credential.unlink()
                else:
                    credential.write_text(
                        "wrong-token" if case == "wrong" else bearer, encoding="ascii"
                    )
                    credential.chmod(0o600)
                c, w, a, f = len(calls), len(wire), len(requests), len(faults)
                proc = await asyncio.create_subprocess_exec(
                    str(binary),
                    "resolve-protected-runtime-fixture",
                    endpoint,
                    str(credential),
                    REQUEST,
                    "legacy" if legacy else "auto",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    out, err = await asyncio.wait_for(proc.communicate(), 8)
                finally:
                    if proc.returncode is None:
                        proc.kill()
                        await proc.wait()
                assert proc.returncode == 0, err.decode()
                assert bearer.encode() not in out and bearer.encode() not in err
                actual = json.loads(out)
                label = (legacy, case, actual)
                if expected is None:
                    assert actual["resolution"] == "unobserved", label
                else:
                    assert actual == expected, label
                if case == "missing":
                    assert len(requests) == a and len(wire) == w and len(calls) == c, label
                elif case == "wrong":
                    assert requests[a:] and not any(requests[a:]), label
                    assert len(wire) == w and len(calls) == c, label
                else:
                    assert requests[a:] and all(requests[a:]), label
                    assert calls[c:] == [(2, REQUEST)], label
                    tool_calls = [item for item in wire[w:] if item.get("method") == "tools/call"]
                    assert len(tool_calls) == 1, label
                    assert tool_calls[0]["params"]["name"] == "job.list", label
                    assert tool_calls[0]["params"]["arguments"] == {
                        "limit": 2,
                        "clientRequestId": REQUEST,
                    }, label
                    after = wire[w + wire[w:].index(tool_calls[0]) + 1 :]
                    assert not any(
                        item.get("method") in ("tools/call", "initialize", "server/discover")
                        for item in after
                    ), label
                    if case in ("http404", "http503"):
                        assert faults[f:] == [case], label
            print(
                "NATIVE_RESOLUTION_PASS",
                "legacy" if legacy else "auto",
                "cases",
                len(cases),
                "business_calls",
                len(calls),
                "response_faults",
                len(faults),
                flush=True,
            )
        finally:
            uv.should_exit = True
            await asyncio.wait_for(serving, 10)


async def qualify_resolution(binary: Path) -> None:
    await qualify_mode(binary, False)
    await qualify_mode(binary, True)
