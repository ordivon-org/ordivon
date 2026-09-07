#!/usr/bin/env python3
import json, sys
from collections import Counter
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'ACTIVATED_E2E_SUBGRAPH_R1.json'
j = json.loads(path.read_text())
errors=[]

def fail(msg): errors.append(msg)

nodes=j['nodes']; ids=[n['id'] for n in nodes]; node_ids=set(ids)
if len(ids)!=len(node_ids): fail('duplicate node IDs')
classes=Counter(n['activationClass'] for n in nodes)
if classes != Counter({'CONSTITUTIVE':32,'CLOSURE_CRITICAL_SUPPORT':14}):
    fail(f'unexpected class counts: {dict(classes)}')
fronts=set(j['fronts'])
for n in nodes:
    if n['front'] not in fronts: fail(f"node {n['id']} has unknown front {n['front']}")
    if not n.get('oracle'): fail(f"node {n['id']} missing oracle")
for e in j['edges']:
    if e['from'] not in node_ids: fail(f'dangling edge source {e}')
    if e['to'] not in node_ids: fail(f'dangling edge target {e}')

agents=j['candidateOpeningAgents']
front_owners={}
for agent,fs in agents.items():
    for f in fs:
        if f not in fronts: fail(f'{agent} owns unknown front {f}')
        if f in front_owners: fail(f'front {f} multiply assigned to {front_owners[f]} and {agent}')
        front_owners[f]=agent
missing=sorted(fronts-set(front_owners))
if missing: fail(f'unassigned fronts: {missing}')
extra=sorted(set(front_owners)-fronts)
if extra: fail(f'unknown assigned fronts: {extra}')
if len(agents)!=24: fail(f'opening agent count is {len(agents)}, expected 24')
if agents.get('A23') != ['F25']: fail('A23 must remain dedicated independent Red Team / Product QA')
if 'F25' in agents.get('A24',[]): fail('Rights / Provenance must remain separate from Red Team')
if 'F24' not in agents.get('A21',[]): fail('A21 must own Human protocol/readiness preparation')

# Key semantic dependency guards.
edges={(e['from'],e['to']) for e in j['edges']}
required_edges={
    ('V-G1','V-K1'), ('V-G1','V-V1'), ('V-G2','V-R2'), ('V-G4','V-R3'),
    ('V-V2','V-S2'), ('V-V3','V-V4'), ('V-V4','V-V5'), ('V-S1','V-V6'),
    ('V-S2','V-S1'), ('V-A1','V-A2'), ('V-A2','V-A3'), ('V-C2','V-C3'),
    ('V-C3','V-C4'), ('V-C4','V-R1'), ('V-R1','V-C5'), ('V-C7','V-C8'),
    ('V-C11','V-H2'), ('V-H2','V-G2'), ('V-C1','V-C12')
}
for e in sorted(required_edges-edges): fail(f'missing required semantic edge {e}')

# Explicit dormant anti-scope guards.
for required in ['multiplayer session','online identity/accounts','commerce/IAP','LLM runtime NPCs','giant/open-world streaming']:
    if required not in j['dormantR1']: fail(f'missing dormant scope guard: {required}')

if errors:
    print('VEILWILD_E2E_SUBGRAPH_INVALID')
    for e in errors: print(' -',e)
    sys.exit(1)
print('VEILWILD_E2E_SUBGRAPH_VALID')
print('active_nodes=',len(nodes))
print('constitutive=',classes['CONSTITUTIVE'])
print('closure_critical_support=',classes['CLOSURE_CRITICAL_SUPPORT'])
print('edges=',len(j['edges']))
print('fronts=',len(fronts))
print('opening_agents=',len(agents))
print('pressure_triggered=',len(j['pressureTriggered']))
print('dormant_r1=',len(j['dormantR1']))
print('cross_cutting_planes=',len(j['crossCuttingPlanes']))
