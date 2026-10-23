from __future__ import annotations
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT=Path(__file__).resolve().parents[2]
TOOL=ROOT/"profiles/research/tool-qualification/tool-qualification-packet-r1.schema.json"
COMP=ROOT/"profiles/research/mechanical-components/research-mechanical-component-r1.schema.json"

def load(p):
    s=json.loads(p.read_text(encoding="utf-8")); Draft202012Validator.check_schema(s); return s
@pytest.fixture(scope="module")
def ts(): return load(TOOL)
@pytest.fixture(scope="module")
def cs(): return load(COMP)
def good_tool():
    return {"packetKind":"research-tool-qualification-packet","schemaVersion":"r1","observationCut":"2026-10-12T08:00:00Z","qualifiedProblemClass":"scholarly.discovery.supplement","qualifiedOperation":"search","ownerRef":"owner:external:example","canonicalToolId":"example-tool","ownerCurrentnessEvidenceRef":"evidence:owner-current:1","interfaceRef":"interface:search-v1","effectClass":"read_only","executionOwnerRef":"owner:external:example","invocationSurface":"provider-native/search","evidenceRefs":["evidence:q:1"],"positiveControlRefs":["case:p:1"],"negativeControlRefs":["case:n:1"],"nonClaims":["not scientific correctness"],"standing":"QUALIFIED_IN_SCOPE"}
def hold_tool():
    return {"packetKind":"research-tool-qualification-packet","schemaVersion":"r1","observationCut":"2026-10-12T08:00:00Z","qualifiedProblemClass":"x","qualifiedOperation":"search","ownerRef":"owner:x","canonicalToolId":"x","effectClass":"read_only","nonClaims":["hold"],"standing":"HOLD","holdReasons":["HOLD_CURRENTNESS_UNKNOWN"]}
def good_comp(kind="Normalize"):
    x={"componentKind":"research-mechanical-component","schemaVersion":"r1","componentId":"component:x","mechanicalKind":kind,"ownerRef":"owner:research-profile","truthRole":"static-mechanical-definition","inputRefs":["schema:in"],"outputRefs":["schema:out"],"nonClaims":["not live availability"]}
    if kind=="Effect Adapter": x.update(effectAuthorizationOwnerRef="owner:effect",replaySemantics="readback before retry")
    return x
def valid(s,x): Draft202012Validator(s).validate(x)
def invalid(s,x):
    with pytest.raises(ValidationError): Draft202012Validator(s).validate(x)

@pytest.mark.parametrize("x,ok",[
(good_tool(),True),(hold_tool(),True),
({k:v for k,v in good_tool().items() if k!="ownerCurrentnessEvidenceRef"},False),
({**good_tool(),"currentProviderStatus":"READY"},False),
({**good_tool(),"negativeControlRefs":[]},False),
({**good_tool(),"nonClaims":[]},False),
({**good_tool(),"reuseDisposition":"PROMOTE_LEGO"},False),
({**good_tool(),"effectClass":"external_mutation"},False),
])
def test_tool_qualification_packet_contract(ts,x,ok):
    (valid if ok else invalid)(ts,x)

@pytest.mark.parametrize("x,ok",[
(good_comp(),True),(good_comp("Effect Adapter"),True),
({**good_comp(),"mechanicalKind":"TRANSFORM"},False),
({**good_comp(),"available":True},False),
({k:v for k,v in good_comp("Effect Adapter").items() if k!="effectAuthorizationOwnerRef"},False),
({**good_comp(),"mechanicalKind":"Scientific Judgment"},False),
({**good_comp(),"jobId":"job-123"},False),
])
def test_research_mechanical_component_contract(cs,x,ok):
    (valid if ok else invalid)(cs,x)
