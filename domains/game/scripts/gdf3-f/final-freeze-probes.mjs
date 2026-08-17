#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const statusIdentity={token:'VALID',targets:['action','run-category','record','appeal'],ambiguousWithoutTarget:true};
const authorityPair={content:'FOUL',analyst:{binding:false},referee:{binding:true},sameContent:true};
const roleFusion={entity:'X',operations:{proposal:false,interpretation:false,ruleChange:true,caseDetermination:true,enforcement:true},authorityOperationSpecific:true};
const basisPairs={
  sameEvidence:{evidence:'E',normA:'N1',normB:'N2',resultA:'VALID',resultB:'INVALID'},
  sameNorm:{norm:'N',evidenceA:'E1',evidenceB:'E2',resultA:'VALID',resultB:'INVALID'}
};
const deterministicPair={
  algorithm:'A',
  transientExecution:{officialStatus:false,adjudicative:false},
  officialResult:{officialStatus:true,appealable:true,adjudicative:true}
};
const solitaryPair={
  entity:'Solo',
  tentativeBelief:{binding:false,adjudicative:false},
  selfMaintainedCertification:{binding:true,scope:'self-authored challenge',adjudicative:true},
  externalInstitutionRequired:false
};
const review={d0:{status:'PENALTY',current:false},d1:{status:'NO_PENALTY',current:true,supersedes:'d0'},historyPreserved:true,dedicatedLineagePrimitive:false};
const enforcement={determination:'DISQUALIFIED',binding:true,enforcementSucceeded:false,determinationStillExists:true};
const fusedExecution={determinationAndEnforcementSameStep:true,conceptuallySeparableUnderCounterfactualReplacement:true};
const substrate={human:{authority:'A'},synthetic:{authority:'A'},semanticContractChanged:false};
const owner={worldTruth:'H',officialStatus:'INVALID',canCoexist:true};

const result={
  schemaVersion:1,
  kind:'ordivon.game.gdf3-f-final-freeze-probes',
  cases:{statusIdentity,authorityPair,roleFusion,basisPairs,deterministicPair,solitaryPair,review,enforcement,fusedExecution,substrate,owner},
  falsifiers:{
    targetStatusCannotDisappear:statusIdentity.ambiguousWithoutTarget,
    bindingCannotComeFromContent:authorityPair.sameContent && authorityPair.analyst.binding!==authorityPair.referee.binding,
    authorityMustBeOperationSpecific:roleFusion.authorityOperationSpecific,
    basisTypingCounterfactual:true,
    deterministicAlgorithmDoesNotDecideBoundary:deterministicPair.transientExecution.adjudicative!==deterministicPair.officialResult.adjudicative,
    externalInstitutionNotRequired:!solitaryPair.externalInstitutionRequired && !solitaryPair.tentativeBelief.adjudicative && solitaryPair.selfMaintainedCertification.adjudicative,
    lineageRemainsDerived:review.historyPreserved && !review.dedicatedLineagePrimitive && review.d1.supersedes==='d0',
    enforcementNotCore:enforcement.binding && !enforcement.enforcementSucceeded && enforcement.determinationStillExists,
    fusedImplementationDoesNotEraseSeparation:fusedExecution.determinationAndEnforcementSameStep && fusedExecution.conceptuallySeparableUnderCounterfactualReplacement,
    substrateNeutral:substrate.semanticContractChanged===false,
    officialStatusNotWorldTruth:owner.canCoexist && owner.worldTruth!==owner.officialStatus
  },
  frozenContract:{
    name:'AuthoritativeCaseDeterminationContract',
    obligations:['DeterminationTargetAndStatus','BindingAuthorityAndCurrentness','TypedDeterminationBasisWhenMaterial'],
    ontologyPrimitive:false
  }
};

if(!(basisPairs.sameEvidence.resultA!==basisPairs.sameEvidence.resultB && basisPairs.sameNorm.resultA!==basisPairs.sameNorm.resultB)) throw new Error('basis counterfactual construction failed');
const out=process.argv[2]??'evidence/gdf3-f/final-freeze-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
