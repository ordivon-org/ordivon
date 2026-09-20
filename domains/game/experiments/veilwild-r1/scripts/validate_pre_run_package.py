#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; errors=[]
def fail(x): errors.append(x)
files=['ACTIVATED_E2E_SUBGRAPH_R1.json','AGENT_HANDOFF_SCHEMA_R1.json','AGENT_ROLE_CARDS_R1.json','AGENT_ROLE_INDEX_R1.json','TOPOLOGY_FALSIFICATION_REVIEWERS_R1.json']
objs={}
for f in files:
    try: objs[f]=json.loads((root/f).read_text())
    except Exception as e: fail(f'{f}: {e}')
if errors:
    print('VEILWILD_PRE_RUN_PACKAGE_INVALID'); [print(' -',e) for e in errors]; sys.exit(1)
j=objs['ACTIVATED_E2E_SUBGRAPH_R1.json']; nodes=j['nodes']; node_by={n['id']:n for n in nodes}; fronts=j['fronts']; agents=j['candidateOpeningAgents']
if (len(nodes),len(fronts),len(agents))!=(46,27,25): fail('topology headline counts mismatch')
agg=objs['AGENT_ROLE_CARDS_R1.json']; idx=objs['AGENT_ROLE_INDEX_R1.json']['roles']
if agg.get('authority')!='COORDINATOR_AND_TOPOLOGY_REVIEW_ONLY_BEFORE_FIRST_VERDICT_FREEZE': fail('aggregate role-card authority guard missing')
front_owner={}; closure_owner={}
for aid,fs in agents.items():
    rp=root/'roles'/f'{aid}.json'
    if not rp.exists(): fail(f'missing isolated role {aid}'); continue
    card=json.loads(rp.read_text())['role']
    if card['agentId']!=aid: fail(f'role id mismatch {aid}')
    actual=[x['id'] for x in card['fronts']]
    if actual!=fs: fail(f'front mismatch {aid}: {actual} != {fs}')
    if idx.get(aid,{}).get('fronts')!=fs: fail(f'index mismatch {aid}')
    for f in fs:
        if f in front_owner: fail(f'duplicate front owner {f}')
        front_owner[f]=aid
    expected=sorted(n['id'] for n in nodes if n['front'] in fs); actualc=sorted(c['id'] for c in card.get('ownedClosures',[]))
    if actualc!=expected: fail(f'closure ownership mismatch {aid}: {actualc} != {expected}')
    for c in actualc:
        if c in closure_owner: fail(f'duplicate closure owner {c}')
        closure_owner[c]=aid
if set(front_owner)!=set(fronts): fail(f'front coverage missing {sorted(set(fronts)-set(front_owner))}')
if set(closure_owner)!=set(node_by): fail(f'closure coverage missing {sorted(set(node_by)-set(closure_owner))}')
if front_owner.get('F25')!='A23' or front_owner.get('F18')!='A25' or front_owner.get('F17')!='A17': fail('critical owner separation failed')
if node_by.get('V-H1',{}).get('front')!='F02' or node_by.get('V-G7',{}).get('front')!='F02': fail('player semantics ownership failed')
if 'V-C1' in node_by: fail('V-C1 must remain absent')
hs=objs['AGENT_HANDOFF_SCHEMA_R1.json']; pat=hs['properties']['agentId']['pattern']
if '2[0-5]' not in pat: fail('handoff agentId pattern does not admit A25')
human=hs['properties']['humanClaims']['properties']
for k in ['fun','immersion','believability','detectability','cueUsefulness','fairness','comprehension']:
    if human.get(k,{}).get('const')!='UNKNOWN': fail(f'Human UNKNOWN guard missing {k}')
for required_surface in ['boardCollaboration','workstationUse','frictionReceipts']:
    if required_surface not in hs.get('required',[]): fail(f'handoff required surface missing {required_surface}')
board=hs['properties'].get('boardCollaboration',{})
if board.get('properties',{}).get('topic',{}).get('const')!='game-e2e:veilwild-r1:production-r1': fail('Board topic guard missing')
if board.get('properties',{}).get('rootClientMessageId',{}).get('const')!='veilwild-r1-production-r1-board-root-859e3ac': fail('Board root guard missing')
if board.get('properties',{}).get('firstVerdictFrozenBeforePeerRead',{}).get('const') is not True: fail('Board independence guard missing')
fr=hs['properties'].get('frictionReceipts',{})
frreq=set(fr.get('items',{}).get('required',[]))
for k in ['frictionId','category','surface','observedConsequence','exactCondition','workaroundOrResolution','ownerRoute','severity','reusableLesson']:
    if k not in frreq: fail(f'friction receipt missing required field {k}')
for required_surface in ['roundContext','externalEvaluation']:
    if required_surface not in hs.get('required',[]): fail(f'handoff required surface missing {required_surface}')
roundctx=hs['properties'].get('roundContext',{})
for k in ['roundId','roundInputRevision','pressureSources','materialDelta','nextRoundRecommendation']:
    if k not in set(roundctx.get('required',[])): fail(f'roundContext missing required field {k}')
ext=hs['properties'].get('externalEvaluation',{})
extreq=set(ext.get('items',{}).get('required',[]))
for k in ['reference','authorityClass','applicability','criterionUsed','standing','exactCondition','evidenceOrRationale']:
    if k not in extreq: fail(f'externalEvaluation missing required field {k}')
sp=hs['properties'].get('scopePressureProposals',{})
req={'blockedActiveClosure','exactCandidateOrCondition','failingOracle','attemptedExistingCarrier','whyExistingCarrierIsInsufficient','proposedCapability','stableInput','stableOutput','distinctFailureModes','distinctOracle','proposedOwnerOrFront','scopeDelta','revertOrStopCondition'}
if not req.issubset(set(sp.get('items',{}).get('required',[]))): fail('scopePressureProposals schema incomplete')
for aid in sorted(agents):
    cp=subprocess.run([sys.executable,str(root/'scripts/generate_agent_prompt.py'),aid,'--baseline','POST_CONVERGENCE_TEST'],capture_output=True,text=True)
    if cp.returncode!=0: fail(f'prompt generation failed {aid}: {cp.stderr}'); continue
    t=cp.stdout
    for need in [f'AGENT_ID = {aid}',f'roles/{aid}.json','Independence before first verdict','Human boundary','POST_CONVERGENCE_TEST','10. Board collaboration','11. Workstation professional software','12. Friction receipts','game-e2e:veilwild-r1:production-r1','13. External standards and multi-round campaign','EXTERNAL_STANDARDS_AND_MULTI_ROUND_PROTOCOL_R1.md']:
        if need not in t: fail(f'prompt {aid} missing {need}')
    if 'Read:\n- experiments/veilwild-r1/AGENT_ROLE_CARDS_R1.json' in t: fail(f'{aid} instructed to read aggregate role cards')
revs=objs['TOPOLOGY_FALSIFICATION_REVIEWERS_R1.json']['reviewers']
if set(revs)!={'TA','TB','TC','TD','TE','TF'}: fail('topology reviewer set drift')
for rid in revs:
    cp=subprocess.run([sys.executable,str(root/'scripts/generate_topology_review_prompt.py'),rid,'--baseline','80822fa'],capture_output=True,text=True)
    if cp.returncode!=0 or 'FIRST_RECOMMENDATION' not in cp.stdout: fail(f'topology reviewer prompt broken {rid}')
if errors:
    print('VEILWILD_PRE_RUN_PACKAGE_INVALID'); [print(' -',e) for e in errors]; sys.exit(1)
print('VEILWILD_PRE_RUN_PACKAGE_VALID')
print('active_e2e=46 fronts=27 opening_agents=25 isolated_role_cards=25 topology_reviewers=6')
print('closure_coverage=46/46 human_unknown_guards=7 scope_pressure_schema=present board_contract=present workstation_friction_contract=present multiround_contract=present external_standards_contract=present')
