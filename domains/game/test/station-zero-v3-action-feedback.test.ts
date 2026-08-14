import assert from "node:assert/strict";
import test from "node:test";

import { StationZeroV3PlayService, StationZeroV3Store } from "../src/station-zero-v3/index.ts";

const recoverOrder = {
  primaryObjectiveId: "recover-research-core" as const,
  posture: "aggressive" as const,
  formation: "cohesive" as const,
  lootPolicy: "opportunistic" as const,
};

function rescueContext(preview: Awaited<ReturnType<StationZeroV3PlayService["generatePreview"]>>["preview"], actorId: string) {
  const context = preview.contexts.find((entry) => entry.factionId === "rescue" && entry.actor.actorId === actorId);
  assert.ok(context, `missing Rescue context ${actorId}`);
  return context;
}

test("next Planning carries exact one-Turn own-action feedback without hidden World facts", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:action-feedback:one-turn";
    play.initialize({ runId });
    play.saveOrder(runId, recoverOrder);
    const first = await play.generatePreview(runId);
    assert.equal(rescueContext(first.preview, "security-chen").previousActionFeedback, null);
    const firstSecurity = first.view.experience.preview?.actorIntents.find((entry) => entry.actorId === "security-chen");
    assert.equal(firstSecurity?.action, "Overwatch Command Deck");
    const committed = await play.commitPreview(runId, first.preview.previewId);
    const securityResult = committed.view.aftermath?.ownIntentResults.find((entry) => entry.actorId === "security-chen");
    assert.equal(securityResult?.status, "no_effect");
    assert.equal(securityResult?.reason, "no_hostile_movement_triggered");

    play.saveOrder(runId, recoverOrder);
    const second = await play.generatePreview(runId);
    const feedback = rescueContext(second.preview, "security-chen").previousActionFeedback;
    assert.ok(feedback);
    assert.equal(feedback.turnSequence, 0);
    assert.equal(feedback.candidateLabel, "Overwatch Command Deck");
    assert.equal(feedback.status, "no_effect");
    assert.equal(feedback.reason, "no_hostile_movement_triggered");
    assert.equal(feedback.intent.kind, "guard");
    assert.equal("facts" in feedback, false);
    assert.equal(JSON.stringify(feedback).includes("pirate-captain-veyra"), false);
    assert.equal(JSON.stringify(feedback).includes("hive-alpha"), false);
  } finally {
    store.close();
  }
});

test("fixture planner avoids immediate semantic repetition after no-effect and contested actions", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:action-feedback:adapt";
    let view = play.initialize({ runId });
    const actions: Array<Record<string, string>> = [];
    const results: Array<Record<string, { status: string; reason: string }>> = [];
    while (view.run.status === "running" && view.run.turn <= 6) {
      play.saveOrder(runId, recoverOrder);
      const generated = await play.generatePreview(runId);
      actions.push(Object.fromEntries(generated.view.experience.preview!.actorIntents.map((entry) => [entry.actorId, entry.action])));
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
      results.push(Object.fromEntries(view.aftermath!.ownIntentResults.map((entry) => [entry.actorId, { status: entry.status, reason: entry.reason }])));
    }

    assert.equal(actions[0]!["security-chen"], "Overwatch Command Deck");
    assert.equal(results[0]!["security-chen"]!.status, "no_effect");
    assert.equal(actions[1]!["security-chen"], "Overwatch Power Console");

    assert.equal(actions[1]!["medic-reyes"], "Move to Junction Machinery");
    assert.equal(results[1]!["medic-reyes"]!.status, "contested");
    assert.equal(actions[2]!["medic-reyes"], "Move to Reactor Console");

    assert.equal(actions[5]!["engineer-imani"], "Move to Command Deck");
    assert.equal(results[5]!["engineer-imani"]!.status, "contested");
    assert.notEqual(actions[6]!["engineer-imani"], "Move to Command Deck");
  } finally {
    store.close();
  }
});

test("Recover fixture has no consecutive identical failed semantic action after feedback", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:action-feedback:no-loop";
    let view = play.initialize({ runId });
    const previousFailure = new Map<string, string>();
    while (view.run.status === "running") {
      play.saveOrder(runId, recoverOrder);
      const generated = await play.generatePreview(runId);
      const planned = new Map(generated.view.experience.preview!.actorIntents.map((entry) => [entry.actorId, entry.action]));
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
      for (const result of view.aftermath!.ownIntentResults) {
        const action = planned.get(result.actorId)!;
        const failed = ["contested", "interrupted", "invalidated", "no_effect"].includes(result.status);
        if (failed) {
          assert.notEqual(previousFailure.get(result.actorId), action, `${result.actorName} repeated failed action ${action}`);
          previousFailure.set(result.actorId, action);
        } else {
          previousFailure.delete(result.actorId);
        }
      }
    }
    assert.equal(view.run.turn, 14);
  } finally {
    store.close();
  }
});
