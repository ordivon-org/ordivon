import assert from "node:assert/strict";
import test from "node:test";

import { StationZeroV3PlayService, StationZeroV3Store } from "../src/station-zero-v3/index.ts";

const recoverOrder = {
  primaryObjectiveId: "recover-research-core" as const,
  posture: "aggressive" as const,
  formation: "cohesive" as const,
  lootPolicy: "opportunistic" as const,
};

function impact(view: ReturnType<StationZeroV3PlayService["initialize"]>, objectiveId: string) {
  const row = view.experience.preview?.planImpact.find((entry) => entry.objectiveId === objectiveId);
  assert.ok(row, `missing Plan Impact row for ${objectiveId}`);
  return row;
}

test("default Rescue preview exposes direct required-objective work without forecasting outcomes", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:plan-impact:rescue";
    play.initialize({ runId });
    const generated = await play.generatePreview(runId);
    const rescue = impact(generated.view, "rescue-two-civilians");
    assert.equal(rescue.mandatory, true);
    assert.equal(rescue.selectedPriority, true);
    assert.equal(rescue.impact, "direct");
    assert.deepEqual(rescue.actorIds, ["medic-reyes"]);
    assert.deepEqual(rescue.actorNames, ["Medic Reyes"]);
    assert.equal(impact(generated.view, "rescue-team-survives").impact, "none");
  } finally {
    store.close();
  }
});

test("Recover Core preview distinguishes no action, route positioning, and direct objective action", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:plan-impact:recover";
    let view = play.initialize({ runId });

    play.saveOrder(runId, recoverOrder);
    let generated = await play.generatePreview(runId);
    assert.equal(impact(generated.view, "recover-research-core").selectedPriority, true);
    assert.equal(impact(generated.view, "recover-research-core").impact, "none");
    assert.equal(impact(generated.view, "rescue-two-civilians").impact, "none");
    view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    assert.equal(view.run.turn, 1);

    play.saveOrder(runId, recoverOrder);
    generated = await play.generatePreview(runId);
    const positioning = impact(generated.view, "recover-research-core");
    assert.equal(positioning.impact, "positioning");
    assert.deepEqual(positioning.actorIds, ["engineer-imani"]);
    view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    assert.equal(view.run.turn, 2);

    play.saveOrder(runId, recoverOrder);
    generated = await play.generatePreview(runId);
    const direct = impact(generated.view, "recover-research-core");
    assert.equal(direct.impact, "direct");
    assert.deepEqual(direct.actorIds, ["engineer-imani"]);
  } finally {
    store.close();
  }
});
