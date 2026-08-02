import assert from "node:assert/strict";
import test from "node:test";

import { createMissionControlCatalog } from "../src/mission-control/catalog.ts";
import {
  doctrineForPolicy,
  forecastCommands,
  missionFronts,
  missionOutcome,
  passiveForecast,
  policyForDoctrine,
} from "../src/mission-control/experience.ts";
import { MissionControlService } from "../src/mission-control/service.ts";
import { ENGINEER_ID, MEDIC_ID, initialTeamWorld } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";

function service(store = new GameStore(":memory:")) {
  return { store, service: new MissionControlService(store, () => new FixtureTeamProvider()) };
}

test("passive next-Tick forecast is exact, bounded, and side-effect free", () => {
  const state = initialTeamWorld();
  const forecast = passiveForecast(state);
  assert.equal(forecast.status, "available");
  assert.equal(forecast.fromRevision, 0);
  assert.equal(forecast.resultingRevision, 1);
  assert.equal(forecast.resources.find((entry) => entry.resourceId === "oxygen")?.after, 74);
  assert.equal(forecast.resources.find((entry) => entry.resourceId === "reactor-heat")?.after, 46);
  assert.equal(forecast.resources.find((entry) => entry.resourceId === "crew-health")?.after, 48);
  assert.equal(state.revision, 0);
  assert.equal(state.resources.oxygen, 78);
});

test("Play catalog exposes doctrines without removing Lab providers", () => {
  const catalog = createMissionControlCatalog();
  assert.deepEqual(catalog.doctrines.map((entry) => entry.doctrineId), [
    "delegated-response",
    "critical-approval",
    "strict-control",
  ]);
  assert.equal(catalog.playDefaults.doctrineId, "critical-approval");
  assert.ok(catalog.providers.some((entry) => entry.providerId === "codex"));
});

test("critical approval runs multiple verified Ticks and stops at a real intervention", async () => {
  const { store, service: mission } = service();
  try {
    const runId = "run:experience:critical";
    mission.initialize({ runId, doctrineId: "critical-approval" });
    const first = await mission.advancePlay(runId, "until-intervention", 24, 512);
    assert.equal(first.boundary, "intervention");
    assert.deepEqual(first.committedRevisions, [1, 2, 3]);
    assert.equal(first.view.run.turn, 3);
    const card = first.view.inbox.find((entry) => entry.kind === "authority-request");
    assert.ok(card?.forecast?.resources.some((entry) => entry.resourceId === "oxygen"));
    const approve = card?.commands.find((entry) => entry.action === "approve");
    assert.ok(approve?.proposalId);
    mission.command(runId, { action: "approve", proposalId: approve.proposalId });
    const afterApproval = mission.state(runId);
    assert.equal(afterApproval.experience.activeInterventionId, null);
    const next = await mission.advancePlay(runId, "until-intervention", 24, 512);
    assert.ok(next.committedRevisions.length >= 1);
    assert.ok(next.view.run.turn > first.view.run.turn);
  } finally {
    store.close();
  }
});

test("delegated doctrine can complete the deterministic baseline without per-Tick confirmation", async () => {
  const { store, service: mission } = service();
  try {
    const runId = "run:experience:delegated";
    mission.initialize({ runId, doctrineId: "delegated-response" });
    const result = await mission.advancePlay(runId, "until-intervention", 24, 512);
    assert.equal(result.boundary, "terminal");
    assert.equal(result.view.run.status, "victory");
    assert.equal(result.view.run.turn, 18);
    assert.equal(result.committedRevisions.length, 18);
    assert.equal(result.view.experience.fronts.length, 4);
    assert.equal(result.view.experience.outcome?.headline, "Rescue signal verified");
  } finally {
    store.close();
  }
});


test("doctrine mappings preserve explicit modes and bounded fallbacks", () => {
  assert.equal(policyForDoctrine("delegated-response"), "autonomous");
  assert.equal(policyForDoctrine("critical-approval"), "supervised");
  assert.equal(policyForDoctrine("strict-control"), "locked");
  assert.equal(policyForDoctrine(undefined), "supervised");
  assert.equal(doctrineForPolicy("autonomous"), "delegated-response");
  assert.equal(doctrineForPolicy("supervised"), "critical-approval");
  assert.equal(doctrineForPolicy("locked"), "strict-control");
  assert.equal(doctrineForPolicy(undefined), "critical-approval");
});

test("proposal forecast reports rejected admission and every irreversible first-playable effect", () => {
  const rejectedState = initialTeamWorld();
  const rejected = forecastCommands(rejectedState, [{
    kind: "repair_system",
    commandId: "forecast:rejected",
    actorId: ENGINEER_ID,
    expectedRevision: 0,
    targetSystemId: "cooling",
  }], "Invalid remote repair");
  assert.equal(rejected.status, "unavailable");
  assert.match(rejected.unavailableReason ?? "", /must be in reactor/i);

  const repairedState = initialTeamWorld();
  repairedState.agents[ENGINEER_ID]!.location = "reactor";
  const repair = forecastCommands(repairedState, [{
    kind: "repair_system", commandId: "forecast:repair", actorId: ENGINEER_ID,
    expectedRevision: 0, targetSystemId: "cooling",
  }], "Repair cooling");
  assert.match(repair.irreversibleEffects[0] ?? "", /spare part/i);
  assert.ok(repair.objectiveChanges.includes("cooling-operational"));

  const sealedState = initialTeamWorld();
  sealedState.agents[ENGINEER_ID]!.location = "maintenance";
  sealedState.agents[ENGINEER_ID]!.inventory.sealant = 1;
  sealedState.rooms.storage!.inventory.sealant = 0;
  const seal = forecastCommands(sealedState, [{
    kind: "seal_hull", commandId: "forecast:seal", actorId: ENGINEER_ID,
    expectedRevision: 0, targetHazardId: "maintenance-breach",
  }], "Seal breach");
  assert.match(seal.irreversibleEffects[0] ?? "", /permanently sealed/i);

  const medicalState = initialTeamWorld();
  medicalState.agents[MEDIC_ID]!.location = "medical-bay";
  medicalState.agents[MEDIC_ID]!.inventory.medkit = 1;
  medicalState.rooms["medical-bay"]!.inventory.medkit = 0;
  const treatment = forecastCommands(medicalState, [{
    kind: "stabilize_crew", commandId: "forecast:treat", actorId: MEDIC_ID,
    expectedRevision: 0, targetCrewId: "crew-01",
  }], "Stabilize casualty");
  assert.match(treatment.irreversibleEffects[0] ?? "", /medkit/i);

  const distressState = initialTeamWorld();
  distressState.agents[ENGINEER_ID]!.location = "communications";
  distressState.systems.communications!.integrity = 0.9;
  distressState.systems.communications!.powered = true;
  const distress = forecastCommands(distressState, [{
    kind: "send_distress", commandId: "forecast:distress", actorId: ENGINEER_ID,
    expectedRevision: 0, targetSystemId: "communications",
  }], "Transmit distress");
  assert.match(distress.irreversibleEffects[0] ?? "", /rescue signal/i);
});

test("Mission Fronts cover resolved, warning, and critical product states", () => {
  const critical = initialTeamWorld();
  critical.resources.reactorHeat = 90;
  critical.resources.oxygen = 25;
  critical.crew["crew-01"]!.health = 15;
  critical.mission.turnLimit = 3;
  const criticalFronts = missionFronts(critical, [], passiveForecast(critical));
  assert.equal(criticalFronts.find((front) => front.frontId === "reactor")?.status, "critical");
  assert.equal(criticalFronts.find((front) => front.frontId === "crew")?.status, "critical");
  assert.equal(criticalFronts.find((front) => front.frontId === "habitation")?.status, "critical");
  assert.equal(criticalFronts.find((front) => front.frontId === "rescue")?.status, "critical");

  const warning = initialTeamWorld();
  warning.resources.reactorHeat = 65;
  warning.resources.oxygen = 50;
  warning.crew["crew-01"]!.health = 40;
  warning.mission.turnLimit = 8;
  const warningFronts = missionFronts(warning, [], passiveForecast(warning));
  assert.ok(warningFronts.some((front) => front.status === "at-risk"));

  const resolved = initialTeamWorld();
  resolved.systems.cooling!.integrity = 0.9;
  resolved.systems.cooling!.powered = true;
  resolved.systems["life-support"]!.integrity = 0.9;
  resolved.systems["life-support"]!.powered = true;
  resolved.systems.communications!.integrity = 0.9;
  resolved.systems.communications!.powered = true;
  resolved.hazards["maintenance-breach"]!.contained = true;
  resolved.crew["crew-01"]!.stabilized = true;
  resolved.mission.distressSent = true;
  const resolvedFronts = missionFronts(resolved, [], passiveForecast(resolved));
  assert.ok(resolvedFronts.every((front) => front.status === "resolved"));
  assert.ok(resolvedFronts.every((front) => front.primaryBlocker === null));
});

test("outcome projection distinguishes victory, failure, and terminal margins", () => {
  assert.equal(missionOutcome(initialTeamWorld()), null);
  const victory = initialTeamWorld();
  victory.mission.status = "victory";
  victory.mission.reason = "rescue_signal_verified";
  victory.mission.distressSent = true;
  victory.crew["crew-01"]!.stabilized = true;
  victory.hazards["maintenance-breach"]!.contained = true;
  victory.systems.cooling!.integrity = 0.9;
  victory.systems["life-support"]!.powered = true;
  victory.resources.batteryCharge = 8;
  victory.resources.energyConsumed = 48;
  const victoryOutcome = missionOutcome(victory);
  assert.equal(victoryOutcome?.headline, "Rescue signal verified");
  assert.ok(victoryOutcome?.nearMisses.some((entry) => /Battery/.test(entry)));

  const failure = initialTeamWorld();
  failure.mission.status = "failure";
  failure.mission.reason = "reactor_meltdown";
  failure.resources.reactorHeat = 100;
  failure.resources.oxygen = 40;
  failure.crew["crew-01"]!.health = 25;
  const failureOutcome = missionOutcome(failure);
  assert.equal(failureOutcome?.headline, "Mission failed");
  assert.match(failureOutcome?.summary ?? "", /reactor_meltdown/);
  assert.ok((failureOutcome?.nearMisses.length ?? 0) >= 3);
});

test("Play advancement validates budgets and preserves terminal and pending-intervention boundaries", async () => {
  const { store, service: mission } = service();
  try {
    const runId = "run:experience:boundaries";
    mission.initialize({ runId, doctrineId: "critical-approval" });
    await assert.rejects(() => mission.advancePlay(runId, "one-tick", 0), /maximumWorldTicks/);
    await assert.rejects(() => mission.advancePlay(runId, "one-tick", 1, 513), /maximumInternalSteps/);
    const first = await mission.advancePlay(runId, "until-intervention", 24, 512);
    assert.equal(first.boundary, "intervention");
    const repeated = await mission.advancePlay(runId, "until-intervention", 24, 512);
    assert.equal(repeated.boundary, "intervention");
    assert.deepEqual(repeated.committedRevisions, []);
  } finally {
    store.close();
  }

  const terminalStore = new GameStore(":memory:");
  try {
    const terminalMission = new MissionControlService(terminalStore, () => new FixtureTeamProvider());
    const runId = "run:experience:terminal-boundary";
    terminalMission.initialize({ runId, doctrineId: "delegated-response" });
    const completed = await terminalMission.advancePlay(runId, "until-intervention", 24, 512);
    assert.equal(completed.boundary, "terminal");
    const repeated = await terminalMission.advancePlay(runId, "one-tick");
    assert.equal(repeated.boundary, "terminal");
    assert.deepEqual(repeated.steps, []);
  } finally {
    terminalStore.close();
  }
});


test("forecast, Mission Front, and outcome projections cover terminal and fallback branches", () => {
  const terminalState = initialTeamWorld();
  terminalState.resources.reactorHeat = 94;
  const terminalForecast = forecastCommands(terminalState, [{
    kind: "wait", commandId: "forecast:terminal", actorId: ENGINEER_ID, expectedRevision: 0,
  }], "Wait into meltdown");
  assert.deepEqual(terminalForecast.terminal, { status: "failure", reason: "reactor_meltdown" });

  const unavailable = forecastCommands(initialTeamWorld(), [{
    kind: "repair_system", commandId: "forecast:fallback", actorId: ENGINEER_ID,
    expectedRevision: 0, targetSystemId: "cooling",
  }], "Unavailable forecast");
  const fallbackFronts = missionFronts(initialTeamWorld(), [{
    objectiveId: "cooling-operational",
    label: "Repair cooling",
    priority: "critical",
    status: "active",
    dependencies: [],
    alternatives: [],
    actorIds: [ENGINEER_ID],
  }], unavailable);
  assert.equal(fallbackFronts.find((front) => front.frontId === "reactor")?.primaryBlocker, "Repair cooling");
  assert.match(fallbackFronts.find((front) => front.frontId === "reactor")?.forecast ?? "", /40 → 40/);

  const alternate = initialTeamWorld();
  alternate.mission.status = "failure";
  alternate.mission.reason = "mission_timeout";
  alternate.mission.distressSent = true;
  alternate.crew["crew-01"]!.health = 0;
  alternate.crew["crew-01"]!.stabilized = true;
  alternate.hazards["maintenance-breach"]!.sealed = true;
  alternate.systems.cooling!.integrity = 0.9;
  alternate.systems["life-support"]!.powered = true;
  alternate.resources.batteryCharge = 20;
  alternate.resources.oxygen = 80;
  alternate.resources.reactorHeat = 10;
  const outcome = missionOutcome(alternate);
  assert.ok(outcome?.facts.some((entry) => /was lost/.test(entry)));
  assert.ok(outcome?.facts.some((entry) => /permanently sealed/.test(entry)));
  assert.ok(outcome?.facts.some((entry) => /cooling was restored/.test(entry)));
  assert.ok(outcome?.facts.some((entry) => /Life support remained powered/.test(entry)));
  assert.ok(outcome?.facts.some((entry) => /rescue signal was transmitted/.test(entry)));
  assert.deepEqual(outcome?.nearMisses, ["Navigator Sato ended at 0% health."]);
});

test("one-Tick and three-Tick Play controls stop at their requested verified budgets", async () => {
  const oneStore = new GameStore(":memory:");
  try {
    const mission = new MissionControlService(oneStore, () => new FixtureTeamProvider());
    const runId = "run:experience:one-tick";
    mission.initialize({ runId, doctrineId: "delegated-response" });
    const result = await mission.advancePlay(runId, "one-tick");
    assert.equal(result.boundary, "tick-verified");
    assert.deepEqual(result.committedRevisions, [1]);
  } finally {
    oneStore.close();
  }

  const threeStore = new GameStore(":memory:");
  try {
    const mission = new MissionControlService(threeStore, () => new FixtureTeamProvider());
    const runId = "run:experience:three-ticks";
    mission.initialize({ runId, doctrineId: "delegated-response" });
    const result = await mission.advancePlay(runId, "three-ticks");
    assert.equal(result.boundary, "maximum-ticks");
    assert.deepEqual(result.committedRevisions, [1, 2, 3]);
  } finally {
    threeStore.close();
  }
});
