#!/usr/bin/env python3
import argparse
import asyncio
import datetime as dt
import json
import urllib.request
import uuid

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

N8N_URL = "http://127.0.0.1:5678/webhook/ordivon-integration-smoke-v1"
REQUEST_TYPE = "io.ordivon.integration.smoke.request.v1"
RESULT_TYPE = "io.ordivon.integration.result.v1"


def _post_n8n(event: dict) -> dict:
    req = urllib.request.Request(
        N8N_URL,
        data=json.dumps(event, separators=(",", ":")).encode(),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


@activity.defn
async def invoke_n8n(event: dict) -> dict:
    result = await asyncio.to_thread(_post_n8n, event)
    if result.get("type") != RESULT_TYPE:
        raise RuntimeError(f"unexpected integration result type: {result!r}")
    if result.get("correlationid") != event.get("id"):
        raise RuntimeError(f"integration correlation mismatch: {result!r}")
    return result


@workflow.defn
class N8nIntegrationSmokeWorkflow:
    @workflow.run
    async def run(self, event: dict) -> dict:
        result = await workflow.execute_activity(
            invoke_n8n,
            event,
            start_to_close_timeout=dt.timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        if result.get("correlationid") != event.get("id"):
            raise ValueError("workflow received mismatched integration result")
        return result


async def run(address: str) -> dict:
    client = await Client.connect(address)
    token = uuid.uuid4().hex
    task_queue = f"ordivon-n8n-smoke-{token[:12]}"
    workflow_id = f"ordivon-n8n-smoke-{token}"
    event = {
        "specversion": "1.0",
        "id": token,
        "source": "urn:ordivon:temporal-production-green-acceptance",
        "type": REQUEST_TYPE,
        "time": dt.datetime.now(dt.timezone.utc).isoformat(),
        "datacontenttype": "application/json",
        "data": {"message": "temporal-to-n8n", "workflowId": workflow_id},
    }
    async with Worker(
        client,
        task_queue=task_queue,
        workflows=[N8nIntegrationSmokeWorkflow],
        activities=[invoke_n8n],
    ):
        result = await client.execute_workflow(
            N8nIntegrationSmokeWorkflow.run,
            event,
            id=workflow_id,
            task_queue=task_queue,
            execution_timeout=dt.timedelta(minutes=2),
        )
    if result.get("correlationid") != token:
        raise RuntimeError("Temporal result correlation mismatch")
    return {"workflowId": workflow_id, "taskQueue": task_queue, "result": result}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default="127.0.0.1:17233")
    args = parser.parse_args()
    result = asyncio.run(run(args.address))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
