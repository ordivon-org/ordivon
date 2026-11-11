"""Local-only streamable-HTTP MCP smoke against one disposable PG18 schema13."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

if len(sys.argv) != 2:
    raise SystemExit("expected Rust Host executable")
dsn = os.environ.get("HOST_RUST_TEST_DSN", "")
if not dsn or "127.0.0.1" not in dsn or os.environ.get("ORDIVON_HOST_V2_DSN") != dsn:
    raise SystemExit("refusing non-disposable PG test DSN")

with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]

env = dict(os.environ)
env.update(
    ORDIVON_HOST_V2_TRANSPORT="streamable-http",
    ORDIVON_HOST_V2_HOST="127.0.0.1",
    ORDIVON_HOST_V2_PORT=str(port),
    ORDIVON_HOST_V2_PATH="/mcp",
)
server = subprocess.Popen(
    [sys.argv[1]], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env
)
url = f"http://127.0.0.1:{port}/mcp"


def post(method, params, request_id, session=None):
    payload = {"jsonrpc": "2.0", "method": method}
    if request_id is not None:
        payload["id"] = request_id
    if params is not None:
        payload["params"] = params
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Protocol-Version": "2025-06-18",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=7) as response:
        data = response.read()
        if not data:
            body = {}
        else:
            decoded = data.decode("utf-8")
            try:
                body = json.loads(decoded)
            except json.JSONDecodeError:
                # SDK can use event-stream (including initialization priming)
                # even when subsequent normal requests use JSON responses.
                records = []
                for line in decoded.splitlines():
                    if line.startswith("data:"):
                        try:
                            records.append(json.loads(line[len("data:"):].strip()))
                        except json.JSONDecodeError:
                            continue
                valid = [item for item in records if isinstance(item, dict) and
                         item.get("jsonrpc") == "2.0"]
                if not valid:
                    raise RuntimeError("MCP HTTP returned unrecognized payload: " + decoded[:800])
                body = valid[-1]
        return response.status, body, response.headers


try:
    initialized = None
    for _ in range(100):
        if server.poll() is not None:
            raise RuntimeError("Rust HTTP Host exited during startup")
        try:
            initialized = post(
                "initialize",
                {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "host-rust-http-smoke", "version": "1.0.0"},
                },
                1,
            )
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    assert initialized is not None, "Rust HTTP Host didn't accept initialization"
    status, body, headers = initialized
    assert status == 200 and body["result"]["serverInfo"]["name"], body
    session = headers.get("Mcp-Session-Id")
    assert session, "missing stateful MCP session"
    # Origin/Host allowlist is a real network boundary; localhost binding alone
    # cannot protect against a browser resolving an attacker hostname to loopback.
    bad_origin = urllib.request.Request(
        url,
        data=json.dumps({
            "jsonrpc": "2.0", "id": 99, "method": "tools/list", "params": {}
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Mcp-Protocol-Version": "2025-06-18",
            "Mcp-Session-Id": session,
            "Origin": "https://untrusted.example",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(bad_origin, timeout=7)
        raise AssertionError("Host accepted untrusted Origin header")
    except urllib.error.HTTPError as exc:
        assert exc.code in {400, 403}, f"unexpected Origin rejection: {exc.code}"

    notify_status, _, _ = post("notifications/initialized", None, None, session)
    assert notify_status == 202, notify_status
    _, listed, _ = post("tools/list", {}, 2, session)
    names = [t["name"] for t in listed["result"]["tools"]]
    assert names == ["host.status", "work.create", "work.get", "work.list", "work.snapshot.commit"], names
    _, work, _ = post(
        "tools/call",
        {"name": "work.get", "arguments": {"workRef": "work:test:rust-mcp-stdio"}},
        3,
        session,
    )
    assert work["result"]["structuredContent"]["revision"] == 2, work
    _, status, _ = post(
        "tools/call",
        {"name": "host.status", "arguments": {"detail": "summary"}},
        4,
        session,
    )
    assert status["result"]["structuredContent"]["authority"]["journalSchema"] == 13, status
    _, listing, _ = post(
        "tools/call",
        {"name": "work.list", "arguments": {"state": "open", "limit": 200}},
        5,
        session,
    )
    assert "work:test:rust-mcp-created" in {
        item["workRef"] for item in listing["result"]["structuredContent"]["works"]
    }, listing
    print(f"MCP_STREAMABLE_HTTP_PASS loopback=127.0.0.1 tools={len(names)} work_revision=2")
finally:
    server.terminate()
    try:
        server.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.communicate()
