#!/usr/bin/env node
import fs from 'node:fs';
const matrix = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf1-a/term-boundary-matrix.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf1-a/target-separation-probes.json', 'utf8'));

for (const item of matrix.separations) {
  for (const k of ['left','right','reason']) if (!(k in item)) throw new Error(`separation missing ${k}`);
}
for (const c of matrix.boundaryCases) {
  if (!c.id || !Array.isArray(c.pressure) || c.pressure.length === 0) throw new Error(`invalid boundary case ${c.id}`);
}
const probeChecks = {
  inputActionSeparated: probes.sameInputDifferentAction.separated === true,
  movementActionSeparated: probes.sameActionDifferentMovement.separated === true,
  trajectoryOutcomeSeparated: probes.goalEquivalent.identicalTaskOutcome === true && probes.goalEquivalent.exactTrajectoriesEqual === false,
  performanceSkillPressure: probes.robustness.nominalSpecialist.nominalMean > probes.robustness.robustController.nominalMean && probes.robustness.nominalSpecialist.crossConditionMean < probes.robustness.robustController.crossConditionMean,
  attemptExecutionSeparated: probes.attemptVsExecution.attemptExists === true && probes.attemptVsExecution.executed === false,
};
if (Object.values(probeChecks).some((x) => !x)) throw new Error(`probe check failed: ${JSON.stringify(probeChecks)}`);

console.log(JSON.stringify({
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-a-term-boundary-audit',
  separationCount: matrix.separations.length,
  boundaryCaseCount: matrix.boundaryCases.length,
  externalAnchorCount: matrix.externalAnchors.length,
  probeChecks,
  strongConclusion: 'GDF1-A requires deeper action/control/skill target separation than R21: participant movement, input, semantic GameAction, execution trajectory, outcome, skill-state and embodiment evidence cannot be collapsed.'
}, null, 2));
