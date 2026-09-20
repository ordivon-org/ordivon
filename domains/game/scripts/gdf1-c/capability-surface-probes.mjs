#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// GDF1-C structural probes only. Numbers are synthetic counterexamples, not empirical estimates.

const causalGraph = {
  endpointError: ['hitQuality'],
  completionTime: ['formalScore'],
  hitQuality: ['formalScore'],
  animationStylePhase: ['styleValue'],
  redundantWristPath: [],
  inputDeviceAxis: ['normalizedControlSignal'],
  normalizedControlSignal: ['endpointError'],
  formalScore: [],
  styleValue: [],
};
const participantInfluence = new Set(['endpointError', 'completionTime', 'animationStylePhase', 'redundantWristPath', 'inputDeviceAxis', 'normalizedControlSignal']);

function reachesTarget(start, targets, seen = new Set()) {
  if (targets.has(start)) return true;
  if (seen.has(start)) return false;
  seen.add(start);
  return (causalGraph[start] ?? []).some((next) => reachesTarget(next, targets, seen));
}

function deriveTRVS(targets) {
  const targetSet = new Set(targets);
  return Object.keys(causalGraph)
    .filter((v) => participantInfluence.has(v) && reachesTarget(v, targetSet, new Set()))
    .sort();
}

const scoreTRVS = deriveTRVS(['formalScore']);
const styleTRVS = deriveTRVS(['styleValue']);
const combinedTRVS = deriveTRVS(['formalScore', 'styleValue']);

const actionContract = {
  gameActions: ['AIM', 'FIRE'],
  mappingA: { device: 'mouse', expression: 'mouse-delta', normalizedActions: ['AIM', 'FIRE'] },
  mappingB: { device: 'adaptive-stick', expression: 'stick-deflection', normalizedActions: ['AIM', 'FIRE'] },
};
const remap = {
  sameGameActionSemantics: JSON.stringify(actionContract.mappingA.normalizedActions) === JSON.stringify(actionContract.mappingB.normalizedActions),
  differentInputExpression: actionContract.mappingA.expression !== actionContract.mappingB.expression,
  accessCanDiffer: true,
  initialMappingSpecificPerformanceCanDiffer: true,
};

const profiles = {
  peakSpecialist: {
    base: { score: 0.97, timing: 0.93 },
    perturbation: { score: 0.54, timing: 0.58 },
    remap: { score: 0.61, timing: 0.62 },
    delayedRetention: { score: 0.76, timing: 0.75 },
  },
  robustGeneralist: {
    base: { score: 0.90, timing: 0.86 },
    perturbation: { score: 0.83, timing: 0.82 },
    remap: { score: 0.80, timing: 0.78 },
    delayedRetention: { score: 0.85, timing: 0.83 },
  },
};

function flattenProfile(p) {
  return Object.entries(p).flatMap(([condition, metrics]) => Object.entries(metrics).map(([metric, value]) => ({ condition, metric, value })));
}
function dominates(a, b) {
  const aa = flattenProfile(a);
  const bb = flattenProfile(b);
  const byKey = new Map(bb.map((x) => [`${x.condition}:${x.metric}`, x.value]));
  let strictly = false;
  for (const x of aa) {
    const y = byKey.get(`${x.condition}:${x.metric}`);
    if (y === undefined || x.value < y) return false;
    if (x.value > y) strictly = true;
  }
  return strictly;
}
const profileComparison = {
  peakDominatesRobust: dominates(profiles.peakSpecialist, profiles.robustGeneralist),
  robustDominatesPeak: dominates(profiles.robustGeneralist, profiles.peakSpecialist),
};
profileComparison.incomparableWithoutWeighting = !profileComparison.peakDominatesRobust && !profileComparison.robustDominatesPeak;

const humanIndependentSkill = { steeringLine: 0.62, brakingTiming: 0.57, recovery: 0.48 };
const systemContribution = { stabilization: 0.88, correction: 0.92 };
const jointPerformance = {
  unassistedLapQuality: 0.60,
  assistedLapQuality: 0.83,
  humanIndependentSkillBefore: humanIndependentSkill,
  humanIndependentSkillAfterImmediateAssistedRun: humanIndependentSkill,
};
const sharedControl = {
  immediateJointImprovement: jointPerformance.assistedLapQuality > jointPerformance.unassistedLapQuality,
  humanIndependentSkillNotAutomaticallyUpdated: JSON.stringify(jointPerformance.humanIndependentSkillBefore) === JSON.stringify(jointPerformance.humanIndependentSkillAfterImmediateAssistedRun),
};

const entryThreshold = 0.70;
const floorCases = {
  manualMapping: { effectiveCompletionCapability: 0.64, meetsThreshold: false },
  remappedAccess: { effectiveCompletionCapability: 0.73, meetsThreshold: true },
  sharedAssist: { effectiveCompletionCapability: 0.82, meetsThreshold: true },
};
const floorRelation = {
  threshold: entryThreshold,
  changesWithConfiguration: new Set(Object.values(floorCases).map((x) => x.meetsThreshold)).size > 1,
};

const expressionCurves = {
  coarseActionResolution: [
    { capability: 0.5, value: 0.5 },
    { capability: 0.7, value: 0.7 },
    { capability: 0.9, value: 0.8 },
    { capability: 1.0, value: 0.8 },
  ],
  fineActionResolution: [
    { capability: 0.5, value: 0.5 },
    { capability: 0.7, value: 0.7 },
    { capability: 0.9, value: 0.9 },
    { capability: 1.0, value: 0.98 },
  ],
};
const saturation = {
  coarseSaturatesEarlier: expressionCurves.coarseActionResolution.at(-1).value === expressionCurves.coarseActionResolution.at(-2).value,
  fineStillExpressesDifference: expressionCurves.fineActionResolution.at(-1).value > expressionCurves.fineActionResolution.at(-2).value,
};

const techniqueFamily = {
  id: 'cornering-family',
  invariants: ['brake-before-apex', 'steer-through-apex', 'accelerate-on-exit'],
  normalDynamics: { brakeLeadMs: 620, steeringRate: 0.62, throttleResumeMs: 120 },
  fastDynamics: { brakeLeadMs: 810, steeringRate: 0.74, throttleResumeMs: 170 },
};
const techniqueTransfer = {
  sameFamily: true,
  parametersChanged: JSON.stringify(techniqueFamily.normalDynamics) !== JSON.stringify(techniqueFamily.fastDynamics),
  exactSequenceNotInvariant: true,
};

const transformations = [
  { id: 'T-map', changed: ['input mapping'], heldFixed: ['GameAction semantics', 'formal evaluation'] },
  { id: 'T-assist', changed: ['control contribution topology'], heldFixed: ['task goal', 'GameAction semantics'] },
  { id: 'T-dynamics', changed: ['world/control dynamics', 'timing'], heldFixed: ['technique functional invariants', 'task goal'] },
];

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-c-capability-surface-probes',
  epistemicBoundary: {
    proves: [
      'TaskRelevantVariableSet can be derived from a declared causal/evaluation graph before expert telemetry in this toy model',
      'changing evaluation target can change the relevant variable set without changing observed expert data',
      'same GameAction semantics can coexist with different physical/input mappings',
      'multi-condition SkillProfiles can be incomparable without declared weighting',
      'joint assisted performance can improve without automatically changing the Human-independent SkillProfile',
      'entry requirement satisfaction and capability-expression saturation can change with control configuration',
      'a TechniqueFamily can preserve functional invariants while parameters change under altered dynamics'
    ],
    doesNotProve: [
      'empirical effect sizes',
      'that formalScore or styleValue are universal PlayerValue targets',
      'that assistance never teaches Human skill',
      'that all techniques admit one clean family classification',
      'that one profile comparison should drive design without PlayerValue evidence'
    ]
  },
  taskRelevantVariables: { scoreTRVS, styleTRVS, combinedTRVS },
  actionContract,
  remap,
  profiles,
  profileComparison,
  humanIndependentSkill,
  systemContribution,
  jointPerformance,
  sharedControl,
  floorCases,
  floorRelation,
  expressionCurves,
  saturation,
  techniqueFamily,
  techniqueTransfer,
  transformations,
};

const output = process.argv[2] ?? 'evidence/gdf1-c/capability-surface-probes.json';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
