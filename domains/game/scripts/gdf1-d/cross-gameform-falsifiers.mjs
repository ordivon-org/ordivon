#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// Structural cross-GameForm probes only; values/labels are toy semantics, not empirical effect sizes.

const chess = {
  motorTelemetry: { cursorDistance: 1 },
  taskVariables: { relevantRegionDetectionMs: 420, candidateQuality: 0.92, searchWaste: 0.18 },
  skillClaimPossibleWithoutMotorMetric: true,
};

const sandbox = {
  t0: { commitments: [{ id: 'build-shelter', authority: 'participant', current: true }] },
  t1: { commitments: [{ id: 'build-shelter', authority: 'participant', current: false }, { id: 'make-sculpture', authority: 'participant', current: true }] },
};
const sandboxRelevance = {
  t0: ['resource-efficiency', 'weather-protection'],
  t1: ['shape-control', 'material-expression'],
  changedWithoutFormalRuleMutation: true,
};

const rtsTopology = {
  player: { contributions: ['select-squad', 'choose-target', 'issue-attack-order'] },
  pathfinder: { contributions: ['route-units'] },
  unitAI: { contributions: ['local-targeting', 'collision-avoidance'] },
  gameAuthority: { contributions: ['admit-order', 'resolve-damage'] },
};
const rtsAttribution = {
  highLevelGameActionOwnedByPlayer: true,
  lowLevelMovementNotPlayerMotorTrajectory: true,
  topologyNeeded: Object.keys(rtsTopology).length > 1,
};

const remapCases = {
  accessOnly: {
    heldFixed: ['GameAction semantics', 'timing window', 'information', 'world dynamics'],
    changed: ['physical input channel'],
    expected: 'higher-order-skill-mostly-preserved',
  },
  expressionRemap: {
    heldFixed: ['GameAction semantics', 'world dynamics'],
    changed: ['gain', 'effector', 'control transfer function'],
    expected: 'higher-order-skill-plus-recalibration',
  },
  skillFamilyChange: {
    heldFixed: ['goal label'],
    changed: ['action vocabulary', 'observation', 'timing', 'world dynamics'],
    expected: 'new-or-materially-revised-skill-scope',
  },
};

const saturationCauses = {
  gameStructure: { observedPlateau: true, cause: 'action-resolution-cap' },
  measurement: { observedPlateau: true, cause: 'score-rounded-to-integer' },
  challenge: { observedPlateau: true, cause: 'opponents-too-easy' },
  population: { observedPlateau: true, cause: 'sample-lacks-higher-capability-subjects' },
};

const embodimentCases = {
  chess: { bodyMorphologyChangesCoreReachability: false, bodyOwnershipNeededForSkillClaim: false },
  vrClimb: { bodyMorphologyChangesCoreReachability: true, bodyScaleAffectsActionPossibility: true },
  adaptiveController: { bodyControllerFitChangesAccess: true, sameGameActionSemanticsCanRemain: true },
};

const techniqueCases = {
  racing: { recurrentFunctionalOrganization: true, usefulFamily: true },
  fighting: { recurrentFunctionalOrganization: true, multipleFamilies: true, usefulFamily: true },
  chess: { recurrentMotorOrganization: false, skillExists: true, usefulFamilyRequired: false },
  sandbox: { recurrentOrganizationMayBeEmergent: true, analystClusteringRisk: true, usefulFamilyRequired: false },
};

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-d-cross-gameform-falsifiers',
  epistemicBoundary: {
    proves: [
      'SkillProfile can be instantiated with strategic/perceptual task variables even when motor telemetry is negligible',
      'participant-authored current commitments can change task relevance without formal rule mutation',
      'RTS command control requires controller/layer attribution without identifying player action with unit motor trajectory',
      'mapping transformations differ materially and should not all be called the same remap',
      'observed performance saturation is causally ambiguous without attribution',
      'embodiment is non-universal but can become structurally relevant in body-scaled/access cases',
      'TechniqueFamily is optional rather than necessary for all Skill claims'
    ],
    doesNotProve: [
      'empirical prevalence/effect sizes',
      'a complete theory of creativity or embodiment',
      'that every participant-authored commitment is stable or valuable',
      'that chess has no motor component whatsoever',
      'that technique families are objectively unique clusters'
    ]
  },
  chess,
  sandbox,
  sandboxRelevance,
  rtsTopology,
  rtsAttribution,
  remapCases,
  saturationCauses,
  embodimentCases,
  techniqueCases,
};

const output = process.argv[2] ?? 'evidence/gdf1-d/cross-gameform-falsifiers.json';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
