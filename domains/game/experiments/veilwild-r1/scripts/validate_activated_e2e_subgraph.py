#!/usr/bin/env python3
import json,sys
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parents[1]
j=json.loads((root/'ACTIVATED_E2E_SUBGRAPH_R1.json').read_text())
errors=[]
def fail(x): errors.append(x)
nodes=j['nodes']; ids=[n['id'] for n in nodes]; byid={n['id']:n for n in nodes}
if len(ids)!=46: fail(f'active node count {len(ids)} != 46')
if len(ids)!=len(set(ids)): fail('duplicate node IDs')
classes=Counter(n['activationClass'] for n in nodes)
if classes!=Counter({'CONSTITUTIVE':33,'CLOSURE_CRITICAL_SUPPORT':13}): fail(f'bad class counts {dict(classes)}')
if 'V-C1' in byid: fail('generic V-C1 Asset Authoring must not be an independent closure')
for cid,front in [('V-G7','F02'),('V-H1','F02'),('V-H2','F24')]:
    if byid.get(cid,{}).get('front')!=front: fail(f'{cid} must be on {front}')
if byid.get('V-G7',{}).get('activationClass')!='CONSTITUTIVE': fail('V-G7 must be constitutive')
if byid.get('V-H2',{}).get('name')!='Player Evidence / Human Playtest': fail('V-H2 naming/closure guard drift')
fronts=j['fronts']
if len(fronts)!=27: fail(f'front count {len(fronts)} != 27')
for n in nodes:
    if n['front'] not in fronts: fail(f"{n['id']} unknown front {n['front']}")
    if not n.get('oracle'): fail(f"{n['id']} missing oracle")
edge_types={'PRODUCTION_OR_SEMANTIC_DEPENDENCY','VALIDATION_INPUT','ADMISSION_INPUT','FEEDBACK_OR_EVIDENCE_UPDATE','SUPPORTS_OR_REPAIRS'}
edges={(e['from'],e['to'],e.get('edgeType')) for e in j['edges']}
for a,b,t in edges:
    if a not in byid or b not in byid: fail(f'dangling edge {a}->{b}')
    if t not in edge_types: fail(f'bad edge type {t} on {a}->{b}')
required={('V-G2','V-G7'),('V-G3','V-G7'),('V-G7','V-V5'),('V-G7','V-V9'),('V-G7','V-A1'),('V-G7','V-R4'),('V-G7','V-R5'),('V-G7','V-C10'),('V-V2','V-C2'),('V-V3','V-C2'),('V-V4','V-C2'),('V-V5','V-C2'),('V-V7','V-C2'),('V-A1','V-C2'),('V-C2','V-C3'),('V-C3','V-C4'),('V-C4','V-R1'),('V-C11','V-H2'),('V-H2','V-G2')}
pairs={(a,b) for a,b,_ in edges}
for e in sorted(required-pairs): fail(f'missing required semantic edge {e}')
ag=j['candidateOpeningAgents']
if len(ag)!=25: fail(f'opening agent count {len(ag)} != 25')
front_owner={}
for aid,fs in ag.items():
    for f in fs:
        if f not in fronts: fail(f'{aid} owns unknown front {f}')
        if f in front_owner: fail(f'{f} multiply owned by {front_owner[f]} and {aid}')
        front_owner[f]=aid
if set(front_owner)!=set(fronts): fail(f'front coverage mismatch missing={sorted(set(fronts)-set(front_owner))}')
if ag.get('A17')!=['F17']: fail(f'A17 must own only F17, got {ag.get("A17")}')
if ag.get('A25')!=['F18']: fail(f'A25 must own only F18, got {ag.get("A25")}')
if ag.get('A23')!=['F25']: fail('A23 must remain dedicated F25 Red Team')
if len(j.get('pressureTriggered',[]))!=7: fail('pressure-triggered new-E2E count must be 7')
if len(j.get('implementationEscalations',[]))!=5: fail('implementation escalation count must be 5')
for x in j.get('pressureTriggered',[]):
    for k in ['name','trigger','blockedActiveClosures','admissionOracle','ownerRoute']:
        if not x.get(k): fail(f'pressure entry {x.get("name")} missing {k}')
for x in j.get('implementationEscalations',[]):
    for k in ['name','withinClosures','trigger','rule']:
        if not x.get(k): fail(f'escalation {x.get("name")} missing {k}')
scp=j.get('scopeChangeProtocol',{})
if not scp.get('unilateralActivationProhibited'): fail('unilateral topology activation must be prohibited')
if len(scp.get('proposalReceiptRequiredFields',[]))<10: fail('scope-pressure receipt is under-specified')
if len(j.get('crossCuttingPlanes',[]))!=7: fail('cross-cutting planes must remain 7')
if 'Authority / Admission / Cross-Owner Boundary' not in j.get('crossCuttingPlanes',[]): fail('P2 cross-owner authority semantics missing')
for d in ['multiplayer session','online identity/accounts','commerce/IAP','LLM runtime NPCs','giant/open-world streaming']:
    if d not in j['dormantR1']: fail(f'dormant guard missing {d}')
for ph in ['phase0','phase1','phase2a','phase2b','phase2c','phase2d','phase3','phase4','phase5','phase6']:
    if ph not in j.get('executionProtocol',{}): fail(f'missing phase {ph}')
if errors:
    print('VEILWILD_E2E_SUBGRAPH_INVALID'); [print(' -',e) for e in errors]; sys.exit(1)
print('VEILWILD_E2E_SUBGRAPH_VALID')
print('active_nodes=46 constitutive=33 support=13 edges=',len(j['edges']))
print('fronts=27 opening_agents=25 pressure_triggered=7 implementation_escalations=5 dormant=',len(j['dormantR1']),'planes=7')
