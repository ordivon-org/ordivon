import assert from "node:assert/strict";
import test from "node:test";

import {
  compileStationZeroV3AgentContext,
  createStationZeroV3PlayCatalog,
  defaultStationZeroV3CommanderOrder,
  FixtureStationZeroV3AgentProvider,
  StationZeroV3PlayService,
  StationZeroV3Store,
} from "../src/station-zero-v3/index.ts";

async function fixtureChoice(
  state: ReturnType<StationZeroV3Store["loadState"]>,
  planning: NonNullable<ReturnType<StationZeroV3Store["latestPlanning"]>>,
  runId: string,
  actorId: string,
  patch: Record<string, unknown>,
) {
  const provider = new FixtureStationZeroV3AgentProvider();
  const order = { ...defaultStationZeroV3CommanderOrder(runId, planning, state), ...patch };
  const context = compileStationZeroV3AgentContext(state, planning, actorId, order);
  const decision = await provider.decide(context);
  const selected = context.candidates.find((candidate) => candidate.candidateId === decision.candidateId);
  assert.ok(selected);
  return selected;
}

test("Commander catalog explains every surfaced option and defaults protection to explicit opt-in", () => {
  const catalog = createStationZeroV3PlayCatalog();
  for (const collection of [catalog.objectives, catalog.postures, catalog.formations, catalog.commanderDirectives, catalog.lethalForce, catalog.lootPolicies]) {
    assert.ok(collection.length > 0);
    assert.ok(collection.every((entry) => typeof entry.description === "string" && entry.description.trim().length > 0));
  }

  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:order-default-protection";
    const view = play.initialize({ runId });
    assert.equal(view.experience.order?.protectedActorId, null);
  } finally {
    store.close();
  }
});

test("situational retreat and loot controls change fixture decisions only when their opportunity exists", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:order-situational-controls";
    play.initialize({ runId });
    const planning = store.latestPlanning(runId);
    assert.ok(planning);
    const initial = store.loadState(runId);

    const retreatState = structuredClone(initial);
    retreatState.actors["medic-reyes"]!.health = 45;
    assert.equal((await fixtureChoice(retreatState, planning, runId, "medic-reyes", { retreatHealthThreshold: 0 })).label, "Move to Power Console");
    assert.equal((await fixtureChoice(retreatState, planning, runId, "medic-reyes", { retreatHealthThreshold: 0.6 })).label, "Extract from Station Zero");

    const lootState = structuredClone(initial);
    lootState.groundItems["ground:medkit"]!.zoneId = "rescue-airlock";
    lootState.passages["passage:rescue-deck"]!.state = "closed";
    assert.equal((await fixtureChoice(lootState, planning, runId, "medic-reyes", { lootPolicy: "ignore" })).label, "Overwatch Rescue Airlock");
    assert.equal((await fixtureChoice(lootState, planning, runId, "medic-reyes", { lootPolicy: "opportunistic" })).label, "Pick up medkit");
  } finally {
    store.close();
  }
});

test("explicit protection and lethal preference have distinct deterministic fixture semantics", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:order-explicit-semantics";
    play.initialize({ runId });
    const planning = store.latestPlanning(runId);
    assert.ok(planning);
    const initial = store.loadState(runId);

    const unprotected = await fixtureChoice(initial, planning, runId, "security-chen", { protectedActorId: null, posture: "cautious" });
    const protectedMedic = await fixtureChoice(initial, planning, runId, "security-chen", { protectedActorId: "medic-reyes", posture: "cautious" });
    assert.equal(unprotected.label, "Overwatch Command Deck");
    assert.equal(protectedMedic.label, "Overwatch Rescue Airlock");

    const combatState = structuredClone(initial);
    combatState.actors["pirate-hacker-nyx"]!.position.zoneId = "command-deck";
    combatState.factionKnowledge.rescue.knownActors["pirate-hacker-nyx"] = {
      actorId: "pirate-hacker-nyx",
      lastKnownZoneId: "command-deck",
      observedLifeState: "active",
      observedHealthBand: "healthy",
      confidence: "confirmed",
      observedAtTurn: 0,
    };
    const permitted = await fixtureChoice(combatState, planning, runId, "security-chen", { lethalForce: "permitted" });
    const preferred = await fixtureChoice(combatState, planning, runId, "security-chen", { lethalForce: "preferred" });
    const forbidden = await fixtureChoice(combatState, planning, runId, "security-chen", { lethalForce: "forbidden" });
    assert.equal(permitted.label, "Move to an uncharted adjacent sector");
    assert.match(preferred.label, /against Hacker Nyx/);
    assert.equal(forbidden.label, "Move to an uncharted adjacent sector");
  } finally {
    store.close();
  }
});
