import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  initialStationZeroV3CommanderOrder,
  StationZeroV3PlayService,
  StationZeroV3Store,
} from "../src/station-zero-v3/index.ts";

const standingPatch = {
  primaryObjectiveId: "recover-research-core" as const,
  posture: "aggressive" as const,
  formation: "cohesive" as const,
  retreatHealthThreshold: 0.6,
  lethalForce: "preferred" as const,
  collateralPolicy: "limited" as const,
  lootPolicy: "opportunistic" as const,
  protectedActorId: "medic-reyes",
  commanderDirectiveId: "scan-reactor" as const,
};

test("first Planning still starts from current World defaults", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const view = play.initialize({ runId: "run:station-zero-v3:inherit:first" });
    assert.equal(view.experience.orderRevision, 1);
    assert.equal(view.experience.order?.primaryObjectiveId, "rescue-two-civilians");
    assert.equal(view.experience.order?.posture, "balanced");
    assert.equal(view.experience.order?.formation, "split");
    assert.equal(view.experience.order?.lootPolicy, "mission-only");
    assert.equal(view.experience.order?.commanderDirectiveId, "scan-reactor");
  } finally {
    store.close();
  }
});

test("new Planning inherits standing Commander intent but recalculates the Turn-local remote capability", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:inherit:turn-one";
    play.initialize({ runId });
    const saved = play.saveOrder(runId, standingPatch);
    assert.equal(saved.orderRevision, 2);
    const turnZero = await play.generatePreview(runId);
    const turnZeroOrder = turnZero.preview.playerOrder;
    const committed = await play.commitPreview(runId, turnZero.preview.previewId);
    const turnOne = committed.view.experience.order;
    assert.ok(turnOne);

    assert.notEqual(turnOne.planningId, turnZeroOrder.planningId);
    assert.equal(turnOne.expectedTurn, 1);
    assert.equal(turnOne.expectedWorldRevision, 1);
    assert.equal(committed.view.experience.orderRevision, 1);
    assert.equal(turnOne.primaryObjectiveId, turnZeroOrder.primaryObjectiveId);
    assert.equal(turnOne.posture, turnZeroOrder.posture);
    assert.equal(turnOne.formation, turnZeroOrder.formation);
    assert.equal(turnOne.retreatHealthThreshold, turnZeroOrder.retreatHealthThreshold);
    assert.equal(turnOne.lethalForce, turnZeroOrder.lethalForce);
    assert.equal(turnOne.collateralPolicy, turnZeroOrder.collateralPolicy);
    assert.equal(turnOne.lootPolicy, turnZeroOrder.lootPolicy);
    assert.equal(turnOne.protectedActorId, turnZeroOrder.protectedActorId);
    assert.equal(turnOne.priorityTargetActorId, turnZeroOrder.priorityTargetActorId);
    assert.equal(turnZeroOrder.commanderDirectiveId, "scan-reactor");
    assert.equal(turnOne.commanderDirectiveId, "reroute-cooling");
    assert.notEqual(committed.view.experience.orderDigest, turnZero.preview.orderDigest);
  } finally {
    store.close();
  }
});

test("inherited protection clears when the Rescue specialist is no longer active", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:inherit:protection";
    play.initialize({ runId });
    const planning = store.latestPlanning(runId)!;
    const state = structuredClone(store.loadState(runId));
    const previous = { ...play.state(runId).experience.order!, protectedActorId: "medic-reyes" };

    state.actors["medic-reyes"]!.lifeState = "extracted";
    const inherited = initialStationZeroV3CommanderOrder(runId, planning, state, previous);
    assert.equal(inherited.protectedActorId, null);

    state.actors["medic-reyes"]!.lifeState = "active";
    assert.equal(initialStationZeroV3CommanderOrder(runId, planning, state, previous).protectedActorId, "medic-reyes");
  } finally {
    store.close();
  }
});

test("priority target inheritance follows Rescue knowledge, not hidden target truth", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:inherit:priority";
    play.initialize({ runId });
    const planning = store.latestPlanning(runId)!;
    const state = structuredClone(store.loadState(runId));
    const previous = { ...play.state(runId).experience.order!, priorityTargetActorId: "pirate-hacker-nyx" };
    state.factionKnowledge.rescue.knownActors["pirate-hacker-nyx"] = {
      actorId: "pirate-hacker-nyx",
      lastKnownZoneId: "command-deck",
      observedLifeState: "active",
      observedHealthBand: "healthy",
      confidence: "confirmed",
      observedAtTurn: 0,
    };

    state.actors["pirate-hacker-nyx"]!.lifeState = "dead";
    assert.equal(
      initialStationZeroV3CommanderOrder(runId, planning, state, previous).priorityTargetActorId,
      "pirate-hacker-nyx",
      "hidden actual death must not silently clear a target Rescue still observes as active",
    );

    state.factionKnowledge.rescue.knownActors["pirate-hacker-nyx"]!.observedLifeState = "dead";
    assert.equal(initialStationZeroV3CommanderOrder(runId, planning, state, previous).priorityTargetActorId, null);
  } finally {
    store.close();
  }
});

test("inherited Commander intent is retained across process reopen", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-order-inherit-"));
  const path = join(directory, "station-zero.sqlite3");
  const runId = "run:station-zero-v3:inherit:restart";
  let expectedOrder;
  let expectedDigest;
  const firstStore = new StationZeroV3Store(path);
  try {
    const play = new StationZeroV3PlayService(firstStore);
    play.initialize({ runId });
    play.saveOrder(runId, standingPatch);
    const generated = await play.generatePreview(runId);
    const committed = await play.commitPreview(runId, generated.preview.previewId);
    expectedOrder = committed.view.experience.order;
    expectedDigest = committed.view.experience.orderDigest;
    assert.equal(committed.view.experience.orderRevision, 1);
  } finally {
    firstStore.close();
  }

  const reopened = new StationZeroV3Store(path);
  try {
    const play = new StationZeroV3PlayService(reopened);
    const resumed = play.resume(runId);
    assert.deepEqual(resumed.experience.order, expectedOrder);
    assert.equal(resumed.experience.orderDigest, expectedDigest);
    assert.equal(resumed.experience.orderRevision, 1);
  } finally {
    reopened.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
