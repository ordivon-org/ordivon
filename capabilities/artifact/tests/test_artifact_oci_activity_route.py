"""Isolated Temporal routing witness; no production Worker authority claim."""

import asyncio
import concurrent.futures
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import pytest
from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

NATIVE_QUEUE = "artifact-r18-native-oci"
ORCHESTRATION_QUEUE = "artifact-r18-orchestration"
ACTIVITY = "artifact.r18.native-verify-probe"


@workflow.defn
class RouteWitness:
    @workflow.run
    async def run(self, intent: dict) -> dict:
        return await workflow.execute_activity(
            ACTIVITY,
            intent,
            result_type=dict,
            task_queue=NATIVE_QUEUE,
            schedule_to_close_timeout=timedelta(seconds=35),
            start_to_close_timeout=timedelta(seconds=25),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )


@pytest.mark.integration
def test_explicit_native_activity_queue_consumes_existing_operation(tmp_path):
    from artifact_operations.contract import operation_envelope
    from artifact_operations.executor import ArtifactOperationExecutor
    from artifact_operations.providers import DirectPythonOperationProvider
    from artifact_operations.receipt import operation_file_fact

    subject = tmp_path / "page.html"
    subject.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Test</title></head>'
        "<body><main><h1>Test</h1></main></body></html>"
    )
    profile = Path(__file__).resolve().parents[1] / "artifact-delivery/examples/web-r1.json"
    intent = operation_envelope(
        "r18-native-route",
        "verify",
        {"profile": operation_file_fact(profile), "artifact": operation_file_fact(subject)},
        {"webProvider": "oci"},
    )
    executor = ArtifactOperationExecutor(
        tmp_path / "state", provider=DirectPythonOperationProvider()
    )
    native_calls = []

    @activity.defn(name=ACTIVITY)
    def native_verify(value: dict) -> dict:
        native_calls.append(activity.info().task_queue)
        return executor.execute(value)

    async def run():
        async with await WorkflowEnvironment.start_local(
            dev_server_existing_path="/opt/ordivon/external/temporal-cli/1.8.3/temporal",
            dev_server_startup_timeout=timedelta(seconds=30),
            ui=False,
        ) as env:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                async with (
                    Worker(env.client, task_queue=ORCHESTRATION_QUEUE, workflows=[RouteWitness]),
                    Worker(
                        env.client,
                        task_queue=NATIVE_QUEUE,
                        activities=[native_verify],
                        activity_executor=pool,
                    ),
                ):
                    handle = await env.client.start_workflow(
                        RouteWitness.run,
                        intent,
                        id="r18-native-route",
                        task_queue=ORCHESTRATION_QUEUE,
                    )
                    result = await asyncio.wait_for(handle.result(), 45)
                    history = await handle.fetch_history()
                assert native_calls == [NATIVE_QUEUE]
                schedules = [
                    e.activity_task_scheduled_event_attributes
                    for e in history.events
                    if e.HasField("activity_task_scheduled_event_attributes")
                ]
                assert len(schedules) == 1 and schedules[0].task_queue.name == NATIVE_QUEUE
                assert result["metadata"]["profileVerificationComplete"] is False
                assert {"target", "accessibility"} <= set(result["metadata"]["gateVsas"])
                for f in result["roles"].values():
                    data = Path(f["path"]).read_bytes()
                    assert (
                        len(data) == f["size"] and hashlib.sha256(data).hexdigest() == f["sha256"]
                    )
                raw = json.loads(Path(result["roles"]["rawEvidence:target"]["path"]).read_bytes())
                assert raw["browserEvidence"]["provider"]["kind"] == "podman-oci"
                assert executor.execute(intent)["roles"] == result["roles"]
                await Replayer(workflows=[RouteWitness]).replay_workflow(history)
                print(
                    "NATIVE_QUEUE_ROUTE",
                    NATIVE_QUEUE,
                    "EVENTS",
                    len(history.events),
                    "ROLES",
                    len(result["roles"]),
                    "REPLAY_PASS",
                    "INCOMPLETE_PROFILE",
                )

    asyncio.run(run())
