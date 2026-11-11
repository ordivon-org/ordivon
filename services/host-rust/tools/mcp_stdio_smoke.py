"""Strict disposable-database MCP stdio protocol smoke, not a production client."""
import json
import os
import subprocess
import sys

if len(sys.argv) != 2 or not os.environ.get("HOST_RUST_TEST_DSN"):
    raise SystemExit("requires executable and isolated HOST_RUST_TEST_DSN")
if os.environ["ORDIVON_HOST_V2_DSN"] != os.environ["HOST_RUST_TEST_DSN"]:
    raise SystemExit("refusing mismatched target DSN")

p = subprocess.Popen(
    [sys.argv[1]],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=os.environ.copy(),
    text=True,
    bufsize=1,
)


def request(method, params=None, request_id=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if request_id is not None:
        msg["id"] = request_id
    p.stdin.write(json.dumps(msg) + "\n")
    p.stdin.flush()
    if request_id is not None:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("MCP subprocess ended: " + p.stderr.read()[:700])
        response = json.loads(line)
        assert response.get("id") == request_id, response
        assert "error" not in response, response
        return response["result"]


try:
    initialized = request(
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "host-rust-smoke", "version": "1.0.0"},
        },
        1,
    )
    assert initialized["serverInfo"]["name"]
    request("notifications/initialized")
    names = [tool["name"] for tool in request("tools/list", {}, 2)["tools"]]
    assert names == [
        "attention.ack", "attention.delta", "attention.get", "attention.reentry",
        "host.status", "subscription.follow", "subscription.list",
        "subscription.unfollow", "work.create", "work.get", "work.list",
        "work.snapshot.commit"
    ], names
    ok = request("tools/call", {"name": "host.status", "arguments": {"detail": "summary"}}, 3)
    data = ok.get("structuredContent")
    assert data is not None, ok
    assert data["schemaVersion"] == 3 and data["kind"] == "ordivon.host-status", data
    assert data["authority"]["journalSchema"] == 13, data
    assert data["authority"]["journalBackend"] == "postgresql", data
    assert data["doctor"] is None
    denied = request("tools/call", {"name": "host.status", "arguments": {"detail": "history"}}, 4)
    assert denied.get("isError") is True, denied
    initial = request(
        "tools/call",
        {"name": "work.get", "arguments": {"workRef": "work:test:rust-mcp-stdio"}},
        5,
    )
    assert initial["structuredContent"]["revision"] == 1, initial
    args = {
        "workRef": "work:test:rust-mcp-stdio",
        "expectedRevision": 1,
        "snapshot": {
            "objective": "Rust Host live MCP CAS 🌍",
            "frontier": "committed-via-rust-mcp",
            "established": ["PG18 CAS", "MCP wire parity"],
            "nextActions": ["verify Python recovery"],
        },
        "actorRef": "actor:test:rust-mcp",
        "continuityDisposition": "complete",
    }
    committed = request("tools/call", {"name": "work.snapshot.commit", "arguments": args}, 6)
    first = committed["structuredContent"]
    assert first["admission"] == "committed" and first["revision"] == 2, first
    assert first["state"] == "completed", first
    replay = request("tools/call", {"name": "work.snapshot.commit", "arguments": args}, 7)
    duplicate = replay["structuredContent"]
    assert duplicate["admission"] == "existing" and duplicate["revision"] == 2, duplicate
    current = request(
        "tools/call", {"name": "work.get", "arguments": {"workRef": args["workRef"]}}, 8
    )
    assert current["structuredContent"]["revision"] == 2, current
    historical = request(
        "tools/call", {"name": "work.get", "arguments": {"workRef": args["workRef"], "revision": 1}}, 9
    )
    assert historical["structuredContent"]["state"] == "historical_state_unknown", historical
    # Create and list through the actual MCP transport; not a domain-only test.
    new_ref = "work:test:rust-mcp-created"
    create_args = {
        "workRef": new_ref,
        "workKind": "migration-smoke",
        "actorRef": "actor:test:rust-mcp",
        "initialSnapshot": {
            "objective": "Rust MCP Work.create 🌍",
            "frontier": "created-with-rust",
            "nextActions": ["verify Python receipt"],
        },
    }
    created = request("tools/call", {"name": "work.create", "arguments": create_args}, 10)
    assert created["structuredContent"]["admission"] == "committed", created
    assert created["structuredContent"]["revision"] == 1, created
    duplicated = request("tools/call", {"name": "work.create", "arguments": create_args}, 11)
    assert duplicated["structuredContent"]["admission"] == "existing", duplicated
    listing = request(
        "tools/call",
        {"name": "work.list", "arguments": {"state": "open", "limit": 200}},
        12,
    )
    assert new_ref in {
        item["workRef"] for item in listing["structuredContent"]["works"]
    }, listing
    # C-owned MCP bridge exercises B's existing transaction-safe domain API.
    follow = request(
        "tools/call",
        {"name": "subscription.follow", "arguments": {
            "actorRef": "actor:test:rust-mcp", "targetKind": "work", "targetRef": new_ref
        }},
        13,
    )
    assert follow["structuredContent"]["admission"] in {"committed", "existing"}, follow
    subscriptions = request(
        "tools/call",
        {"name": "subscription.list", "arguments": {"actorRef": "actor:test:rust-mcp"}},
        14,
    )
    assert new_ref in {
        item["targetRef"] for item in subscriptions["structuredContent"]["subscriptions"]
    }, subscriptions
    for i, name, args in (
        (15, "attention.get", {"actorRef": "actor:test:rust-mcp"}),
        (16, "attention.delta", {"actorRef": "actor:test:rust-mcp", "afterSequence": 0}),
        (17, "attention.reentry", {"actorRef": "actor:test:rust-mcp", "afterSequence": 0}),
    ):
        response = request("tools/call", {"name": name, "arguments": args}, i)
        assert response.get("structuredContent"), (name, response)
    ack = request(
        "tools/call",
        {"name": "attention.ack", "arguments": {"actorRef": "actor:test:rust-mcp", "cursor": 0}},
        18,
    )
    assert ack.get("structuredContent"), ack
    unfollow = request(
        "tools/call",
        {"name": "subscription.unfollow", "arguments": {
            "actorRef": "actor:test:rust-mcp", "targetKind": "work", "targetRef": new_ref
        }},
        19,
    )
    assert unfollow["structuredContent"]["admission"] in {"committed", "existing"}, unfollow
    print(
        "MCP_STDIO_PASS"
        f" version={initialized['protocolVersion']} tools={names}"
        f" schema={data['authority']['journalSchema']}"
        " work_cas=COMMITTED work_replay=EXISTING history=UNKNOWN"
    )
finally:
    p.terminate()
    try:
        p.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
