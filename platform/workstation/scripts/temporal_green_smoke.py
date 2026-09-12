#!/usr/bin/env python3
"""Execute one real Workflow against the production-green Temporal cluster."""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

WORKFLOW_NAME = "ordivon.operations.green-smoke"


@workflow.defn(name=WORKFLOW_NAME)
class GreenSmokeWorkflow:
    @workflow.run
    async def run(self, value: str) -> dict[str, str]:
        return {"input": value, "standing": "PASS", "workflowId": workflow.info().workflow_id}


async def amain(address: str, namespace: str) -> None:
    client = await Client.connect(address, namespace=namespace)
    workflow_id = f"operations-green-smoke-{uuid.uuid4()}"
    task_queue = f"operations-green-smoke-{uuid.uuid4()}"
    async with Worker(client, task_queue=task_queue, workflows=[GreenSmokeWorkflow]):
        result = await client.execute_workflow(
            GreenSmokeWorkflow.run,
            "green-cluster",
            id=workflow_id,
            task_queue=task_queue,
        )
    if result != {"input": "green-cluster", "standing": "PASS", "workflowId": workflow_id}:
        raise RuntimeError(f"unexpected Workflow result: {result!r}")
    handle = client.get_workflow_handle(workflow_id)
    description = await handle.describe()
    print(json.dumps({
        "schemaVersion": 1,
        "kind": "ordivon.operations.temporal-green-smoke",
        "workflowId": workflow_id,
        "workflowType": WORKFLOW_NAME,
        "taskQueue": task_queue,
        "result": result,
        "status": str(description.status.name),
        "runId": description.run_id,
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
