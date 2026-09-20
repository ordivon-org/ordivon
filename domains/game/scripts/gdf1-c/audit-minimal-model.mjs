#!/usr/bin/env node
import fs from 'node:fs';

const model = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf1-c/minimal-skill-control-model.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf1-c/capability-surface-probes.json', 'utf8'));

const objectIds = new Set(model.objects.map((x) => x.id));
if (objectIds.size !== model.objects.length) throw new Error('duplicate model object id');
for (const item of model.objects) {
  if (!item.id || !item.definition || !item.guard) throw new Error(`invalid object ${item.id}`);
}
for (const rel of model.derivedRelations) {
  if (!rel.id || !rel.definition || !rel.guard) throw new Error(`invalid derived relation ${rel.id}`);
}

const checks = {
  trvsChangesWithEvaluationTarget:
    JSON.stringify(probes.taskRelevantVariables.scoreTRVS) !== JSON.stringify(probes.taskRelevantVariables.styleTRVS),
  irrelevantRedundantPathExcluded:
    !probes.taskRelevantVariables.combinedTRVS.includes('redundantWristPath'),
  sameActionDifferentMapping:
    probes.remap.sameGameActionSemantics === true && probes.remap.differentInputExpression === true,
  skillProfilesCanRemainIncomparable:
    probes.profileComparison.incomparableWithoutWeighting === true,
  jointPerformanceNotHumanSkill:
    probes.sharedControl.immediateJointImprovement === true && probes.sharedControl.humanIndependentSkillNotAutomaticallyUpdated === true,
  floorIsConfigurationRelative:
    probes.floorRelation.changesWithConfiguration === true,
  ceilingIsConfigurationRelative:
    probes.saturation.coarseSaturatesEarlier === true && probes.saturation.fineStillExpressesDifference === true,
  techniqueAllowsReparameterization:
    probes.techniqueTransfer.sameFamily === true && probes.techniqueTransfer.parametersChanged === true,
  transferHasExactTransformations:
    probes.transformations.every((x) => Array.isArray(x.changed) && x.changed.length > 0 && Array.isArray(x.heldFixed) && x.heldFixed.length > 0),
};
if (Object.values(checks).some((x) => !x)) throw new Error(`C probe failed ${JSON.stringify(checks)}`);

console.log(JSON.stringify({
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-c-minimal-model-audit',
  modelObjectCount: model.objects.length,
  derivedRelationCount: model.derivedRelations.length,
  strongLawCount: model.strongLaws.length,
  checks,
  retainedCoreCandidates: [
    'SkillScopeSpec',
    'ControlContributionTopology',
    'TaskRelevantVariableSet',
    'ProbeTransformation',
    'SkillProfile/ConditionalCapabilitySurface'
  ],
  strongConclusion: 'GDF1-C makes Skill operational without scalarizing it: capability claims are scope-bound, task-relevant variables derive from declared causal/evaluation structure, performance evidence is configuration/provenance bound, transfer names exact transformations, and assisted/joint performance is attribution-separated from Human-independent skill.'
}, null, 2));
