#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/game-practical-reconstruction-gpr1/role-authority-contracts.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/game-practical-reconstruction-gpr1/role-authority-probes.json','utf8'));
const c=matrix.contracts;
const checks={
  foundationsFrozen:Object.values(matrix.foundationStatus).slice(0,4).every(x=>x==='FROZEN') && matrix.foundationStatus.reopenTriggered===false,
  nineMappedConcepts:Object.keys(c).length===9,
  roleAssignmentSource:c.RoleAssignmentRecord.status==='STABILIZE_SOURCE_RECORD',
  authorityEdgeDerived:c.ScopedAuthorityEdge.status==='STABILIZE_NORMALIZED_DERIVED_VIEW',
  openOperationKeys:c.ScopedAuthorityEdge.operationKeyRule.includes('namespaced open operation keys'),
  noScopeTree:c.ScopedAuthorityEdge.scopeRule.includes('No universal scope tree'),
  authorityProfileDerived:c.AuthorityProfile.status==='STABILIZE_DERIVED_VIEW',
  authorityCheckFiveStates:c.AuthorityProfile.checkDisposition.length===5,
  manifestContextBound:c.AgentAuthorityManifest.status==='STABILIZE_CONTEXT_BOUND_DERIVED_SNAPSHOT',
  manifestNotAdmission:c.AgentAuthorityManifest.criticalLaw.includes('GameAction admission'),
  causalProfileMultiAxis:c.RoleCausalAccessProfile.axes.length>=5,
  topologyGraph:c.ParticipationAuthorityTopology.status==='STABILIZE_DERIVED_GRAPH_VIEW',
  separationPolicyNotUniversal:c.AuthoritySeparationPolicy.status==='STABILIZE_POLICY_INTERFACE_NOT_UNIVERSAL_INVARIANT',
  delegationWorkflow:c.DelegationGrantRecord.status==='STABILIZE_CONDITIONAL_SOURCE_WORKFLOW',
  subdelegationExplicit:c.DelegationGrantRecord.admissionRules.some(x=>x.includes('Subdelegation')||x.includes('subdelegation')),
  appointmentCollapsed:c.AppointmentReplacementRecord.status==='RETAIN_AS_CONDITIONAL_ROLE_ASSIGNMENT_CHANGE_RECEIPT',
  fortyStressCases:matrix.stressCases.length>=40,
  engineeringAudit:Object.keys(matrix.currentEngineeringAudit).length>=5,
  currentGrantNotDelegation:matrix.currentEngineeringAudit.AuthorityGrant.classification==='ONE_SHOT_ACTION_AUTHORIZATION_GRANT',
  noBroadImplementation:matrix.implementationDecision.broadImplementationNow===false,
  gpr2Selected:matrix.nextRound.name.startsWith('GPR2'),
  probesPass:Object.values(probes.probes).every(x=>x===true),
  lawAuthorityCapability:matrix.crossCuttingLaws.includes('Authority != Capability'),
  lawAuthorityLegality:matrix.crossCuttingLaws.includes('Authority != ActionLegality'),
  lawNoGlobalRank:matrix.crossCuttingLaws.includes('Authority != GlobalRank'),
  lawDelegationApproval:matrix.crossCuttingLaws.includes('Delegation != OneShotActionApproval'),
  lawDerivedCache:matrix.crossCuttingLaws.includes('DerivedAuthorityCache != independent authority source')
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GPR1 audit failed\n${JSON.stringify(checks,null,2)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gpr1-audit',contractCount:Object.keys(c).length,stressCaseCount:matrix.stressCases.length,lawCount:matrix.crossCuttingLaws.length,probeCount:Object.keys(probes.probes).length,checkCount:Object.keys(checks).length,checks,decision:'GPR1 reconstructs Role & Authority as a practical toolkit: RoleAssignment/Delegation/optional role-change receipts and local policy may be sources; ScopedAuthorityEdge and all profile/manifest/topology surfaces are normalized derived projections. No global authority hierarchy, no authority=capability/legality, no generic Station Zero AuthorityGrant=delegation, and no foundation reopen.'},null,2));
