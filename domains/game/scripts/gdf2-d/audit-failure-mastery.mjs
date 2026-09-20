#!/usr/bin/env node
import fs from 'node:fs';
const model=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf2-d/failure-mastery-model.json','utf8'));
const p=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf2-d/failure-mastery-probes.json','utf8'));
const names=new Set(model.objects.map(x=>x.name));
const required=['FailureAssessment','PursuitTerminalityClaim','RecoveryTransitionSet','QuerySpecificRecoveryCostProjection','LearningOpportunityProfile','MasteryClaimSpec','CapabilityMasteryClaim','DemonstratedMasteryEvidence'];
for(const x of required) if(!names.has(x)) throw new Error(`missing ${x}`);
const checks={
  failureEvaluationRelative:p.evaluationRelativeFailure.sameHistoryDifferentFailureAssessment,
  deathNotUniversalFailure:p.roguelikeDeath.deathNotUniversalFailure,
  terminalitySeparated:p.terminality.failureSignalDoesNotDetermineTerminality,
  learningOpportunityNotFailureCount:p.learningOpportunity.sameFailureCountDifferentOpportunity&&p.learningOpportunity.scores.diagnostic>p.learningOpportunity.scores.opaque,
  opportunityNotActualLearning:p.learningOpportunity.opportunityNotLearning,
  masteryNeedsRobustnessScope:p.mastery.bothNominalPass&&p.mastery.robustnessDiffers,
  zeroErrorNotMastery:p.saturationZeroError.zeroErrorDoesNotIdentifyMastery,
  assistAttribution:p.assistAttribution.jointPassesHumanDoesNot,
  openEndedMastery:p.openEndedMastery.terminalCompletionDefined===false&&p.openEndedMastery.localClaimPasses&&p.openEndedMastery.doesNotClaimGlobalMaximum,
  localNotTransferMastery:p.transferScope.localMasteryWithoutTransfer,
  recoveryNonScalar:p.recovery.tradeoffNoDominance&&p.recovery.noUniversalSeverityWithoutWeights,
  enoughLearningDimensions:model.learningOpportunityDimensions.length>=7,
  explicitMasteryRobustness:model.masteryRobustnessDimensions.length>=8,
  noFoundationReopen:Object.values(model.foundationReopen).filter(x=>typeof x==='boolean').every(x=>x===false)
};
if(Object.values(checks).some(x=>!x)) throw new Error(`D audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf2-d-failure-mastery-audit',objectCount:model.objects.length,matchedResultCount:model.matchedResults.length,lawCount:model.laws.length,checks,strongestConclusion:'Failure is evaluation-relative and terminality is a separate recovery/pursuit relation. Learning opportunity is a structural/evidence profile rather than a property of failure and does not imply actual learning. Mastery is a scoped SkillProfile claim over declared conditions/probes/robustness dimensions, not a completion, zero-error, high-score or assisted-performance boolean.'},null,2));
