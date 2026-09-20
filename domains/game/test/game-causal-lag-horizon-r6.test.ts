import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

// @ts-expect-error Browser-compatible JS module intentionally has no declaration file.
import {HORIZON_OBJECTIVE,VOLATILE_HORIZON_WITNESS,STABLE_HORIZON_WITNESS,analyzePressureCompositionSaturation,solveHorizonPolicy,solveMyopicPolicy} from '../experiments/product-composition-r1/causal-lag-horizon-r6/horizon-policy.js';

const design=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/pc01-causal-works-f0/design.json',import.meta.url),'utf8'));

test('R6 saturation screen does not falsely declare the R5 composition space saturated',()=>{
  const result=analyzePressureCompositionSaturation(design,{maxSequenceLength:5});
  assert.equal(result.localUnitCount,27);
  assert.equal(result.localEquivalenceClasses,20);
  assert.equal(result.redundantLocalUnits,7);
  assert.equal(result.uniqueFraction,20/27);
  assert.equal(result.baselineOnlyEquivalenceClasses,7);
  assert.deepEqual(
    result.sequenceSaturation.map((row:any)=>({
      length:row.length,
      validSequenceCount:row.validSequenceCount,
      distinctEquivalenceWords:row.distinctEquivalenceWords,
      uniqueFraction:row.uniqueFraction,
    })),
    [
      {length:1,validSequenceCount:27,distinctEquivalenceWords:20,uniqueFraction:20/27},
      {length:2,validSequenceCount:243,distinctEquivalenceWords:180,uniqueFraction:20/27},
      {length:3,validSequenceCount:2187,distinctEquivalenceWords:1620,uniqueFraction:20/27},
      {length:4,validSequenceCount:19683,distinctEquivalenceWords:14580,uniqueFraction:20/27},
      {length:5,validSequenceCount:177147,distinctEquivalenceWords:131220,uniqueFraction:20/27},
    ],
  );
  assert.equal(result.saturationEstablished,false);
});

test('volatile horizon witness makes locally suboptimal information strategically optimal',()=>{
  const myopic=solveMyopicPolicy(design,VOLATILE_HORIZON_WITNESS);
  assert.equal(myopic.objective,'IMMEDIATE_EXPECTED_NET');
  assert.equal(myopic.expectedImmediateNet,78.8);
  assert.deepEqual(myopic.policy,{
    diagnostic:'none',
    architectureByObservation:{NONE:'process'},
  });

  const low=solveHorizonPolicy(design,{...VOLATILE_HORIZON_WITNESS,remainingTarget:155});
  assert.equal(low.objective,HORIZON_OBJECTIVE);
  assert.equal(low.horizon,2);
  assert.equal(low.successProbability,0.68704);
  assert.equal(low.expectedTotalNet,157.808);
  assert.equal(low.firstPolicyImmediateExpectedNet,76.7);
  assert.deepEqual(low.firstPolicy,{
    diagnostic:'process',
    architectureByObservation:{FAULT:'process',OK:'route'},
  });
  assert.ok(low.firstPolicyImmediateExpectedNet<myopic.expectedImmediateNet);

  const high=solveHorizonPolicy(design,{...VOLATILE_HORIZON_WITNESS,remainingTarget:160});
  assert.equal(high.successProbability,0.636);
  assert.equal(high.expectedTotalNet,158.52);
  assert.deepEqual(high.firstPolicy,{
    diagnostic:'none',
    architectureByObservation:{NONE:'route'},
  });
});

test('same volatile local state changes current policy when only contract margin changes',()=>{
  const low=solveHorizonPolicy(design,{...VOLATILE_HORIZON_WITNESS,remainingTarget:155});
  const high=solveHorizonPolicy(design,{...VOLATILE_HORIZON_WITNESS,remainingTarget:160});
  assert.notDeepEqual(low.firstPolicy,high.firstPolicy);
  assert.deepEqual(low.window,high.window);
  assert.equal(low.persistence,high.persistence);
  assert.equal(low.previousArchitecture,high.previousArchitecture);
});

test('stable horizon witness independently shows target-sensitive current policy',()=>{
  const lower=solveHorizonPolicy(design,{...STABLE_HORIZON_WITNESS,remainingTarget:185});
  const higher=solveHorizonPolicy(design,{...STABLE_HORIZON_WITNESS,remainingTarget:190});
  assert.equal(lower.successProbability,0.70846);
  assert.deepEqual(lower.firstPolicy,{
    diagnostic:'route',
    architectureByObservation:{FAULT:'route',OK:'source'},
  });
  assert.equal(higher.successProbability,0.549);
  assert.deepEqual(higher.firstPolicy,{
    diagnostic:'none',
    architectureByObservation:{NONE:'route'},
  });
  assert.notDeepEqual(lower.firstPolicy,higher.firstPolicy);
});

test('R6 exact solver stays intentionally bounded and fails closed on noncomposing or oversized windows',()=>{
  assert.throws(()=>solveHorizonPolicy(design,{
    ...VOLATILE_HORIZON_WITNESS,
    units:[
      VOLATILE_HORIZON_WITNESS.units[0],
      {...VOLATILE_HORIZON_WITNESS.units[1],sourceCycleIndex:2},
    ],
    remainingTarget:155,
  }),/window seam/i);

  assert.throws(()=>solveHorizonPolicy(design,{
    ...VOLATILE_HORIZON_WITNESS,
    units:[
      ...VOLATILE_HORIZON_WITNESS.units,
      VOLATILE_HORIZON_WITNESS.units[1],
      VOLATILE_HORIZON_WITNESS.units[1],
    ],
    remainingTarget:155,
  }),/horizon.*1\.\.3/i);

  assert.throws(()=>solveHorizonPolicy(design,{
    ...VOLATILE_HORIZON_WITNESS,
    units:[
      {...VOLATILE_HORIZON_WITNESS.units[0],pressureProfileId:'FREE_SCAN'},
      VOLATILE_HORIZON_WITNESS.units[1],
    ],
    remainingTarget:155,
  }),/pressure profile/i);
});

test('R6 horizon oracle cannot mint player or product authority',()=>{
  const result=solveHorizonPolicy(design,{...VOLATILE_HORIZON_WITNESS,remainingTarget:155});
  assert.equal(result.newPlayerVerbsAdded,0);
  assert.equal(result.productSelected,false);
  assert.equal(result.g0Entered,false);
  assert.equal(result.humanOutcomeEstablished,false);
  assert.equal(result.gameCoreChanged,false);
  assert.equal(result.solverAuthority,'MECHANICAL_ORACLE_ONLY');
});


test('R6 is a reproducible LEGO branch-decision asset without a new project node',()=>{
  const evidence=JSON.parse(readFileSync(new URL('../experiments/product-composition-r1/causal-lag-horizon-r6/evidence/mechanical-acceptance-r6.json',import.meta.url),'utf8'));
  const pkg=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8'));
  const experimentReadme=readFileSync(new URL('../experiments/product-composition-r1/causal-lag-horizon-r6/README.md',import.meta.url),'utf8');
  const rootReadme=readFileSync(new URL('../README.md',import.meta.url),'utf8');
  const authority=readFileSync(new URL('../docs/authority.md',import.meta.url),'utf8');
  const project=readFileSync(new URL('../.ordivon/project.yaml',import.meta.url),'utf8');
  const plan=JSON.parse(readFileSync(new URL('../planning/lego-plan-r1.json',import.meta.url),'utf8'));

  assert.equal(evidence.pass,true);
  assert.equal(evidence.methodSnapshot.ordivonNextRevision,'2231438e8f293742c1f5f1a2622b3e567003f5e0');
  assert.equal(evidence.lensRouting.selectedLegoLens,'lego-ck-design');
  assert.deepEqual(evidence.lensRouting.domainMethods,['exact-combinatorial-enumeration','finite-horizon-dynamic-programming']);
  assert.equal(evidence.branchCompetition.saturation.localUnitCount,27);
  assert.equal(evidence.branchCompetition.saturation.localEquivalenceClasses,20);
  assert.equal(evidence.branchCompetition.saturation.saturationEstablished,false);
  assert.equal(evidence.branchCompetition.horizon.targetSensitiveWindowStates,96);
  assert.equal(evidence.branchCompetition.horizon.adjacentTargetPolicyTransitions,625);
  assert.equal(evidence.branchCompetition.selectedBranch,'HORIZON_AWARE_CONTRACT_PLANNING');

  assert.equal(evidence.volatileWitness.myopic.expectedImmediateNet,78.8);
  assert.equal(evidence.volatileWitness.target155.successProbability,0.68704);
  assert.deepEqual(evidence.volatileWitness.target155.firstPolicy,{
    diagnostic:'process',
    architectureByObservation:{FAULT:'process',OK:'route'},
  });
  assert.equal(evidence.volatileWitness.target160.successProbability,0.636);
  assert.deepEqual(evidence.volatileWitness.target160.firstPolicy,{
    diagnostic:'none',
    architectureByObservation:{NONE:'route'},
  });
  assert.equal(evidence.stableWitness.target185.successProbability,0.70846);
  assert.equal(evidence.stableWitness.target190.successProbability,0.549);

  assert.equal(evidence.browserCarrierCreated,false);
  assert.equal(evidence.newPlayerVerbsAdded,0);
  assert.equal(evidence.productSelected,false);
  assert.equal(evidence.g0Entered,false);
  assert.equal(evidence.humanOutcomeEstablished,false);
  assert.equal(evidence.gameCoreChanged,false);

  assert.equal(pkg.scripts['eval:causal-lag:r6'],'node experiments/product-composition-r1/causal-lag-horizon-r6/scripts/mechanical-acceptance.ts');
  assert.match(experimentReadme,/Lens Router/);
  assert.match(experimentReadme,/DOMAIN_METHOD/);
  assert.match(experimentReadme,/20 \/ 27/);
  assert.match(experimentReadme,/96/);
  assert.match(experimentReadme,/625/);
  assert.match(experimentReadme,/no browser carrier/i);
  assert.match(rootReadme,/causal-lag-horizon-r6/i);
  assert.match(authority,/R6 \*\*Horizon Contract Oracle\*\*/);

  assert.equal(plan.nodes.length,8);
  assert.equal(plan.nodes.some((node:any)=>node.id==='G09'),false);
  const gs4=plan.slices.find((slice:any)=>slice.id==='GS4');
  assert.equal(gs4?.status,'COMPLETE');
  assert.deepEqual(gs4?.nodeIds,['G06','G07','G08']);
  assert.equal(plan.review.standing,'STABLE');

  for(const path of [
    'experiments/product-composition-r1/causal-lag-horizon-r6/README.md',
    'experiments/product-composition-r1/causal-lag-horizon-r6/horizon-policy.js',
    'experiments/product-composition-r1/causal-lag-horizon-r6/scripts/mechanical-acceptance.ts',
    'experiments/product-composition-r1/causal-lag-horizon-r6/evidence/mechanical-acceptance-r6.json',
  ]) assert.match(project,new RegExp(path.replaceAll('/','\\/')));
});
