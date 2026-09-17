import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const kb = JSON.parse(readFileSync(new URL("../standards/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;
const library = JSON.parse(readFileSync(new URL("../standards/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const memory = JSON.parse(readFileSync(new URL("../standards/game_design_counterexample_memory_r1.json", import.meta.url), "utf8")) as any;

test("wave 2 adds cancelled, relaunched, rolled-back and foundation-reversal primary evidence", () => {
  const sourceIds = new Set(kb.sources.map((item: any) => item.id));
  for (const id of [
    "blizzard-overwatch-future-2023",
    "naughtydog-tlou-online-2023",
    "valve-artifact-future-2021",
    "gdc-ffxiv-realm-reborn-2014",
    "unknownworlds-belowzero-story-future-2019",
    "unknownworlds-belowzero-roadmap-2019",
    "ubisoft-r6-operation-health-2017",
    "bungie-d2-forsaken-update-2-0-2018",
  ]) assert.ok(sourceIds.has(id), `missing source ${id}`);
});

test("wave 2 adds explicit experiences for cancellation, relaunch, rewrite and live-system reversal", () => {
  const ids = new Set(library.experiences.map((item: any) => item.id));
  for (const id of [
    "exp.overwatch.old-vision-starved-live-game",
    "exp.overwatch.hero-missions-cut-to-protect-live-game",
    "exp.tlouonline.satisfying-prototype-unsustainable-operating-model",
    "exp.artifact.game-side-rework-without-sustainable-population",
    "exp.ffxiv.relaunch-instead-of-patching-failed-foundation",
    "exp.belowzero.playable-whole-story-mismatch-reset",
    "exp.belowzero.roadmap-became-feature-commitment-pressure",
    "exp.r6.health-over-content-cadence",
    "exp.destiny2.foundation-reversal-weapon-slot-ammo",
  ]) assert.ok(ids.has(id), `missing experience ${id}`);
});

test("wave 2 counterexamples attack assumptions instead of ranking failed projects", () => {
  const ids = new Set(memory.counterexamples.map((item: any) => item.id));
  for (const id of [
    "counterexample.overwatch.old-vision-can-outlive-its-premise",
    "counterexample.tlouonline.good-game-can-have-wrong-operating-model",
    "counterexample.artifact.game-side-fix-does-not-prove-viability",
    "counterexample.ffxiv.shipped-product-can-require-relaunch",
    "counterexample.belowzero.near-complete-content-can-still-need-rewrite",
    "counterexample.belowzero.roadmap-can-become-commitment-pressure",
    "counterexample.r6.content-cadence-can-yield-to-system-health",
    "counterexample.destiny2.live-foundation-can-be-reversed",
  ]) assert.ok(ids.has(id), `missing counterexample ${id}`);

  assert.ok(memory.counterexamples.length >= 27);
  for (const item of memory.counterexamples) {
    assert.equal(item.authority, "SOURCE_GROUNDED_COUNTEREXAMPLE_HYPOTHESIS");
    assert.equal(item.canBlockNovelCombination, false);
    assert.equal(item.humanOutcomeEstablished, false);
    assert.ok(item.falseUniversalizations.length >= 2);
    assert.ok(item.cheapDiscriminator.length > 0);
  }
});

test("wave 2 preserves the existing counterexample record shape rather than expanding schema", () => {
  const allowed = [
    "id", "kind", "referenceGames", "assumption", "failureSignal", "context", "revisionOrSalvage",
    "transferBoundary", "falseUniversalizations", "cheapDiscriminator", "experienceRefs", "sourceRefs",
    "authority", "humanOutcomeEstablished", "canBlockNovelCombination",
  ].sort();
  for (const item of memory.counterexamples) {
    assert.deepEqual(Object.keys(item).sort(), allowed, `${item.id} schema drift`);
  }
});
