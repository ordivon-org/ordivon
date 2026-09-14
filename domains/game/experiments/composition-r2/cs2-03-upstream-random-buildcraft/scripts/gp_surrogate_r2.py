#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = Path(__file__).with_name('computational_player_science_r1.py')
spec = importlib.util.spec_from_file_location('cps', MODULE_PATH)
cps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cps)
FOLLOW = json.loads((ROOT / 'evidence' / 'active-player-model-followup-r1.json').read_text())


def params_to_unit(p):
    vals=np.array([p[k] for k in cps.PARAMS],dtype=float)
    return (vals-cps.BOUNDS[:,0])/(cps.BOUNDS[:,1]-cps.BOUNDS[:,0])


def sqdist_ard(a,b,lengths):
    aa=a/lengths; bb=b/lengths
    return np.maximum(0.0, np.sum(aa*aa,axis=1)[:,None]+np.sum(bb*bb,axis=1)[None,:]-2*aa@bb.T)


def kernel(a,b,lengths):
    return np.exp(-0.5*sqdist_ard(a,b,lengths))


def fit_gp(x,y,lengths,noise):
    ym=float(np.mean(y)); ys=float(np.std(y)) or 1.0
    z=(y-ym)/ys
    k=kernel(x,x,lengths)+(noise+1e-9)*np.eye(len(x))
    try: L=np.linalg.cholesky(k)
    except np.linalg.LinAlgError: return None
    alpha=np.linalg.solve(L.T,np.linalg.solve(L,z))
    nlml=0.5*float(z@alpha)+float(np.sum(np.log(np.diag(L))))+0.5*len(x)*math.log(2*math.pi)
    return {'x':x,'ym':ym,'ys':ys,'lengths':lengths.copy(),'noise':noise,'L':L,'alpha':alpha,'nlml':nlml}


def predict(m,xs):
    ks=kernel(m['x'],xs,m['lengths'])
    mean_z=ks.T@m['alpha']
    v=np.linalg.solve(m['L'],ks)
    var_z=np.maximum(1e-12,1.0-np.sum(v*v,axis=0))
    return m['ym']+m['ys']*mean_z, (m['ys']**2)*var_z


def tune_gp(x,y):
    lengths=np.full(x.shape[1],0.5)
    noise=0.05
    best=fit_gp(x,y,lengths,noise)
    # Coordinate descent on exact GP marginal likelihood; bounded to the declared unit cube.
    lgrid=[0.12,0.2,0.32,0.5,0.8,1.2,1.8]
    ngrid=[1e-4,5e-4,0.002,0.01,0.03,0.08,0.2]
    for _ in range(3):
        for j in range(x.shape[1]):
            local=best
            for cand in lgrid:
                trial=best['lengths'].copy(); trial[j]=cand
                m=fit_gp(x,y,trial,best['noise'])
                if m is not None and m['nlml']<local['nlml']: local=m
            best=local
        local=best
        for cand in ngrid:
            m=fit_gp(x,y,best['lengths'],cand)
            if m is not None and m['nlml']<local['nlml']: local=m
        best=local
    return best


def r2(y,p):
    den=float(np.sum((y-np.mean(y))**2))
    return 1-float(np.sum((y-p)**2))/den

rng=np.random.default_rng(20260914)
samples=cps.lhs(128,len(cps.PARAMS),rng)
responses=np.array([cps.evaluate_profile(cps.unit_to_params(x),i+1) for i,x in enumerate(samples)])
order=rng.permutation(len(samples)); train_idx,test_idx=order[:100],order[100:]
x_train=samples[train_idx]; y_train=responses[train_idx]
x_test=samples[test_idx]; y_test=responses[test_idx]

# Add the direct high-EIG follow-up points to training only; independent R1 test set stays frozen.
active_x=np.vstack([params_to_unit(o['params']) for o in FOLLOW['observations']])
active_y=np.array([o['directSimulatedScoreATE'] for o in FOLLOW['observations']],dtype=float)
x_aug=np.vstack([x_train,active_x]); y_aug=np.concatenate([y_train,active_y])

model=tune_gp(x_aug,y_aug)
pred,var=predict(model,x_test)
test_r2=r2(y_test,pred); mae=float(np.mean(np.abs(y_test-pred)))
coverage=float(np.mean((y_test>=pred-1.96*np.sqrt(var+model['noise']*model['ys']**2)) & (y_test<=pred+1.96*np.sqrt(var+model['noise']*model['ys']**2))))

# ARD sensitivity proxy: shorter fitted length scale => faster variation / greater local sensitivity.
inv=1/np.maximum(model['lengths'],1e-12); sens=inv/inv.sum()

cand=cps.lhs(2048,len(cps.PARAMS),np.random.default_rng(998877))
pm,pv=predict(model,cand)
obs_noise=max(1e-12,model['noise']*model['ys']**2)
eig=0.5*np.log1p(pv/obs_noise)
ranks=np.argsort(-eig)[:10]
nexts=[]
for k,i in enumerate(ranks,1):
    nexts.append({'rank':k,'expectedInformationGainNats':float(eig[i]),'epistemicPredictiveVariance':float(pv[i]),'surrogatePredictedScoreATE':float(pm[i]),'params':cps.unit_to_params(cand[i])})

out={
 'schemaVersion':1,
 'kind':'cs2-03-gp-player-effect-surrogate-r2',
 'standing':'PASS_LOCAL_GP_SURROGATE' if test_r2>=0.75 else 'WEAK_LOCAL_GP_SURROGATE',
 'target':'paired total-score ATE of UPSTREAM vs DOWNSTREAM',
 'method':'Gaussian process with ARD RBF kernel; hyperparameters selected by bounded coordinate descent on exact marginal likelihood',
 'frozenIndependentTestProfiles':len(test_idx),
 'baseTrainingProfiles':len(train_idx),
 'activeFollowupProfilesAdded':len(active_x),
 'testR2':float(test_r2),
 'testMAE':mae,
 'approx95PredictiveCoverage':coverage,
 'fittedNoiseFractionStandardized':float(model['noise']),
 'ardLengthScales':{k:float(v) for k,v in zip(cps.PARAMS,model['lengths'])},
 'ardSensitivityProxy':{k:float(v) for k,v in zip(cps.PARAMS,sens)},
 'negativeLogMarginalLikelihood':float(model['nlml']),
 'nextExperimentSelection':{
   'criterion':'Gaussian-process one-observation expected information gain using posterior epistemic variance and fitted observation-noise scale',
   'candidatePool':len(cand),
   'topCandidates':nexts
 },
 'comparisonToR1Polynomial':{
   'r1TestR2':0.6248356991634916,
   'r1TestMAE':0.45706376952804434,
   'deltaR2':float(test_r2-0.6248356991634916),
   'deltaMAE':float(mae-0.45706376952804434)
 },
 'boundary':'This GP emulates direct synthetic-player simulation inside the declared parameter envelope. Its uncertainty is surrogate epistemic uncertainty, not calibrated uncertainty about a Human population or subjective Player Value.'
}
(ROOT/'evidence'/'gp-player-effect-surrogate-r2.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
