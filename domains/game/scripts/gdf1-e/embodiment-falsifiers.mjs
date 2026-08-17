#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// Structural matched dissociations only. Human phenomenology is not simulated.

const base = {
  avatarMeshScale: 1.0,
  collisionWidth: 0.8,
  vulnerabilityWidth: 0.8,
  apertureWidth: 1.0,
  toolReach: 1.0,
  armReach: 0.7,
  remoteLocusDistance: 4.0,
};

const visualOnlyRescale = {
  before: { avatarMeshScale: 1.0, collisionWidth: 0.8 },
  after: { avatarMeshScale: 0.5, collisionWidth: 0.8 },
};
visualOnlyRescale.structuralPassabilityUnchanged =
  (visualOnlyRescale.before.collisionWidth <= base.apertureWidth) ===
  (visualOnlyRescale.after.collisionWidth <= base.apertureWidth);

const collisionOnlyRescale = {
  before: { avatarMeshScale: 1.0, collisionWidth: 0.8 },
  after: { avatarMeshScale: 1.0, collisionWidth: 1.2 },
};
collisionOnlyRescale.passabilityChanged =
  (collisionOnlyRescale.before.collisionWidth <= base.apertureWidth) !==
  (collisionOnlyRescale.after.collisionWidth <= base.apertureWidth);
collisionOnlyRescale.visualAvatarUnchanged = collisionOnlyRescale.before.avatarMeshScale === collisionOnlyRescale.after.avatarMeshScale;

const collisionVsVulnerability = {
  sameCollision: { collisionWidth: 0.8 },
  narrowVulnerability: { vulnerabilityWidth: 0.4 },
  wideVulnerability: { vulnerabilityWidth: 1.0 },
  movementPassabilitySame: true,
  damageExposureDifferent: true,
};

const toolExtension = {
  bareReach: base.armReach,
  toolReach: base.armReach + base.toolReach,
};
toolExtension.reachableSetExpanded = toolExtension.toolReach > toolExtension.bareReach;
toolExtension.bodyOwnershipRequiredByStructuralModel = false;

const remoteControl = {
  inputEffectorLocation: 0,
  controlLocusLocation: base.remoteLocusDistance,
  anatomicalContinuity: false,
  gameActionEffective: true,
  selfLocationRequiredByStructuralModel: false,
};

const sensorEffector = {
  configurationA: { sensorRange: 10, effectorRange: 2 },
  configurationB: { sensorRange: 4, effectorRange: 2 },
  sameEffectorReach: true,
  differentInformationAccess: true,
};

const agencyOwnershipLogicalTable = [
  { case: 'owned-and-controlled', objectiveControl: true, ownershipEvidenceTarget: true, agencyEvidenceTarget: true },
  { case: 'controlled-external-object', objectiveControl: true, ownershipEvidenceTarget: false, agencyEvidenceTarget: true },
  { case: 'passively-moved-owned-object', objectiveControl: false, ownershipEvidenceTarget: true, agencyEvidenceTarget: false },
];
const agencyOwnership = {
  ownershipNotNecessaryForObjectiveControl: agencyOwnershipLogicalTable.some((x) => x.objectiveControl && !x.ownershipEvidenceTarget),
  agencyNotNecessaryForOwnership: agencyOwnershipLogicalTable.some((x) => x.ownershipEvidenceTarget && !x.agencyEvidenceTarget),
};

const actionCouplingProjection = {
  symbolicChess: { fieldsPresent: ['control mapping', 'control locus'], embodiedFieldsRequired: false },
  vrClimb: { fieldsPresent: ['sensor envelope','effector envelope','control mapping','control locus','morphology/reach geometry','collision geometry','vulnerability/consequence geometry'], embodiedFieldsRequired: true },
  racingVehicle: { fieldsPresent: ['control mapping','control locus','tool/vehicle mediation','collision geometry','dynamic/inertial constraints'], embodiedFieldsRequired: true },
};

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-e-embodiment-falsifiers',
  epistemicBoundary: {
    proves: [
      'visual avatar scale and authoritative collision reachability can vary independently in a declared Game model',
      'collision/passability and vulnerability/damage roles can vary independently',
      'tool mediation can expand reachable action space without a structural requirement for subjective ownership',
      'remote control can be effective without anatomical continuity or structural self-location requirement',
      'sensor and effector envelopes are independent control constraints',
      'ownership/agency/objective-control targets are logically non-identical',
      'a sparse ActionCouplingProfile can be optional for symbolic forms and richer for body/tool-coupled forms'
    ],
    doesNotProve: [
      'human body ownership, self-location or agency effect sizes',
      'that visual avatar changes never influence performance',
      'that tools are never experienced as owned/embodied',
      'a neural body-schema theory',
      'that every Game needs an ActionCouplingProfile object in implementation'
    ]
  },
  visualOnlyRescale,
  collisionOnlyRescale,
  collisionVsVulnerability,
  toolExtension,
  remoteControl,
  sensorEffector,
  agencyOwnershipLogicalTable,
  agencyOwnership,
  actionCouplingProjection,
};

const output = process.argv[2] ?? 'evidence/gdf1-e/embodiment-falsifiers.json';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
