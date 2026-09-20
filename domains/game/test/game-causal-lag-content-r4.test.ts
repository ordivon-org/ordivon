import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {createSessionRun,commitRound,nextRound,publicView,selectArchitecture} from '../experiments/product-composition-r1/causal-lag-session-r3/web/core.js';
// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {CONTENT_ROLES,FIRST_BREADTH_ARC,analyzeTransitionSpace,compileRunRecipe,validateContentUnit} from '../experiments/product-composition-r1/causal-lag-content-r4/content-grammar.js';

const design=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-causal-works-f0/design.json',import.meta.url),'utf8'));

test('R4 content grammar keeps exactly the authored semantic role vocabulary',()=>{
  assert.deepEqual(CONTENT_ROLES,[
    'INTRODUCE',
    'PRACTICE',
    'VARY',
    'COMBINE',
    'STRESS',
    'RECONTEXTUALIZE',
    'CONCLUDE',
  ]);
});

test('a content unit owns only role and an existing context transition',()=>{
  const unit={id:'u',role:'VARY',sourceCycleIndex:0,executionCycleIndex:1};
  assert.deepEqual(validateContentUnit(design,unit),unit);
  assert.throws(()=>validateContentUnit(design,{...unit,role:'LEVEL_UP'}),/role/i);
  assert.throws(()=>validateContentUnit(design,{...unit,sourceCycleIndex:99}),/source/i);
  assert.throws(()=>validateContentUnit(design,{...unit,executionCycleIndex:99}),/execution/i);
  assert.equal('rewardByCauseAndArchitecture' in unit,false);
  assert.equal('diagnosticCost' in unit,false);
  assert.equal('switchCost' in unit,false);
});

test('run recipe composition fails closed when adjacent context seams do not discharge',()=>{
  const broken={
    id:'broken',
    targetTotal:200,
    initialArchitecture:'route',
    units:[
      {id:'a',role:'INTRODUCE',sourceCycleIndex:0,executionCycleIndex:1},
      {id:'b',role:'CONCLUDE',sourceCycleIndex:2,executionCycleIndex:0},
    ],
  };
  assert.throws(()=>compileRunRecipe(design,broken),/context seam/i);
});

test('the first breadth arc is a seven-beat chain over existing PC01 contexts',()=>{
  const compiled=compileRunRecipe(design,FIRST_BREADTH_ARC);
  assert.deepEqual(FIRST_BREADTH_ARC.units.map((u:any)=>u.role),[
    'INTRODUCE',
    'PRACTICE',
    'VARY',
    'COMBINE',
    'STRESS',
    'RECONTEXTUALIZE',
    'CONCLUDE',
  ]);
  assert.deepEqual(compiled.sessionRules,{
    roundCount:7,
    targetTotal:560,
    initialArchitecture:'route',
    contextChain:[
      {sourceCycleIndex:0,executionCycleIndex:0},
      {sourceCycleIndex:0,executionCycleIndex:1},
      {sourceCycleIndex:1,executionCycleIndex:1},
      {sourceCycleIndex:1,executionCycleIndex:2},
      {sourceCycleIndex:2,executionCycleIndex:2},
      {sourceCycleIndex:2,executionCycleIndex:0},
      {sourceCycleIndex:0,executionCycleIndex:1},
    ],
  });
  assert.equal(compiled.maxTheoreticalBase,700);
  assert.equal(compiled.unitCount,7);
});

test('existing transition space already creates policy breadth without new verbs',()=>{
  const analysis=analyzeTransitionSpace(design,{
    persistences:[0.2,0.55,0.9],
    previousArchitectures:design.architectureModes,
  });
  assert.equal(analysis.transitionCount,9);
  assert.equal(analysis.evaluatedStates,81);
  assert.equal(analysis.distinctPolicySignatures,7);
  assert.equal(analysis.transitionsWithMultiplePolicies,9);
  assert.equal(analysis.newPlayerVerbsAdded,0);
  for(const row of analysis.transitions)assert.ok(row.distinctPolicySignatures>=2);
});

test('R3 session kernel accepts compiled R4 rules without changing default reward authority',()=>{
  const compiled=compileRunRecipe(design,FIRST_BREADTH_ARC);
  const run=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route','route','route','route'],
  });
  const first=publicView(run);
  assert.equal(first.current?.currentContext.id,design.cycles[0].id);
  assert.equal(first.current?.executionForecast.id,design.cycles[0].id);
  assert.equal(first.contract.targetTotal,560);

  for(let i=0;i<7;i++){
    selectArchitecture(run,'route');
    commitRound(run);
    if(i<6)nextRound(run);
  }
  const done=publicView(run);
  assert.equal(done.sessionStatus,'SUCCESS');
  assert.equal(done.totalNet,700);
  assert.equal(done.history.length,7);
  assert.equal(done.contract.targetTotal,560);
});

test('seven-beat arc can also terminate in mathematically unrecoverable failure',()=>{
  const compiled=compileRunRecipe(design,FIRST_BREADTH_ARC);
  const run=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route','route','route','route'],
  });

  for(let i=0;i<4;i++){
    selectArchitecture(run,'source');
    commitRound(run);
    if(i<3&&publicView(run).sessionStatus==='ACTIVE')nextRound(run);
  }
  const view=publicView(run);
  assert.equal(view.sessionStatus,'FAILURE');
  assert.equal(view.totalNet,238);
  assert.equal(view.contract.maxRecoverableTotal,538);
  assert.equal(view.contract.status,'FAILED_UNRECOVERABLE');
});

test('R4 content metadata cannot mint product or Human authority',()=>{
  const compiled=compileRunRecipe(design,FIRST_BREADTH_ARC);
  assert.equal(compiled.productSelected,false);
  assert.equal(compiled.g0Entered,false);
  assert.equal(compiled.humanOutcomeEstablished,false);
  assert.equal(compiled.gameCoreChanged,false);
});


test('R4 is a reproducible LEGO-planned repository asset with bounded authority',()=>{
  const evidence=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/causal-lag-content-r4/evidence/mechanical-acceptance-r4.json',import.meta.url),'utf8'));
  const pkg=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8'));
  const experimentReadme=readFileSync(new URL('../experiments/product-composition-r1/causal-lag-content-r4/README.md',import.meta.url),'utf8');
  const rootReadme=readFileSync(new URL('../README.md',import.meta.url),'utf8');
  const project=readFileSync(new URL('../.ordivon/project.yaml',import.meta.url),'utf8');
  const plan=JSON.parse(readFileSync(new URL('../planning/lego-plan-r1.json',import.meta.url),'utf8'));

  assert.equal(evidence.pass,true);
  assert.equal(evidence.designDigest,'sha256:19a258b457f4bbdeaf1e97a24c01bd9b800f0e50a4e3ffebe857e75290e0ac7c');
  assert.equal(evidence.transitionAnalysis.transitionCount,9);
  assert.equal(evidence.transitionAnalysis.distinctPolicySignatures,7);
  assert.equal(evidence.transitionAnalysis.transitionsWithMultiplePolicies,9);
  assert.equal(evidence.terminalWitnesses.success.totalNet,700);
  assert.equal(evidence.terminalWitnesses.failure.totalNet,238);
  assert.equal(evidence.terminalWitnesses.failure.contract.maxRecoverableTotal,538);
  assert.equal(evidence.defaultR3Compatibility.roundCount,4);
  assert.equal(evidence.defaultR3Compatibility.targetTotal,320);
  assert.equal(evidence.productSelected,false);
  assert.equal(evidence.g0Entered,false);
  assert.equal(evidence.humanOutcomeEstablished,false);
  assert.equal(evidence.gameCoreChanged,false);

  assert.equal(pkg.scripts['eval:causal-lag:r4'],'node experiments/product-composition-r1/causal-lag-content-r4/scripts/mechanical-acceptance.ts');
  assert.equal(pkg.scripts['e2e:causal-lag:r4'],'node experiments/product-composition-r1/causal-lag-content-r4/scripts/e2e-causal-lag-content-r4.ts');
  assert.match(pkg.scripts.webcheck,/causal-lag-content-r4\/web\/\*\.js/);

  assert.match(experimentReadme,/Question Compiler/);
  assert.match(experimentReadme,/C-K Design/);
  assert.match(experimentReadme,/Compositional Contracts/);
  assert.match(experimentReadme,/Feedback Control/);
  assert.match(experimentReadme,/7 distinct policy signatures/);
  assert.match(rootReadme,/causal-lag-content-r4/i);

  const nodes=new Map<string,any>(plan.nodes.map((node:any)=>[node.id,node]));
  assert.equal(nodes.get('G06')?.label,'StatefulSessionKernel');
  assert.equal(nodes.get('G07')?.label,'ContentGrammarCompiler');
  assert.equal(nodes.get('G08')?.label,'BreadthVerifier');
  assert.ok(plan.edges.some((edge:any)=>edge.from==='G07'&&edge.to==='G06'&&edge.type==='CONTROL'));
  assert.ok(plan.edges.some((edge:any)=>edge.from==='G08'&&edge.to==='G04'&&edge.type==='EVIDENCE'));

  for(const path of [
    'experiments/product-composition-r1/causal-lag-content-r4/README.md',
    'experiments/product-composition-r1/causal-lag-content-r4/content-grammar.js',
    'experiments/product-composition-r1/causal-lag-content-r4/web/app.js',
    'experiments/product-composition-r1/causal-lag-content-r4/scripts/mechanical-acceptance.ts',
    'experiments/product-composition-r1/causal-lag-content-r4/scripts/e2e-causal-lag-content-r4.ts',
    'experiments/product-composition-r1/causal-lag-content-r4/evidence/mechanical-acceptance-r4.json',
  ]) assert.match(project,new RegExp(path.replaceAll('/','\\/')));
});
