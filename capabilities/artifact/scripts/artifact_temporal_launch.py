#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from artifact_temporal_workflow import ARTIFACT_WORKFLOW, TRUST_MATERIAL_SIGNAL
from temporalio.client import Client
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from artifact_operations import validate_public_trust_material_envelope


def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()



async def main_async()->int:
    p=argparse.ArgumentParser();p.add_argument('--address',default='127.0.0.1:17233');p.add_argument('--namespace',default='default');p.add_argument('--task-queue',default='ordivon-artifact');sub=p.add_subparsers(dest='command',required=True);s=sub.add_parser('start');s.add_argument('--request',type=Path,required=True);s.add_argument('--workflow-id');s.add_argument('--allow-local-unsigned-development',action='store_true');s.add_argument('--initial-trust-material',type=Path);g=sub.add_parser('signal-trust');g.add_argument('--workflow-id',required=True);g.add_argument('--trust-material',type=Path,required=True);a=p.parse_args();client=await Client.connect(a.address,namespace=a.namespace)
    if a.command=='signal-trust':
        await client.get_workflow_handle(a.workflow_id).signal(TRUST_MATERIAL_SIGNAL,json.loads(a.trust_material.read_text()));print(json.dumps({'status':'SIGNALLED','workflowId':a.workflow_id},sort_keys=True));return 0
    request=a.request.resolve();digest=sha(request);wid=a.workflow_id or f'ordivon-artifact-{digest[:24]}';value={'request':{'path':str(request),'sha256':digest},'allowLocalUnsignedDevelopment':bool(a.allow_local_unsigned_development)}
    if a.initial_trust_material is not None:value['initialTrustMaterial']=validate_public_trust_material_envelope(json.loads(a.initial_trust_material.read_text()))
    try: handle=await client.start_workflow(ARTIFACT_WORKFLOW,value,id=wid,task_queue=a.task_queue,id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,id_conflict_policy=WorkflowIDConflictPolicy.FAIL)
    except WorkflowAlreadyStartedError: print(json.dumps({'status':'ALREADY_STARTED','workflowId':wid},sort_keys=True));return 2
    print(json.dumps({'status':'STARTED','workflowId':handle.id,'runId':handle.first_execution_run_id},sort_keys=True));return 0
def main()->int:return asyncio.run(main_async())
if __name__=='__main__':raise SystemExit(main())
