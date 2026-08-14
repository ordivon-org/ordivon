import assert from "node:assert/strict";
import test from "node:test";

import {
  createStationZeroV3TemporalExpressions,
  stationZeroV3BoundedFactSummary,
  stationZeroV3ExpressionAssets,
  StationZeroV3PlayService,
  StationZeroV3Store,
  type StationZeroFact,
} from "../src/station-zero-v3/index.ts";

test("Aseprite metadata binds exact idle/move/impact sprite frames", () => {
  const assets = stationZeroV3ExpressionAssets();
  assert.equal(assets.rescueSprite.src, "/v3/assets/rescue-expression.png");
  assert.deepEqual(
    [assets.rescueSprite.sheetWidth, assets.rescueSprite.sheetHeight],
    [72, 24],
  );
  assert.deepEqual(
    [assets.rescueSprite.idle.x, assets.rescueSprite.move.x, assets.rescueSprite.impact.x],
    [0, 24, 48],
  );
  assert.deepEqual(
    [assets.rescueSprite.idle.width, assets.rescueSprite.move.width, assets.rescueSprite.impact.width],
    [24, 24, 24],
  );
  assert.equal(assets.systemSignalSrc, "/v3/assets/system-signal.svg");
  assert.equal(assets.hazardSignalSrc, "/v3/assets/hazard-signal.svg");
});

test("committed Turn expressions preserve hidden topology while surfacing visible movement", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:temporal-hidden-boundary";
    play.initialize({ runId });
    const generated = await play.generatePreview(runId);
    const view = (await play.commitPreview(runId, generated.preview.previewId)).view;
    assert.ok(view.aftermath);

    const movements = view.aftermath.expressions.filter((entry) => entry.kind === "move");
    assert.equal(movements.length, 5);
    assert.deepEqual(movements.map((entry) => entry.sequence), [0, 1, 2, 3, 4]);

    const chen = movements.find((entry) => entry.label === "Security Chen");
    assert.ok(chen?.map?.from && chen.map.to);
    assert.equal(chen.visual?.kind, "sprite");
    if (chen.visual?.kind === "sprite") assert.equal(chen.visual.frame.x, 24);

    const nyx = movements.find((entry) => entry.label === "Hacker Nyx");
    assert.ok(nyx);
    assert.match(nyx.detail, /Entered Junction Machinery from an uncharted sector/);
    assert.equal(nyx.map?.from, null);
    assert.equal(nyx.map?.to, null);
    assert.ok(nyx.map?.point);
    assert.equal(nyx.visual, null);

    const aftermath = JSON.stringify(view.aftermath);
    assert.doesNotMatch(aftermath, /Storage Floor|storage-floor|Cargo Crates|crate-cover/);
    assert.match(aftermath, /an uncharted sector/);
    assert.ok(view.aftermath.visibleFacts.some((fact) => fact.summary === "Hacker Nyx moved from an uncharted sector to Junction Machinery."));
  } finally {
    store.close();
  }
});

test("temporal compiler binds system/hazard vectors and clips hidden passage identity", async () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:temporal-vector-bindings";
    const initial = play.initialize({ runId });
    const initialState = store.loadState(runId);

    const hiddenPassageFact = {
      factId: "fact:test:hidden-passage",
      kind: "passage_changed",
      passageId: "passage:junction-storage",
      before: "open",
      after: "closed",
    } satisfies StationZeroFact;
    const hiddenPassageSummary = stationZeroV3BoundedFactSummary(initialState, hiddenPassageFact, initial.map);
    assert.equal(hiddenPassageSummary, "Junction Machinery access changed from open to closed.");
    assert.doesNotMatch(hiddenPassageSummary, /storage/i);
    const hiddenPassageExpression = createStationZeroV3TemporalExpressions(initialState, [hiddenPassageFact], initial.map)[0];
    assert.ok(hiddenPassageExpression?.map?.point);
    assert.equal(hiddenPassageExpression?.map?.points.length, 0);
    assert.doesNotMatch(JSON.stringify(hiddenPassageExpression), /storage|passage:junction-storage/i);

    const systemFact = {
      factId: "fact:test:system",
      kind: "system_changed",
      systemId: "power-grid",
      integrityBefore: 0.72,
      integrityAfter: 0.8,
      poweredBefore: true,
      poweredAfter: true,
    } satisfies StationZeroFact;
    const systemExpression = createStationZeroV3TemporalExpressions(initialState, [systemFact], initial.map)[0];
    assert.equal(systemExpression?.kind, "system");
    assert.deepEqual(systemExpression?.visual, { kind: "icon", src: "/v3/assets/system-signal.svg" });

    play.saveOrder(runId, { commanderDirectiveId: "scan-reactor" });
    const generated = await play.generatePreview(runId);
    const after = (await play.commitPreview(runId, generated.preview.previewId)).view;
    const afterState = store.loadState(runId);
    const knownNyx = afterState.factionKnowledge.rescue.knownActors["pirate-hacker-nyx"];
    assert.ok(knownNyx);
    assert.equal(knownNyx.lastKnownZoneId, "junction-cover");
    const staleContactState = structuredClone(afterState);
    staleContactState.actors["pirate-hacker-nyx"]!.position.zoneId = "storage-floor";
    const staleHealthFact = {
      factId: "fact:test:stale-contact-health",
      kind: "actor_health_changed",
      actorId: "pirate-hacker-nyx",
      before: 80,
      after: 65,
      causes: ["fact:test:stale-contact-damage"],
    } satisfies StationZeroFact;
    const staleHealthExpression = createStationZeroV3TemporalExpressions(staleContactState, [staleHealthFact], after.map)[0];
    const knownNyxZone = after.map.zones.find((zone) => zone.zoneId === knownNyx.lastKnownZoneId)!;
    assert.deepEqual(staleHealthExpression?.map?.point, {
      x: knownNyxZone.geometry.x + knownNyxZone.geometry.width / 2,
      y: knownNyxZone.geometry.y + knownNyxZone.geometry.height / 2,
    });
    assert.doesNotMatch(JSON.stringify(staleHealthExpression), /storage-floor|Storage Floor/);

    const hazardFact = {
      factId: "fact:test:hazard",
      kind: "hazard_changed",
      hazardId: "reactor-instability",
      severityBefore: 2,
      severityAfter: 1,
      contained: false,
    } satisfies StationZeroFact;
    const hazardExpression = createStationZeroV3TemporalExpressions(afterState, [hazardFact], after.map)[0];
    assert.equal(hazardExpression?.kind, "hazard");
    assert.deepEqual(hazardExpression?.visual, { kind: "icon", src: "/v3/assets/hazard-signal.svg" });
    assert.equal(hazardExpression?.tone, "positive");
  } finally {
    store.close();
  }
});


test("temporal compiler suppresses only exact damage-health duplicates", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const runId = "run:station-zero-v3:temporal-dedup";
    const view = play.initialize({ runId });
    const state = store.loadState(runId);
    const facts: StationZeroFact[] = [
      {
        factId: "fact:test:damage",
        kind: "damage_dealt",
        sourceActorId: "pirate-raider-holt",
        targetActorId: "security-chen",
        amount: 20,
        damageType: "kinetic",
      },
      {
        factId: "fact:test:damage-health",
        kind: "actor_health_changed",
        actorId: "security-chen",
        before: 110,
        after: 90,
      },
      {
        factId: "fact:test:healing",
        kind: "actor_health_changed",
        actorId: "security-chen",
        before: 90,
        after: 100,
      },
    ];
    const expressions = createStationZeroV3TemporalExpressions(state, facts, view.map);
    assert.deepEqual(expressions.map((entry) => entry.kind), ["impact", "health"]);
    assert.equal(expressions[0]?.detail, "Unknown contact dealt 20 damage");
    assert.equal(expressions[1]?.detail, "Health 90 → 100");
  } finally {
    store.close();
  }
});
