#!/usr/bin/env node
import fs from 'node:fs';

const model = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf3-b/authority-decomposition.json', 'utf8'));
const probes = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf3-b/authority-topology-probes.json', 'utf8'));
const f = probes.strongestFalsifiers;
const checks = {
  enoughBoundaryCases: model.boundaryCases.length >= 18,
  finalAuthorityNotScalar: f.finalAuthorityNotGlobalScalar === true,
  recommendationSeparated: f.recommendationNotFinalAuthority === true,
  replacementCurrentness: f.roleOccupantCanChangeByCondition === true,
  reviewSeparated: f.reviewAuthorityNotFirstInstanceAuthority === true,
  appointmentSeparated: f.appointmentAuthorityNotAdjudicationAuthority === true,
  adviceSeparated: f.adviceNotActionAuthority === true,
  aggregationSeparated: f.aggregateEffectNotMemberAuthority === true,
  adaptiveAuthoritySeparated: f.adaptiveGameAuthorityNotPlayerAuthority === true,
  entityAuthoritySeparated: f.entityIdentityNotAuthorityIdentity === true,
  scopeConditionRequired: f.authorityRequiresScopeConditionCurrentness === true,
  ruleVsCaseSeparated: f.ruleChangeAuthorityNotCaseRulingAuthority === true,
  rulingVsEnforcementSeparated: f.rulingNotEnforcement === true,
  verificationHistorySeparated: f.verificationNotWorldHistoryRewrite === true,
  topologyCompressed: model.compressionResults.ParticipationAuthorityTopology === 'COMPRESS_TO_DERIVED_PROJECTION',
  noIndependentResponsibility: model.selection.participationAuthorityTopologyIndependentResponsibility === false,
  adjudicationSurvives: model.compressionResults.AdjudicationProcessFamily === 'RETAIN_FOR_GDF3_C',
  noFoundationReopen: Object.values(model.foundationReopen).every((x) => x === false)
};
if (Object.values(checks).some((x) => !x)) throw new Error(`GDF3-B audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({
  schemaVersion:1,
  kind:'ordivon.game.gdf3-b-audit',
  boundaryCaseCount:model.boundaryCases.length,
  authorityEdgeFieldCount:model.candidateAuthorityEdgeFields.length,
  testedOperationCount:model.operationsUnderTest.length,
  checks,
  strongestConclusion:'ParticipationAuthorityTopology does not survive as an independent foundation responsibility. The tested cases compress into scope/time/operation-bound authority relations plus contribution/action semantics. Global authority rank, delegation/aggregation/role-conflict primitives are rejected. Adjudication/interpretation/review/contestability remains the irreducible next residual.'
}, null, 2));
