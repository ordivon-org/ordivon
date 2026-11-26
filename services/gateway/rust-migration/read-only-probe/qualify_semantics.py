"""Independent source-backed error and descriptor contract qualification."""

from __future__ import annotations

import asyncio
import json
import random
import re
import socket
from pathlib import Path
from types import SimpleNamespace

import uvicorn
from mcp.server import MCPServer
from mcp_types import CallToolResult, TextContent

from ordivon_gateway.logic.owner_protocol import OwnerCallError
from ordivon_gateway.transport.owner_error_decode import extract_owner_tool_error
from ordivon_gateway.transport.owner_error_projection import (
    _host_cursor_recovery_text,
    _runtime_artifact_recovery_text,
)

RUNTIME = {
    "origin": "runtime_core",
    "code": "ARTIFACT_NOT_UTF8",
    "commitState": "not_committed",
    "message": "SECRET_NOT_FOR_OUTPUT",
    "retryClass": "never",
    "retryable": False,
    "field": "artifactId",
}
HOST = {
    "kind": "ordivon.host-domain-error",
    "schemaVersion": 1,
    "code": "CONFLICT",
    "reason": "topic_resume_cursor_ahead",
    "resourceKind": "topic",
    "retryable": False,
    "suggestedAction": "reread-topic-horizon-and-check-cursor-domain",
    "requestedAfterSequence": 200,
    "observedTopicHighSequence": 100,
    "detail": "SECRET_NOT_FOR_OUTPUT",
}


def descriptor(i):
    return dict(
        artifactId=f"opaque-{i}",
        attemptId="unrelated-attempt",
        kind="future-kind",
        digest="sha256:" + "a" * 64,
        retainedBytes=i,
        truncated=False,
    )


def independent_descriptor(payload, count):
    rows = payload.get("artifacts")
    ids = (
        [
            r.get("artifactId")
            for r in rows
            if isinstance(r, dict)
            and isinstance(r.get("artifactId"), str)
            and r["artifactId"].strip()
        ]
        if isinstance(rows, list)
        else []
    )
    coverage = (
        isinstance(rows, list) and len(ids) == len(rows) == count == len(set(ids))
        if type(count) is int and 0 <= count < 2**64
        else None
    )
    required = {"artifactId", "attemptId", "kind", "digest", "retainedBytes", "truncated"}

    def valid(row):
        return (
            isinstance(row, dict)
            and required <= row.keys() <= required | {"droppedBytes"}
            and all(
                isinstance(row[k], str) and row[k] and row[k].strip() == row[k]
                for k in ("artifactId", "attemptId", "kind")
            )
            and isinstance(row["digest"], str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", row["digest"]) is not None
            and all(
                type(row[k]) is int and 0 <= row[k] < 2**64
                for k in ("retainedBytes", "droppedBytes")
                if k in row
            )
            and type(row["truncated"]) is bool
        )

    metadata = None if coverage is None else coverage and all(map(valid, rows))
    return {
        "identity_complete": coverage,
        "metadata_complete": metadata,
        "descriptors": rows if metadata else [],
    }


def add_descriptor_cases(add):
    rng = random.Random(20261126)
    bad = [
        ("digest", "sha256:" + "z" * 64),
        ("digest", "sha256:" + "A" * 64),
        ("kind", " "),
        ("attemptId", None),
        ("artifactId", " x "),
        ("artifactId", ""),
        ("retainedBytes", True),
        ("retainedBytes", 2**64),
        ("retainedBytes", 1.0),
        ("truncated", 0),
        ("droppedBytes", None),
        ("droppedBytes", -1),
        ("extra", 1),
    ]

    def case(payload, count):
        add(
            "artifact_descriptor",
            {"payload": payload, "count": count},
            independent_descriptor(payload, count),
        )

    for k, v in bad:
        case({"artifacts": [{**descriptor(1), k: v}]}, 1)
    for count in (None, 0, 1, 2, False, -1, 1.0, 2**64):
        for payload in (
            {},
            {"artifacts": None},
            {"artifacts": []},
            {"artifacts": [descriptor(1)]},
            {"artifacts": [descriptor(1)] * 2},
        ):
            case(payload, count)
    for i in range(1024):
        rows = [descriptor(n) for n in range(rng.randrange(8))]
        for row in rows:
            row["retainedBytes"] = rng.randrange(2**64)
            if rng.randrange(2):
                row["droppedBytes"] = rng.randrange(2**64)
            if rng.randrange(4) == 0:
                k, v = rng.choice(bad)
                row[k] = v
        count = rng.choice((len(rows), len(rows), None, 0, len(rows) + 1))
        case({"artifacts": rows}, count)


def source_error(result, owner, tool):
    if result.get("isError") is not True or owner not in {
        "runtime.linux",
        "runtime.windows",
        "runtime.harness",
        "host",
        "host.read",
    }:
        return None
    adapted = SimpleNamespace(
        structured_content=result.get("structuredContent"),
        content=[
            SimpleNamespace(text=i.get("text"))
            for i in result.get("content", [])
            if i.get("type") == "text"
        ],
    )
    e = extract_owner_tool_error(adapted, owner_id=owner, tool_name=tool)
    if e is None:
        return None
    exc = OwnerCallError("opaque", owner_id=owner, tool_name=tool, error=e)
    host = _host_cursor_recovery_text(exc)
    art = _runtime_artifact_recovery_text(exc)
    if host:
        return {
            "kind": "host_cursor",
            "requested": e["requestedAfterSequence"],
            "observed": e["observedTopicHighSequence"],
        }
    if art:
        return {"kind": "runtime_artifact", "action": art.split("suggestedAction=")[1].split()[0]}
    if owner.startswith("runtime."):
        return {"kind": "runtime", "commit_state": e["commitState"], "retryable": e["retryable"]}
    return {"kind": "host"}


def add_error_cases(add):
    def case(result, owner, tool, expected=...):
        if expected is ...:
            expected = source_error(result, owner, tool)
        add("owner_error", dict(result=result, owner=owner, tool=tool), expected)

    for owner, tool, error in (
        ("runtime.linux", "artifact.read", RUNTIME),
        ("runtime.linux", "job.list", RUNTIME),
        ("runtime.windows", "artifact.read", RUNTIME),
        ("host", "topic.resume", HOST),
        ("host.read", "topic.resume", HOST),
        ("skills", "host.status", HOST),
    ):
        for k in error:
            for v in (None, False, 1, "invalid", [], {}):
                e = {**error, k: v}
                case({"isError": True, "structuredContent": {"error": e}}, owner, tool)
        for e in (error, {**error, "detail": "x" * 8200}, {**error, "detail": "汉" * 3000}):
            wrapper = {"error": e} if owner.startswith("runtime.") else e
            for text in (
                json.dumps(wrapper),
                f"Error executing tool {tool}: " + json.dumps(wrapper),
                "Error executing tool wrong: " + json.dumps(wrapper),
            ):
                case({"isError": True, "content": [{"type": "text", "text": text}]}, owner, tool)
        case({"isError": False, "structuredContent": {"error": error}}, owner, tool)
    rng = random.Random(20261126)
    for _ in range(512):
        e = {
            **HOST,
            "requestedAfterSequence": rng.randrange(2**64),
            "observedTopicHighSequence": rng.randrange(2**64),
        }
        case({"isError": True, "structuredContent": {"error": e}}, "host", "topic.resume")
    # Explicitly narrower native standing than legacy: no floating extension,
    # unknown Owner prefix, non-text content, or oversized UTF8 fallback.
    case(
        {"isError": True, "structuredContent": {"error": {**HOST, "extension": 1.5}}},
        "host",
        "topic.resume",
        None,
    )
    case(
        {"isError": True, "structuredContent": {"error": RUNTIME}},
        "runtime.unknown",
        "artifact.read",
        None,
    )
    case(
        {"isError": True, "content": [{"type": "image", "text": json.dumps({"error": RUNTIME})}]},
        "runtime.linux",
        "artifact.read",
        None,
    )


async def qualify_error_transport(binary: Path):
    for legacy in (False, True):
        server = MCPServer("typed-error-receiver")
        calls = []
        reply = None

        @server.tool(name="runtime.describe", structured_output=False)
        async def describe(schemaVersion: int = 1) -> CallToolResult:
            calls.append(schemaVersion)
            assert reply is not None
            return reply

        app = server.streamable_http_app(
            streamable_http_path="/mcp",
            stateless_http=not legacy,
            json_response=True,
            host="127.0.0.1",
        )
        cases = [
            (
                CallToolResult(
                    content=[TextContent(type="text", text="SECRET_NOT_FOR_OUTPUT")],
                    structuredContent={"error": RUNTIME},
                    isError=True,
                ),
                {
                    "failure": "tool",
                    "evidence": {
                        "kind": "runtime",
                        "commit_state": "not_committed",
                        "retryable": False,
                    },
                },
            ),
            (
                CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {"error": {**RUNTIME, "commitState": "unknown", "retryable": True}}
                            ),
                        )
                    ],
                    isError=True,
                ),
                {
                    "failure": "tool",
                    "evidence": {"kind": "runtime", "commit_state": "unknown", "retryable": True},
                },
            ),
            (
                CallToolResult(
                    content=[TextContent(type="text", text="SECRET_NOT_FOR_OUTPUT")],
                    structuredContent={"error": HOST},
                    isError=True,
                ),
                {"failure": "tool", "evidence": None},
            ),
            (
                CallToolResult(
                    content=[TextContent(type="text", text="SECRET_NOT_FOR_OUTPUT")],
                    structuredContent={"error": RUNTIME},
                    isError=False,
                ),
                {"standing": "reported"},
            ),
        ]
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen(128)
            endpoint = f"http://127.0.0.1:{sock.getsockname()[1]}/mcp"
            uv = uvicorn.Server(uvicorn.Config(app, log_level="critical"))
            serving = asyncio.create_task(uv.serve(sockets=[sock]))
            try:
                for _ in range(250):
                    if uv.started:
                        break
                    await asyncio.sleep(0.02)
                assert uv.started
                for reply, expected in cases:
                    before = len(calls)
                    proc = await asyncio.create_subprocess_exec(
                        str(binary),
                        "observe-runtime-error-fixture",
                        endpoint,
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
                    assert b"SECRET_NOT_FOR_OUTPUT" not in out + err
                    assert json.loads(out) == expected, (legacy, out, expected)
                    assert calls[before:] == [1]
                print(
                    "NATIVE_TYPED_ERROR_TCP_PASS",
                    "legacy" if legacy else "auto",
                    len(cases),
                    flush=True,
                )
            finally:
                uv.should_exit = True
                await asyncio.wait_for(serving, 10)
