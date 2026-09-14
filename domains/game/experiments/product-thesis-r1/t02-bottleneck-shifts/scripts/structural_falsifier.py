#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'design.json').read_text())
RES=D['resources']; B=D['unitBudget']; TOPS=D['topologies']; OBJ=D['objectives']; F=D['flowModel']
# architecture vector: eA,eB,eC,pA,pB,pC,tPair,tSolo,buffer; exactly B units.

def compositions(total,n,prefix=()):
    if n==1:
        yield prefix+(total,); return
    for x in range(total+1): yield from compositions(total-x,n-1,prefix+(x,))

ALLOC=list(compositions(B,9))
ARCH=[(top,a) for top in TOPS for a in ALLOC]


def paired(top):
    pair,solo=top.split('|'); return tuple(pair),solo


def throughputs(arch,perturbed=False):
    top,a=arch; e=a[0:3]; p=a[3:6]; tp,ts,buf=a[6],a[7],a[8]
    base=[min(F['extractorCapacityPerUnit']*e[i],F['processorCapacityPerUnit']*p[i]) for i in range(3)]
    pair,solo=paired(top); idx={r:i for i,r in enumerate(RES)}; pi=[idx[r] for r in pair]; si=idx[solo]
    pair_cap=F['trunkCapacityPerUnit']*tp*(0.55 if perturbed else 1.0)+F['bufferPairRelief']*buf
    solo_cap=F['trunkCapacityPerUnit']*ts+F['bufferSoloRelief']*buf
    out=base[:]
    pair_sum=sum(base[i] for i in pi)
    if pair_sum>pair_cap and pair_sum>0:
        for i in pi: out[i]=base[i]*(pair_cap/pair_sum)
    out[si]=min(base[si],solo_cap)
    return out


def utility(t,w):
    # Weighted geometric utility over delivered flow keeps all three resources decision-relevant.
    return math.exp(sum(wi*math.log1p(max(0.0,ti)) for wi,ti in zip(w,t)))

def bottleneck_profile(arch,perturbed=False):
    top,a=arch; e=a[0:3]; p=a[3:6]; tp,ts,buf=a[6],a[7],a[8]; pair,solo=paired(top); idx={r:i for i,r in enumerate(RES)}
    raw=[F['extractorCapacityPerUnit']*e[i] for i in range(3)]
    proc=[F['processorCapacityPerUnit']*p[i] for i in range(3)]
    pair_cap=F['trunkCapacityPerUnit']*tp*(0.55 if perturbed else 1.0)+F['bufferPairRelief']*buf
    solo_cap=F['trunkCapacityPerUnit']*ts+F['bufferSoloRelief']*buf
    base=[min(raw[i],proc[i]) for i in range(3)]; pair_idx=[idx[r] for r in pair]; pair_sum=sum(base[i] for i in pair_idx)
    prof=[]
    for i,r in enumerate(RES):
        if raw[i]<=proc[i] and raw[i]<=1e-12: kind='absent'
        elif raw[i] <= proc[i]: kind='extraction'
        else: kind='processing'
        if i in pair_idx and pair_sum>pair_cap+1e-12: kind='transport'
        if r==solo and base[i]>solo_cap+1e-12: kind='transport'
        prof.append(kind)
    return tuple(prof)

def sig(arch):
    top,a=arch
    return {'topology':top,'allocation':{'eA':a[0],'eB':a[1],'eC':a[2],'pA':a[3],'pB':a[4],'pC':a[5],'pairTrunk':a[6],'soloTrunk':a[7],'buffer':a[8]}}

scores={}
for name,od in OBJ.items():
    w=od['weights']; scores[(name,False)]=[]; scores[(name,True)]=[]
    for arch in ARCH:
        scores[(name,False)].append(utility(throughputs(arch,False),w))
        scores[(name,True)].append(utility(throughputs(arch,True),w))

best_idx={k:max(range(len(ARCH)),key=lambda i:v[i]) for k,v in scores.items()}
best_val={k:scores[k][best_idx[k]] for k in scores}
baseline_arch={name:ARCH[best_idx[(name,False)]] for name in OBJ}
pert_arch={name:ARCH[best_idx[(name,True)]] for name in OBJ}

# Universal architecture maximizes mean fraction of each baseline objective optimum.
univ_scores=[]
for i,arch in enumerate(ARCH):
    ratios=[scores[(name,False)][i]/best_val[(name,False)] for name in OBJ]
    univ_scores.append(sum(ratios)/len(ratios))
ui=max(range(len(ARCH)),key=lambda i:univ_scores[i]); univ=ARCH[ui]
univ_regret={name:1-scores[(name,False)][ui]/best_val[(name,False)] for name in OBJ}

old_pert_regret={}
changed={}
rows={}
for name in OBJ:
    bi=best_idx[(name,False)]; pi=best_idx[(name,True)]
    old_pert_regret[name]=1-scores[(name,True)][bi]/best_val[(name,True)]
    changed[name]=baseline_arch[name] != pert_arch[name]
    rows[name]={
      'baselineBest':sig(baseline_arch[name]),'baselineThroughput':throughputs(baseline_arch[name],False),'baselineBottleneck':bottleneck_profile(baseline_arch[name],False),'baselineScore':best_val[(name,False)],
      'perturbedBest':sig(pert_arch[name]),'perturbedThroughput':throughputs(pert_arch[name],True),'perturbedBottleneck':bottleneck_profile(pert_arch[name],True),'perturbedScore':best_val[(name,True)],
      'oldBaselineArchitectureRegretAfterPerturbation':old_pert_regret[name]
    }

base_sigs={ (a[0],a[1]) for a in baseline_arch.values() }
base_tops={a[0] for a in baseline_arch.values()}
bprofiles={bottleneck_profile(a,False) for a in baseline_arch.values()}
metrics={
 'architectureCount':len(ARCH),
 'distinctBaselineOptimalArchitectures':len(base_sigs),
 'distinctBaselineOptimalTopologies':len(base_tops),
 'universalArchitecture':sig(univ),
 'universalRegretByObjective':univ_regret,
 'maxUniversalRegret':max(univ_regret.values()),
 'meanUniversalRegret':sum(univ_regret.values())/len(univ_regret),
 'perturbationChangesOptimumFraction':sum(changed.values())/len(changed),
 'meanOldOptimumPerturbationRegret':sum(old_pert_regret.values())/len(old_pert_regret),
 'maxOldOptimumPerturbationRegret':max(old_pert_regret.values()),
 'distinctBottleneckProfiles':len(bprofiles)
}
r=D['predeclaredDecisionRules']
checks={
 'distinctBaselineOptimalArchitectures':metrics['distinctBaselineOptimalArchitectures']>=r['distinctBaselineOptimalArchitecturesMin'],
 'distinctBaselineOptimalTopologies':metrics['distinctBaselineOptimalTopologies']>=r['distinctBaselineOptimalTopologiesMin'],
 'maxUniversalRegret':metrics['maxUniversalRegret']>=r['maxUniversalRegretMin'],
 'perturbationChangesOptimumFraction':metrics['perturbationChangesOptimumFraction']>=r['perturbationChangesOptimumFractionMin'],
 'meanOldOptimumPerturbationRegret':metrics['meanOldOptimumPerturbationRegret']>=r['meanOldOptimumPerturbationRegretMin'],
 'distinctBottleneckProfiles':metrics['distinctBottleneckProfiles']>=r['distinctBottleneckProfilesMin']
}
standing='SURVIVES_TOPOLOGY_BOTTLENECK_FALSIFIER' if all(checks.values()) else 'FAILS_TOPOLOGY_BOTTLENECK_FALSIFIER'
out={'schemaVersion':1,'kind':'t02-bottleneck-shifts-structural-falsifier-r1','standing':standing,'mechanismModifiedAfterObservation':False,'metrics':metrics,'checks':checks,'objectives':rows,'boundary':'This establishes only structural/topological bottleneck migration in the declared computational carrier. It does not establish Human satisfaction, ownership, market demand or G0 selection.'}
(ROOT/'evidence').mkdir(exist_ok=True)
(ROOT/'evidence'/'structural-falsifier-r1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'standing':standing,'metrics':metrics,'checks':checks,'objectiveSummary':rows},indent=2))
raise SystemExit(0 if standing.startswith('SURVIVES') else 3)
