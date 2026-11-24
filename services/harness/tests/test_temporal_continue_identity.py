"""Continuation identity is a durable input contract, not just a workflow ID."""

from __future__ import annotations

import ast
import asyncio
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@dataclass(frozen=True)
class AgentContinueInput:
    spec_path: str = "/durable/spec.json"
    agent_id: str = "A01"
    turn_request_id: str = "turn"
    prompt: str = "original"
    campaign_ref: str = "campaign"


class AlreadyStarted(Exception):
    run_id = "run-1"


class Status(Enum):
    FAILED = 1
    COMPLETED = 2


def launcher():
    path = Path(__file__).resolve().parents[1] / "scripts/temporal_agent_automation_launch.py"
    tree = ast.parse(path.read_text())
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "_require_existing_continue_input",
            "_admit_workflow",
            "_admit_failed_continue_retry",
        }
    ]
    # Execute actual functions without importing the CLI or needing Temporal
    # in the ordinary Harness test environment.
    ns = {
        "Client": object,
        "AgentContinueInput": AgentContinueInput,
        "asdict": asdict,
        "WorkflowIDReusePolicy": SimpleNamespace(REJECT_DUPLICATE=1, ALLOW_DUPLICATE_FAILED_ONLY=2),
        "WorkflowIDConflictPolicy": SimpleNamespace(USE_EXISTING=1, FAIL=2),
        "WorkflowExecutionStatus": Status,
        "WorkflowAlreadyStartedError": AlreadyStarted,
        "AGENT_CONTINUE_WORKFLOW": "continue",
    }
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), ns)
    return ns


class FakeClient:
    def __init__(self, original=AgentContinueInput(), status=Status.FAILED):
        self.original = original
        self.status = status
        self.start_workflow = AsyncMock(side_effect=AlreadyStarted())
        self.data_converter = SimpleNamespace(decode=AsyncMock(return_value=[asdict(original)]))
        self.history_reads = []

    def get_workflow_handle(self, workflow_id, *, run_id=None):
        async def events(**kwargs):
            self.history_reads.append((workflow_id, run_id))
            yield SimpleNamespace(
                event_id=1,
                HasField=lambda name: name == "workflow_execution_started_event_attributes",
                workflow_execution_started_event_attributes=SimpleNamespace(
                    workflow_type=SimpleNamespace(name="continue"),
                    input=SimpleNamespace(payloads=[object()]),
                ),
            )

        return SimpleNamespace(
            describe=AsyncMock(return_value=SimpleNamespace(status=self.status, run_id="run-1")),
            fetch_history_events=events,
        )


@pytest.mark.parametrize(
    "changes",
    [{"prompt": "other"}, {"agent_id": "A02"}, {"campaign_ref": "other"}, {"spec_path": "/other"}],
)
def test_existing_id_does_not_prove_equal_continuation(changes):
    ns = launcher()
    client = FakeClient()
    requested = AgentContinueInput(**changes)
    with pytest.raises(ValueError, match="identity"):
        asyncio.run(
            ns["_admit_workflow"](client, "continue", requested, workflow_id="turn", task_queue="q")
        )
    assert client.history_reads == [("turn", "run-1")]


def test_exact_existing_run_is_replay_not_new_admission():
    ns = launcher()
    client = FakeClient()
    value = asyncio.run(
        ns["_admit_workflow"](
            client, "continue", AgentContinueInput(), workflow_id="turn", task_queue="q"
        )
    )
    assert value == {"workflowId": "turn", "disposition": "existing", "runId": "run-1"}
    assert client.history_reads == [("turn", "run-1")]
    assert client.start_workflow.call_args.kwargs["id_conflict_policy"] == 2


def test_failed_retry_cannot_rebind_input_before_effect_claim():
    ns = launcher()
    client = FakeClient()
    with pytest.raises(ValueError, match="identity"):
        asyncio.run(
            ns["_admit_failed_continue_retry"](
                client,
                AgentContinueInput(prompt="changed"),
                logical_workflow_id="turn",
                task_queue="q",
            )
        )
    client.start_workflow.assert_not_called()
