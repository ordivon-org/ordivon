#!/usr/bin/env node
import fs from 'node:fs';
const matrix=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/gdf2-e/cross-gameform-matrix.json','utf8'));
const audit=JSON.parse(fs.readFileSync(process.argv[3]??'evidence/gdf2-e/survival-audit.json','utf8'));
const p=JSON.parse(fs.readFileSync(process.argv[4]??'evidence/gdf2-e/integration-probes.json','utf8'));
const core=new Set(audit.provisionalCoreResponsibilities.map(x=>x.name));
const requiredCore=['ChallengeAssessmentContract','FailureRecoveryContract','MasteryClaimContract'];
for(const x of requiredCore) if(!core.has(x)) throw new Error(`missing core responsibility ${x}`);
const statusCounts=audit.dispositions.reduce((m,x)=>(m[x.status]=(m[x.status]??0)+1,m),{});
const checks={
  enoughGameForms:matrix.gameForms.length>=12,
  onlyThreeProvisionalCore:audit.provisionalCoreResponsibilities.length===3,
  candidateCountMatches:audit.dispositions.length===audit.compression.candidateCount,
  retireLearningProfile:audit.dispositions.some(x=>x.candidate==='LearningOpportunityProfile'&&x.status==='retire'),
  terminalityDemoted:audit.dispositions.some(x=>x.candidate==='PursuitTerminalityClaim'&&x.status==='derived-model'),
  opponentHandedOff:audit.dispositions.some(x=>x.candidate==='OpponentInteractionSurface'&&x.status==='handoff'),
  teamAttributionGuard:p.team.teamLossDoesNotAssignIndividualFailure,
  sandboxNoUniversalFailureRecovery:p.sandbox.challengeWithoutDesignerFailure&&p.sandbox.recoveryNotUniversal,
  learningProfileOverbreadth:p.learning.controllabilityNotNecessary&&p.learning.cheapRetryNotNecessary&&p.learning.singleMessageDiagnosticityNotNecessary,
  masteryCircularityRejected:p.masteryCircularity.circularClaimRejected&&p.masteryHeldOut.nonCircularSupport,
  openEndedMastery:p.creative.localMasteryWithoutCompletion,
  terminalityDerived:p.recovery.terminalityDerived,
  assistAttribution:p.assist.attributionRequired,
  currentnessBound:p.currentness.timelessMasteryRejected,
  syntheticBoundary:p.synthetic.noHumanInference,
  noFoundationReopen:Object.values(matrix.foundationReopen).filter(x=>typeof x==='boolean').every(x=>x===false)&&Object.values(audit.foundationReopen).filter(x=>typeof x==='boolean').every(x=>x===false)
};
if(Object.values(checks).some(x=>!x)) throw new Error(`E audit failed ${JSON.stringify(checks)}`);
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.gdf2-e-integration-audit',gameFormCount:matrix.gameForms.length,candidateCount:audit.dispositions.length,provisionalCoreResponsibilities:[...core],statusCounts,checks,strongestConclusion:'Cross-GameForm pressure compresses GDF2 to three provisional responsibilities: challenge assessment is relational/scoped and non-scalar; failure is evaluation-relative with recovery transitions kept separate from terminality/severity; mastery is a scoped SkillProfile evidence claim. LearningOpportunityProfile and PursuitTerminalityClaim do not survive as independent core constructs, and detailed opponent/social/Human experience mechanisms hand off.'},null,2));
