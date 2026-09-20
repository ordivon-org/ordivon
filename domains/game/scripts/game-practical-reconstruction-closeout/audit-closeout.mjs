#!/usr/bin/env node
import fs from 'node:fs';
const coverage=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/game-practical-reconstruction-closeout/practical-reconstruction-coverage.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/game-practical-reconstruction-closeout/residual-coverage-probes.json','utf8'));
const resolutions=coverage.r0Coverage.map(x=>x.resolution);
const summary=coverage.r0ResolutionSummary;
const candidates=coverage.residualCandidates;
const selected=candidates.find(x=>x.selection==='WINNER');
const checks={
  foundationsFrozen:Object.values(coverage.foundationStatus).slice(0,4).every(x=>x==='FROZEN') && coverage.foundationStatus.reopenTriggered===false,
  sixRounds:coverage.programmeStatus.gprRoundsCompleted.length===6,
  thirtySevenR0:coverage.r0Coverage.length===37 && coverage.programmeStatus.r0ConceptCount===37,
  allR0Accounted:coverage.programmeStatus.r0ConceptsUnaccounted===0,
  reconstructed33:resolutions.filter(x=>x==='RECONSTRUCTED').length===33 && summary.RECONSTRUCTED===33,
  absorbed4:resolutions.filter(x=>x==='ABSORBED_OR_DECOMPOSED').length===4 && summary.ABSORBED_OR_DECOMPOSED===4,
  noOriginalUnresolved:summary.GENUINELY_UNRESOLVED===0,
  reviewAbsorbed:coverage.r0Coverage.find(x=>x.concept==='ReviewRequest')?.finalForm.includes('ContestRequestRecord'),
  appealAbsorbed:coverage.r0Coverage.find(x=>x.concept==='AppealRequest')?.finalForm.includes('ContestRequestRecord'),
  enforcementDecomposed:coverage.r0Coverage.find(x=>x.concept==='EnforcementRecord')?.finalForm.includes('EnforcementAttemptRecord'),
  officialCertificationSplit:coverage.r0Coverage.find(x=>x.concept==='OfficialStatusCertificationView')?.finalForm.includes('CertificationView'),
  finalityGpr2:coverage.r0Coverage.find(x=>x.concept==='FinalityStatus')?.resolvedBy==='GPR2',
  gdf3BiasFound:coverage.coverageBiasFinding.includes('GDF3-heavy'),
  upstreamInventoryPresent:coverage.upstreamDerivedInventory.length>=7,
  cfmChallengeResidual:coverage.upstreamDerivedInventory.some(x=>x.conceptCluster==='GDF2 challenge projections' && x.classification.includes('GENUINELY_UNRESOLVED')),
  cfmFailureResidual:coverage.upstreamDerivedInventory.some(x=>x.conceptCluster==='GDF2 failure/recovery projections' && x.consumerPressure==='VERY_HIGH'),
  cfmMasteryResidual:coverage.upstreamDerivedInventory.some(x=>x.conceptCluster==='GDF2 mastery/evidence projections' && x.classification.includes('GENUINELY_UNRESOLVED')),
  consumerAuditRich:Object.keys(coverage.currentConsumerAudit).length>=11,
  providerFailureSeparated:coverage.currentConsumerAudit.ProviderProcessFailure.classification.includes('TECHNICAL_PROVIDER_FAILURE'),
  persistenceRecoverySeparated:coverage.currentConsumerAudit.PersistenceRecover.classification.includes('TECHNICAL_RECEIPT_STATE_RECOVERY'),
  masteryDirectConsumer:coverage.currentConsumerAudit.ProductSystemMastery.classification==='DIRECT_PRODUCT_VOCABULARY_WITHOUT_FORMAL_MASTERY_VIEW',
  challengeDirectConsumer:coverage.currentConsumerAudit.PressureAndViabilityEvidence.classification==='DIRECT_CHALLENGE_ASSESSMENT_RESEARCH_CONSUMER',
  winnerExists:selected?.candidateId==='R-CFM',
  winnerScore:selected?.selectionScore===29,
  coherenceNotConcept:candidates.find(x=>x.candidateId==='R-COHERENCE')?.classification==='IMPLEMENTATION_CONSUMPTION_CONCERN',
  unexploredNotEligible:candidates.find(x=>x.candidateId==='R-UNEXPLORED-GAME')?.classification==='NOT_ELIGIBLE_FOR_PRACTICAL_RECONSTRUCTION_YET',
  gpr7Admitted:coverage.selectedNextRound.round==='GPR7' && coverage.selectedNextRound.admissionStatus==='ADMITTED_AFTER_WHOLE_PRACTICAL_COVERAGE_SEARCH',
  noFurtherRoadmap:coverage.selectedNextRound.notARoadmapBeyondGPR7===true,
  probesPass:Object.values(probes.probes).every(x=>x===true),
  closeoutNotWholeClosure:coverage.closeoutDecision.includes('whole practical reconstruction problem space is not closed')
};
if(Object.values(checks).some(v=>!v)) throw new Error(`closeout audit failed\n${JSON.stringify(checks,null,2)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.practical-reconstruction-closeout-audit',r0ConceptCount:coverage.r0Coverage.length,reconstructedCount:summary.RECONSTRUCTED,absorbedOrDecomposedCount:summary.ABSORBED_OR_DECOMPOSED,residualCandidateCount:candidates.length,selectedResidual:selected.name,probeCount:Object.keys(probes.probes).length,checkCount:Object.keys(checks).length,checks,decision:coverage.closeoutDecision},null,2));
