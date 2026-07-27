import { writeFileSync } from "node:fs";

import { sha256 } from "../src/digest.ts";
import type { AvailableAction, WorldState } from "../src/model.ts";
import {
  communicationsFirstPolicy,
  recoveryPolicy,
  runPolicy,
  type ScriptedPolicy,
} from "../src/policies.ts";
import { initialWorld } from "../src/scenario.ts";
import { scoreMission } from "../src/scoring.ts";
import { applyWorldCommandV2, listAvailableActions, materializeAction } from "../src/world.ts";

function randomGenerator(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (1_664_525 * state + 1_013_904_223) >>> 0;
    return state / 2 ** 32;
  };
}

function finishWithPolicy(state: WorldState, policy: ScriptedPolicy, prefix: string): WorldState {
  let current = structuredClone(state);
  for (let step = 0; step < 64 && current.mission.status === "running"; step += 1) {
    const action = policy.choose(current);
    if (!action) break;
    const result = applyWorldCommandV2(
      current,
      materializeAction(action, `${prefix}:${step}:${action.actionId}`),
    );
    if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
    current = result.state;
  }
  return current;
}

function randomTrajectory(seed: number): WorldState {
  const random = randomGenerator(seed);
  let state = initialWorld();
  for (let step = 0; step < 64 && state.mission.status === "running"; step += 1) {
    const actions = listAvailableActions(state);
    const action = actions[Math.floor(random() * actions.length)];
    if (!action) throw new Error(`no action at random trajectory ${seed}:${step}`);
    const result = applyWorldCommandV2(
      state,
      materializeAction(action, `random:${seed}:${step}:${action.actionId}`),
    );
    if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
    state = result.state;
  }
  return state;
}

function summarizePolicy(policy: ScriptedPolicy) {
  const result = runPolicy(policy);
  return {
    policy: policy.name,
    status: result.state.mission.status,
    reason: result.state.mission.reason,
    turn: result.state.turn,
    digest: result.digest,
    score: scoreMission(result.state),
  };
}

function perturbRecoveryPath() {
  let state = initialWorld();
  const turns: Array<{
    turn: number;
    chosenAction: string;
    alternatives: number;
    recoverableVictories: number;
    alreadyIrrecoverable: boolean;
  }> = [];
  let totalAlternatives = 0;
  let recoverableAlternatives = 0;

  while (state.mission.status === "running") {
    const chosen = recoveryPolicy.choose(state);
    if (!chosen) throw new Error(`recovery policy stopped at revision ${state.revision}`);
    const alternatives = listAvailableActions(state).filter(
      (action) => action.actionId !== chosen.actionId,
    );
    let recoverable = 0;
    for (const alternative of alternatives) {
      const result = applyWorldCommandV2(
        state,
        materializeAction(
          alternative,
          `perturb:${state.turn}:${alternative.actionId}`,
        ),
      );
      if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
      const terminal = finishWithPolicy(
        result.state,
        recoveryPolicy,
        `recover:${state.turn}:${alternative.actionId}`,
      );
      if (terminal.mission.status === "victory") recoverable += 1;
    }
    totalAlternatives += alternatives.length;
    recoverableAlternatives += recoverable;
    turns.push({
      turn: state.turn,
      chosenAction: chosen.actionId,
      alternatives: alternatives.length,
      recoverableVictories: recoverable,
      alreadyIrrecoverable: alternatives.length > 0 && recoverable === 0,
    });
    const result = applyWorldCommandV2(
      state,
      materializeAction(chosen, `baseline:${state.turn}:${chosen.actionId}`),
    );
    if (result.status !== "accepted") throw new Error(`${result.code}: ${result.reason}`);
    state = result.state;
  }

  return {
    totalAlternatives,
    recoverableAlternatives,
    recoverableRate:
      totalAlternatives === 0 ? 0 : recoverableAlternatives / totalAlternatives,
    firstZeroRecoveryTurn: turns.find(
      (turn) => turn.alternatives > 0 && turn.recoverableVictories === 0,
    )?.turn ?? null,
    turns,
  };
}

const randomRuns = 1_000;
const randomSeed = 20_260_727;
const terminalReasons: Record<string, number> = {};
const scores: number[] = [];
let best: { seed: number; score: number; reason: string | null; digest: string } | null = null;
for (let index = 0; index < randomRuns; index += 1) {
  const seed = randomSeed + index;
  const terminal = randomTrajectory(seed);
  const reason = terminal.mission.reason ?? terminal.mission.status;
  terminalReasons[reason] = (terminalReasons[reason] ?? 0) + 1;
  const score = scoreMission(terminal).total;
  scores.push(score);
  if (!best || score > best.score) {
    best = { seed, score, reason: terminal.mission.reason, digest: sha256(terminal) };
  }
}

const report = {
  measurementVersion: 1,
  scenario: { id: "station-zero", version: 1 },
  ruleset: { id: "station-zero-core", version: 2 },
  fixedAt: "2026-07-27",
  baselines: [summarizePolicy(recoveryPolicy), summarizePolicy(communicationsFirstPolicy)],
  random: {
    runs: randomRuns,
    initialSeed: randomSeed,
    terminalReasons,
    score: {
      minimum: Math.min(...scores),
      maximum: Math.max(...scores),
      average: scores.reduce((total, score) => total + score, 0) / scores.length,
    },
    best,
  },
  perturbation: perturbRecoveryPath(),
};

if (process.argv.includes("--write")) {
  writeFileSync("docs/M15-MEASUREMENT.json", JSON.stringify(report, null, 2) + "\n");
}
console.log(JSON.stringify(report, null, 2));
