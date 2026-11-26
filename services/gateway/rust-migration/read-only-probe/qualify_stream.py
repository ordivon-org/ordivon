"""Independent concatenation oracle and real protected SDK stream composition."""

from __future__ import annotations

import ast
import asyncio
import copy
import hashlib
import json
import random
import secrets
import socket
import tempfile
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import uvicorn
from mcp.server import MCPServer
from mcp_types import CallToolResult, TextContent
from qualify_chunk import REF, digest, fixture
from qualify_chunk import oracle as chunk_oracle
from qualify_semantics import independent_descriptor
from starlette.responses import PlainTextResponse

ROOT = Path(__file__).resolve().parents[4]


def stream_fixture(parts):
    text = "".join(parts)
    d, _, _ = fixture(text)
    windows = []
    offset = 0
    for part in parts:
        _, r, v = fixture(text, offset, offset + len(part))
        windows.append({"request": r, "response": v})
        offset += len(part)
    return dict(
        operationRef=REF,
        descriptor=d,
        maxTotalBytes=d["retainedBytes"],
        maxWindows=4096,
        windows=windows,
    )


def oracle(v):
    def rejected(reason):
        return {"standing": "rejected", "reason": reason}

    from ordivon_gateway.logic.execution_refs import GatewayError, parse_execution_ref

    n, w = v.get("maxTotalBytes"), v.get("maxWindows")
    if type(n) is not int or n < 0 or type(w) is not int or w < 0:
        return rejected("stream_budget")
    try:
        parse_execution_ref(v["operationRef"])
    except GatewayError:
        return rejected("invalid_operation_ref")
    d = v["descriptor"]
    if not independent_descriptor({"artifacts": [d]}, 1)["metadata_complete"]:
        return rejected("unqualified_descriptor")
    if not 0 <= n <= 64 * 1024**2 or not 1 <= w <= 4096 or d["retainedBytes"] > n:
        return rejected("stream_budget")
    if not isinstance(v["windows"], list):
        return rejected("invalid_windows")
    parts = []
    cursor = 0
    finished = False
    for item in v["windows"]:
        if finished:
            return rejected("window_after_eof")
        if len(parts) >= w:
            return rejected("window_budget")
        result = chunk_oracle(v["operationRef"], d, item["request"], item["response"])
        if result["standing"] != "qualified":
            return rejected(result["reason"])
        if result["offset"] != cursor:
            return rejected("noncontiguous_window")
        parts.append(result["content"])
        cursor = result["next_offset"]
        finished = result["eof"]
        if finished and digest("".join(parts)) != d["digest"]:
            return rejected("stream_digest_mismatch")
    return {
        "standing": "verified" if finished else "incomplete",
        "received_bytes": cursor,
        "windows": len(parts),
    }


def add_stream_cases(add):
    def case(v):
        add("artifact_stream", v, oracle(v))

    for parts in ([""], ["x"], ["中", "🙂", "abc"], ["é", "e\u0301"]):
        v = stream_fixture(parts)
        case(v)
        case({**v, "windows": []})
        case({**v, "windows": v["windows"] + v["windows"][:1]})
        for limit in (0, 1, 4097, True, -1, 2**64):
            case({**v, "maxWindows": limit})
            case({**v, "maxTotalBytes": limit})
        case({**v, "operationRef": "wrong"})
    rng = random.Random(20261126)
    for _ in range(1024):
        parts = [
            "".join(rng.choice("abc中🙂é\n") for _ in range(rng.randrange(1, 12)))
            for _ in range(rng.randrange(2, 10))
        ]
        v = stream_fixture(parts)
        case(v)
        pos = rng.randrange(len(parts))
        case({**v, "windows": v["windows"][:pos]})
        mutation = copy.deepcopy(v)
        changed = mutation["windows"][pos]["response"]
        changed["content"] = "x" * len(parts[pos].encode("utf-8"))
        case(mutation)
        case({**v, "windows": v["windows"][:pos] + v["windows"][pos + 1 :]})
        case(
            {**v, "windows": v["windows"][:pos] + v["windows"][pos : pos + 1] + v["windows"][pos:]}
        )
        case({**v, "maxWindows": max(1, len(parts) - 1)})


def qualify_harness_source():
    # Execute the exact consumer method, with a fake peer to establish a source
    # counterexample; no claim of a corrupted real artifact.
    path = ROOT / "services/harness/src/ordivon_harness/gateway_execution_port.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {"_field", "read_stdout"}
    funcs = [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    assert len(funcs) == 2
    from typing import Any

    scope = {"JsonValue": Any, "GatewayExecutionResult": Any, "GatewayExecutionError": ValueError}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(path), "exec"), scope)
    original = SimpleNamespace(
        artifact_ids=("opaque.stdout",),
        operation_ref=REF,
        request_id="r",
        capability="execution.linux",
    )
    calls = []

    def reply(name, args):
        calls.append((name, args["offset"]))
        return {
            "operation_ref": REF,
            "artifact_id": "opaque.stdout",
            "offset": 0,
            "next_offset": 999,
            "eof": True,
            "content": "wrong",
            "digest": digest("right"),
        }

    assert scope["read_stdout"](SimpleNamespace(_call=reply), original) == "wrong"
    assert calls == [("artifact.read", 0)]
    try:
        scope["read_stdout"](
            SimpleNamespace(_call=reply),
            SimpleNamespace(**{**vars(original), "artifact_ids": ("opaque-id",)}),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("opaque kind-less ID unexpectedly accepted")
    print(
        "HARNESS_SOURCE_COUNTEREXAMPLE final geometry/digest accepted; opaque ID rejected",
        flush=True,
    )


async def qualify_stream_transport(binary: Path):
    text = "中文🙂abcé"
    raw = text.encode("utf-8")
    d, _, _ = fixture(text)
    normal = dict(
        operationRef=REF, descriptor=d, maxTotalBytes=len(raw), maxWindows=20, chunkBytes=4
    )
    binding = {
        "issuer": "fixture-issuer",
        "principal": "fixture-principal",
        "capability": "execution.linux",
        "request_id": "original",
        "operation_ref": REF,
    }
    key = (
        "request:gw-principal:"
        + hashlib.sha256(
            json.dumps(
                [
                    "ordivon.gateway-principal-scoped-execution-request.v1",
                    binding["issuer"],
                    binding["principal"],
                    binding["capability"],
                    binding["request_id"],
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    )
    import subprocess

    schema = json.loads(
        subprocess.check_output(
            [binary, "eval"], input=b'{"operation":"artifact_evidence_schema","input":null}\n'
        )
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    for legacy in (False, True):
        server = MCPServer("protected-stream-fixture")
        bearer = secrets.token_urlsafe(32)
        calls = []
        wire = []
        checked = []
        mode = "good"
        lookups = []

        @server.tool(name="job.list", structured_output=True)
        async def list_jobs(limit: int, clientRequestId: str) -> dict[str, object]:
            lookups.append((limit, clientRequestId))
            row = {
                "clientRequestId": key,
                "jobId": "job-a",
                "workspaceId": "ws-fixture",
                "createdAtMs": 1,
            }
            if clientRequestId != key or mode == "scope_absent":
                return {"jobs": [], "nextCursor": None}
            if mode == "scope_foreign":
                return {"jobs": [{**row, "clientRequestId": "other"}], "nextCursor": None}
            if mode == "scope_wrong_job":
                return {"jobs": [{**row, "jobId": "other"}], "nextCursor": None}
            if mode == "scope_ambiguous":
                return {"jobs": [row, {**row, "jobId": "other"}], "nextCursor": None}
            return {"jobs": [row], "nextCursor": None}

        @server.tool(name="artifact.read", structured_output=False)
        async def read(
            jobId: str, artifactId: str, offset: int, maxBytes: int, schemaVersion: int = 1
        ) -> CallToolResult:
            calls.append((jobId, artifactId, offset, maxBytes, schemaVersion))
            end = min(len(raw), offset + maxBytes)
            while end > offset:
                try:
                    content = raw[offset:end].decode("utf-8")
                    break
                except UnicodeDecodeError:
                    end -= 1
            else:
                content = ""
            result = dict(
                jobId=jobId,
                artifactId=artifactId,
                offset=offset,
                nextOffset=end,
                eof=end == len(raw),
                digest=d["digest"],
                content=content,
            )
            if mode in ("corrupt", "scope_corrupt") and offset == 0:
                result["content"] = "x" * (end - offset)
            if mode == "foreign" and offset == 0:
                result["artifactId"] = "other"
            if mode == "error":
                error = {
                    "origin": "runtime_core",
                    "code": "ARTIFACT_NOT_FOUND",
                    "commitState": "not_committed",
                    "message": "PRIVATE_FIXTURE_DETAIL",
                    "retryClass": "never",
                    "retryable": False,
                    "field": "artifactId",
                }
                return CallToolResult(
                    content=[TextContent(type="text", text="PRIVATE_FIXTURE_DETAIL")],
                    structuredContent={"error": error},
                    isError=True,
                )
            return CallToolResult(
                content=[TextContent(type="text", text="fixture")],
                structuredContent=result,
                isError=False,
            )

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
                dict(scope["headers"]).get(b"authorization", b""), ("Bearer " + bearer).encode()
            )
            checked.append(ok)
            if not ok:
                await PlainTextResponse("denied", status_code=401)(scope, receive, send)
                return
            if scope["method"] != "POST":
                await app(scope, receive, send)
                return
            chunks = []
            while True:
                msg = await receive()
                chunks.append(msg.get("body", b""))
                if not msg.get("more_body"):
                    break
            body = b"".join(chunks)
            wire.append(json.loads(body))
            done = False

            async def replay():
                nonlocal done
                if done:
                    return await receive()
                done = True
                return {"type": "http.request", "body": body, "more_body": False}

            await app(scope, replay, send)

        with tempfile.TemporaryDirectory(prefix="native-stream-") as tmp, socket.socket() as sock:
            credential = Path(tmp) / "token"
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
                for mode in (
                    "good",
                    "corrupt",
                    "foreign",
                    "error",
                    "budget",
                    "wrong",
                    "missing",
                    "invalid",
                    "scope_good",
                    "scope_corrupt",
                    "scope_absent",
                    "scope_foreign",
                    "scope_wrong_job",
                    "scope_ambiguous",
                    "scope_wrong_principal",
                    "scope_wrong_issuer",
                    "scope_wrong_request",
                    "scope_invalid",
                    "scope_ref_mismatch",
                ):
                    c, w, a, k = len(calls), len(wire), len(checked), len(lookups)
                    input = dict(normal)
                    scoped = mode.startswith("scope_")
                    if scoped:
                        input["binding"] = dict(binding)
                        if mode == "scope_wrong_principal":
                            input["binding"]["principal"] = "other"
                        if mode == "scope_wrong_issuer":
                            input["binding"]["issuer"] = "other"
                        if mode == "scope_wrong_request":
                            input["binding"]["request_id"] = "other"
                        if mode == "scope_invalid":
                            input["binding"]["capability"] = "execution.windows"
                        if mode == "scope_ref_mismatch":
                            input["binding"]["operation_ref"] = (
                                "ordivon-exec:v1:runtime.linux:other"
                            )
                    if mode == "budget":
                        input["maxWindows"] = 1
                    if mode == "invalid":
                        input["chunkBytes"] = 2
                    if mode == "missing":
                        credential.unlink()
                    else:
                        credential.write_text(
                            "wrong" if mode == "wrong" else bearer, encoding="ascii"
                        )
                        credential.chmod(0o600)
                    proc = await asyncio.create_subprocess_exec(
                        str(binary),
                        "verify-scoped-artifact-stream-fixture"
                        if scoped
                        else "verify-protected-artifact-stream-fixture",
                        endpoint,
                        str(credential),
                        "legacy" if legacy else "auto",
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    try:
                        out, err = await asyncio.wait_for(
                            proc.communicate(json.dumps(input).encode()), 8
                        )
                    finally:
                        if proc.returncode is None:
                            proc.kill()
                            await proc.wait()
                    assert proc.returncode == 0, err.decode()
                    assert (
                        bearer.encode() not in out + err
                        and b"PRIVATE_FIXTURE_DETAIL" not in out + err
                    )
                    actual = json.loads(out)
                    if scoped:
                        tc = [
                            m["params"]["name"] for m in wire[w:] if m.get("method") == "tools/call"
                        ]
                        if mode in ("scope_good", "scope_corrupt"):
                            assert actual["outcome"] == "scoped_stream", actual
                            evidence = actual["evidence"]
                            validator.validate(evidence)
                            assert evidence["operation_ref"] == REF and evidence["descriptor"] == d
                            assert evidence["evidence"]["standing"] == (
                                "verified" if mode == "scope_good" else "rejected"
                            )
                            assert tc == ["job.list"] + ["artifact.read"] * 5, tc
                            assert lookups[k:] == [(2, key)]
                            for invalid in (
                                {**evidence, "schema_version": 2},
                                {**evidence, "kind": "bad"},
                                {**evidence, "domain_success": True},
                                {**evidence, "evidence": {**evidence["evidence"], "forged": True}},
                            ):
                                assert not validator.is_valid(invalid), invalid
                        else:
                            assert actual == {
                                "outcome": "stream",
                                "evidence": {
                                    "standing": "rejected",
                                    "reason": "invalid_operation_binding"
                                    if mode in ("scope_invalid", "scope_ref_mismatch")
                                    else "unqualified_operation_binding",
                                },
                            }, actual
                            assert len(calls) == c
                            if mode in ("scope_invalid", "scope_ref_mismatch"):
                                assert not tc and len(checked) == a and len(lookups) == k
                            else:
                                assert tc == ["job.list"] and len(lookups) == k + 1, tc
                        continue
                    assert len(lookups) == k
                    if mode == "good":
                        assert actual == {
                            "outcome": "stream",
                            "evidence": {
                                "standing": "verified",
                                "received_bytes": len(raw),
                                "windows": 5,
                            },
                        }, actual
                    elif mode == "corrupt":
                        assert actual["evidence"] == {
                            "standing": "rejected",
                            "reason": "stream_digest_mismatch",
                        }, actual
                    elif mode == "foreign":
                        assert actual["evidence"]["reason"] == "mismatched_window_identity", actual
                    elif mode == "error":
                        assert (
                            actual["outcome"] == "owner_failure"
                            and actual["failure"]["failure"] == "tool"
                        ), actual
                    elif mode == "budget":
                        assert actual["evidence"] == {
                            "standing": "incomplete",
                            "received_bytes": 3,
                            "windows": 1,
                        }, actual
                    elif mode == "wrong":
                        assert (
                            actual["outcome"] == "owner_failure"
                            and checked[a:]
                            and not any(checked[a:])
                        ), actual
                    else:
                        assert actual["evidence"]["standing"] == "rejected", actual
                    new_calls = calls[c:]
                    if mode in ("wrong", "missing", "invalid"):
                        assert not new_calls
                        if mode != "wrong":
                            assert len(checked) == a
                    else:
                        assert all(checked[a:])
                        assert all(
                            row[0] == "job-a" and row[1] == d["artifactId"] and row[4] == 1
                            for row in new_calls
                        )
                        tool_calls = [m for m in wire[w:] if m.get("method") == "tools/call"]
                        assert len(tool_calls) == len(new_calls)
                        assert all(m["params"]["name"] == "artifact.read" for m in tool_calls)
                        assert len([m for m in wire[w:] if m.get("method") == "initialize"]) == int(
                            legacy
                        )
                        assert len(new_calls) == (5 if mode in ("good", "corrupt") else 1), (
                            mode,
                            new_calls,
                        )
                print(
                    "PROTECTED_STREAM_TCP_PASS",
                    "legacy" if legacy else "auto",
                    8,
                    "unscoped cases + 11 scoped cases",
                    flush=True,
                )
            finally:
                uv.should_exit = True
                await asyncio.wait_for(serving, 10)
