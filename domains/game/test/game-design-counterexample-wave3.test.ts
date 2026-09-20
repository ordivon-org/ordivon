import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const kb = JSON.parse(readFileSync(new URL("../standards/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;
const library = JSON.parse(readFileSync(new URL("../standards/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const memory = JSON.parse(readFileSync(new URL("../standards/game_design_counterexample_memory_r1.json", import.meta.url), "utf8")) as any;

test("wave 3 adds social, economy and procedural-system primary evidence", () => {
  const ids = new Set(kb.sources.map((item: any) => item.id));
  for (const id of [
    "unknownworlds-subnautica-multiplayer-2015",
    "blizzard-overwatch-role-queue-2019",
    "blizzard-overwatch-5v5-6v6-2024",
    "blizzard-overwatch-leavers-2023",
    "bungie-d2-unstable-cores-2025",
    "bungie-d2-legendary-shards-2023",
    "factorio-fff-390",
    "factorio-fff-258",
  ]) assert.ok(ids.has(id), `missing ${id}`);
});

test("wave 3 adds experiences without changing Experience schema", () => {
  const ids = new Set(library.experiences.map((item: any) => item.id));
  for (const id of [
    "exp.subnautica.multiplayer-late-addition-crosscuts-architecture",
    "exp.overwatch.role-flexibility-externalized-social-negotiation",
    "exp.overwatch.role-queue-solved-composition-created-population-bottleneck",
    "exp.overwatch.leaver-xp-penalty-missed-target",
    "exp.destiny2.unstable-cores-friction-without-buildcraft",
    "exp.destiny2.legendary-shards-economy-baggage",
    "exp.factorio.noise-procedure-abstraction-removed",
    "exp.factorio.autoplace-fragmented-generator-to-unified-expression",
  ]) assert.ok(ids.has(id), `missing ${id}`);
});

test("wave 3 adds contextual counterexamples rather than multiplayer/economy/procgen bans", () => {
  const ids = new Set(memory.counterexamples.map((item: any) => item.id));
  for (const id of [
    "counterexample.subnautica.multiplayer-is-not-necessarily-a-bolt-on-feature",
    "counterexample.overwatch.social-freedom-can-externalize-negotiation-cost",
    "counterexample.overwatch.structural-fix-can-create-population-bottleneck",
    "counterexample.overwatch.weak-penalty-can-miss-intent-and-hit-incidental-users",
    "counterexample.destiny2.currency-friction-does-not-imply-interesting-choice",
    "counterexample.destiny2.universal-currency-can-become-economy-baggage",
    "counterexample.factorio.smarter-procgen-abstraction-can-lose-to-simpler-representation",
    "counterexample.factorio.fragmented-procgen-representations-can-block-control",
  ]) assert.ok(ids.has(id), `missing ${id}`);
  assert.ok(memory.counterexamples.length >= 35);
  for (const item of memory.counterexamples) {
    assert.equal(item.canBlockNovelCombination, false);
    assert.equal(item.humanOutcomeEstablished, false);
  }
});

test("wave 3 keeps the exact existing counterexample record shape", () => {
  const allowed = [
    "id", "kind", "referenceGames", "assumption", "failureSignal", "context", "revisionOrSalvage",
    "transferBoundary", "falseUniversalizations", "cheapDiscriminator", "experienceRefs", "sourceRefs",
    "authority", "humanOutcomeEstablished", "canBlockNovelCombination",
  ].sort();
  for (const item of memory.counterexamples) assert.deepEqual(Object.keys(item).sort(), allowed, item.id);
});
