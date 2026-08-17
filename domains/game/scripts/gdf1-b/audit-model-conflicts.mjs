#!/usr/bin/env node
import fs from 'node:fs';
const matrix = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf1-b/model-conflict-matrix.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf1-b/model-falsifier-probes.json', 'utf8'));

const allowed = new Set(matrix.protocol.statuses);
const modelIds = new Set(matrix.models.map((x) => x.id));
if (modelIds.size !== matrix.models.length) throw new Error('duplicate model id');
for (const c of matrix.conflicts) {
  if (!allowed.has(c.status)) throw new Error(`${c.id} invalid status ${c.status}`);
  if (!modelIds.has(c.a)) throw new Error(`${c.id} unknown model ${c.a}`);
  if (c.b.startsWith('M') && !modelIds.has(c.b)) throw new Error(`${c.id} unknown model ${c.b}`);
  if (c.status === 'real-conflict' && !c.discriminatingPrediction) throw new Error(`${c.id} real conflict missing discriminatingPrediction`);
}
const statuses = Object.fromEntries([...allowed].map((s) => [s, matrix.conflicts.filter((x) => x.status === s).length]));
const checks = {
  acquisitionRetentionRankingReversal: probes.singleScoreSkillFailure.rankingReversal === true,
  variabilityRankingDependsOnTaskVariable: probes.taskRelevantVariability.rankingDiffersByVariableChoice === true,
  commandShareNotMonotonicAcrossTargets: Object.values(probes.manualControlMonotonicity).every(Boolean),
  affordanceLegalitySeparated: probes.affordanceLegality.physicalPieceMovementPossible === true && probes.affordanceLegality.ruleLegalMove === false,
  exactTechniqueNotLogicallyRequired: probes.exactTechniqueUniversal.distinctTechniques === true && probes.exactTechniqueUniversal.sameTaskOutcome === true,
};
if (Object.values(checks).some((x) => !x)) throw new Error(`probe failure ${JSON.stringify(checks)}`);
console.log(JSON.stringify({
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-b-model-conflict-audit',
  modelCount: matrix.models.length,
  conflictCount: matrix.conflicts.length,
  conflictStatusCounts: statuses,
  checks,
  skillCandidate: matrix.skillReconstruction.to,
  strongConclusion: 'Most named motor/control theories are not global Game-foundation rivals. The strongest falsifications target universal collapses: exact trajectory/repetition, open-loop-only control, current-score=skill, globally-low-variability=skill, raw-manual-command-share=agency, and affordance=Game-legality.'
}, null, 2));
