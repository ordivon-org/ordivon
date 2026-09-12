#!/usr/bin/env python
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from artifact_handoff import build_intent
from admission import normalize
from bound_refs import occurrence_ref, provider_observation_ref, effect_authority_ref

NOW=datetime(2026,9,12,5,40,tzinfo=timezone.utc)

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def opa_action(normalized:dict)->str:
    with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:
        json.dump(normalized,f); p=Path(f.name)
    try:
        r=subprocess.run(['opa','eval','--format','raw','--data',str(ROOT/'policy/distribution.rego'),'--input',str(p),'data.ordivon.distribution.decision.action'],check=True,text=True,capture_output=True)
        return r.stdout.strip()
    finally:p.unlink(missing_ok=True)

def provider(intent:dict)->dict:
    x={'schemaVersion':2,'observationRef':'sha256:'+'0'*64,'occurrenceRef':intent['occurrenceRef'],'provider':'github','accountRef':'repo:test/artifacts','adapter':'github-release-write','effectName':'publish_artifact','effectMode':'write','effectSupported':True,'executionMode':'api','missingProviderRequirements':[],'missingInteractions':[],'sourceKind':'provider_cli','sourceRef':'test:provider-read-only','observedAt':'2026-09-12T05:35:00Z','validUntil':'2026-09-12T05:45:00Z'}
    x['observationRef']=provider_observation_ref(x); return x

def authority(intent:dict)->dict:
    x={'schemaVersion':2,'authorityRef':'sha256:'+'0'*64,'occurrenceRef':intent['occurrenceRef'],'principalRef':'test:principal','provider':'github','accountRef':'repo:test/artifacts','effectName':'publish_artifact','decision':'grant','issuedAt':'2026-09-12T05:35:00Z','validUntil':'2026-09-12T05:45:00Z','sourceRef':'test:exact-approval'}
    x['authorityRef']=effect_authority_ref(x); return x

def package(root:Path,*,release_ready:bool,trust:str)->Path:
    primary=b'deterministic artifact bytes'
    (root/'artifacts').mkdir()
    (root/'artifacts/a.bin').write_bytes(primary)
    value={'schemaVersion':1,'kind':'artifact-delivery-package-index','status':'PASS','primary':{'name':'a.bin','path':'artifacts/a.bin','size':len(primary),'digest':{'sha256':digest(primary)}},'releaseReady':release_ready,'trustStanding':trust}
    p=root/'package-index.json';p.write_text(json.dumps(value));return p

def intent_for(pkg:Path)->dict:
    return build_intent(package_index=pkg,provider='github',account_ref='repo:test/artifacts',adapter='github-release-write',effect_name='publish_artifact',effect_payload={'name':'a.bin'},intent_id='intent:test:artifact',source_ref='artifact-package:test')

def main()->int:
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); unreleased=intent_for(package(root,release_ready=False,trust='LOCAL_UNSIGNED_DEVELOPMENT'))
        env={'schemaVersion':2,'intent':unreleased,'providerObservation':provider(unreleased),'effectAuthority':None}
        assert opa_action(normalize(env,NOW))=='artifact_release_not_ready'
        print('PASS real-shape unreleased Artifact is blocked before effect authority')

    with tempfile.TemporaryDirectory() as d:
        root=Path(d); ready=intent_for(package(root,release_ready=True,trust='CRYPTOGRAPHICALLY_VERIFIED'))
        noauth={'schemaVersion':2,'intent':ready,'providerObservation':provider(ready),'effectAuthority':None}
        assert opa_action(normalize(noauth,NOW))=='user_action_required'
        withauth=deepcopy(noauth);withauth['effectAuthority']=authority(ready)
        assert opa_action(normalize(withauth,NOW))=='preflight_ready'
        print('PASS release-ready Artifact still requires exact effect authority')

        mutated=deepcopy(ready);mutated['artifact']['trustStanding']='LOCAL_UNSIGNED_DEVELOPMENT'
        assert occurrence_ref(mutated)!=ready['occurrenceRef']
        print('PASS trust-standing mutation changes occurrence identity')

        primary=root/'artifacts/a.bin';primary.write_bytes(b'tampered')
        try:intent_for(root/'package-index.json')
        except ValueError as e:
            assert 'do not match' in str(e);print('PASS primary-byte drift fails handoff')
        else:raise AssertionError('tampered primary unexpectedly admitted')
    return 0
if __name__=='__main__':raise SystemExit(main())
