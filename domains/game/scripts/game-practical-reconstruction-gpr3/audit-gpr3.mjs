#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/game-practical-reconstruction-gpr3/evidence-norm-explanation-contracts.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/game-practical-reconstruction-gpr3/evidence-norm-explanation-probes.json','utf8'));
const c=matrix.contracts;
const checks={
  foundationsFrozen:Object.values(matrix.foundationStatus).slice(0,4).every(x=>x==='FROZEN') && matrix.foundationStatus.reopenTriggered===false,
  eightContracts:Object.keys(c).length===8,
  bundleDerived:c.EvidenceBundleForCase.status==='STABILIZE_DERIVED_CASE_RELATIVE_VIEW',
  bundleNoDupStore:c.EvidenceBundleForCase.storageRule.includes('not duplicate'),
  evidenceQuestionRelative:c.EvidenceBundleForCase.laws.some(x=>x.includes('case/question-relative')),
  normViewDerived:c.NormApplicationView.status==='STABILIZE_DERIVED_CURRENT_NORM_VIEW',
  stableRepNotTopology:c.NormApplicationView.laws.includes('StableRuleRepresentation != StableEffectiveRuleTopology'),
  noUniversalReasoner:c.NormApplicationView.laws.includes('NormApplicationView != universal inference engine'),
  interpretiveConditional:c.InterpretiveCommitmentRecord.status==='STABILIZE_CONDITIONAL_GDF0_SOURCE_ADAPTER',
  interpretiveNeedsGdf0:c.InterpretiveCommitmentRecord.admissionRule.includes('GDF0 EffectiveRuleTopology'),
  precedentConditional:c.PrecedentLink.status==='STABILIZE_CONDITIONAL_TYPED_RELATION_VIEW_OR_RECORD',
  precedentNoBindingByCitation:c.PrecedentLink.laws.includes('Citation != BindingForce'),
  conventionDerived:c.ConventionStatusView.status==='STABILIZE_DERIVED_OBSERVED_VS_CONSTITUTIVE_VIEW',
  conventionFrequencyNotAuthority:c.ConventionStatusView.laws.includes('ConventionFrequency != Authority'),
  discretionDerived:c.DiscretionEnvelope.status==='STABILIZE_DERIVED_BOUNDED_CHOICE_VIEW',
  discretionNotArbitrary:c.DiscretionEnvelope.laws.includes('Discretion != Arbitrariness'),
  verificationDerived:c.VerificationView.status==='STABILIZE_DERIVED_ADAPTER_OVER_VERIFICATION_SOURCES',
  verificationNotCertification:c.VerificationView.laws.includes('Verification != Certification by identity'),
  explanationComposite:c.DeterminationExplanationView.status==='STABILIZE_COMPOSITE_DERIVED_EXPLANATION_VIEW',
  generatedExplanationNotAuthority:c.DeterminationExplanationView.laws.includes('GeneratedExplanation != AuthoritativeEffect'),
  noCot:c.DeterminationExplanationView.laws.includes('no chain-of-thought requirement'),
  fiftyPlusCases:matrix.stressCases.length>=55,
  eightEngineeringFindings:Object.keys(matrix.currentEngineeringAudit).length>=8,
  replayGraphSeparated:matrix.currentEngineeringAudit.RunEvidenceGraph.classification==='STRONG_PROVENANCE_HISTORY_GRAPH_NOT_CASE_EVIDENCE_ONTOLOGY',
  missionEvidenceLocal:matrix.currentEngineeringAudit.MissionControlEvidenceView.classification==='PRODUCT_UX_EVIDENCE_STAGE_PROJECTION',
  verificationExistingSource:matrix.currentEngineeringAudit.VerificationReceipt.classification==='EXISTING_STRONG_VERIFICATION_SOURCE',
  rationaleSeparated:matrix.currentEngineeringAudit.AgentRationale.classification==='BOUNDED_OPERATIONAL_EXPLANATION_NOT_NORM_REASONING',
  rulesetVersionSource:matrix.currentEngineeringAudit.RulesetVersionBinding.classification==='EXECUTABLE_RULE_REPRESENTATION_AND_VERSION_SOURCE',
  partialNeedOnly:matrix.implementationDecision.partialCurrentConsumerNeed==='PROVEN_FOR_VERIFICATION_AND_PROVENANCE_VIEWS_ONLY',
  noBroadImplementation:matrix.implementationDecision.broadImplementationNow===false,
  gpr4Selected:matrix.nextRound.name.startsWith('GPR4'),
  probesPass:Object.values(probes.probes).every(x=>x===true),
  lawEvidenceTruth:matrix.crossCuttingLaws.includes('Evidence != WorldTruth'),
  lawReplayBundle:matrix.crossCuttingLaws.includes('ReplayEvidenceGraph != CaseEvidenceBundleByIdentity'),
  lawTelemetry:matrix.crossCuttingLaws.includes('ProviderTelemetry != GameCaseEvidenceByIdentity'),
  lawPrivateInterpretation:matrix.crossCuttingLaws.includes('PrivateInterpretation != InterpretiveCommitment'),
  lawPrecedent:matrix.crossCuttingLaws.includes('PriorDecision != BindingPrecedent'),
  lawConvention:matrix.crossCuttingLaws.includes('ConventionFrequency != Authority'),
  lawDiscretion:matrix.crossCuttingLaws.includes('WithinDiscretionEnvelope != GoodOrCorrect'),
  lawExplanation:matrix.crossCuttingLaws.includes('ExplanationView != SourceOfTruth')
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GPR3 audit failed\n${JSON.stringify(checks,null,2)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gpr3-audit',contractCount:Object.keys(c).length,stressCaseCount:matrix.stressCases.length,lawCount:matrix.crossCuttingLaws.length,probeCount:Object.keys(probes.probes).length,checkCount:Object.keys(checks).length,checks,decision:'GPR3 reconstructs evidence/norm/explanation as a mostly-derived toolkit over existing provenance/verification/GDF0/GPR1/GPR2 sources. InterpretiveCommitment and PrecedentLink may have conditional durable relation identity, but neither record existence nor citation creates binding semantics. Existing replay evidence and verification are reused rather than replaced.'},null,2));
