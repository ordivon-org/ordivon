#!/usr/bin/env python3
from __future__ import annotations
import itertools,json,math
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
M=['wonder','logic','empathy','humor','risk','violence']; SEQ=list(itertools.product(M,repeat=4))
P={
'scholar':({'wonder':1,'logic':1.6,'empathy':.5,'humor':.2,'risk':.4,'violence':-.5},.65,[('logic','wonder')]),
'romantic':({'wonder':1,'logic':.1,'empathy':1.7,'humor':.4,'risk':.5,'violence':-.6},.5,[('empathy','risk')]),
'trickster':({'wonder':.5,'logic':.1,'empathy':.2,'humor':1.8,'risk':1,'violence':-.1},.8,[('humor','risk')]),
'warrior':({'wonder':.2,'logic':.4,'empathy':.1,'humor':-.2,'risk':1.2,'violence':1.5},.45,[('risk','violence')]),
'healer':({'wonder':.4,'logic':.5,'empathy':1.8,'humor':.3,'risk':-.2,'violence':-1.2},.55,[('empathy','logic')])}
def audience(s,p):
 w,nov,pairs=P[p]; score=0; seen=Counter()
 for i,m in enumerate(s):
  score+=w[m]; score += nov if seen[m]==0 else -nov*seen[m]
  if i and ((s[i-1],m) in pairs or (m,s[i-1]) in pairs): score+=1.1
  seen[m]+=1
 return score
# creator intents are deliberately independent of audience personas.
I={
'architect':{'wonder':.6,'logic':1.8,'empathy':.2,'humor':0,'risk':.3,'violence':-.5},
'caretaker':{'wonder':.5,'logic':.3,'empathy':1.9,'humor':.2,'risk':-.3,'violence':-1},
'comedian':{'wonder':.4,'logic':0,'empathy':.3,'humor':2,'risk':.5,'violence':-.4},
'daredevil':{'wonder':.3,'logic':.1,'empathy':0,'humor':.3,'risk':1.8,'violence':1},
'poet':{'wonder':1.8,'logic':.2,'empathy':1.1,'humor':.4,'risk':.1,'violence':-.8},
'brutalist':{'wonder':0,'logic':.5,'empathy':-.6,'humor':-.4,'risk':1,'violence':1.8}}
def intent(s,i): return sum(I[i][m] for m in s)-0.25*sum(max(0,n-2) for n in Counter(s).values())
def norm(v,lo,hi): return 0 if hi<=lo else (v-lo)/(hi-lo)
# Precompute normalized intent/audience scores so blend weights are comparable.
intent_scores={i:[intent(s,i) for s in SEQ] for i in I}; aud_scores={p:[audience(s,p) for s in SEQ] for p in P}
intent_bounds={i:(min(v),max(v)) for i,v in intent_scores.items()}; aud_bounds={p:(min(v),max(v)) for p,v in aud_scores.items()}
weights=[.25,.5,.75]; rows=[]
for lam in weights:
 choices={}; intent_ret=[]; repeat=[]
 for i in I:
  for p in P:
   vals=[]
   for k,s in enumerate(SEQ):
    iv=norm(intent_scores[i][k],*intent_bounds[i]); av=norm(aud_scores[p][k],*aud_bounds[p]); vals.append(lam*iv+(1-lam)*av)
   k=max(range(len(SEQ)),key=lambda x:vals[x]); s=SEQ[k]; choices[(i,p)]=s; intent_ret.append(norm(intent_scores[i][k],*intent_bounds[i])); repeat.append(max(Counter(s).values())/4)
 # for each creator, does audience identity change artifact?
 adapt=sum(len({choices[(i,p)] for p in P})>=2 for i in I)/len(I)
 # for each audience, do different creators preserve distinct artifacts?
 divers=np.mean([len({choices[(i,p)] for i in I})/len(I) for p in P])
 counts=Counter(choices.values()); maxshare=max(counts.values())/len(choices)
 rows.append({'authorshipWeight':lam,'creatorAudienceAdaptationRate':adapt,'meanCreatorDiversityWithinAudience':float(divers),'meanIntentRetention':float(np.mean(intent_ret)),'meanMaxMotifShare':float(np.mean(repeat)),'maxSingleSequenceShare':maxshare,'distinctChosenSequences':len(counts)})
mid=next(x for x in rows if x['authorshipWeight']==.5)
checks={
 'audienceChangesArtifacts':mid['creatorAudienceAdaptationRate']>=0.80,
 'creatorIntentPreserved':mid['meanIntentRetention']>=0.75,
 'creatorDiversitySurvives':mid['meanCreatorDiversityWithinAudience']>=0.65,
 'noUniversalRubricSequence':mid['maxSingleSequenceShare']<=0.25,
 'noMotifSpamCollapse':mid['meanMaxMotifShare']<=0.75,
 'tradeoffStableAcrossWeights':all(x['distinctChosenSequences']>=8 for x in rows)
}
standing='SURVIVES_AUTHORSHIP_ADAPTATION_FALSIFIER' if all(checks.values()) else 'FAILS_AUTHORSHIP_ADAPTATION_FALSIFIER'
out={'schemaVersion':1,'kind':'t04-responsive-creation-computational-authorship-r1','standing':standing,'mechanismModifiedAfterObservation':False,'creatorModels':len(I),'audiencePersonas':len(P),'sequenceSpace':len(SEQ),'weightSweep':rows,'checks':checks,'boundary':'This estimates whether creator-intent diversity and audience adaptation can coexist in the declared deterministic responsive-persona model. It does not identify Human authorship, enjoyment or social meaning.'}
(ROOT/'evidence').mkdir(exist_ok=True);(ROOT/'evidence'/'computational-authorship-r1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));raise SystemExit(0 if standing.startswith('SURVIVES') else 3)
