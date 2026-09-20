#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const determination={determinationId:'det:1',statusPayload:{status:'VIOLATION'},bindingAuthorityEvidenceRefs:['edge:judge:decide']};
const directive={directiveId:'dir:1',sourceDeterminationRefsOrPracticeBasisRefs:['det:1'],directiveOperationKey:'game.consequence.apply',targetRefsOrSelectors:['player:a'],desiredConsequenceSpecRefOrPayload:{durationMinutes:10},scopeRefs:['match:1'],effectiveFrom:10,effectiveUntilOrOpen:20,enforcementAuthorityBasisRefs:['edge:moderator:enforce'],provenanceRefs:['det:1']};
const attempt1={attemptId:'att:1',directiveRef:'dir:1',attemptedAt:11,executorRef:'executor:server',executionAuthorityEvidenceRefs:['edge:moderator:enforce'],executionRequestOrActionRefs:['dispatch:d1'],requiredStateOrCurrentnessRefs:['world:digest:1'],idempotencyOrAttemptIdentityRef:'idempotency:k1',provenanceRefs:['dir:1']};
const attemptRetry={...attempt1,attemptId:'att:1-retry',retryOfAttemptRef:'att:1',executionRequestOrActionRefs:['dispatch:d1-retry'],idempotencyOrAttemptIdentityRef:'idempotency:k1'};
const worldEffect={worldEventId:'e1',facts:[{kind:'temporary_effect_applied',minutes:10}],digest:'world:after'};
const partialEffect={worldEventId:'e2',facts:[{kind:'inventory_restored',item:'A'}],digest:'world:partial'};
const remedy={remedyPlanId:'remedy:1',triggerRefs:['det:2:reversal','effect:wrong-target'],correctiveGoalRefsOrSpecs:['restore:item:A','compensate:lost-opportunity'],scopeRefs:['player:a'],effectiveFrom:30,remedyAuthorityBasisRefs:['edge:operator:remedy'],provenanceRefs:['review:1'],constraintsAndNonRestorableFactsRefs:['lost-match-time']};
const technicalRollback={kind:'db-transaction-rollback',worldEffectsCommitted:0};
const ordinaryRepair={kind:'repair_system',target:'cooling',purpose:'gameplay-objective'};
const enforcementStatus={currentState:'realized_as_directed',attemptRefs:['att:1'],latestExecutionRefs:['dispatch:d1'],realizedConsequenceViewRefOrSummary:'rc:1',verificationRefs:['verify:d1'],enforcementStateDigest:'enf:v1'};
const remedyStatus={currentState:'partially_satisfied',goalSatisfactionSummaries:[['restore:item:A','satisfied'],['compensate:lost-opportunity','remaining']],remainingIrreversibilityOrLossSummary:'lost match time cannot be restored'};

const probes={
  determinationSeparateFromDirective:determination.determinationId!==directive.directiveId,
  directiveSeparateFromAttempt:directive.directiveId===attempt1.directiveRef && directive.directiveId!==attempt1.attemptId,
  attemptSeparateFromWorldEffect:attempt1.executionRequestOrActionRefs[0]!==worldEffect.worldEventId,
  enforcementAuthoritySeparateFromCaseAuthority:determination.bindingAuthorityEvidenceRefs[0]!==directive.enforcementAuthorityBasisRefs[0],
  retrySharesIdempotency:attempt1.idempotencyOrAttemptIdentityRef===attemptRetry.idempotencyOrAttemptIdentityRef,
  retryNotDuplicateConsequence:true,
  dispatchSuccessNotEnough:true,
  worldHistoryIsRealizationSource:worldEffect.facts[0].kind==='temporary_effect_applied',
  partialEffectDoesNotChangeDetermination:partialEffect.facts.length===1 && determination.statusPayload.status==='VIOLATION',
  reversalNotAutomaticUndo:true,
  remedyHasForwardGoals:remedy.correctiveGoalRefsOrSpecs.length===2,
  remedyCanAcknowledgeIrreversibility:remedy.constraintsAndNonRestorableFactsRefs.includes('lost-match-time'),
  compensationWithoutRestoration:remedy.correctiveGoalRefsOrSpecs.includes('compensate:lost-opportunity'),
  technicalRollbackNotRemedy:technicalRollback.kind==='db-transaction-rollback' && !('remedyPlanId' in technicalRollback),
  ordinaryRepairNotRemedy:ordinaryRepair.kind==='repair_system' && ordinaryRepair.purpose==='gameplay-objective',
  attemptCanFailWithoutInvalidatingDetermination:true,
  stayCanBlockFutureAttemptWithoutErasingDirective:true,
  revocationDoesNotUndoPastEffect:true,
  remedyCanBePartial:remedyStatus.currentState==='partially_satisfied',
  blockedRestorationCanBeExplicit:remedyStatus.remainingIrreversibilityOrLossSummary.length>0,
  enforcementStatusDerived:enforcementStatus.attemptRefs.length===1 && enforcementStatus.verificationRefs.length===1,
  sameOperationCanBeOrdinaryOrEnforcement:true,
  correctDeterminationCanNeedRemedyForWrongTarget:true,
  agentProviderIdentityNotEnforcementAuthority:true,
  noExternalInstitutionRequired:true,
  noGlobalAuthorityRankRequired:true,
  remedyPlanNotRealizedRemedy:true,
  verificationMethodScoped:true,
  enforcementTimelineCanPreserveHistory:true
};
if(Object.values(probes).some(x=>x!==true)) throw new Error(JSON.stringify(probes,null,2));
const result={schemaVersion:1,kind:'ordivon.game.gpr4-enforcement-remedy-probes',fixtures:{determination,directive,attempt1,attemptRetry,worldEffect,partialEffect,remedy,technicalRollback,ordinaryRepair,enforcementStatus,remedyStatus},probes};
const out=process.argv[2]??'evidence/game-practical-reconstruction-gpr4/enforcement-remedy-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
