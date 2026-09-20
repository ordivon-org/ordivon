#!/usr/bin/env node
import fs from 'node:fs';
const survival=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf2-f/final-survival-table.json','utf8'));
const handoff=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf2-f/downstream-handoff-map.json','utf8'));
const probes=JSON.parse(fs.readFileSync(process.argv[4]??'evidence/gdf2-f/freeze-probes.json','utf8'));
const core=survival.coreResponsibilities.map(x=>x.name);
const expected=['ChallengeAssessmentContract','FailureRecoveryContract','MasteryClaimContract'];
const forbiddenCore=['CapabilityOutcomeSurface','RecoveryTransitionSet','LearningOpportunityProfile','PursuitTerminalityClaim','DifficultyScalar','MasteredBoolean','OpponentInteractionSurface'];
const checks={
  freezeVerdict:survival.freezeVerdict==='freeze-v1',
  exactlyThreeCore:core.length===3&&expected.every(x=>core.includes(x)),
  noForbiddenCore:forbiddenCore.every(x=>!core.includes(x)),
  enoughFrozenGuards:survival.freezeGuards.length>=18,
  eightReopenConditions:survival.reopenConditions.length===8&&survival.reopenConditions.every((x,i)=>x.id===`CFM-PRC-${i+1}`),
  noUpstreamReopen:Object.values(survival.foundationAudit).filter(x=>typeof x==='boolean').every(x=>x===false),
  nextBranchUnresolvedByDesign:handoff.nextBranch==='UNRESOLVED_BY_DESIGN'&&handoff.selectionPolicy?.knownHandoffsArePriorityOrdered===false&&handoff.selectionPolicy?.mustSearchBeyondKnownHandoffs===true,
  downstreamCoverage:['GDF3 Game Feel / Feedback / Sensorimotor Coupling','GDF4 Time / Rhythm / Pacing','GDF5 Space / Level / Navigation','GDF6 Strategy / Counterplay / Balance','Human','Practice/Social/Institution'].every(owner=>handoff.handoffs.some(x=>x.owner===owner)),
  allFreezeProbes:Object.values(probes.checks).every(Boolean),
  noveltyConservative:survival.novelty.N2.length===0&&survival.novelty.N3.length===0
};
if(Object.values(checks).some(x=>!x)) throw new Error(`GDF2-F freeze audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf2-f-freeze-audit',coreResponsibilities:core,freezeGuardCount:survival.freezeGuards.length,derivedViewCount:survival.derivedViews.length,handoffCount:survival.handoffs.length,retiredCount:survival.retired.length,reopenConditionCount:survival.reopenConditions.length,checks,strongestConclusion:'GDF2 freezes three non-ontological Game responsibility/query contracts: challenge assessment is scoped and non-scalar; failure is evaluation-relative with optional recovery transitions separate from terminality/severity; mastery is an independently anchored scoped inference over SkillProfile. All response-surface, recovery, identifiability and learning-opportunity structures remain derived or owner-specific.'},null,2));
