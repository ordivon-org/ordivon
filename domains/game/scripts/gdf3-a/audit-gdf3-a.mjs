#!/usr/bin/env node
import fs from 'node:fs';

const matrix = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf3-a/term-role-matrix.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf3-a/participation-role-probes.json', 'utf8'));
const terms = new Set(matrix.terms.map((x) => x.term));
const required = ['Entity','Subject','Role','Player','Participant','Spectator','Audience','CoachAdvisor','RefereeJudge','Verifier','GameMasterFacilitator','ModeratorOperator','ExperienceManagerDirector','Adjudication','Mediation','ParticipationRole','RoleCausalAccessProfile','RoleAssignment'];
for (const term of required) if (!terms.has(term)) throw new Error(`missing term ${term}`);
const f = probes.strongestFalsifiers;
const checks = {
  enoughBoundaryCases: matrix.boundaryCases.length >= 16,
  roleAndIdentitySeparated: f.participantCannotBeEntityKind === true,
  spectatorBoundarySurvives: f.spectatorNotCausallyIrrelevantByIdentity === true,
  observationNotRoleIdentity: f.observationDoesNotDetermineRole === true,
  adjudicationAuthoritySeparated: f.adjudicationAuthorityNotObservationOrEvidenceAlone === true,
  gmBundleNotAtomic: f.namedRoleNotAtomicFunction === true,
  indirectInfluenceSeparated: f.causalInfluenceNotDirectActionIdentity === true,
  directorNotPlayerIdentity: f.causalSystemComponentNotPlayerIdentity === true,
  roleFusionVisible: f.entityIdentityNotEnoughForRoleConflict === true,
  noCollectiveSubjectRequired: f.audienceDoesNotRequireCollectiveSubject === true,
  participantPrimitiveRejected: matrix.candidateCompression.ParticipantAsPrimitive === 'REJECT',
  mediationPrimitiveRejected: matrix.candidateCompression.MediationAsPrimitive === 'REJECT',
  adjudicationRetainedForTest: matrix.candidateCompression.AdjudicationProcessFamily === 'RETAIN_FOR_DEEPER_TEST',
  noFoundationReopen: Object.values(matrix.foundationReopen).every((x) => x === false)
};
if (Object.values(checks).some((x) => !x)) throw new Error(`GDF3-A audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({
  schemaVersion:1,
  kind:'ordivon.game.gdf3-a-audit',
  termCount:matrix.terms.length,
  boundaryCaseCount:matrix.boundaryCases.length,
  checks,
  strongestConclusion:'Participant is not admitted as an entity kind or universal role; named roles are bundles of scoped rights/functions; Game-relative role/authority topology and adjudication survive as deeper research targets, while one Mediation primitive, collective Audience Subject and new F1-F9 coordinate are rejected.'
}, null, 2));
