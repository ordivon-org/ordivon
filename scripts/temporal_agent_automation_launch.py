#!/usr/bin/env python3
"""Start one deterministic Temporal Agent Automation workflow from an existing campaign spec."""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from pathlib import Path

from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.common import WorkflowIDReusePolicy, WorkflowIDConflictPolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from campaign_materialization import CampaignLaunchSpec, compile_campaign
from standard_identifiers import require_uuid7
from temporal_agent_automation import (
    OCCURRENCE_MATERIALIZE_WORKFLOW,
    AGENT_RECONCILE_WORKFLOW,
    AGENT_HUMAN_RESUME_WORKFLOW,
    AGENT_CONTINUE_WORKFLOW,
    OccurrenceInput,
    AgentContinueInput,
)


def _materialization_for(spec: CampaignLaunchSpec, agent_id: str):
    rows = [row for row in compile_campaign(spec) if row.agent_id == agent_id]
    if len(rows) != 1:
        raise ValueError("agentId does not identify exactly one occurrence")
    return rows[0]


async def _admit_workflow(
    client: Client, workflow, value, *, workflow_id: str, task_queue: str
) -> dict[str, str]:
    try:
        handle = await client.start_workflow(
            workflow,
            value,
            id=workflow_id,
            task_queue=task_queue,
            id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
        )
    except WorkflowAlreadyStartedError as error:
        # REJECT_DUPLICATE intentionally prevents a completed deterministic effect identity
        # from being started again. That server-side rejection is positive replay evidence,
        # not an ambiguous admission failure: the exact Workflow ID already exists and no
        # provider effect was dispatched by this call. Preserve the original Run ID when
        # Temporal supplies it so acceptance can prove that replay did not mint a new run.
        result = {"workflowId": workflow_id, "disposition": "existing"}
        if error.run_id:
            result["runId"] = error.run_id
        return result
    # USE_EXISTING covers an exact identity that is still running; either way this call has
    # successfully converged on the requested deterministic Workflow identity.
    return {"workflowId": handle.id, "disposition": "admitted"}


async def _admit_failed_continue_retry(
    client: Client, value: AgentContinueInput, *, logical_workflow_id: str, task_queue: str
) -> dict[str, str]:
    prior = await client.get_workflow_handle(logical_workflow_id).describe()
    if prior.status != WorkflowExecutionStatus.FAILED:
        return {
            "workflowId": logical_workflow_id,
            "disposition": "existing",
            "retryStanding": f"not-admitted-prior-{prior.status.name.lower()}",
            "priorRunId": prior.run_id,
        }
    retry_id = str(uuid.uuid7())
    admission = await _admit_workflow(
        client,
        AGENT_CONTINUE_WORKFLOW,
        value,
        workflow_id=retry_id,
        task_queue=task_queue,
    )
    return {
        **admission,
        "retryStanding": "admitted-after-failed",
        "retryId": retry_id,
        "logicalWorkflowId": logical_workflow_id,
        "priorRunId": prior.run_id,
    }


async def run(a) -> None:
    raw = json.loads(a.spec.read_text(encoding="utf-8"))
    spec = CampaignLaunchSpec.from_dict(raw)
    client = await Client.connect(a.address, namespace=a.namespace)

    if a.operation == "campaign-materialize":
        if a.agent_id or a.prompt_file or a.turn_request_id or a.resume_id:
            raise ValueError("campaign-materialize does not accept agent/turn/resume arguments")
        materializations = compile_campaign(spec)
        # Workflow admissions are independent durable Temporal identities. Admit them concurrently
        # so controller latency scales with the slowest Temporal RPC rather than roster length.
        # asyncio.gather preserves input order, while each workflow still carries the exact stable
        # effectId with REJECT_DUPLICATE/USE_EXISTING semantics owned by Temporal.
        results = await asyncio.gather(
            *(
                _admit_workflow(
                    client,
                    OCCURRENCE_MATERIALIZE_WORKFLOW,
                    OccurrenceInput(spec_path=str(a.spec.resolve()), agent_id=materialization.agent_id),
                    workflow_id=materialization.effect_id,
                    task_queue=a.task_queue,
                )
                for materialization in materializations
            )
        )
        admissions = [
            {
                "agentId": materialization.agent_id,
                "effectId": materialization.effect_id,
                "workflowId": result["workflowId"],
                "workflowType": OCCURRENCE_MATERIALIZE_WORKFLOW,
                "disposition": result["disposition"],
                **({"runId": result["runId"]} if "runId" in result else {}),
            }
            for materialization, result in zip(materializations, results, strict=True)
        ]
        out = {
            "kind": "temporal-materialization-admissions",
            "campaignId": spec.campaign_id,
            "requested": len(admissions),
            "admitted": len(admissions),
            "workflows": admissions,
        }
    elif a.operation == "materialize":
        if not a.agent_id or a.prompt_file or a.turn_request_id or a.resume_id:
            raise ValueError("materialize requires exactly --agent-id")
        materialization = _materialization_for(spec, a.agent_id)
        workflow_id = materialization.effect_id
        admission = await _admit_workflow(
            client,
            OCCURRENCE_MATERIALIZE_WORKFLOW,
            OccurrenceInput(spec_path=str(a.spec.resolve()), agent_id=a.agent_id),
            workflow_id=workflow_id,
            task_queue=a.task_queue,
        )
        out = {
            **admission,
            "workflowType": OCCURRENCE_MATERIALIZE_WORKFLOW,
            "campaignId": spec.campaign_id,
            "agentId": a.agent_id,
            "effectId": materialization.effect_id,
        }
    elif a.operation == "pre-effect-retry":
        if not a.agent_id or a.prompt_file or a.turn_request_id or a.resume_id:
            raise ValueError("pre-effect-retry requires exactly --agent-id")
        materialization = _materialization_for(spec, a.agent_id)
        retry_id = str(uuid.uuid7())
        admission = await _admit_workflow(
            client,
            OCCURRENCE_MATERIALIZE_WORKFLOW,
            OccurrenceInput(spec_path=str(a.spec.resolve()), agent_id=a.agent_id),
            workflow_id=retry_id,
            task_queue=a.task_queue,
        )
        out = {
            **admission,
            "workflowType": OCCURRENCE_MATERIALIZE_WORKFLOW,
            "campaignId": spec.campaign_id,
            "agentId": a.agent_id,
            "effectId": materialization.effect_id,
            "retryId": retry_id,
        }
    elif a.operation == "reconcile":
        if not a.agent_id or a.prompt_file or a.turn_request_id or a.resume_id:
            raise ValueError("reconcile requires exactly --agent-id")
        materialization = _materialization_for(spec, a.agent_id)
        # Reconciliation is a repeatable observation of one existing materialization effect, not a new effect.
        # Each observation gets a generic UUIDv7 execution identity while the compiled effect digest remains
        # the stable provider-effect identity being observed.
        observation_id = str(uuid.uuid7())
        workflow_id = observation_id
        admission = await _admit_workflow(
            client,
            AGENT_RECONCILE_WORKFLOW,
            OccurrenceInput(spec_path=str(a.spec.resolve()), agent_id=a.agent_id),
            workflow_id=workflow_id,
            task_queue=a.task_queue,
        )
        out = {
            **admission,
            "workflowType": AGENT_RECONCILE_WORKFLOW,
            "campaignId": spec.campaign_id,
            "agentId": a.agent_id,
            "effectId": materialization.effect_id,
            "observationId": observation_id,
        }
    elif a.operation == "human-resume":
        if not a.agent_id or a.prompt_file or a.turn_request_id or not a.resume_id:
            raise ValueError("human-resume requires --agent-id and --resume-id")
        materialization = _materialization_for(spec, a.agent_id)
        resume_id = a.resume_id
        if not (
            resume_id.startswith("sha256:")
            and len(resume_id) == 71
            and all(ch in "0123456789abcdef" for ch in resume_id[7:])
        ):
            raise ValueError("resumeId must be one full SHA-256 digest")
        admission = await _admit_workflow(
            client,
            AGENT_HUMAN_RESUME_WORKFLOW,
            OccurrenceInput(spec_path=str(a.spec.resolve()), agent_id=a.agent_id),
            workflow_id=resume_id,
            task_queue=a.task_queue,
        )
        out = {
            **admission,
            "workflowType": AGENT_HUMAN_RESUME_WORKFLOW,
            "campaignId": spec.campaign_id,
            "agentId": a.agent_id,
            "effectId": materialization.effect_id,
            "resumeId": resume_id,
        }
    else:
        if not a.agent_id or a.prompt_file is None or not a.turn_request_id or a.resume_id:
            raise ValueError(
                "continue/continue-retry requires --agent-id --prompt-file --turn-request-id"
            )
        _materialization_for(spec, a.agent_id)
        prompt = a.prompt_file.read_text(encoding="utf-8")
        if not prompt or prompt != prompt.strip():
            raise ValueError("continuation prompt must be non-empty and trimmed")
        if len(prompt.encode("utf-8")) > 32768:
            raise ValueError("continuation prompt exceeds 32768 UTF-8 bytes")
        turn_request_id = require_uuid7(a.turn_request_id, "turnRequestId")
        workflow_id = turn_request_id
        value = AgentContinueInput(
            spec_path=str(a.spec.resolve()),
            agent_id=a.agent_id,
            turn_request_id=turn_request_id,
            prompt=prompt,
        )
        if a.operation == "continue-retry":
            admission = await _admit_failed_continue_retry(
                client,
                value,
                logical_workflow_id=turn_request_id,
                task_queue=a.task_queue,
            )
        else:
            admission = await _admit_workflow(
                client,
                AGENT_CONTINUE_WORKFLOW,
                value,
                workflow_id=workflow_id,
                task_queue=a.task_queue,
            )
        out = {
            **admission,
            "workflowType": AGENT_CONTINUE_WORKFLOW,
            "campaignId": spec.campaign_id,
            "agentId": a.agent_id,
            "turnRequestId": turn_request_id,
        }
    print(json.dumps(out, sort_keys=True))


p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--spec", type=Path, required=True)
p.add_argument(
    "--operation",
    choices=(
        "campaign-materialize",
        "materialize",
        "pre-effect-retry",
        "reconcile",
        "human-resume",
        "continue",
        "continue-retry",
    ),
    default="campaign-materialize",
)
p.add_argument("--agent-id")
p.add_argument("--prompt-file", type=Path)
p.add_argument("--turn-request-id")
p.add_argument("--resume-id")
p.add_argument("--address", default="127.0.0.1:17233")
p.add_argument("--namespace", default="default")
p.add_argument("--task-queue", default="ordivon-agent-automation")
a = p.parse_args()
asyncio.run(run(a))
