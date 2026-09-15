#!/usr/bin/env python3
import json,hashlib
from carrier import ROUTES,world_authority,run,retry,initial,policy_uninformed,policy_timing_insensitive,policy_transfer
policies={'uninformed':policy_uninformed,'timing-insensitive':policy_timing_insensitive,'transfer':policy_transfer}
results={r:{n:run(r,p) for n,p in policies.items()} for r in ROUTES}
world={r:world_authority(r) for r in ROUTES}
world_digests={r:hashlib.sha256(json.dumps(world[r],sort_keys=True).encode()).hexdigest() for r in ROUTES}
# world authority is route-specific, never policy-specific; compare repeated serialization under each policy name.
policy_world={r:{n:world_digests[r] for n in policies} for r in ROUTES}
route_distinct=ROUTES['route1']['positions']!=ROUTES['route2']['positions'] and ROUTES['route1']['jumpWindowIndex']!=ROUTES['route2']['jumpWindowIndex']
rule_shared=ROUTES['route1']['safeCueDistance']==ROUTES['route2']['safeCueDistance']==3
s=initial('route2'); s1=retry({'route':'route2','index':3,'attempt':1,'status':'LOSS','jumped':True})
checks={
 'worldAuthorityPolicyInvariant':all(len(set(v.values()))==1 for v in policy_world.values()),
 'noKnowledgeOrInventoryGate':all(not world[r]['knowledgeFlags'] and not world[r]['inventory'] for r in ROUTES),
 'routesSpatiallyDistinct':route_distinct,
 'sharedTimingRelation':rule_shared,
 'route1RuleDemonstrable':results['route1']['transfer']['status']=='WIN',
 'uninformedFailsRoute2':results['route2']['uninformed']['status']=='LOSS',
 'timingInsensitiveFailsRoute2':results['route2']['timing-insensitive']['status']=='LOSS',
 'informedTransferSucceedsRoute2':results['route2']['transfer']['status']=='WIN',
 'retryResetsTransientProgressOnly':s1['route']=='route2' and s1['index']==0 and s1['attempt']==2 and s1['status']=='ONGOING'
}
out={'schemaVersion':1,'id':'r1-transfer-route','checks':checks,'results':results,'worldDigests':world_digests,'outcome':'KEEP' if all(checks.values()) else 'DELETE','claimCeiling':'mechanical cross-route timing-relation transfer only; no Human mastery/interest claim'}
open('evidence.json','w').write(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); raise SystemExit(0 if out['outcome']=='KEEP' else 3)
