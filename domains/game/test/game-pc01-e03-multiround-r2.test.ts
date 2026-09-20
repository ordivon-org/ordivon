import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {REGIMES,beginRound,commit,createLearningRun,inspect,predictivePersistence,publicView,selectArchitecture,solveLearnedPolicy,updateRegimeBelief} from '../experiments/product-composition-r1/pc01-e03-multiround-r2/web/core.js';

const design=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-causal-works-f0/design.json',import.meta.url),'utf8'));
const close=(a:number,b:number,e=1e-9)=>assert.ok(Math.abs(a-b)<=e,`expected ${a} ≈ ${b}`);

test('R2 freezes two hidden run-level stability regimes with an equal prior',()=>{
  assert.deepEqual(REGIMES,{
    STABLE:{persistence:0.9},
    VOLATILE:{persistence:0.2},
  });
  const belief=updateRegimeBelief(design,[]);
  close(belief.STABLE,0.5);
  close(belief.VOLATILE,0.5);
  close(predictivePersistence(belief),0.55);
});

test('one persistent transition moves route-shift across the diagnosis threshold',()=>{
  const history=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'process'}];
  const belief=updateRegimeBelief(design,history);
  close(belief.STABLE,0.955/(0.955+0.64));
  assert.ok(predictivePersistence(belief)>0.6);
  const learned=solveLearnedPolicy(design,'route-shift',history,{historyAware:true});
  const blind=solveLearnedPolicy(design,'route-shift',history,{historyAware:false});
  assert.equal(learned.policy.diagnostic,'route');
  assert.deepEqual(learned.policy.architectureByObservation,{OK:'process',FAULT:'route'});
  assert.equal(blind.policy.diagnostic,'none');
  assert.ok(learned.expectedValue>blind.expectedValue);
});

test('one changed transition pushes the same route-shift state toward no-scan',()=>{
  const history=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'route'}];
  const belief=updateRegimeBelief(design,history);
  close(belief.STABLE,0.03/(0.03+0.24));
  assert.ok(predictivePersistence(belief)<0.3);
  const learned=solveLearnedPolicy(design,'route-shift',history,{historyAware:true});
  assert.equal(learned.policy.diagnostic,'none');
  assert.deepEqual(learned.policy.architectureByObservation,{NONE:'process'});
});

test('different histories flip the optimal scan under an otherwise identical current decision',()=>{
  const persistent=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'process'}];
  const changed=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'route'}];
  const a=solveLearnedPolicy(design,'route-shift',persistent,{historyAware:true});
  const b=solveLearnedPolicy(design,'route-shift',changed,{historyAware:true});
  assert.equal(a.scenarioId,b.scenarioId);
  assert.equal(a.currentContextId,b.currentContextId);
  assert.equal(a.executionContextId,b.executionContextId);
  assert.equal(a.previousArchitecture,b.previousArchitecture);
  assert.notEqual(a.policy.diagnostic,b.policy.diagnostic);
  assert.equal(a.policy.diagnostic,'route');
  assert.equal(b.policy.diagnostic,'none');
});

test('history-blind control cannot distinguish those two histories',()=>{
  const persistent=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'process'}];
  const changed=[{sourceCycleIndex:0,sourceCause:'process',executionCause:'route'}];
  const a=solveLearnedPolicy(design,'route-shift',persistent,{historyAware:false});
  const b=solveLearnedPolicy(design,'route-shift',changed,{historyAware:false});
  assert.deepEqual(a.policy,b.policy);
  close(a.persistenceEstimate,0.55);
  close(b.persistenceEstimate,0.55);
});

test('public run view exposes transition history but hides regime and model probabilities',()=>{
  const run=createLearningRun(design,{regime:'STABLE'});
  beginRound(run,'route-shift',{sourceCause:'process',executionCause:'process'});
  inspect(run,'route');
  selectArchitecture(run,'process');
  commit(run);
  const view=publicView(run);
  assert.equal(view.history.length,1);
  assert.deepEqual(view.history[0],{
    round:1,
    scenarioId:'route-shift',
    sourceCause:'process',
    executionCause:'process',
    persisted:true,
    net:86,
  });
  const serialized=JSON.stringify(view).toLowerCase();
  assert.doesNotMatch(serialized,/stable|volatile|posterior|probability|persistenceestimate|optimal|expectedvalue/);
  assert.equal('hiddenRegime' in view,false);
  assert.equal('belief' in view,false);
});

test('same public current state can follow different histories while oracle policy differs',()=>{
  const persistentRun=createLearningRun(design,{regime:'STABLE'});
  beginRound(persistentRun,'route-shift',{sourceCause:'process',executionCause:'process'});
  selectArchitecture(persistentRun,'process');
  commit(persistentRun);
  beginRound(persistentRun,'route-shift',{sourceCause:'source',executionCause:'source'});

  const changedRun=createLearningRun(design,{regime:'VOLATILE'});
  beginRound(changedRun,'route-shift',{sourceCause:'process',executionCause:'route'});
  selectArchitecture(changedRun,'process');
  commit(changedRun);
  beginRound(changedRun,'route-shift',{sourceCause:'source',executionCause:'source'});

  const a=publicView(persistentRun);
  const b=publicView(changedRun);
  assert.equal(a.current?.scenarioId,'route-shift');
  assert.equal(b.current?.scenarioId,'route-shift');
  assert.deepEqual(a.current?.currentContext,b.current?.currentContext);
  assert.deepEqual(a.current?.executionForecast,b.current?.executionForecast);
  assert.notDeepEqual(a.history,b.history);

  const policyA=solveLearnedPolicy(design,'route-shift',persistentRun.history,{historyAware:true});
  const policyB=solveLearnedPolicy(design,'route-shift',changedRun.history,{historyAware:true});
  assert.equal(policyA.policy.diagnostic,'route');
  assert.equal(policyB.policy.diagnostic,'none');
});


test('R2 is a reproducible repository asset with bounded learning claims',()=>{
  const evidence=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-e03-multiround-r2/evidence/mechanical-acceptance-r2.json',import.meta.url),'utf8'));
  const pkg=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8'));
  const experimentReadme=readFileSync(new URL('../experiments/product-composition-r1/pc01-e03-multiround-r2/README.md',import.meta.url),'utf8');
  const rootReadme=readFileSync(new URL('../README.md',import.meta.url),'utf8');
  const project=readFileSync(new URL('../.ordivon/project.yaml',import.meta.url),'utf8');

  assert.equal(evidence.pass,true);
  assert.equal(evidence.designDigest,'sha256:19a258b457f4bbdeaf1e97a24c01bd9b800f0e50a4e3ffebe857e75290e0ac7c');
  assert.equal(evidence.oracleEvidence.historySensitivePolicyFlip,true);
  assert.equal(evidence.oracleEvidence.historyBlindSame,true);
  assert.equal(evidence.publicCarrierEvidence.sameCurrentDecision,true);
  assert.equal(evidence.publicCarrierEvidence.publicModelLeak,false);
  assert.equal(evidence.productSelected,false);
  assert.equal(evidence.g0Entered,false);
  assert.equal(evidence.humanOutcomeEstablished,false);
  assert.equal(evidence.humanLearningEstablished,false);

  assert.equal(pkg.scripts['eval:pc01-e03:r2'],'node experiments/product-composition-r1/pc01-e03-multiround-r2/scripts/mechanical-acceptance.ts');
  assert.equal(pkg.scripts['e2e:pc01-e03:r2'],'node experiments/product-composition-r1/pc01-e03-multiround-r2/scripts/e2e-pc01-e03-multiround-r2.ts');
  assert.match(pkg.scripts.webcheck,/pc01-e03-multiround-r2\/web\/\*\.js/);

  assert.match(experimentReadme,/Memory Run/);
  assert.match(experimentReadme,/history/i);
  assert.match(experimentReadme,/hidden/i);
  assert.match(experimentReadme,/humanLearningEstablished=false/);
  assert.match(rootReadme,/pc01-e03-multiround-r2/i);

  for(const path of [
    'experiments/product-composition-r1/pc01-e03-multiround-r2/README.md',
    'experiments/product-composition-r1/pc01-e03-multiround-r2/web/core.js',
    'experiments/product-composition-r1/pc01-e03-multiround-r2/web/app.js',
    'experiments/product-composition-r1/pc01-e03-multiround-r2/scripts/mechanical-acceptance.ts',
    'experiments/product-composition-r1/pc01-e03-multiround-r2/scripts/e2e-pc01-e03-multiround-r2.ts',
    'experiments/product-composition-r1/pc01-e03-multiround-r2/evidence/mechanical-acceptance-r2.json',
  ]) assert.match(project,new RegExp(path.replaceAll('/','\\/')));
});
