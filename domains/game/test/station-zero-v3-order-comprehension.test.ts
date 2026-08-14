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

test("fixture carries acquired mission cargo toward extraction and honors assigned rescue responsibility", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:successor-commitment";
    play.initialize({ runId });
    const planning = store.latestPlanning(runId);
    assert.ok(planning);
    const initial = store.loadState(runId);

    const cargoState = structuredClone(initial);
    cargoState.actors["engineer-imani"]!.position.zoneId = "reactor-console";
    cargoState.actors["engineer-imani"]!.inventoryItemIds.push("research-core");
    cargoState.factionKnowledge.rescue.discoveredZoneIds.push("reactor-entry", "reactor-console");
    const cargoChoice = await fixtureChoice(cargoState, planning, runId, "engineer-imani", {
      primaryObjectiveId: "recover-research-core",
      posture: "balanced",
      formation: "split",
    });
    assert.equal(cargoChoice.intent.kind, "move");
    assert.ok(cargoChoice.tags.includes("route:rescue-airlock"));
    assert.ok(cargoChoice.tags.includes("objective:advance"));

    const acquireState = structuredClone(initial);
    acquireState.actors["engineer-imani"]!.position.zoneId = "junction-console";
    acquireState.factionKnowledge.rescue.discoveredZoneIds.push("reactor-entry", "reactor-console");
    const acquireOrder = {
      ...defaultStationZeroV3CommanderOrder(runId, planning, acquireState),
      primaryObjectiveId: "recover-research-core" as const,
      posture: "cautious" as const,
      formation: "split" as const,
    };
    const acquireContext = compileStationZeroV3AgentContext(acquireState, planning, "engineer-imani", acquireOrder);
    const reactorRoute = acquireContext.candidates.find((candidate) => candidate.tags.includes("route:reactor-console"));
    assert.ok(reactorRoute);
    assert.ok(reactorRoute.tags.includes("objective:advance"));

    const responsibilityState = structuredClone(initial);
    const kade = responsibilityState.actors["civilian-kade"]!;
    responsibilityState.factionKnowledge.rescue.knownActors[kade.actorId] = {
      actorId: kade.actorId,
      lastKnownZoneId: kade.position.zoneId,
      observedLifeState: "active",
      observedHealthBand: "wounded",
      confidence: "confirmed",
      observedAtTurn: 0,
    };
    responsibilityState.factionKnowledge.rescue.discoveredZoneIds.push("life-entry", "life-console");
    const responsibilityChoice = await fixtureChoice(responsibilityState, planning, runId, "engineer-imani", {
      primaryObjectiveId: "rescue-two-civilians",
      posture: "cautious",
      formation: "cohesive",
    });
    assert.ok(responsibilityChoice.tags.includes("responsibility:advance"));
  } finally {
    store.close();
  }
});

test("Hive focus can route through known Maintenance Entry before the Nest is revealed", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:hive-route-commitment";
    play.initialize({ runId });
    const planning = store.latestPlanning(runId);
    assert.ok(planning);
    const state = store.loadState(runId);
    state.factionKnowledge.rescue.discoveredZoneIds.push("maintenance-entry");
    const selected = await fixtureChoice(state, planning, runId, "security-chen", {
      primaryObjectiveId: "eliminate-hive-alpha",
      posture: "aggressive",
      formation: "split",
      lethalForce: "preferred",
    });
    assert.equal(selected.intent.kind, "move");
    assert.ok(selected.tags.includes("route:maintenance-entry"));
    assert.ok(selected.tags.includes("objective:advance"));

    const contactState = structuredClone(state);
    contactState.factionKnowledge.rescue.discoveredZoneIds.push("life-entry");
    contactState.factionKnowledge.rescue.knownActors["hive-alpha"] = {
      actorId: "hive-alpha",
      lastKnownZoneId: "life-entry",
      observedLifeState: "active",
      observedHealthBand: "healthy",
      confidence: "confirmed",
      observedAtTurn: 0,
    };
    const contactOrder = {
      ...defaultStationZeroV3CommanderOrder(runId, planning, contactState),
      primaryObjectiveId: "eliminate-hive-alpha" as const,
      posture: "aggressive" as const,
      formation: "split" as const,
    };
    const contactContext = compileStationZeroV3AgentContext(contactState, planning, "security-chen", contactOrder);
    const pursuit = contactContext.candidates.find((candidate) => candidate.tags.includes("route:life-entry"));
    assert.ok(pursuit);
    assert.ok(pursuit.tags.includes("objective:advance"));
  } finally {
    store.close();
  }
});
