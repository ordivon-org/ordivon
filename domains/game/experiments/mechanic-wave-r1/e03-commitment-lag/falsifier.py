#!/usr/bin/env python3
import json
from carrier import SCENARIOS,best_policy,observation
z_total,_,z_policy,z_traces=best_policy(0)
l_total,_,l_policy,l_traces=best_policy(1)
z={t['scenario']:t for t in z_traces}; l={t['scenario']:t for t in l_traces}
different=[sid for sid in z if (z[sid]['first']['action'],z[sid]['recoveryAction'])!=(l[sid]['first']['action'],l[sid]['recoveryAction'])]
higher=[sid for sid in z if l[sid]['totalCost']>z[sid]['totalCost'] or l[sid]['recoverySteps']>z[sid]['recoverySteps']]
same_stale_obs=observation(SCENARIOS[0],1)==observation(SCENARIOS[1],1) and (SCENARIOS[0]['oldState']+SCENARIOS[0]['drift'])!=(SCENARIOS[1]['oldState']+SCENARIOS[1]['drift'])
checks={
 'staleViewAliasesDifferentTrueStates':same_stale_obs,
 'zeroLagAndLaggedOptimalTraceDiffer':bool(different),
 'stalenessChangesRecoveryCostOrPath':bool(higher),
 'laggedOptimalCostStrictlyHigher':l_total>z_total,
 'staleMarkerHistoryDerived':all(t['stale']==(t['first']['observationAge']>0) for t in l_traces+z_traces),
 'allFrozenScenariosRecoverToTarget':all(t['final']==0 for t in l_traces+z_traces)
}
out={'schemaVersion':1,'id':'r1-commitment-lag','checks':checks,'zeroLag':{'policy':z_policy,'totalCost':z_total,'traces':z_traces},'lagged':{'policy':l_policy,'totalCost':l_total,'traces':l_traces},'differentTraceScenarios':different,'higherRecoveryScenarios':higher,'outcome':'KEEP' if all(checks.values()) else 'DELETE','claimCeiling':'mechanical stale-view commitment/recovery consequence only; no Human value claim'}
open('evidence.json','w').write(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); raise SystemExit(0 if out['outcome']=='KEEP' else 3)
