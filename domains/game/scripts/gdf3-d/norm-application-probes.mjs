#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const norm = ({id,text,scope='case',current=true,source='practice',priority=0}) => ({id,text,scope,current,source,priority});

const closed = {
  caseBasis:{x:7},
  norm:norm({id:'R1',text:'ALLOW iff x >= 5'}),
  result:'ALLOW',
  openTextureNeeded:false
};

const exception = {
  defaultNorm:norm({id:'R2',text:'PROHIBIT action A unless exception E'}),
  caseWithoutE:{E:false,result:'PROHIBIT'},
  caseWithE:{E:true,result:'ALLOW'},
  normTextHeldFixed:true
};

const conflictPriority = {
  n1:norm({id:'N1',text:'ALLOW A',priority:1}),
  n2:norm({id:'N2',text:'PROHIBIT A',priority:2}),
  result:'PROHIBIT',
  changedPriorityResult:'ALLOW'
};

const spiritBounded = {
  literalRule:'apply Laws',
  purposeClause:'spirit of the game',
  discretion:'within framework of Laws',
  purposeIsUnboundedOverride:false
};

const factualSubjective = {
  factual:{example:'position/offside/location',reviewMode:'VAR-only usually appropriate'},
  subjective:{example:'intensity/interference/handball considerations',reviewMode:'on-field review appropriate'},
  oneUniversalPredicateClosure:false
};

const precedent = {
  priorDecision:'P1',
  similarity:true,
  bindingByIdentity:false,
  persuasiveWhenAdmitted:true,
  standingForceRequiresAuthorityRecognition:true
};

const convention = {
  frequentUnauthorized:{frequency:0.9,binding:false},
  rareAuthorized:{frequency:0.1,binding:true},
  frequencyNotAuthority:true
};

const speedrun = {
  broadRuleWord:'glitchless',
  artifactMechanicsHeldFixed:true,
  communityAdoptedTechniqueListCanChange:true,
  effectiveCategorySemanticsCanChangeWithoutArtifactPatch:true
};

const discretion = {
  caseBasis:'K',
  normBasis:'S',
  authorizedOutcomes:['O1','O2'],
  arbitraryOutcome:'O3',
  arbitraryOutcomeAuthorized:false,
  residualChoiceExists:true
};

const interpretiveVsRuleChange = {
  sameOutcome:'A prohibited',
  path1:{kind:'rule-change',representationChanged:true,authoritySource:'rules-authority'},
  path2:{kind:'interpretive-change',representationChanged:false,authoritySource:'interpretive-authority',effectiveSemanticsChanged:true},
  outcomeDoesNotDetermineProvenance:true
};

const retroactivity = {
  eventHistoryDigest:'H1',
  newInterpretation:'I2',
  prospective:{appliesTo:['future-cases'],historyChanged:false},
  retrospectiveCertification:{appliesTo:['past-record-status'],historyChanged:false},
  temporalScopeIndependent:true
};

const oneOffToStanding = {
  caseRuling:{id:'D1',futureNormForce:false},
  laterPracticeAdoption:{interpretiveCommitment:'I1',futureNormForce:true},
  priorRulingNotPrecedentByIdentity:true
};

const agent = {
  entity:'Agent-X',
  proposal:{reading:'literal',binding:false},
  alternative:{reading:'purpose-sensitive',binding:false},
  caseAuthority:{canBindCurrentCase:true},
  ruleChangeAuthority:false,
  currentCaseRulingCreatesStandingFutureRule:false
};

const adoptedAgentInterpretation = {
  entity:'Agent-X',
  delegatedInterpretiveScope:'category-C for season-S',
  current:true,
  futureForceWithinScope:true,
  forceDerivesFromDelegation:true
};

const consistency = {
  caseA:{facts:['f1','f2'],result:'R'},
  caseB:{facts:['f1','f2','defeater'],result:'not-R'},
  identicalOutcomeRequiredForConsistency:false,
  relevanceDimensionsMatter:true
};

const result = {
  schemaVersion:1,
  kind:'ordivon.game.gdf3-d-norm-application-probes',
  epistemicBoundary:{
    proves:[
      'closed norm application remains a sufficient limiting case',
      'exceptions/defeaters can alter outcomes with fixed norm text through case conditions/applicability relations',
      'norm conflicts can be represented through scoped priority/resolution relations whose currentness may change',
      'purpose/spirit clauses can be operative while remaining bounded rather than functioning as universal trump rules',
      'factual and subjective application regimes can coexist under one rule system',
      'prior decisions do not become binding precedents merely by historical existence or similarity',
      'frequency of convention does not determine authority',
      'effective category semantics can change through adopted practice interpretation while artifact mechanics stay fixed',
      'discretion can be represented as bounded residual choice rather than arbitrariness',
      'rule change and interpretive change can yield the same practical outcome while retaining different provenance',
      'retroactive normative status change need not rewrite underlying event history',
      'one-off rulings acquire standing future norm force only through a later authority/recognition relation',
      'an Agent with case authority but no rule-change authority can bind a current case without automatically legislating for future cases',
      'delegated standing interpretive force derives from authority scope/currentness rather than model identity',
      'consistency does not require identical outcomes where norm-relevant case differences exist'
    ],
    doesNotProve:[
      'that every practice should expose explicit priority graphs',
      'that rules and standards have one exact universal dividing line',
      'that purpose-sensitive interpretation is always superior to literal application',
      'that precedent should be binding in games',
      'that discretion is desirable in every GameForm',
      'that a universal normative reasoning engine is part of Game foundations',
      'that the derived NormApplicationBasis must be a storage object'
    ]
  },
  cases:{closed,exception,conflictPriority,spiritBounded,factualSubjective,precedent,convention,speedrun,discretion,interpretiveVsRuleChange,retroactivity,oneOffToStanding,agent,adoptedAgentInterpretation,consistency},
  strongestFalsifiers:{
    closedRuleModelNotUniversal: closed.openTextureNeeded === false && factualSubjective.oneUniversalPredicateClosure === false,
    exceptionNotPrimitive: exception.normTextHeldFixed && exception.caseWithoutE.result !== exception.caseWithE.result,
    conflictResolutionCurrentnessMatters: conflictPriority.result !== conflictPriority.changedPriorityResult,
    purposeNotUnboundedMetaRule: spiritBounded.purposeIsUnboundedOverride === false,
    ruleStandardNotOntologicalBinary: factualSubjective.factual.reviewMode !== factualSubjective.subjective.reviewMode,
    priorDecisionNotBindingPrecedent: !precedent.bindingByIdentity && precedent.standingForceRequiresAuthorityRecognition,
    conventionFrequencyNotAuthority: convention.frequencyNotAuthority && !convention.frequentUnauthorized.binding && convention.rareAuthorized.binding,
    adoptedInterpretationCanChangeEffectiveRules: speedrun.effectiveCategorySemanticsCanChangeWithoutArtifactPatch,
    discretionNotArbitrariness: discretion.residualChoiceExists && !discretion.arbitraryOutcomeAuthorized,
    ruleChangeNotInterpretiveChange: interpretiveVsRuleChange.path1.kind !== interpretiveVsRuleChange.path2.kind && interpretiveVsRuleChange.outcomeDoesNotDetermineProvenance,
    retroactivityNotHistoryRewrite: !retroactivity.prospective.historyChanged && !retroactivity.retrospectiveCertification.historyChanged,
    rulingNotPrecedentByIdentity: oneOffToStanding.priorRulingNotPrecedentByIdentity && oneOffToStanding.laterPracticeAdoption.futureNormForce,
    caseAuthorityNotLegislativeAuthority: agent.caseAuthority.canBindCurrentCase && !agent.ruleChangeAuthority && !agent.currentCaseRulingCreatesStandingFutureRule,
    modelIdentityNotInterpretiveAuthority: adoptedAgentInterpretation.forceDerivesFromDelegation,
    consistencyNotIdenticalOutcome: !consistency.identicalOutcomeRequiredForConsistency && consistency.relevanceDimensionsMatter
  }
};

const output = process.argv[2] ?? 'evidence/gdf3-d/norm-application-probes.json';
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
