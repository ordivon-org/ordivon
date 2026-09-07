#!/usr/bin/env python3
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('reviewer_id'); p.add_argument('--baseline',required=True); a=p.parse_args()
root=Path(__file__).resolve().parents[1]
r=json.loads((root/'TOPOLOGY_FALSIFICATION_REVIEWERS_R1.json').read_text())['reviewers']
if a.reviewer_id not in r: raise SystemExit('unknown reviewer')
c=r[a.reviewer_id]
print(f"{a.reviewer_id}\nOrdivon Game E2E — Veilwild R1 Pre-Run Topology Falsification\n\nEXACT_BASELINE = {a.baseline}\n\nRole: {c['name']}\n\n{c['mission']}\n")
print('Before freezing your first recommendation, do not read another current-round TA-TF report, verdict, scratchpad, Coordinator synthesis, or A01-A24 production result. Do not read the single-Agent prototype commits after the clean campaign baseline.')
print('\nRead the common Game/Veilwild design, ACTIVATED_E2E_SUBGRAPH_R1.md/.json, MULTI_AGENT_EXECUTION_PROTOCOL_R1.md, AGENT_HANDOFF_SCHEMA_R1.json, AGENT_ROLE_CARDS_R1.json, and TOPOLOGY_FALSIFICATION_GATE_R1.md.')
print('\nFocus:')
for x in c['focus']: print('- '+x)
print('\nFreeze FIRST_RECOMMENDATION = ACCEPT_TOPOLOGY / ACCEPT_WITH_REPAIRS / REJECT_TOPOLOGY, then provide TOP_5_FALSIFIERS, MISSING_E2ES, OVER_SPLIT_E2ES, OVER_MERGED_E2ES, BAD_AGENT_BUNDLES, BAD_INDEPENDENCE_BOUNDARIES, DORMANT/PRESSURE_TRIGGER_ERRORS, and REQUIRED_REPAIRS_BEFORE_LAUNCH.')
print('\nYou are a topology reviewer, not a product producer. Do not implement Veilwild content in this review.')
