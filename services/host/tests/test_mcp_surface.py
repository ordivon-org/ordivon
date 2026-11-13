from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import psycopg
import pytest
from mcp import Client
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ordivon_host_v2 import HostV2
from ordivon_host_v2.mcp_server import build_server

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def snapshot(frontier: str) -> dict[str, object]:
    return {
        "objective": "prove Social Work Fabric northbound vertical",
        "frontier": frontier,
        "established": [],
        "unresolved": [],
        "rejected": [],
        "constraints": ["owner boundaries preserved"],
        "nextActions": [],
        "referenceRefs": [],
    }


def test_official_mcp_exposes_social_work_surface_and_runs_vertical_slice() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    token = uuid4().hex
    actor_a = f"actor:agent:mcp-a:{token}"
    actor_b = f"actor:agent:mcp-b:{token}"
    work_ref = f"work:mcp:{token}"
    space_ref = f"space:mcp:{token}"
    topic_ref = f"topic:mcp:{token}"
    message_ref = f"message:mcp:{token}"

    async def call(client: Client, name: str, arguments: dict[str, object]) -> dict[str, object]:
        result = await client.call_tool(name, arguments)
        assert result.is_error is False, (name, result)
        assert result.structured_content is not None
        return result.structured_content

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert "task.resume" not in names
            assert "board.post" not in names

            for actor in (actor_a, actor_b):
                created = await call(
                    client, "actor.declare", {"actorRef": actor, "actorKind": "agent"}
                )
                assert created["actorRef"] == actor

            created_work = await call(
                client,
                "work.create",
                {
                    "workRef": work_ref,
                    "workKind": "investigation",
                    "actorRef": actor_a,
                    "initialSnapshot": snapshot("r1"),
                },
            )
            assert created_work["revision"] == 1
            work_inventory = await call(client, "work.list", {"state": "open", "limit": 20})
            assert any(row["workRef"] == work_ref for row in work_inventory["works"])
            assert work_inventory["rankingApplied"] is False

            await call(
                client,
                "space.create",
                {
                    "spaceRef": space_ref,
                    "purpose": "cross-agent collaboration",
                    "actorRef": actor_a,
                    "subjectRefs": [work_ref],
                },
            )
            for actor in (actor_a, actor_b):
                joined = await call(
                    client,
                    "space.participation.set",
                    {"spaceRef": space_ref, "actorRef": actor, "standing": "joined"},
                )
                assert joined["standing"] == "joined"

            spaces = await call(
                client, "space.list", {"actorRef": actor_a, "subjectRef": work_ref, "limit": 20}
            )
            assert [row["spaceRef"] for row in spaces["spaces"]] == [space_ref]
            assert spaces["rankingApplied"] is False

            await call(
                client,
                "topic.create",
                {
                    "topicRef": topic_ref,
                    "spaceRef": space_ref,
                    "title": "matching",
                    "actorRef": actor_a,
                },
            )
            await call(
                client,
                "subscription.follow",
                {"actorRef": actor_a, "targetKind": "topic", "targetRef": topic_ref},
            )
            subscriptions = await call(
                client, "subscription.list", {"actorRef": actor_a, "targetKind": "topic"}
            )
            assert [row["targetRef"] for row in subscriptions["subscriptions"]] == [topic_ref]
            assert subscriptions["rankingApplied"] is False
            baseline = await call(
                client, "attention.delta", {"actorRef": actor_a, "afterSequence": 0, "limit": 500}
            )
            high = int(baseline["snapshotHighSequence"])

            posted = await call(
                client,
                "message.post",
                {
                    "messageRef": message_ref,
                    "spaceRef": space_ref,
                    "topicRef": topic_ref,
                    "authorActorRef": actor_b,
                    "body": "please inspect",
                    "recordedAtMs": 1,
                    "messageKind": "finding",
                },
            )
            assert posted["messageRef"] == message_ref
            exact = await call(
                client,
                "message.get",
                {"messageRef": message_ref, "expectedDigest": posted["messageDigest"]},
            )
            assert exact["messageRef"] == message_ref
            assert exact["messageDigest"] == posted["messageDigest"]
            assert exact["body"] == "please inspect"
            search = await call(
                client,
                "message.search",
                {"query": "inspect", "spaceRef": space_ref, "topicRef": topic_ref, "limit": 20},
            )
            assert [row["messageRef"] for row in search["messages"]] == [message_ref]
            assert search["rankingApplied"] is False
            assert search["ordering"] == "sequence_desc"
            await call(
                client,
                "message.relation.add",
                {
                    "sourceMessageRef": message_ref,
                    "relation": "mentions",
                    "targetRef": actor_a,
                    "actorRef": actor_b,
                },
            )
            delta = await call(
                client,
                "attention.delta",
                {"actorRef": actor_a, "afterSequence": high, "limit": 100},
            )
            kinds = {row["eventKind"] for row in delta["events"]}
            assert {"message", "message_relation"} <= kinds
            assert delta["rankingApplied"] is False

            updated = await call(
                client,
                "work.snapshot.commit",
                {
                    "workRef": work_ref,
                    "expectedRevision": 1,
                    "snapshot": snapshot("r2"),
                    "actorRef": actor_a,
                },
            )
            assert updated["revision"] == 2
            current = await call(client, "work.get", {"workRef": work_ref})
            assert current["snapshot"]["frontier"] == "r2"

            status = await call(client, "host.status", {"detail": "integrity"})
            assert status["schemaVersion"] == 3
            assert status["authority"]["journalSchema"] == 13
            assert status["doctor"]["healthy"] is True
            assert "board" not in status

    asyncio.run(scenario())


def test_integrity_allows_pruned_noncurrent_history_with_sound_current_work() -> None:
    """A disposable PG consumer proves current Work health despite optional history pruning.

    Preserve the exact test row for cleanup; this tests MCP not just the Store.
    """
    assert DSN is not None
    token = uuid4().hex
    actor_ref = f"actor:agent:mcp-integrity:{token}"
    work_ref = f"work:mcp-integrity:{token}"

    async def call(client: Client, tool: str, args: dict[str, object]) -> dict[str, object]:
        result = await client.call_tool(tool, args)
        assert not result.is_error, (tool, result)
        assert result.structured_content is not None
        return result.structured_content

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            await call(
                client,
                "actor.declare",
                {"actorRef": actor_ref, "actorKind": "agent"},
            )
            await call(
                client,
                "work.create",
                {
                    "workRef": work_ref,
                    "workKind": "integrity-regression",
                    "actorRef": actor_ref,
                    "initialSnapshot": snapshot("r1"),
                },
            )
            for revision in (1, 2):
                await call(
                    client,
                    "work.snapshot.commit",
                    {
                        "workRef": work_ref,
                        "expectedRevision": revision,
                        "snapshot": snapshot(f"r{revision + 1}"),
                        "actorRef": actor_ref,
                    },
                )

            before = await call(client, "host.status", {"detail": "integrity"})
            assert before["doctor"]["healthy"] is True

            # Separate committed transaction: a real Host connection must see
            # the missing row, rather than an uncommitted test-only illusion.
            with psycopg.connect(DSN, row_factory=dict_row) as conn:
                prior = conn.execute(
                    "SELECT work_ref,revision,snapshot_digest,payload,"
                    "writer_actor_ref,created_at,change_sequence "
                    "FROM work_snapshots WHERE work_ref=%s AND revision=2",
                    (work_ref,),
                ).fetchone()
                assert prior is not None
                conn.execute(
                    "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=2",
                    (work_ref,),
                )

            try:
                integrity = await call(client, "host.status", {"detail": "integrity"})
                checks = {item["name"]: item for item in integrity["doctor"]["checks"]}
                assert integrity["doctor"]["healthy"] is True
                assert "work.snapshot_history_contiguous" not in checks
                assert checks["work.current_snapshot"]["status"] == "ok"
                assert checks["work.current_snapshot_payload_digest"]["status"] == "ok"
                assert "work.snapshot_history_digest" not in checks
                history = await call(client, "host.status", {"detail": "history"})
                history_checks = {item["name"]: item for item in history["doctor"]["checks"]}
                assert history["doctor"]["healthy"] is True
                assert "work.snapshot_history_contiguous" not in history_checks
                assert history_checks["work.snapshot_history_digest"]["status"] == "ok"
                summary = await call(client, "host.status", {"detail": "summary"})
                assert summary["doctor"] is None
            finally:
                with psycopg.connect(DSN) as conn:
                    conn.execute(
                        "INSERT INTO work_snapshots("
                        "work_ref,revision,snapshot_digest,payload,writer_actor_ref,"
                        "created_at,change_sequence) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (
                            prior["work_ref"],
                            prior["revision"],
                            prior["snapshot_digest"],
                            Jsonb(prior["payload"]),
                            prior["writer_actor_ref"],
                            prior["created_at"],
                            prior["change_sequence"],
                        ),
                    )
            after = await call(client, "host.status", {"detail": "integrity"})
            assert after["doctor"]["healthy"] is True

    asyncio.run(scenario())
