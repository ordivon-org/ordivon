import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { StationZeroV3PlayService, StationZeroV3Store } from "../src/station-zero-v3/index.ts";

const recoverOrder = {
  primaryObjectiveId: "recover-research-core" as const,
  posture: "aggressive" as const,
  formation: "cohesive" as const,
  lootPolicy: "opportunistic" as const,
};

async function terminalRun(play: StationZeroV3PlayService, runId: string, order: typeof recoverOrder | null) {
  let view = play.initialize({ runId });
  while (view.run.status === "running") {
    if (order) play.saveOrder(runId, order);
    const generated = await play.generatePreview(runId);
    view = (await play.commitPreview(runId, generated.preview.previewId)).view;
  }
  return view;
}

test("running operation has no terminal debrief", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const view = play.initialize({ runId: "run:station-zero-v3:debrief:running" });
    assert.equal(view.debrief, null);
  } finally {
    store.close();
  }
});

test("default operation debrief reports exact focus and required milestones without counterfactuals", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const view = await terminalRun(play, "run:station-zero-v3:debrief:default", null);
    assert.ok(view.debrief);
    assert.equal(view.debrief.committedTurns, 20);
    assert.equal(view.debrief.terminalReason, "turn_limit");
    assert.equal(view.debrief.terminalReasonLabel, "Turn limit reached");
    assert.equal(view.debrief.requiredCompleted, 1);
    assert.equal(view.debrief.requiredTotal, 2);
    assert.deepEqual(view.debrief.focus, [{
      objectiveId: "rescue-two-civilians",
      name: "Extract two civilians",
      turns: 20,
      totalTurns: 20,
    }]);
    assert.equal(view.debrief.objectives.length, 2);
    const civilians = view.debrief.objectives.find((entry) => entry.objectiveId === "rescue-two-civilians")!;
    assert.equal(civilians.finalProgress, 1);
    assert.equal(civilians.target, 2);
    assert.equal(civilians.firstProgressTurn, 10);
    assert.equal(civilians.completedTurn, null);
    const survival = view.debrief.objectives.find((entry) => entry.objectiveId === "rescue-team-survives")!;
    assert.equal(survival.finalProgress, 1);
    assert.equal(survival.finalStatus, "completed");
    assert.equal(survival.firstProgressTurn, 10);
    assert.equal(survival.completedTurn, 10);
    assert.equal(JSON.stringify(view.debrief).includes("recover-research-core"), false);
    assert.equal(JSON.stringify(view.debrief).includes("hive-alpha"), false);
  } finally {
    store.close();
  }
});

test("Recover operation debrief exposes selected focus without claiming required progress", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const view = await terminalRun(play, "run:station-zero-v3:debrief:recover", recoverOrder);
    assert.ok(view.debrief);
    assert.equal(view.outcomes.rescue, "failure");
    assert.equal(view.debrief.requiredCompleted, 0);
    assert.deepEqual(view.debrief.focus, [{
      objectiveId: "recover-research-core",
      name: "Recover the Research Core",
      turns: 20,
      totalTurns: 20,
    }]);
    assert.deepEqual(view.debrief.objectives.map((entry) => entry.objectiveId), [
      "rescue-two-civilians",
      "rescue-team-survives",
      "recover-research-core",
    ]);
    assert.ok(view.debrief.objectives.every((entry) => entry.finalProgress === 0));
    assert.ok(view.debrief.objectives.every((entry) => entry.firstProgressTurn === null));
    assert.ok(view.debrief.objectives.every((entry) => entry.completedTurn === null));
    assert.equal(JSON.stringify(view.debrief).includes("hive-alpha"), false);
    assert.equal(JSON.stringify(view.debrief).includes("pirate-captain-veyra"), false);
  } finally {
    store.close();
  }
});

test("operation debrief is reconstructed identically after store reopen", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-v3-debrief-reopen-"));
  const path = join(directory, "station-zero.sqlite3");
  const runId = "run:station-zero-v3:debrief:reopen";
  let expected;
  const firstStore = new StationZeroV3Store(path);
  try {
    const play = new StationZeroV3PlayService(firstStore);
    expected = (await terminalRun(play, runId, recoverOrder)).debrief;
    assert.ok(expected);
  } finally {
    firstStore.close();
  }
  const reopened = new StationZeroV3Store(path);
  try {
    const play = new StationZeroV3PlayService(reopened);
    const actual = play.resume(runId).debrief;
    assert.deepEqual(actual, expected);
  } finally {
    reopened.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
