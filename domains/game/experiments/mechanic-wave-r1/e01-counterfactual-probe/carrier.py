#!/usr/bin/env python3
from __future__ import annotations

FAULTS=("source","process","route")
CORRECTIONS=("repair-source","repair-process","repair-route")
INSPECTIONS=("inspect-input","inspect-flow")
PRIOR={"source":0.34,"process":0.33,"route":0.33}

# deliberately coarse: each inspection isolates one fault and leaves the negative result ambiguous.
def observe(fault:str, inspection:str|None)->str:
    if inspection is None: return "symptom:throughput-low"
    if inspection=="inspect-input": return "fault" if fault=="source" else "ok"
    if inspection=="inspect-flow": return "fault" if fault=="process" else "ok"
    raise ValueError(inspection)

def reward(fault:str, correction:str)->int:
    target={"source":"repair-source","process":"repair-process","route":"repair-route"}[fault]
    return 10 if correction==target else -6

def expected_reward(policy, inspection=None):
    total=0.0
    for f,p in PRIOR.items(): total += p*reward(f, policy(observe(f,inspection)))
    if inspection is not None: total -= 1.0
    return total

def best_policy(inspection=None):
    observations=sorted({observe(f,inspection) for f in FAULTS})
    mapping={}
    for o in observations:
        members=[f for f in FAULTS if observe(f,inspection)==o]
        mass=sum(PRIOR[f] for f in members)
        mapping[o]=max(CORRECTIONS,key=lambda c:sum(PRIOR[f]/mass*reward(f,c) for f in members))
    return mapping, expected_reward(lambda o:mapping[o],inspection)

def play(fault:str, inspection:str|None, correction:str):
    return {"fault":fault,"observation":observe(fault,inspection),"correction":correction,"reward":reward(fault,correction),"inspectionCost":1 if inspection else 0}

if __name__=='__main__':
    import argparse,json
    ap=argparse.ArgumentParser(); ap.add_argument('fault',choices=FAULTS); ap.add_argument('--inspect',choices=INSPECTIONS); ap.add_argument('--correct',choices=CORRECTIONS,required=True)
    a=ap.parse_args(); print(json.dumps(play(a.fault,a.inspect,a.correct),sort_keys=True))
