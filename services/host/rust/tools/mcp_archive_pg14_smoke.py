"""Independent real MCP stdio consumer contract against disposable PG18 schema14 only."""
import json
import os
import subprocess
import sys

import psycopg

assert len(sys.argv) == 2, "Rust binary argument required"
dsn = os.environ["HOST_RUST_TEST_DSN"]
assert dsn == os.environ["ORDIVON_HOST_V2_DSN"]
assert "127.0.0.1" in dsn or "localhost" in dsn, "refuse nonloopback database"

actor = "actor:r46:mcp-archive"
space = "space:r46:mcp-archive"
archived = "topic:r46:mcp-archive-a"
active = "topic:r46:mcp-archive-z"
with psycopg.connect(dsn) as db:
    db.execute("INSERT INTO actor_refs(actor_ref,actor_kind) VALUES(%s,'agent')", (actor,))
    db.execute(
        "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES(%s,'R46 real MCP',%s)",
        (space, actor),
    )
    for ref in [archived, active]:
        db.execute(
            "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) VALUES(%s,%s,'R46','open',%s)",
            (ref, space, actor),
        )

proc = subprocess.Popen(
    [sys.argv[1]],
    env=os.environ.copy(),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


def request(method, params=None, request_id=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if request_id is not None:
        msg["id"] = request_id
    proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    if request_id is None:
        return
    raw = proc.stdout.readline()
    assert raw, "Rust stdio MCP ended: " + proc.stderr.read()[:1600]
    result = json.loads(raw)
    assert result.get("id") == request_id, result
    assert "error" not in result, result
    return result["result"]


call_no = 4


def call(name, args, *, failure=None):
    global call_no
    call_no += 1
    result = request("tools/call", {"name": name, "arguments": args}, call_no)
    if failure:
        assert result.get("isError") is True, (name, result)
        assert result["structuredContent"]["error"]["code"] == failure, result
        return result["structuredContent"]
    assert not result.get("isError"), (name, result)
    assert isinstance(result.get("structuredContent"), dict), result
    return result["structuredContent"]


try:
    info = request(
        "initialize",
        {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "archive-r46", "version": "1"}},
        1,
    )
    assert info["serverInfo"]["name"], info
    request("notifications/initialized")
    registry = request("tools/list", {}, 2)["tools"]
    tools = {tool["name"]: tool for tool in registry}
    for required in ["host.status", "topic.list", "topic.state.set", "topic.resume", "message.post", "message.get"]:
        assert required in tools, required
    topic_input = tools["topic.list"]["inputSchema"]
    assert "includeArchived" in topic_input["properties"], topic_input
    state_input = tools["topic.state.set"]["inputSchema"]
    assert "state" in state_input["properties"] and "expectedState" in state_input["properties"]
    status = call("host.status", {"detail": "summary"})
    assert status["authority"]["journalSchema"] == 14, status

    msg = call("message.post", {
        "messageRef": "message:r46:mcp-archive", "spaceRef": space, "topicRef": archived,
        "authorActorRef": actor, "body": "durable before archive", "recordedAtMs": 1_795_012_000_000,
        "messageKind": "finding"
    })
    high = msg["sequence"]
    invalid = call("topic.state.set", {
        "topicRef": archived, "actorRef": actor, "state": "archived", "expectedState": "open",
        "expectedHighSequence": high,
    }, failure="CONFLICT")
    closed = call("topic.state.set", {
        "topicRef": archived, "actorRef": actor, "state": "closed", "expectedState": "open",
        "expectedHighSequence": high,
    })
    assert closed["state"] == "closed"
    done = call("topic.state.set", {
        "topicRef": archived, "actorRef": actor, "state": "archived", "expectedState": "closed",
        "expectedHighSequence": high,
    })
    assert done["state"] == "archived"
    default = call("topic.list", {"spaceRef": space})
    assert [x["topicRef"] for x in default["topics"]] == [active], default
    explicit = call("topic.list", {"spaceRef": space, "includeArchived": True})
    assert [x["topicRef"] for x in explicit["topics"]] == [archived, active], explicit
    assert explicit["topics"][0]["state"] == "archived"

    resumed = call("topic.resume", {"topicRef": archived, "afterSequence": 0, "limit": 50})
    assert [x["messageRef"] for x in resumed["messages"]] == [msg["messageRef"]], resumed
    exact = call("message.get", {"messageRef": msg["messageRef"]})
    assert exact["messageDigest"] == msg["messageDigest"]

    call("topic.state.set", {
        "topicRef": archived, "actorRef": actor, "state": "open", "expectedState": "archived",
        "expectedHighSequence": high,
    }, failure="CONFLICT")
    restore = call("topic.state.set", {
        "topicRef": archived, "actorRef": actor, "state": "closed", "expectedState": "archived",
        "expectedHighSequence": high,
    })
    assert restore["state"] == "closed"
    reopened = call("topic.state.set", {
        "topicRef": archived, "actorRef": actor, "state": "open", "expectedState": "closed",
        "expectedHighSequence": high,
    })
    assert reopened["state"] == "open"
    assert len(call("topic.list", {"spaceRef": space})["topics"]) == 2
    print("R46_RUST_REAL_MCP_STDIO_PG14_ARCHIVED_CONSUMER_PASS: default_hidden=1 explicit=2 source_message=preserved lifecycle_two_step=PASS input_schema=PASS host_schema=14", flush=True)
finally:
    proc.stdin.close()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(timeout=5)
    proc.stdout.close()
    proc.stderr.close()
