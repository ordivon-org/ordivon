#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/game-practical-reconstruction-gpr2/case-contestability-contracts.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/game-practical-reconstruction-gpr2/case-contestability-probes.json','utf8'));
const c=matrix.contracts;
const checks={
  foundationsFrozen:Object.values(matrix.foundationStatus).slice(0,4).every(x=>x==='FROZEN') && matrix.foundationStatus.reopenTriggered===false,
  determinationConditionalSource:c.AuthoritativeDeterminationRecord.status==='STABILIZE_CONDITIONAL_SOURCE_RECORD',
  boundaryDiagnostic:c.CaseDeterminationBoundaryDiagnostic.status==='STABILIZE_DERIVED_DEVELOPER_DIAGNOSTIC',
  boundaryThreeOutputs:c.CaseDeterminationBoundaryDiagnostic.outputs.length===3,
  deterministicNotBoundary:c.CaseDeterminationBoundaryDiagnostic.nonCriteria.includes('deterministic versus discretionary'),
  basisTraceDerived:c.DeterminationBasisTrace.status==='STABILIZE_DERIVED_AUDIT_VIEW',
  noChainOfThought:c.DeterminationBasisTrace.laws.some(x=>x.includes('chain-of-thought')),
  genericContestSource:c.ContestRequestRecord.status==='STABILIZE_CONDITIONAL_GENERIC_WORKFLOW_SOURCE',
  requestWorkflowStates:c.ContestRequestRecord.workflowStatesForProjection.length>=7,
  reviewAsView:c.ReviewRequestView.status==='STABILIZE_PRACTICE_DEFINED_VIEW_OVER_CONTEST_REQUEST',
  appealAsView:c.AppealRequestView.status==='STABILIZE_PRACTICE_DEFINED_VIEW_OVER_CONTEST_REQUEST',
  appealNotUniversalReview:c.AppealRequestView.law.includes('not Review by universal identity'),
  contestabilityDerived:c.ReviewContestabilityProfile.status==='STABILIZE_DERIVED_POLICY_AUTHORITY_VIEW',
  contestabilityUsesAuthority:c.ReviewContestabilityProfile.laws.some(x=>x.includes('GPR1 effective authority')),
  lineageGraph:c.DecisionLineage.status==='STABILIZE_DERIVED_GRAPH_NOT_CHAIN',
  lineageBranching:c.DecisionLineage.laws.some(x=>x.includes('branch')),
  officialDerived:c.OfficialStatusView.status==='STABILIZE_DERIVED_USER_AGENT_VIEW',
  certificationSpecialized:c.CertificationView.status==='STABILIZE_SPECIALIZED_DERIVED_VIEW',
  officialNotCertification:c.CertificationView.laws.includes('OfficialStatus != Certification by identity'),
  finalityDerived:c.FinalityStatusView.status==='STABILIZE_DERIVED_UI_QUERY',
  finalityNotTruth:c.FinalityStatusView.laws.includes('finality != truth'),
  fiftyPlusCases:matrix.stressCases.length>=50,
  currentAudit:Object.keys(matrix.currentEngineeringAudit).length>=6,
  proposalReviewSeparated:matrix.currentEngineeringAudit.MissionControlProposalReview.classification==='PRE_COMMIT_PROPOSAL_REVIEW_NOT_CASE_REVIEW',
  verificationSeparated:matrix.currentEngineeringAudit.VerificationReceipt.classification==='EXECUTION_VERIFICATION_EVIDENCE_NOT_CERTIFICATION',
  worldStatusSeparated:matrix.currentEngineeringAudit.WorldMissionStatus.classification==='AUTHORITATIVE_WORLD_STATE_NOT_SEPARATE_CASE_DETERMINATION',
  noCurrentDirectConsumer:matrix.implementationDecision.currentDirectConsumerNeed==='NOT_PROVEN',
  noBroadImplementation:matrix.implementationDecision.broadImplementationNow===false,
  gpr3Selected:matrix.nextRound.name.startsWith('GPR3'),
  probesPass:Object.values(probes.probes).every(x=>x===true),
  lawReviewReplay:matrix.crossCuttingLaws.includes('Review != Replay'),
  lawFinalityTruth:matrix.crossCuttingLaws.includes('Finality != Truth'),
  lawRequestOutcome:matrix.crossCuttingLaws.includes('ReviewRequest != ReviewAdmission') && matrix.crossCuttingLaws.includes('ReviewAdmission != ReviewOutcome'),
  lawWorldTruth:matrix.crossCuttingLaws.includes('OfficialCaseStatus != WorldTruth'),
  lawVerificationCertification:matrix.crossCuttingLaws.includes('Verification != CertificationByIdentity'),
  lawProviderDecision:matrix.crossCuttingLaws.includes('ProviderDecision != AuthoritativeDeterminationByIdentity')
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GPR2 audit failed\n${JSON.stringify(checks,null,2)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gpr2-audit',contractCount:Object.keys(c).length,stressCaseCount:matrix.stressCases.length,lawCount:matrix.crossCuttingLaws.length,probeCount:Object.keys(probes.probes).length,checkCount:Object.keys(checks).length,checks,decision:'GPR2 reconstructs authoritative determinations as conditional source records; contest requests as generic optional workflow sources; Review/Appeal as practice-defined views; and basis, contestability, lineage, official status, certification and finality as derived projections. Current Station Zero proposal review/verification/authority decisions/World status are not silently reclassified as adjudication.'},null,2));
