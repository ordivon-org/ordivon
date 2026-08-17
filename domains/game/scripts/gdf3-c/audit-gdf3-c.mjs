#!/usr/bin/env node
import fs from 'node:fs';

const matrix = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf3-c/adjudication-term-case-matrix.json','utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf3-c/adjudication-probes.json','utf8'));
const terms = new Set(matrix.terms.map((x)=>x.term));
const required = ['Observation','Evidence','Claim','WorldTruth','CaseFinding','RuleRepresentation','ApplicableNormBasis','Interpretation','Classification','RationaleOrReasoningBasis','AuthoritativeDetermination','EnforcementOrEffectuation','Review','Appeal','Contestability','Finality','DecisionLineage','Reversal','AdjudicationCaseContract'];
for (const term of required) if (!terms.has(term)) throw new Error(`missing term ${term}`);
const f = probes.strongestFalsifiers;
const checks = {
  enoughBoundaryCases: matrix.boundaryCases.length >= 24,
  deterministicBaselinePresent: matrix.zeroModel.name === 'DeterministicAdmission',
  deterministicNotUniversal: f.deterministicAdmissionNotUniversal === true,
  observationEvidenceSeparated: f.observationNotEvidenceByIdentity === true,
  evidenceTruthSeparated: f.evidenceNotWorldTruth === true,
  classificationRulingSeparated: f.classificationNotRuling === true,
  finalityTruthSeparated: f.finalityNotTruth === true,
  reviewReplaySeparated: f.reviewNotReplay === true,
  reversalHistorySeparated: f.reversalNotHistoryErasure === true,
  reversalRollbackSeparated: f.reversalNotFullRollback === true,
  contestabilityDecisionSeparated: f.contestabilityNotDecisionContent === true,
  certificationHistorySeparated: f.certificationNotHistoryRewrite === true,
  intentAdmissionSeparated: f.naturalLanguageInterpretationNotAuthoritativeEffect === true,
  generationAuthoritySeparated: f.ruleGenerationNotRuleAuthority === true,
  supportDecisionAuthoritySeparated: f.judgingSupportNotDecisionAuthority === true,
  defeasibilitySurvives: f.adjudicationCanBeDefeasible === true,
  modelIdentityAuthoritySeparated: f.modelIdentityNotOutputAuthorityIdentity === true,
  rulingEnforcementSeparated: f.rulingNotEnforcement === true,
  interpretationPrimitiveRejected: matrix.candidateCompression.InterpretationPrimitive === 'REJECT_AS_SINGLE_STAGE',
  reviewPrimitiveRejected: matrix.candidateCompression.ReviewPrimitive === 'REJECT',
  contestabilityPrimitiveRejected: matrix.candidateCompression.ContestabilityPrimitive === 'REJECT_TO_DERIVED_TOPOLOGY',
  adjudicationContractRetained: matrix.candidateCompression.AdjudicationCaseContract === 'RETAIN_AS_GAME_OWNED_RESPONSIBILITY_CANDIDATE',
  independentResponsibilitySurvives: matrix.selection.adjudicationIndependentResponsibility === true,
  noNewSemanticPrimitive: matrix.selection.newSemanticPrimitiveRequired === false,
  noFoundationReopen: Object.values(matrix.foundationReopen).every((x)=>x === false)
};
if (Object.values(checks).some((x)=>!x)) throw new Error(`GDF3-C audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({
  schemaVersion:1,
  kind:'ordivon.game.gdf3-c-audit',
  termCount:matrix.terms.length,
  boundaryCaseCount:matrix.boundaryCases.length,
  checkCount:Object.keys(checks).length,
  checks,
  strongestConclusion:'GDF3-C rejects Evidence/Interpretation/Review/Finality/Contestability as new primitives but retains an AdjudicationCaseContract as a distinct Game-owned responsibility candidate. It separates case question, evidence/finding, current norm basis, nonbinding interpretation/classification, binding determination, enforcement and review lineage; finality is not truth, reversal is neither history erasure nor universal rollback, and natural-language/model output remains non-authoritative until admitted by current authority.'
}, null, 2));
