#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, urllib.request, uuid
from pathlib import Path

URL='http://127.0.0.1:5678/webhook/ordivon-distribution-adapter-smoke-v1'

def event_for(mode:str,event_id:str,intent_file:Path|None)->dict:
    if mode=='blocked':
        if intent_file is None: raise ValueError('--intent is required for blocked mode')
        intent=json.loads(intent_file.read_text())
        data_intent={'intentId':intent['intentId'],'occurrenceRef':intent['occurrenceRef'],'provider':intent['carrier']['provider'],'effectName':intent['effect']['name'],'artifact':intent.get('artifact')}
        decision={'action':'artifact_release_not_ready','reason':'artifact-backed-effect-requires-release-ready-artifact','externalEffectPerformed':False}
    else:
        data_intent={'intentId':'provider-readback-only','occurrenceRef':'synthetic-read-only','provider':'github','effectName':'provider_readback','artifact':None}
        decision={'action':'preflight_ready','reason':'read-only-provider-positive-control','externalEffectPerformed':False}
    return {'specversion':'1.0','id':event_id,'source':'urn:ordivon:operations:n8n-distribution-acceptance','type':'io.ordivon.distribution.admission.v1','time':dt.datetime.now(dt.timezone.utc).isoformat(),'datacontenttype':'application/json','data':{'intent':data_intent,'decision':decision}}

def invoke(event:dict)->dict:
    req=urllib.request.Request(URL,data=json.dumps(event,separators=(',',':')).encode(),method='POST',headers={'Content-Type':'application/json','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('blocked','readback'),required=True);p.add_argument('--intent',type=Path);p.add_argument('--id');p.add_argument('--pretty',action='store_true');a=p.parse_args()
    event_id=a.id or f'ordivon-dist-adapter-{a.mode}-{uuid.uuid4().hex}'
    event=event_for(a.mode,event_id,a.intent);result=invoke(event)
    if result.get('correlationid')!=event_id: raise RuntimeError('correlation mismatch')
    data=result.get('data') or {}
    if data.get('externalEffectPerformed') is not False: raise RuntimeError('adapter result claimed external effect')
    if a.mode=='blocked':
        if result.get('type')!='io.ordivon.integration.distribution.blocked.v1' or data.get('providerCalled') is not False: raise RuntimeError(f'bad blocked result: {result!r}')
    else:
        if result.get('type')!='io.ordivon.integration.distribution.readback.v1' or data.get('providerCalled') is not True or data.get('externalMethod')!='GET': raise RuntimeError(f'bad readback result: {result!r}')
        if (data.get('observedObject') or {}).get('number')!=72: raise RuntimeError('unexpected GitHub readback object')
    print(json.dumps(result,indent=2 if a.pretty else None,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
