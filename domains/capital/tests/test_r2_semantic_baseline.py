from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def test_r1_r2_baseline_freezes_authority_without_widening():
    b=load('planning/r1-r2-semantic-baseline.json')
    assert b['inventory']=={'registryEntries':39,'canonicalEntries':34,'functionalLegos':12,'readOnlyCircuitFamilies':3,'nonLiveEffectScenarios':5}
    assert b['authorityStanding']['executionLane']=='NON_LIVE'
    assert b['authorityStanding']['productionAuthorization']=='BLOCK_NOT_GRANTED'
    assert b['authorityStanding']['externalFinancialWriteAllowed'] is False
    assert b['authorityStanding']['privateAccountDataAdmission']=='NOT_ADMITTED'
    assert b['authorityStanding']['portfolioRiskBudget']=='UNSET'
