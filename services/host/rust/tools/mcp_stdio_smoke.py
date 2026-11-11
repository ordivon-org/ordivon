"""Strict disposable-database MCP stdio protocol smoke, not a production client."""
import json
import os
import subprocess
import sys

from jsonschema import Draft202012Validator

if len(sys.argv) != 2 or not os.environ.get("HOST_RUST_TEST_DSN"):
    raise SystemExit("requires executable and isolated HOST_RUST_TEST_DSN")
if os.environ["ORDIVON_HOST_V2_DSN"] != os.environ["HOST_RUST_TEST_DSN"]:
    raise SystemExit("refusing mismatched target DSN")

# The metadata is a claim: validate each actual successful structuredContent.
_published_schemas = {}
_schema_validation_hits = set()

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
        result = response["result"]
        if method == "tools/call" and not result.get("isError"):
            name = params["name"]
            schema = _published_schemas.get(name)
            assert schema is not None, ("unregistered output schema", name)
            payload = result.get("structuredContent")
            assert isinstance(payload, dict), (name, result)
            Draft202012Validator(schema).validate(payload)
            _schema_validation_hits.add(name)
        return result


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
    registry = request("tools/list", {}, 2)["tools"]
    names = [tool["name"] for tool in registry]
    for item in registry:
        assert "outputSchema" in item, item["name"]
        schema = item["outputSchema"]
        Draft202012Validator.check_schema(schema)
        _published_schemas[item["name"]] = schema

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
        "space.participation.set",
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
        "work.get",
        "work.list",
        "work.snapshot.commit",
    ], names
    ok = request("tools/call", {"name": "host.status", "arguments": {"detail": "summary"}}, 3)
    data = ok.get("structuredContent")
    assert data is not None, ok
    assert data["schemaVersion"] == 3 and data["kind"] == "ordivon.host-status", data
    assert data["authority"]["journalSchema"] == 13, data
    assert data["authority"]["journalBackend"] == "postgresql", data
    assert data["doctor"] is None
    doctor_path = os.environ.get("HOST_RUST_DOCTOR_ORACLE_PATH")
    assert doctor_path, "original Python Host Doctor oracle missing"
    with open(doctor_path, encoding="utf-8") as file:
        python_doctor = json.load(file)
    def comparable(value):
        return {key: item for key, item in value.items() if key != "observedAtMs"}
    assert comparable(data) == python_doctor["summary"], (data, python_doctor)
    integrity = request(
        "tools/call", {"name":"host.status","arguments":{"detail":"integrity"}}, 4
    )
    assert integrity.get("isError") is not True, integrity
    assert comparable(integrity["structuredContent"]) == python_doctor["integrity"], integrity
    history = request(
        "tools/call", {"name":"host.status","arguments":{"detail":"history"}}, 57
    )
    assert history.get("isError") is not True, history
    assert comparable(history["structuredContent"]) == python_doctor["history"], history
    assert history["structuredContent"]["doctor"]["healthy"] is False, history
    doctor_checks = {check["name"]:check for check in history["structuredContent"]["doctor"]["checks"]}
    assert doctor_checks["work.current_snapshot"]["status"] == "ok", doctor_checks
    assert doctor_checks["work.snapshot_history_contiguous"]["detail"] == "invalidWorks=1"
    assert doctor_checks["work.snapshot_history_digest"]["detail"] == "invalid=1"
    print("MCP_DOCTOR_R5_PYTHON_RUST_PARITY_PASS summary+integrity+history MVCC=ONE_HISTORY_SNAPSHOT gap=1 digest=1")

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
    # Negative wire parity: expected domain rejections are typed and recoverable
    # by the Gateway rather than opaque, unclassified text failures.
    future = request(
        "tools/call",
        {"name": "attention.delta", "arguments": {
            "actorRef": "actor:test:rust-mcp", "afterSequence": 1000000000
        }},
        20,
    )
    assert future.get("isError") is True, future
    error = future.get("structuredContent", {}).get("error")
    assert error and error["code"] == "CONFLICT", future
    assert error["kind"] == "ordivon.host-domain-error", future
    assert error["retryable"] is False, future
    assert error["suggestedAction"] == "reread-current-state-and-reconcile", future
    assert future["content"][0]["text"].startswith(
        "Error executing tool attention.delta: {"
    ), future
    absent = request(
        "tools/call",
        {"name": "work.get", "arguments": {"workRef": "work:test:never-existed"}},
        21,
    )
    assert absent.get("isError") is True, absent
    missing = absent.get("structuredContent", {}).get("error")
    assert missing and missing["code"] == "NOT_FOUND", absent
    assert missing["resourceKind"] == "work", absent
    bad_cursor = request(
        "tools/call",
        {"name": "subscription.list", "arguments": {
            "actorRef": "actor:test:rust-mcp", "afterTargetKind": "work"
        }},
        22,
    )
    assert bad_cursor.get("structuredContent", {}).get("error", {}).get("code") == "INVALID_ARGUMENT"
    print("MCP_DOMAIN_ERROR_ENVELOPE_PASS conflicts=typed not_found=typed invalid_argument=typed")
    # Actual cross-language Social continuity: Python created this Topic and
    # its first message. Rust reads, writes, links and acknowledges the exact
    # same PG authority, then Python checks receipts and persisted state.
    social_topic = "topic:test:rust-mcp-social"
    social_space = "space:test:rust-mcp-social"
    actor = "actor:test:rust-mcp"
    original_message = "message:test:rust-mcp-python-seed"
    new_message = "message:test:rust-mcp-social-rust"
    first_page = request(
        "tools/call",
        {"name": "topic.resume", "arguments": {"topicRef":social_topic,"afterSequence":0}},
        23,
    )
    first_data = first_page["structuredContent"]
    assert [m["messageRef"] for m in first_data["messages"]] == [original_message], first_data
    cursor_before = request(
        "tools/call",
        {"name":"topic.cursor.get","arguments":{"actorRef":actor,"topicRef":social_topic}},
        24,
    )
    assert cursor_before["structuredContent"]["cursor"] == 0, cursor_before
    post_args = {
        "messageRef":new_message,"spaceRef":social_space,"topicRef":social_topic,
        "authorActorRef":actor,"body":"Rust 续读后提交，原始 Python Host 可恢复 🌍",
        "recordedAtMs":1700000000111,"messageKind":"finding",
    }
    posted = request("tools/call",{"name":"message.post","arguments":post_args},25)
    posted_data=posted["structuredContent"]
    assert posted_data["admission"]=="committed",posted
    posted_again = request("tools/call",{"name":"message.post","arguments":post_args},26)
    assert posted_again["structuredContent"]["admission"]=="existing",posted_again
    relation_args = {"sourceMessageRef":new_message,"relation":"reply_to",
                     "targetRef":original_message,"actorRef":actor}
    linked = request("tools/call",{"name":"message.relation.add","arguments":relation_args},27)
    assert linked["structuredContent"]["admission"]=="committed",linked
    linked_again = request("tools/call",{"name":"message.relation.add","arguments":relation_args},28)
    assert linked_again["structuredContent"]["sourceMessageRef"]==new_message,linked_again
    second_page=request("tools/call",{"name":"topic.resume","arguments":{
        "topicRef":social_topic,"afterSequence":first_data["messages"][0]["sequence"],
    }},29)
    assert [m["messageRef"] for m in second_page["structuredContent"]["messages"]]==[new_message],second_page
    high=posted_data["sequence"]
    ack_args={"actorRef":actor,"topicRef":social_topic,"cursor":high}
    acknowledged=request("tools/call",{"name":"topic.cursor.ack","arguments":ack_args},30)
    assert acknowledged["structuredContent"]["cursor"]==high,acknowledged
    read_cursor=request("tools/call",{"name":"topic.cursor.get","arguments":{
        "actorRef":actor,"topicRef":social_topic,
    }},31)
    assert read_cursor["structuredContent"]["cursor"]==high,read_cursor
    beyond=request("tools/call",{"name":"topic.cursor.ack","arguments":{
        "actorRef":actor,"topicRef":social_topic,"cursor":high+1
    }},32)
    assert beyond["structuredContent"]["error"]["code"]=="CONFLICT",beyond
    close_args={"topicRef":social_topic,"actorRef":actor,"state":"closed",
                "expectedState":"open","expectedHighSequence":high}
    closed=request("tools/call",{"name":"topic.state.set","arguments":close_args},33)
    assert closed["structuredContent"]["state"]=="closed",closed
    post_closed=request("tools/call",{"name":"message.post","arguments":{
        **post_args,"messageRef":"message:test:rust-mcp-closed-rejected"
    }},34)
    assert post_closed["structuredContent"]["error"]["code"]=="CONFLICT",post_closed
    stale=request("tools/call",{"name":"topic.state.set","arguments":{
        **close_args,"expectedHighSequence":0,
    }},35)
    assert stale["structuredContent"]["error"]["code"]=="CONFLICT",stale
    retained=request("tools/call",{"name":"topic.resume","arguments":{
        "topicRef":social_topic,"afterSequence":0,
    }},36)
    assert [m["messageRef"] for m in retained["structuredContent"]["messages"]]==[
        original_message,new_message,
    ],retained
    print("MCP_SOCIAL_CONTINUITY_PASS python_seed=1 rust_message=1 relation=1 cursor_ack=1 cas_close=1 negative_conflict=3")
    actor_args={"actorRef":"actor:test:rust-mcp-declared","actorKind":"agent"}
    declared = request("tools/call",{"name":"actor.declare","arguments":actor_args},37)
    assert declared["structuredContent"]["admission"] == "committed",declared
    replay = request("tools/call",{"name":"actor.declare","arguments":actor_args},38)
    assert replay["structuredContent"]["admission"] == "existing",replay
    assert replay["structuredContent"]["createdAt"] == declared["structuredContent"]["createdAt"]
    bad_kind = request("tools/call",{"name":"actor.declare","arguments":{
        **actor_args,"actorKind":"human",
    }},39)
    assert bad_kind["isError"] is True,bad_kind
    assert bad_kind["structuredContent"]["error"]["code"]=="CONFLICT",bad_kind
    print("MCP_ACTOR_DECLARE_PASS new=committed replay=existing conflicting_kind=rejected")
    # R5: All first collaboration resources originate from Rust MCP rather
    # than Python seeding an already-existing Space/Topic. Domain receipts
    # and rows are later independently recovered with the original Python Host.
    r5_actor = "actor:test:rust-mcp-r5-first"
    r5_space = "space:test:rust-mcp-r5-first"
    r5_topic = "topic:test:rust-mcp-r5-first"
    r5_message = "message:test:rust-mcp-r5-first"
    actor = request("tools/call",{"name":"actor.declare","arguments":{
        "actorRef":r5_actor,"actorKind":"agent",
    }},40)
    assert actor["structuredContent"]["admission"]=="committed",actor
    original_space = {"spaceRef":r5_space,"purpose":"新 Agent 的 Rust MCP 原生协作 🧩",
                      "actorRef":r5_actor,"subjectRefs":["subject:zeta","subject:alpha"]}
    space = request("tools/call",{"name":"space.create","arguments":original_space},41)
    space_data = space["structuredContent"]
    assert space_data["admission"]=="committed",space
    assert space_data["subjectRefs"]==["subject:alpha","subject:zeta"],space
    duplicate = request("tools/call",{"name":"space.create","arguments":original_space},42)
    assert duplicate["structuredContent"]["admission"]=="existing",duplicate
    assert duplicate["structuredContent"]["createdAt"]==space_data["createdAt"],duplicate
    early_space = request("tools/call",{"name":"space.get","arguments":{
        "spaceRef":r5_space,
    }},43)
    assert early_space["structuredContent"]["participantCount"]==0,early_space
    assert early_space["structuredContent"]["topicCount"]==0,early_space
    topic_args={"topicRef":r5_topic,"spaceRef":r5_space,
                "title":"由 Rust MCP 原生创建的会话 🧩","actorRef":r5_actor}
    topic=request("tools/call",{"name":"topic.create","arguments":topic_args},44)
    assert topic["structuredContent"]["admission"]=="committed",topic
    assert topic["structuredContent"]["state"]=="open",topic
    same_topic=request("tools/call",{"name":"topic.create","arguments":topic_args},45)
    assert same_topic["structuredContent"]["admission"]=="existing",same_topic
    joined_args={"spaceRef":r5_space,"actorRef":r5_actor,"standing":"joined"}
    joined=request("tools/call",{"name":"space.participation.set","arguments":joined_args},46)
    assert joined["structuredContent"]["standing"]=="joined",joined
    left=request("tools/call",{"name":"space.participation.set","arguments":{
        **joined_args,"standing":"left",
    }},47)
    assert left["structuredContent"]["standing"]=="left",left
    joined_again=request("tools/call",{"name":"space.participation.set","arguments":joined_args},48)
    assert joined_again["structuredContent"]["standing"]=="joined",joined_again
    # Stale desired-state hash must not replay a former joined result after a
    # left transition; no command-receipt mapping for membership.
    assert joined_again["structuredContent"]["updatedAt"]>=left["structuredContent"]["updatedAt"]
    current_space=request("tools/call",{"name":"space.get","arguments":{
        "spaceRef":r5_space,"participantLimit":200,"topicLimit":200,"maxBytes":2097152
    }},49)
    sp=current_space["structuredContent"]
    assert sp["participantCount"]==1 and sp["participants"][0]["standing"]=="joined",sp
    assert sp["topicCount"]==1 and sp["topics"][0]["topicRef"]==r5_topic,sp
    new_message_args={
        "messageRef":r5_message,"spaceRef":r5_space,"topicRef":r5_topic,
        "authorActorRef":r5_actor,
        "body":"新 Agent 从零创建协作世界，真实 Rust MCP↔Python Host 🌍",
        "recordedAtMs":1700000000222,"messageKind":"finding",
    }
    posted=request("tools/call",{"name":"message.post","arguments":new_message_args},50)
    assert posted["structuredContent"]["admission"]=="committed",posted
    # R5 B-owned immutable Message read and indexed CJK search:
    # real rmcp transport, exact original-Python recovery through the same PG.
    read_response=request("tools/call",{"name":"message.get","arguments":{
        "messageRef":r5_message,"expectedDigest":posted["structuredContent"]["messageDigest"]
    }},60)
    read_data=read_response["structuredContent"]
    assert read_data["kind"]=="ordivon.host-message-read",read_response
    assert read_data["body"]==new_message_args["body"],read_response
    assert read_data["messageRef"]==r5_message,read_response
    search_args={"query":"协作世界","spaceRef":r5_space,"topicRef":r5_topic}
    searched=request("tools/call",{"name":"message.search","arguments":search_args},61)
    searched_data=searched["structuredContent"]
    assert searched_data["kind"]=="ordivon.host-message-search",searched
    assert searched_data["ordering"]=="sequence_desc",searched
    assert searched_data["rankingApplied"] is False,searched
    assert [m["messageRef"] for m in searched_data["messages"]]==[r5_message],searched
    observed_path=os.environ.get("HOST_RUST_READ_SEARCH_ORACLE_PATH")
    assert observed_path, "missing original Python message-read parity output path"
    with open(observed_path,"w",encoding="utf-8") as file:
        json.dump({"read":read_data,"search":searched_data},file,ensure_ascii=False,sort_keys=True)
        file.write("\n")
    before=request("tools/call",{"name":"message.search","arguments":{
        **search_args,"beforeSequence":posted["structuredContent"]["sequence"],
    }},62)
    assert before["structuredContent"]["messages"]==[],before
    mismatch=request("tools/call",{"name":"message.get","arguments":{
        "messageRef":r5_message,"expectedDigest":"sha256:"+"0"*64,
    }},63)
    assert mismatch["structuredContent"]["error"]["code"]=="CONFLICT",mismatch
    missing=request("tools/call",{"name":"message.get","arguments":{
        "messageRef":"message:test:r5-not-found",
    }},64)
    assert missing["structuredContent"]["error"]["code"]=="NOT_FOUND",missing
    assert missing["structuredContent"]["error"]["resourceKind"]=="message",missing
    assert missing["structuredContent"]["error"]["resourceRef"]=="message:test:r5-not-found",missing
    blank=request("tools/call",{"name":"message.search","arguments":{
        **search_args,"query":"   ",
    }},65)
    assert blank["structuredContent"]["error"]["code"]=="INVALID_ARGUMENT",blank
    missing_topic=request("tools/call",{"name":"message.search","arguments":{
        **search_args,"topicRef":"topic:test:r5-not-found",
    }},66)
    assert missing_topic["structuredContent"]["error"]["code"]=="NOT_FOUND",missing_topic
    assert missing_topic["structuredContent"]["error"]["resourceKind"]=="topic",missing_topic
    print("MCP_B_MESSAGE_GET_SEARCH_R5_PASS read=EXACT indexed_CJK=YES descending=true cursor=bounded integrity=guarded typed_errors=4")
    discovered=request("tools/call",{"name":"topic.resume","arguments":{
        "topicRef":r5_topic,"afterSequence":0
    }},51)
    assert [m["messageRef"] for m in discovered["structuredContent"]["messages"]]==[r5_message],discovered
    conflict=request("tools/call",{"name":"space.create","arguments":{
        **original_space,"purpose":"different initial semantics"
    }},52)
    assert conflict.get("structuredContent",{}).get("error",{}).get("code")=="CONFLICT",conflict
    wrong_topic=request("tools/call",{"name":"topic.create","arguments":{
        **topic_args,"title":"wrong original title"
    }},53)
    assert wrong_topic.get("structuredContent",{}).get("error",{}).get("code")=="CONFLICT",wrong_topic
    bad_space=request("tools/call",{"name":"space.create","arguments":{
        **original_space,"spaceRef":"space:invalid ",
    }},54)
    assert bad_space.get("structuredContent",{}).get("error",{}).get("code")=="INVALID_ARGUMENT",bad_space
    duplicate_subject=request("tools/call",{"name":"space.create","arguments":{
        **original_space,"spaceRef":"space:test:rust-mcp-r5-duplicate-subject",
        "subjectRefs":["subject:same","subject:same"]
    }},55)
    assert duplicate_subject.get("structuredContent",{}).get("error",{}).get("code")=="INVALID_ARGUMENT",duplicate_subject
    missing_actor=request("tools/call",{"name":"space.create","arguments":{
        **original_space,"spaceRef":"space:test:rust-mcp-r5-no-actor",
        "actorRef":"actor:test:not-declared"
    }},56)
    assert missing_actor.get("structuredContent",{}).get("error",{}).get("code")=="NOT_FOUND",missing_actor
    missing_resource = missing_actor["structuredContent"]["error"]
    assert missing_resource["resourceKind"] == "actor", missing_resource
    assert missing_resource["resourceRef"] == "actor:test:not-declared", missing_resource
    # B's native RR/byte-budget relations and Topic inventories now go
    # through official rmcp, and Python re-reads the identical PG response.
    references_args={"sourceMessageRef":r5_message,"relation":"references",
                     "targetRef":r5_message,"actorRef":r5_actor}
    self_ref=request("tools/call",{"name":"message.relation.add","arguments":references_args},67)
    assert self_ref["structuredContent"]["admission"]=="committed",self_ref
    opaque_args={"sourceMessageRef":r5_message,"relation":"about",
                 "targetRef":"subject:test:r5-opaque","actorRef":r5_actor}
    opaque=request("tools/call",{"name":"message.relation.add","arguments":opaque_args},68)
    assert opaque["structuredContent"]["admission"]=="committed",opaque
    both_args={"messageRef":r5_message,"direction":"both"}
    both=request("tools/call",{"name":"message.relation.list","arguments":both_args},69)
    both_data=both["structuredContent"]
    assert len(both_data["relations"])==2,both
    assert {v["relation"] for v in both_data["relations"]}=={"references","about"},both
    outgoing=request("tools/call",{"name":"message.relation.list","arguments":{
        **both_args,"direction":"outgoing"
    }},70)
    assert len(outgoing["structuredContent"]["relations"])==2,outgoing
    incoming=request("tools/call",{"name":"message.relation.list","arguments":{
        **both_args,"direction":"incoming"
    }},71)
    assert len(incoming["structuredContent"]["relations"])==1,incoming
    assert incoming["structuredContent"]["relations"][0]["relation"]=="references",incoming
    first=request("tools/call",{"name":"message.relation.list","arguments":{
        **both_args,"limit":1
    }},72)
    first_data=first["structuredContent"]
    assert len(first_data["relations"])==1 and first_data["hasMore"] is True,first
    second=request("tools/call",{"name":"message.relation.list","arguments":{
        **both_args,"afterChangeSequence":first_data["nextAfterChangeSequence"],"limit":1
    }},73)
    assert len(second["structuredContent"]["relations"])==1,second
    assert [m["targetRef"] for m in first_data["relations"]+second["structuredContent"]["relations"]]==[
        m["targetRef"] for m in both_data["relations"]
    ],(first,second,both)
    topic_inventory=request("tools/call",{"name":"topic.list","arguments":{
        "spaceRef":r5_space
    }},74)
    topics_data=topic_inventory["structuredContent"]
    assert [t["topicRef"] for t in topics_data["topics"]]==[r5_topic],topic_inventory
    after_topic=request("tools/call",{"name":"topic.list","arguments":{
        "spaceRef":r5_space,"afterTopicRef":r5_topic
    }},75)
    assert after_topic["structuredContent"]["topics"]==[],after_topic
    rel_missing=request("tools/call",{"name":"message.relation.list","arguments":{
        "messageRef":"message:test:r5-absent-for-relations"
    }},76)
    assert rel_missing["structuredContent"]["error"]["resourceKind"]=="message",rel_missing
    assert rel_missing["structuredContent"]["error"]["code"]=="NOT_FOUND",rel_missing
    topics_missing=request("tools/call",{"name":"topic.list","arguments":{
        "spaceRef":"space:test:r5-absent-for-topics"
    }},77)
    assert topics_missing["structuredContent"]["error"]["resourceKind"]=="space",topics_missing
    assert topics_missing["structuredContent"]["error"]["code"]=="NOT_FOUND",topics_missing
    invalid_cursor=request("tools/call",{"name":"message.relation.list","arguments":{
        **both_args,"afterChangeSequence":-1
    }},78)
    assert invalid_cursor["structuredContent"]["error"]["code"]=="INVALID_ARGUMENT",invalid_cursor
    invalid_topic_limit=request("tools/call",{"name":"topic.list","arguments":{
        "spaceRef":r5_space,"limit":0
    }},79)
    assert invalid_topic_limit["structuredContent"]["error"]["code"]=="INVALID_ARGUMENT",invalid_topic_limit
    with open(observed_path,encoding="utf-8") as file:
        observed=json.load(file)
    observed["relationBoth"]=both_data
    observed["topicList"]=topics_data
    with open(observed_path,"w",encoding="utf-8") as file:
        json.dump(observed,file,sort_keys=True,ensure_ascii=False)
        file.write("\n")
    print("MCP_NATIVE_SOCIAL_READ_R5_PASS relations=2 self_reference_BOTH_once=true cursor_no_skip=true topic_list=1 typed_errors=4 python_oracle=ATTACHED")
    print("MCP_NATIVE_COLLAB_R5_PASS actor=1 space=1 topic=1 participation=joined-left-joined message=1 resume=1 exact_replay=2 invalid=2 conflict=2 missing=1")
    print(f"MCP_NATIVE_OUTPUT_SCHEMA_VALIDATED_PASS published={len(_published_schemas)} exercised={len(_schema_validation_hits)} tools={sorted(_schema_validation_hits)}")
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
