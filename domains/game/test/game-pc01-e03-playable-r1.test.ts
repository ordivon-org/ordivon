import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {SCENARIOS,commit,createPlayableState,evaluatePolicy,inspect,publicView,runWitnesses,selectArchitecture,solvePolicy} from '../experiments/product-composition-r1/pc01-e03-playable-r1/web/core.js';

const design=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-causal-works-f0/design.json',import.meta.url),'utf8'));
const close=(actual:number,expected:number,epsilon=1e-9)=>assert.ok(Math.abs(actual-expected)<=epsilon,`expected ${actual} ≈ ${expected}`);

test('R03 playable freezes exactly two one-step forecast scenarios over PC01 F0 contexts',()=>{
  assert.deepEqual(Object.keys(SCENARIOS),['route-shift','source-rule']);
  assert.deepEqual(SCENARIOS['route-shift'],{
    id:'route-shift',
    sourceCycleIndex:0,
    executionCycleIndex:1,
    previousArchitecture:'route',
    lagSteps:1,
  });
  assert.deepEqual(SCENARIOS['source-rule'],{
    id:'source-rule',
    sourceCycleIndex:1,
    executionCycleIndex:2,
    previousArchitecture:'',
    lagSteps:1,
  });
  for(const scenario of Object.values(SCENARIOS) as any[]){
    assert.equal(scenario.executionCycleIndex,scenario.sourceCycleIndex+1);
    assert.equal(scenario.lagSteps,1);
  }
});

test('route-shift forecast changes the diagnostic/action policy and retains diagnosis value',()=>{
  const anticipatory=solvePolicy(design,'route-shift',{rewardContext:'execution',causePersistence:true,allowDiagnostics:true});
  const reactive=solvePolicy(design,'route-shift',{rewardContext:'source',causePersistence:true,allowDiagnostics:true});
  const noDiagnosis=solvePolicy(design,'route-shift',{rewardContext:'execution',causePersistence:true,allowDiagnostics:false});
  assert.deepEqual(anticipatory.policy,{diagnostic:'route',architectureByObservation:{OK:'process',FAULT:'route'}});
  assert.deepEqual(reactive.policy,{diagnostic:'process',architectureByObservation:{OK:'route',FAULT:'process'}});
  close(anticipatory.expectedValue,84.2);
  close(evaluatePolicy(design,'route-shift',reactive.policy,{rewardContext:'execution',causePersistence:true}),83.6);
  close(noDiagnosis.expectedValue,78.8);
  assert.ok(anticipatory.expectedValue>noDiagnosis.expectedValue);
  assert.ok(anticipatory.expectedValue>evaluatePolicy(design,'route-shift',reactive.policy,{rewardContext:'execution',causePersistence:true}));
});

test('source-rule forecast changes the OK branch under the same route diagnostic',()=>{
  const anticipatory=solvePolicy(design,'source-rule',{rewardContext:'execution',causePersistence:true,allowDiagnostics:true});
  const reactive=solvePolicy(design,'source-rule',{rewardContext:'source',causePersistence:true,allowDiagnostics:true});
  const noDiagnosis=solvePolicy(design,'source-rule',{rewardContext:'execution',causePersistence:true,allowDiagnostics:false});
  assert.deepEqual(anticipatory.policy,{diagnostic:'route',architectureByObservation:{OK:'source',FAULT:'route'}});
  assert.deepEqual(reactive.policy,{diagnostic:'route',architectureByObservation:{OK:'process',FAULT:'route'}});
  close(anticipatory.expectedValue,88);
  close(evaluatePolicy(design,'source-rule',reactive.policy,{rewardContext:'execution',causePersistence:true}),86.8);
  close(noDiagnosis.expectedValue,86.4);
});

test('removing cause persistence collapses current diagnosis value under the same marginal cause distribution',()=>{
  for(const id of Object.keys(SCENARIOS)){
    const independent=solvePolicy(design,id,{rewardContext:'execution',causePersistence:false,allowDiagnostics:true});
    const noDiagnosis=solvePolicy(design,id,{rewardContext:'execution',causePersistence:false,allowDiagnostics:false});
    assert.equal(independent.policy.diagnostic,'none');
    close(independent.expectedValue,noDiagnosis.expectedValue);
    assert.deepEqual(new Set(Object.values(independent.policy.architectureByObservation)),new Set(Object.values(noDiagnosis.policy.architectureByObservation)));
  }
});

test('interactive carrier exposes forecast and inspection but withholds hidden cause until delayed execution resolves',()=>{
  const state=createPlayableState(design,'route-shift',{sourceCause:'process'});
  const initial=publicView(state);
  assert.equal(initial.phase,'decision');
  assert.equal(initial.currentContext.id,design.cycles[0].id);
  assert.equal(initial.executionForecast.id,design.cycles[1].id);
  assert.equal(initial.executionForecast.visible,true);
  assert.equal(initial.lagSteps,1);
  assert.equal(initial.causePersistence,true);
  assert.equal('sourceCause' in initial,false);
  assert.equal('executionCause' in initial,false);
  assert.equal(initial.resolution,null);

  const afterInspect=inspect(state,'route');
  assert.equal(afterInspect.inspection?.diagnostic,'route');
  assert.equal(afterInspect.inspection?.observation,'OK');
  assert.equal('cause' in (afterInspect.inspection??{}),false);
  selectArchitecture(state,'process');
  const resolved=commit(state);
  assert.equal(resolved.phase,'resolved');
  assert.equal(resolved.resolution?.sourceCause,'process');
  assert.equal(resolved.resolution?.executionCause,'process');
  assert.equal(resolved.resolution?.executionContextId,design.cycles[1].id);
  assert.equal(resolved.resolution?.baseReward,100);
  assert.equal(resolved.resolution?.diagnosticCost,6);
  assert.equal(resolved.resolution?.switchCost,8);
  assert.equal(resolved.resolution?.net,86);
});

test('non-persistent ablation can make a truthful current inspection stale at execution',()=>{
  const state=createPlayableState(design,'route-shift',{
    causePersistence:false,
    sourceCause:'process',
    executionCause:'route',
  });
  const afterInspect=inspect(state,'process');
  assert.equal(afterInspect.inspection?.observation,'FAULT');
  selectArchitecture(state,'process');
  const resolved=commit(state);
  assert.equal(resolved.resolution?.sourceCause,'process');
  assert.equal(resolved.resolution?.executionCause,'route');
  assert.equal(resolved.resolution?.baseReward,70);
  assert.equal(resolved.resolution?.net,56);
});

test('mechanical witness keeps product and Human claims closed',()=>{
  const witness=runWitnesses(design);
  assert.equal(witness.pass,true);
  assert.equal(witness.routeShift.forecastChangesPolicy,true);
  assert.equal(witness.routeShift.persistenceRequiredForDiagnosisValue,true);
  assert.equal(witness.sourceRule.forecastChangesPolicy,true);
  assert.equal(witness.sourceRule.persistenceRequiredForDiagnosisValue,true);
  assert.equal(witness.productSelected,false);
  assert.equal(witness.g0Entered,false);
  assert.equal(witness.humanOutcomeEstablished,false);
  assert.equal(witness.gameCoreChanged,false);
  assert.equal(witness.claimBoundary,'PLAYABLE_MECHANICAL_COUPLING_ONLY_NO_HUMAN_VALUE_OR_PRODUCT_SELECTION_CLAIM');
});


test('playable R1 is a reproducible repository asset with bounded evidence authority',()=>{
  const evidence=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-e03-playable-r1/evidence/mechanical-acceptance-r1.json',import.meta.url),'utf8'));
  const pkg=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8'));
  const experimentReadme=readFileSync(new URL('../experiments/product-composition-r1/pc01-e03-playable-r1/README.md',import.meta.url),'utf8');
  const rootReadme=readFileSync(new URL('../README.md',import.meta.url),'utf8');
  const project=readFileSync(new URL('../.ordivon/project.yaml',import.meta.url),'utf8');

  assert.equal(evidence.pass,true);
  assert.equal(evidence.designDigest,'sha256:19a258b457f4bbdeaf1e97a24c01bd9b800f0e50a4e3ffebe857e75290e0ac7c');
  assert.equal(evidence.deterministicInteractiveTraces.routeShift.resolution.net,86);
  assert.equal(evidence.deterministicInteractiveTraces.sourceRule.resolution.net,94);
  assert.equal(evidence.deterministicInteractiveTraces.persistenceAblation.resolution.net,56);
  assert.equal(evidence.productSelected,false);
  assert.equal(evidence.g0Entered,false);
  assert.equal(evidence.humanOutcomeEstablished,false);

  assert.equal(pkg.scripts['eval:pc01-e03:r1'],'node experiments/product-composition-r1/pc01-e03-playable-r1/scripts/mechanical-acceptance.ts');
  assert.equal(pkg.scripts['e2e:pc01-e03:r1'],'node experiments/product-composition-r1/pc01-e03-playable-r1/scripts/e2e-pc01-e03-playable.ts');
  assert.match(pkg.scripts.webcheck,/pc01-e03-playable-r1\/web\/\*\.js/);

  assert.match(experimentReadme,/Causal Lag Lab/);
  assert.match(experimentReadme,/cause persistence/i);
  assert.match(experimentReadme,/forecast/i);
  assert.match(experimentReadme,/productSelected=false/);
  assert.match(experimentReadme,/Human/i);
  assert.match(rootReadme,/pc01-e03-playable-r1/i);

  for(const path of [
    'experiments/product-composition-r1/pc01-e03-playable-r1/README.md',
    'experiments/product-composition-r1/pc01-e03-playable-r1/web/core.js',
    'experiments/product-composition-r1/pc01-e03-playable-r1/web/app.js',
    'experiments/product-composition-r1/pc01-e03-playable-r1/scripts/mechanical-acceptance.ts',
    'experiments/product-composition-r1/pc01-e03-playable-r1/scripts/e2e-pc01-e03-playable.ts',
    'experiments/product-composition-r1/pc01-e03-playable-r1/evidence/mechanical-acceptance-r1.json',
  ]) assert.match(project,new RegExp(path.replaceAll('/','\\/')));
});
