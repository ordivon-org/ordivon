#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const logistic = (skill, demand, sharpness = 3) => 1 / (1 + Math.exp(sharpness * (demand - skill)));
const sensitivity = (fn, skill, delta = 0.05) => Math.abs(fn(skill + delta) - fn(skill - delta)) / (2 * delta);

const cases = {
  lottery: {
    successProbability: 0.10,
    successBySkill: () => 0.10,
    label: 'high adverse-outcome probability, skill-insensitive'
  },
  impossible: {
    successProbability: 0,
    successBySkill: () => 0,
    label: 'structurally infeasible under declared action space'
  },
  trivial: {
    successProbability: 0.99,
    successBySkill: () => 0.99,
    label: 'easy outcome, skill-insensitive'
  },
  frontier: {
    successProbability: logistic(0.5, 0.5),
    successBySkill: (s) => logistic(s, 0.5),
    label: 'skill-matched local frontier'
  },
  overmatchedButPossible: {
    successProbability: logistic(0.2, 0.8),
    successBySkill: (s) => logistic(s, 0.8),
    label: 'low current success but capability-sensitive'
  }
};

for (const value of Object.values(cases)) value.localSkillSensitivity = sensitivity(value.successBySkill, 0.5);

const sameDemandDifferentSkill = {
  demand: 0.6,
  noviceSuccess: logistic(0.25, 0.6),
  expertSuccess: logistic(0.9, 0.6)
};
sameDemandDifferentSkill.materiallyDifferent = Math.abs(sameDemandDifferentSkill.expertSuccess - sameDemandDifferentSkill.noviceSuccess) > 0.4;

const sameSkillDifferentAccess = {
  underlyingSkill: 0.65,
  inaccessibleEffectiveSkill: 0.35,
  accessibleEffectiveSkill: 0.65,
  demand: 0.55
};
sameSkillDifferentAccess.before = logistic(sameSkillDifferentAccess.inaccessibleEffectiveSkill, sameSkillDifferentAccess.demand);
sameSkillDifferentAccess.after = logistic(sameSkillDifferentAccess.accessibleEffectiveSkill, sameSkillDifferentAccess.demand);
sameSkillDifferentAccess.functionalDifficultyChanged = sameSkillDifferentAccess.after > sameSkillDifferentAccess.before;

const failureDissociation = {
  damageTakenButWin: { punishment: true, loss: true, failure: false },
  missedOptionalTargetButFinish: { errorOrLocalFailure: true, terminalFailure: false },
  roguelikeDeathWithMetaProgress: { death: true, runFailure: true, broaderProgressFailure: false },
  speedrunSlowFinish: { completionSuccess: true, targetFailure: true }
};

const learningDissociation = {
  easyBlockedPractice: { immediatePerformance: 0.92, laterRetention: 0.55 },
  harderInterleavedPractice: { immediatePerformance: 0.72, laterRetention: 0.78 }
};
learningDissociation.immediatePerformanceRanksReverseAtRetention =
  learningDissociation.easyBlockedPractice.immediatePerformance > learningDissociation.harderInterleavedPractice.immediatePerformance &&
  learningDissociation.easyBlockedPractice.laterRetention < learningDissociation.harderInterleavedPractice.laterRetention;

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf2-a-challenge-falsifiers',
  epistemicBoundary: {
    proves: [
      'success/failure probability and local skill sensitivity can vary independently in the toy model',
      'structural infeasibility can have zero skill sensitivity',
      'same demand can produce different outcome relations for different SkillProfiles',
      'same SkillProfile can express different functional difficulty under changed access/mapping',
      'failure, punishment, loss, death and completion can be logically dissociated by evaluation scope',
      'immediate practice performance can rank opposite later retention in a constructed desirable-difficulty pattern'
    ],
    doesNotProve: [
      'that local derivative is a complete scientific definition of challenge',
      'human perceived difficulty or flow',
      'player value of failure or challenge',
      'real effect sizes for desirable difficulties',
      'one universal mastery threshold'
    ]
  },
  cases: Object.fromEntries(Object.entries(cases).map(([k,v]) => [k, {successProbability:v.successProbability, localSkillSensitivity:v.localSkillSensitivity, label:v.label}])),
  sameDemandDifferentSkill,
  sameSkillDifferentAccess,
  failureDissociation,
  learningDissociation,
  strongestFalsifiers: {
    lowSuccessDoesNotImplySkillChallenge: cases.lottery.successProbability < 0.2 && cases.lottery.localSkillSensitivity === 0,
    impossibleDoesNotImplyMaximumSkillChallenge: cases.impossible.successProbability === 0 && cases.impossible.localSkillSensitivity === 0,
    frontierCanBeMoreSkillSensitiveThanLowerSuccessCase: cases.frontier.localSkillSensitivity > cases.overmatchedButPossible.localSkillSensitivity,
    sameDemandDifferentFunctionalDifficulty: sameDemandDifferentSkill.materiallyDifferent,
    accessChangesFunctionalDifficultyWithoutChangingUnderlyingSkill: sameSkillDifferentAccess.functionalDifficultyChanged,
    deathNotUniversalFailure: failureDissociation.roguelikeDeathWithMetaProgress.death && !failureDissociation.roguelikeDeathWithMetaProgress.broaderProgressFailure,
    immediateDifficultyNotLearningValue: learningDissociation.immediatePerformanceRanksReverseAtRetention
  }
};

const output = process.argv[2] ?? 'evidence/gdf2-a/challenge-falsifiers.json';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
