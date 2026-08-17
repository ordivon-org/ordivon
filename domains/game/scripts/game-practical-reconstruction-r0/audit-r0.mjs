#!/usr/bin/env node
import fs from 'node:fs';
const p=process.argv[2]??'evidence/game-practical-reconstruction-r0/concept-utility-map.json';
const d=JSON.parse(fs.readFileSync(p,'utf8'));
const names=new Set(d.concepts.map(x=>x.name));
const counts={};
for(const c of d.concepts) counts[c.tier]=(counts[c.tier]??0)+1;
const checks={
  enoughConcepts:d.concepts.length>=30,
  uniqueNames:names.size===d.concepts.length,
  representationForms:Object.keys(d.representationForms).length>=8,
  reconstructionContract:d.reconstructionContract.length>=8,
  hasT1:counts.T1_cross_game_toolkit>=10,
  hasT2:counts.T2_conditional_toolkit>=10,
  hasT3:counts.T3_ui_authoring_vocabulary>=4,
  hasCaution:counts.T4_local_or_caution>=1,
  roleAuthorityCluster:d.priorityClusters[0].id==='P1'&&d.priorityClusters[0].priority==='HIGHEST',
  gpr1Selected:d.selection.nextFocusedRound.startsWith('GPR1'),
  gdf3NotReopened:d.purpose.includes('without promoting them back into foundations'),
  everyConceptHasSources:d.concepts.every(x=>x.semanticSources?.length>0),
  everyConceptDeclaresHiddenDistinctions:d.concepts.every(x=>x.hiddenDistinctions?.length>0),
  everyConceptHasRecommendation:d.concepts.every(x=>typeof x.recommendation==='string'&&x.recommendation.length>0),
  participantIsView:d.concepts.find(x=>x.name==='ParticipantView')?.forms.includes('derived_query_view')===true,
  delegationNotPrimitive:d.concepts.find(x=>x.name==='DelegationGrant')?.forms.includes('workflow_object')===true,
  judgeIsTemplate:d.concepts.find(x=>x.name==='RefereeJudgeRoleBundle')?.forms.includes('local_pattern')===true,
  evidenceGuarded:d.concepts.find(x=>x.name==='EvidenceBundleForCase')?.misuseRisk>=4,
  decisionLineageDerived:d.concepts.find(x=>x.name==='DecisionLineage')?.forms.includes('derived_query_view')===true,
  ruleStandardCaution:d.concepts.find(x=>x.name==='RuleStandardLabels')?.tier==='T4_local_or_caution'
};
if(Object.values(checks).some(Boolean)===false || Object.values(checks).some(x=>!x)) throw new Error(JSON.stringify(checks,null,2));
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.practical-reconstruction-r0-audit',conceptCount:d.concepts.length,tierCounts:counts,clusterCount:d.priorityClusters.length,checkCount:Object.keys(checks).length,checks,selected:d.selection.nextFocusedRound},null,2));
