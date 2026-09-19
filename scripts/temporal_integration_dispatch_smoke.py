#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import urllib.request
import uuid
from pathlib import Path

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

ENV_URL='ORDIVON_DISTRIBUTION_INTEGRATION_URL'
REQUEST_TYPE='io.ordivon.distribution.admission.v1'


def _post(event:dict)->dict:
    url=os.environ.get(ENV_URL)
    if not url: raise RuntimeError(f'{ENV_URL} is required by the integration Activity')
    req=urllib.request.Request(url,data=json.dumps(event,separators=(',',':')).encode(),method='POST',headers={'Content-Type':'application/json','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)

@activity.defn(name='ordivon.distribution.integration-dispatch')
async def dispatch_integration_event(event:dict)->dict:
    result=await asyncio.to_thread(_post,event)
    if result.get('correlationid')!=event.get('id'): raise RuntimeError('integration correlation mismatch')
    if (result.get('data') or {}).get('externalEffectPerformed') is not False: raise RuntimeError('integration result claims external effect')
    return result

@workflow.defn(name='ordivon.distribution.integration-dispatch-smoke')
class DistributionIntegrationDispatchWorkflow:
    @workflow.run
    async def run(self,event:dict)->dict:
        result=await workflow.execute_activity(dispatch_integration_event,event,start_to_close_timeout=dt.timedelta(seconds=45),retry_policy=RetryPolicy(maximum_attempts=2))
        if result.get('correlationid')!=event.get('id'): raise ValueError('workflow integration correlation mismatch')
        if (result.get('data') or {}).get('externalEffectPerformed') is not False: raise ValueError('workflow refuses effectful integration result')
        return result

def make_blocked_event(intent_path:Path,event_id:str)->dict:
    intent=json.loads(intent_path.read_text())
    return {'specversion':'1.0','id':event_id,'source':'urn:ordivon:distribution:r8-temporal-acceptance','type':REQUEST_TYPE,'time':dt.datetime.now(dt.UTC).isoformat(),'datacontenttype':'application/json','data':{'intent':{'intentId':intent['intentId'],'occurrenceRef':intent['occurrenceRef'],'provider':intent['carrier']['provider'],'effectName':intent['effect']['name'],'artifact':intent.get('artifact')},'decision':{'action':'artifact_release_not_ready','reason':'artifact-backed-effect-requires-release-ready-artifact','externalEffectPerformed':False}}}

def make_read_event(event_id:str)->dict:
    return {'specversion':'1.0','id':event_id,'source':'urn:ordivon:distribution:r8-temporal-acceptance','type':REQUEST_TYPE,'time':dt.datetime.now(dt.UTC).isoformat(),'datacontenttype':'application/json','data':{'intent':{'intentId':'provider-readback-only','occurrenceRef':'synthetic-read-only','provider':'github','effectName':'provider_readback','artifact':None},'decision':{'action':'preflight_ready','reason':'read-only-provider-positive-control','externalEffectPerformed':False}}}

async def execute(address:str,event:dict)->dict:
    client=await Client.connect(address)
    token=uuid.uuid4().hex
    task_queue=f'distribution-integration-smoke-{token[:12]}'
    workflow_id=f'distribution-integration-smoke-{token}'
    async with Worker(client,task_queue=task_queue,workflows=[DistributionIntegrationDispatchWorkflow],activities=[dispatch_integration_event]):
        result=await client.execute_workflow(DistributionIntegrationDispatchWorkflow.run,event,id=workflow_id,task_queue=task_queue,execution_timeout=dt.timedelta(minutes=2))
    return {'workflowId':workflow_id,'taskQueue':task_queue,'eventId':event['id'],'result':result}

async def run(address:str,intent:Path)->dict:
    blocked=await execute(address,make_blocked_event(intent,'distribution-r8-blocked-'+uuid.uuid4().hex))
    readback=await execute(address,make_read_event('distribution-r8-readback-'+uuid.uuid4().hex))
    b=blocked['result'];r=readback['result']
    if b.get('type')!='io.ordivon.integration.distribution.blocked.v1' or (b.get('data') or {}).get('providerCalled') is not False: raise RuntimeError('durable blocked path failed')
    if r.get('type')!='io.ordivon.integration.distribution.readback.v1' or (r.get('data') or {}).get('externalMethod')!='GET': raise RuntimeError('durable readback path failed')
    return {'blocked':blocked,'readback':readback}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--address',default='127.0.0.1:17233');p.add_argument('--intent',type=Path,default=Path('evidence/r7-artifact-development-publication-intent.json'));a=p.parse_args()
    print(json.dumps(asyncio.run(run(a.address,a.intent)),indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
