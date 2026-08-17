#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// Cross-form logical probes: these establish separability/coverage, not empirical Human effects.

const team = {
  teamOutcome:'loss',
  playerA:{roleCriterion:'support-objective',satisfied:true,skillEvidence:'strong'},
  playerB:{roleCriterion:'damage-objective',satisfied:false,skillEvidence:'weak'}
};
team.teamLossDoesNotAssignIndividualFailure = team.teamOutcome==='loss' && team.playerA.satisfied===true;

const sandbox = {
  designerTerminalGoal:false,
  participantCriterion:{kind:'self-authored-build',satisfied:false},
  challengeExists:true,
  authoritativeRecoveryTransitionRequired:false
};
sandbox.challengeWithoutDesignerFailure = !sandbox.designerTerminalGoal && sandbox.challengeExists;
sandbox.recoveryNotUniversal = sandbox.authoritativeRecoveryTransitionRequired===false;

const learning = {
  uncontrollableObservation:{variableControllable:false,informative:true,futurePolicyCanAdapt:true},
  oneShotObservation:{sameInstanceRetry:false,informative:true,futureRelatedProbeAvailable:true},
  weakSignals:{singleSignalDiagnostic:false,multipleSignalsJointlyInformative:true}
};
learning.controllabilityNotNecessary = !learning.uncontrollableObservation.variableControllable && learning.uncontrollableObservation.informative && learning.uncontrollableObservation.futurePolicyCanAdapt;
learning.cheapRetryNotNecessary = !learning.oneShotObservation.sameInstanceRetry && learning.oneShotObservation.informative && learning.oneShotObservation.futureRelatedProbeAvailable;
learning.singleMessageDiagnosticityNotNecessary = !learning.weakSignals.singleSignalDiagnostic && learning.weakSignals.multipleSignalsJointlyInformative;

const masteryCircularity = {
  observedTargetPerformance:[0.95,0.96,0.94],
  regionDefinedAs:'only conditions where target performance >= 0.9',
  independentCriterionProvenance:false,
  heldOutProbe:false
};
masteryCircularity.circularClaimRejected = masteryCircularity.regionDefinedAs.includes('target performance') && !masteryCircularity.independentCriterionProvenance && !masteryCircularity.heldOutProbe;

const masteryHeldOut = {
  criterionProvenance:'community-predeclared category rule',
  developmentRuns:[0.93,0.94],
  heldOutTransformedRuns:[0.91,0.9],
  criterion:0.9
};
masteryHeldOut.nonCircularSupport = masteryHeldOut.heldOutTransformedRuns.every(x=>x>=masteryHeldOut.criterion);

const creative = {
  terminalCompletion:false,
  evaluator:'declared community jury',
  criterionProvenance:true,
  localQualityProbes:[0.88,0.91,0.89],
  threshold:0.85
};
creative.localMasteryWithoutCompletion = !creative.terminalCompletion && creative.criterionProvenance && creative.localQualityProbes.every(x=>x>=creative.threshold);

const recovery = {
  localFailure:true,
  checkpoint:{continuation:true},
  noContinue:{continuation:false}
};
recovery.terminalityDerived = recovery.localFailure && recovery.checkpoint.continuation!==recovery.noContinue.continuation;

const assist = {
  jointPerformance:0.94,
  humanIndependentPostAssist:0.57,
  criterion:0.8
};
assist.attributionRequired = assist.jointPerformance>=assist.criterion && assist.humanIndependentPostAssist<assist.criterion;

const currentness = {
  oldPatch:{rules:'v1',masteryEvidence:0.93},
  newPatch:{rules:'v2',probePerformance:0.58},
  exactProbeTransformationDeclared:true
};
currentness.timelessMasteryRejected = currentness.oldPatch.rules!==currentness.newPatch.rules && currentness.oldPatch.masteryEvidence>=0.9 && currentness.newPatch.probePerformance<0.7;

const synthetic = {
  syntheticPolicy:{criterionPass:true},
  humanEvidence:null
};
synthetic.noHumanInference = synthetic.syntheticPolicy.criterionPass && synthetic.humanEvidence===null;

const result={
  schemaVersion:1,
  kind:'ordivon.game.gdf2-e-integration-probes',
  epistemicBoundary:{
    proves:[
      'team loss does not logically assign individual failure when an individual role criterion can be satisfied',
      'self-authored sandbox challenge can exist without designer terminal goals or recovery transitions',
      'controllability, same-instance retry and single-message diagnosticity are not universal necessary conditions for structural learning-opportunity claims',
      'mastery regions defined only by the target success are circular without independent/held-out validation',
      'bounded expressive mastery can be supported without terminal completion under declared evaluator/criterion provenance',
      'pursuit terminality is derivable from failure scope plus recovery continuation differences in the toy case',
      'joint assisted performance can satisfy a criterion while Human-independent performance does not',
      'patch/currentness changes can invalidate timeless mastery inference',
      'synthetic criterion success does not create Human evidence'
    ],
    doesNotProve:[
      'the three provisional core responsibilities are metaphysical primitives',
      'Human learning from any learning-opportunity structure',
      'a universal social/team attribution model',
      'a universal aesthetic mastery criterion',
      'that all version changes reduce transfer'
    ]
  },
  team,
  sandbox,
  learning,
  masteryCircularity,
  masteryHeldOut,
  creative,
  recovery,
  assist,
  currentness,
  synthetic
};
const output=process.argv[2]??'evidence/gdf2-e/integration-probes.json';
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
