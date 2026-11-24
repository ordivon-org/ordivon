import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const kb = JSON.parse(readFileSync(new URL("../knowledge/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;
const library = JSON.parse(readFileSync(new URL("../knowledge/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const memory = JSON.parse(readFileSync(new URL("../knowledge/game_design_counterexample_memory_r1.json", import.meta.url), "utf8")) as any;

const unique = (items: string[]) => new Set(items).size === items.length;

test("counterexample memory is source-qualified and cannot legislate design", () => {
  assert.equal(memory.schemaVersion, 1);
  assert.equal(memory.memoryId, "ordivon-game-design-counterexample-memory-r1");
  assert.ok(memory.counterexamples.length > 0, "counterexample retrieval requires at least one recorded failure");
  assert.ok(memory.counterexamples.every((item: any) => item.referenceGames.length > 0 && item.referenceGames.every((name: string) => name.trim().length > 0)));
  assert.equal(memory.policy.failureIsUniversalLaw, false);
  assert.equal(memory.policy.canBlockNovelCombination, false);
  assert.equal(memory.policy.recommendationAuthority, "NONE");
});

function qualifyCounterexamples(records: any[]): void {
  const experienceIds = new Set(library.experiences.map((item: any) => item.id));
  const sourceIds = new Set(kb.sources.map((item: any) => "kb:" + item.id));
  assert.ok(unique(records.map((item) => item.id)), "duplicate Counterexample IDs");
  for (const item of records) {
    for (const key of ["assumption", "failureSignal", "context", "revisionOrSalvage", "transferBoundary", "cheapDiscriminator"]) {
      assert.ok(item[key].length > 0, item.id + " " + key);
    }
    assert.ok(item.falseUniversalizations.length >= 2, item.id + " universalization traps");
    assert.ok(item.experienceRefs.length >= 1, item.id + " experience refs");
    assert.ok(item.sourceRefs.length >= 1, item.id + " source refs");
    for (const ref of item.experienceRefs) assert.ok(experienceIds.has(ref), item.id + " missing Experience " + ref);
    for (const ref of item.sourceRefs) assert.ok(sourceIds.has(ref), item.id + " missing source " + ref);
    assert.equal(item.authority, "SOURCE_GROUNDED_COUNTEREXAMPLE_HYPOTHESIS", item.id + " authority");
    assert.equal(item.humanOutcomeEstablished, false, item.id + " cannot mint Human evidence");
    assert.equal(item.canBlockNovelCombination, false, item.id + " cannot veto");
  }
}

test("every counterexample carries context, failure evidence and closed sources", () => {
  qualifyCounterexamples(memory.counterexamples);
});

test("one grounded counterexample qualifies; duplicate, orphan and authority escalation fail", () => {
  const sample = memory.counterexamples[0];
  assert.ok(sample);
  qualifyCounterexamples([sample]);
  assert.throws(() => qualifyCounterexamples([sample, sample]), /duplicate Counterexample IDs/);
  assert.throws(() => qualifyCounterexamples([{...sample, experienceRefs: ["not-an-experience"]}]), /missing Experience/);
  assert.throws(() => qualifyCounterexamples([{...sample, sourceRefs: ["kb:not-a-source"]}]), /missing source/);
  assert.throws(() => qualifyCounterexamples([{...sample, canBlockNovelCombination: true}]), /cannot veto/);
});

test("new failure mining adds first-party Factorio, Blizzard and classic postmortem evidence", () => {
  const ids = new Set(kb.sources.map((item: any) => item.id));
  for (const id of [
    "factorio-fff-331",
    "factorio-fff-342",
    "factorio-fff-351",
    "factorio-fff-363",
    "gdc-diablo3-making",
    "gdc-diablo3-redemption",
    "gdc-deus-ex-postmortem",
    "gdc-psychonauts2-postmortem",
  ]) assert.ok(ids.has(id), `missing ${id}`);
});

test("Experience library expands with explicit rejected, removed and redesigned cases", () => {
  const ids = new Set(library.experiences.map((item: any) => item.id));
  for (const id of [
    "exp.factorio.campaign-mimicry-constrained-core",
    "exp.factorio.demo-goal-success-product-mismatch",
    "exp.factorio.strict-prevention-to-fast-recovery",
    "exp.factorio.gui-duplication-and-nested-tabs",
    "exp.factorio.visual-salience-context-failure",
    "exp.diablo3.auction-house-undermined-loot-loop",
    "exp.deusex.preproduction-inventory-became-cutting-debt",
    "exp.psychonauts2.constraint-expanded-design-space",
  ]) assert.ok(ids.has(id), `missing ${id}`);
});


test("counterexamples are registered as reusable Game LEGO, not a domain law", () => {
  const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  const plan = JSON.parse(readFileSync(new URL("../planning/lego-plan-r1.json", import.meta.url), "utf8")) as any;
  const node = plan.nodes.find((x: any) => x.id === "G04");
  assert.ok(node);
  assert.match(readme, /knowledge:counterexamples/);
  assert.match(project, /knowledge\/game_design_counterexample_memory_r1\.json/);
  assert.ok(node.evidence.includes("knowledge/game_design_counterexample_memory_r1.json"));
  assert.match(node.behavioralContract, /blacklist|recommendation/i);
  assert.equal(plan.nodes.some((x: any) => x.kind === "product"), false);
});
