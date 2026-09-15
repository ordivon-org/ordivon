#!/usr/bin/env python3
from __future__ import annotations
import itertools,json
ACTIONS=(-1,0,1)
SCENARIOS=(
 {'id':'drift-up','oldState':0,'drift':1},
 {'id':'drift-down','oldState':0,'drift':-1},
 {'id':'steady-high','oldState':1,'drift':0},
)
TARGET=0

def observation(scenario,lag):
    if lag==0: return scenario['oldState']+scenario['drift']
    if lag==1: return scenario['oldState']
    raise ValueError(lag)

def resolve_first(scenario,lag,action):
    true_before=scenario['oldState']+scenario['drift']; obs=observation(scenario,lag); after=true_before+action
    cost=abs(after-TARGET)+0.25*abs(action)
    return {'observation':obs,'observationAge':lag,'trueBefore':true_before,'action':action,'after':after,'stepCost':cost}

def recovery_action(state):
    if state>TARGET: return -1
    if state<TARGET: return 1
    return 0

def run(scenario,lag,policy):
    obs=observation(scenario,lag); a1=policy[obs]; first=resolve_first(scenario,lag,a1); a2=recovery_action(first['after']); final=first['after']+a2
    repair_cost=abs(final-TARGET)+0.25*abs(a2)
    return {'scenario':scenario['id'],'lag':lag,'stale':lag>0,'first':first,'recoveryAction':a2,'final':final,'totalCost':first['stepCost']+repair_cost,'recoverySteps':int(a2!=0)}

def policy_space(lag):
    obs=sorted({observation(s,lag) for s in SCENARIOS})
    for acts in itertools.product(ACTIONS,repeat=len(obs)): yield dict(zip(obs,acts))
def best_policy(lag):
    scored=[]
    for p in policy_space(lag):
        traces=[run(s,lag,p) for s in SCENARIOS]; total=sum(t['totalCost'] for t in traces)
        scored.append((total,tuple(p[k] for k in sorted(p)),p,traces))
    return min(scored,key=lambda x:(x[0],x[1]))

if __name__=='__main__':
    for lag in (0,1):
        total,_,p,traces=best_policy(lag); print(json.dumps({'lag':lag,'policy':p,'totalCost':total,'traces':traces},sort_keys=True,indent=2))
