import assert from "node:assert/strict";
import test from "node:test";

import { StationZeroV3PlayService, StationZeroV3Store } from "../src/station-zero-v3/index.ts";

const recoverOrder = {
  primaryObjectiveId: "recover-research-core" as const,
  posture: "aggressive" as const,
  formation: "cohesive" as const,
  lootPolicy: "opportunistic" as const,
};

function front(view: ReturnType<StationZeroV3PlayService["initialize"]>, objectiveId: string) {
  const row = view.aftermath?.planReview.objectives.find((entry) => entry.objectiveId === objectiveId);
  assert.ok(row, `missing Plan Review front ${objectiveId}`);
  return row;
}

function intent(view: ReturnType<StationZeroV3PlayService["initialize"]>, actorId: string) {
  const row = view.aftermath?.ownIntentResults.find((entry) => entry.actorId === actorId);
  assert.ok(row, `missing intent review ${actorId}`);
  return row;
}

test("Aftermath binds committed Rescue actions to exact authoritative resolution without widening hidden knowledge", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:plan-review:first-turn";
    play.initialize({ runId });
    play.saveOrder(runId, recoverOrder);
    const generated = await play.generatePreview(runId);
    const view = (await play.commitPreview(runId, generated.preview.previewId)).view;

    assert.equal(intent(view, "medic-reyes").plannedAction, "Move to Command Deck");
    assert.equal(intent(view, "medic-reyes").status, "executed");
    assert.equal(intent(view, "security-chen").plannedAction, "Overwatch Command Deck");
    assert.equal(intent(view, "security-chen").status, "no_effect");
    assert.equal(intent(view, "security-chen").reason, "no_hostile_movement_triggered");
    assert.equal(front(view, "recover-research-core").plannedImpact, "none");
    assert.equal(front(view, "recover-research-core").afterProgress, 0);
    assert.equal(JSON.stringify(view.aftermath).includes("pirate-captain-veyra"), false);
    assert.equal(JSON.stringify(view.aftermath).includes("hive-alpha"), false);
  } finally {
    store.close();
  }
});

test("Plan Review distinguishes direct support from actual objective completion", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:plan-review:core";
    let view = play.initialize({ runId });
    for (let turn = 0; turn <= 2; turn += 1) {
      play.saveOrder(runId, recoverOrder);
      const generated = await play.generatePreview(runId);
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    }
    const core = front(view, "recover-research-core");
    assert.equal(core.plannedImpact, "direct");
    assert.deepEqual(core.supportingActorNames, ["Engineer Imani"]);
    assert.equal(core.beforeProgress, 0);
    assert.equal(core.afterProgress, 0);
    assert.equal(core.afterStatus, "active");
    assert.equal(intent(view, "engineer-imani").plannedAction, "Pick up research-core");
    assert.equal(intent(view, "engineer-imani").status, "executed");
    assert.equal(intent(view, "engineer-imani").reason, "ground_item_acquired");
  } finally {
    store.close();
  }
});

test("Plan Review records visible mission-front completion after a direct extraction plan", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:plan-review:extraction";
    let view = play.initialize({ runId });
    let extractingActorId: string | null = null;
    while (view.run.status === "running" && view.run.turn < 15 && extractingActorId === null) {
      const generated = await play.generatePreview(runId);
      extractingActorId = generated.view.experience.preview?.actorIntents
        .find((entry) => entry.action === "Extract from Station Zero")?.actorId ?? null;
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    }
    assert.ok(extractingActorId, "fixture must expose a direct specialist extraction within the bounded review window");
    const survival = front(view, "rescue-team-survives");
    assert.equal(survival.plannedImpact, "direct");
    assert.equal(survival.beforeProgress, 0);
    assert.equal(survival.afterProgress, 1);
    assert.equal(survival.beforeStatus, "active");
    assert.equal(survival.afterStatus, "completed");
    assert.equal(intent(view, extractingActorId).plannedAction, "Extract from Station Zero");
    assert.equal(intent(view, extractingActorId).reason, "actor_extracted");
  } finally {
    store.close();
  }
});
