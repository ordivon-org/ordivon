#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf3-e/consolidated-minimality-matrix.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf3-e/minimality-probes.json','utf8'));
const f=probes.falsifiers;
const independent=matrix.fieldDeletionTests.filter(x=>x.survivesAsIndependentField).map(x=>x.field);
const checks={
 eightStartingFields:matrix.startingContract.length===8,
 thirtySixCases:matrix.crossRegimeCases.length>=36,
 onlyDeterminationCoreFieldIndependent:independent.length===1&&independent[0]==='AuthoritativeDetermination',
 targetCompressedNotDeleted:matrix.fieldDeletionTests.find(x=>x.field==='CaseTargetOrDecisionQuestion').verdict.includes('DETERMINATION_RELATION_TARGET'),
 basesMergedTyped:matrix.fieldDeletionTests.filter(x=>['CaseBasis','NormApplicationBasis'].includes(x.field)).every(x=>x.verdict==='MERGE_INTO_TYPED_DETERMINATION_BASIS'),
 authorityUsesF6:matrix.fieldDeletionTests.find(x=>x.field==='DecisionAuthority').verdict==='COMPRESS_TO_F6_BINDING_AUTHORITY_RELATION',
 lineageDerived:matrix.fieldDeletionTests.find(x=>x.field==='DecisionLineageOrReview').verdict==='DERIVED_OPTIONAL_VIEW',
 consequenceHandedBack:matrix.fieldDeletionTests.find(x=>x.field==='ConsequenceOrEnforcementRelation').verdict==='HAND_BACK_TO_GDF0_GDF1_F4',
 ordinaryExecutionBoundary:f.ordinaryExecutionNeedNotAdjudicate,
 independentCaseStatus:f.caseStatusCanVaryWithoutHistoryChange,
 typedBasis:f.caseBasisAndNormBasisTypesMatter,
 classificationSeparation:f.classificationNotDetermination,
 authorityBinding:f.authorityRequiredForBinding,
 targetSemantic:f.targetRequiredSemantically,
 rulingEnforcement:f.determinationNotEnforcement,
 lineageDerivable:f.lineageCanRemainDerived,
 reversalHistory:f.reversalNotHistoryErase,
 consequenceExternal:f.consequenceNeedNotBeCore,
 agentAuthority:f.sameAgentDoesNotCollapseAuthority,
 substrateNeutral:f.substrateNeutral,
 minimumThreeObligations:matrix.minimalContract.minimumObligations.length===3,
 freezeReady:matrix.freezeReadiness.readyForFreezeConstruction===true,
 notSilentlyFrozen:matrix.freezeReadiness.freezeNow===false,
 noNewPrimitive:matrix.freezeReadiness.newPrimitiveRequired===false,
 noReopen:Object.values(matrix.foundationReopen).every(x=>x===false)
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GDF3-E audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf3-e-audit',startingFieldCount:matrix.startingContract.length,crossRegimeCaseCount:matrix.crossRegimeCases.length,checkCount:Object.keys(checks).length,checks,strongestConclusion:'The eight-part AdjudicationCaseContract overfit collapses to a minimal AuthoritativeCaseDeterminationContract with three obligations: determination target/status, F5/F6 binding authority/currentness/provenance, and typed determination-basis links when case/evidence basis and norm/evaluation basis can vary independently. Review lineage is derived; enforcement is external; ordinary deterministic execution need not be adjudication. The responsibility survives as a Game-owned anti-collapse contract over F1-F9, not as a new primitive, and is ready for a separate final freeze/falsification round.'},null,2));
