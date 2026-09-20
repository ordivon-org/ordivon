#!/usr/bin/env python3
import itertools, json, statistics
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'design.json').read_text())
CARD=D['cards']; OFFERS=D['offers']; ENC=D['encounters']; SYNERGY=D['synergies']

def add(a,b): return [x+y for x,y in zip(a,b)]
def build_vector(path):
    v=[0,0,0]
    for c in path: v=add(v,CARD[c]['stats'])
    for a,b in itertools.combinations(path,2):
        key={a,b}
        for s in SYNERGY:
            if set(s['cards'])==key:
                v=add(v,s['bonus'])
    return v

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def score_path(path, encounters):
    total=0
    per=[]
    for i,e in enumerate(encounters):
        score=dot(build_vector(path[:i+1]),ENC[e]['weights'])
        total+=score; per.append(score)
    return total,per

def greedy_path(encounters):
    chosen=[]
    for i,e in enumerate(encounters):
        best=max(OFFERS[i],key=lambda c: dot(build_vector(chosen+[c]),ENC[e]['weights']))
        chosen.append(best)
    return tuple(chosen)

paths=list(itertools.product(*OFFERS))
eseqs=list(itertools.product(ENC.keys(), repeat=len(OFFERS)))
optimal_paths=[]; optimal_scores=[]; greedy_uplifts=[]
for es in eseqs:
    vals=[score_path(p,es)[0] for p in paths]
    mx=max(vals); best=paths[vals.index(mx)]
    optimal_paths.append(best); optimal_scores.append(mx)
    gp=greedy_path(es); gv=score_path(gp,es)[0]
    greedy_uplifts.append((mx-gv)/max(1,gv))
mean_by_path={p:statistics.mean(score_path(p,es)[0] for es in eseqs) for p in paths}
best_universal=max(mean_by_path,key=mean_by_path.get)
best_universal_mean=mean_by_path[best_universal]
adaptive_mean=statistics.mean(optimal_scores)
counts=Counter(optimal_paths); first=Counter(p[0] for p in optimal_paths)
human=[]
for seq in D['humanSequences']:
    vals=[score_path(p,seq)[0] for p in paths]
    human.append({'sequence':seq,'optimalScore':max(vals),'meanPathScore':statistics.mean(vals),'optimalPath':list(paths[vals.index(max(vals))])})
metrics={
 'allEncounterSequences':len(eseqs),
 'allBuildPaths':len(paths),
 'uniqueOptimalBuildSignatures':len(counts),
 'largestOptimalSignatureShare':max(counts.values())/len(eseqs),
 'largestFirstPickShare':max(first.values())/len(eseqs),
 'adaptiveOptimalMean':adaptive_mean,
 'bestUniversalPath':list(best_universal),
 'bestUniversalMean':best_universal_mean,
 'adaptiveVsUniversalUplift':(adaptive_mean-best_universal_mean)/best_universal_mean,
 'optimalVsGreedyMeanUplift':statistics.mean(greedy_uplifts),
 'encounterSequencesWithOver2PctOptimalVsGreedyUplift':sum(x>0.02 for x in greedy_uplifts)/len(greedy_uplifts),
 'humanSequenceDiagnostics':human
}
checks={
 'pathDiversity':metrics['uniqueOptimalBuildSignatures']>=6,
 'noUniversalSignatureDominance':metrics['largestOptimalSignatureShare']<0.50,
 'noUniversalFirstPickDominance':metrics['largestFirstPickShare']<0.70,
 'contextAdaptationHasValue':metrics['adaptiveVsUniversalUplift']>0.05,
 'pathReasoningBeatsGreedy':metrics['optimalVsGreedyMeanUplift']>0.05,
 'humanSequencesDifficultyMatched':max(x['optimalScore'] for x in human)-min(x['optimalScore'] for x in human)<=5
}
out={'schemaVersion':1,'experiment':'cs2-03-upstream-random-buildcraft','standing':'STRUCTURAL_PRECHECK_PASS' if all(checks.values()) else 'STRUCTURAL_PRECHECK_FAIL','metrics':metrics,'checks':checks,'humanEvidence':'UNOBSERVED','claimBoundary':'Structural checks validate a nondegenerate carrier only. They do not establish attribution, adaptation, enjoyment, replay desire, or superiority of one randomness timing condition for humans.'}
(ROOT/'evidence'/'structural-precheck.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
