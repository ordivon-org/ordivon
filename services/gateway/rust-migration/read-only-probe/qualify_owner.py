"""Independent native Python MCP producer -> Rust read-only recipient fixture."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import socket
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import uvicorn
from mcp.server import MCPServer
from starlette.responses import PlainTextResponse, RedirectResponse

from ordivon_gateway.logic.routing import default_routes


async def observe_fixture(
    binary: Path,
    case: str,
    *,
    legacy: bool = False,
    query: str | None = None,
    include: bool = False,
    credential_case: str | None = None,
) -> dict:
    server = MCPServer("runtime-readonly-fixture")
    calls: list[int] = []
    wire: list[dict] = []
    requests: list[str] = []
    authenticated: list[bool] = []
    bearer = secrets.token_urlsafe(32)

    @server.tool(name="runtime.describe", structured_output=case != "text")
    async def runtime_describe(schemaVersion: int = 1) -> dict[str, Any]:
        calls.append(schemaVersion)
        if case == "error":
            raise ValueError("synthetic Owner error")
        if case == "slow":
            await asyncio.sleep(4)
        value = {
            "schemaVersion": 1,
            "node": {"nodeId": "fixture-linux", "platform": "linux", "native": True},
            "targets": [
                {"target": "local_linux", "configured": True, "available": case != "false"}
            ],
        }
        if case == "version":
            value["schemaVersion"] = True
        elif case == "node":
            value["node"]["nodeId"] = "other"
        elif case == "duplicate":
            value["targets"].append(value["targets"][0])
        elif case == "contradiction":
            value["targets"][0]["configured"] = False
        elif case == "typed":
            value["targets"][0]["available"] = "true"
        elif case == "absent":
            value["targets"] = []
        elif case == "oversize":
            value["padding"] = "x" * (1024 * 1024 + 1)
        return value

    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=not legacy,
        json_response=True,
        host="127.0.0.1",
    )

    async def capture(scope, receive, send):
        if scope["type"] == "http" and credential_case is not None:
            requests.append(scope["path"])
            # Do not store the received header or token, only the comparison.
            ok = secrets.compare_digest(
                dict(scope["headers"]).get(b"authorization", b""),
                ("Bearer " + bearer).encode("ascii"),
            )
            authenticated.append(ok)
            if not ok:
                await PlainTextResponse("denied", status_code=401)(scope, receive, send)
                return
            if credential_case == "redirect":
                await RedirectResponse("/sink", status_code=307)(scope, receive, send)
                return
        if scope["type"] == "http" and scope.get("method") == "POST":
            chunks = []

            async def observed_receive():
                part = await receive()
                if part["type"] == "http.request":
                    chunks.append(part.get("body", b""))
                    if not part.get("more_body"):
                        wire.append(json.loads(b"".join(chunks)))
                return part

            await app(scope, observed_receive, send)
        else:
            await app(scope, receive, send)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        endpoint = f"http://127.0.0.1:{sock.getsockname()[1]}/mcp"
        uv = uvicorn.Server(uvicorn.Config(capture, log_level="critical"))
        serving = asyncio.create_task(uv.serve(sockets=[sock]))
        try:
            for _ in range(250):
                if uv.started:
                    break
                await asyncio.sleep(0.02)
            assert uv.started
            with tempfile.TemporaryDirectory(prefix="native-discovery-") as tmp:
                if credential_case is not None:
                    credential = Path(tmp) / "bearer"
                    if credential_case != "missing":
                        if credential_case == "fifo":
                            os.mkfifo(credential, 0o600)
                        elif credential_case == "symlink":
                            target = Path(tmp) / "target"
                            target.write_text(bearer, encoding="ascii")
                            target.chmod(0o600)
                            credential.symlink_to(target)
                        else:
                            data = {
                                "wrong": "wrong-token",
                                "oversize_file": "a" * 16385,
                                "malformed": "two tokens",
                                "nonascii": "é",
                                "empty": "",
                            }.get(credential_case, bearer + "\n")
                            credential.write_text(data, encoding="utf-8")
                            credential.chmod(0o644 if credential_case == "public" else 0o600)
                    args = [
                        "observe-protected-runtime-fixture",
                        endpoint,
                        "fixture-linux",
                        str(credential),
                        "legacy" if legacy else "auto",
                    ]
                elif query is None:
                    args = [
                        "observe-runtime-fixture",
                        endpoint,
                        "fixture-linux",
                        "legacy" if legacy else "auto",
                    ]
                if query is not None:
                    route = asdict(default_routes()["execution.linux"])
                    metadata = {
                        key: route[key]
                        for key in ("capability", "category", "owner_id", "description", "tags")
                    }
                    path = Path(tmp) / "search.json"
                    path.write_text(
                        json.dumps(
                            {
                                "metadata": metadata,
                                "query": query,
                                "limit": 10,
                                "include_unavailable": include,
                            }
                        ),
                        encoding="utf-8",
                    )
                    args = ["discover-runtime-fixture", str(path), endpoint, "fixture-linux"]
                    if credential_case is not None:
                        args[0] = "discover-protected-runtime-fixture"
                        args.append(str(credential))
                proc = await asyncio.create_subprocess_exec(
                    str(binary),
                    *args,
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
                result = json.loads(out)
            if query == "zz-no-such-route-xyz":
                assert not requests and not wire and not calls
                return result
            if credential_case in {
                "missing",
                "public",
                "symlink",
                "fifo",
                "oversize_file",
                "malformed",
                "nonascii",
                "empty",
            }:
                assert not requests and not wire and not calls
                return result
            if credential_case == "wrong":
                assert requests and not any(authenticated) and not wire and not calls
                return result
            if credential_case == "redirect":
                assert requests and all(authenticated)
                assert set(requests) == {"/mcp"} and not wire and not calls
                return result
            if credential_case is not None:
                assert requests and all(authenticated) and set(requests) == {"/mcp"}
            tool_calls = [item for item in wire if item.get("method") == "tools/call"]
            assert len(tool_calls) == 1, (case, wire)
            assert tool_calls[0]["params"]["name"] == "runtime.describe"
            assert tool_calls[0]["params"]["arguments"] == {"schemaVersion": 1}
            assert calls == [1], (case, calls)
            if legacy:
                assert any(item.get("method") == "initialize" for item in wire), wire
            return result
        finally:
            uv.should_exit = True
            await asyncio.wait_for(serving, 10)


async def qualify_owner(binary: Path) -> None:
    expected = {
        "true": {"standing": "reported", "configured": True, "available": True},
        "false": {"standing": "reported", "configured": True, "available": False},
        "version": {"standing": "unobserved", "reason": "invalid_status_envelope"},
        "node": {"standing": "unobserved", "reason": "unqualified_node"},
        "duplicate": {"standing": "unobserved", "reason": "invalid_target_inventory"},
        "contradiction": {"standing": "unobserved", "reason": "invalid_target_inventory"},
        "typed": {"standing": "unobserved", "reason": "invalid_target_inventory"},
        "absent": {"standing": "unobserved", "reason": "target_not_observed"},
        "error": {"standing": "unobserved", "reason": "owner_tool_error"},
        "text": {"standing": "unobserved", "reason": "structured_result_absent"},
    }
    for case, result in expected.items():
        observed = await observe_fixture(binary, case)
        assert observed == result, (case, observed, result)
        print("NATIVE_OWNER_FIXTURE_PASS", case, observed, flush=True)
    for case in ("slow", "oversize"):
        observed = await observe_fixture(binary, case)
        assert observed["standing"] == "unobserved", (case, observed)
        assert observed["reason"] in ("observation_deadline", "protocol_or_transport_failed")
        print("NATIVE_OWNER_FIXTURE_PASS", case, observed, flush=True)
    observed = await observe_fixture(binary, "true", legacy=True)
    assert observed == expected["true"]
    print("NATIVE_OWNER_LEGACY_PASS", observed, flush=True)

    empty = {"total_matches": 0, "matches": []}
    match = {
        "total_matches": 1,
        "matches": [{"capability": "execution.linux", "match_kind": "exact"}],
    }
    for case, include, expected_projection, expected_observation in (
        ("true", False, match, expected["true"]),
        ("false", False, empty, expected["false"]),
        ("false", True, match, expected["false"]),
        ("duplicate", False, match, expected["duplicate"]),
    ):
        result = await observe_fixture(binary, case, query="execution.linux", include=include)
        assert result == {"projection": expected_projection, "observation": expected_observation}, (
            case,
            result,
        )
        print("NATIVE_DISCOVERY_COMPOSITION_PASS", case, include, result, flush=True)
    result = await observe_fixture(binary, "true", query="zz-no-such-route-xyz")
    assert result == {"projection": empty, "observation": None}, result
    print("NATIVE_DISCOVERY_ZERO_RPC_PASS", result, flush=True)

    for credential_case in (
        "valid",
        "wrong",
        "missing",
        "public",
        "symlink",
        "fifo",
        "oversize_file",
        "malformed",
        "nonascii",
        "empty",
        "redirect",
    ):
        observed = await observe_fixture(binary, "true", credential_case=credential_case)
        if credential_case == "valid":
            assert observed == expected["true"], observed
        elif credential_case in {"wrong", "redirect"}:
            assert observed["standing"] == "unobserved", observed
        else:
            assert observed == {
                "standing": "unobserved",
                "reason": "unqualified_fixture_credential",
            }, observed
        print("NATIVE_PROTECTED_OWNER_PASS", credential_case, observed, flush=True)
    observed = await observe_fixture(binary, "true", legacy=True, credential_case="valid")
    assert observed == expected["true"], observed
    print("NATIVE_PROTECTED_OWNER_LEGACY_PASS", observed, flush=True)

    for case, credential_case, query, expected_projection, expected_observation in (
        ("true", "valid", "execution.linux", match, expected["true"]),
        ("false", "valid", "execution.linux", empty, expected["false"]),
        (
            "true",
            "wrong",
            "execution.linux",
            match,
            {"standing": "unobserved", "reason": "negotiation_failed"},
        ),
        (
            "true",
            "missing",
            "execution.linux",
            match,
            {"standing": "unobserved", "reason": "unqualified_fixture_credential"},
        ),
        ("true", "fifo", "zz-no-such-route-xyz", empty, None),
    ):
        observed = await observe_fixture(
            binary,
            case,
            query=query,
            credential_case=credential_case,
        )
        assert observed == {
            "projection": expected_projection,
            "observation": expected_observation,
        }, observed
        print("NATIVE_PROTECTED_DISCOVERY_PASS", case, credential_case, query, observed, flush=True)
