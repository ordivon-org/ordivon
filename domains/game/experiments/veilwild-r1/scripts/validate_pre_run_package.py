#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
errors=[]
def fail(x): errors.append(x)
# Core JSONs
files=['ACTIVATED_E2E_SUBGRAPH_R1.json','AGENT_HANDOFF_SCHEMA_R1.json','AGENT_ROLE_CARDS_R1.json','AGENT_ROLE_INDEX_R1.json','TOPOLOGY_FALSIFICATION_REVIEWERS_R1.json']
objs={}
for f in files:
    try: objs[f]=json.loads((root/f).read_text())
    except Exception as e: fail(f'{f}: invalid JSON: {e}')
if errors:
    print('\n'.join(errors)); sys.exit(1)
j=objs['ACTIVATED_E2E_SUBGRAPH_R1.json']
# topology invariants
if len(j['nodes'])!=46: fail('active node count !=46')
if len(j['fronts'])!=27: fail('front count !=27')
if len(j['candidateOpeningAgents'])!=24: fail('agent count !=24')
allowed_edge_types={'PRODUCTION_OR_SEMANTIC_DEPENDENCY','VALIDATION_INPUT','ADMISSION_INPUT','FEEDBACK_OR_EVIDENCE_UPDATE','SUPPORTS_OR_REPAIRS'}
for e in j['edges']:
    if e.get('edgeType') not in allowed_edge_types: fail(f'bad edge type {e}')
for phase in ['phase0','phase1','phase2a','phase2b','phase2c','phase2d','phase3','phase4','phase5','phase6']:
    if phase not in j.get('executionProtocol',{}): fail(f'missing execution phase {phase}')
# Role isolation and exact coverage
idx=objs['AGENT_ROLE_INDEX_R1.json']['roles']; agg=objs['AGENT_ROLE_CARDS_R1.json']
if agg.get('authority')!='COORDINATOR_AND_TOPOLOGY_REVIEW_ONLY_BEFORE_FIRST_VERDICT_FREEZE': fail('aggregate role cards missing authority guard')
front_owner={}
for aid in sorted(j['candidateOpeningAgents']):
    rp=root/'roles'/f'{aid}.json'
    if not rp.exists(): fail(f'missing isolated role card {aid}'); continue
    card=json.loads(rp.read_text())['role']
    if card['agentId']!=aid: fail(f'role id mismatch {aid}')
    expected=j['candidateOpeningAgents'][aid]
    actual=[f['id'] for f in card['fronts']]
    if expected!=actual: fail(f'front mismatch {aid}: {actual} vs {expected}')
    if idx.get(aid,{}).get('fronts')!=expected: fail(f'index mismatch {aid}')
    for f in actual:
        if f in front_owner: fail(f'front {f} duplicate owners')
        front_owner[f]=aid
if set(front_owner)!=set(j['fronts']): fail(f'front coverage mismatch missing={sorted(set(j["fronts"])-set(front_owner))}')
if front_owner.get('F25')!='A23': fail('F25 Red Team must be A23')
if 'F25' in j['candidateOpeningAgents']['A24']: fail('A24 must not own Red Team')
# Prompt generation for all 24; ensure own role only and guards are present.
for aid in sorted(j['candidateOpeningAgents']):
    cp=subprocess.run([sys.executable,str(root/'scripts/generate_agent_prompt.py'),aid,'--baseline','PREP_FREEZE_TEST'],capture_output=True,text=True)
    if cp.returncode!=0: fail(f'prompt generator failed {aid}: {cp.stderr}') ; continue
    t=cp.stdout
    for required in [f'AGENT_ID = {aid}','PREP_FREEZE_TEST','Independence before first verdict','Human boundary',f'roles/{aid}.json']:
        if required not in t: fail(f'prompt {aid} missing {required}')
    if 'Read:\n- experiments/veilwild-r1/AGENT_ROLE_CARDS_R1.json' in t: fail(f'prompt {aid} improperly asks to read aggregate role cards')
# Topology reviewer generation
revs=objs['TOPOLOGY_FALSIFICATION_REVIEWERS_R1.json']['reviewers']
if set(revs)!=set(['TA','TB','TC','TD','TE','TF']): fail('topology reviewers not TA-TF')
for rid in revs:
    cp=subprocess.run([sys.executable,str(root/'scripts/generate_topology_review_prompt.py'),rid,'--baseline','PREP_FREEZE_TEST'],capture_output=True,text=True)
    if cp.returncode!=0 or rid not in cp.stdout or 'FIRST_RECOMMENDATION' not in cp.stdout: fail(f'topology prompt failure {rid}')
# Handoff schema Human UNKNOWN guard
props=objs['AGENT_HANDOFF_SCHEMA_R1.json']['properties']['humanClaims']['properties']
for k in ['fun','immersion','believability','detectability','cueUsefulness','fairness']:
    if props.get(k,{}).get('const')!='UNKNOWN': fail(f'human guard missing {k}')
if errors:
    print('VEILWILD_PRE_RUN_PACKAGE_INVALID')
    for e in errors: print(' -',e)
    sys.exit(1)
print('VEILWILD_PRE_RUN_PACKAGE_VALID')
print('active_e2e=46 fronts=27 opening_agents=24 topology_reviewers=6')
print('isolated_role_cards=24 typed_edges=',len(j['edges']))
print('execution_phases=',len(j['executionProtocol']))
