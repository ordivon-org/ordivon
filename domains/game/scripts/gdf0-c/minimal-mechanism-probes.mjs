#!/usr/bin/env node

/**
 * GDF0-C research-only executable probes.
 *
 * These probes do NOT measure human PlayExperience and do NOT select a product.
 * They only test whether proposed mechanism coordinates make discriminating
 * structural predictions under transparent toy assumptions.
 */

import fs from 'node:fs';
import path from 'node:path';

function round(value, digits = 6) {
  const scale = 10 ** digits;
  return Math.round(value * scale) / scale;
}

function mean(xs) {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

// ---------------------------------------------------------------------------
// Probe A — AgencySculpting / PolicyDifferentiation
// ---------------------------------------------------------------------------
// Hold context count, action count, and legal-action count fixed. Only change
// the payoff topology. In the flat condition one action dominates everywhere;
// in the sculpted condition a different action is best in each context.
// If "constraint amount" alone explained agency structure, these conditions
// would be indistinguishable. They are not.

const contexts = ['north', 'east', 'south', 'west'];
const actions = ['A', 'B', 'C', 'D'];

const flatPayoffs = {
  north: { A: 5, B: 2, C: 1, D: 0 },
  east:  { A: 5, B: 2, C: 1, D: 0 },
  south: { A: 5, B: 2, C: 1, D: 0 },
  west:  { A: 5, B: 2, C: 1, D: 0 },
};

const sculptedPayoffs = {
  north: { A: 5, B: 2, C: 1, D: 0 },
  east:  { A: 1, B: 5, C: 2, D: 0 },
  south: { A: 0, B: 1, C: 5, D: 2 },
  west:  { A: 2, B: 0, C: 1, D: 5 },
};

function bestActionForContext(payoffs, context) {
  return actions.reduce((best, action) =>
    payoffs[context][action] > payoffs[context][best] ? action : best,
  actions[0]);
}

function contextualPolicyValue(payoffs) {
  return mean(contexts.map((context) => {
    const action = bestActionForContext(payoffs, context);
    return payoffs[context][action];
  }));
}

function bestFixedActionValue(payoffs) {
  const values = actions.map((action) => ({
    action,
    value: mean(contexts.map((context) => payoffs[context][action])),
  }));
  values.sort((a, b) => b.value - a.value || a.action.localeCompare(b.action));
  return values[0];
}

function policyDifferentiationProbe(label, payoffs) {
  const optimalActions = contexts.map((context) => bestActionForContext(payoffs, context));
  const contextualValue = contextualPolicyValue(payoffs);
  const fixed = bestFixedActionValue(payoffs);
  return {
    label,
    contexts: contexts.length,
    actions: actions.length,
    legalActionsPerContext: actions.length,
    uniqueOptimalActions: new Set(optimalActions).size,
    optimalActionByContext: Object.fromEntries(contexts.map((c, i) => [c, optimalActions[i]])),
    contextualPolicyValue: round(contextualValue),
    bestContextBlindAction: fixed.action,
    bestContextBlindValue: round(fixed.value),
    adaptivePolicyGain: round(contextualValue - fixed.value),
  };
}

const agencySculpting = [
  policyDifferentiationProbe('flat-dominance', flatPayoffs),
  policyDifferentiationProbe('context-sculpted', sculptedPayoffs),
];

// ---------------------------------------------------------------------------
// Probe E/M — Exploration-learning-progress versus mature execution challenge
// ---------------------------------------------------------------------------
// A fully learnable fixed cue sequence is exposed repeatedly. Prediction error
// falls to zero once the sequence is learned. Separately, execution success
// depends on timing noise and skill precision, so performance discrimination
// can remain after information gain disappears.
//
// This does NOT prove continued human replay value. It only falsifies the
// stronger structural claim that continued differentiated performance requires
// continued environment-model information gain.

const cueSequence = [0, 1, 0, 2, 1, 2, 0, 1, 2, 2, 1, 0];

function explorationMasteryProbe() {
  const known = new Map();
  const predictionErrors = [];
  const learningProgress = [];

  for (let pass = 0; pass < 5; pass += 1) {
    let errors = 0;
    for (let i = 0; i < cueSequence.length; i += 1) {
      const key = i;
      const observed = cueSequence[i];
      const predicted = known.has(key) ? known.get(key) : null;
      if (predicted !== observed) errors += 1;
      known.set(key, observed);
    }
    predictionErrors.push(errors / cueSequence.length);
    if (pass === 0) learningProgress.push(null);
    else learningProgress.push(predictionErrors[pass - 1] - predictionErrors[pass]);
  }

  // Deterministic expected execution scores under a simple timing-noise model.
  // A trial succeeds when |noise| <= tolerance. We evaluate the exact finite
  // noise grid rather than sampling, so evidence is reproducible.
  const noiseGrid = [];
  for (let i = -100; i <= 100; i += 1) noiseGrid.push(i / 100);

  const skillProfiles = [
    { name: 'novice', tolerance: 0.25 },
    { name: 'intermediate', tolerance: 0.5 },
    { name: 'expert', tolerance: 0.75 },
  ];

  const execution = skillProfiles.map(({ name, tolerance }) => {
    const successRate = mean(noiseGrid.map((noise) => Math.abs(noise) <= tolerance ? 1 : 0));
    return { name, tolerance, successRate: round(successRate) };
  });

  return {
    passes: predictionErrors.map((error, pass) => ({
      pass: pass + 1,
      predictionError: round(error),
      learningProgress: learningProgress[pass] == null ? null : round(learningProgress[pass]),
    })),
    modelSaturatedAfterPass: predictionErrors.findIndex((x) => x === 0) + 1,
    executionDiscriminationAfterModelSaturation: execution,
    structuralConclusion:
      'environment-model learning progress can reach zero while execution outcomes remain skill-sensitive',
    humanValueClaim: 'NOT TESTED',
  };
}

// ---------------------------------------------------------------------------
// Probe O — Open-ended sandbox: fixed global goal versus local evaluation
// ---------------------------------------------------------------------------
// Show that absence of a fixed terminal goal does not imply absence of an
// evaluation topology. Local projects can make actions differentially relevant.
// Removing all local evaluation does not make action impossible; it removes the
// model basis for calling one intentional policy better/more fitting than
// another.

function sandboxEvaluationProbe() {
  const projects = {
    symmetry: { placeLeft: 3, placeRight: 3, stack: 0, paint: 1 },
    height:   { placeLeft: 1, placeRight: 1, stack: 4, paint: 0 },
    color:    { placeLeft: 0, placeRight: 0, stack: 1, paint: 4 },
  };
  const sandboxActions = ['placeLeft', 'placeRight', 'stack', 'paint'];
  const choices = Object.entries(projects).map(([project, values]) => {
    const bestValue = Math.max(...sandboxActions.map((action) => values[action]));
    return {
      project,
      bestActions: sandboxActions.filter((action) => values[action] === bestValue),
      bestValue,
    };
  });

  return {
    fixedGlobalTerminalGoal: false,
    localProjects: choices,
    noEvaluationAblation: {
      allActionsEqualUnderModel: true,
      intentionalPolicyOrderingAvailable: false,
      actionStillPhysicallyPossible: true,
    },
    structuralConclusion:
      'no fixed global goal does not entail no local/dynamic evaluation; intentional policy comparison requires some relevance/evaluation relation',
    universalGameNecessityClaim: 'NOT ESTABLISHED',
  };
}

// ---------------------------------------------------------------------------
// Probe R — Perturbation / recovery repertoire
// ---------------------------------------------------------------------------
// A transparent coverage model: training under no perturbation visits only the
// nominal state; moderate perturbation visits recoverable neighboring states;
// extreme perturbation includes unrecoverable states. The purpose is only to
// make the narrow Training-for-the-Unexpected mechanism executable and to
// expose its inverted-U boundary, not to establish biological truth.

function perturbationRecoveryProbe() {
  const testStates = [-2, -1, 0, 1, 2];
  const conditions = [
    { name: 'none', trained: new Set([0]) },
    { name: 'moderate', trained: new Set([-1, 0, 1]) },
    { name: 'extreme', trained: new Set([-2, -1, 0, 1, 2]), unrecoverable: new Set([-2, 2]) },
  ];

  return conditions.map((condition) => {
    const successes = testStates.map((state) => {
      const known = condition.trained.has(state);
      const unrecoverable = condition.unrecoverable?.has(state) ?? false;
      return known && !unrecoverable ? 1 : 0;
    });
    return {
      condition: condition.name,
      trainedStates: [...condition.trained],
      recoveryCoverage: round(mean(successes)),
      assumptionNote:
        condition.name === 'extreme'
          ? 'extreme perturbation includes states defined as unrecoverable'
          : 'recovery succeeds only for trained recoverable states',
    };
  });
}

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf0-c-minimal-mechanism-probes',
  epistemicBoundary: {
    proves: [
      'candidate mechanism coordinates can produce discriminating structural predictions under declared toy assumptions',
      'equal action/constraint counts do not imply equal policy differentiation',
      'environment-model learning progress can vanish while skill-sensitive execution differences remain',
      'absence of a fixed global goal is compatible with local/dynamic evaluation',
    ],
    doesNotProve: [
      'human fun, engagement, replay desire, immersion, or subjective PlayExperience',
      'that AgencySculpting uniquely distinguishes games from work, ritual, training, or art',
      'that any toy model is an evolutionary or psychological mechanism in humans/animals',
      'that every game requires an explicit goal or one scalar utility function',
    ],
  },
  agencySculpting,
  explorationVsMastery: explorationMasteryProbe(),
  openEndedEvaluation: sandboxEvaluationProbe(),
  perturbationRecovery: perturbationRecoveryProbe(),
};

const outputPath = process.argv[2] ?? 'evidence/gdf0-c/minimal-mechanism-probes.json';
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(result, null, 2));
