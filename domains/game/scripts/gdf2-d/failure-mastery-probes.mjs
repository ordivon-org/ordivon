#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// Structural/evidence counterexamples only; no Human learning mechanism is simulated.

const evaluationRelativeFailure = {
  sameRun:{completed:true,timeSec:2500},
  completionCriterion:{satisfied:true},
  sub40Criterion:{satisfied:false}
};
evaluationRelativeFailure.sameHistoryDifferentFailureAssessment=
  evaluationRelativeFailure.completionCriterion.satisfied !== evaluationRelativeFailure.sub40Criterion.satisfied;

const roguelikeDeath = {
  death:true,
  runCriterionSatisfied:false,
  metaKnowledgeGain:true,
  metaResourceGain:true,
  broaderProgressCriterionSatisfied:true
};
roguelikeDeath.deathNotUniversalFailure=roguelikeDeath.death&&roguelikeDeath.broaderProgressCriterionSatisfied;

const terminality = {
  localFailureSignal:true,
  noRecovery:{samePursuitContinuation:false},
  checkpointRecovery:{samePursuitContinuation:true},
  alternateRouteRecovery:{samePursuitContinuation:true}
};
terminality.failureSignalDoesNotDetermineTerminality=
  terminality.localFailureSignal && !terminality.noRecovery.samePursuitContinuation && terminality.checkpointRecovery.samePursuitContinuation;

const opportunityScore=(x)=>Object.values(x).filter(Boolean).length;
const learningOpportunity = {
  diagnosticFailure:{diagnostic:true,attributable:true,actionable:true,controllable:true,reExposure:true,comparable:true,srvsRelevant:true},
  opaqueRandomFailure:{diagnostic:false,attributable:false,actionable:false,controllable:false,reExposure:true,comparable:false,srvsRelevant:false},
  trivialSuccess:{diagnostic:false,attributable:true,actionable:false,controllable:true,reExposure:true,comparable:true,srvsRelevant:false}
};
learningOpportunity.scores={
  diagnostic:opportunityScore(learningOpportunity.diagnosticFailure),
  opaque:opportunityScore(learningOpportunity.opaqueRandomFailure),
  trivial:opportunityScore(learningOpportunity.trivialSuccess)
};
learningOpportunity.sameFailureCountDifferentOpportunity=true;
learningOpportunity.opportunityWithoutActualLearning={beforeSkill:0.5,afterSkill:0.5,opportunityPresent:true};
learningOpportunity.opportunityNotLearning=
  learningOpportunity.opportunityWithoutActualLearning.opportunityPresent &&
  learningOpportunity.opportunityWithoutActualLearning.beforeSkill===learningOpportunity.opportunityWithoutActualLearning.afterSkill;

const mastery = {
  nominalCriterion:{threshold:0.8},
  specialist:{nominal:0.95,retention:0.55,perturbation:0.5,transfer:0.45},
  robust:{nominal:0.9,retention:0.88,perturbation:0.84,transfer:0.8}
};
mastery.bothNominalPass=mastery.specialist.nominal>=mastery.nominalCriterion.threshold&&mastery.robust.nominal>=mastery.nominalCriterion.threshold;
mastery.robustnessDiffers=mastery.robust.retention>mastery.specialist.retention&&mastery.robust.perturbation>mastery.specialist.perturbation;

const saturationZeroError = {
  challenge:'trivial-saturated',
  noviceErrors:0,
  expertErrors:0,
  noviceUnprobedCapability:0.35,
  expertUnprobedCapability:0.9
};
saturationZeroError.zeroErrorDoesNotIdentifyMastery=saturationZeroError.noviceErrors===0&&saturationZeroError.expertErrors===0&&saturationZeroError.noviceUnprobedCapability!==saturationZeroError.expertUnprobedCapability;

const assistAttribution = {
  humanIndependent:{criterion:0.8,postAssistPerformance:0.55},
  jointController:{criterion:0.8,assistedPerformance:0.95}
};
assistAttribution.jointPassesHumanDoesNot=
  assistAttribution.jointController.assistedPerformance>=assistAttribution.jointController.criterion&&
  assistAttribution.humanIndependent.postAssistPerformance<assistAttribution.humanIndependent.criterion;

const openEndedMastery = {
  terminalCompletionDefined:false,
  claim:{scope:'declared expressive technique family',qualityCriterion:0.85,probeQualities:[0.88,0.9,0.87]},
};
openEndedMastery.localClaimPasses=openEndedMastery.claim.probeQualities.every(x=>x>=openEndedMastery.claim.qualityCriterion);
openEndedMastery.doesNotClaimGlobalMaximum=true;

const transferScope = {
  nominalRetention:0.92,
  transformedTask:0.48,
  localMasteryCriterion:0.85,
  transferMasteryCriterion:0.75
};
transferScope.localMasteryWithoutTransfer=transferScope.nominalRetention>=transferScope.localMasteryCriterion&&transferScope.transformedTask<transferScope.transferMasteryCriterion;

const recovery = {
  A:{nextState:'checkpoint',timeLoss:120,resourceLoss:5,historyLoss:0.05},
  B:{nextState:'run-start',timeLoss:20,resourceLoss:60,historyLoss:0.6}
};
recovery.tradeoffNoDominance=
  recovery.A.timeLoss>recovery.B.timeLoss && recovery.A.resourceLoss<recovery.B.resourceLoss && recovery.A.historyLoss<recovery.B.historyLoss;
recovery.noUniversalSeverityWithoutWeights=true;

const result={
  schemaVersion:1,
  kind:'ordivon.game.gdf2-d-failure-mastery-probes',
  epistemicBoundary:{
    proves:[
      'failure assessment can differ over the same history when evaluation criterion changes',
      'death can be local/run failure without broader progress failure',
      'failure signal and pursuit terminality are logically independent',
      'equal failure count can coexist with materially different structural learning-opportunity profiles',
      'learning opportunity can exist while actual SkillProfile change is held absent',
      'nominal mastery performance can coexist with very different retention/perturbation robustness',
      'zero errors on a saturated task do not identify mastery breadth',
      'joint assisted criterion satisfaction does not imply Human-independent mastery',
      'bounded mastery claims can exist for continuous/open-ended evaluation without terminal completion',
      'local retained mastery does not imply transformed-task mastery',
      'recovery cost dimensions can trade off without a universal severity ordering'
    ],
    doesNotProve:[
      'Human learning from any particular feedback condition',
      'a universal numeric learning-opportunity score',
      'a universal mastery threshold',
      'PlayerValue of failure/recovery/mastery',
      'that retention/transfer are required for every locally scoped mastery claim'
    ]
  },
  evaluationRelativeFailure,
  roguelikeDeath,
  terminality,
  learningOpportunity,
  mastery,
  saturationZeroError,
  assistAttribution,
  openEndedMastery,
  transferScope,
  recovery
};

const output=process.argv[2]??'evidence/gdf2-d/failure-mastery-probes.json';
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
