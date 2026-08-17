#!/usr/bin/env node
import fs from 'node:fs';

const matrix = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf2-a/term-target-matrix.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf2-a/challenge-falsifiers.json', 'utf8'));
const termNames = new Set(matrix.terms.map((x) => x.term));
const requiredTerms = [
  'NominalDifficultySetting','StructuralDemandProfile','FunctionalDifficultyRelation','ExperiencedDifficulty','SkillChallengeRelation','OutcomeRisk','Infeasibility','FailureEvent','ErrorEvent','PunishmentConsequence','Loss','Setback','RecoveryTopology','Retry','LearningOpportunity','CapabilityMasteryClaim','SubjectiveCompetence','FlowExperience'
];
for (const term of requiredTerms) if (!termNames.has(term)) throw new Error(`missing term ${term}`);
const checks = {
  enoughBoundaryCases: matrix.boundaryCases.length >= 15,
  fourDifficultyTargetsSeparated: ['NominalDifficultySetting','StructuralDemandProfile','FunctionalDifficultyRelation','ExperiencedDifficulty'].every((x) => termNames.has(x)),
  skillChallengeRiskInfeasibilitySeparated: ['SkillChallengeRelation','OutcomeRisk','Infeasibility'].every((x) => termNames.has(x)),
  failureFamilySeparated: ['FailureEvent','ErrorEvent','PunishmentConsequence','Loss','Setback'].every((x) => termNames.has(x)),
  masteryTargetsSeparated: ['CapabilityMasteryClaim','DemonstratedMastery','SubjectiveCompetence','SocialMastery'].every((x) => termNames.has(x)),
  lowSuccessNotSkillChallenge: probes.strongestFalsifiers.lowSuccessDoesNotImplySkillChallenge === true,
  impossibleNotMaxChallenge: probes.strongestFalsifiers.impossibleDoesNotImplyMaximumSkillChallenge === true,
  sameDemandDifferentDifficulty: probes.strongestFalsifiers.sameDemandDifferentFunctionalDifficulty === true,
  accessRelativeDifficulty: probes.strongestFalsifiers.accessChangesFunctionalDifficultyWithoutChangingUnderlyingSkill === true,
  deathNotFailureIdentity: probes.strongestFalsifiers.deathNotUniversalFailure === true,
  performanceLearningSeparated: probes.strongestFalsifiers.immediateDifficultyNotLearningValue === true,
  noFoundationReopen: Object.values(matrix.foundationReopen).filter((x) => typeof x === 'boolean').every((x) => x === false)
};
if (Object.values(checks).some((x) => !x)) throw new Error(`GDF2-A audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf2-a-audit',termCount:matrix.terms.length,boundaryCaseCount:matrix.boundaryCases.length,lawCount:matrix.laws.length,checks,strongestConclusion:'Difficulty is not one Game scalar. GDF2-A separates nominal setting, structural demand, participant-relative functional difficulty and Human experienced difficulty; further separates skill challenge, outcome risk and infeasibility; and makes failure/mastery evaluation- and scope-relative rather than object identities.'}, null, 2));
