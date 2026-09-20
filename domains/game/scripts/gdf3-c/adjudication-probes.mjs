#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const determination = ({id, caseId, content, binding=true, authority='Judge', basedOn=[], supersedes=null, current=true}) => ({id, caseId, content, binding, authority, basedOn, supersedes, current});

const zeroModel = {
  state: {doorLocked:true, hasKey:false},
  candidate:'open-door',
  currentRule:'open allowed iff !doorLocked || hasKey',
  result:'REJECT',
  explicitEvidenceDisputeNeeded:false,
  reviewNeeded:false
};

const truthVsEvidence = {
  worldTruth:{contactOccurred:true},
  evidenceA:{cameraOccluded:true, testimony:'no-contact-seen'},
  evidenceB:{cameraOccluded:false, replay:'contact-visible'},
  truthHeldFixed:true,
  findingCanDifferWithEvidence:true
};

const observationRelevance = {
  sameObservation:'player crossed line at t=10.2',
  caseQuestionA:'was player out of bounds?',
  caseQuestionB:'was player late relative to t=9.0 deadline?',
  relevanceDependsOnQuestion:true
};

const classificationVsRuling = {
  sameClassification:'subjective-offence-likely',
  analyst:{binding:false},
  referee:{binding:true},
  sameContentDifferentBinding:true
};

const finalityVsTruth = {
  representedWorldTruth:'NO_FOUL',
  officialFinalDetermination:'FOUL',
  finalWithinScope:true,
  correctRelativeToRepresentedTruth:false
};

const reviewLineage = {
  d0: determination({id:'D0',caseId:'K1',content:'PENALTY',authority:'Referee',basedOn:['live-view'],current:false}),
  d1: determination({id:'D1',caseId:'K1',content:'NO_PENALTY',authority:'Referee',basedOn:['VAR-replay'],supersedes:'D0',current:true}),
  oldDecisionErased:false,
  currentDecision:'D1'
};

const partialRollback = {
  originalDecision:'D0',
  reversedBy:'D1',
  postIncidentDisciplinaryAction:'CAUTION_FOR_SEPARATE_POST_INCIDENT_ACT',
  persistsAfterReversal:true,
  fullRollback:false
};

const sameDecisionDifferentContestability = {
  decisionContent:'OUT',
  beforeCutoff:{reviewPathAvailable:true},
  afterCutoff:{reviewPathAvailable:false},
  contestabilityDependsOnProcedureTime:true
};

const reviewWithoutNewEvidence = {
  evidenceDigest:'E1',
  d0:{interpretation:'predicate-A',result:'INVALID'},
  d1:{interpretation:'predicate-B',result:'VALID'},
  newEvidence:false,
  decisionChanged:true
};

const postHocCertification = {
  runHistoryDigest:'RUN-H1',
  beforeCertification:null,
  afterCertification:'VALID_CATEGORY_RECORD',
  runHistoryChanged:false
};

const naturalLanguageIntent = {
  utterance:'clear the second floor then cover the stairs',
  interpretations:[
    {candidate:'plan-A',confidence:0.61},
    {candidate:'plan-B',confidence:0.37}
  ],
  interpretationIsAuthoritativeEffect:false,
  requiresAdmissionOrPolicySelection:true
};

const generatedRule = {
  modelProposal:'new rule text R2',
  currentAuthoritativeRule:'R1',
  proposalIsCurrentRule:false,
  adoptionNeeded:true
};

const judgedSupport = {
  performanceHistory:'P1',
  supportSystemOutput:'element-angle=44deg',
  supportOutputBinding:false,
  superiorJuryDetermination:'element-value-X',
  finalAuthoritySeparated:true
};

const defeasibleCase = {
  initialEvidence:['E1'],
  initialDetermination:'VIOLATION',
  defeatingEvidenceAdded:'E2-exception-applies',
  laterDetermination:'NO_VIOLATION',
  monotonicityRequired:false
};

const fusedAgent = {
  entity:'Agent-X',
  outputs:[
    {kind:'proposal',content:'A1',binding:false},
    {kind:'interpretation',content:'A1-means-X',binding:false},
    {kind:'determination',content:'ADMIT-X',binding:true,authoritySource:'practice-contract'}
  ],
  sameEntityDoesNotCollapseOutputRoles:true
};

const rulingVsEnforcement = {
  determination:'DISQUALIFIED',
  recordUpdateSucceeded:false,
  determinationStillExists:true,
  separated:true
};

const result = {
  schemaVersion:1,
  kind:'ordivon.game.gdf3-c-adjudication-probes',
  epistemicBoundary:{
    proves:[
      'in the constructed cases, deterministic admission is sufficient for a closed canonical-state case but not necessary as the universal adjudication model',
      'evidence/finding can vary while modeled WorldTruth is held fixed',
      'evidence relevance depends on the case question rather than observation identity alone',
      'the same classification content can be nonbinding or binding depending on current authority',
      'scoped finality can coexist with an incorrect determination relative to represented WorldTruth',
      'review can supersede a prior decision while preserving its historical existence in a decision lineage',
      'reversal need not roll back every intervening consequence',
      'contestability can change with procedure/time while decision content remains fixed',
      'review can change a decision through interpretation without new evidence',
      'post-hoc certification can alter official record status without rewriting original run history',
      'natural-language interpretation can remain a candidate rather than authoritative Game effect',
      'generated rule text can remain a proposal until adopted by current authority',
      'judging-support output can remain nonbinding evidence while a jury/authority issues the determination',
      'new defeating evidence can rationally reverse a prior determination, so monotonic evidence accumulation is not universal',
      'one Agent can emit proposal, interpretation and determination outputs with distinct binding/provenance status'
    ],
    doesNotProve:[
      'that one universal adjudication algorithm exists',
      'that every Game action requires an explicit adjudication case object',
      'that WorldTruth is always available to the system',
      'that formal appeal is universally desirable',
      'that adjudication must expose natural-language rationale',
      'that human or synthetic adjudicators are intrinsically more legitimate or correct',
      'that the proposed contract fields are a required storage schema'
    ]
  },
  cases:{
    zeroModel,
    truthVsEvidence,
    observationRelevance,
    classificationVsRuling,
    finalityVsTruth,
    reviewLineage,
    partialRollback,
    sameDecisionDifferentContestability,
    reviewWithoutNewEvidence,
    postHocCertification,
    naturalLanguageIntent,
    generatedRule,
    judgedSupport,
    defeasibleCase,
    fusedAgent,
    rulingVsEnforcement
  },
  strongestFalsifiers:{
    deterministicAdmissionNotUniversal: zeroModel.explicitEvidenceDisputeNeeded === false && truthVsEvidence.findingCanDifferWithEvidence === true,
    observationNotEvidenceByIdentity: observationRelevance.relevanceDependsOnQuestion === true,
    evidenceNotWorldTruth: truthVsEvidence.truthHeldFixed && truthVsEvidence.findingCanDifferWithEvidence,
    classificationNotRuling: classificationVsRuling.sameContentDifferentBinding,
    finalityNotTruth: finalityVsTruth.finalWithinScope && !finalityVsTruth.correctRelativeToRepresentedTruth,
    reviewNotReplay: reviewWithoutNewEvidence.decisionChanged && !reviewWithoutNewEvidence.newEvidence,
    reversalNotHistoryErasure: reviewLineage.oldDecisionErased === false && reviewLineage.currentDecision === 'D1',
    reversalNotFullRollback: partialRollback.persistsAfterReversal && !partialRollback.fullRollback,
    contestabilityNotDecisionContent: sameDecisionDifferentContestability.contestabilityDependsOnProcedureTime,
    certificationNotHistoryRewrite: !postHocCertification.runHistoryChanged && postHocCertification.afterCertification !== null,
    naturalLanguageInterpretationNotAuthoritativeEffect: !naturalLanguageIntent.interpretationIsAuthoritativeEffect && naturalLanguageIntent.requiresAdmissionOrPolicySelection,
    ruleGenerationNotRuleAuthority: generatedRule.proposalIsCurrentRule === false && generatedRule.adoptionNeeded,
    judgingSupportNotDecisionAuthority: !judgedSupport.supportOutputBinding && judgedSupport.finalAuthoritySeparated,
    adjudicationCanBeDefeasible: !defeasibleCase.monotonicityRequired && defeasibleCase.initialDetermination !== defeasibleCase.laterDetermination,
    modelIdentityNotOutputAuthorityIdentity: fusedAgent.sameEntityDoesNotCollapseOutputRoles,
    rulingNotEnforcement: rulingVsEnforcement.separated && rulingVsEnforcement.determinationStillExists && !rulingVsEnforcement.recordUpdateSucceeded
  }
};

const output = process.argv[2] ?? 'evidence/gdf3-c/adjudication-probes.json';
fs.mkdirSync(path.dirname(output), {recursive:true});
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
