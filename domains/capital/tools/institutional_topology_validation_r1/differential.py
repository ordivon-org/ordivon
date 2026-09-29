from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import jsonschema

from ordivon_capital.governance.institutional_topology import (
    validate_office_assignment_shape,
    validate_office_role_document,
    validate_office_verdict_shape,
    validate_review_topology_document,
)

ROOT=Path(__file__).resolve().parents[2]
EX=ROOT/'planning/r3/examples'
REGISTRY=json.loads((ROOT/'config/capital_office_registry.json').read_text())
SEED=20260929
CASES=1500

def paths(v,p=()):
    out=[p]
    if isinstance(v,dict):
        for k,c in v.items(): out+=paths(c,p+(k,))
    elif isinstance(v,list):
        for i,c in enumerate(v): out+=paths(c,p+(i,))
    return out

def get(v,p):
    for x in p: v=v[x]
    return v

def setv(v,p,x):
    if not p:return x
    c=v
    for q in p[:-1]: c=c[q]
    c[p[-1]]=x; return v

def delete(v,p):
    if not p:return None
    c=v
    for q in p[:-1]: c=c[q]
    q=p[-1]
    if isinstance(c,dict):c.pop(q,None)
    elif isinstance(c,list) and isinstance(q,int) and q<len(c):c.pop(q)
    return v

def mutate(base,rng,i):
    v=copy.deepcopy(base); p=rng.choice(paths(v)); c=get(v,p); op=i%8
    if op==0:return delete(v,p)
    if op==1:
        if isinstance(c,dict): c['__unexpected__']=True; return v
        return setv(v,p,{'__unexpected__':True})
    if op==2:
        if isinstance(c,list): c.append(copy.deepcopy(c[0]) if c else '__unexpected__'); return v
        return setv(v,p,[copy.deepcopy(c),copy.deepcopy(c)])
    if op==3:
        if isinstance(c,bool):return setv(v,p,not c)
        if isinstance(c,(int,float)) and not isinstance(c,bool):return setv(v,p,'not-a-number')
        if isinstance(c,str):return setv(v,p,'')
        return setv(v,p,False)
    if op==4:return setv(v,p,None)
    if op==5:
        if isinstance(c,str):return setv(v,p,c+'__MUTATED__')
        if isinstance(c,list):return setv(v,p,[])
        if isinstance(c,dict):return setv(v,p,{})
        return setv(v,p,'__MUTATED__')
    if op==6:
        if isinstance(c,str):return setv(v,p,'2026-09-29')
        if isinstance(c,bool):return setv(v,p,1)
        return setv(v,p,'bad value with spaces')
    if isinstance(c,dict):
        ks=list(c)
        if ks:c[ks[0]]=copy.deepcopy(c[ks[-1]])
        return v
    if isinstance(c,list):rng.shuffle(c);return v
    if isinstance(c,str):return setv(v,p,c.upper())
    return v

def local(fn,doc):
    try:fn(doc);return True
    except (ValueError,TypeError,KeyError):return False

def run(label,schema,example,fn,offset):
    sch=json.loads((ROOT/'schema'/schema).read_text()); base=json.loads((EX/example).read_text())
    oracle=jsonschema.Draft202012Validator(sch,format_checker=jsonschema.FormatChecker())
    if not oracle.is_valid(base) or not local(fn,base):raise RuntimeError(f'base rejected: {label}')
    rng=random.Random(SEED+offset); mism=[]
    for i in range(CASES):
        case=mutate(base,rng,i); a=oracle.is_valid(case); b=local(fn,case)
        if a!=b and len(mism)<20:mism.append({'case':i,'oracleValid':a,'localValid':b,'document':case})
    return {'label':label,'cases':CASES,'mismatchCount':len(mism),'mismatches':mism}

def main():
    rows=[
      run('office-role','capital-office-role-v1.schema.json','office-role-risk-example.json',validate_office_role_document,1),
      run('office-assignment','capital-office-assignment-v1.schema.json','office-assignment-risk-example.json',validate_office_assignment_shape,2),
      run('office-verdict','capital-office-verdict-v1.schema.json','office-verdict-risk-example.json',validate_office_verdict_shape,3),
      run('review-topology','capital-review-topology-v1.schema.json','review-topology-example.json',validate_review_topology_document,4),
    ]
    mism=sum(x['mismatchCount'] for x in rows); result={'schemaVersion':1,'kind':'ordivon.capital.r3-w3-validator-differential','seed':SEED,'totalCases':CASES*4,'mismatches':mism,'contracts':rows,'standing':'PASS_ZERO_MISMATCH' if mism==0 else 'FAIL_MISMATCH'}
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if mism==0 else 1
if __name__=='__main__':raise SystemExit(main())
