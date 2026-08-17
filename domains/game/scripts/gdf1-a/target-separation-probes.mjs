#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

// Research-only structural probes. These are semantic counterexamples under declared mappings,
// not empirical motor-control evidence.

const contexts = {
  gameplay: { A: 'JUMP', X: 'ATTACK' },
  menu: { A: 'CONFIRM', X: 'CANCEL' },
};

const sameInputDifferentAction = {
  input: 'A',
  gameplayAction: contexts.gameplay.A,
  menuAction: contexts.menu.A,
  separated: contexts.gameplay.A !== contexts.menu.A,
};

const remappedControllers = [
  { controller: 'keyboard', physicalExpression: 'right-index-keypress', signal: 'BUTTON_A', action: 'JUMP' },
  { controller: 'adaptive-grip', physicalExpression: 'grip-contraction', signal: 'BUTTON_A', action: 'JUMP' },
  { controller: 'voice-adapter', physicalExpression: 'spoken-jump', signal: 'BUTTON_A', action: 'JUMP' },
];
const sameActionDifferentMovement = {
  uniquePhysicalExpressions: new Set(remappedControllers.map((x) => x.physicalExpression)).size,
  uniqueActions: new Set(remappedControllers.map((x) => x.action)).size,
  separated: new Set(remappedControllers.map((x) => x.physicalExpression)).size > 1 && new Set(remappedControllers.map((x) => x.action)).size === 1,
};

const goalEquivalentTrajectories = [
  { name: 'smooth', endpointError: 0, pathLength: 10, peakDeviation: 0.5 },
  { name: 'curved', endpointError: 0, pathLength: 13, peakDeviation: 2.2 },
  { name: 'corrected', endpointError: 0, pathLength: 15, peakDeviation: 3.4 },
];
const goalEquivalent = {
  exactTrajectoriesEqual: false,
  identicalTaskOutcome: goalEquivalentTrajectories.every((x) => x.endpointError === 0),
  conclusion: 'ExactMovementRepetition is not required for equal task-level outcome under this toy task definition.',
};

const controllers = {
  nominalSpecialist: {
    nominal: [10, 10, 10, 10],
    perturbation: [2, 2, 2, 2],
  },
  robustController: {
    nominal: [9, 9, 9, 9],
    perturbation: [8, 8, 8, 8],
  },
};
const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
const robustness = Object.fromEntries(Object.entries(controllers).map(([k, v]) => [k, {
  nominalMean: mean(v.nominal),
  perturbationMean: mean(v.perturbation),
  crossConditionMean: mean([...v.nominal, ...v.perturbation]),
} ]));

const actionAttempt = { intent: 'DASH_EAST', inputAdmitted: true, stamina: 0, legalIfStamina: true };
const attemptVsExecution = {
  attemptExists: actionAttempt.inputAdmitted,
  executed: actionAttempt.stamina > 0 && actionAttempt.legalIfStamina,
  reason: 'INSUFFICIENT_CAPABILITY_RESOURCE',
};

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-a-target-separation-probes',
  epistemicBoundary: {
    proves: [
      'under declared mappings, one input token can denote different GameActions by context',
      'different physical expressions can map to one GameAction',
      'different trajectories can be goal-equivalent under a declared task variable',
      'one nominal performance score can rank controllers differently from cross-condition robustness',
      'an admitted action attempt can diverge from execution under capability/resource constraints'
    ],
    doesNotProve: [
      'human motor-control mechanisms',
      'a universal Skill metric',
      'that robustness is always more valuable than peak performance',
      'subjective agency or embodiment',
      'scientific novelty'
    ]
  },
  sameInputDifferentAction,
  sameActionDifferentMovement,
  goalEquivalentTrajectories,
  goalEquivalent,
  robustness,
  attemptVsExecution,
  laws: [
    'InputSignal != GameAction',
    'PlayerMotorMovement != GameAction',
    'MovementTrajectory != TaskOutcome',
    'PerformanceSample != SkillState',
    'ActionAttempt != ExecutedAction'
  ]
};

const output = process.argv[2] ?? 'evidence/gdf1-a/target-separation-probes.json';
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
