"""Official rmcp stdio Work accountability end-to-end on disposable Host PG18.

This is a consumer protocol test. Work and review refs below are declarations,
not verified Runtime/Artifact external effects or authenticated actor identities.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

if len(sys.argv) != 2:
    raise SystemExit("usage: mcp_engagement_stdio_smoke.py RUST_BINARY")
dsn = os.environ.get("HOST_RUST_TEST_DSN", "")
if not dsn or "127.0.0.1" not in dsn or os.environ.get("ORDIVON_HOST_V2_DSN") != dsn:
    raise SystemExit("REFUSE_NON_DISPOSABLE_R7_DATABASE")
observed_path = os.environ.get("HOST_RUST_ENGAGEMENT_OBSERVED_PATH")
if not observed_path:
    raise SystemExit("missing HOST_RUST_ENGAGEMENT_OBSERVED_PATH")

work_ref = "work:test:r7-mcp-engagement-lifecycle"
cancel_ref = "work:test:r7-mcp-engagement-cancellation"
requester = "actor:test:r7-mcp-requester"
reviewer = "actor:test:r7-mcp-reviewer"
agent_a = "actor:test:r7-mcp-worker-a"
agent_b = "actor:test:r7-mcp-worker-b"
native_names = {"work.engagement.advance", "work.engagement.list"}
counter = 0
registrations: dict[str, dict] = {}
observed: dict = {"workRef": work_ref, "revisions": {}, "receipts": {}}
proc = subprocess.Popen(
    [sys.argv[1]],
    env=os.environ.copy(),
    text=True,
    bufsize=1,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)


def request(method: str, params: dict | None = None, *, notify: bool = False) -> dict:
    global counter
    msg: dict = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        counter += 1
        msg["id"] = counter
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(msg, separators=(",", ":"), ensure_ascii=False) + "\n")
    proc.stdin.flush()
    if notify:
        return {}
    assert proc.stdout is not None
    line = proc.stdout.readline()
    if not line:
        assert proc.stderr is not None
        raise RuntimeError("R7 rust MCP terminated: " + proc.stderr.read()[-900:])
    reply = json.loads(line)
    assert reply.get("id") == counter, reply
    assert "error" not in reply, reply
    return reply["result"]


def call_tool(name: str, args: dict) -> dict:
    # The exact published native inputSchema must accept every actual command.
    # This checks actual rmcp domain Serde wiring, not a hand-maintained DTO.
    if name in native_names:
        Draft202012Validator(registrations[name]["inputSchema"]).validate(args)
    result = request("tools/call", {"name": name, "arguments": args})
    if result.get("isError") is not True:
        schema = registrations[name]["outputSchema"]
        payload = result["structuredContent"]
        assert isinstance(payload, dict), (name, result)
        Draft202012Validator(schema).validate(payload)
    return result


def ok(name: str, args: dict) -> dict:
    result = call_tool(name, args)
    assert result.get("isError") is not True, (name, result)
    return result["structuredContent"]


def rejected(name: str, args: dict, expected: str) -> dict:
    result = call_tool(name, args)
    assert result.get("isError") is True, (name, result)
    error = result["structuredContent"]["error"]
    assert error["code"] == expected, (name, error)
    assert error["retryable"] is False, error
    return error


def advance(
    rev: int, actor: str, action: dict, request_id: str, *, expected: str = "committed"
) -> dict:
    args = {
        "workRef": work_ref,
        "expectedRevision": rev,
        "actorRef": actor,
        "clientRequestId": request_id,
        "action": action,
    }
    result = ok("work.engagement.advance", args)
    assert result["admission"] == expected, result
    if expected == "committed":
        observed["receipts"][request_id] = {"request": args, "response": result}
    return result


def phase(output: dict, expected: str, rev: int, state: str = "open") -> None:
    assert output["revision"] == rev, output
    assert output["state"] == state, output
    assert output["snapshot"]["engagement"]["phase"] == expected, output


try:
    init = request(
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "host-r7-mcp-engagement", "version": "1.0.0"},
        },
    )
    assert init["serverInfo"]["name"], init
    request("notifications/initialized", notify=True)
    listed = request("tools/list", {})["tools"]
    registrations = {item["name"]: item for item in listed}
    assert len(registrations) == 32 and native_names <= registrations.keys()
    for name in native_names:
        schema = registrations[name]["outputSchema"]
        assert schema["type"] == "object" and schema["properties"]
        Draft202012Validator.check_schema(schema)
    # Schema authority is now A's actual domain Serde type via JsonSchema.
    # Match both positive variants and negative shape/enum counterexamples.
    advance_schema = Draft202012Validator(registrations["work.engagement.advance"]["inputSchema"])
    list_schema = Draft202012Validator(registrations["work.engagement.list"]["inputSchema"])
    base = {
        "workRef": work_ref,
        "expectedRevision": 1,
        "actorRef": requester,
        "clientRequestId": "request:test:schema-only",
    }
    valid_actions = [
        {"type": "offer", "consumerActorRef": reviewer, "acceptanceCriteria": ["verify"]},
        {"type": "claim"},
        {"type": "release", "reason": "returned"},
        {
            "type": "submit",
            "claimEpoch": 1,
            "deliveryRef": "delivery:test",
            "summary": "done",
            "outputRefs": ["artifact:test"],
            "evidenceRefs": ["receipt:test"],
        },
        {
            "type": "review",
            "claimEpoch": 1,
            "decision": "accepted",
            "rationale": "verified",
            "verificationRefs": ["proof:test"],
        },
        {"type": "cancel", "reason": "no longer requested"},
    ]
    for action in valid_actions:
        advance_schema.validate({**base, "action": action})
    for invalid_action in [
        {"type": "offer", "consumerActorRef": reviewer},  # missing acceptance criteria
        {
            "type": "submit",
            "claimEpoch": 1,
            "summary": "done",
            "outputRefs": ["artifact:test"],
            "evidenceRefs": ["receipt:test"],
        },
        {
            "type": "review",
            "claimEpoch": 1,
            "decision": "approved",
            "rationale": "verified",
            "verificationRefs": ["proof:test"],
        },
        {"type": "execute"},  # Runtime dispatch is NOT Host accountability
    ]:
        try:
            advance_schema.validate({**base, "action": invalid_action})
        except JsonSchemaValidationError:
            pass
        else:
            raise AssertionError(
                f"Domain-generated MCP input schema accepted invalid action: {invalid_action}"
            )
    for phase_label in (
        "offered",
        "claimed",
        "submitted",
        "returned",
        "accepted",
        "cancelled",
    ):
        list_schema.validate({"phase": phase_label})
    try:
        list_schema.validate({"phase": "executed"})
    except JsonSchemaValidationError:
        pass
    else:
        raise AssertionError("invalid phase cannot be an MCP ListEngagements filter")
    print("R10_DOMAIN_SERDE_GENERATED_MCP_INPUT_SCHEMA_PASS variants=6 invalid_actions=4 phases=6")
    print("R7_NATIVE_MCP_TYPED_EXTENSIONS_ADVERTISED_PASS count=2 source_python31=NOT_CLAIMED")

    for actor in (requester, reviewer, agent_a, agent_b):
        created = ok("actor.declare", {"actorRef": actor, "actorKind": "agent"})
        assert created["actorRef"] == actor

    def new_work(ref: str) -> dict:
        return ok(
            "work.create",
            {
                "workRef": ref,
                "workKind": "research-deliverable",
                "actorRef": requester,
                "initialSnapshot": {"objective": "可消费科研成果 🌍", "frontier": "公开接取与验收"},
            },
        )

    assert new_work(work_ref)["revision"] == 1

    offer = {
        "type": "offer",
        "consumerActorRef": reviewer,
        "acceptanceCriteria": ["由指定消费者独立核对工件与回执"],
    }
    offered = advance(1, requester, offer, "request:r7:mcp:offer")
    phase(offered, "offered", 2)
    again = advance(1, requester, offer, "request:r7:mcp:offer", expected="existing")
    phase(again, "offered", 2)
    # One identity with a different request digest MUST never overwrite receipt.
    rejected(
        "work.engagement.advance",
        {
            "workRef": work_ref,
            "expectedRevision": 2,
            "actorRef": agent_a,
            "clientRequestId": "request:r7:mcp:offer",
            "action": {"type": "claim"},
        },
        "CONFLICT",
    )
    # Existing generic WorkSnapshot cannot erase the upgraded accountability field.
    rejected(
        "work.snapshot.commit",
        {
            "workRef": work_ref,
            "expectedRevision": 2,
            "snapshot": {"objective": "old", "frontier": "erase attempted"},
            "actorRef": requester,
            "continuityDisposition": "continue",
        },
        "CONFLICT",
    )

    # Unsubscribed reviewer sees an offered Work from current Work authority,
    # with no fabricated personal subscription or event delivery.
    subs = ok("subscription.list", {"actorRef": reviewer})
    assert subs["subscriptions"] == [], subs
    inbox = ok("work.engagement.list", {"phase": "offered", "consumerActorRef": reviewer})
    assert work_ref in {x["workRef"] for x in inbox["engagements"]}, inbox

    first = advance(2, agent_a, {"type": "claim"}, "request:r7:mcp:claim-a")
    phase(first, "claimed", 3)
    assert first["snapshot"]["engagement"]["claimEpoch"] == 1
    rejected(
        "work.engagement.advance",
        {
            "workRef": work_ref,
            "expectedRevision": 2,
            "actorRef": agent_b,
            "clientRequestId": "request:r7:mcp:claim-b-stale",
            "action": {"type": "claim"},
        },
        "CONFLICT",
    )

    submit_one = {
        "type": "submit",
        "claimEpoch": 1,
        "deliveryRef": "delivery:test:r7-1",
        "summary": "科研成果与运行证据仅作为引用声明",
        "outputRefs": ["artifact:test:r7-output-1"],
        "evidenceRefs": ["receipt:test:r7-effect-1"],
    }
    for who, epoch in ((agent_a, 0), (agent_b, 1)):
        rejected(
            "work.engagement.advance",
            {
                "workRef": work_ref,
                "expectedRevision": 3,
                "actorRef": who,
                "clientRequestId": f"request:r7:mcp:wrong-submit-{who}-{epoch}",
                "action": {**submit_one, "claimEpoch": epoch},
            },
            "CONFLICT",
        )
    submitted = advance(3, agent_a, submit_one, "request:r7:mcp:submit-1")
    phase(submitted, "submitted", 4)
    in_review = ok(
        "work.engagement.list",
        {
            "phase": "submitted",
            "consumerActorRef": reviewer,
        },
    )
    assert [x["workRef"] for x in in_review["engagements"] if x["workRef"] == work_ref] == [
        work_ref
    ]
    assert (
        in_review["engagements"][0]["engagement"]["delivery"]["deliveryRef"] == "delivery:test:r7-1"
    )
    assert ok("subscription.list", {"actorRef": reviewer})["subscriptions"] == []

    rejected(
        "work.engagement.advance",
        {
            "workRef": work_ref,
            "expectedRevision": 4,
            "actorRef": agent_b,
            "clientRequestId": "request:r7:mcp:bad-consumer",
            "action": {
                "type": "review",
                "claimEpoch": 1,
                "decision": "accepted",
                "rationale": "cannot impersonate reviewer",
                "verificationRefs": ["evidence:test:r7-bad"],
            },
        },
        "CONFLICT",
    )
    returned = advance(
        4,
        reviewer,
        {
            "type": "review",
            "claimEpoch": 1,
            "decision": "returned",
            "rationale": "结果不符合先前验收条件",
            "verificationRefs": ["evidence:test:r7-rejected"],
        },
        "request:r7:mcp:return",
    )
    phase(returned, "returned", 5)
    again_claimed = advance(5, agent_b, {"type": "claim"}, "request:r7:mcp:reclaim-b")
    phase(again_claimed, "claimed", 6)
    assert again_claimed["snapshot"]["engagement"]["claimEpoch"] == 2

    rejected(
        "work.engagement.advance",
        {
            "workRef": work_ref,
            "expectedRevision": 6,
            "actorRef": agent_a,
            "clientRequestId": "request:r7:mcp:stale-agent",
            "action": submit_one,
        },
        "CONFLICT",
    )
    rejected(
        "work.engagement.advance",
        {
            "workRef": work_ref,
            "expectedRevision": 6,
            "actorRef": agent_b,
            "clientRequestId": "request:r7:mcp:duplicate-delivery",
            "action": {**submit_one, "claimEpoch": 2},
        },
        "CONFLICT",
    )
    submit_two = {
        **submit_one,
        "claimEpoch": 2,
        "deliveryRef": "delivery:test:r7-2",
        "outputRefs": ["artifact:test:r7-output-2"],
        "evidenceRefs": ["receipt:test:r7-effect-2"],
    }
    submitted_again = advance(6, agent_b, submit_two, "request:r7:mcp:submit-2")
    phase(submitted_again, "submitted", 7)
    final = advance(
        7,
        reviewer,
        {
            "type": "review",
            "claimEpoch": 2,
            "decision": "accepted",
            "rationale": "消费方确认第二版满足验收条件",
            "verificationRefs": ["evidence:test:r7-consumer-accepted"],
        },
        "request:r7:mcp:accept",
    )
    phase(final, "accepted", 8, "completed")
    assert final["snapshot"]["engagement"]["assigneeActorRef"] == agent_b
    assert final["snapshot"]["engagement"]["delivery"]["deliveryRef"] == "delivery:test:r7-2"
    assert (
        ok(
            "work.engagement.list",
            {
                "phase": "submitted",
                "consumerActorRef": reviewer,
            },
        )["engagements"]
        == []
    )
    accepted = ok(
        "work.engagement.list",
        {
            "phase": "accepted",
            "consumerActorRef": reviewer,
        },
    )
    assert work_ref in [x["workRef"] for x in accepted["engagements"]]

    for revision in range(1, 9):
        observed["revisions"][str(revision)] = ok(
            "work.get", {"workRef": work_ref, "revision": revision}
        )
    assert observed["revisions"]["4"]["state"] == "historical_state_unknown"
    assert observed["revisions"]["8"]["state"] == "completed"

    # An independent engagement can be released and cancelled through MCP.
    assert new_work(cancel_ref)["revision"] == 1

    def cancel_step(revision: int, actor: str, action: dict, request_id: str) -> dict:
        return ok(
            "work.engagement.advance",
            {
                "workRef": cancel_ref,
                "expectedRevision": revision,
                "actorRef": actor,
                "clientRequestId": request_id,
                "action": action,
            },
        )

    assert cancel_step(1, requester, offer, "request:r7:mcp:cancel-offer")["revision"] == 2
    assert (
        cancel_step(2, agent_a, {"type": "claim"}, "request:r7:mcp:cancel-claim")["revision"] == 3
    )
    assert (
        cancel_step(
            3,
            agent_a,
            {
                "type": "release",
                "reason": "任务已交还给发布者",
            },
            "request:r7:mcp:cancel-release",
        )["snapshot"]["engagement"]["phase"]
        == "offered"
    )
    cancelled = cancel_step(
        4,
        requester,
        {
            "type": "cancel",
            "reason": "需求撤销但不撤销任何真实外部副作用",
        },
        "request:r7:mcp:cancel-final",
    )
    assert cancelled["state"] == "abandoned"
    rejected("work.engagement.list", {"limit": 0}, "INVALID_ARGUMENT")
    rejected("work.engagement.list", {"beforeWorkRef": work_ref}, "INVALID_ARGUMENT")
    rejected("work.engagement.list", {"maxBytes": 100}, "INVALID_ARGUMENT")

    with open(observed_path, "w", encoding="utf-8") as stream:
        json.dump(observed, stream, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    print(
        "R7_MCP_ENGAGEMENT_STDIO_REAL_PG18_PASS offers=2 claims=3 submitted=2 returned=1 accepted=1 canceled=1 stale_and_wrong_rejected=true replay=existing=exact inbox_without_follow=true typed_success_schema=PASS"
    )
finally:
    proc.terminate()
    try:
        proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
