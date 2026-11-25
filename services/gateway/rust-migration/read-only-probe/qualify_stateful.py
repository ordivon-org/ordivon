"""Native recipient temporal contract: one process, one independent TCP producer.

The model only describes the synthetic producer and expected observation;
it never calls the Rust implementation to derive its oracle.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import secrets
import socket
import tempfile
from pathlib import Path

import uvicorn
from mcp.server import MCPServer
from starlette.responses import PlainTextResponse

ACTIONS = ("ready", "not_ready", "invalid", "rotate", "stale", "missing", "http503", "http404")


async def qualify_trace(binary: Path, *, legacy: bool) -> None:
    # All ordered action pairs, with each pair resetting by an explicit ready.
    # Reproducible and independent of random seeds, no timing-based oracle.
    trace = [action for pair in itertools.product(ACTIONS, repeat=2) for action in ("ready", *pair)]
    assert len(trace) == 192
    bearer = secrets.token_urlsafe(32)
    tokens = [bearer]
    case = "ready"
    calls: list[int] = []
    wire: list[str] = []
    faults: list[str] = []
    requests: list[bool] = []
    server = MCPServer("temporal-runtime-fixture")

    @server.tool(name="runtime.describe", structured_output=True)
    async def describe(schemaVersion: int = 1) -> dict[str, object]:
        calls.append(schemaVersion)
        return {
            "schemaVersion": 1,
            "node": {"nodeId": "fixture-linux", "platform": "linux", "native": True},
            "targets": [
                {
                    "target": "local_linux",
                    "configured": True,
                    "available": case != "not_ready",
                    "executionProfiles": None if case == "invalid" else ["trusted_local"],
                }
            ],
        }

    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=not legacy,
        json_response=True,
        host="127.0.0.1",
    )

    async def controlled(scope, receive, send):
        if scope["type"] != "http":
            await app(scope, receive, send)
            return
        ok = secrets.compare_digest(
            dict(scope["headers"]).get(b"authorization", b""),
            ("Bearer " + bearer).encode("ascii"),
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
            message = await receive()
            assert message["type"] == "http.request"
            chunks.append(message.get("body", b""))
            if not message.get("more_body"):
                break
        body = b"".join(chunks)
        method = json.loads(body).get("method", "")
        wire.append(method)
        delivered = False

        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        # Complete the SDK's actual business invocation, then replace its
        # response. The consumer has lost evidence, not the Owner's effect.
        if method == "tools/call" and case in ("http503", "http404"):

            async def discard(_message):
                pass

            await app(scope, replay, discard)
            faults.append(case)
            await PlainTextResponse("response fault", status_code=int(case[4:]))(
                scope, replay, send
            )
        else:
            await app(scope, replay, send)

    with tempfile.TemporaryDirectory(prefix="gateway-temporal-") as tmp, socket.socket() as sock:
        credential = Path(tmp) / "bearer"
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        endpoint = f"http://127.0.0.1:{sock.getsockname()[1]}/mcp"
        uv = uvicorn.Server(uvicorn.Config(controlled, log_level="critical"))
        serving = asyncio.create_task(uv.serve(sockets=[sock]))
        proc = None
        try:
            for _ in range(250):
                if uv.started:
                    break
                await asyncio.sleep(0.02)
            assert uv.started
            proc = await asyncio.create_subprocess_exec(
                str(binary),
                "observe-protected-runtime-sequence-fixture",
                endpoint,
                "fixture-linux",
                str(credential),
                "legacy" if legacy else "auto",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            assert proc.stdin is not None and proc.stdout is not None
            # Drain stderr concurrently so a noisy SDK cannot stall the protocol.
            assert proc.stderr is not None
            stderr_task = asyncio.create_task(proc.stderr.read())
            for step, case in enumerate(trace):
                if case == "rotate":
                    bearer = secrets.token_urlsafe(32)
                    tokens.append(bearer)
                if case == "missing":
                    credential.unlink(missing_ok=True)
                else:
                    # Atomic replacement deliberately changes the inode on every step.
                    temp = credential.with_suffix(".next")
                    stale = tokens[-2] if len(tokens) > 1 else "invalid-fixture-token"
                    temp.write_text(stale if case == "stale" else bearer, encoding="ascii")
                    temp.chmod(0o600)
                    temp.replace(credential)
                c, w, f, a = len(calls), len(wire), len(faults), len(requests)
                proc.stdin.write(b"observe\n")
                await proc.stdin.drain()
                output = await asyncio.wait_for(proc.stdout.readline(), 8)
                result = json.loads(output)
                assert all(token.encode() not in output for token in tokens)
                label = (legacy, step, case, result)
                if case == "missing":
                    assert result == {
                        "standing": "unobserved",
                        "reason": "unqualified_fixture_credential",
                    }, label
                    assert len(requests) == a and len(wire) == w and len(calls) == c, label
                elif case == "stale":
                    assert result["standing"] == "unobserved", label
                    assert requests[a:] and not any(requests[a:]), label
                    assert len(wire) == w and len(calls) == c, label
                else:
                    assert calls[c:] == [1], label
                    assert wire[w:].count("tools/call") == 1, label
                    assert requests[a:] and all(requests[a:]), label
                    if case in ("http503", "http404"):
                        assert result["standing"] == "unobserved", label
                        assert faults[f:] == [case], label
                    elif case == "invalid":
                        assert result == {
                            "standing": "unobserved",
                            "reason": "invalid_execution_context_inventory",
                        }, label
                    else:
                        assert result == {
                            "standing": "reported",
                            "configured": True,
                            "available": case != "not_ready",
                        }, label
                # No response replay or renegotiation after business dispatch.
                if "tools/call" in wire[w:]:
                    after = wire[w:][wire[w:].index("tools/call") + 1 :]
                    assert not {"initialize", "server/discover", "tools/call"}.intersection(
                        after
                    ), label
            proc.stdin.close()
            await asyncio.wait_for(proc.wait(), 8)
            stderr = await stderr_task
            assert proc.returncode == 0
            assert all(token.encode() not in stderr for token in tokens)
            print(
                "NATIVE_TEMPORAL_TRACE_PASS",
                "legacy" if legacy else "auto",
                "transitions",
                len(trace),
                "business_calls",
                len(calls),
                "response_faults",
                len(faults),
                flush=True,
            )
        finally:
            if proc is not None and proc.returncode is None:
                proc.kill()
                await proc.wait()
            uv.should_exit = True
            await asyncio.wait_for(serving, 10)


async def qualify_stateful(binary: Path) -> None:
    await qualify_trace(binary, legacy=False)
    await qualify_trace(binary, legacy=True)
