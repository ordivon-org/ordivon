#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// Final logical/adversarial probes. They validate separations, not Human phenomenology.

const challengeVsFailure={
  sameCondition:{criterion:'sub-40',target:'player-A',rules:'v1'},
  prospectiveChallengeClaim:{estimatedThreshold:'bounded',identifiedStatus:'bounded-only'},
  histories:[{time:2380,failure:false},{time:2500,failure:true}]
};
challengeVsFailure.challengeExistsBeforeOutcome=true;
challengeVsFailure.failureDependsOnRealizedHistory=challengeVsFailure.histories.some(x=>x.failure)&&challengeVsFailure.histories.some(x=>!x.failure);

const challengeVsMastery={
  conditionRegion:['nominal','perturb-A','perturb-B'],
  challengeClaims:['threshold','discrimination'],
  targetEvidence:{nominal:0.95,perturbA:0.92,perturbB:0.91},
  independentCriterion:true
};
challengeVsMastery.reverseInferenceDirections=true;
challengeVsMastery.masteryNeedsCrossProbeEvidence=Object.keys(challengeVsMastery.targetEvidence).length>=3&&challengeVsMastery.independentCriterion;

const failureWithoutSkill={
  criterion:'coin-must-land-heads',
  realized:'tails',
  failureAssessment:true,
  skillChallenge:false
};
failureWithoutSkill.failureDoesNotRequireSkillChallenge=failureWithoutSkill.failureAssessment&&!failureWithoutSkill.skillChallenge;

const challengeWithoutFailure={
  criterion:'maximize-style-quality',
  binaryFailureDefined:false,
  capabilityGradient:true
};
challengeWithoutFailure.challengeDoesNotRequireFailure=!challengeWithoutFailure.binaryFailureDefined&&challengeWithoutFailure.capabilityGradient;

const masteryWithoutCompletion={
  terminalCompletion:false,
  criterionIndependent:true,
  heldOutProbeResults:[0.9,0.92,0.91],
  threshold:0.88
};
masteryWithoutCompletion.validLocalClaim=!masteryWithoutCompletion.terminalCompletion&&masteryWithoutCompletion.criterionIndependent&&masteryWithoutCompletion.heldOutProbeResults.every(x=>x>=masteryWithoutCompletion.threshold);

const recovery={
  sameFailureAssessment:true,
  routes:{checkpoint:{continueSamePursuit:true,timeCost:2},reset:{continueSamePursuit:false,timeCost:600}}
};
recovery.failureAndTerminalitySeparate=recovery.sameFailureAssessment&&recovery.routes.checkpoint.continueSamePursuit!==recovery.routes.reset.continueSamePursuit;

const team={teamLoss:true,individualRoleSatisfied:true};
team.attributionGuard=team.teamLoss&&team.individualRoleSatisfied;

const assist={joint:0.93,humanIndependent:0.58,criterion:0.8};
assist.attributionGuard=assist.joint>=assist.criterion&&assist.humanIndependent<assist.criterion;

const synthetic={syntheticHeldOutPass:true,humanEvidence:null};
synthetic.humanBoundary=synthetic.syntheticHeldOutPass&&synthetic.humanEvidence===null;

const version={old:{rules:'v1',score:0.94},current:{rules:'v2',score:0.6},transformationDeclared:true};
version.currentnessGuard=version.old.rules!==version.current.rules&&version.transformationDeclared;

const underidentified={aggregatePassRate:0.5,models:['steep-skill-sensitive','flat-chance'],identifiedUnique:false};
underidentified.equivalenceGuard=underidentified.models.length>1&&!underidentified.identifiedUnique;

const result={
  schemaVersion:1,
  kind:'ordivon.game.gdf2-f-freeze-probes',
  checks:{
    challengeFailureRemainDistinct:challengeVsFailure.challengeExistsBeforeOutcome&&challengeVsFailure.failureDependsOnRealizedHistory,
    challengeMasteryRemainDistinct:challengeVsMastery.reverseInferenceDirections&&challengeVsMastery.masteryNeedsCrossProbeEvidence,
    failureWithoutSkillChallenge:failureWithoutSkill.failureDoesNotRequireSkillChallenge,
    challengeWithoutFailure:challengeWithoutFailure.challengeDoesNotRequireFailure,
    masteryWithoutCompletion:masteryWithoutCompletion.validLocalClaim,
    terminalityDerivedNotFailureIdentity:recovery.failureAndTerminalitySeparate,
    teamAttribution:team.attributionGuard,
    assistAttribution:assist.attributionGuard,
    syntheticHumanBoundary:synthetic.humanBoundary,
    currentnessBound:version.currentnessGuard,
    underidentificationExplicit:underidentified.equivalenceGuard
  },
  epistemicBoundary:{
    proves:[
      'the three core responsibility directions are logically non-redundant in the constructed corpus',
      'failure can exist without skill challenge and challenge without binary failure',
      'bounded mastery can exist without terminal completion',
      'terminality is separable/derivable from recovery continuation rather than failure identity',
      'team/shared/synthetic/currentness cases require attribution/evidence guards',
      'underidentified challenge explanations must remain explicit'
    ],
    doesNotProve:[
      'Human experienced difficulty, flow, frustration, learning or PlayerValue',
      'that the three responsibility contracts are new semantic primitives',
      'a universal difficulty/mastery scalar or empirical effect size'
    ]
  },
  challengeVsFailure,challengeVsMastery,failureWithoutSkill,challengeWithoutFailure,masteryWithoutCompletion,recovery,team,assist,synthetic,version,underidentified
};
const output=process.argv[2]??'evidence/gdf2-f/freeze-probes.json';
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
