#!/usr/bin/env python3
import json
import sys
from pathlib import Path

NODE_STATES = {"DISCOVERED","DESIGNED","IMPLEMENTING","IMPLEMENTED","VERIFIED","DEFERRED","REJECTED"}
SLICE_STATES = {"PROPOSED","ACTIVE","BLOCKED","COMPLETE","DEFERRED"}
ROOT_KEYS = {"schemaVersion","kind","truthRole","project","nodes","edges","slices","gaps","doNotOwn","review"}

class PlanError(Exception):
    pass

def require(ok, message):
    if not ok:
        raise PlanError(message)

def validate(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    require(isinstance(data, dict), "root must be an object")
    require(ROOT_KEYS <= set(data), "missing root keys: " + repr(sorted(ROOT_KEYS - set(data))))
    require(data["schemaVersion"] == 1, "schemaVersion must be 1")
    require(data["kind"] == "ordivon.project-lego-plan", "invalid kind")
    require(data["truthRole"] == "planning-projection-not-project-truth", "invalid truthRole")
    project = data["project"]
    require(project.get("id") and project.get("purpose") and project.get("sourceEvidence"), "project id/purpose/sourceEvidence required")
    ids = []
    for node in data["nodes"]:
        for k in ("id","label","kind","responsibility","authority","state","sharedRefs","evidence","mustNotOwn","acceptance"):
            require(k in node, "node missing " + k)
        require(node["state"] in NODE_STATES, "invalid node state " + str(node["state"]))
        if node["state"] in {"IMPLEMENTED","VERIFIED"}:
            require(bool(node["evidence"]), node["id"] + " implemented/verified requires evidence")
        if node["state"] == "VERIFIED":
            require(bool(node["acceptance"]), node["id"] + " verified requires acceptance")
        for ref in node["sharedRefs"]:
            require(isinstance(ref,str) and len(ref)==3 and ref[0]=="L" and ref[1:].isdigit(), "invalid sharedRef " + repr(ref))
        ids.append(node["id"])
    require(len(ids)==len(set(ids)), "node ids must be unique")
    idset=set(ids)
    for edge in data["edges"]:
        require(edge.get("from") in idset and edge.get("to") in idset, "edge references unknown node: " + repr(edge))
        require(edge.get("type") and edge.get("label"), "edge type/label required")
    slice_ids=[]
    active=0
    for sl in data["slices"]:
        for k in ("id","objective","status","nodeIds","acceptance","evidence","blockers"):
            require(k in sl, "slice missing " + k)
        require(sl["status"] in SLICE_STATES, "invalid slice state " + str(sl["status"]))
        require(sl["nodeIds"] and all(n in idset for n in sl["nodeIds"]), "slice references unknown/empty nodes")
        require(bool(sl["acceptance"]), "slice acceptance required")
        if sl["status"]=="COMPLETE":
            require(bool(sl["evidence"]), "complete slice requires evidence")
        if sl["status"]=="ACTIVE":
            active += 1
        slice_ids.append(sl["id"])
    require(len(slice_ids)==len(set(slice_ids)), "slice ids must be unique")
    review=data["review"]
    require(review.get("sourceRevision") and review.get("updatedAt"), "review sourceRevision/updatedAt required")
    require(review.get("standing") in {"INITIAL","ACTIVE","STABLE","DEFERRED"}, "invalid review standing")
    return {"ok":True,"path":str(path),"project":project["id"],"nodes":len(ids),"edges":len(data["edges"]),"slices":len(data["slices"]),"activeSlices":active}

def main():
    if len(sys.argv)<2:
        print("usage: check_project_lego_plan_r1.py PLAN.json [PLAN.json ...]", file=sys.stderr)
        return 2
    failed=False
    for raw in sys.argv[1:]:
        try:
            print(json.dumps(validate(raw), sort_keys=True))
        except Exception as exc:
            failed=True
            print(json.dumps({"ok":False,"path":raw,"error":str(exc)}, sort_keys=True), file=sys.stderr)
    return 1 if failed else 0

if __name__=="__main__":
    raise SystemExit(main())
