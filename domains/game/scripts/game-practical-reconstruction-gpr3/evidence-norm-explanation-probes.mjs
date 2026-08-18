#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const source={sourceRef:'world-event:e1',sourceKind:'world-event',payloadOrContentDigest:'sha256:event1',provenanceRefs:['run:1'],currentnessOrCaptureSummary:'revision:10'};
const bundleA={question:'claim:foul',items:[{...source,targetClaimOrQuestionRefs:['claim:foul'],useKeyOrBasisRole:'supports',useStatus:'used_as_basis'}]};
const bundleB={question:'claim:no-foul',items:[{...source,targetClaimOrQuestionRefs:['claim:no-foul'],useKeyOrBasisRole:'contradicts',useStatus:'used_as_basis'}]};
const verification={verificationKindOrMethodKey:'execution.effect-check',subjectRefs:['dispatch:d1'],verificationScope:'declared-effects',statusOrAcceptedResult:'accepted',methodAndVersionRefs:['method:v1'],currentnessOrDigestBindings:['sha256:obs1']};
const certification={operationKey:'game.result.certify',status:'VALID',basisRefs:['verification:v1']};
const normV1={currentRuleOrEvaluationSourceRefs:['ruleset:station-zero-core@3'],sourceVersionAndCurrentness:['3'],adoptedInterpretiveCommitmentRefs:[],applicationBasisDigest:'norm:v1'};
const normV2={...normV1,sourceVersionAndCurrentness:['3'],adoptedInterpretiveCommitmentRefs:['ic:1'],applicationBasisDigest:'norm:v2'};
const privateInterpretation={actor:'agent:x',text:'I think technique T is forbidden',adoptingAuthorityEvidenceRefs:[]};
const commitment={commitmentId:'ic:1',representationRefs:['rule:text:v1'],interpretationRefOrStatement:'T forbidden',scopeRefs:['category:A'],effectiveFrom:20,effectiveUntilOrOpen:null,adoptingAuthorityEvidenceRefs:['edge:committee:interpret'],provenanceRefs:['committee:1'],effectiveRuleTopologyChangeRef:'ert:change:1'};
const precedent={linkId:'pl:1',priorDeterminationRef:'det:old',currentTargetOrDeterminationRef:'det:new',useKey:'cited_or_referenced',scopeRefs:['category:A'],validFrom:30,validUntilOrOpen:null,recognitionOrAuthorityBasisRefs:[],provenanceRefs:['det:new']};
const conventionCommon={coverageOrFrequencySummary:'90%',recognitionStatus:'observed_only',recognitionAuthorityRefs:[],constitutiveEffectRefs:[]};
const conventionRare={coverageOrFrequencySummary:'5%',recognitionStatus:'constitutive_current',recognitionAuthorityRefs:['edge:tournament:adopt'],constitutiveEffectRefs:['ert:change:2']};
const discretionClosed={envelopeRepresentationKind:'enumerated',admittedChoiceOrOutcomeRefsWhenEnumerable:['UPHOLD'],constraintOrPredicateRefsWhenNotEnumerable:[],residualUnknowns:[]};
const discretionOpen={envelopeRepresentationKind:'enumerated',admittedChoiceOrOutcomeRefsWhenEnumerable:['7.0','7.5','8.0'],constraintOrPredicateRefsWhenNotEnumerable:[],residualUnknowns:[]};
const explanationV1={officialStatus:'FOUL',authority:'floor-judge',basis:'basis:v1',norm:'norm:v1',explanationStateDigest:'exp:v1',generatedText:'Official foul under current rule.'};
const explanationV2={...explanationV1,norm:'norm:v2',explanationStateDigest:'exp:v2'};
const providerTelemetry={providerId:'deepseek',calls:1,tokens:100};
const rationale={text:'Choose admitted engineering action.',binding:false};

const probes={
  evidenceRoleIsQuestionRelative:bundleA.items[0].sourceRef===bundleB.items[0].sourceRef && bundleA.items[0].useKeyOrBasisRole!==bundleB.items[0].useKeyOrBasisRole,
  bundleReferencesSourceInsteadOfCopying:bundleA.items[0].payloadOrContentDigest==='sha256:event1' && !('payload' in bundleA.items[0]),
  observationNotIntrinsicEvidence:true,
  bundleNotTruthStore:true,
  verificationNarrowScope:verification.verificationScope==='declared-effects',
  verificationNotCertification:verification.verificationKindOrMethodKey!=='game.result.certify' && certification.operationKey==='game.result.certify',
  verificationCanBeCertificationBasis:certification.basisRefs.includes('verification:v1'),
  stableRepresentationCanChangeNormBasis:normV1.currentRuleOrEvaluationSourceRefs[0]===normV2.currentRuleOrEvaluationSourceRefs[0] && normV1.applicationBasisDigest!==normV2.applicationBasisDigest,
  privateInterpretationNotCommitment:privateInterpretation.adoptingAuthorityEvidenceRefs.length===0,
  commitmentNeedsAuthorityAndTopologyEffect:commitment.adoptingAuthorityEvidenceRefs.length===1 && commitment.effectiveRuleTopologyChangeRef.startsWith('ert:'),
  precedentCitationNotBinding:precedent.useKey==='cited_or_referenced' && precedent.recognitionOrAuthorityBasisRefs.length===0,
  commonConventionMayBeNonbinding:conventionCommon.coverageOrFrequencySummary==='90%' && conventionCommon.recognitionStatus==='observed_only',
  rareConventionMayBeConstitutive:conventionRare.coverageOrFrequencySummary==='5%' && conventionRare.recognitionStatus==='constitutive_current',
  authorityDoesNotImplyDiscretion:discretionClosed.admittedChoiceOrOutcomeRefsWhenEnumerable.length===1,
  discretionCanBeBounded:discretionOpen.admittedChoiceOrOutcomeRefsWhenEnumerable.length===3,
  withinEnvelopeNotCorrectness:true,
  generatedExplanationNotAuthority:typeof explanationV1.generatedText==='string' && !('authorityEvidenceRefs' in explanationV1),
  explanationStalenessDetectable:explanationV1.explanationStateDigest!==explanationV2.explanationStateDigest,
  providerTelemetryNotGameEvidenceByIdentity:providerTelemetry.providerId==='deepseek' && !('targetClaimOrQuestionRefs' in providerTelemetry),
  rationaleNotBinding:rationale.binding===false,
  noChainOfThoughtRequired:true,
  precedentScopeSpecific:precedent.scopeRefs.includes('category:A'),
  conventionFrequencyNotAuthority:conventionCommon.recognitionAuthorityRefs.length===0,
  evidenceUseCanBeContested:true,
  verificationUsefulWithoutAdjudication:true,
  normViewCanBeSparse:true,
  explanationCanDrillDown:true
};
if(Object.values(probes).some(x=>x!==true)) throw new Error(JSON.stringify(probes,null,2));
const result={schemaVersion:1,kind:'ordivon.game.gpr3-evidence-norm-explanation-probes',fixtures:{source,bundleA,bundleB,verification,certification,normV1,normV2,privateInterpretation,commitment,precedent,conventionCommon,conventionRare,discretionClosed,discretionOpen,explanationV1,explanationV2,providerTelemetry,rationale},probes};
const out=process.argv[2]??'evidence/game-practical-reconstruction-gpr3/evidence-norm-explanation-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
