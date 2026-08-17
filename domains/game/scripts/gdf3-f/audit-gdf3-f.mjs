#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf3-f/final-falsification-matrix.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf3-f/final-freeze-probes.json','utf8'));
const f=probes.falsifiers;
const positive=matrix.boundaryCases.filter(x=>x.expected).length;
const negative=matrix.boundaryCases.filter(x=>!x.expected).length;
const checks={
 threeObligations:matrix.candidate.obligations.length===3,
 noOntologyPrimitive:matrix.candidate.ontologyPrimitive===false,
 tenAttackQuestions:matrix.finalAttackQuestions.length===10,
 totalCompressionRepresentationPasses:matrix.totalCompressionAttack.representationResult==='PASS',
 totalCompressionResponsibilityFails:matrix.totalCompressionAttack.responsibilityResult==='FAIL',
 fortyEightBoundaryCases:matrix.boundaryCases.length>=48,
 positiveAndNegativeCoverage:positive>=20&&negative>=20,
 targetSurvives:f.targetStatusCannotDisappear===true,
 bindingSurvives:f.bindingCannotComeFromContent===true,
 operationAuthority:f.authorityMustBeOperationSpecific===true,
 basisTyping:f.basisTypingCounterfactual===true,
 deterministicBoundary:f.deterministicAlgorithmDoesNotDecideBoundary===true,
 solitaryBoundary:f.externalInstitutionNotRequired===true,
 lineageDerived:f.lineageRemainsDerived===true,
 enforcementExternal:f.enforcementNotCore===true,
 fusedImplementation:f.fusedImplementationDoesNotEraseSeparation===true,
 substrateNeutral:f.substrateNeutral===true,
 statusNotTruth:f.officialStatusNotWorldTruth===true,
 lineageMatrix:matrix.lineageAttack.result==='DERIVED_VIEW_SUFFICIENT'&&!matrix.lineageAttack.newPrimitiveRequired,
 enforcementMatrix:matrix.enforcementAttack.result==='CORE_OBLIGATION_NOT_REQUIRED'&&!matrix.enforcementAttack.newPrimitiveRequired,
 solitaryMatrix:matrix.solitarySelfAuthoredAttack.result==='SURVIVES',
 agentMatrix:matrix.roleFusedAgentAttack.result==='SURVIVES',
 nineReopenConditions:matrix.foundationReopenConditions.length===9,
 freezeSelected:matrix.freezeDecision.gdf3Freeze===true,
 noNewPrimitive:matrix.freezeDecision.newSemanticPrimitiveRequired===false,
 noUpstreamReopen:Object.values(matrix.upstreamReopen).every(x=>x===false),
 noPresetNext:matrix.postFreezeContinuation.nextBranchPreset===false
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GDF3-F audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf3-f-audit',boundaryCaseCount:matrix.boundaryCases.length,positiveBoundaryCases:positive,negativeBoundaryCases:negative,reopenConditionCount:matrix.foundationReopenConditions.length,checkCount:Object.keys(checks).length,checks,freezeDecision:'FREEZE GDF3 as Authoritative Case Determination Foundations v1. The frozen item is a three-obligation Game-owned responsibility contract over F1-F9, not a new primitive. Ordinary deterministic execution remains outside the boundary unless an independently meaningful binding case status exists. Solitary/self-authored and Human/Agent role-fused regimes do not falsify the authority model. Review lineage stays derived; enforcement stays external. After freeze, no next branch is preselected: rerun whole-Game domain coverage.'},null,2));
