import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  STATION_ZERO_V3_SCENARIO_CASES,
  StationZeroV3PlayService,
  StationZeroV3Store,
  createStationZeroV3Genesis,
} from "../src/station-zero-v3/index.ts";
// @ts-expect-error Browser module intentionally has no Node declaration.
import { renderStationZeroV3App } from "../web-v3/render.js";

test("v3 second slice is one exact content delta rather than a generic mutation system", () => {
  assert.deepEqual(
    STATION_ZERO_V3_SCENARIO_CASES.map((entry) => entry.caseId),
    ["fixed-genesis", "junction-bottleneck"],
  );
  const baseline = createStationZeroV3Genesis("same-seed", "fixed-genesis");
  const bottleneck = createStationZeroV3Genesis("same-seed", "junction-bottleneck");
  assert.equal(baseline.zones["junction-cover"]!.capacity, 2);
  assert.equal(bottleneck.zones["junction-cover"]!.capacity, 1);

  const normalized = structuredClone(bottleneck);
  normalized.zones["junction-cover"]!.capacity = baseline.zones["junction-cover"]!.capacity;
  assert.deepEqual(normalized, baseline, "G5-P2 case must not smuggle additional World/content changes");
});

test("scenario_case_id durably binds Genesis identity and survives reopen", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-v3-case-"));
  const path = join(directory, "station-zero-v3.sqlite3");
  const runId = "run:station-zero-v3:junction-bottleneck";
  try {
    let store = new StationZeroV3Store(path);
    const created = store.createRun({ runId, scenarioCaseId: "junction-bottleneck" });
    assert.equal(created.scenarioCaseId, "junction-bottleneck");
    assert.equal(store.loadState(runId).zones["junction-cover"]!.capacity, 1);
    assert.equal(store.createRun({ runId }).scenarioCaseId, "junction-bottleneck", "omitted case must recover retained identity");
    assert.throws(
      () => store.createRun({ runId, scenarioCaseId: "fixed-genesis" }),
      /bound to another Scenario Case/,
    );
    assert.equal(store.verify(runId).verified, true);
    store.close();

    store = new StationZeroV3Store(path);
    assert.equal(store.getRun(runId).scenarioCaseId, "junction-bottleneck");
    assert.equal(store.loadState(runId).zones["junction-cover"]!.capacity, 1);
    assert.equal(store.verify(runId).verified, true);
    store.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("unsupported retained Scenario Case identity fails closed", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const runId = "run:station-zero-v3:bad-case";
    store.createRun({ runId });
    store.db.prepare("UPDATE runs SET scenario_case_id = 'invented-case' WHERE run_id = ?").run(runId);
    assert.throws(() => store.getRun(runId), /Scenario Case is invalid/);
  } finally {
    store.close();
  }
});

test("play catalog and known map make the second slice selectable and legible", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const catalog = play.catalog();
    assert.equal(catalog.defaultScenarioCaseId, "fixed-genesis");
    assert.deepEqual(catalog.cases.map((entry) => entry.caseId), ["fixed-genesis", "junction-bottleneck"]);

    const landing = renderStationZeroV3App({ view: null, catalog, runs: [], busy: null, error: null });
    assert.match(landing, /data-testid="scenario-case"/);
    assert.match(landing, /Contested Signal/);
    assert.match(landing, /Junction Bottleneck/);

    const runId = "run:station-zero-v3:case-surface";
    const view = play.initialize({ runId, scenarioCaseId: "junction-bottleneck" });
    assert.equal(view.run.scenarioCaseId, "junction-bottleneck");
    assert.equal(play.listRuns()[0]?.scenarioCaseId, "junction-bottleneck");
    const junction = view.map.zones.find((zone) => zone.zoneId === "junction-cover");
    assert.ok(junction);
    assert.equal(junction.capacity, 1);

    const html = renderStationZeroV3App({ view, catalog, runs: play.listRuns(), busy: null, error: null });
    assert.match(html, /Station Zero v3 · Junction Bottleneck/);
    assert.match(html, /data-zone-id="junction-cover"/);
    assert.match(html, /full cover · Cap 1/);
  } finally {
    store.close();
  }
});
