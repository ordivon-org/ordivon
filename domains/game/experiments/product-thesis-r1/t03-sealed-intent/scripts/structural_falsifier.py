#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / 'design.json').read_text())
ACTIONS = D['playerActions']
PLANS = list(itertools.product(ACTIONS, repeat=D['playerUnits']))
FAMILIES = list(D['enemyFamilies'])
VARIANTS = ['left_tiebreak', 'right_tiebreak']
W, H = D['board']['width'], D['board']['height']


def md(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
def inside(p): return 0 <= p[0] < W and 0 <= p[1] < H

def step_toward(pos, target, side='left_tiebreak'):
    x,y=pos; tx,ty=target
    if y != ty:
        return (x, y + (1 if ty>y else -1))
    if x != tx:
        return (x + (1 if tx>x else -1), y)
    return pos

def flank(pos, objective, side='left_tiebreak'):
    x,y=pos; ox,_=objective
    if x != ox:
        return (x + (1 if ox>x else -1), y)
    dx=-1 if side=='left_tiebreak' else 1
    p=(x+dx,y)
    return p if inside(p) else (x-dx,y)

def adjacent_enemy(pos, enemies, side):
    cand=[(md(pos,e), e[0], e[1], i,e) for i,e in enumerate(enemies) if md(pos,e)==1]
    if not cand: return None
    cand.sort(key=lambda z:(z[1],z[2]) if side=='left_tiebreak' else (-z[1],z[2]))
    return cand[0][3], cand[0][4]

def player_commitment(state, plan):
    out=[]; enemy=state['enemy']; obj=tuple(state['objective'])
    for i,(pos0,act) in enumerate(zip(state['player'],plan)):
        pos=tuple(pos0); dest=pos; target=None
        if act=='advance': dest=step_toward(pos,obj)
        elif act=='flank': dest=flank(pos,obj,'left_tiebreak')
        elif act=='strike': target=adjacent_enemy(pos,[tuple(x) for x in enemy],'left_tiebreak')
        out.append({'unit':i,'action':act,'origin':pos,'dest':dest,'target':target})
    return out

def enemy_commitment(state,family,variant):
    pp=[tuple(x) for x in state['player']]; obj=tuple(state['objective']); out=[]
    for i,pos0 in enumerate(state['enemy']):
        pos=tuple(pos0); dest=pos; target=None; act='brace'
        adj=adjacent_enemy(pos,pp,variant)
        if adj is not None:
            act='strike'; target=adj
        elif family=='PRESS':
            # approach nearest player; tie-break by requested lateral ordering
            ordered=sorted(pp,key=lambda p:(md(pos,p),p[0] if variant=='left_tiebreak' else -p[0],p[1]))
            dest=step_toward(pos,ordered[0],variant); act='advance'
        else:
            if md(pos,obj)<=1: act='brace'
            else: dest=step_toward(pos,obj,variant); act='advance'
        out.append({'unit':i,'action':act,'origin':pos,'dest':dest,'target':target})
    return out

def resolve_moves(pcom,ecom):
    allc=[('P',x) for x in pcom]+[('E',x) for x in ecom]
    desired=Counter(x['dest'] for _,x in allc if x['dest']!=x['origin'])
    finalP=[]; finalE=[]
    for side,x in allc:
        dest=x['dest']
        final= x['origin'] if (dest!=x['origin'] and desired[dest]>1) else dest
        (finalP if side=='P' else finalE).append(final)
    return finalP,finalE

def resolve(state,plan,family,variant):
    pcom=player_commitment(state,plan); ecom=enemy_commitment(state,family,variant)
    ppos,epos=resolve_moves(pcom,ecom)
    p_dead=set(); e_dead=set(); p_braced={i for i,x in enumerate(pcom) if x['action']=='brace'}; e_braced={i for i,x in enumerate(ecom) if x['action']=='brace'}
    # strikes are committed against a target cell at time of commitment and land only if target remains there.
    for i,x in enumerate(pcom):
        if x['action']=='strike' and x['target'] is not None:
            j,cell=x['target']
            if epos[j]==cell:
                if j in e_braced: e_braced.remove(j)
                else: e_dead.add(j)
    for i,x in enumerate(ecom):
        if x['action']=='strike' and x['target'] is not None:
            j,cell=x['target']
            if ppos[j]==cell:
                if j in p_braced: p_braced.remove(j)
                else: p_dead.add(j)
    psurv=[p for i,p in enumerate(ppos) if i not in p_dead]
    esurv=[p for i,p in enumerate(epos) if i not in e_dead]
    obj=tuple(state['objective'])
    control=(1 if obj in psurv and obj not in esurv else 0)
    score=3*control + len(psurv) + 2*len(e_dead) - 2*len(p_dead)
    return {'score':score,'objectiveControl':control,'playerSurvivors':len(psurv),'enemyRemoved':len(e_dead),'playerRemoved':len(p_dead),'playerCommitment':pcom,'enemyCommitment':ecom,'finalPlayer':psurv,'finalEnemy':esurv}

def expected_scores(state,family):
    return {p:sum(resolve(state,p,family,v)['score'] for v in VARIANTS)/len(VARIANTS) for p in PLANS}
def worst_scores(state,family):
    return {p:min(resolve(state,p,family,v)['score'] for v in VARIANTS) for p in PLANS}
def best(scores):
    m=max(scores.values()); return [p for p,v in scores.items() if v==m],m

def range_all(state):
    vals=[resolve(state,p,f,v)['score'] for p in PLANS for f in FAMILIES for v in VARIANTS]
    return max(vals)-min(vals)

rows=[]; exp_best=[]; mini_best=[]; exact_revision=[]; regrets=[]
for st in D['states']:
    exp={}; mini={}
    for f in FAMILIES:
        eb,ev=best(expected_scores(st,f)); mb,mv=best(worst_scores(st,f))
        exp[f]=(eb,ev); mini[f]=(mb,mv)
        exp_best.extend(eb); mini_best.extend(mb)
        # exact-commitment oracle revision relative to family-optimal representative
        rep=sorted(eb)[0]
        for v in VARIANTS:
            exact={p:resolve(st,p,f,v)['score'] for p in PLANS}; xb,xv=best(exact)
            exact_revision.append(rep not in xb)
            regret=xv-resolve(st,rep,f,v)['score']; denom=max(1,range_all(st)); regrets.append(regret/denom)
    rows.append({
      'state':st['id'],
      'expectedBest':{f:{'plans':['/'.join(p) for p in exp[f][0]],'score':exp[f][1]} for f in FAMILIES},
      'minimaxBest':{f:{'plans':['/'.join(p) for p in mini[f][0]],'score':mini[f][1]} for f in FAMILIES},
      'expectedFamilyCueChangesPlan':set(exp['PRESS'][0]).isdisjoint(set(exp['CONTROL'][0])),
      'minimaxFamilyCueChangesPlan':set(mini['PRESS'][0]).isdisjoint(set(mini['CONTROL'][0]))
    })

expected_leverage=sum(r['expectedFamilyCueChangesPlan'] for r in rows)/len(rows)
minimax_leverage=sum(r['minimaxFamilyCueChangesPlan'] for r in rows)/len(rows)
# Count one deterministic representative per state/family to avoid ties inflating plan prevalence.
rep_counts=Counter()
for r in rows:
    for f in FAMILIES: rep_counts[tuple(r['expectedBest'][f]['plans'][0].split('/'))]+=1
dominant_share=max(rep_counts.values())/(len(rows)*len(FAMILIES))
revision_rate=sum(exact_revision)/len(exact_revision)
mean_regret=sum(regrets)/len(regrets)
rules=D['predeclaredDecisionRules']
checks={
 'familyCueCausalLeverageExpected': expected_leverage >= rules['familyCueCausalLeverageExpectedMin'],
 'familyCueCausalLeverageMinimax': minimax_leverage >= rules['familyCueCausalLeverageMinimaxMin'],
 'dominantExpectedPlanShare': dominant_share <= rules['dominantExpectedPlanShareMax'],
 'exactCommitmentRevisionRate': revision_rate >= rules['exactCommitmentRevisionRateMin'],
 'meanOracleRegretFraction': mean_regret <= rules['meanOracleRegretFractionMax']
}
standing='SURVIVES_CLEAN_STRUCTURAL_FALSIFIER' if all(checks.values()) else 'FAILS_CLEAN_STRUCTURAL_FALSIFIER'
out={
 'schemaVersion':1,'kind':'t03-sealed-intent-clean-structural-falsifier-r1','standing':standing,
 'planSpace':len(PLANS),'states':len(D['states']),'enemyFamilies':len(FAMILIES),'sealedVariantsPerFamily':len(VARIANTS),
 'metrics':{
   'expectedFamilyCueCausalLeverage':expected_leverage,
   'minimaxFamilyCueCausalLeverage':minimax_leverage,
   'dominantExpectedPlanShare':dominant_share,
   'distinctExpectedRepresentativePlans':len(rep_counts),
   'exactCommitmentRevisionRate':revision_rate,
   'meanOracleRegretFraction':mean_regret
 },
 'checks':checks,'stateResults':rows,
 'boundary':'This is a clean structural/product-thesis falsifier for T03 only. It does not establish Human tension, mastery, fun, market value or G0 selection.'
}
(ROOT/'evidence').mkdir(exist_ok=True)
(ROOT/'evidence'/'structural-falsifier-r1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['standing','planSpace','states','metrics','checks']},indent=2))
raise SystemExit(0 if standing.startswith('SURVIVES') else 3)
