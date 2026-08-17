#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const logistic = (skill, b, a = 1) => 1 / (1 + Math.exp(a * (b - skill)));
const slopeAt = (fn, x, d=1e-4) => (fn(x+d)-fn(x-d))/(2*d);

// Equal success at the test profile, different discrimination.
const testSkill = 0.5;
const equalSuccess = {
  steep: { p: logistic(testSkill, 0.5, 8), slope: slopeAt((s)=>logistic(s,0.5,8), testSkill) },
  shallow: { p: logistic(testSkill, 0.5, 0.4), slope: slopeAt((s)=>logistic(s,0.5,0.4), testSkill) }
};
equalSuccess.sameP = Math.abs(equalSuccess.steep.p-equalSuccess.shallow.p) < 1e-9;
equalSuccess.differentDiscrimination = equalSuccess.steep.slope > equalSuccess.shallow.slope * 10;

// Equal discrimination shape, different threshold/location.
const equalSlopeDifferentThreshold = {
  easy: { b:0.3, a:4, pAt05:logistic(0.5,0.3,4) },
  hard: { b:0.8, a:4, pAt05:logistic(0.5,0.8,4) }
};
equalSlopeDifferentThreshold.sameDiscriminationParameter = equalSlopeDifferentThreshold.easy.a === equalSlopeDifferentThreshold.hard.a;
equalSlopeDifferentThreshold.differentThreshold = equalSlopeDifferentThreshold.easy.b !== equalSlopeDifferentThreshold.hard.b;

// Same immediate capability surface, different failure/recovery costs.
const recovery = {
  capabilitySurfaceId: 'surface-X',
  cheapCheckpoint: { retryTimeSec:2, resourceLoss:0, persistentHistoryLoss:0 },
  severeReset: { retryTimeSec:900, resourceLoss:100, persistentHistoryLoss:0.9 }
};
recovery.sameImmediateDemand = true;
recovery.differentRecoveryCost = recovery.cheapCheckpoint.retryTimeSec !== recovery.severeReset.retryTimeSec;

// Same target skill, change skill-independent random floor/ceiling component.
const chanceMix = (skill, chanceWeight) => chanceWeight*0.5 + (1-chanceWeight)*logistic(skill,0.5,6);
const stochasticity = {
  mostlySkill: { chanceWeight:0.1, p:chanceMix(0.5,0.1), slope:slopeAt((s)=>chanceMix(s,0.1),0.5) },
  mostlyChance: { chanceWeight:0.8, p:chanceMix(0.5,0.8), slope:slopeAt((s)=>chanceMix(s,0.8),0.5) }
};
stochasticity.sameMidpointProbability = Math.abs(stochasticity.mostlySkill.p-stochasticity.mostlyChance.p) < 1e-9;
stochasticity.skillSensitivityReducedByChance = stochasticity.mostlySkill.slope > stochasticity.mostlyChance.slope;

// Continuous/nonterminal expression surface.
const expressiveQuality = (skill) => 0.4 + 0.5*skill + 0.1*Math.sin(skill*Math.PI);
const continuousChallenge = {
  binaryFailureDefined:false,
  qualityAt02:expressiveQuality(0.2),
  qualityAt08:expressiveQuality(0.8)
};
continuousChallenge.capabilityChangesQuality = continuousChallenge.qualityAt08 > continuousChallenge.qualityAt02;

// Assistance transformations: threshold shift vs flattening vs relocation.
const assist = {
  baseline: { timingWeight:0.6, strategyWeight:0.4, threshold:0.6, discrimination:5 },
  accessAssist: { timingWeight:0.6, strategyWeight:0.4, threshold:0.45, discrimination:5 },
  automation: { timingWeight:0.1, strategyWeight:0.4, threshold:0.4, discrimination:2 },
  relocation: { timingWeight:0.15, strategyWeight:0.75, threshold:0.55, discrimination:5 }
};
const assistanceResults = {
  thresholdShiftWithoutFlattening: assist.accessAssist.threshold < assist.baseline.threshold && assist.accessAssist.discrimination === assist.baseline.discrimination,
  automationFlattensExpression: assist.automation.discrimination < assist.baseline.discrimination && assist.automation.timingWeight < assist.baseline.timingWeight,
  relocationChangesSkillDimensionWeights: assist.relocation.strategyWeight > assist.baseline.strategyWeight && assist.relocation.timingWeight < assist.baseline.timingWeight
};

// Opponent-relative surface.
const pvpWin = (self, opp) => logistic(self-opp, 0, 5);
const opponent = {
  selfSkill:0.7,
  vsNovice:pvpWin(0.7,0.3),
  vsExpert:pvpWin(0.7,0.9)
};
opponent.sameMapSameSelfDifferentDifficulty = opponent.vsNovice > opponent.vsExpert;

// History changes puzzle challenge without artifact/rule change.
const history = {
  samePuzzle:true,
  beforeSolutionMemory:{ effectiveKnowledge:0.2, pSuccess:logistic(0.2,0.65,7) },
  afterSolutionMemory:{ effectiveKnowledge:0.95, pSuccess:logistic(0.95,0.65,7) }
};
history.surfaceChangedByHistory = history.afterSolutionMemory.pSuccess > history.beforeSolutionMemory.pSuccess;

// Infeasible vs merely overmatched.
const feasibility = {
  infeasible:{ support:0, skillSensitivity:0 },
  overmatched:{ support:logistic(0.1,0.9,6), skillSensitivity:slopeAt((s)=>logistic(s,0.9,6),0.1) }
};
feasibility.distinct = feasibility.infeasible.support === 0 && feasibility.overmatched.support > 0 && feasibility.overmatched.skillSensitivity > 0;

const result = {
  schemaVersion:1,
  kind:'ordivon.game.gdf2-b-functional-difficulty-probes',
  epistemicBoundary:{
    proves:[
      'equal success probability can coexist with different capability discrimination',
      'difficulty location/threshold and discrimination can vary independently',
      'recovery/consequence severity can vary while immediate capability demand is held fixed',
      'skill-independent chance can flatten capability discrimination while preserving midpoint success probability',
      'continuous challenge can exist without binary failure',
      'assistance can shift threshold, flatten expression, or relocate skill dimensions',
      'opponent profile and history can alter the response relation without changing base content',
      'infeasibility and overmatched-but-possible conditions are structurally distinct'
    ],
    doesNotProve:[
      'that logistic curves are a universal Game difficulty law',
      'a universal scalar measure of challenge',
      'Human perceived difficulty, flow, frustration, fairness or PlayerValue',
      'empirical effect sizes of assistance or randomness',
      'that every SkillProfile admits one monotonic response surface'
    ]
  },
  equalSuccess,
  equalSlopeDifferentThreshold,
  recovery,
  stochasticity,
  continuousChallenge,
  assist,
  assistanceResults,
  opponent,
  history,
  feasibility
};

const output = process.argv[2] ?? 'evidence/gdf2-b/functional-difficulty-probes.json';
fs.mkdirSync(path.dirname(output), {recursive:true});
fs.writeFileSync(output, JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
