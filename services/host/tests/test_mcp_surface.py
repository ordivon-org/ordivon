from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from mcp import Client

from ordivon_host_v2 import HostV2
from ordivon_host_v2.mcp_server import build_server

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def _checkpoint(task_id: str, frontier: str) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-working-checkpoint",
        "truthRole": "semantic-working-claim",
        "taskId": task_id,
        "objective": "mcp-v2 continuity",
        "frontier": frontier,
        "established": ["baseline retained"],
        "unresolved": ["next transition"],
        "rejected": [],
        "constraints": ["exact revision only"],
        "nextActions": ["continue"],
        "runtime": None,
    }



def test_official_mcp_v2_exposes_migrated_host_surface_and_runs_vertical_slice() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    task_id = f"task:v2:mcp:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert names == {
                "host.status",
                "attention.delta",
                "board.list",
                "board.search",
                "board.post",
                "task.observe",
                "task.list",
                "task.resume",
                "task.adopt",
                "task.checkpoint",
            }
            by_name = {tool.name: tool for tool in listed.tools}
            adopt_schema = by_name["task.adopt"].input_schema
            checkpoint_schema = by_name["task.checkpoint"].input_schema
            status_schema = by_name["host.status"].input_schema
            assert len(adopt_schema["properties"]["initialCheckpoint"]["oneOf"]) == 2
            assert len(checkpoint_schema["properties"]["checkpoint"]["oneOf"]) == 2
            assert {"detail", "recentLimit"} <= set(status_schema["properties"])
            for tool in listed.tools:
                assert tool.output_schema is not None
                assert tool.output_schema.get("additionalProperties") is not True

            status = await client.call_tool(
                "host.status", {"detail": "integrity", "recentLimit": 0}
            )
            assert status.is_error is False
            assert status.structured_content is not None
            assert status.structured_content["detail"] == "integrity"
            assert status.structured_content["authority"]["journalBackend"] == "postgresql"
            assert status.structured_content["interface"]["surfaceVersion"] == 9
            assert status.structured_content["interface"]["toolCount"] == 10
            assert set(status.structured_content["interface"]["toolNames"]) == names
            assert "news" not in status.structured_content
            assert status.structured_content["doctor"]["healthy"] is True

            adopted = await client.call_tool(
                "task.adopt",
                {
                    "taskId": task_id,
                    "goalId": "goal:mcp-v2",
                    "initialCheckpoint": _checkpoint(task_id, "created"),
                },
            )
            assert adopted.is_error is False
            assert adopted.structured_content is not None
            assert adopted.structured_content["task"]["revision"] == 1

            updated = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 1,
                    "checkpoint": _checkpoint(task_id, "resumable"),
                },
            )
            assert updated.is_error is False
            listed_tasks = await client.call_tool(
                "task.list", {"goalId": "goal:mcp-v2", "limit": 10}
            )
            assert listed_tasks.is_error is False
            assert listed_tasks.structured_content is not None
            assert listed_tasks.structured_content["schemaVersion"] == 4
            assert listed_tasks.structured_content["itemView"] == "basic"
            listed_task = listed_tasks.structured_content["tasks"][0]
            assert listed_task["task_id"] == task_id
            assert "checkpoint" not in listed_task

            resumed = await client.call_tool("task.resume", {"taskId": task_id})
            assert resumed.is_error is False
            assert resumed.structured_content is not None
            assert resumed.structured_content["schemaVersion"] == 4
            assert resumed.structured_content["task"]["revision"] == 2
            assert "checkpoint" not in resumed.structured_content["task"]
            assert resumed.structured_content["checkpoint"]["frontier"] == "resumable"

    asyncio.run(scenario())




def test_mcp_full_checkpoint_terminal_and_writer_replay_contract() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    task_id = f"task:v2:mcp-contract:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            adopted = await client.call_tool(
                "task.adopt",
                {
                    "taskId": task_id,
                    "goalId": "goal:mcp-v2-contract",
                    "initialCheckpoint": _checkpoint(task_id, "baseline"),
                    "writerLabel": "writer:a",
                },
            )
            assert adopted.structured_content is not None
            assert adopted.structured_content["writerLabel"] == "writer:a"

            next_checkpoint = _checkpoint(task_id, "full-proven")
            next_checkpoint["unresolved"] = []
            next_checkpoint["nextActions"] = ["terminalize"]
            updated = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 1,
                    "checkpoint": next_checkpoint,
                    "writerLabel": "writer:b",
                },
            )
            assert updated.structured_content is not None
            assert updated.structured_content["admission"] == "committed"
            assert updated.structured_content["checkpoint"]["frontier"] == "full-proven"
            assert updated.structured_content["checkpoint"]["established"] == [
                "baseline retained"
            ]
            assert updated.structured_content["checkpoint"]["constraints"] == [
                "exact revision only"
            ]
            assert updated.structured_content["writerLabel"] == "writer:b"

            replay = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 1,
                    "checkpoint": next_checkpoint,
                    "writerLabel": "writer:c",
                },
            )
            assert replay.structured_content is not None
            assert replay.structured_content["admission"] == "existing"
            assert replay.structured_content["writerLabel"] == "writer:b"

            rejected_terminal = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 2,
                    "checkpoint": {"frontier": "done"},
                    "continuityDisposition": "complete",
                },
            )
            assert rejected_terminal.is_error is True

            current = await client.call_tool(
                "task.resume", {"taskId": task_id, "expectedRevision": 2}
            )
            assert current.structured_content is not None
            terminal = dict(current.structured_content["checkpoint"])
            terminal["frontier"] = "done"
            terminal["unresolved"] = []
            terminal["nextActions"] = []
            completed = await client.call_tool(
                "task.checkpoint",
                {
                    "taskId": task_id,
                    "expectedRevision": 2,
                    "checkpoint": terminal,
                    "continuityDisposition": "complete",
                    "writerLabel": "writer:terminal",
                },
            )
            assert completed.structured_content is not None
            assert completed.structured_content["task"]["state"] == "completed"

    asyncio.run(scenario())


def test_mcp_checkpoint_rejects_task_identity_mismatch() -> None:
    assert DSN is not None
    HostV2(DSN).initialize()
    task_id = f"task:v2:mcp-mismatch:{uuid4().hex}"

    async def scenario() -> None:
        async with Client(build_server(DSN), raise_exceptions=True) as client:
            bad = _checkpoint("task:v2:wrong", "bad")
            rejected = await client.call_tool(
                "task.adopt",
                {
                    "taskId": task_id,
                    "goalId": "goal:mcp-v2-contract",
                    "initialCheckpoint": bad,
                },
            )
            assert rejected.is_error is True

    asyncio.run(scenario())
