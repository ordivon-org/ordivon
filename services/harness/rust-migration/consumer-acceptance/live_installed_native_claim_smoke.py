#!/usr/bin/env python3
"""Disposable real installed Runtime native Claim smoke, never a deployer.

Usage: HARNESS_PG_TEST_DSN='...' ORDIVON_LIVE_MCP_URL='http://127.0.0.1:8897/mcp'
       ORDIVON_LIVE_BEARER_FILE='/etc/ordivon/runtime-mcp.token'
       python live_installed_native_claim_smoke.py

Uses disposable source workspace, separate Harness test PG, one exact native job,
and a recipient file. Never targets pre-existing workspaces.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.mcp_http_client import LoopbackMcpEndpoint, OfficialMcpClient
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from tests.test_r3_supported_agent_run import completed, contract

SCHEMA = "harness_claim_live_" + os.environ.get("ORDIVON_LIVE_SCHEMA_SUFFIX", "r24")
SOURCE = os.environ.get("ORDIVON_LIVE_SOURCE_REV", "3f1bd38018f4823a81ce13b5e5a162dc116338ee")
ROOT = os.environ.get("ORDIVON_LIVE_SOURCE_REPO", "/root/projects/ordivon")

def client():
    return OfficialMcpClient(
        LoopbackMcpEndpoint(os.environ["ORDIVON_LIVE_MCP_URL"]),
        bearer_token_file=Path(os.environ["ORDIVON_LIVE_BEARER_FILE"]),
    )

def call(native, name, data):
    error, value = native.call_tool(name, data)
    if error:
        raise RuntimeError(f"{name} native rejected: {value}")
    return value

def adapter(_):
    return ScriptedTurnAdapter((completed("model-call:r24-live-completed"),))

def main():
    dsn = os.environ["HARNESS_PG_TEST_DSN"]
    suffix = secrets.token_hex(5)
    workspace = "ws-harness-r24-liveclaim-" + suffix
    v = contract("liveclaim-" + suffix)
    recipient = Path(os.environ["ORDIVON_LIVE_RECIPIENT"]) / ("harness-r24-" + suffix + ".txt")
    native = client()
    with PostgresHarnessStore(dsn, schema=SCHEMA, initialize=True):
        pass
    opened = call(native, "workspace.open", {
        "schemaVersion":1,"workspaceId":workspace,"sourceRepo":ROOT,"sourceRevision":SOURCE,
    })
    assert opened["workspaceId"] == workspace
    print("LIVE_TEST_WORKSPACE " + workspace,flush=True)

    class LostBeforeCommit:
        def call_tool(self, name, arguments):
            if name == "workspace.claim.reserve":
                raise ConnectionError("simulated loss before Runtime received reserve")
            return native.call_tool(name, arguments)

    try:
        HarnessAgentRun.create(
            dsn, SCHEMA, v, adapter, workspace_claim_client=LostBeforeCommit(),
            workspace_claim_workspace_id=workspace,
        )
    except Exception as exc:
        assert type(exc).__name__ == "HarnessWorkspaceAdmissionUnavailable", repr(exc)
    else:
        raise AssertionError("unprotected Run became usable")
    with PostgresHarnessStore(dsn, schema=SCHEMA) as store:
        assert store.load_run(v.harness_run_id).status.value == "created"
    print("LIVE_PRECOMMIT_FAILED_CLOSED_NO_READY_RUN",flush=True)

    class LostAfterCommit:
        lost=False
        def call_tool(self, name, arguments):
            value = native.call_tool(name, arguments)
            if name == "workspace.claim.reserve" and not self.lost:
                self.lost=True
                raise ConnectionError("simulated loss of committed Runtime Claim response")
            return value

    run = HarnessAgentRun.create(
        dsn, SCHEMA, v, adapter, workspace_claim_client=LostAfterCommit(),
        workspace_claim_workspace_id=workspace,
    )
    original = run.workspace_claim.require_held()
    assert original["runRef"] == v.harness_run_id
    claim_req = run.workspace_claim.request_id
    claim = call(native, "workspace.claim.get", {"schemaVersion":1,"clientRequestId":claim_req})
    assert claim["state"]=="held" and claim["claimId"]==original["claimId"]
    print("LIVE_LOST_COMMIT_REPLY_SAME_ORIGINAL_RUN_CLAIM_HELD",flush=True)

    recon_env = dict(os.environ)
    recon_env.update({
       "ORDIVON_LIVE_RUN_ID":v.harness_run_id,
       "ORDIVON_LIVE_WORKSPACE":workspace,
       "ORDIVON_LIVE_CLAIM_ID":original["claimId"],
       "ORDIVON_LIVE_CLAIM_REQUEST":claim_req,
    })
    reconnect = subprocess.run([sys.executable,str(Path(__file__).resolve()),"--reconnect"],
        env=recon_env,check=True,capture_output=True,text=True,timeout=35)
    assert "LIVE_NEW_PROCESS_SAME_RUN_AND_CLAIM_NO_MODEL_REPLAY" in reconnect.stdout, reconnect.stdout
    print(reconnect.stdout.strip(),flush=True)

    original_bytes = "R24_ACTUAL_INSTALLED_NATIVE_PROTECTED_OUTPUT_" + suffix
    call(native,"workspace.mutate",{"schemaVersion":1,"workspaceId":workspace,
        "mutations":[{"mode":"WRITE","relativePath":"r24-live-proof.txt","content":original_bytes}]})
    request_id = "r24-live-physical-tooljob-" + suffix
    job = call(native,"workspace.exec",{"schemaVersion":1,"clientRequestId":request_id,
        "execution":{"workspaceId":workspace,"executable":"/usr/bin/bash","cwdRelative":".",
          "args":["-lc","git add r24-live-proof.txt && git -c user.name='Harness Proof' -c user.email='harness@users.noreply.invalid' commit -m 'R24 original live test output'"],
          "timeoutMs":30000},"waitMs":2000})
    job_id=job["jobId"]
    for _ in range(25):
        if job.get("executionTerminal"):
            break
        job=call(native,"job.observe",{"jobId":job_id,"waitMs":2000})
    assert job["executionTerminal"] and job["exitCode"] == 0,job
    workspace_state=call(native,"workspace.get",{"schemaVersion":1,"workspaceId":workspace})
    assert workspace_state["activeJobIds"]==[],workspace_state

    denied, denied_result = native.call_tool("workspace.close",{
         "schemaVersion":1,"workspaceId":workspace,"force":False,
         "consumerReleased":True,"expectedSourceStateDigest":workspace_state["sourceStateDigest"]})
    assert denied and denied_result.get("error",{}).get("code")=="CONCURRENCY_LIMIT", denied_result
    still=call(native,"workspace.read",{"schemaVersion":1,"workspaceId":workspace,
         "relativePath":"r24-live-proof.txt","mode":"FULL","maxBytes":4096})
    assert still["content"]==original_bytes
    held=run.workspace_claim.require_held()
    assert held["claimId"]==original["claimId"]
    print("LIVE_REAL_JOB_TERMINAL_ZERO_ACTIVE_WORKSPACE_CLOSE_DENIED_ORIGINAL_BYTES_READABLE",flush=True)

    # Native job has exited, yet original model Run is still CREATED.
    completed_run=run.run(({"role":"user","content":"Deliver exact output."},))
    assert completed_run.loop_result.stop_code.value == "candidate_completed"
    final=run.inspect_finalization_source()
    assert final["sourceStanding"]=="source-settled"
    assert final["unsettledToolIntentDigests"] == []
    # Caller recipient independently reads original byte, not merely Job exit status.
    recipient.write_bytes(still["content"].encode())
    expected_digest=hashlib.sha256(original_bytes.encode()).hexdigest()
    ack={"harnessRunId":v.harness_run_id,"runReceiptDigest":final["runReceiptDigest"],
         "accepted":True,"sha256":expected_digest}
    def verified(source, receipt):
        s=call(native,"workspace.get",{"schemaVersion":1,"workspaceId":workspace})
        return (source["sourceStanding"]=="source-settled" and s["activeJobIds"]==[]
            and recipient.read_bytes()==original_bytes.encode()
            and hashlib.sha256(recipient.read_bytes()).hexdigest()==receipt["sha256"])
    released=run.release_workspace_after_delivery(recipient_ack=ack,
        verify_delivered_and_drained=verified)
    assert released["state"]=="released"
    result=call(native,"workspace.close",{"schemaVersion":1,"workspaceId":workspace,
         "force":False,"consumerReleased":True,
         "expectedSourceStateDigest":workspace_state["sourceStateDigest"]})
    assert result["removed"] is True, result
    assert recipient.read_bytes() == original_bytes.encode()
    observed=call(native,"job.list",{"clientRequestId":request_id,"limit":10})
    assert len(observed["jobs"])==1 and observed["jobs"][0]["jobId"]==job_id
    print("LIVE_COMPLETED_DELIVERED_BYTES_ACK_CLAIM_RELEASED_NATIVE_CLOSE_REMOVED",flush=True)
    print(json.dumps({"workspaceId":workspace,"runId":v.harness_run_id,"jobId":job_id,
       "claimId":original["claimId"],"recipientSha256":expected_digest},sort_keys=True),flush=True)

def reconnect():
    native=client()
    run_id=os.environ["ORDIVON_LIVE_RUN_ID"]
    with PostgresHarnessStore(os.environ["HARNESS_PG_TEST_DSN"],schema=SCHEMA) as store:
        prior=store.load_run(run_id)
        assert prior.status.value=="created"
        rev=prior.revision
    run=HarnessAgentRun.open(os.environ["HARNESS_PG_TEST_DSN"],SCHEMA,run_id,
      adapter,workspace_claim_client=native,
      workspace_claim_workspace_id=os.environ["ORDIVON_LIVE_WORKSPACE"])
    assert run.harness_run_id==run_id
    assert run.workspace_claim.request_id==os.environ["ORDIVON_LIVE_CLAIM_REQUEST"]
    assert run.workspace_claim.require_held()["claimId"]==os.environ["ORDIVON_LIVE_CLAIM_ID"]
    with PostgresHarnessStore(os.environ["HARNESS_PG_TEST_DSN"],schema=SCHEMA) as store:
       assert store.load_run(run_id).revision==rev
    print("LIVE_NEW_PROCESS_SAME_RUN_AND_CLAIM_NO_MODEL_REPLAY")

if __name__=="__main__":
    reconnect() if len(sys.argv)>1 and sys.argv[1]=="--reconnect" else main()
