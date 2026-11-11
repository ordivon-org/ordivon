"""Local-only streamable-HTTP MCP smoke against one disposable PG18 schema13."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from jsonschema import Draft202012Validator

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

_http_output_schemas = {}
_http_validation_hits = set()



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
        if method == "tools/call" and "result" in body:
            result = body["result"]
            if not result.get("isError"):
                name = params["name"]
                schema = _http_output_schemas.get(name)
                assert schema is not None, ("missing HTTP output schema", name)
                structured = result.get("structuredContent")
                assert isinstance(structured, dict), (name, result)
                Draft202012Validator(schema).validate(structured)
                _http_validation_hits.add(name)
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
    registry = listed["result"]["tools"]
    names = [t["name"] for t in registry]
    for item in registry:
        assert "outputSchema" in item, item["name"]
        Draft202012Validator.check_schema(item["outputSchema"])
        _http_output_schemas[item["name"]] = item["outputSchema"]

    assert names == [
        "actor.declare",
        "attention.ack",
        "attention.delta",
        "attention.get",
        "attention.reentry",
        "host.status",
        "message.get",
        "message.post",
        "message.relation.add",
        "message.relation.list",
        "message.search",
        "space.create",
        "space.get",
        "space.list",
        "space.participation.list",
        "space.participation.set",
        "space.subject.list",
        "subscription.follow",
        "subscription.list",
        "subscription.unfollow",
        "topic.create",
        "topic.cursor.ack",
        "topic.cursor.get",
        "topic.list",
        "topic.resume",
        "topic.state.set",
        "work.create",
        "work.engagement.advance",
        "work.engagement.list",
        "work.get",
        "work.list",
        "work.snapshot.commit",
    ], names
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
    _, resumed, _ = post(
        "tools/call",
        {"name":"topic.resume","arguments":{"topicRef":"topic:test:rust-mcp-social","afterSequence":0}},
        6, session,
    )
    assert [m["messageRef"] for m in resumed["result"]["structuredContent"]["messages"]]==[
        "message:test:rust-mcp-python-seed","message:test:rust-mcp-social-rust"
    ],resumed
    _, r5_space_http, _ = post(
        "tools/call",
        {"name":"space.get","arguments":{"spaceRef":"space:test:rust-mcp-r5-first"}},
        7, session,
    )
    restored=r5_space_http["result"]["structuredContent"]
    assert restored["subjectRefs"]==["subject:alpha","subject:zeta"],restored
    assert restored["participantCount"]==1 and restored["topicCount"]==1,restored
    _, r5_search_http, _ = post(
        "tools/call",
        {"name":"message.search","arguments":{
            "query":"协作世界","spaceRef":"space:test:rust-mcp-r5-first",
            "topicRef":"topic:test:rust-mcp-r5-first",
        }},
        9, session,
    )
    searched=r5_search_http["result"]["structuredContent"]
    assert [m["messageRef"] for m in searched["messages"]]==[
        "message:test:rust-mcp-r5-first"
    ],searched
    _, r5_relations_http, _=post(
        "tools/call",
        {"name":"message.relation.list","arguments":{
            "messageRef":"message:test:rust-mcp-r5-first","direction":"both"
        }},10,session,
    )
    relation_page=r5_relations_http["result"]["structuredContent"]
    assert len(relation_page["relations"])==2,relation_page
    _, r5_topics_http, _=post(
        "tools/call",{"name":"topic.list","arguments":{
            "spaceRef":"space:test:rust-mcp-r5-first"
        }},11,session,
    )
    assert len(r5_topics_http["result"]["structuredContent"]["topics"])==1,r5_topics_http
    _, r6_spaces_http, _=post(
        "tools/call",{"name":"space.list","arguments":{
            "actorRef":"actor:test:rust-mcp-r5-first","subjectRef":"subject:alpha"
        }},12,session,
    )
    spaces=r6_spaces_http["result"]["structuredContent"]
    assert [s["spaceRef"] for s in spaces["spaces"]]==[
        "space:test:rust-mcp-r5-first"
    ],spaces
    _, r6_subjects_http, _=post(
        "tools/call",{"name":"space.subject.list","arguments":{
            "spaceRef":"space:test:rust-mcp-r5-first"
        }},13,session,
    )
    assert r6_subjects_http["result"]["structuredContent"]["subjectRefs"]==[
        "subject:alpha","subject:zeta"
    ],r6_subjects_http
    _, r6_members_http, _=post(
        "tools/call",{"name":"space.participation.list","arguments":{
            "spaceRef":"space:test:rust-mcp-r5-first"
        }},14,session,
    )
    assert len(r6_members_http["result"]["structuredContent"]["participants"])==1,r6_members_http
    _, historical, _ = post(
        "tools/call", {"name":"host.status","arguments":{"detail":"history"}}, 8, session,
    )
    doctor = historical["result"]["structuredContent"]["doctor"]
    assert doctor["healthy"] is False, historical
    diagnostics = {check["name"]: check for check in doctor["checks"]}
    assert diagnostics["work.current_snapshot"]["status"] == "ok", diagnostics
    assert diagnostics["work.snapshot_history_contiguous"]["detail"] == "invalidWorks=1", diagnostics
    assert diagnostics["work.snapshot_history_digest"]["detail"] == "invalid=1", diagnostics
    # A separate HTTP MCP session performs a new durable Work intake and
    # claim. Its full typed reply is validated by post() against the official
    # advertised output schema; old Python WorkStore rereads this same PG row.
    http_work_ref="work:test:r7-mcp-http"
    _, created_http, _=post("tools/call",{"name":"work.create","arguments":{
        "workRef":http_work_ref,"workKind":"research-deliverable",
        "actorRef":"actor:test:r7-mcp-requester",
        "initialSnapshot":{"objective":"HTTP Agent Work 协作","frontier":"awaiting claim"},
    }},100,session)
    assert created_http["result"]["structuredContent"]["revision"]==1,created_http
    _, offered_http, _=post("tools/call",{
        "name":"work.engagement.advance","arguments":{
            "workRef":http_work_ref,"expectedRevision":1,
            "actorRef":"actor:test:r7-mcp-requester",
            "clientRequestId":"request:r7:mcp:http-offer",
            "action":{"type":"offer",
                "consumerActorRef":"actor:test:r7-mcp-reviewer",
                "acceptanceCriteria":["指定消费方核对工件及验收证据"]},
        }
    },101,session)
    assert offered_http["result"]["structuredContent"]["snapshot"]["engagement"]["phase"]=="offered",offered_http
    _, inbox_http, _=post("tools/call",{
        "name":"work.engagement.list","arguments":{
            "phase":"offered","consumerActorRef":"actor:test:r7-mcp-reviewer"
        }
    },102,session)
    assert http_work_ref in {
        x["workRef"] for x in inbox_http["result"]["structuredContent"]["engagements"]
    },inbox_http
    _, claimed_http, _=post("tools/call",{
        "name":"work.engagement.advance","arguments":{
            "workRef":http_work_ref,"expectedRevision":2,
            "actorRef":"actor:test:r7-mcp-worker-a",
            "clientRequestId":"request:r7:mcp:http-claim",
            "action":{"type":"claim"},
        }
    },103,session)
    assert claimed_http["result"]["structuredContent"]["revision"]==3,claimed_http
    assert claimed_http["result"]["structuredContent"]["snapshot"]["engagement"]["claimEpoch"]==1,claimed_http
    print("R7_HTTP_NATIVE_WORK_ENGAGEMENT_PASS offer=1 claim=1 consumer_inbox=1 schema=ACTUAL")
    print(f"MCP_HTTP_OUTPUT_SCHEMA_VALIDATED_PASS published={len(_http_output_schemas)} exercised={len(_http_validation_hits)}")
    print(f"MCP_STREAMABLE_HTTP_PASS loopback=127.0.0.1 tools={len(names)} work_revision=2")
finally:
    server.terminate()
    try:
        server.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.communicate()
