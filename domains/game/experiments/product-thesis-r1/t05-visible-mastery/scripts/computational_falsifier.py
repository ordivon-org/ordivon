#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'design.json').read_text()); P=D['physics']; ROOMS=D['rooms']

def hit(ax,ay,aw,ah,b): return ax<b[0]+b[2] and ax+aw>b[0] and ay<b[1]+b[3] and ay+ah>b[1]

def attempt(room_idx,threshold,noise=0.0,rng=None,max_frames=1200):
    r=ROOMS[room_idx]; x,y=map(float,r['spawn']); vx=vy=0.0; ground=False; jumped=False; frames=0; min_y=y; landings=[]; cause='timeout'
    rng=rng or np.random.default_rng(0); noisy_threshold=float(threshold)+(float(rng.normal(0,noise)) if noise>0 else 0.0)
    # input model intentionally matches existing E2E: hold right continuously, jump whenever grounded after x threshold.
    for frame in range(max_frames):
        frames=frame+1
        vx+=P['accel']; vx*=P['drag']; vx=max(-P['maxVx'],min(P['maxVx'],vx))
        if ground and x>=noisy_threshold:
            vy=P['jumpVy']; ground=False; jumped=True
        vy=min(P['maxVy'],vy+P['gravity']); prev_y=y; x+=vx; y+=vy; x=max(0,min(696,x)); ground=False
        for plat in r['platforms']:
            if hit(x,y,P['body'][0],P['body'][1],plat) and prev_y+P['body'][1]<=plat[1]+5 and vy>=0:
                y=plat[1]-P['body'][1]; vy=0; ground=True; landings.append((round(x,2),plat[1]))
        min_y=min(min_y,y)
        if y>410:
            cause='fall'; return {'success':False,'frames':frames,'cause':cause,'minY':min_y,'landings':landings,'threshold':noisy_threshold}
        if 'hazard' in r and hit(x,y,P['body'][0],P['body'][1],r['hazard']):
            cause='hazard'; return {'success':False,'frames':frames,'cause':cause,'minY':min_y,'landings':landings,'threshold':noisy_threshold}
        if hit(x,y,P['body'][0],P['body'][1],r['goal']):
            return {'success':True,'frames':frames,'cause':'goal','minY':min_y,'landings':landings,'threshold':noisy_threshold}
    return {'success':False,'frames':frames,'cause':cause,'minY':min_y,'landings':landings,'threshold':noisy_threshold}

def bands(success_thresholds,step):
    if not success_thresholds:return []
    out=[]; start=prev=success_thresholds[0]
    for x in success_thresholds[1:]:
        if x-prev>step: out.append((start,prev)); start=x
        prev=x
    out.append((start,prev)); return out

def band_width(b): return b[1]-b[0]+5

step=5; grid=list(range(0,651,step)); scans=[]
for i in range(3):
    vals=[]
    for t in grid:
        z=attempt(i,t); vals.append({'threshold':t,'success':z['success'],'frames':z['frames'],'cause':z['cause'],'minY':z['minY']})
    success=[v['threshold'] for v in vals if v['success']]; bs=bands(success,step)
    scans.append({'room':i+1,'successBands':bs,'maxBandWidth':max([band_width(b) for b in bs],default=0),'successfulThresholdCount':len(success),'samples':vals})

known=[attempt(i,D['knownAutomationThresholds'][i])['success'] for i in range(3)]
# For room 3, treat separated successful threshold bands as distinct routing/control regimes and compare fastest median representative.
r3=scans[2]['successBands']; r3_reps=[]
for b in r3:
    ts=list(range(b[0],b[1]+1,5)); runs=[attempt(2,t) for t in ts if attempt(2,t)['success']]
    if runs:
        best=min(runs,key=lambda z:z['frames']); r3_reps.append({'band':b,'bestThreshold':best['threshold'],'frames':best['frames'],'minY':best['minY'],'landings':best['landings']})
r3_reps=sorted(r3_reps,key=lambda z:z['frames'])
if len(r3_reps)>=2:
    fast=r3_reps[0]; safe=r3_reps[-1]; time_diff=abs(safe['frames']-fast['frames'])/min(safe['frames'],fast['frames'])
else: time_diff=0.0

# Thompson-sampling threshold learner over coarse candidate timings under motor noise.
def learner(room,seed,attempts=20,noise=12.0):
    rng=np.random.default_rng(seed); arms=np.arange(0,651,20); a=np.ones(len(arms)); b=np.ones(len(arms)); hist=[]
    for n in range(attempts):
        theta=rng.beta(a,b); j=int(np.argmax(theta)); z=attempt(room,float(arms[j]),noise=noise,rng=rng); reward=1 if z['success'] else 0; a[j]+=reward; b[j]+=1-reward; hist.append(reward)
    return hist
learning={}
for room in range(3):
    H=np.array([learner(room,10000+room*100+s) for s in range(96)],dtype=float)
    early=float(H[:,:5].mean()); late=float(H[:,-5:].mean())
    learning[f'room{room+1}']={'earlySuccess':early,'lateSuccess':late,'improvement':late-early}

rules=D['predeclaredDecisionRules']
checks={
 'knownAutomationPolicyCompletesAllRooms':all(known)==rules['knownAutomationPolicyCompletesAllRooms'],
 'successBandWidthEachRoom':all(x['maxBandWidth']>=rules['minSuccessBandWidthPixelsEachRoom'] for x in scans),
 'room3DistinctSuccessBands':len(r3)>=rules['room3DistinctSuccessBandsMin'],
 'room3FastSafeCompletionTimeDifference':time_diff>=rules['room3FastSafeCompletionTimeDifferenceMinFraction'],
 'learnerImprovementEachRoom':all(x['improvement']>=rules['learnerLateMinusEarlySuccessMin'] for x in learning.values()),
 'learnerLateSuccessEachRoom':all(x['lateSuccess']>=rules['learnerLateSuccessMin'] for x in learning.values())
}
standing='SURVIVES_COMPUTATIONAL_MASTERY_FALSIFIER' if all(checks.values()) else 'FAILS_COMPUTATIONAL_MASTERY_FALSIFIER'
out={'schemaVersion':1,'kind':'t05-visible-mastery-computational-falsifier-r1','standing':standing,'mechanismModifiedAfterObservation':False,'knownAutomationCompletion':known,'roomScanSummary':[{k:v for k,v in x.items() if k!='samples'} for x in scans],'room3Regimes':r3_reps,'room3FastSafeTimeDifferenceFraction':time_diff,'syntheticLearning':learning,'checks':checks,'boundary':'Computational evidence only: deterministic reachability, timing-policy diversity and learnability under declared synthetic motor-noise model. It does not identify Human flow, enjoyment, self-attribution or voluntary retry.'}
(ROOT/'evidence').mkdir(exist_ok=True); (ROOT/'evidence'/'computational-falsifier-r1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
raise SystemExit(0 if standing.startswith('SURVIVES') else 3)
