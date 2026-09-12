#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parent.parent
ASYNC=ROOT/'contracts/asyncapi'

def load_json(name):return json.loads((ASYNC/name).read_text())

def validate(schema_name,value):
    schema=load_json(schema_name); errors=list(Draft202012Validator(schema).iter_errors(value));
    if errors: raise AssertionError('; '.join(e.message for e in errors))

def main():
    text=(ASYNC/'integration-events.asyncapi.yaml').read_text()
    for needle in ['asyncapi: 3.0.0','version: 0.2.0','DistributionAdmission:','DistributionBlockedResult:','DistributionReadbackResult:','const: io.ordivon.distribution.admission.v1','const: io.ordivon.integration.distribution.blocked.v1','const: io.ordivon.integration.distribution.readback.v1']:
        assert needle in text, needle
    admission={'intent':{'intentId':'i','occurrenceRef':'sha256:x','provider':'github','effectName':'publish_artifact','artifact':{'releaseReady':False}},'decision':{'action':'artifact_release_not_ready','reason':'artifact-backed-effect-requires-release-ready-artifact','externalEffectPerformed':False}}
    validate('distribution-admission-data.schema.json',admission)
    blocked={'admissionAction':'artifact_release_not_ready','provider':'github','providerCalled':False,'externalEffectPerformed':False,'reason':'blocked'}
    validate('distribution-integration-result-data.schema.json',blocked)
    readback={'admissionAction':'preflight_ready','provider':'github','providerCalled':True,'externalEffectPerformed':False,'externalMethod':'GET','observedObject':{'number':72}}
    validate('distribution-integration-result-data.schema.json',readback)
    for bad in ({**blocked,'externalEffectPerformed':True},{**readback,'externalEffectPerformed':True}):
        try:validate('distribution-integration-result-data.schema.json',bad)
        except AssertionError:pass
        else:raise AssertionError('effectful integration result unexpectedly accepted')
    print('PASS AsyncAPI Distribution integration contract shape')
    return 0
if __name__=='__main__':raise SystemExit(main())
