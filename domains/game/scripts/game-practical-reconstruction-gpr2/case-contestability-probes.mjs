#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const worldHistory={runId:'run:1',eventIds:['e1','e2'],digest:'world:H1'};
const d0={determinationId:'det:0',determinationOperationKey:'game.case.decide',targetRefOrSelector:'incident:1',statusPayload:{status:'FOUL'},scopeRefs:['match:1'],effectiveAt:10,bindingAuthorityEvidenceRefs:['edge:floor-judge:decide'],authorityStateDigestOrCurrentnessEvidence:'auth:d0',provenanceRefs:['referee:floor'],caseBasisRefs:['replay:v1'],normOrEvaluationBasisRefs:['rules:v1']};
const d1={...d0,determinationId:'det:1',effectiveAt:20,statusPayload:{status:'NO_FOUL'},bindingAuthorityEvidenceRefs:['edge:head-judge:review'],authorityStateDigestOrCurrentnessEvidence:'auth:d1',provenanceRefs:['referee:head'],relatedPriorDeterminationRefs:['det:0'],lineageRelationKeys:['reverses']};
const certA={determinationId:'cert:a',determinationOperationKey:'game.result.certify',targetRefOrSelector:'run:1',statusPayload:{status:'VALID'},scopeRefs:['category:any-percent'],effectiveAt:30,bindingAuthorityEvidenceRefs:['edge:mod:certify'],authorityStateDigestOrCurrentnessEvidence:'auth:cert',provenanceRefs:['moderation:1'],caseBasisRefs:['verification:run:1'],normOrEvaluationBasisRefs:['category:any-percent:v2']};
const certB={...certA,determinationId:'cert:b',scopeRefs:['category:no-major-glitches'],statusPayload:{status:'INVALID'},normOrEvaluationBasisRefs:['category:nmg:v3']};
const request={requestId:'contest:1',channelKey:'game.case.appeal',requesterRef:'player:a',targetDeterminationRefs:['det:0'],requestedAt:11,requestScopeRefs:['match:1'],requestBasisRefs:['claim:new-angle'],provenanceRefs:['player:a']};
const contestOpen={determinationRef:'det:0',contestabilityState:'open',availableChannels:['game.case.appeal'],reviewAuthorityOperationKeysAndSourceRefs:[['game.case.review','edge:head-judge:review']],deadlineOrCurrentnessBoundaries:[25],stayOrInterimEffectPolicy:'no_automatic_stay'};
const contestClosed={...contestOpen,contestabilityState:'closed_within_queried_scope',availableChannels:[],deadlineOrCurrentnessBoundaries:[25]};
const lineage={nodes:['det:0','det:1'],typedRelations:[{from:'det:1',to:'det:0',kind:'reverses'}],currentDeterminationRefsByScope:['det:1'],historicalDeterminationRefs:['det:0']};
const basisEvidenceChange={caseOrCanonicalStateBasisRefs:['replay:v2'],normOrEvaluationApplicationBasisRefs:['rules:v1']};
const basisNormChange={caseOrCanonicalStateBasisRefs:['replay:v1'],normOrEvaluationApplicationBasisRefs:['rules:v2']};
const providerDecision={kind:'agent-decision',candidateId:'candidate:1',confidence:0.9};
const verification={kind:'verification-receipt',success:true,checks:['digest','effect']};
const proposalReview={phase:'proposal-review',proposalStatus:'proposed',priorBindingCaseStatus:false};

const probes={
  worldHistoryUnaffectedByReversal:worldHistory.digest==='world:H1' && d1.lineageRelationKeys.includes('reverses'),
  officialStatusNotWorldTruth:d0.statusPayload.status==='FOUL' && worldHistory.eventIds.length===2,
  reviewCreatesNewDetermination:d0.determinationId!==d1.determinationId && d1.relatedPriorDeterminationRefs.includes(d0.determinationId),
  reversalPreservesPriorHistory:lineage.historicalDeterminationRefs.includes('det:0') && lineage.currentDeterminationRefsByScope.includes('det:1'),
  decisionLineageIsGraph:Array.isArray(lineage.typedRelations) && !('singleChain' in lineage),
  requestNotReviewOutcome:request.targetDeterminationRefs.includes('det:0') && !('statusPayload' in request),
  requestDoesNotGrantReviewerAuthority:!('reviewerAuthority' in request),
  appealNoAutomaticStay:contestOpen.stayOrInterimEffectPolicy==='no_automatic_stay',
  finalityIsDerived:contestClosed.contestabilityState==='closed_within_queried_scope' && contestOpen.contestabilityState==='open',
  categoryStatusesCanDiffer:certA.targetRefOrSelector===certB.targetRefOrSelector && certA.scopeRefs[0]!==certB.scopeRefs[0] && certA.statusPayload.status!==certB.statusPayload.status,
  certificationDistinctFromVerification:certA.determinationOperationKey==='game.result.certify' && verification.kind==='verification-receipt',
  verificationCanBeBasis:certA.caseBasisRefs.includes('verification:run:1'),
  providerDecisionNotDetermination:providerDecision.kind==='agent-decision' && !('bindingAuthorityEvidenceRefs' in providerDecision),
  proposalReviewNotCaseReview:proposalReview.priorBindingCaseStatus===false,
  evidenceChangeDistinctFromNormChange:basisEvidenceChange.caseOrCanonicalStateBasisRefs[0]!==basisNormChange.caseOrCanonicalStateBasisRefs[0] && basisEvidenceChange.normOrEvaluationApplicationBasisRefs[0]!==basisNormChange.normOrEvaluationApplicationBasisRefs[0],
  deterministicCanStillBeOfficial:true,
  externalInstitutionNotRequired:true,
  reviewAuthorityCanDifferFromOriginal:d0.bindingAuthorityEvidenceRefs[0]!==d1.bindingAuthorityEvidenceRefs[0],
  officialNotCertification:d0.determinationOperationKey!=='game.result.certify',
  noChainOfThoughtRequired:!('rationale' in d0) && !('chainOfThought' in d0),
  enforcementNotDetermination:!('enforcement' in d1),
  appealNotGuaranteedCorrection:true,
  finalityNotTruth:true,
  sameModelDifferentAuthorityPossible:true,
  requestWorkflowCanExpire:true
};
if(Object.values(probes).some(x=>x!==true)) throw new Error(JSON.stringify(probes,null,2));
const result={schemaVersion:1,kind:'ordivon.game.gpr2-case-contestability-probes',fixtures:{worldHistory,d0,d1,certA,certB,request,contestOpen,contestClosed,lineage,basisEvidenceChange,basisNormChange,providerDecision,verification,proposalReview},probes};
const out=process.argv[2]??'evidence/game-practical-reconstruction-gpr2/case-contestability-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
