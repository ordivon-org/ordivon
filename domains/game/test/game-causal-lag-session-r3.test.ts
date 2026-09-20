import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

// @ts-expect-error Browser-compatible JS core intentionally has no declaration file.
import {SESSION_RULES,commitRound,createSessionRun,inspect,nextRound,publicView,selectArchitecture} from '../experiments/product-composition-r1/causal-lag-session-r3/web/core.js';

const design=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-causal-works-f0/design.json',import.meta.url),'utf8'));

test('R3 freezes a four-round chained-context contract without changing PC01 rewards',()=>{
  assert.deepEqual(SESSION_RULES,{
    roundCount:4,
    targetTotal:320,
    initialArchitecture:'route',
    contextChain:[
      {sourceCycleIndex:0,executionCycleIndex:1},
      {sourceCycleIndex:1,executionCycleIndex:2},
      {sourceCycleIndex:2,executionCycleIndex:0},
      {sourceCycleIndex:0,executionCycleIndex:1},
    ],
  });
});

test('the architecture actually committed in one round becomes the built architecture in the next',()=>{
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'process',
    transitionScript:['process','process','process','process'],
  });
  assert.equal(publicView(run).current?.previousArchitecture,'route');
  selectArchitecture(run,'process');
  commitRound(run);
  nextRound(run);
  const next=publicView(run);
  assert.equal(next.current?.previousArchitecture,'process');
});

test('the execution cause of one round becomes the current hidden cause of the next',()=>{
  const run=createSessionRun(design,{
    regime:'VOLATILE',
    initialCause:'process',
    transitionScript:['route','source','process','route'],
  });
  selectArchitecture(run,'process');
  const resolved=commitRound(run);
  assert.equal(resolved.current?.resolution?.executionCause,'route');
  nextRound(run);
  const next=publicView(run);
  assert.equal(next.current?.currentContext.id,design.cycles[1].id);
  assert.equal(next.current?.executionForecast.id,design.cycles[2].id);
  assert.equal((run as any).current.sourceCause,'route');
});

test('context progression is a real chain across all four rounds',()=>{
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  const expected=[
    [design.cycles[0].id,design.cycles[1].id],
    [design.cycles[1].id,design.cycles[2].id],
    [design.cycles[2].id,design.cycles[0].id],
    [design.cycles[0].id,design.cycles[1].id],
  ];
  for(let i=0;i<expected.length;i++){
    const view=publicView(run);
    const pair=expected[i]!;
    assert.equal(view.current?.currentContext.id,pair[0]);
    assert.equal(view.current?.executionForecast.id,pair[1]);
    selectArchitecture(run,'route');
    commitRound(run);
    if(i<expected.length-1)nextRound(run);
  }
});

test('diagnostic and architecture-switch costs now contribute to one session-wide contract',()=>{
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'process',
    transitionScript:['process','process','process','process'],
  });
  inspect(run,'route');
  selectArchitecture(run,'process');
  const view=commitRound(run);
  assert.equal(view.current?.resolution?.baseReward,100);
  assert.equal(view.current?.resolution?.diagnosticCost,6);
  assert.equal(view.current?.resolution?.switchCost,8);
  assert.equal(view.current?.resolution?.net,86);
  assert.equal(view.totalNet,86);
  assert.equal(view.contract.targetTotal,320);
  assert.equal(view.contract.remainingTarget,234);
  assert.equal(view.contract.status,'ACTIVE');
});

test('a coherent high-performing four-round run reaches explicit SUCCESS',()=>{
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  for(let i=0;i<4;i++){
    selectArchitecture(run,'route');
    commitRound(run);
    if(i<3)nextRound(run);
  }
  const view=publicView(run);
  assert.equal(view.sessionStatus,'SUCCESS');
  assert.equal(view.totalNet,400);
  assert.equal(view.contract.remainingTarget,0);
  assert.equal(view.current?.phase,'resolved');
  assert.throws(()=>nextRound(run),/terminal/i);
});

test('a run fails as soon as the contract becomes mathematically unrecoverable',()=>{
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  for(let i=0;i<2;i++){
    selectArchitecture(run,'source');
    commitRound(run);
    if(i<1)nextRound(run);
  }
  const view=publicView(run);
  assert.equal(view.totalNet,115);
  assert.equal(view.sessionStatus,'FAILURE');
  assert.equal(view.contract.maxRecoverableTotal,315);
  assert.equal(view.contract.status,'FAILED_UNRECOVERABLE');
  assert.throws(()=>nextRound(run),/terminal/i);
});

test('before resolution public state exposes context and history but not hidden regime or future cause',()=>{
  const run=createSessionRun(design,{
    regime:'VOLATILE',
    initialCause:'process',
    transitionScript:['route','source','process','route'],
  });
  const view=publicView(run);
  const text=JSON.stringify(view).toLowerCase();
  assert.doesNotMatch(text,/stable|volatile|hiddenregime|executioncause/);
  assert.equal(view.sessionStatus,'ACTIVE');
  assert.equal(view.current?.phase,'decision');
  assert.equal(view.current?.previousArchitecture,'route');
  assert.equal(view.history.length,0);
});

test('R3 does not mint Human or product authority',()=>{
  const run=createSessionRun(design,{
    regime:'STABLE',
    initialCause:'route',
    transitionScript:['route','route','route','route'],
  });
  const view=publicView(run);
  assert.equal(view.productSelected,false);
  assert.equal(view.g0Entered,false);
  assert.equal(view.humanOutcomeEstablished,false);
  assert.equal(view.gameCoreChanged,false);
});


test('R3 is a reproducible repository asset with explicit session continuity authority',()=>{
  const evidence=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/causal-lag-session-r3/evidence/mechanical-acceptance-r3.json',import.meta.url),'utf8'));
  const pkg=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8'));
  const experimentReadme=readFileSync(new URL('../experiments/product-composition-r1/causal-lag-session-r3/README.md',import.meta.url),'utf8');
  const rootReadme=readFileSync(new URL('../README.md',import.meta.url),'utf8');
  const project=readFileSync(new URL('../.ordivon/project.yaml',import.meta.url),'utf8');

  assert.equal(evidence.pass,true);
  assert.equal(evidence.designDigest,'sha256:19a258b457f4bbdeaf1e97a24c01bd9b800f0e50a4e3ffebe857e75290e0ac7c');
  assert.equal(evidence.terminalWitnesses.success.sessionStatus,'SUCCESS');
  assert.equal(evidence.terminalWitnesses.success.totalNet,400);
  assert.equal(evidence.terminalWitnesses.failure.sessionStatus,'FAILURE');
  assert.equal(evidence.terminalWitnesses.failure.totalNet,115);
  assert.equal(evidence.continuityWitness.secondRound.current.previousArchitecture,'process');
  assert.equal(evidence.publicBoundary.publicLeak,false);

  assert.equal(pkg.scripts['eval:causal-lag:r3'],'node experiments/product-composition-r1/causal-lag-session-r3/scripts/mechanical-acceptance.ts');
  assert.equal(pkg.scripts['e2e:causal-lag:r3'],'node experiments/product-composition-r1/causal-lag-session-r3/scripts/e2e-causal-lag-session-r3.ts');
  assert.match(pkg.scripts.webcheck,/causal-lag-session-r3\/web\/\*\.js/);

  assert.match(experimentReadme,/Stateful Run/);
  assert.match(experimentReadme,/architecture persistence/i);
  assert.match(experimentReadme,/latent cause/i);
  assert.match(experimentReadme,/SUCCESS/);
  assert.match(experimentReadme,/FAILURE/);
  assert.match(rootReadme,/causal-lag-session-r3/i);

  for(const path of [
    'experiments/product-composition-r1/causal-lag-session-r3/README.md',
    'experiments/product-composition-r1/causal-lag-session-r3/web/core.js',
    'experiments/product-composition-r1/causal-lag-session-r3/web/app.js',
    'experiments/product-composition-r1/causal-lag-session-r3/scripts/mechanical-acceptance.ts',
    'experiments/product-composition-r1/causal-lag-session-r3/scripts/e2e-causal-lag-session-r3.ts',
    'experiments/product-composition-r1/causal-lag-session-r3/evidence/mechanical-acceptance-r3.json',
  ]) assert.match(project,new RegExp(path.replaceAll('/','\\/')));
});
