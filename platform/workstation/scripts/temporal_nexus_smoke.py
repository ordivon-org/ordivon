#!/usr/bin/env python3
"""Real workflow-backed Temporal Nexus smoke proof for the production cluster."""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from datetime import timedelta

import nexusrpc
from temporalio import nexus, workflow
from temporalio.client import Client
from temporalio.worker import Worker

ENDPOINT = "ordivon-operations-nexus-smoke"
TASK_QUEUE = "ordivon-operations-nexus-smoke"


@nexusrpc.service(name="ordivon.operations.nexus-smoke")
class SmokeService:
    echo: nexusrpc.Operation[str, str]


@workflow.defn(name="ordivon.operations.nexus-smoke-target")
class SmokeTargetWorkflow:
    @workflow.run
    async def run(self, value: str) -> str:
        return "handled:" + value


@nexusrpc.handler.service_handler(service=SmokeService)
class SmokeServiceHandler:
    @nexus.workflow_run_operation
    async def echo(
        self,
        ctx: nexus.WorkflowRunOperationContext,
        input: str,
    ) -> nexus.WorkflowHandle[str]:
        return await ctx.start_workflow(
            SmokeTargetWorkflow.run,
            input,
            id=f"nexus-smoke-target-{input}",
            task_queue=TASK_QUEUE,
        )


@workflow.defn(name="ordivon.operations.nexus-smoke-caller")
class SmokeCallerWorkflow:
    @workflow.run
    async def run(self, value: str) -> str:
        client = workflow.create_nexus_client(service=SmokeService, endpoint=ENDPOINT)
        return await client.execute_operation(
            SmokeService.echo,
            value,
            schedule_to_close_timeout=timedelta(seconds=30),
        )


async def amain(address: str, namespace: str) -> None:
    client = await Client.connect(address, namespace=namespace)
    token = str(uuid.uuid4())
    caller_id = f"nexus-smoke-caller-{token}"
    expected = f"handled:{token}"
    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SmokeTargetWorkflow, SmokeCallerWorkflow],
        nexus_service_handlers=[SmokeServiceHandler()],
    ):
        result = await client.execute_workflow(
            SmokeCallerWorkflow.run,
            token,
            id=caller_id,
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(seconds=45),
        )
    if result != expected:
        raise RuntimeError(f"unexpected Nexus result: {result!r}")
    description = await client.get_workflow_handle(caller_id).describe()
    print(json.dumps({
        "schemaVersion": 1,
        "kind": "ordivon.operations.temporal-nexus-smoke",
        "standing": "PASS",
        "endpoint": ENDPOINT,
        "service": "ordivon.operations.nexus-smoke",
        "operation": "echo",
        "callerWorkflowId": caller_id,
        "callerRunId": description.run_id,
        "callerStatus": description.status.name,
        "result": result,
    }, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default="127.0.0.1:17233")
    parser.add_argument("--namespace", default="default")
    args = parser.parse_args()
    asyncio.run(amain(args.address, args.namespace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
