#!/usr/bin/env python3
from __future__ import annotations
import json, math
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
H=[(c,m) for c in range(6) for m in range(3)]
def clue(i,h):
 c,m=h
 return [f'parity:{c%2}',f'district:{0 if c<3 else 1}',f'motive:{m}',f'trace:{(c+m)%3}',f'route:{c%3}',f'witness:{(c*2+m)%4}',f'timing:{(c+2*m)%5}',f'signature:{(c*3+m*2)%7}'][i]
def filt(cands,i,truth):
 v=clue(i,truth); return [h for h in cands if clue(i,h)==v]
def gain(cands,i):
 groups=Counter(clue(i,h) for h in cands); n=len(cands)
 return math.log2(n)-sum((k/n)*math.log2(k) for k in groups.values())
def run_policy(truth,temp,rng,budget=2):
 cands=H[:]; unused=list(range(8)); seq=[]
 for _ in range(budget):
  if len(cands)<=1: break
  gs=np.array([gain(cands,i) for i in unused],float)
  if temp==0: j=int(np.argmax(gs))
  elif math.isinf(temp): j=int(rng.integers(0,len(unused)))
  else:
   z=(gs-gs.max())/temp; p=np.exp(z); p/=p.sum(); j=int(rng.choice(len(unused),p=p))
  i=unused.pop(j); seq.append(i); cands=filt(cands,i,truth)
 return len(cands),tuple(seq)
models=[('optimal',0.0),('low-noise',0.15),('bounded',0.5),('high-noise',1.0),('random',float('inf'))]
rows=[]
for name,temp in models:
 rem=[]; seqs=[]
 for ti,t in enumerate(H):
  reps=1 if temp==0 else 200
  for r in range(reps):
   n,s=run_policy(t,temp,np.random.default_rng(100000*ti+r+int(1000*(0 if math.isinf(temp) else temp))))
   rem.append(n); seqs.append(s)
 rows.append({'model':name,'temperature':None if math.isinf(temp) else temp,'solvedRate':sum(x==1 for x in rem)/len(rem),'meanRemaining':sum(rem)/len(rem),'distinctSequences':len(set(seqs)),'firstClueEntropyBits':-sum((v/len(seqs))*math.log2(v/len(seqs)) for v in Counter(s[0] if s else -1 for s in seqs).values())})
# generous budget control: optimal vs fixed under 4 clues should converge, confirming scarcity creates the decision.
def fixed(truth,order,b=4):
 c=H[:]
 for i in order[:b]: c=filt(c,i,truth)
 return len(c)
generous_opt=[run_policy(t,0,np.random.default_rng(1),4)[0] for t in H]
generous_fixed=[fixed(t,list(range(8)),4) for t in H]
optimal=next(x for x in rows if x['model']=='optimal'); bounded=next(x for x in rows if x['model']=='bounded'); high=next(x for x in rows if x['model']=='high-noise'); random=next(x for x in rows if x['model']=='random')
checks={
 'optimalScarceSolved':optimal['solvedRate']>=0.95,
 'boundedRobustness':bounded['solvedRate']>=0.70 and bounded['meanRemaining']<=1.5,
 'highNoiseStillInformative':high['meanRemaining']<=2.0,
 'randomClearlyWorse':random['meanRemaining']>=1.8 and random['solvedRate']<=0.65,
 'adaptiveBranchingExists':bounded['distinctSequences']>=4,
 'generousBudgetCollapsesSelectionValue':abs(sum(generous_opt)/len(H)-sum(generous_fixed)/len(H))<=0.1
}
standing='SURVIVES_BOUNDED_RATIONALITY_ROBUSTNESS' if all(checks.values()) else 'FAILS_BOUNDED_RATIONALITY_ROBUSTNESS'
out={'schemaVersion':1,'kind':'t01-scarce-evidence-computational-robustness-r1','standing':standing,'mechanismModifiedAfterObservation':False,'playerModels':rows,'generousControl':{'optimalMeanRemaining':sum(generous_opt)/len(H),'fixedMeanRemaining':sum(generous_fixed)/len(H)},'checks':checks,'boundary':'This estimates robustness of evidence-selection value under declared bounded clue-choice models. It does not identify Human satisfaction, fairness or aha experience.'}
(ROOT/'evidence').mkdir(exist_ok=True);(ROOT/'evidence'/'computational-robustness-r1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));raise SystemExit(0 if standing.startswith('SURVIVES') else 3)
