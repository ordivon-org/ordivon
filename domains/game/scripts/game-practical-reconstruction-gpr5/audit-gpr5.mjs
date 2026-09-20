#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/game-practical-reconstruction-gpr5/role-bundle-template-contracts.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/game-practical-reconstruction-gpr5/role-bundle-probes.json','utf8'));
const c=matrix.contracts;
const t=matrix.templateLibrary;
const checks={
  foundationsFrozen:Object.values(matrix.foundationStatus).slice(0,4).every(x=>x==='FROZEN') && matrix.foundationStatus.reopenTriggered===false,
  fiveContracts:Object.keys(c).length===5,
  sixTemplateFamilies:Object.keys(t).length===6,
  templateOptional:c.RoleBundleTemplateDefinition.status==='STABILIZE_OPTIONAL_AUTHORING_PRESET',
  noHiddenGrants:c.RoleBundleTemplateDefinition.defaultAdmissionPolicy.startsWith('NO_HIDDEN_GRANTS'),
  planDerived:c.RoleBundleInstantiationPlan.status==='STABILIZE_DERIVED_AUTHORING_PLAN',
  manifestDerived:c.RoleBundleManifest.status==='STABILIZE_DERIVED_CURRENT_HUMAN_AGENT_VIEW',
  compositionDerived:c.RoleBundleCompositionView.status==='STABILIZE_DERIVED_COMPOSITION_VIEW',
  diagnosticDerived:c.RoleBundleCompatibilityDiagnostic.status==='STABILIZE_DERIVED_AUTHORING_AUDIT',
  diagnosticHiddenGrant:c.RoleBundleCompatibilityDiagnostic.checks.includes('template_selected_but_no_authority_source'),
  refereeFamily:t.RefereeJudge.status==='STABILIZE_TEMPLATE_FAMILY',
  gmFamily:t.GameMaster.status==='STABILIZE_TEMPLATE_FAMILY',
  coachFamily:t.CoachAdvisor.status==='STABILIZE_TEMPLATE_FAMILY',
  moderatorFamily:t.Moderator.status==='STABILIZE_TEMPLATE_FAMILY',
  operatorFamily:t.Operator.status==='STABILIZE_TEMPLATE_FAMILY',
  experienceFamily:t.ExperienceManager.status==='STABILIZE_TEMPLATE_FAMILY',
  refereeNoHiddenCase:t.RefereeJudge.strongGuards.includes('RefereeLabel != CaseAuthority'),
  gmNoOmnipotence:t.GameMaster.strongGuards.includes('GMLabel != Omnipotence'),
  coachNoControl:t.CoachAdvisor.strongGuards.includes('Coach != Controller'),
  moderatorNoAllPower:t.Moderator.strongGuards.includes('ModeratorLabel != AllGovernanceAuthority'),
  operatorNoAdmin:t.Operator.strongGuards.includes('OperatorLabel != GlobalAdminByIdentity'),
  experienceBounded:t.ExperienceManager.strongGuards.includes('ExperienceManager != OmniscientPlayerModel'),
  seventyCases:matrix.stressCases.length>=70,
  nineEngineeringFindings:Object.keys(matrix.currentEngineeringAudit).length>=9,
  teamRoleLocal:matrix.currentEngineeringAudit.TeamActorRole.classification==='LOCAL_SPECIALIST_DOCTRINE_OBJECTIVE_PROFILE',
  coordinatorLocal:matrix.currentEngineeringAudit.TeamCoordinatorRole.classification==='LOCAL_ORCHESTRATION_TASK_ROLE',
  controllerSeparate:matrix.currentEngineeringAudit.StationZeroControllerKind.classification==='CONTROL_LOCUS_OR_REALIZATION_SUBSTRATE_NOT_ROLE',
  standingOrderSeparate:matrix.currentEngineeringAudit.StationZeroStandingOrder.classification==='STRATEGIC_INSTRUCTION_CONSTRAINT_NOT_DIRECT_WORLD_AUTHORITY',
  casefileDiegetic:matrix.currentEngineeringAudit.CasefilePersonRole.classification==='DIEGETIC_PRESENTATION_OCCUPATION_LABEL',
  localPatternProven:matrix.implementationDecision.currentPatternValue==='PROVEN_LOCAL_ROLE_TEMPLATE_VALUE',
  genericNeedNotProven:matrix.implementationDecision.currentGenericFrameworkNeed==='NOT_YET_PROVEN',
  noBroadImplementation:matrix.implementationDecision.broadImplementationNow===false,
  gpr6Selected:matrix.nextRound.name.startsWith('GPR6'),
  probesPass:Object.values(probes.probes).every(x=>x===true),
  lawTemplateGrant:matrix.crossCuttingLaws.includes('RoleBundleTemplate != AuthorityGrant'),
  lawComposition:matrix.crossCuttingLaws.includes('TemplateComposition != AuthorityUnion'),
  lawProvider:matrix.crossCuttingLaws.includes('ProviderIdentity != RoleAuthority'),
  lawObservation:matrix.crossCuttingLaws.includes('ObservationAccess != Control'),
  lawWrite:matrix.crossCuttingLaws.includes('WriteCapability != NormativeAuthority'),
  lawSameLabel:matrix.crossCuttingLaws.includes('SameDisplayLabelCanMapToDifferentLocalBundles'),
  lawStale:matrix.crossCuttingLaws.includes('StaleRoleBundleManifest != CurrentAuthorityEvidence')
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GPR5 audit failed\n${JSON.stringify(checks,null,2)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gpr5-audit',contractCount:Object.keys(c).length,templateFamilyCount:Object.keys(t).length,stressCaseCount:matrix.stressCases.length,lawCount:matrix.crossCuttingLaws.length,probeCount:Object.keys(probes.probes).length,checkCount:Object.keys(checks).length,checks,decision:'GPR5 reconstructs familiar roles as optional authoring/template families with no hidden grants. Concrete manifests derive from actual RoleAssignment, access, capability, control and GPR1-GPR4 authority sources. Current Station Zero proves local role-template value but not a generic framework implementation need.'},null,2));
