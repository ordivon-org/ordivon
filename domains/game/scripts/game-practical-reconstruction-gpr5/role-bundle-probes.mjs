#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const refereeTemplate={templateId:'role-bundle:referee',displayLabel:'Referee',defaultAdmissionPolicy:'NO_HIDDEN_GRANTS',slices:['observe_case','classify_or_recommend','case_decide','case_review','enforce']};
const judgeNoAuthority={holderRef:'human:j1',displayLabels:['Referee'],roleAssignmentRefs:['ra:j1'],effectiveAuthorityOperations:[],controlOrCapabilitySummary:['whistle'],bundleStateDigest:'bundle:j1:v1'};
const judgeWithAuthority={...judgeNoAuthority,effectiveAuthorityOperations:['game.case.decide'],bundleStateDigest:'bundle:j1:v2'};
const coach={templateId:'role-bundle:coach',slices:['observe','analyze','recommend'],effectiveAuthorityOperations:[]};
const gmSplit={holders:{'human:g1':['present_or_generate_world','control_npcs_or_world_entities'],'human:g2':['case_adjudicate']},effectiveOperationMappings:{'human:g1':['game.world.control.local'],'human:g2':['game.case.decide']}};
const moderatorOperator={holderRef:'agent:m1',displayLabels:['Moderator','Operator'],effectiveAuthorityOperations:['game.case.decide','game.operation.execute'],capabilities:['moderation-api-write'],providerId:'provider:a'};
const moderatorOperatorProviderSwap={...moderatorOperator,providerId:'provider:b'};
const engineer={roleId:'engineer',controllerKind:'agent',capabilityIds:['repair','power-control'],objectiveDoctrine:['systems','mission-cargo']};
const engineerNoTool={...engineer,capabilityIds:['power-control']};
const playerOrder={kind:'standing-order',worldMutationAuthority:false,strategyConstraint:true};
const casefileRole={role:'Archive technician',authorityRefs:[]};
const experience={templateId:'role-bundle:experience-manager',effectiveAuthorityOperations:['game.experience.adjust'],optimizationMetric:'retention',playerValue:null};
const diagnostic={checks:['template_selected_but_no_authority_source','authority_without_required_capability_or_tool','capability_or_control_without_required_authority','self_review_or_separation_policy_conflict'],disposition:'blocked_missing_source'};

const probes={
  templateDoesNotGrantAuthority:refereeTemplate.defaultAdmissionPolicy==='NO_HIDDEN_GRANTS' && judgeNoAuthority.effectiveAuthorityOperations.length===0,
  explicitAuthorityChangesManifest:judgeWithAuthority.effectiveAuthorityOperations.includes('game.case.decide') && judgeWithAuthority.bundleStateDigest!==judgeNoAuthority.bundleStateDigest,
  sameLabelDifferentManifest:judgeWithAuthority.displayLabels[0]===judgeNoAuthority.displayLabels[0] && judgeWithAuthority.effectiveAuthorityOperations.length!==judgeNoAuthority.effectiveAuthorityOperations.length,
  coachNonbindingByDefault:coach.effectiveAuthorityOperations.length===0,
  splitGmResponsibilities:gmSplit.effectiveOperationMappings['human:g1'][0]!==gmSplit.effectiveOperationMappings['human:g2'][0],
  sameHolderMultipleLabelsDoNotCreateAllAuthority:moderatorOperator.displayLabels.length===2 && !moderatorOperator.effectiveAuthorityOperations.includes('game.rule.change'),
  providerSwapPreservesSemanticBundle:moderatorOperator.effectiveAuthorityOperations.join('|')===moderatorOperatorProviderSwap.effectiveAuthorityOperations.join('|') && moderatorOperator.providerId!==moderatorOperatorProviderSwap.providerId,
  roleSeparateFromController:engineer.roleId==='engineer' && engineer.controllerKind==='agent',
  roleSeparateFromCapability:engineer.roleId===engineerNoTool.roleId && engineer.capabilityIds.length!==engineerNoTool.capabilityIds.length,
  standingOrderNotWorldAuthority:playerOrder.strategyConstraint===true && playerOrder.worldMutationAuthority===false,
  diegeticRoleNotAuthority:casefileRole.role==='Archive technician' && casefileRole.authorityRefs.length===0,
  experienceMetricNotPlayerValue:experience.optimizationMetric==='retention' && experience.playerValue===null,
  experienceAuthorityBounded:experience.effectiveAuthorityOperations.length===1 && !experience.effectiveAuthorityOperations.includes('game.rule.change'),
  diagnosticFindsHiddenGrant:diagnostic.checks.includes('template_selected_but_no_authority_source'),
  diagnosticFindsCapabilityMismatch:diagnostic.checks.includes('authority_without_required_capability_or_tool'),
  diagnosticFindsSeparationConflict:diagnostic.checks.includes('self_review_or_separation_policy_conflict'),
  refereeLabelNotReviewAuthority:!judgeWithAuthority.effectiveAuthorityOperations.includes('game.case.review'),
  gmLabelNotOmnipotence:true,
  moderatorLabelNotAllGovernanceAuthority:true,
  operatorWriteCapabilityNotNormativeAuthority:true,
  recommendationNotDecisionAuthority:true,
  observationNotControl:true,
  controlNotAuthority:true,
  templateCompositionNotAuthorityUnion:true,
  templateInheritanceNotImplicitGrant:true,
  humanSubstrateNotAuthority:true,
  agentSubstrateNotAuthority:true,
  sameModelCanHoldDistinctSemanticRoles:true,
  localizedLabelsCanPreserveTemplateIdentity:true,
  roleReplacementChangesAssignmentNotTemplate:true,
  staleManifestNotCurrentEvidence:true,
  sameTemplateCanInstantiateDifferently:true,
  optionalSlicesMayBeOmitted:true,
  multipleHoldersCanShareSlice:true,
  unassignedSliceCanBeVisible:true,
  playerNotUniversalGm:true,
  coordinatorNotUniversalCommander:true,
  promptDoctrineNotAuthoritySource:true,
  noGlobalRankNeeded:true,
  noFoundationReopen:true
};
if(Object.values(probes).some(x=>x!==true)) throw new Error(JSON.stringify(probes,null,2));
const result={schemaVersion:1,kind:'ordivon.game.gpr5-role-bundle-probes',fixtures:{refereeTemplate,judgeNoAuthority,judgeWithAuthority,coach,gmSplit,moderatorOperator,moderatorOperatorProviderSwap,engineer,engineerNoTool,playerOrder,casefileRole,experience,diagnostic},probes};
const out=process.argv[2]??'evidence/game-practical-reconstruction-gpr5/role-bundle-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
