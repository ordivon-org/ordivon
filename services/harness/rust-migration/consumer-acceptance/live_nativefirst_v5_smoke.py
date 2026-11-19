#!/usr/bin/env python3
"""R26 independent native-first REAL installed Runtime MCP smoke.

Scoped disposable Runtime workspaces and a disposable Harness PostgreSQL database.
No production Run/SCM/Release changed. Do not force-close on failure.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path
import secrets
import subprocess
import sys

from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.workspace_claim import WorkspaceRunClaim
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.runtime_port import HarnessWorkspaceAdmissionUnavailable
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from tests.test_r3_supported_agent_run import FakeRuntime, completed, contract, execution_binding

def native_client():
    return OfficialMcpClient(
        LoopbackMcpEndpoint("http://127.0.0.1:8897/mcp"),
        bearer_token_file=Path("/etc/ordivon/runtime-mcp.token"),
    )

def require_call(client, name, arguments):
    failed, result = client.call_tool(name, arguments)
    if failed:
        raise RuntimeError(f"{name} failed: {result}")
    return result

def adapter(_):
    return ScriptedTurnAdapter((completed("model-call:v5-native-first"),))

def new_agent(dsn, schema, run_contract, client, workspace):
    return HarnessAgentRun.create(
        dsn, schema, run_contract, adapter,
        execution_binding=replace(execution_binding(run_contract),workspace_ref=workspace),
        runtime=FakeRuntime(),
        workspace_claim_client=client,
        workspace_claim_workspace_id=workspace,
    )

def assert_pg_absent(dsn, schema, run_id):
    with PostgresHarnessStore(dsn, schema=schema) as store:
        try:
            store.load_run(run_id)
        except KeyError:
            return
        raise AssertionError("PG Run born without original Native Claim authority")

def reconnect():
    dsn=os.environ["HARNESS_PG_TEST_DSN"]
    schema=os.environ["ORDIVON_TEST_SCHEMA"]
    run_id=os.environ["ORDIVON_TEST_RUN_ID"]
    workspace=os.environ["ORDIVON_TEST_WORKSPACE"]
    claim_id=os.environ["ORDIVON_TEST_CLAIM_ID"]
    client=native_client()
    with PostgresHarnessStore(dsn, schema=schema) as store:
        before=store.load_run(run_id)
        assert before.status.value == "created"
        original_rev=before.revision
    with PostgresHarnessStore(dsn,schema=schema) as store:
        original_contract=EventSourcedRunContinuity.open(store,run_id).contract
    restored=HarnessAgentRun.open(dsn,schema,run_id,adapter,
            execution_binding=replace(execution_binding(original_contract),workspace_ref=workspace),
            runtime=FakeRuntime(),
            workspace_claim_client=client,workspace_claim_workspace_id=workspace)
    assert restored.workspace_claim.require_held()["claimId"] == claim_id
    with PostgresHarnessStore(dsn, schema=schema) as store:
        assert store.load_run(run_id).revision == original_rev
    print("LIVE_NEW_PROCESS_ORIGINAL_RUN_CLAIM_REOPEN_NO_MODEL_REPLAY",flush=True)

def main():
    dsn=os.environ["HARNESS_PG_TEST_DSN"]
    suffix=secrets.token_hex(5)
    schema="harness_v5_nativefirst_"+suffix
    w1="ws-harness-v5-nativefirst-w1-"+suffix
    w2="ws-harness-v5-nativefirst-w2-"+suffix
    source="5ae84bdb6a89781fd380c91696f4c904c8a69ec9"
    source_repo="/root/projects/ordivon"
    run_contract=contract("v5-nativefirst-"+suffix,tools=True)
    run_id=run_contract.harness_run_id
    client=native_client()
    required={"workspace.claim.get","workspace.claim.reserve","workspace.claim.release","workspace.open","workspace.close","job.observe","workspace.exec","workspace.get"}
    actual={tool["name"] for tool in client.list_tools()}
    assert required.issubset(actual),f"Native installed catalog missing {sorted(required-actual)}"
    print("LIVE_INSTALLED_NATIVE_CLAIM_CATALOG_QUALIFIED",flush=True)

    with PostgresHarnessStore(dsn,schema=schema,initialize=True):
        pass
    require_call(client,"workspace.open",{"schemaVersion":1,"workspaceId":w1,"sourceRepo":source_repo,"sourceRevision":source})
    require_call(client,"workspace.open",{"schemaVersion":1,"workspaceId":w2,"sourceRepo":source_repo,"sourceRevision":source})
    print("LIVE_DISPOSABLE_WORKSPACES_CREATED "+w1+" "+w2,flush=True)

    class BeforeReserveLost:
        def call_tool(self,name,arguments):
            if name=="workspace.claim.reserve":
                raise ConnectionError("injected before Native receives reserve")
            return client.call_tool(name,arguments)

    try:
        new_agent(dsn,schema,run_contract,BeforeReserveLost(),w1)
        raise AssertionError("unprotected Run was executable")
    except HarnessWorkspaceAdmissionUnavailable:
        pass
    assert_pg_absent(dsn,schema,run_id)
    original_claim=WorkspaceRunClaim(run_contract,w1,client)
    missing_error,missing=client.call_tool("workspace.claim.get",
                   {"schemaVersion":1,"clientRequestId":original_claim.request_id})
    assert missing_error and missing["error"]["code"]=="WORKSPACE_NOT_FOUND",missing
    print("LIVE_PRE_RESERVE_LOSS_NO_PG_RUN_NO_NATIVE_CLAIM",flush=True)

    # Native authentic reserve succeeds; original PostgreSQL birth is fault-injected.
    original_create=PostgresHarnessStore.create_run
    calls=[0]
    def fail_first_pg_birth(self, run_contract):
        calls[0]+=1
        raise RuntimeError("test-only PG birth interruption AFTER authentic Native HELD")
    PostgresHarnessStore.create_run=fail_first_pg_birth
    try:
        try:
            new_agent(dsn,schema,run_contract,client,w1)
            raise AssertionError("injected PG birth should fail")
        except RuntimeError as exc:
            assert "test-only PG birth interruption" in str(exc),repr(exc)
    finally:
        PostgresHarnessStore.create_run=original_create
    assert calls==[1],calls
    assert_pg_absent(dsn,schema,run_id)
    claim=original_claim.require_held()
    assert claim["workspaceId"]==w1 and claim["runRef"]==run_id
    original_claim_id=claim["claimId"]
    print("LIVE_NATIVE_FIRST_HELD_PG_BIRTH_FAILED_ORPHAN_HELD",flush=True)

    # A different physically-existing Workspace must not steal the same original Run.
    try:
        new_agent(dsn,schema,run_contract,client,w2)
        raise AssertionError("caller W2 adopted original W1 holder")
    except HarnessWorkspaceAdmissionUnavailable:
        pass
    assert_pg_absent(dsn,schema,run_id)
    assert original_claim.require_held()["claimId"]==original_claim_id
    print("LIVE_ORPHAN_HELD_WRONG_W2_REFUSED_AND_W1_PRESERVED",flush=True)

    # Restart the same exact Run/Workspace/ClientRequestId.
    run=new_agent(dsn,schema,run_contract,client,w1)
    assert run.workspace_claim.require_held()["claimId"]==original_claim_id
    with PostgresHarnessStore(dsn,schema=schema) as store:
        assert store.load_run(run_id).status.value=="created"
    child_env=dict(os.environ)
    child_env.update({"ORDIVON_TEST_SCHEMA":schema,"ORDIVON_TEST_RUN_ID":run_id,
       "ORDIVON_TEST_WORKSPACE":w1,"ORDIVON_TEST_CLAIM_ID":original_claim_id})
    child=subprocess.run([sys.executable,__file__,"--reconnect"],env=child_env,
            check=True,capture_output=True,text=True,timeout=45)
    assert "LIVE_NEW_PROCESS_ORIGINAL_RUN_CLAIM_REOPEN_NO_MODEL_REPLAY" in child.stdout,child.stdout
    print(child.stdout.strip(),flush=True)
    print("LIVE_SAME_NATIVE_HELD_THEN_PG_RUN_BORN",flush=True)

    # Terminal physical native Job exists and activeJobIds=[]; original Run remains CREATED.
    contents="V5_EXACT_REAL_RUNTIME_WORKSPACE_NATIVE_FIRST_"+suffix
    require_call(client,"workspace.mutate",{"schemaVersion":1,"workspaceId":w1,"mutations":[
       {"mode":"WRITE","relativePath":"nativefirst-artifact.txt","content":contents}]})
    req_id="v5-nativefirst-physical-result-"+suffix
    job=require_call(client,"workspace.exec",{"schemaVersion":1,"clientRequestId":req_id,
      "execution":{"workspaceId":w1,"cwdRelative":".","executable":"/usr/bin/bash",
        "args":["-lc","git add nativefirst-artifact.txt && git -c user.name='Native Smoke' -c user.email='native-smoke@users.noreply.invalid' commit -m 'R26 native-first verified bytes'"],
        "timeoutMs":30000},"waitMs":2000})
    job_id=job["jobId"]
    for _ in range(35):
        if job.get("executionTerminal"):
            break
        job=require_call(client,"job.observe",{"jobId":job_id,"waitMs":2000})
    assert job["executionTerminal"] and job["exitCode"]==0,job
    state=require_call(client,"workspace.get",{"schemaVersion":1,"workspaceId":w1})
    assert state["activeJobIds"]==[],state
    failed,denied=client.call_tool("workspace.close",{
      "schemaVersion":1,"workspaceId":w1,"force":False,"consumerReleased":True,
      "expectedSourceStateDigest":state["sourceStateDigest"]})
    assert failed and denied.get("error",{}).get("code")=="CONCURRENCY_LIMIT",denied
    read=require_call(client,"workspace.read",{
       "schemaVersion":1,"workspaceId":w1,"relativePath":"nativefirst-artifact.txt",
       "mode":"FULL","maxBytes":2048})
    assert read["content"]==contents
    assert original_claim.require_held()["claimId"]==original_claim_id
    print("LIVE_NATIVE_JOB_TERMINAL_JOBZERO_ACTIVE_RUN_CLOSE_DENIED_BYTES_RETAINED",flush=True)

    # Release attempts before domain consumer has accepted actual bytes must fail.
    try:
        run.release_workspace_after_delivery(
           recipient_ack={}, verify_delivered_and_drained=lambda *_: True)
        raise AssertionError("released original Claim without source+recipient")
    except HarnessWorkspaceAdmissionUnavailable:
        pass
    assert original_claim.require_held()["state"]=="held"

    outcome=run.run(({"role":"user","content":"Produce accepted exact output"},))
    assert outcome.loop_result.stop_code.value=="candidate_completed"
    final=run.inspect_finalization_source()
    assert final["sourceStanding"]=="source-settled",final
    assert final["unsettledToolIntentDigests"]==[],final
    recipient_dir=Path(os.environ["ORDIVON_TEST_RECIPIENT_DIR"])
    recipient_dir.mkdir(parents=True,exist_ok=True)
    recipient=recipient_dir/("v5-nativefirst-"+suffix+".txt")
    recipient.write_bytes(read["content"].encode("utf-8"))
    sha=hashlib.sha256(contents.encode()).hexdigest()
    ack={"harnessRunId":run_id,"runReceiptDigest":final["runReceiptDigest"],"accepted":True,
         "sha256":sha,"byteLength":len(contents.encode())}
    def verified(source,receipt):
        bytes_read=recipient.read_bytes()
        original=require_call(client,"workspace.get",{"schemaVersion":1,"workspaceId":w1})
        return (source["sourceStanding"]=="source-settled" and
           original["activeJobIds"]==[] and len(bytes_read)==receipt["byteLength"] and
           hashlib.sha256(bytes_read).hexdigest()==receipt["sha256"] and
           bytes_read==contents.encode("utf-8"))
    released=run.release_workspace_after_delivery(
       recipient_ack=ack,verify_delivered_and_drained=verified)
    assert released["state"]=="released",released
    closed=require_call(client,"workspace.close",{"schemaVersion":1,"workspaceId":w1,
       "force":False,"consumerReleased":True,
       "expectedSourceStateDigest":state["sourceStateDigest"]})
    assert closed["removed"] is True,closed
    claim_after=require_call(client,"workspace.claim.get",{
       "schemaVersion":1,"clientRequestId":original_claim.request_id})
    assert claim_after["state"]=="released",claim_after
    failed_w1,w1_result=client.call_tool("workspace.get",{"schemaVersion":1,"workspaceId":w1})
    assert failed_w1 and w1_result["error"]["code"]=="WORKSPACE_NOT_FOUND",w1_result
    ws2=require_call(client,"workspace.get",{"schemaVersion":1,"workspaceId":w2})
    closed2=require_call(client,"workspace.close",{"schemaVersion":1,"workspaceId":w2,
       "force":False,"consumerReleased":True,
       "expectedSourceStateDigest":ws2["sourceStateDigest"]})
    assert closed2["removed"] is True,closed2
    assert recipient.read_bytes()==contents.encode("utf-8")
    print("LIVE_DOMAIN_BYTES_ACK_CLAIM_RELEASED_NATIVE_CLOSES_REMOVED",flush=True)
    print(json.dumps({"runId":run_id,"nativeJobId":job_id,"claimId":original_claim_id,
        "workspace1":w1,"workspace2":w2,"recipientSha256":sha},sort_keys=True),flush=True)

if __name__=="__main__":
    reconnect() if len(sys.argv)>1 and sys.argv[1]=="--reconnect" else main()
