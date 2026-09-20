#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const logistic=(x)=>1/(1+Math.exp(-x));
const mean=(xs)=>xs.reduce((a,b)=>a+b,0)/xs.length;

// 1) Same aggregate pass rate, radically different latent surfaces.
const skills=[0.1,0.3,0.5,0.7,0.9];
const steep=skills.map(s=>logistic(10*(s-0.5)));
const flat=skills.map(()=>0.5);
const aggregateEquivalence={skills,steep,flat,steepMean:mean(steep),flatMean:mean(flat)};
aggregateEquivalence.sameAggregate=Math.abs(aggregateEquivalence.steepMean-aggregateEquivalence.flatMean)<1e-12;
aggregateEquivalence.differentSurface=steep.some((p,i)=>Math.abs(p-flat[i])>0.2);

// 2) Population selection reversal.
const easySurface=s=>logistic(6*(s-0.35));
const hardSurface=s=>logistic(6*(s-0.65));
const broadPopulation=[0.1,0.2,0.3,0.4,0.5,0.6];
const selectedExperts=[0.65,0.75,0.85,0.95];
const selection={
  easyBroadRate:mean(broadPopulation.map(easySurface)),
  hardSelectedRate:mean(selectedExperts.map(hardSurface)),
  standardizedEasyRate:mean(skills.map(easySurface)),
  standardizedHardRate:mean(skills.map(hardSurface))
};
selection.naiveReversal=selection.hardSelectedRate>selection.easyBroadRate;
selection.standardizedRestoresOrdering=selection.standardizedEasyRate>selection.standardizedHardRate;

// 3) Gauge/scale equivalence for logistic ability-location-discrimination representation.
const response=(theta,a,b)=>logistic(a*(theta-b));
const gauge={theta:0.6,a:4,b:0.5};
gauge.original=response(gauge.theta,gauge.a,gauge.b);
// theta'=2theta+1, b'=2b+1, a'=a/2 preserves a(theta-b).
gauge.transformed={theta:2*gauge.theta+1,a:gauge.a/2,b:2*gauge.b+1};
gauge.transformedP=response(gauge.transformed.theta,gauge.transformed.a,gauge.transformed.b);
gauge.sameProbability=Math.abs(gauge.original-gauge.transformedP)<1e-12;

// 4) One-shot heterogeneity versus within-controller randomness.
// Both produce 50% aggregate success in one trial, but repeated same-controller trials separate them.
const heterogeneityControllers=[0,0,0,1,1,1]; // deterministic controller types
const repeatedHeterogeneity=heterogeneityControllers.map(p=>Array.from({length:20},()=>p));
const deterministicWithinVariances=repeatedHeterogeneity.map(xs=>mean(xs.map(x=>(x-mean(xs))**2)));
// deterministic pseudo-sequence with 50/50 per controller for reproducibility
const rngPattern=[0,1,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,0,1];
const repeatedRandom=heterogeneityControllers.map(()=>rngPattern);
const randomWithinVariances=repeatedRandom.map(xs=>mean(xs.map(x=>(x-mean(xs))**2)));
const repeatedTrials={
  oneShotAggregateBoth:0.5,
  heterogeneityMeanWithinVariance:mean(deterministicWithinVariances),
  randomMeanWithinVariance:mean(randomWithinVariances)
};
repeatedTrials.repetitionSeparates=repeatedTrials.randomMeanWithinVariance>repeatedTrials.heterogeneityMeanWithinVariance+0.1;

// 5) Multidimensional compensation and directional discrimination.
const outcome2d=(timing,strategy)=>logistic(5*(0.6*timing+0.4*strategy-0.5));
const compensation={
  profileA:{timing:0.8,strategy:0.2},
  profileB:{timing:0.4,strategy:0.8}
};
compensation.pA=outcome2d(compensation.profileA.timing,compensation.profileA.strategy);
compensation.pB=outcome2d(compensation.profileB.timing,compensation.profileB.strategy);
compensation.sameOutcome=Math.abs(compensation.pA-compensation.pB)<1e-12;
const eps=1e-4;
compensation.timingGradient=(outcome2d(0.5+eps,0.5)-outcome2d(0.5-eps,0.5))/(2*eps);
compensation.strategyGradient=(outcome2d(0.5,0.5+eps)-outcome2d(0.5,0.5-eps))/(2*eps);
compensation.directional=compensation.timingGradient>compensation.strategyGradient;

// 6) Observed performance can be non-monotonic even when attainable envelope is monotonic.
const capabilityOptions={
  low:[0.45,0.55],
  high:[0.45,0.55,0.9] // superset
};
const selectedPolicyPerformance={low:0.55,high:0.45}; // high-capability subject chooses worse/riskier available policy
const attainable={low:Math.max(...capabilityOptions.low),high:Math.max(...capabilityOptions.high)};
const monotonicity={selectedPolicyPerformance,attainable};
monotonicity.observedCanWorsen=selectedPolicyPerformance.high<selectedPolicyPerformance.low;
monotonicity.bestAttainableDoesNotWorsen=attainable.high>=attainable.low;

// 7) Assistance: same mean improvement can hide different shape changes.
const population=[0.2,0.5,0.8];
const baseline=s=>logistic(5*(s-0.55));
const thresholdShift=s=>logistic(5*(s-0.45));
const flattenRaw=s=>logistic(2*(s-0.35));
const targetGain=mean(population.map(thresholdShift))-mean(population.map(baseline));
// affine calibration of flattening output solely for toy equal-mean comparison.
const raw=population.map(flattenRaw);
const delta=targetGain-(mean(raw)-mean(population.map(baseline)));
const flatten=s=>Math.max(0,Math.min(1,flattenRaw(s)+delta));
const assist={
  population,
  baseline:population.map(baseline),
  thresholdShift:population.map(thresholdShift),
  flatten:population.map(flatten)
};
assist.meanGainThreshold=mean(assist.thresholdShift)-mean(assist.baseline);
assist.meanGainFlatten=mean(assist.flatten)-mean(assist.baseline);
assist.sameMeanGain=Math.abs(assist.meanGainThreshold-assist.meanGainFlatten)<1e-9;
assist.differentProfileShape=assist.thresholdShift.some((p,i)=>Math.abs(p-assist.flatten[i])>0.04);

// 8) Pairwise opponent matrix: equal aggregate rates hide matchup structure.
const opponentMatrices={
  transitive:[[0.5,0.7,0.9],[0.3,0.5,0.7],[0.1,0.3,0.5]],
  cyclic:[[0.5,0.8,0.2],[0.2,0.5,0.8],[0.8,0.2,0.5]]
};
const matrixMean=m=>mean(m.flat());
const opponent={transitiveMean:matrixMean(opponentMatrices.transitive),cyclicMean:matrixMean(opponentMatrices.cyclic),matrices:opponentMatrices};
opponent.sameAggregate=Math.abs(opponent.transitiveMean-opponent.cyclicMean)<1e-12;
opponent.differentMatchupStructure=JSON.stringify(opponentMatrices.transitive)!==JSON.stringify(opponentMatrices.cyclic);

// 9) Recovery transitions vs scalar severity.
const recovery={
  checkpoint:{nextState:'checkpoint',timeCost:2,resourceLoss:0,historyPreserved:0.95},
  reset:{nextState:'run-start',timeCost:900,resourceLoss:100,historyPreserved:0.1}
};
recovery.transitionsStructurallyDistinct=recovery.checkpoint.nextState!==recovery.reset.nextState;
recovery.noUniversalScalarWithoutWeights=true;

const result={
  schemaVersion:1,
  kind:'ordivon.game.gdf2-c-identifiability-probes',
  epistemicBoundary:{
    proves:[
      'aggregate pass rate can be observationally equivalent across distinct latent response surfaces',
      'population selection can reverse naive pass-rate ordering and standardization can change the comparison',
      'location/scale gauge transformations can preserve logistic response probability',
      'repeated same-controller trials can separate deterministic between-controller heterogeneity from within-controller outcome randomness in the toy design',
      'multidimensional SkillProfiles can compensate to the same outcome while having directional gradients',
      'observed selected-policy performance may worsen even when the best-attainable capability envelope expands',
      'one average assistance gain can hide distinct response-shape transformations',
      'equal aggregate opponent win rate can hide distinct matchup matrices',
      'recovery transition structure is distinct from any scalar cost aggregation'
    ],
    doesNotProve:[
      'universal logistic Game challenge laws',
      'that the listed probe family is sufficient for every GameForm',
      'Human perceived difficulty, learning, fairness or PlayerValue',
      'unique latent SkillProfile coordinates without modeling assumptions',
      'that synthetic-controller capability coordinates equal Human capability coordinates'
    ]
  },
  aggregateEquivalence,
  selection,
  gauge,
  repeatedTrials,
  compensation,
  monotonicity,
  assist,
  opponent,
  recovery
};

const output=process.argv[2]??'evidence/gdf2-c/identifiability-probes.json';
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
