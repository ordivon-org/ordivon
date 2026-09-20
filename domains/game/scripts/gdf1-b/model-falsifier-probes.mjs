#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// Structural counterexamples only. Empirical claims live in the evidence ledger/doc.

const acquisitionRetention = {
  blockedLike: { acquisition: 95, delayedRetention: 70 },
  randomLike: { acquisition: 82, delayedRetention: 88 },
};

const singleScoreSkillFailure = {
  acquisitionWinner: acquisitionRetention.blockedLike.acquisition > acquisitionRetention.randomLike.acquisition ? 'blockedLike' : 'randomLike',
  retentionWinner: acquisitionRetention.blockedLike.delayedRetention > acquisitionRetention.randomLike.delayedRetention ? 'blockedLike' : 'randomLike',
};
singleScoreSkillFailure.rankingReversal = singleScoreSkillFailure.acquisitionWinner !== singleScoreSkillFailure.retentionWinner;

const variabilityProfiles = {
  controllerA: { endpointErrorSd: 1.0, redundantPathSd: 5.0 },
  controllerB: { endpointErrorSd: 2.2, redundantPathSd: 1.1 },
};
const taskRelevantVariability = {
  lowerGlobalVariabilityWinner: (variabilityProfiles.controllerA.endpointErrorSd + variabilityProfiles.controllerA.redundantPathSd) < (variabilityProfiles.controllerB.endpointErrorSd + variabilityProfiles.controllerB.redundantPathSd) ? 'A' : 'B',
  lowerTaskRelevantErrorWinner: variabilityProfiles.controllerA.endpointErrorSd < variabilityProfiles.controllerB.endpointErrorSd ? 'A' : 'B',
};
taskRelevantVariability.rankingDiffersByVariableChoice = taskRelevantVariability.lowerGlobalVariabilityWinner !== taskRelevantVariability.lowerTaskRelevantErrorWinner;

const assistance = {
  manual: { exactCommandExecution: 1.0, taskPerformance: 0.62, agencyProxy: 0.55 },
  assisted: { exactCommandExecution: 0.58, taskPerformance: 0.86, agencyProxy: 0.70 },
};
const manualControlMonotonicity = {
  lessExactCommandExecution: assistance.assisted.exactCommandExecution < assistance.manual.exactCommandExecution,
  higherPerformance: assistance.assisted.taskPerformance > assistance.manual.taskPerformance,
  higherAgencyProxy: assistance.assisted.agencyProxy > assistance.manual.agencyProxy,
};

const affordanceLegality = {
  physicalPieceMovementPossible: true,
  ruleLegalMove: false,
  conclusion: 'Physical/action possibility and Game legality can diverge under a declared rule system.',
};

const techniqueSolutions = [
  { technique: 'A', trajectorySignature: 'smooth-direct', outcomeError: 0 },
  { technique: 'B', trajectorySignature: 'late-correction', outcomeError: 0 },
];
const exactTechniqueUniversal = {
  distinctTechniques: new Set(techniqueSolutions.map((x) => x.trajectorySignature)).size > 1,
  sameTaskOutcome: techniqueSolutions.every((x) => x.outcomeError === 0),
};

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-b-model-falsifier-probes',
  epistemicBoundary: {
    proves: [
      'one practice score cannot logically encode all retention/transfer orderings when rankings reverse',
      'variability-based rankings depend on which task variables count',
      'raw command-execution share need not be monotonic with separate performance/agency targets in a declared multi-target model',
      'physical possibility and formal Game legality can be assigned independently',
      'goal-equivalent outcomes do not logically require one exact technique/trajectory'
    ],
    doesNotProve: [
      'that toy numbers reproduce any empirical effect size',
      'that assistance always raises agency',
      'that random practice always improves learning',
      'that one variability metric universally measures skill',
      'that ecological and internal-model theories are fully adjudicated'
    ]
  },
  acquisitionRetention,
  singleScoreSkillFailure,
  variabilityProfiles,
  taskRelevantVariability,
  assistance,
  manualControlMonotonicity,
  affordanceLegality,
  techniqueSolutions,
  exactTechniqueUniversal,
};

const output = process.argv[2] ?? 'evidence/gdf1-b/model-falsifier-probes.json';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
