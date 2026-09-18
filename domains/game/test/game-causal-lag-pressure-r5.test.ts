import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {commitRound,createSessionRun,inspect,nextRound,publicView,selectArchitecture} from '../experiments/product-composition-r1/causal-lag-session-r3/web/core.js';
// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {FIRST_BREADTH_ARC,compileRunRecipe} from '../experiments/product-composition-r1/causal-lag-content-r4/content-grammar.js';
// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {PRESSURE_PROFILES,FIRST_PRESSURE_RUN,compilePressureRun} from '../experiments/product-composition-r1/causal-lag-pressure-r5/pressure-topology.js';

const design=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-causal-works-f0/design.json',import.meta.url),'utf8'));

test('R5 pressure profiles vary information price without changing switch inertia',()=>{
  assert.deepEqual(PRESSURE_PROFILES,{
    SCAN_CHEAP:{diagnosticCost:3,switchCost:8},
    BASELINE:{diagnosticCost:6,switchCost:8},
    SCAN_EXPENSIVE:{diagnosticCost:12,switchCost:8},
  });
});

test('R5 content references pressure by identity and compiles a ten-beat chain',()=>{
  const compiled=compilePressureRun(design,FIRST_PRESSURE_RUN);
  assert.equal(compiled.unitCount,10);
  assert.equal(compiled.sessionRules.roundCount,10);
  assert.equal(compiled.sessionRules.targetTotal,780);
  assert.equal(compiled.sessionRules.initialArchitecture,'route');
  assert.deepEqual(compiled.units.map((u:any)=>u.pressureProfileId),[
    'SCAN_CHEAP',
    'SCAN_CHEAP',
    'BASELINE',
    'BASELINE',
    'SCAN_EXPENSIVE',
    'SCAN_EXPENSIVE',
    'SCAN_EXPENSIVE',
    'BASELINE',
    'SCAN_CHEAP',
    'SCAN_CHEAP',
  ]);
  assert.deepEqual(compiled.sessionRules.contextChain,[
    {sourceCycleIndex:0,executionCycleIndex:0},
    {sourceCycleIndex:0,executionCycleIndex:1},
    {sourceCycleIndex:1,executionCycleIndex:1},
    {sourceCycleIndex:1,executionCycleIndex:2},
    {sourceCycleIndex:2,executionCycleIndex:2},
    {sourceCycleIndex:2,executionCycleIndex:0},
    {sourceCycleIndex:0,executionCycleIndex:0},
    {sourceCycleIndex:0,executionCycleIndex:1},
    {sourceCycleIndex:1,executionCycleIndex:2},
    {sourceCycleIndex:2,executionCycleIndex:0},
  ]);
  assert.deepEqual(compiled.sessionRules.pressureChain.map((p:any)=>p.diagnosticCost),[3,3,6,6,12,12,12,6,3,3]);
  assert.deepEqual(compiled.sessionRules.pressureChain.map((p:any)=>p.switchCost),Array(10).fill(8));
  assert.equal(compiled.newPlayerVerbsAdded,0);
});

test('pressure content cannot smuggle numeric costs into the content unit',()=>{
  const bad={
    ...FIRST_PRESSURE_RUN,
    units:FIRST_PRESSURE_RUN.units.map((u:any,i:number)=>i===0?{...u,diagnosticCost:0}:u),
  };
  assert.throws(()=>compilePressureRun(design,bad),/content unit cannot own diagnosticCost/i);
});

test('unknown pressure-profile identity fails closed',()=>{
  const bad={
    ...FIRST_PRESSURE_RUN,
    units:FIRST_PRESSURE_RUN.units.map((u:any,i:number)=>i===4?{...u,pressureProfileId:'FREE_SCAN'}:u),
  };
  assert.throws(()=>compilePressureRun(design,bad),/pressure profile/i);
});

test('R3 kernel applies resolved per-round pressure costs and exposes only current costs',()=>{
  const sessionRules={
    roundCount:2,
    targetTotal:150,
    initialArchitecture:'route',
    contextChain:[
      {sourceCycleIndex:0,executionCycleIndex:0},
      {sourceCycleIndex:0,executionCycleIndex:1},
    ],
    pressureChain:[
      {profileId:'SCAN_CHEAP',diagnosticCost:3,switchCost:8},
      {profileId:'SCAN_EXPENSIVE',diagnosticCost:12,switchCost:8},
    ],
  };
  const run=createSessionRun(design,{
    sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route'],
  });
  let view=publicView(run);
  assert.deepEqual(view.current?.costPressure,{profileId:'SCAN_CHEAP',diagnosticCost:3,switchCost:8});
  assert.doesNotMatch(JSON.stringify(view).toLowerCase(),/stable|volatile|persistence|executioncause/);

  inspect(run,'route');
  selectArchitecture(run,'route');
  commitRound(run);
  view=publicView(run);
  assert.equal(view.current?.resolution?.diagnosticCost,3);
  assert.equal(view.current?.resolution?.switchCost,0);
  assert.equal(view.current?.resolution?.net,97);

  nextRound(run);
  view=publicView(run);
  assert.deepEqual(view.current?.costPressure,{profileId:'SCAN_EXPENSIVE',diagnosticCost:12,switchCost:8});

  inspect(run,'route');
  selectArchitecture(run,'route');
  commitRound(run);
  view=publicView(run);
  assert.equal(view.current?.resolution?.diagnosticCost,12);
  assert.equal(view.current?.resolution?.net,88);
  assert.equal(view.totalNet,185);
  assert.equal(view.sessionStatus,'SUCCESS');
});

test('pressureChain validation rejects length and negative-cost drift',()=>{
  const base={
    roundCount:2,
    targetTotal:150,
    initialArchitecture:'route',
    contextChain:[
      {sourceCycleIndex:0,executionCycleIndex:0},
      {sourceCycleIndex:0,executionCycleIndex:1},
    ],
  };
  assert.throws(()=>createSessionRun(design,{
    sessionRules:{...base,pressureChain:[{profileId:'X',diagnosticCost:3,switchCost:8}]},
  }),/pressureChain length/i);
  assert.throws(()=>createSessionRun(design,{
    sessionRules:{...base,pressureChain:[
      {profileId:'X',diagnosticCost:-1,switchCost:8},
      {profileId:'Y',diagnosticCost:3,switchCost:8},
    ]},
  }),/diagnosticCost/i);
});

test('R4 recipe without pressureChain retains historical design costs',()=>{
  const compiled=compileRunRecipe(design,FIRST_BREADTH_ARC);
  assert.equal('pressureChain' in compiled.sessionRules,false);
  const run=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route','route','route','route'],
  });
  let view=publicView(run);
  assert.deepEqual(view.current?.costPressure,{profileId:'DESIGN_DEFAULT',diagnosticCost:6,switchCost:8});
  inspect(run,'route');
  selectArchitecture(run,'route');
  commitRound(run);
  view=publicView(run);
  assert.equal(view.current?.resolution?.diagnosticCost,6);
  assert.equal(view.current?.resolution?.net,94);
});

test('ten-beat R5 run has explicit reachable success and unrecoverable failure',()=>{
  const compiled=compilePressureRun(design,FIRST_PRESSURE_RUN);

  const success=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:Array(10).fill('route'),
  });
  for(let i=0;i<10;i++){
    selectArchitecture(success,'route');
    commitRound(success);
    if(i<9)nextRound(success);
  }
  const s=publicView(success);
  assert.equal(s.sessionStatus,'SUCCESS');
  assert.equal(s.totalNet,1000);
  assert.equal(s.history.length,10);

  const failure=createSessionRun(design,{
    sessionRules:compiled.sessionRules,
    regime:'STABLE',
    initialCause:'route',
    transitionScript:Array(10).fill('route'),
  });
  while(publicView(failure).sessionStatus==='ACTIVE'){
    selectArchitecture(failure,'source');
    commitRound(failure);
    if(publicView(failure).sessionStatus==='ACTIVE')nextRound(failure);
  }
  const f=publicView(failure);
  assert.equal(f.sessionStatus,'FAILURE');
  assert.equal(f.history.length,6);
  assert.equal(f.totalNet,374);
  assert.equal(f.contract.maxRecoverableTotal,774);
  assert.equal(f.contract.targetTotal,780);
});

test('R5 compilation cannot mint Human, product, G0, or Game Core authority',()=>{
  const compiled=compilePressureRun(design,FIRST_PRESSURE_RUN);
  assert.equal(compiled.productSelected,false);
  assert.equal(compiled.g0Entered,false);
  assert.equal(compiled.humanOutcomeEstablished,false);
  assert.equal(compiled.gameCoreChanged,false);
});


test('R5 is a reproducible LEGO pressure-topology asset without project-node inflation',()=>{
  const evidence=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/causal-lag-pressure-r5/evidence/mechanical-acceptance-r5.json',import.meta.url),'utf8'));
  const pkg=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8'));
  const experimentReadme=readFileSync(new URL('../experiments/product-composition-r1/causal-lag-pressure-r5/README.md',import.meta.url),'utf8');
  const rootReadme=readFileSync(new URL('../README.md',import.meta.url),'utf8');
  const authority=readFileSync(new URL('../docs/authority.md',import.meta.url),'utf8');
  const project=readFileSync(new URL('../.ordivon/project.yaml',import.meta.url),'utf8');
  const plan=JSON.parse(readFileSync(new URL('../planning/lego-plan-r1.json',import.meta.url),'utf8'));

  assert.equal(evidence.pass,true);
  assert.equal(evidence.designDigest,'sha256:19a258b457f4bbdeaf1e97a24c01bd9b800f0e50a4e3ffebe857e75290e0ac7c');
  assert.equal(evidence.axisScreening.localStateCount,27);
  assert.equal(evidence.axisScreening.persistence.statesChanged,19);
  assert.equal(evidence.axisScreening.diagnosticCost.statesChanged,27);
  assert.equal(evidence.axisScreening.switchCost.statesChanged,18);
  assert.equal(evidence.axisScreening.contractTarget.statesChanged,0);
  assert.equal(evidence.regimeConditioning['0.2'].statesChanged,0);
  assert.equal(evidence.regimeConditioning['0.55'].statesChanged,16);
  assert.equal(evidence.regimeConditioning['0.9'].statesChanged,27);
  assert.equal(evidence.regimeConditioning['0.9'].cheapScanStates,27);
  assert.equal(evidence.regimeConditioning['0.9'].expensiveScanStates,0);
  assert.equal(evidence.explorationPolicy.used,false);
  assert.equal(evidence.terminalWitnesses.success.totalNet,1000);
  assert.equal(evidence.terminalWitnesses.failure.totalNet,374);
  assert.equal(evidence.terminalWitnesses.failure.contract.maxRecoverableTotal,774);
  assert.deepEqual(evidence.r4Compatibility.currentCostPressure,{profileId:'DESIGN_DEFAULT',diagnosticCost:6,switchCost:8});
  assert.equal(evidence.newPlayerVerbsAdded,0);
  assert.equal(evidence.productSelected,false);
  assert.equal(evidence.g0Entered,false);
  assert.equal(evidence.humanOutcomeEstablished,false);
  assert.equal(evidence.gameCoreChanged,false);

  assert.equal(pkg.scripts['eval:causal-lag:r5'],'node experiments/product-composition-r1/causal-lag-pressure-r5/scripts/mechanical-acceptance.ts');
  assert.equal(pkg.scripts['e2e:causal-lag:r5'],'node experiments/product-composition-r1/causal-lag-pressure-r5/scripts/e2e-causal-lag-pressure-r5.ts');
  assert.match(pkg.scripts.webcheck,/causal-lag-pressure-r5\/web\/\*\.js/);

  assert.match(experimentReadme,/Question Compiler/);
  assert.match(experimentReadme,/C-K Design/);
  assert.match(experimentReadme,/Feedback Control/);
  assert.match(experimentReadme,/Exploration Policy/);
  assert.match(experimentReadme,/27\/27/);
  assert.match(rootReadme,/causal-lag-pressure-r5/i);
  assert.match(authority,/R5 \*\*Pressure Run\*\*/);

  assert.equal(plan.nodes.length,8);
  assert.equal(plan.nodes.some((node:any)=>node.id==='G09'),false);
  const gs3=plan.slices.find((slice:any)=>slice.id==='GS3');
  assert.equal(gs3?.status,'COMPLETE');
  assert.deepEqual(gs3?.nodeIds,['G06','G07','G08']);
  assert.equal(plan.review.standing,'STABLE');

  for(const path of [
    'experiments/product-composition-r1/causal-lag-pressure-r5/README.md',
    'experiments/product-composition-r1/causal-lag-pressure-r5/pressure-topology.js',
    'experiments/product-composition-r1/causal-lag-pressure-r5/web/app.js',
    'experiments/product-composition-r1/causal-lag-pressure-r5/scripts/mechanical-acceptance.ts',
    'experiments/product-composition-r1/causal-lag-pressure-r5/scripts/e2e-causal-lag-pressure-r5.ts',
    'experiments/product-composition-r1/causal-lag-pressure-r5/evidence/mechanical-acceptance-r5.json',
  ]) assert.match(project,new RegExp(path.replaceAll('/','\\/')));
});
