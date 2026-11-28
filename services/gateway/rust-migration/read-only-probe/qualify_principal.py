"""Independent namespace and protected reattachment consumer qualification."""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import secrets
import socket
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import uvicorn
from mcp.server import MCPServer
from starlette.responses import PlainTextResponse

from ordivon_gateway.security.execution_access import verified_execution_request_id


def oracle(coords):
    issuer, principal, capability, request = coords
    return (
        "request:gw-principal:"
        + hashlib.sha256(
            json.dumps(
                [
                    "ordivon.gateway-principal-scoped-execution-request.v1",
                    issuer,
                    principal,
                    capability,
                    request,
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
    )


def qualify_namespace(binary: Path):
    # Exhaustive single ASCII codepoints plus representative Unicode and
    # independently generated mixed tuples. Synthetic values, never credentials.
    rng = random.Random(17017)
    alphabet = [
        "a",
        ":",
        '"',
        "\\",
        "\x00",
        "\x1f",
        "\u2028",
        "\u2029",
        "é",
        "e\u0301",
        "中",
        "😀",
        "\U0010ffff",
    ]
    cases = [("issuer", "principal", "execution.linux", chr(i)) for i in range(128)]
    cases += [
        ("a:b", "c", "execution.linux", "x"),
        ("a", "b:c", "execution.linux", "x"),
        ("é", "principal", "execution.linux", "x"),
        ("e\u0301", "principal", "execution.linux", "x"),
        ("issuer", "principal", "execution.linux", ""),
    ]
    for _ in range(1024):
        cases.append(
            tuple("".join(rng.choices(alphabet, k=rng.randrange(1, 25))) for _ in range(4))
        )
    inputs = "".join(
        json.dumps({"operation": "principal_namespace", "input": c}) + "\n" for c in cases
    )
    result = subprocess.run(
        [binary, "eval"], input=inputs, capture_output=True, text=True, check=True, timeout=20
    )
    outputs = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(outputs) == len(cases)
    for coords, got in zip(cases, outputs, strict=True):
        expected = oracle(coords)
        assert got == expected, (coords, got, expected)
        # Also exercise actual existing Python ingress-context consumer where
        # identity is valid (not a production authentication assertion).
        if coords[0].strip() and coords[1].strip():
            ctx = SimpleNamespace(
                request_context=SimpleNamespace(
                    request=SimpleNamespace(
                        scope={
                            "state": {
                                "ordivon_access_issuer": coords[0],
                                "ordivon_access_principal": coords[1],
                            }
                        }
                    )
                )
            )
            assert got == verified_execution_request_id(coords[3], coords[2], ctx)
    assert outputs[128] != outputs[129]
    assert outputs[130] != outputs[131]
    print("NATIVE_PRINCIPAL_NAMESPACE_PARITY", len(cases), flush=True)


async def qualify_binding(binary: Path, legacy: bool):
    server = MCPServer("native-principal-fixture")
    bearer = secrets.token_urlsafe(32)
    calls = []
    requests = []
    base = {
        "issuer": "issuer-A",
        "principal": "principal-A",
        "capability": "execution.linux",
        "request_id": "同一:request",
        "operation_ref": "ordivon-exec:v1:runtime.linux:job-a",
    }
    key = oracle(tuple(base[k] for k in ("issuer", "principal", "capability", "request_id")))
    row = {"jobId": "job-a", "clientRequestId": key, "workspaceId": "ws-a", "createdAtMs": 2}
    case = "found"

    @server.tool(name="job.list", structured_output=True)
    async def list_jobs(limit: int, clientRequestId: str) -> dict[str, object]:
        calls.append((limit, clientRequestId))
        if case == "owner_error":
            raise ValueError("synthetic failure")
        if case == "foreign":
            return {"jobs": [{**row, "clientRequestId": "foreign"}]}
        if clientRequestId != key or case == "absent":
            return {"jobs": [], "nextCursor": None}
        if case == "ambiguous":
            return {"jobs": [row, {**row, "jobId": "job-b", "createdAtMs": 1}]}
        return {"jobs": [row], "nextCursor": None}

    app = server.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=not legacy, json_response=True, host="127.0.0.1"
    )

    async def guarded(scope, receive, send):
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
        await app(scope, receive, send)

    cases = [
        ("found", {}, True, True),
        ("issuer", {"issuer": "issuer-B"}, False, True),
        ("principal", {"principal": "principal-B"}, False, True),
        ("request", {"request_id": "another"}, False, True),
        ("wrong_ref", {"operation_ref": "ordivon-exec:v1:runtime.linux:job-b"}, False, True),
        ("wrong_owner", {"operation_ref": "ordivon-exec:v1:runtime.windows:job-a"}, False, False),
        ("capability", {"capability": "execution.windows"}, False, False),
        ("blank_issuer", {"issuer": "\x1c"}, False, False),
        ("blank_principal", {"principal": "\u3000"}, False, False),
        ("empty_request", {"request_id": ""}, False, False),
        ("malformed_ref", {"operation_ref": "job-a"}, False, False),
        ("absent", {}, False, True),
        ("ambiguous", {}, False, True),
        ("foreign", {}, False, True),
        ("owner_error", {}, False, True),
        ("wrong_token", {}, False, False),
        ("missing", {}, False, False),
        ("found_again", {}, True, True),
    ]
    with tempfile.TemporaryDirectory(prefix="gateway-principal-") as tmp, socket.socket() as sock:
        credential = Path(tmp) / "bearer"
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        endpoint = f"http://127.0.0.1:{sock.getsockname()[1]}/mcp"
        uv = uvicorn.Server(uvicorn.Config(guarded, log_level="critical"))
        serving = asyncio.create_task(uv.serve(sockets=[sock]))
        try:
            for _ in range(250):
                if uv.started:
                    break
                await asyncio.sleep(0.02)
            assert uv.started
            for case, changes, matched, invoke in cases:
                if case == "missing":
                    credential.unlink()
                else:
                    credential.write_text(
                        "bad-token" if case == "wrong_token" else bearer, encoding="ascii"
                    )
                    credential.chmod(0o600)
                fixture = {**base, **changes}
                c, a = len(calls), len(requests)
                proc = await asyncio.create_subprocess_exec(
                    str(binary),
                    "qualify-principal-runtime-fixture",
                    endpoint,
                    str(credential),
                    "legacy" if legacy else "auto",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    out, err = await asyncio.wait_for(
                        proc.communicate(json.dumps(fixture).encode()), 8
                    )
                finally:
                    if proc.returncode is None:
                        proc.kill()
                        await proc.wait()
                assert proc.returncode == 0, err.decode()
                assert bearer.encode() not in out and bearer.encode() not in err
                assert json.loads(out) == {"standing": "matched" if matched else "unqualified"}, (
                    case,
                    out,
                )
                if invoke:
                    expected_key = oracle(
                        tuple(
                            fixture[k] for k in ("issuer", "principal", "capability", "request_id")
                        )
                    )
                    assert calls[c:] == [(2, expected_key)], (case, calls[c:])
                    assert requests[a:] and all(requests[a:])
                else:
                    assert len(calls) == c
                    if case == "wrong_token":
                        assert requests[a:] and not any(requests[a:])
                    else:
                        assert len(requests) == a
            print(
                "NATIVE_PRINCIPAL_BINDING_PASS",
                "legacy" if legacy else "auto",
                len(cases),
                "business_calls",
                len(calls),
                flush=True,
            )
        finally:
            uv.should_exit = True
            await asyncio.wait_for(serving, 10)


async def qualify_principal(binary: Path):
    qualify_namespace(binary)
    await qualify_binding(binary, False)
    await qualify_binding(binary, True)
