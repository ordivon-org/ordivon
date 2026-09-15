#!/usr/bin/env python3
import json
from carrier import FAULTS,CORRECTIONS,INSPECTIONS,reward,best_policy,observe
unique={f:[c for c in CORRECTIONS if reward(f,c)==max(reward(f,x) for x in CORRECTIONS)] for f in FAULTS}
no_map,no_value=best_policy(None)
inspect=[]
for ins in INSPECTIONS:
    mapping,value=best_policy(ins)
    groups={o:sorted(f for f in FAULTS if observe(f,ins)==o) for o in sorted({observe(f,ins) for f in FAULTS})}
    inspect.append({'inspection':ins,'mapping':mapping,'value':value,'groups':groups})
best=max(inspect,key=lambda x:x['value'])
single_success={c:sum(1 for f in FAULTS if reward(f,c)>0) for c in CORRECTIONS}
checks={
 'uniqueOptimalCorrectionPerFault':all(len(v)==1 for v in unique.values()) and len({v[0] for v in unique.values()})==len(FAULTS),
 'inspectionCreatesActionRelevantPartition':any(len(set(x['mapping'].values()))>=2 for x in inspect),
 'inspectionStrictlyImprovesExpectedReward':best['value']>no_value,
 'noUniversalCorrection':max(single_success.values())<len(FAULTS),
 'negativeObservationRemainsAmbiguous':all(any(len(g)>=2 for o,g in x['groups'].items() if o=='ok') for x in inspect)
}
out={'schemaVersion':1,'id':'r1-counterfactual-probe','checks':checks,'noInspection':{'mapping':no_map,'value':no_value},'bestInspection':best,'allInspections':inspect,'singleCorrectionSuccessCounts':single_success,'outcome':'KEEP' if all(checks.values()) else 'DELETE','claimCeiling':'mechanical counterfactual-probe consequence only; no Human interest claim'}
open('evidence.json','w').write(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); raise SystemExit(0 if out['outcome']=='KEEP' else 3)
