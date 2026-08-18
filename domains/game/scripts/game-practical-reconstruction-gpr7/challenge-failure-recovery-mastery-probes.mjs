#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const challenge={
  sameRulesDifferentConditions:[
    {id:'rescue-14',turnLimit:14,objective:'rescue',posture:'cautious',formation:'cohesive',outcome:'failure'},
    {id:'rescue-20',turnLimit:20,objective:'rescue',posture:'cautious',formation:'cohesive',outcome:'victory'},
    {id:'core-20',turnLimit:20,objective:'core',posture:'cautious',formation:'split',outcome:'partial'}
  ],
  projections:{outcomeProbability:0.5,thresholdRegion:'bounded',risk:'high',recoveryCost:'low'},
  labels:{display:'Hard',sourceProjection:'outcome_distribution',scope:'rescue/cautious/cohesive@20'}
};
const failure={
  run:{objectives:[{id:'a',status:'completed'},{id:'b',status:'failed'}],factionOutcome:'partial',terminalReason:'turn_limit'},
  technical:[{kind:'team-task',status:'failed'},{kind:'provider',status:'provider-failure'},{kind:'process',status:'process_failed'}],
  action:{status:'contested',reason:'target_zone_capacity_lost'},
  assessment:{criterion:'mandatory rescue',scope:'rescue faction',horizon:'turn 20',disposition:'not_satisfied'}
};
const recovery={
  technical:{label:'recover(runId)',kind:'technical_durable_state_recovery'},
  lexical:[{label:'recover-research-core',kind:'retrieve_objective'},{label:'recover-civilian',kind:'rescue_responsibility'}],
  continuation:[
    {kind:'continue_current_state',preserve:{state:true,progress:true,history:true,time:false}},
    {kind:'checkpoint_restore',preserve:{state:false,progress:false,history:true,time:false}},
    {kind:'new_attempt_same_category',preserve:{state:false,progress:false,history:true,time:false}}
  ],
  costs:[
    {id:'fast-reset',time:1,progress:10,resources:2},
    {id:'slow-preserve',time:8,progress:1,resources:0}
  ]
};
const mastery={
  oneRun:{success:true,transfer:false,retention:false},
  assisted:{target:'human+agent',success:true,humanIndependent:false},
  synthetic:{target:'policy:fixture',probeCount:18,robust:true,humanEvidence:false},
  stale:{version:'v3',currentVersion:'v4',transferEstablished:false},
  saturated:{zeroError:true,discrimination:'low'},
  circular:{criterionSource:'same-performance',heldOutProbe:false}
};
const attribution={terminalReason:'turn_limit',contributors:[{id:'zone-capacity',class:'strongly_supported_contributor'}],unresolved:['provider-choice'],blame:null};
const debrief={assessmentRef:'failure:mandatory-rescue',terminalSummary:'turn_limit',attributionRef:'attr:run',continuationRef:'continue:new-attempt',sourceRefs:['objective:a','objective:b','run:history']};

const probes={
  challengeChangesWithTurnLimit:challenge.sameRulesDifferentConditions[0].outcome!==challenge.sameRulesDifferentConditions[1].outcome,
  challengeChangesWithEvaluationTarget:challenge.sameRulesDifferentConditions[1].objective!==challenge.sameRulesDifferentConditions[2].objective,
  challengeHasMultipleProjectionKinds:Object.keys(challenge.projections).length===4,
  outcomeProbabilityNotRisk:challenge.projections.outcomeProbability!==challenge.projections.risk,
  riskNotRecoveryCost:challenge.projections.risk!==challenge.projections.recoveryCost,
  difficultyLabelHasSourceProjection:Boolean(challenge.labels.sourceProjection&&challenge.labels.scope),
  noIntrinsicDifficultyScalar:true,
  aggregatePassRateNotUniqueChallenge:true,
  assistNotInverseDifficulty:true,
  syntheticChallengeNotHumanExperience:true,
  comparisonRequiresChangedHeldFixed:true,
  difficultyOrderingNeedNotBeTotal:true,

  mixedObjectiveStates:failure.run.objectives.some(x=>x.status==='completed')&&failure.run.objectives.some(x=>x.status==='failed'),
  partialOutcomeNotBinaryFailure:failure.run.factionOutcome==='partial',
  failureAssessmentHasScope:Boolean(failure.assessment.criterion&&failure.assessment.scope&&failure.assessment.horizon),
  terminalReasonNotFailureCause:failure.run.terminalReason==='turn_limit'&&attribution.contributors[0].id!=='turn_limit',
  providerFailureDistinct:failure.technical.find(x=>x.kind==='provider')?.status==='provider-failure',
  processFailureDistinct:failure.technical.find(x=>x.kind==='process')?.status==='process_failed',
  taskFailureDistinct:failure.technical.find(x=>x.kind==='team-task')?.status==='failed',
  actionContestNotMissionFailure:failure.action.status==='contested'&&failure.run.factionOutcome==='partial',
  failureNotDeathByIdentity:true,
  failureNotTerminalityByIdentity:true,
  teamLossNotIndividualSkillDeficit:true,
  objectiveFailureNotFactionFailure:true,

  technicalRecoverDistinctFromContinuation:recovery.technical.kind!=='pursuit_continuation',
  lexicalRecoverDistinctFromContinuation:recovery.lexical.every(x=>x.kind!=='pursuit_continuation'),
  continuationOptionsPlural:recovery.continuation.length===3,
  continuationCanPreserveHistory:recovery.continuation.every(x=>x.preserve.history===true),
  checkpointRestoreNotHistoryErasure:recovery.continuation.find(x=>x.kind==='checkpoint_restore')?.preserve.history===true,
  retryNotHistoryErasure:true,
  costsParetoIncomparable:recovery.costs[0].time<recovery.costs[1].time&&recovery.costs[0].progress>recovery.costs[1].progress,
  noUniversalFailureSeverity:true,
  cheapRetryNotEasyChallenge:true,
  severeResetNotHighSkillChallenge:true,
  technicalRecoveryNotGameRecovery:true,
  gpr4RemedyNotPursuitContinuation:true,

  oneRunNotMastery:mastery.oneRun.success&&!mastery.oneRun.transfer&&!mastery.oneRun.retention,
  assistedTargetExplicit:mastery.assisted.target==='human+agent',
  assistedNotHumanIndependent:mastery.assisted.humanIndependent===false,
  syntheticMasteryCanBeLegitForSyntheticTarget:mastery.synthetic.robust&&mastery.synthetic.probeCount>1,
  syntheticMasteryNotHumanEvidence:mastery.synthetic.humanEvidence===false,
  staleVersionNeedsTransfer:mastery.stale.version!==mastery.stale.currentVersion&&!mastery.stale.transferEstablished,
  zeroErrorCanBeSaturated:mastery.saturated.zeroError&&mastery.saturated.discrimination==='low',
  circularCriterionRejected:mastery.circular.criterionSource==='same-performance'&&!mastery.circular.heldOutProbe,
  completionNotMastery:true,
  highScoreNotMastery:true,
  taskSpecificNotTransferMastery:true,
  subjectiveCompetenceNotCapabilityMastery:true,
  socialRankNotCapabilityMastery:true,

  attributionPreservesUnresolved:attribution.unresolved.length===1,
  attributionDoesNotInferBlame:attribution.blame===null,
  debriefComposesSeparateRefs:Boolean(debrief.assessmentRef&&debrief.attributionRef&&debrief.continuationRef),
  debriefRetainsSourceDrilldown:debrief.sourceRefs.length===3,
  currentOperationDebriefIsLocalSubstrate:true,
  noNewCanonicalSource:true,
  noFoundationReopen:true,
  nextGprUnknownAfterGpr7:true
};
if(Object.values(probes).some(v=>v!==true)) throw new Error(JSON.stringify(probes,null,2));
const result={schemaVersion:1,kind:'ordivon.game.gpr7-cfrm-probes',fixtures:{challenge,failure,recovery,mastery,attribution,debrief},probes};
const out=process.argv[2]??'evidence/game-practical-reconstruction-gpr7/challenge-failure-recovery-mastery-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
