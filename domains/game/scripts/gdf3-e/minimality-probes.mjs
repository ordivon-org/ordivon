#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const ordinaryDoor={candidate:'OPEN',canonicalState:{locked:true,hasKey:false},result:'REJECT',independentCaseStatus:false};
const sameHistoryDifferentStatus={history:'RUN-H',categoryA:'VALID',categoryB:'INVALID',historyChanged:false};
const sameBasisDifferentNorm={caseBasis:'E1',normA:'N1',normB:'N2',resultA:'VALID',resultB:'INVALID'};
const sameClassificationDifferentAuthority={classification:'FOUL',analyst:{binding:false},referee:{binding:true}};
const rulingVsEnforcement={determination:'DISQUALIFIED',binding:true,recordUpdateSucceeded:false};
const reviewLineage={d0:{status:'PENALTY',current:false},d1:{status:'NO_PENALTY',current:true,supersedes:'d0'},historyErased:false};
const roleFusedAgent={entity:'Agent-X',outputs:[{kind:'interpretation',binding:false},{kind:'ruleProposal',binding:false},{kind:'caseDetermination',binding:true,authoritySource:'case-delegation'}],sameEntityDifferentAuthority:true};
const syntheticSwap={human:{authorityContract:'A',result:'R'},synthetic:{authorityContract:'A',result:'R'},semanticDifferenceRequired:false};
const targetNecessity={statusToken:'VALID',targets:['run-category','action-legality','record-certification'],unscopedTokenAmbiguous:true};
const typedBasisNecessity={sameGenericBasisBag:['E1','N1'],caseBasis:'E1',normBasis:'N1',typesCounterfactuallyRelevant:true};
const authorityNecessity={sameContent:'OUT',bindingSourceA:null,bindingSourceB:'referee-authority',bindingDiffers:true};
const lineageDerived={events:[{id:'d0',kind:'determination'},{id:'d1',kind:'determination',supersedes:'d0'}],dedicatedLineageObjectNeeded:false,reconstructable:true};
const consequenceExternal={determination:'FOUL',enforcement:'restart',separable:true,determinationIdentitySurvivesWithoutEmbeddingEnforcement:true};
const result={
 schemaVersion:1,
 kind:'ordivon.game.gdf3-e-minimality-probes',
 cases:{ordinaryDoor,sameHistoryDifferentStatus,sameBasisDifferentNorm,sameClassificationDifferentAuthority,rulingVsEnforcement,reviewLineage,roleFusedAgent,syntheticSwap,targetNecessity,typedBasisNecessity,authorityNecessity,lineageDerived,consequenceExternal},
 falsifiers:{
   ordinaryExecutionNeedNotAdjudicate:!ordinaryDoor.independentCaseStatus,
   caseStatusCanVaryWithoutHistoryChange:!sameHistoryDifferentStatus.historyChanged && sameHistoryDifferentStatus.categoryA!==sameHistoryDifferentStatus.categoryB,
   caseBasisAndNormBasisTypesMatter:sameBasisDifferentNorm.resultA!==sameBasisDifferentNorm.resultB && typedBasisNecessity.typesCounterfactuallyRelevant,
   classificationNotDetermination:sameClassificationDifferentAuthority.analyst.binding!==sameClassificationDifferentAuthority.referee.binding,
   authorityRequiredForBinding:authorityNecessity.bindingDiffers,
   targetRequiredSemantically:targetNecessity.unscopedTokenAmbiguous,
   determinationNotEnforcement:rulingVsEnforcement.binding && !rulingVsEnforcement.recordUpdateSucceeded,
   lineageCanRemainDerived:lineageDerived.reconstructable && !lineageDerived.dedicatedLineageObjectNeeded,
   reversalNotHistoryErase:reviewLineage.d1.supersedes==='d0' && !reviewLineage.historyErased,
   consequenceNeedNotBeCore:consequenceExternal.separable && consequenceExternal.determinationIdentitySurvivesWithoutEmbeddingEnforcement,
   sameAgentDoesNotCollapseAuthority:roleFusedAgent.sameEntityDifferentAuthority,
   substrateNeutral:syntheticSwap.semanticDifferenceRequired===false
 },
 minimalContract:{
   name:'AuthoritativeCaseDeterminationContract',
   obligations:['DeterminationTargetAndStatus','BindingAuthorityAndCurrentness','TypedDeterminationBasisWhenMaterial'],
   derived:['DecisionLineageReviewTopology','NormApplicationDetail','DiscretionEnvelope'],
   external:['EnforcementConsequenceExecution','WorldTruth','PerceptionMechanism','HumanLegitimacyMechanism']
 }
};
const out=process.argv[2]??'evidence/gdf3-e/minimality-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
