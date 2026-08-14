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
    assert.match(html, /Mission intent/);
    assert.match(html, /This Turn/);
    assert.match(html, /data-testid="order-guidance"/);
    assert.match(html, /Required mission priority: locate, escort, and extract both civilians/);
    assert.match(html, /data-testid="order-contingencies"/);
    assert.doesNotMatch(html, /<details class="order-contingencies"[^>]* open/);
    assert.match(html, /Only matter when matching local opportunities arise/);
    assert.match(html, /no protection priority/);
    assert.match(html, /Generate team plan/);
    assert.match(html, /Commit simultaneous Turn/);
    assert.match(html, /data-testid="plan-impact"/);
    assert.match(html, /Mission fronts touched by admitted Rescue actions/);
    assert.match(html, /Not an outcome forecast/);
    assert.match(html, /data-objective-id="rescue-two-civilians" data-impact="direct"/);
    assert.match(html, /Direct action/);
    assert.match(html, /Medic Reyes/);
    assert.equal((html.match(/data-testid="rescue-intent"/g) ?? []).length, 3);
    assert.equal((html.match(/data-testid="rescue-responsibility"/g) ?? []).length, 1);
    assert.match(html, /Search civilian sector: med-ward/);
    assert.doesNotMatch(html, /civilian-kade/);
    assert.equal((html.match(/data-testid="sealed-enemy-plan"/g) ?? []).length, 2);
    assert.doesNotMatch(html, /Captain Veyra/);
    assert.doesNotMatch(html, /swarm-drone-one|swarm-stalker-kappa/);
    assert.match(html, /Operational map/);
    assert.match(html, /data-testid="spatial-map"/);
    assert.match(html, /6 zones · 3 uncharted access/);
    assert.match(html, /data-passage-id="passage:deck-junction"/);
    assert.doesNotMatch(html, /reactor-entry|storage-floor|maintenance-entry|comms-entry/);
    assert.doesNotMatch(html, /passage:deck-reactor|passage:junction-storage|passage:junction-comms/);
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


test("v3 browser renderer keeps temporal recap persistent but map playback one-shot", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:web-temporal";
    play.initialize({ runId });
    const generated = await play.generatePreview(runId);
    const view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    assert.ok(view.aftermath?.expressions.length);

    const staticHtml = renderStationZeroV3App({
      view,
      catalog: play.catalog(),
      runs: play.listRuns(),
      busy: null,
      error: null,
    });
    assert.match(staticHtml, /data-testid="temporal-expression-strip"/);
    assert.equal((staticHtml.match(/data-testid="temporal-expression"/g) ?? []).length, view.aftermath.expressions.length);
    assert.match(staticHtml, /data-testid="plan-review"/);
    assert.equal((staticHtml.match(/data-testid="plan-review-front"/g) ?? []).length, 2);
    assert.match(staticHtml, /Committed plan → current visible state/);
    assert.match(staticHtml, /Planned: Move to Power Console/);
    assert.match(staticHtml, /data-testid="intent-review"/);
    assert.doesNotMatch(staticHtml, /class="temporal-map-event/);
    assert.match(staticHtml, /<details><summary>Visible World facts/);
    assert.doesNotMatch(staticHtml, /<details open><summary>Visible World facts/);

    const liveHtml = renderStationZeroV3App({
      view,
      catalog: play.catalog(),
      runs: play.listRuns(),
      busy: null,
      error: null,
      expressionTurnSequence: view.aftermath.turnSequence,
    });
    assert.match(liveHtml, /expression-strip is-live/);
    assert.match(liveHtml, /class="temporal-map-event/);
    assert.match(liveHtml, /\/v3\/assets\/rescue-expression\.png/);
  } finally {
    store.close();
  }
});
