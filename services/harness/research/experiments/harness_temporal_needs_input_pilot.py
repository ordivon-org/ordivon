#!/usr/bin/env python3
"""Migration-only Temporal pilot for Harness NEEDS_INPUT wait/wake ownership.

Temporal owns only durable waiting and caller-wake admission here. Harness remains the owner of
snapshot/cognition state, provider-call evidence, trace segments, and terminal result semantics.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import timedelta
import json
from pathlib import Path
import tempfile

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

SEGMENT_ACTIVITY = "migration.harness.needs-input.segment"
PILOT_WORKFLOW = "migration.harness.needs-input"
WAKE_UPDATE = "submit-caller-input"
STATE_QUERY = "interaction-state"


@dataclass(frozen=True)
class PilotInput:
    state_root: str
    driver: str
    harness_python: str
    harness_source_root: str


@dataclass(frozen=True)
class WakeInput:
    request_id: str
    messages: tuple[dict, ...]


@dataclass(frozen=True)
class SegmentInput:
    pilot: PilotInput
    phase: str
    messages: tuple[dict, ...] = ()


@activity.defn(name=SEGMENT_ACTIVITY)
async def run_harness_segment(value: SegmentInput) -> dict:
    args = [
        "/usr/bin/env",
        f"PYTHONPATH={value.pilot.harness_source_root}:{value.pilot.harness_source_root}/src",
        value.pilot.harness_python,
        value.pilot.driver,
        "--state-root",
        value.pilot.state_root,
        "--phase",
        value.phase,
    ]
    if value.phase == "resume":
        args += ["--messages-json", json.dumps(list(value.messages), separators=(",", ":"))]
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(
            "Harness segment failed: " + stderr.decode("utf-8", errors="replace")[-4000:]
        )
    lines = stdout.decode("utf-8").strip().splitlines()
    if not lines:
        raise RuntimeError("Harness segment returned no JSON result")
    result = json.loads(lines[-1])
    if not isinstance(result, dict):
        raise RuntimeError("Harness segment result is not one JSON object")
    return result


RETRY = RetryPolicy(
    initial_interval=timedelta(milliseconds=100),
    maximum_interval=timedelta(seconds=1),
    maximum_attempts=3,
)


@workflow.defn(name=PILOT_WORKFLOW)
class HarnessNeedsInputWorkflow:
    def __init__(self) -> None:
        self.waiting = False
        self.pending: WakeInput | None = None
        self.wake_accept_count = 0
        self.snapshot_digest: str | None = None

    @workflow.run
    async def run(self, value: PilotInput) -> dict:
        first = await workflow.execute_activity(
            SEGMENT_ACTIVITY,
            SegmentInput(value, "start"),
            result_type=dict,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RETRY,
        )
        if first.get("status") != "paused" or first.get("stopCode") != "needs_input":
            return {"first": first, "final": first, "wakeAcceptCount": 0}
        self.snapshot_digest = first.get("snapshotDigest")
        self.waiting = True
        await workflow.wait_condition(lambda: self.pending is not None)
        wake = self.pending
        assert wake is not None
        self.pending = None
        self.waiting = False
        final = await workflow.execute_activity(
            SEGMENT_ACTIVITY,
            SegmentInput(value, "resume", wake.messages),
            result_type=dict,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RETRY,
        )
        return {
            "first": first,
            "final": final,
            "wakeAcceptCount": self.wake_accept_count,
            "acceptedWakeRequestId": wake.request_id,
        }

    @workflow.update(name=WAKE_UPDATE)
    def submit_caller_input(self, value: WakeInput) -> dict:
        self.pending = value
        self.wake_accept_count += 1
        return {
            "accepted": True,
            "requestId": value.request_id,
            "snapshotDigest": self.snapshot_digest,
        }

    @submit_caller_input.validator
    def validate_submit_caller_input(self, value: WakeInput) -> None:
        if not self.waiting or self.pending is not None:
            raise ValueError("Harness workflow is not waiting for caller input")
        if not value.request_id or value.request_id != value.request_id.strip():
            raise ValueError("wake request ID is invalid")
        if not value.messages:
            raise ValueError("wake requires at least one caller message")
        for message in value.messages:
            if (
                set(message) != {"role", "content"}
                or message.get("role") != "user"
                or not isinstance(message.get("content"), str)
                or not message["content"]
            ):
                raise ValueError("wake accepts only non-empty plain user messages")

    @workflow.query(name=STATE_QUERY)
    def interaction_state(self) -> dict:
        return {
            "waiting": self.waiting,
            "pending": self.pending is not None,
            "wakeAcceptCount": self.wake_accept_count,
            "snapshotDigest": self.snapshot_digest,
        }


async def execute(args) -> dict:
    client = await Client.connect(args.address, namespace=args.namespace)
    task_queue = f"harness-needs-input-pilot-{args.suffix}"
    state_root = Path(tempfile.mkdtemp(prefix="harness-temporal-needs-input-"))
    pilot = PilotInput(
        state_root=str(state_root),
        driver=str(Path(args.driver).resolve()),
        harness_python=str(Path(args.harness_python).expanduser().absolute()),
        harness_source_root=str(Path(args.harness_source_root).resolve()),
    )
    async with Worker(
        client,
        task_queue=task_queue,
        workflows=[HarnessNeedsInputWorkflow],
        activities=[run_harness_segment],
    ):
        handle = await client.start_workflow(
            HarnessNeedsInputWorkflow.run,
            pilot,
            id=f"harness-needs-input-pilot-{args.suffix}",
            task_queue=task_queue,
        )
        for _ in range(200):
            state = await handle.query(STATE_QUERY, result_type=dict)
            if state.get("waiting"):
                break
            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("Temporal workflow never reached NEEDS_INPUT wait")

        wake = WakeInput(
            request_id=f"wake:{args.suffix}:1",
            messages=({"role": "user", "content": "the bounded answer is yes"},),
        )
        first_ack = await handle.execute_update(WAKE_UPDATE, wake, id=wake.request_id, result_type=dict)
        duplicate_ack = await handle.execute_update(WAKE_UPDATE, wake, id=wake.request_id, result_type=dict)
        result = await handle.result()

    if first_ack != duplicate_ack:
        raise RuntimeError("same Temporal Update ID did not replay the same admission result")
    if result.get("wakeAcceptCount") != 1:
        raise RuntimeError("same Temporal Update ID executed the wake handler more than once")
    first = result.get("first", {})
    final = result.get("final", {})
    if first.get("status") != "paused" or first.get("pauseReason") != "needs-input":
        raise RuntimeError("Harness first segment did not preserve NEEDS_INPUT snapshot")
    if final.get("status") != "completed" or final.get("traceSegments") != 2:
        raise RuntimeError("Harness resume did not preserve two-segment terminal history")
    if final.get("providerDispatches") != 2:
        raise RuntimeError("pilot expected one scripted provider dispatch per Harness segment")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.harness-temporal-needs-input-pilot",
        "workflowId": handle.id,
        "taskQueue": task_queue,
        "firstAck": first_ack,
        "duplicateAck": duplicate_ack,
        "result": result,
        "standing": "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default="127.0.0.1:7233")
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--suffix", required=True)
    parser.add_argument("--driver", required=True)
    parser.add_argument("--harness-python", default="/root/projects/ordivon/services/harness/.venv/bin/python")
    parser.add_argument("--harness-source-root", required=True)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(execute(args)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
