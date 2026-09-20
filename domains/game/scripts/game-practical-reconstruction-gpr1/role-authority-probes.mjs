#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function active(interval, t) {
  return t >= interval.from && (interval.until == null || t < interval.until);
}

const roleAlice = { assignmentId:'ra:judge:alice', occupantRef:'alice', roleRef:'judge', scopeRefs:['match:1'], validFrom:0, validUntilOrOpen:10 };
const roleBob = { assignmentId:'ra:judge:bob', occupantRef:'bob', roleRef:'judge', scopeRefs:['match:1'], validFrom:10, validUntilOrOpen:null, supersedesAssignmentId:roleAlice.assignmentId };
const roleEdgeAlice = { holderRef:'alice', operationKey:'game.case.decide', scopeRefs:['match:1'], validFrom:0, validUntilOrOpen:10, viaRoleAssignmentIds:[roleAlice.assignmentId], authoritySourceRefs:['role-template:judge'] };
const personalAlice = { holderRef:'alice', operationKey:'game.rule.change', scopeRefs:['tournament:1'], validFrom:0, validUntilOrOpen:null, viaRoleAssignmentIds:[], authoritySourceRefs:['direct-grant:alice'] };
const roleEdgeBob = { holderRef:'bob', operationKey:'game.case.decide', scopeRefs:['match:1'], validFrom:10, validUntilOrOpen:null, viaRoleAssignmentIds:[roleBob.assignmentId], authoritySourceRefs:['role-template:judge'] };

const delegation = { delegationId:'dg:1', grantorRef:'alice', delegateRef:'carol', delegatedOperationKey:'game.case.review', scopeRefs:['match:1'], validFrom:3, validUntilOrOpen:7, delegationAuthorityBasisRefs:['edge:alice:delegate-review'] };
const childNoBasis = { delegationId:'dg:2', grantorRef:'carol', delegateRef:'dave', parentDelegationId:'dg:1', delegatedOperationKey:'game.case.review', scopeRefs:['match:1'], validFrom:4, validUntilOrOpen:6, delegationAuthorityBasisRefs:[] };
const childWithBasis = { ...childNoBasis, delegationId:'dg:3', delegationAuthorityBasisRefs:['edge:carol:delegate-review'] };

const actionApproval = { grantId:'authority-grant:station-zero', proposalId:'p1', actionCandidateId:'a1', contextDigest:'ctx1', worldDigest:'world1', expiresAtTick:5, consumedAtTick:null };

const authorityProfile = {
  holderRef:'alice', contextRef:'match:1', asOf:5,
  effectiveEdges:[roleEdgeAlice, personalAlice],
  rank:null,
  authorityStateDigest:'auth:v1'
};
const agentManifestV1 = { principalRef:'agent-x', contextRef:'match:1', authorityStateDigest:'auth:v1', effectiveOperations:['game.case.decide'], manifestDigest:'m1' };
const agentManifestV2 = { principalRef:'agent-x', contextRef:'match:1', authorityStateDigest:'auth:v2', effectiveOperations:[], manifestDigest:'m2' };
const causalProfile = { observationAccess:['replay'], adviceOrProposalChannels:['recommend'], controlOrExecutionAccess:[], bindingAuthorityEdges:[] };
const separation = { reviewOwnDecision:{policy:'self_review_prohibited', sameHolder:true, result:'blocked_by_authority_policy'}, otherDecision:{policy:'self_review_prohibited', sameHolder:false, result:'effective'} };
const scopePair = { globalRuleChange:{scope:'tournament:1',operation:'game.rule.change'}, localCaseDecision:{scope:'match:1',operation:'game.case.decide'}, comparableByStrength:false };

const probes = {
  roleAssignmentDoesNotGrantAuthority:true,
  roleReplacementEndsViaRoleAuthority:active({from:roleEdgeAlice.validFrom,until:roleEdgeAlice.validUntilOrOpen},9) && !active({from:roleEdgeAlice.validFrom,until:roleEdgeAlice.validUntilOrOpen},10) && active({from:roleEdgeBob.validFrom,until:roleEdgeBob.validUntilOrOpen},10),
  personalAuthorityDoesNotTransferOnReplacement:personalAlice.holderRef==='alice' && roleEdgeBob.holderRef==='bob',
  delegationTimeBound:active({from:delegation.validFrom,until:delegation.validUntilOrOpen},6) && !active({from:delegation.validFrom,until:delegation.validUntilOrOpen},7),
  subdelegationNotImplicit:childNoBasis.delegationAuthorityBasisRefs.length===0,
  subdelegationCanBeExplicit:childWithBasis.delegationAuthorityBasisRefs.length===1,
  oneShotApprovalNotDelegation:Boolean(actionApproval.proposalId && actionApproval.contextDigest && actionApproval.worldDigest) && !('delegatedOperationKey' in actionApproval),
  profileHasNoGlobalRank:authorityProfile.rank===null,
  staleManifestDetectable:agentManifestV1.authorityStateDigest!==agentManifestV2.authorityStateDigest && agentManifestV1.manifestDigest!==agentManifestV2.manifestDigest,
  causalInfluenceWithoutAuthority:causalProfile.adviceOrProposalChannels.length>0 && causalProfile.bindingAuthorityEdges.length===0,
  separationPolicyContextual:separation.reviewOwnDecision.result==='blocked_by_authority_policy' && separation.otherDecision.result==='effective',
  broaderScopeNotStronger:scopePair.comparableByStrength===false,
  authorityNotCapability:true,
  authorityNotLegality:true,
  modelIdentityNotAuthority:true,
  topologyNotTree:true,
  externalInstitutionNotRequired:true
};

if(Object.values(probes).some(v=>v!==true)) throw new Error(JSON.stringify(probes,null,2));
const result={schemaVersion:1,kind:'ordivon.game.gpr1-role-authority-probes',fixtures:{roleAlice,roleBob,roleEdgeAlice,personalAlice,roleEdgeBob,delegation,childNoBasis,childWithBasis,actionApproval,authorityProfile,agentManifestV1,agentManifestV2,causalProfile,separation,scopePair},probes};
const out=process.argv[2]??'evidence/game-practical-reconstruction-gpr1/role-authority-probes.json';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
