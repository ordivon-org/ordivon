#!/usr/bin/env python
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from bound_refs import occurrence_ref


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return 'sha256:'+h.hexdigest()


def build_intent(*, package_index: Path, provider: str, account_ref: str, adapter: str, effect_name: str, effect_payload: object, intent_id: str, source_ref: str) -> dict:
    package=json.loads(package_index.read_text())
    if package.get('schemaVersion') != 1 or package.get('kind') != 'artifact-delivery-package-index':
        raise ValueError('unsupported Artifact package index')
    artifact=package.get('primary')
    digest=(artifact or {}).get('digest') if isinstance(artifact,dict) else None
    primary_sha=(digest or {}).get('sha256') if isinstance(digest,dict) else None
    if not isinstance(primary_sha,str) or len(primary_sha) != 64:
        raise ValueError('Artifact package index lacks primary.digest.sha256')
    primary_rel=artifact.get('path')
    if not isinstance(primary_rel,str) or not primary_rel:
        raise ValueError('Artifact package index lacks primary path')
    primary_path=(package_index.parent/primary_rel).resolve()
    package_root=package_index.parent.resolve()
    if package_root not in primary_path.parents:
        raise ValueError('Artifact primary path escapes package directory')
    if not primary_path.is_file():
        raise ValueError('Artifact primary file is absent')
    actual_primary=sha256(primary_path).removeprefix('sha256:')
    if actual_primary != primary_sha:
        raise ValueError('Artifact primary bytes do not match package index digest')
    release_ready=package.get('releaseReady')
    trust=package.get('trustStanding')
    if not isinstance(release_ready,bool): raise ValueError('Artifact package index lacks boolean releaseReady')
    if not isinstance(trust,str) or not trust: raise ValueError('Artifact package index lacks trustStanding')
    intent={
      'schemaVersion':2,
      'intentId':intent_id,
      'occurrenceRef':'sha256:'+'0'*64,
      'artifact':{
        'sha256': 'sha256:'+primary_sha,
        'releaseReady':release_ready,
        'trustStanding':trust,
        'sourceRef':source_ref,
      },
      'carrier':{'adapter':adapter,'provider':provider,'accountRef':account_ref},
      'effect':{'name':effect_name,'payload':effect_payload},
    }
    intent['occurrenceRef']=occurrence_ref(intent)
    return intent


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--package-index',type=Path,required=True)
    p.add_argument('--provider',required=True); p.add_argument('--account-ref',required=True)
    p.add_argument('--adapter',required=True); p.add_argument('--effect-name',required=True)
    p.add_argument('--payload-json',required=True); p.add_argument('--intent-id',required=True); p.add_argument('--source-ref',required=True)
    a=p.parse_args()
    payload=json.loads(a.payload_json)
    print(json.dumps(build_intent(package_index=a.package_index,provider=a.provider,account_ref=a.account_ref,adapter=a.adapter,effect_name=a.effect_name,effect_payload=payload,intent_id=a.intent_id,source_ref=a.source_ref),indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
