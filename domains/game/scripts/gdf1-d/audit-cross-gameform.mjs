#!/usr/bin/env node
import fs from 'node:fs';

const matrix = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf1-d/cross-gameform-matrix.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf1-d/cross-gameform-falsifiers.json', 'utf8'));

const ids = new Set(matrix.cases.map((x) => x.id));
if (ids.size !== matrix.cases.length) throw new Error('duplicate case id');
if (matrix.cases.length < 10) throw new Error('cross-gameform corpus too narrow');

const verdicts = new Map(matrix.constructVerdicts.map((x) => [x.construct, x.verdict]));
const checks = {
  motorAndSymbolicFormsCovered: matrix.cases.some((x) => x.motorLoad === 'high') && matrix.cases.some((x) => x.motorLoad === 'minimal'),
  openEndedFormCovered: matrix.cases.some((x) => x.participantAuthoredEvaluation === 'high'),
  assistAndSyntheticCovered: ids.has('shared-assist') && ids.has('synthetic'),
  skillProfileSurvivesSymbolic: probes.chess.skillClaimPossibleWithoutMotorMetric === true,
  evaluationCommitmentMustBeDynamic: JSON.stringify(probes.sandboxRelevance.t0) !== JSON.stringify(probes.sandboxRelevance.t1) && probes.sandboxRelevance.changedWithoutFormalRuleMutation === true,
  rtsNeedsContributionTopology: probes.rtsAttribution.topologyNeeded === true && probes.rtsAttribution.lowLevelMovementNotPlayerMotorTrajectory === true,
  remapClassesDiffer: new Set(Object.values(probes.remapCases).map((x) => x.expected)).size === 3,
  saturationNeedsAttribution: new Set(Object.values(probes.saturationCauses).map((x) => x.cause)).size === 4,
  embodimentNonUniversalButStructuralSometimes: probes.embodimentCases.chess.bodyMorphologyChangesCoreReachability === false && probes.embodimentCases.vrClimb.bodyMorphologyChangesCoreReachability === true,
  techniqueOptional: probes.techniqueCases.chess.skillExists === true && probes.techniqueCases.chess.usefulFamilyRequired === false,
  evaluationTargetReconstructed: verdicts.get('EvaluationTargetSet') === 'replace',
  embodimentNextRoundEarned: verdicts.get('Embodiment') === 'dedicated-next-round-required',
};
if (Object.values(checks).some((x) => !x)) throw new Error(`D audit failed ${JSON.stringify(checks)}`);

console.log(JSON.stringify({
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-d-cross-gameform-audit',
  caseCount: matrix.cases.length,
  constructVerdictCount: matrix.constructVerdicts.length,
  checks,
  strongestReconstruction: 'EvaluationTargetSet -> time/provenance-bound EvaluationCommitmentSet; SkillProfile survives symbolic/strategic forms; TechniqueFamily is demoted to optional derived view; SaturationBoundary requires causal attribution; Embodiment earns a dedicated next falsification round because it is non-universal yet structurally constitutive in some control forms.',
}, null, 2));
