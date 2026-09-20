#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf3-d/norm-application-matrix.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf3-d/norm-application-probes.json','utf8'));
const f=probes.strongestFalsifiers;
const checks={
  enoughTerms:matrix.termSeparations.length>=14,
  enoughCases:matrix.boundaryCases.length>=36,
  closedModelPresent:matrix.zeroModel.name==='ClosedNormApplication',
  closedNotUniversal:f.closedRuleModelNotUniversal===true,
  exceptionCompressed:f.exceptionNotPrimitive===true,
  conflictCurrentness:f.conflictResolutionCurrentnessMatters===true,
  purposeBounded:f.purposeNotUnboundedMetaRule===true,
  noRuleStandardBinary:f.ruleStandardNotOntologicalBinary===true,
  precedentNotIdentity:f.priorDecisionNotBindingPrecedent===true,
  conventionNotFrequency:f.conventionFrequencyNotAuthority===true,
  interpretationCanAlterEffectiveRules:f.adoptedInterpretationCanChangeEffectiveRules===true,
  discretionBounded:f.discretionNotArbitrariness===true,
  ruleVsInterpretiveChangeSeparated:f.ruleChangeNotInterpretiveChange===true,
  retroactivityNotHistoryRewrite:f.retroactivityNotHistoryRewrite===true,
  rulingNotPrecedent:f.rulingNotPrecedentByIdentity===true,
  caseNotLegislativeAuthority:f.caseAuthorityNotLegislativeAuthority===true,
  agentIdentityNotAuthority:f.modelIdentityNotInterpretiveAuthority===true,
  consistencyNotIdentity:f.consistencyNotIdenticalOutcome===true,
  normApplicationNotIndependent:matrix.compressionResults.NormApplicationIndependentResponsibility==='REJECT',
  normSubviewRetained:matrix.compressionResults.NormApplicationBasis==='RETAIN_AS_DERIVED_SUBVIEW_OF_ADJUDICATION_CASE_CONTRACT',
  gdf0AbsorbsAdoptedInterpretation:matrix.gdf0Consumption.effectiveRuleTopologyAbsorbs.length>=5,
  adjudicationRefined:matrix.selection.adjudicationCaseContractRefined===true,
  noNewPrimitive:matrix.selection.newSemanticPrimitiveRequired===false,
  noFoundationReopen:Object.values(matrix.foundationReopen).every((x)=>x===false)
};
if(Object.values(checks).some((x)=>!x)) throw new Error(`GDF3-D audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf3-d-audit',termCount:matrix.termSeparations.length,boundaryCaseCount:matrix.boundaryCases.length,checkCount:Object.keys(checks).length,checks,strongestConclusion:'Norm Application does not survive as a second independent GDF3 responsibility. Rules, standards, purpose/ethos, exceptions, norm conflicts, precedents, conventions, discretion, open texture, interpretive change and retroactivity compress into GDF0 EffectiveRuleTopology plus ordinary scope/currentness/authority relations and a derived NormApplicationBasis subview inside AdjudicationCaseContract. An authoritative adopted interpretation that changes Game semantics is itself part of current EffectiveRuleTopology even without a text change; provenance still distinguishes interpretation change from rule representation change.'},null,2));
