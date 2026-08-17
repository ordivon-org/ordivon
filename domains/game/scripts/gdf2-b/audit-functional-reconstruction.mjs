#!/usr/bin/env node
import fs from 'node:fs';
const model=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf2-b/functional-reconstruction.json','utf8'));
const p=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf2-b/functional-difficulty-probes.json','utf8'));
const names=new Set(model.reconstruction.objects.map(x=>x.name));
const required=['ChallengeConditionSpec','CapabilityOutcomeSurface','FeasibilityRegion','CapabilityThresholdRegion','CapabilityDiscriminationProfile','SkillIndependentOutcomeComponent','OpponentInteractionSurface','ConsequenceRecoveryProfile','FunctionalDifficultyProjection'];
for(const x of required) if(!names.has(x)) throw new Error(`missing ${x}`);
const checks={
  umbrellasRetired:model.reconstruction.retiredUmbrellas.length===3,
  equalPNotEqualDiscrimination:p.equalSuccess.sameP&&p.equalSuccess.differentDiscrimination,
  thresholdDiscriminationIndependent:p.equalSlopeDifferentThreshold.sameDiscriminationParameter&&p.equalSlopeDifferentThreshold.differentThreshold,
  recoverySeparateFromDemand:p.recovery.sameImmediateDemand&&p.recovery.differentRecoveryCost,
  stochasticitySeparateFromSkill:p.stochasticity.sameMidpointProbability&&p.stochasticity.skillSensitivityReducedByChance,
  continuousWithoutFailure:p.continuousChallenge.binaryFailureDefined===false&&p.continuousChallenge.capabilityChangesQuality,
  assistHasThreeTransformationClasses:Object.values(p.assistanceResults).every(Boolean),
  opponentRelational:p.opponent.sameMapSameSelfDifferentDifficulty===true,
  historyMatters:p.history.samePuzzle&&p.history.surfaceChangedByHistory,
  infeasibleNotOvermatched:p.feasibility.distinct===true,
  noFoundationReopen:Object.values(model.foundationReopen).filter(x=>typeof x==='boolean').every(x=>x===false)
};
if(Object.values(checks).some(x=>!x)) throw new Error(`B audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf2-b-functional-reconstruction-audit',objectCount:model.reconstruction.objects.length,matchedResultCount:model.matchedResults.length,modelCount:model.modelTournament.length,lawCount:model.laws.length,checks,strongestConclusion:'Functional difficulty is better represented as query-specific projections over a capability-outcome response surface plus feasibility, skill-independent/opponent uncertainty and consequence/recovery. Skill challenge is not identical to fail rate or a local derivative; threshold/location and capability discrimination are separate dimensions, and assistance can shift, flatten or relocate the response surface.'},null,2));
