#!/usr/bin/env node
import fs from 'node:fs';

const matrix = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf1-e/embodiment-dissociation-matrix.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf1-e/embodiment-falsifiers.json', 'utf8'));

const verdicts = new Map(matrix.constructVerdicts.map((x) => [x.construct, x.verdict]));
const checks = {
  enoughSeparations: matrix.separations.length >= 12,
  negativeAndPositiveBodyCases: matrix.cases.some((x) => x.structuralBodyRequired === false) && matrix.cases.some((x) => x.structuralBodyRequired === true),
  embodimentSingleConstructRejected: verdicts.get('Embodiment') === 'reject-as-single-game-construct',
  actionCouplingIntroduced: verdicts.get('ActionCouplingProfile') === 'introduce-derived-core-candidate',
  visualAvatarNotCollisionBody: probes.visualOnlyRescale.structuralPassabilityUnchanged === true && probes.collisionOnlyRescale.passabilityChanged === true && probes.collisionOnlyRescale.visualAvatarUnchanged === true,
  collisionNotVulnerability: probes.collisionVsVulnerability.movementPassabilitySame === true && probes.collisionVsVulnerability.damageExposureDifferent === true,
  toolExtendsReachWithoutOwnershipRequirement: probes.toolExtension.reachableSetExpanded === true && probes.toolExtension.bodyOwnershipRequiredByStructuralModel === false,
  remoteControlNoAnatomicalContinuity: probes.remoteControl.gameActionEffective === true && probes.remoteControl.anatomicalContinuity === false && probes.remoteControl.selfLocationRequiredByStructuralModel === false,
  sensorEffectorSeparated: probes.sensorEffector.sameEffectorReach === true && probes.sensorEffector.differentInformationAccess === true,
  ownershipAgencyControlSeparated: Object.values(probes.agencyOwnership).every(Boolean),
  actionCouplingSparseAndConditional: probes.actionCouplingProjection.symbolicChess.embodiedFieldsRequired === false && probes.actionCouplingProjection.vrClimb.embodiedFieldsRequired === true,
  noFoundationReopen: matrix.foundationReopen.R29 === false && matrix.foundationReopen.GDF0_PRC7 === false,
};
if (Object.values(checks).some((x) => !x)) throw new Error(`E audit failed ${JSON.stringify(checks)}`);

console.log(JSON.stringify({
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-e-embodiment-audit',
  separationCount: matrix.separations.length,
  caseCount: matrix.cases.length,
  checks,
  strongestConclusion: 'Embodiment is not one Game construct. Game should own a sparse conditional ActionCouplingProfile for structural sensing/effector/control-locus/morphology/tool/collision/vulnerability/dynamics relations; Avatar remains representational, while ownership/self-location/agency/body-schema mechanisms remain Human-side evidence targets. No new R29 primitive is required.',
}, null, 2));
