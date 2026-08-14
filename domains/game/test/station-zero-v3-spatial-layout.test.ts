import assert from "node:assert/strict";
import test from "node:test";

import {
  assertStationZeroV3SpatialLayout,
  createStationZeroV3Genesis,
  stationZeroV3SpatialLayout,
  StationZeroV3PlayService,
  StationZeroV3Store,
} from "../src/station-zero-v3/index.ts";

test("Tiled spatial layout is a complete non-authoritative geometry projection of Genesis topology", () => {
  const state = createStationZeroV3Genesis();
  const layout = stationZeroV3SpatialLayout();
  assert.doesNotThrow(() => assertStationZeroV3SpatialLayout(layout, state));
  assert.equal(Object.keys(layout.zones).length, 20);
  assert.equal(Object.keys(layout.passages).length, 20);
  assert.match(layout.layoutDigest, /^[a-f0-9]{64}$/);

  const tampered = structuredClone(layout);
  tampered.passages["passage:deck-reactor"]!.zoneBId = "maintenance-entry";
  assert.throws(
    () => assertStationZeroV3SpatialLayout(tampered, state),
    /endpoints diverge from World authority/,
  );
});

test("player spatial projection exposes connected known geometry and masked frontier without hidden topology identities", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const view = play.initialize({ runId: "run:station-zero-v3:spatial-projection" });
    assert.deepEqual(view.map.zones.map((zone) => zone.zoneId).sort(), [
      "command-deck",
      "junction-console",
      "junction-cover",
      "med-console",
      "med-ward",
      "rescue-airlock",
    ]);
    assert.deepEqual(view.map.passages.map((passage) => passage.passageId).sort(), [
      "passage:deck-junction",
      "passage:junction-machinery",
      "passage:junction-med",
      "passage:med-ward",
      "passage:rescue-deck",
    ]);
    assert.equal(view.map.frontiers.length, 3);
    assert.ok(view.map.frontiers.every((frontier) => view.known.zoneIds.includes(frontier.fromZoneId)));
    assert.ok(view.map.frontiers.every((frontier) => frontier.points.length >= 2));
    assert.ok(view.map.width > 0 && view.map.height > 0);

    const projection = JSON.stringify(view.map);
    for (const hiddenZoneId of [
      "reactor-entry", "reactor-console", "storage-floor", "maintenance-entry", "comms-entry",
      "life-entry", "life-console", "life-duct", "maintenance-nest", "cargo-airlock",
    ]) {
      assert.doesNotMatch(projection, new RegExp(hiddenZoneId));
    }
    for (const hiddenPassageId of ["passage:deck-reactor", "passage:junction-storage", "passage:junction-comms"]) {
      assert.doesNotMatch(projection, new RegExp(hiddenPassageId.replaceAll(":", "\\:")));
    }
  } finally {
    store.close();
  }
});

test("spatial projection expands only after Rescue Knowledge expands", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:spatial-expansion";
    const before = play.initialize({ runId });
    assert.equal(before.map.zones.length, 6);
    assert.equal(before.map.passages.length, 5);
    assert.equal(before.map.frontiers.length, 3);

    play.saveOrder(runId, { commanderDirectiveId: "scan-reactor" });
    const generated = await play.generatePreview(runId);
    const after = (await play.commitPreview(runId, generated.preview.previewId)).view;

    assert.equal(after.run.turn, 1);
    assert.deepEqual(after.map.zones.map((zone) => zone.zoneId).sort(), [...after.known.zoneIds].sort());
    assert.ok(after.map.zones.some((zone) => zone.zoneId === "reactor-entry"));
    assert.ok(after.map.passages.some((passage) => passage.passageId === "passage:deck-reactor"));
    assert.ok(after.map.frontiers.length < before.map.frontiers.length);

    const projection = JSON.stringify(after.map);
    for (const stillHiddenZoneId of ["storage-floor", "maintenance-entry", "life-entry", "life-console", "life-duct", "maintenance-nest", "cargo-airlock"]) {
      assert.doesNotMatch(projection, new RegExp(stillHiddenZoneId));
    }
    assert.doesNotMatch(projection, /passage:junction-storage|passage:storage-maintenance|passage:maintenance-life/);
  } finally {
    store.close();
  }
});
