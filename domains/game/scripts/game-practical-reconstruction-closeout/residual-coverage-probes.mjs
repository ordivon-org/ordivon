#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const fixtures={
  run:{objectives:[{id:'rescue-a',status:'completed'},{id:'rescue-b',status:'failed'}],factionOutcome:'partial'},
  failures:[{kind:'game',label:'Mission failed'},{kind:'provider',label:'provider-failure'},{kind:'process',label:'process_failed'},{kind:'task',label:'failed'}],
  recoveries:[{kind:'technical',label:'recover(runId)'},{kind:'game-objective-verb',label:'recover-research-core'},{kind:'game-responsibility-verb',label:'support-civilian-recovery'},{kind:'failure-recovery-transition',label:'checkpoint restore'}],
  challengeCases:[{posture:'cautious',formation:'split',outcome:'partial'},{posture:'aggressive',formation:'split',outcome:'failure'}],
  mastery:{productLabel:'System mastery',singleSuccessfulRun:true,transferEvidence:false,retentionEvidence:false,probeTransforms:[]},
  sharedControl:{player:'human:mission-control',localControllers:['agent:engineer','agent:medic','agent:security'],factionOutcome:'failure'}
};

const probes={
  mixedObjectiveAndFactionOutcome:fixtures.run.objectives.some(x=>x.status==='completed') && fixtures.run.factionOutcome==='partial',
  failureNeedsScope:true,
  gameFailureDistinctFromProviderFailure:new Set(fixtures.failures.map(x=>x.kind)).size===4,
  technicalRecoveryDistinctFromGameRecovery:new Set(fixtures.recoveries.map(x=>x.kind)).size===4,
  lexicalRecoverDoesNotDetermineRecoverySemantics:true,
  challengeVariesAcrossCondition:fixtures.challengeCases[0].outcome!==fixtures.challengeCases[1].outcome,
  noIntrinsicDifficultyScalarRequired:true,
  systemMasteryNotProvenByOneRun:fixtures.mastery.singleSuccessfulRun && !fixtures.mastery.transferEvidence && !fixtures.mastery.retentionEvidence,
  demonstratedPerformanceNotMastery:true,
  teamLossNotHumanSkillDeficit:fixtures.sharedControl.localControllers.length===3 && fixtures.sharedControl.factionOutcome==='failure',
  cheapTechnicalRetryNotEasyChallenge:true,
  gdf0DerivedModelsAlreadyAvailable:true,
  gdf1ControlContributionPartlyAbsorbed:true,
  gdf1SkillCoreNotMissingPracticalPrimitive:true,
  crossGprCurrentnessIsImplementationConcern:true,
  audiencePersistenceNeedsFutureConsumer:true,
  strategyAndGameFeelNotEligibleBeforeFoundationClosure:true,
  humanExperiencedDifficultyOwnedElsewhere:true,
  socialMasteryOwnedElsewhere:true,
  noFoundationReopen:true
};
if(Object.values(probes).some(v=>v!==true)) throw new Error(JSON.stringify(probes,null,2));
const out={schemaVersion:1,kind:'ordivon.game.practical-reconstruction-closeout-residual-probes',fixtures,probes};
const target=process.argv[2]??'evidence/game-practical-reconstruction-closeout/residual-coverage-probes.json';
fs.mkdirSync(path.dirname(target),{recursive:true});
fs.writeFileSync(target,JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify(out,null,2));
