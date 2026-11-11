"""Test-only: unauthenticated MCP client can claim consumer ActorRef in PG18.

Use the production Rust rmcp StreamableHTTP implementation and official Python
MCP SDK across three separate clients. This is not a production probe.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import socket
import subprocess
import sys

import psycopg
from mcp import Client

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.work_store import WorkStore

WORK = "work:test:r10:actor-boundary"
CREATOR = "actor:test:r10:creator"
WORKER = "actor:test:r10:worker"
CONSUMER = "actor:test:r10:consumer"
REQUEST_ID = "request:test:r10:anonymous-consumer-review"
ACTION = {
    "type": "review",
    "claimEpoch": 1,
    "decision": "accepted",
    "rationale": "caller only supplied the consumer ActorRef label",
    "verificationRefs": ["evidence:test:r10:unverified"],
}


def disposable_pg18() -> None:
    dsn = os.getenv("HOST_RUST_TEST_DSN", "")
    if (
        os.getenv("ORDIVON_TEST_DISPOSABLE_PG18") != "yes"
        or not dsn.startswith("postgresql://")
        or "@127.0.0.1:" not in dsn
        or dsn != os.getenv("ORDIVON_HOST_V2_DSN")
        or os.getenv("ORDIVON_GATEWAY_HOST_URL")
    ):
        raise RuntimeError("REFUSE_PRODUCTION_DATABASE_OR_INSTALLED_GATEWAY")
    with psycopg.connect(dsn) as conn:
        version = int(conn.execute("SHOW server_version_num").fetchone()[0])
        schema = int(
            conn.execute("SELECT schema_version FROM host_v2_schema WHERE singleton").fetchone()[0]
        )
    assert version // 10000 == 18 and schema == 13


async def call(client: Client, name: str, args: dict) -> dict:
    response = await client.call_tool(name, args)
    if response.is_error or not isinstance(response.structured_content, dict):
        raise RuntimeError(f"{name} did not succeed: {response}")
    return response.structured_content


def advance(revision: int, actor: str, action: dict, request_id: str) -> dict:
    return {
        "workRef": WORK,
        "expectedRevision": revision,
        "actorRef": actor,
        "action": action,
        "clientRequestId": request_id,
    }


async def run_clients(url: str, child: subprocess.Popen) -> bool:
    for retry in range(80):
        if child.poll() is not None:
            raise RuntimeError("Rust Host terminated during official SDK connection")
        try:
            async with Client(url) as ready:
                names = {tool.name for tool in (await ready.list_tools()).tools}
                assert {"work.engagement.advance", "work.engagement.list"} <= names
            break
        except OSError, ConnectionError, TimeoutError:
            if retry == 79:
                raise
            await asyncio.sleep(0.15)

    async with Client(url) as requester:
        for actor in (CREATOR, WORKER, CONSUMER):
            result = await call(
                requester,
                "actor.declare",
                {
                    "actorRef": actor,
                    "actorKind": "agent",
                },
            )
            assert result["actorRef"] == actor
        created = await call(
            requester,
            "work.create",
            {
                "workRef": WORK,
                "workKind": "review-provenance",
                "actorRef": CREATOR,
                "initialSnapshot": {
                    "objective": "verify that actor labels are not credentials",
                    "frontier": "the consumer identity must be independently bound",
                },
            },
        )
        assert created["revision"] == 1
        offered = await call(
            requester,
            "work.engagement.advance",
            advance(
                1,
                CREATOR,
                {
                    "type": "offer",
                    "consumerActorRef": CONSUMER,
                    "acceptanceCriteria": ["actual verified consumer must review evidence"],
                },
                "request:test:r10:offer",
            ),
        )
        assert offered["revision"] == 2

    async with Client(url) as worker:
        claim = await call(
            worker,
            "work.engagement.advance",
            advance(
                2,
                WORKER,
                {"type": "claim"},
                "request:test:r10:claim",
            ),
        )
        assert claim["revision"] == 3
        submitted = await call(
            worker,
            "work.engagement.advance",
            advance(
                3,
                WORKER,
                {
                    "type": "submit",
                    "claimEpoch": 1,
                    "deliveryRef": "delivery:test:r10:submitted",
                    "summary": "unverified reference strings",
                    "outputRefs": ["artifact:test:r10:unverified"],
                    "evidenceRefs": ["receipt:test:r10:unverified"],
                },
                "request:test:r10:submit",
            ),
        )
        assert submitted["state"] == "open" and submitted["revision"] == 4

    # Third independent client has NO credentials, delegated identity or
    # subscription: the only claim to reviewer identity is an ordinary string.
    async with Client(url) as anonymous_client:
        found = await call(
            anonymous_client,
            "work.engagement.list",
            {
                "phase": "submitted",
                "consumerActorRef": CONSUMER,
            },
        )
        assert WORK in {item["workRef"] for item in found["engagements"]}
        result = await anonymous_client.call_tool(
            "work.engagement.advance",
            advance(4, CONSUMER, ACTION, REQUEST_ID),
        )
        if result.is_error:
            return False
        response = result.structured_content
        assert isinstance(response, dict)
        assert response["revision"] == 5 and response["state"] == "completed"
        assert response["snapshot"]["engagement"]["phase"] == "accepted"
        return True


def verify_python_authority(accepted: bool) -> None:
    dsn = os.environ["HOST_RUST_TEST_DSN"]
    work = WorkStore(dsn).get_work(WORK)
    assert work["snapshotDigest"] == canonical_digest(work["snapshot"])
    if not accepted:
        assert work["revision"] == 4 and work["state"] == "open"
        return
    assert work["revision"] == 5 and work["state"] == "completed"
    with psycopg.connect(dsn) as conn:
        receipt = conn.execute(
            "SELECT operation,request_digest,response FROM command_receipts "
            "WHERE client_request_id=%s",
            (REQUEST_ID,),
        ).fetchone()
    assert receipt is not None
    operation, request_digest, response = receipt
    assert operation == "work.engagement.advance"
    assert request_digest == canonical_digest(
        {
            "operation": "work.engagement.advance",
            "workRef": WORK,
            "expectedRevision": 4,
            "actorRef": CONSUMER,
            "action": ACTION,
        }
    )
    assert response["snapshot"]["engagement"]["phase"] == "accepted"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("host_binary")
    parser.add_argument("--require-verified-principal", action="store_true")
    args = parser.parse_args()
    disposable_pg18()
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
    env = dict(os.environ)
    env.update(
        ORDIVON_HOST_V2_TRANSPORT="streamable-http",
        ORDIVON_HOST_V2_HOST="127.0.0.1",
        ORDIVON_HOST_V2_PORT=str(port),
        ORDIVON_HOST_V2_PATH="/mcp",
    )
    host = subprocess.Popen(
        [args.host_binary],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        accepted = asyncio.run(run_clients(f"http://127.0.0.1:{port}/mcp", host))
        verify_python_authority(accepted)
        print(
            "R10_ACTORREF_BOUNDARY_PROBE "
            f"anonymous_client_review={'COMMITTED' if accepted else 'DENIED'} "
            "official_sdk=true distinct_sessions=3 original_pg18_receipt=CHECKED "
            "installed_gateway=UNTESTED production=UNTOUCHED",
            flush=True,
        )
        if args.require_verified_principal:
            # A negative-only observation is insufficient to prove real
            # authenticated principal binding and positive authorization.
            print(
                "R10_RELEASE_NOT_QUALIFIED: verified principal positive/negative "
                "consumer attestation absent",
                file=sys.stderr,
            )
            return 4
        return 0
    finally:
        host.terminate()
        try:
            host.wait(timeout=5)
        except subprocess.TimeoutExpired:
            host.kill()
            host.wait()


if __name__ == "__main__":
    sys.exit(main())
