import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import {
  compileOperationFrontier,
  compileSkillPlan,
  simulateSkillPlan,
  type OperationCandidate,
} from "../src/host/operations.ts";
import { analyzeGoalStrategy, analyzeThreats } from "../src/host/strategy.ts";
import { initialWorld } from "../src/world.ts";
import type { WorldState } from "../src/model.ts";

function select(
  state: WorldState,
  predicate: (candidate: OperationCandidate) => boolean,
): OperationCandidate {
  const candidate = compileOperationFrontier(state).find(predicate);
  assert.ok(candidate, "expected Operation candidate");
  return candidate;
}

function applyCandidate(state: WorldState, candidate: OperationCandidate): WorldState {
  return simulateSkillPlan(state, compileSkillPlan(state, candidate)).state;
}

function apply(
  state: WorldState,
  kind: OperationCandidate["kind"],
  targetId: string,
  powered?: boolean,
): WorldState {
  const candidate = select(state, (item) =>
    item.kind === kind &&
    item.target.id === targetId &&
    (powered === undefined ||
      item.successCondition.kind === "system_power" && item.successCondition.powered === powered));
  return applyCandidate(state, candidate);
}

test("initial strategy exposes explicit Goal dependencies and finite threat horizons", () => {
  const state = initialWorld();
  const analysis = analyzeGoalStrategy(state);
  assert.equal(analysis.totalVictoryRequirements, 8);
  assert.deepEqual(analysis.remainingVictoryRequirements, [
    "cooling_operational",
    "breach_sealed",
    "life_support_operational",
    "life_support_powered",
    "crew_stabilized",
    "distress_sent",
  ]);
  assert.deepEqual(analysis.activeDistressPrerequisites, [
    "communications_operational",
    "communications_powered",
  ]);
  const distress = analysis.requirements.find((requirement) => requirement.id === "distress_sent");
  assert.deepEqual(distress?.dependencies, ["communications_operational", "communications_powered"]);
  assert.deepEqual(
    analysis.activeThreats.slice(0, 3).map((threat) => [threat.id, threat.ticksToFailure]),
    [
      ["reactor_meltdown", 10],
      ["station_asphyxiation", 20],
      ["crew_lost", 25],
    ],
  );
  assert.equal(analysis.lowerBoundTimeFeasible, true);
  assert.ok(analysis.optimisticStepSlack > 0);
});

test("Operation frontier has contiguous transparent ranks and prioritizes urgent cooling", () => {
  const frontier = compileOperationFrontier(initialWorld());
  assert.deepEqual(frontier.map((candidate) => candidate.strategy.strategicRank), [1, 2, 3, 4, 5, 6]);
  assert.ok(frontier.every((candidate, index) =>
    index === 0 || frontier[index - 1]!.strategy.strategicScore <= candidate.strategy.strategicScore));
  assert.equal(frontier[0]?.kind, "repair_system");
  assert.equal(frontier[0]?.target.id, "cooling");
  assert.deepEqual(frontier[0]?.strategy.urgentMitigationsAdvanced, ["reactor_meltdown"]);
  assert.equal(frontier.at(-1)?.kind, "wait");
});

test("temporary oxygen or heat threshold loss is not misreported as structural regression", () => {
  const state = initialWorld();
  state.resources.oxygen = 38;
  const communications = select(
    state,
    (candidate) => candidate.kind === "repair_system" && candidate.target.id === "communications",
  );
  assert.ok(communications.strategy.remainingVictoryRequirements.includes("oxygen_safe"));
  assert.ok(!communications.strategy.regressed.includes("oxygen_safe"));
  assert.equal(communications.strategy.classification, "goal_progress");
});

test("safe cooling shutdown is derived from heat and remaining Goal horizon", () => {
  let state = initialWorld();
  state = apply(state, "repair_system", "cooling");
  state = apply(state, "set_power", "cooling", true);
  const earlyShutdown = select(
    state,
    (candidate) => candidate.kind === "set_power" && candidate.target.id === "cooling" &&
      candidate.successCondition.kind === "system_power" && !candidate.successCondition.powered,
  );
  assert.deepEqual(earlyShutdown.strategy.controlAdvantages, []);

  state = apply(state, "seal_hazard", "maintenance-breach");
  state = apply(state, "repair_system", "life-support");
  const safeShutdown = select(
    state,
    (candidate) => candidate.kind === "set_power" && candidate.target.id === "cooling" &&
      candidate.successCondition.kind === "system_power" && !candidate.successCondition.powered,
  );
  assert.deepEqual(safeShutdown.strategy.controlAdvantages, [
    "cooling_shutdown_preserves_battery_through_optimistic_goal_horizon",
  ]);
  assert.equal(safeShutdown.strategy.classification, "safety_progress");
  assert.ok(safeShutdown.strategy.projectedPowerDraw <
    Object.values(state.systems).filter((system) => system.powered)
      .reduce((total, system) => total + system.powerDraw, 0));
});

test("two-Operation lookahead exposes the final enable-communications to distress sequence", () => {
  let state = initialWorld();
  for (let decisions = 0; decisions < 20 && state.mission.status === "running"; decisions += 1) {
    const candidate = compileOperationFrontier(state)[0];
    assert.ok(candidate);
    if (candidate.kind === "set_power" && candidate.target.id === "communications" &&
      candidate.successCondition.kind === "system_power" && candidate.successCondition.powered) {
      assert.equal(candidate.strategy.strategicRank, 1);
      assert.equal(candidate.strategy.oneStepLookahead.projectedVictoryLabel, "Send verified distress signal");
      assert.ok(candidate.strategy.oneStepLookahead.projectedVictoryOperationId?.startsWith("operation:send_distress"));
      return;
    }
    state = applyCandidate(state, candidate);
  }
  assert.fail("ranked policy never reached communications enablement");
});

test("rank-one semantic policy reaches verified victory without Fixture or model correction", () => {
  let state = initialWorld();
  const trace: string[] = [];
  for (let decisions = 0; decisions < 24 && state.mission.status === "running"; decisions += 1) {
    const candidate = compileOperationFrontier(state)[0];
    assert.ok(candidate);
    trace.push(candidate.label);
    state = applyCandidate(state, candidate);
  }
  assert.equal(state.mission.status, "victory");
  assert.equal(state.mission.reason, "rescue_signal_verified");
  assert.ok(state.turn <= state.mission.turnLimit);
  assert.ok(trace.includes("Disable Reactor Cooling"));
  assert.equal(trace.at(-1), "Send verified distress signal");
  assert.equal(sha256(state), "4a6534c8a6a3ccdbf0e3970fdf3643bed4ab21f398b57d28ae6c29eabb0ed6e9");
});

test("old Codex near-goal state clearly separates control, regression, and terminal failure", () => {
  let state = initialWorld();
  state = apply(state, "repair_system", "cooling");
  state = apply(state, "set_power", "cooling", true);
  state = apply(state, "stabilize_crew", "crew-01");
  state = apply(state, "seal_hazard", "maintenance-breach");
  state = apply(state, "repair_system", "life-support");
  state = apply(state, "set_power", "life-support", true);
  state = apply(state, "repair_system", "communications");
  state = apply(state, "set_power", "communications", true);

  const frontier = compileOperationFrontier(state);
  const communicationsOff = select(
    state,
    (candidate) => candidate.kind === "set_power" && candidate.target.id === "communications" &&
      candidate.successCondition.kind === "system_power" && !candidate.successCondition.powered,
  );
  const lifeSupportOff = select(
    state,
    (candidate) => candidate.kind === "set_power" && candidate.target.id === "life-support" &&
      candidate.successCondition.kind === "system_power" && !candidate.successCondition.powered,
  );
  const distress = select(state, (candidate) => candidate.kind === "send_distress");
  assert.equal(communicationsOff.strategy.classification, "goal_regression");
  assert.ok(communicationsOff.strategy.regressed.includes("communications_powered"));
  assert.equal(lifeSupportOff.strategy.classification, "goal_regression");
  assert.ok(lifeSupportOff.strategy.regressed.includes("life_support_powered"));
  assert.equal(distress.strategy.classification, "immediate_failure");
  assert.equal(distress.projected.missionReason, "power_exhausted");
  const communicationsIndex = frontier.findIndex((candidate) =>
    candidate.operationCandidateId === communicationsOff.operationCandidateId);
  const lifeSupportIndex = frontier.findIndex((candidate) =>
    candidate.operationCandidateId === lifeSupportOff.operationCandidateId);
  assert.ok(communicationsIndex >= 0);
  assert.ok(lifeSupportIndex >= 0);
  assert.ok(communicationsIndex < lifeSupportIndex);
});

test("threat analysis handles powered safety, low atmosphere, terminal worlds, and severity bands", () => {
  const safe = initialWorld();
  safe.systems.cooling!.integrity = 0.9;
  safe.systems.cooling!.powered = true;
  safe.systems["life-support"]!.integrity = 0.9;
  safe.systems["life-support"]!.powered = true;
  safe.hazards["maintenance-breach"]!.sealed = true;
  safe.crew["crew-01"]!.stabilized = true;
  const safeThreats = analyzeThreats(safe);
  assert.ok(!safeThreats.some((threat) => threat.id === "reactor_meltdown"));
  assert.ok(!safeThreats.some((threat) => threat.id === "station_asphyxiation"));
  assert.ok(!safeThreats.some((threat) => threat.id === "crew_lost"));
  assert.ok(safeThreats.some((threat) => threat.id === "power_exhausted"));

  const dangerous = initialWorld();
  dangerous.resources.reactorHeat = 94;
  dangerous.resources.oxygen = 20;
  dangerous.agents["engineer-01"]!.location = "reactor";
  dangerous.agents["engineer-01"]!.health = 20;
  dangerous.crew["crew-01"]!.health = 12;
  const threats = analyzeThreats(dangerous);
  assert.equal(threats[0]?.severity, "critical");
  assert.ok(threats.some((threat) => threat.id === "engineer_incapacitated"));
  assert.ok(threats.some((threat) => threat.id === "crew_lost"));

  dangerous.mission.status = "failure";
  dangerous.mission.reason = "reactor_meltdown";
  assert.deepEqual(analyzeThreats(dangerous), []);
});

test("optimistic lower bound marks late unfinished states and terminal states", () => {
  const late = initialWorld();
  late.turn = 27;
  late.revision = 27;
  const analysis = analyzeGoalStrategy(late);
  assert.equal(analysis.turnsRemaining, 1);
  assert.equal(analysis.lowerBoundTimeFeasible, false);
  assert.ok(analysis.optimisticStepSlack < 0);

  const victory = initialWorld();
  victory.mission.status = "victory";
  victory.mission.reason = "rescue_signal_verified";
  victory.mission.distressSent = true;
  victory.systems.cooling!.integrity = 0.9;
  victory.hazards["maintenance-breach"]!.sealed = true;
  victory.systems["life-support"]!.integrity = 0.9;
  victory.systems["life-support"]!.powered = true;
  victory.crew["crew-01"]!.stabilized = true;
  assert.equal(analyzeGoalStrategy(victory).optimisticMinimumPrimitiveStepsToVictory, 0);

  const failure = initialWorld();
  failure.mission.status = "failure";
  failure.mission.reason = "reactor_meltdown";
  assert.equal(analyzeGoalStrategy(failure).optimisticMinimumPrimitiveStepsToVictory, Number.POSITIVE_INFINITY);

  const missingEngineer = initialWorld();
  delete missingEngineer.agents["engineer-01"];
  assert.equal(analyzeGoalStrategy(missingEngineer).optimisticMinimumPrimitiveStepsToVictory, Number.POSITIVE_INFINITY);
});
