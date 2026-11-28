"""Opt-in LIVE DeepSeek + installed Gateway/Runtime + original PG + hidden QA.

Only the three public task files are placed into the Agent's separate Runtime
Git Workspace. Oracle and hidden test stay in this caller-side harness source.
This is one billable node qualification, never part of ordinary CI.
"""

from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import time
import uuid

import pytest

from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.plugin_gateway_effect import (
    PluginGatewayExecutionBridgeFactory,
    PluginGatewayExecutionGrant,
)
from ordivon_harness.postgres_store import PostgresHarnessStore
from tests.test_plugin_gateway_effect import _contract


@pytest.mark.node_qualification
@pytest.mark.skipif(
    os.environ.get("HARNESS_REAL_CODING_TASK_R4") != "1",
    reason="explicit billable real coding task with separate Runtime Workspace and scratch PG18",
)
def test_live_model_edits_public_fixture_and_independent_hidden_qa_accepts(pg_schema):
    task_id = "HARNESS-EDIT-ADDRESSING-002"
    workspace_id = os.environ["HARNESS_REAL_CODING_WORKSPACE_ID"]
    gateway_url = os.environ["HARNESS_REAL_GATEWAY_URL"]
    bearer_file = Path(os.environ["HARNESS_REAL_GATEWAY_BEARER_TOKEN_FILE"])
    secret_file = Path(os.environ["HARNESS_REAL_DEEPSEEK_SECRET_FILE"])
    work_root = Path("/var/lib/ordivon/pg-candidate/workspaces") / workspace_id
    task_root = Path(__file__).resolve().parents[1]
    qa_file = task_root / "evals/harness-edit-addressing-002/qa.py"
    fixture = task_root / "fixtures/harness-edit-addressing-repeated-v1"
    assert work_root.is_dir()
    assert {p.name for p in work_root.iterdir() if p.is_file() and p.name != ".git"} == {
        "SPEC.md",
        "feature_flags.py",
        "test_feature_flags.py",
    }, "a hidden task file reached the model-visible Workspace"
    protected = {
        name: (work_root / name).read_bytes() for name in ("SPEC.md", "test_feature_flags.py")
    }
    assert all(protected[name] == (fixture / name).read_bytes() for name in protected)
    assert (work_root / "feature_flags.py").read_bytes() == (
        fixture / "feature_flags.py"
    ).read_bytes()
    spec = importlib.util.spec_from_file_location("r4_independent_domain_qa", qa_file)
    assert spec is not None and spec.loader is not None
    qa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qa)
    qa_task = qa.validate_task()
    assert qa_task["taskId"] == task_id

    settings = DeepSeekSettings.from_secret_file(
        secret_file, timeout_seconds=75, max_output_tokens=4096
    )
    endpoint = LoopbackMcpEndpoint(gateway_url, name="ordivon-gateway")
    client = OfficialMcpClient(endpoint, bearer_token_file=bearer_file)
    grant = PluginGatewayExecutionGrant(
        capability="execution.linux",
        workspace_id=workspace_id,
        executable_allowlist=("/usr/bin/python3",),
        env_allowlist=(),
        max_timeout_ms=90000,
    )
    factory = PluginGatewayExecutionBridgeFactory(endpoint, client, grant)
    uid = uuid.uuid4().hex[:16]
    run_id = "harness-run:real-coding-r4-" + uid
    sample = _contract(factory)
    contract = replace(
        sample,
        harness_run_id=run_id,
        caller_run_ref="trial:real-coding-r4-" + uid,
        provider_id="provider:deepseek",
        adapter_id=DeepSeekTurnAdapter.adapter_id,
        requested_model_id=settings.model,
        harness_implementation_id="ordivon-harness@r4-live-domain-consumer",
        created_at_ms=int(time.time() * 1000),
        budget={
            "maxModelCalls": 6,
            "maxToolCalls": 5,
            "maxObservationBytes": 131072,
            "maxWallTimeMs": 250000,
            "maxTotalTokens": 30000,
            "maxModelRetries": 0,
            "maxToolCorrections": 1,
            "maxConclusionCorrections": 1,
            "maxObservationOnlyTurns": 3,
            "maxNoProgressTurns": 3,
        },
    )
    agent = HarnessAgentRun.create(
        pg_schema[0],
        pg_schema[1],
        contract,
        lambda exact: DeepSeekTurnAdapter(settings, completion_contract=exact.completion_contract),
        tool_bridge_factory=factory,
    )
    task_message = (
        "You are an autonomous coding agent operating on an isolated tiny Git "
        "Workspace. Read SPEC.md, feature_flags.py, and test_feature_flags.py "
        "with the currently authorized execution_submit tool. The user task "
        "is exactly the requirement in SPEC.md. Fix the bug by editing only "
        "feature_flags.py. Use only executable=/usr/bin/python3 with cwdRelative='.' "
        "and Python '-c' or '-m' arguments. After editing, run the public "
        "test_feature_flags.py unittest with the same authorized tool. "
        "Use the observed physical Tool output to decide whether you can "
        "conclude candidate_completed. Do not assume a Tool succeeded if "
        "there is no Owner observation. No hidden QA, oracle or intended edit "
        "code is provided."
    )
    execution = agent.run(({"role": "user", "content": task_message},))
    stop = execution.loop_result.stop_code.value
    usage = dict(execution.loop_result.usage)
    candidate_path = work_root / "feature_flags.py"
    accepted = qa.run_candidate("real-deepseek-r4", candidate_path)
    protected_ok = all(
        (work_root / name).read_bytes() == contents for name, contents in protected.items()
    )
    with PostgresHarnessStore(pg_schema[0], schema=pg_schema[1]) as store:
        continuity = EventSourcedRunContinuity.open(store, run_id)
        step = continuity.load_current_tool_step()
        owner_ref = step.receipt.runtime_job_ref if step.receipt is not None else None
        request_id = step.intent.client_request_id
        observed = step.receipt is not None and step.receipt.status.value == "observed"
        store.validate_run_history(run_id)
        persisted = store.load_run(run_id).status.value
    owner_checked = False
    if owner_ref and request_id:
        error, response = client.call_tool(
            "execution.get",
            {
                "operationRef": f"ordivon-exec:v1:runtime.linux:{owner_ref}",
                "requestId": request_id,
                "capability": "execution.linux",
                "eventLimit": 10,
                "waitMs": 0,
            },
        )
        owner_checked = (
            error is False
            and response.get("native_id") == owner_ref
            and response.get("execution_disposition") == "succeeded"
            and response.get("delivery_disposition") == "committed"
            and response.get("exit_code") == 0
        )
    report = {
        "kind": "harness.real-coding-domain-consumer-r4",
        "taskId": task_id,
        "sourcePgRunId": run_id,
        "model": settings.model,
        "provider": "real-deepseek",
        "gateway": "installed-real-owner",
        "runtimeWorkspaceId": workspace_id,
        "lastOwnerJobId": owner_ref,
        "ownerObservationConfirmed": owner_checked,
        "lastToolStepObserved": observed,
        "sourceRunStatus": persisted,
        "runStopCode": stop,
        "modelCalls": usage.get("modelCalls"),
        "toolCalls": usage.get("toolCalls"),
        "totalTokens": usage.get("totalTokens"),
        "visiblePassed": accepted["visiblePassed"],
        "hiddenPassed": accepted["hiddenPassed"],
        "changedPathsForDomainVerifier": accepted["changedPaths"],
        "protectedPublicFilesUnchanged": protected_ok,
        "domainTaskSolved": bool(
            accepted["visiblePassed"] and accepted["hiddenPassed"] and protected_ok
        ),
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True)
    assert owner_checked, report
    assert observed, report
    assert persisted == "completed", report
    assert stop == "candidate_completed", report
    assert usage.get("toolCalls", 0) >= 2, report
    assert protected_ok, report
    assert accepted["visiblePassed"] and accepted["hiddenPassed"], report
