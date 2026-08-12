import assert from "node:assert/strict";
import test from "node:test";

import { StationZeroV3PlayService, StationZeroV3Store } from "../src/station-zero-v3/index.ts";
// @ts-expect-error Browser module intentionally has no Node declaration.
import { renderStationZeroV3App } from "../web-v3/render.js";

test("v3 browser renderer exposes strategic controls and sealed enemy plans without hidden actions", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:web-render";
    play.initialize({ runId });
    const generated = await play.generatePreview(runId);
    const html = renderStationZeroV3App({
      view: generated.view,
      catalog: play.catalog(),
      runs: play.listRuns(),
      busy: null,
      error: null,
    });
    assert.match(html, /Commander Order/);
    assert.match(html, /Generate team plan/);
    assert.match(html, /Commit simultaneous Turn/);
    assert.equal((html.match(/data-testid="rescue-intent"/g) ?? []).length, 3);
    assert.equal((html.match(/data-testid="rescue-responsibility"/g) ?? []).length, 1);
    assert.match(html, /Search civilian sector: med-ward/);
    assert.doesNotMatch(html, /civilian-kade/);
    assert.equal((html.match(/data-testid="sealed-enemy-plan"/g) ?? []).length, 2);
    assert.doesNotMatch(html, /Captain Veyra/);
    assert.doesNotMatch(html, /swarm-drone-one|swarm-stalker-kappa/);
    assert.match(html, /Operational map/);
  } finally {
    store.close();
  }
});

test("v3 browser renderer shows bounded aftermath and asymmetric terminal outcomes", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:web-terminal";
    let view = play.initialize({ runId });
    while (view.run.status === "running") {
      const generated = await play.generatePreview(runId);
      view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    }
    const html = renderStationZeroV3App({ view, catalog: play.catalog(), runs: play.listRuns(), busy: null, error: null });
    assert.match(html, /data-testid="terminal-summary"/);
    assert.match(html, /Encounter complete/);
    assert.match(html, /Pirate/);
    assert.match(html, /Swarm/);
    assert.match(html, /data-testid="aftermath"/);
    assert.doesNotMatch(html, /factionPlans/);
  } finally {
    store.close();
  }
});
