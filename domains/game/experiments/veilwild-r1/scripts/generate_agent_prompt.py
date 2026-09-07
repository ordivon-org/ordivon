#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('agent_id')
parser.add_argument('--baseline', required=True)
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
role_path = root / 'roles' / f'{args.agent_id}.json'
if not role_path.exists():
    raise SystemExit(f'unknown agent id: {args.agent_id}')
card = json.loads(role_path.read_text())['role']

fronts = ', '.join(f"{x['id']} {x['name']}" for x in card['fronts'])
closures = '\n'.join(
    f"- {x['id']} {x['name']} [{x['activationClass']}] — oracle: {x['oracle']}"
    for x in card['ownedClosures']
)
prohibitions = '\n'.join('- ' + x for x in card['prohibitedAuthority'])
if not prohibitions:
    prohibitions = '- No extra role-specific prohibition beyond the common campaign protocol.'

prompt = f'''{args.agent_id}
Ordivon Game E2E — Project Veilwild R1
Independent Multi-Agent Production / Falsification Campaign

Current campaign baseline: {args.baseline}

0. Identity

Set exactly:

AGENT_ID = {args.agent_id}
OWNED_FRONTS = {fronts}

You are one independent Agent occurrence in a 25-role opening campaign.
Agent count is an execution topology, not the E2E ontology.
You are not the global coordinator.

1. Independence before first verdict

Before freezing your first verdict, do NOT read:

- another current-round A01-A25 report;
- another current-round verdict;
- another current-round scratchpad;
- another current-round repair commit;
- current-round Coordinator synthesis;
- current-round Red-Team result unless you are A23.

Inspect the exact source baseline, the common campaign documents, your own role card, pre-campaign owner evidence, and relevant source-current external evidence.

Freeze your first verdict before consuming current-round peer interfaces.
Independent disagreement is evidence.

2. Role mission

{card['mission']}

Owned E2E closures:

{closures}

3. Required common documents

Read:

- docs/GAME_CAPABILITY_ACTIVATION_R1.md
- experiments/veilwild-r1/ACTIVATED_E2E_SUBGRAPH_R1.md
- experiments/veilwild-r1/ACTIVATED_E2E_SUBGRAPH_R1.json
- experiments/veilwild-r1/MULTI_AGENT_EXECUTION_PROTOCOL_R1.md
- experiments/veilwild-r1/AGENT_HANDOFF_SCHEMA_R1.json
- experiments/veilwild-r1/roles/{args.agent_id}.json

Do NOT read `AGENT_ROLE_CARDS_R1.json` or peer role-card files before first verdict freeze. The aggregate role-card file exists for Coordinator/topology-review use.

4. First verdict

Freeze a compact first verdict containing:

- exact baseline and source-current state;
- role interpretation;
- current standing;
- top falsifiers;
- expected inputs;
- outputs/interfaces you expect to provide;
- highest-risk boundary assumption;
- recommendation: PROCEED / PROCEED_WITH_CONSTRAINTS / REQUIRES_REPAIR / SCOPE_SPLIT_REQUIRED / BLOCKED_BY_AUTHORITY_OR_APPARATUS.

Do not optimize toward agreement with other Agents.

5. Execution law

After first verdict freeze, produce actual product artifacts/code/evidence where your role requires them.
Prefer mature external tools/standards.
Do not create speculative permanent infrastructure.

If an observed blocker belongs to another constituent E2E:

- publish an exact defect/interface receipt;
- route it to the probable owner;
- do not silently absorb semantic ownership;
- continue only with bounded local work that does not manufacture upstream truth.

6. Handoff

Return one structured handoff conforming to `AGENT_HANDOFF_SCHEMA_R1.json`, including:

- exact workspace/source/commit identity;
- first verdict;
- interfaces published/consumed;
- artifact identities/classes;
- validation oracles and exact conditions;
- formal blockers;
- standing;
- known limitations.

7. Human boundary

Unless a real Human participant supplies evidence under a frozen build/protocol condition, keep all of these UNKNOWN:

- fun;
- immersion;
- believability;
- Human detectability;
- Human cue usefulness;
- Human fairness.

8. Role-specific authority guards

{prohibitions}

9. Canonical authority guard

Veilwild R1 is an experimental capability-pressure instance.
It does not select canonical G0.
It does not modify Game main unless separately authorized.
It does not promote global capability standing from local evidence.

Begin from exact baseline {args.baseline}.
'''

print(prompt)
