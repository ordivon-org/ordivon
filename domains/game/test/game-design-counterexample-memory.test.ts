import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const kb = JSON.parse(readFileSync(new URL("../standards/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;
const library = JSON.parse(readFileSync(new URL("../standards/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const memory = JSON.parse(readFileSync(new URL("../standards/game_design_counterexample_memory_r1.json", import.meta.url), "utf8")) as any;
const doc = readFileSync(new URL("../docs/GAME_DESIGN_COUNTEREXAMPLE_MEMORY_R1.md", import.meta.url), "utf8");

const unique = (items: string[]) => new Set(items).size === items.length;

test("counterexample memory is large enough to challenge success-only teardown bias", () => {
  assert.equal(memory.schemaVersion, 1);
  assert.equal(memory.memoryId, "ordivon-game-design-counterexample-memory-r1");
  assert.ok(memory.counterexamples.length >= 18);
  assert.ok(new Set(memory.counterexamples.flatMap((item: any) => item.referenceGames)).size >= 12);
  assert.equal(memory.policy.failureIsUniversalLaw, false);
  assert.equal(memory.policy.canBlockNovelCombination, false);
  assert.equal(memory.policy.recommendationAuthority, "NONE");
});

test("each counterexample carries context, failure signal, revision and a cheap discriminator", () => {
  assert.ok(unique(memory.counterexamples.map((item: any) => item.id)));
  for (const item of memory.counterexamples) {
    assert.ok(item.assumption.length > 0, `${item.id} assumption`);
    assert.ok(item.failureSignal.length > 0, `${item.id} signal`);
    assert.ok(item.context.length > 0, `${item.id} context`);
    assert.ok(item.revisionOrSalvage.length > 0, `${item.id} revision`);
    assert.ok(item.transferBoundary.length > 0, `${item.id} transfer`);
    assert.ok(item.falseUniversalizations.length >= 2, `${item.id} universalization traps`);
    assert.ok(item.cheapDiscriminator.length > 0, `${item.id} probe`);
    assert.equal(item.authority, "SOURCE_GROUNDED_COUNTEREXAMPLE_HYPOTHESIS");
    assert.equal(item.humanOutcomeEstablished, false);
    assert.equal(item.canBlockNovelCombination, false);
  }
});

test("counterexample provenance closes over Experience and external source records", () => {
  const experienceIds = new Set(library.experiences.map((item: any) => item.id));
  const sourceIds = new Set(kb.sources.map((item: any) => `kb:${item.id}`));
  for (const item of memory.counterexamples) {
    assert.ok(item.experienceRefs.length >= 1, `${item.id} experience refs`);
    assert.ok(item.sourceRefs.length >= 1, `${item.id} source refs`);
    for (const ref of item.experienceRefs) assert.ok(experienceIds.has(ref), `${item.id} missing ${ref}`);
    for (const ref of item.sourceRefs) assert.ok(sourceIds.has(ref), `${item.id} missing ${ref}`);
  }
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

test("human guide treats failure as contextual evidence rather than anti-pattern law", () => {
  assert.match(doc, /counterexample/i);
  assert.match(doc, /failure.*context/i);
  assert.match(doc, /not.*anti-pattern/i);
  assert.match(doc, /not.*ranking/i);
  assert.match(doc, /cheap.*discriminator/i);
  assert.match(doc, /rejected|removed|cancelled|redesign/i);
});


test("counterexample memory is discoverable without being embedded as Game law", () => {
  const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
  const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
  const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
  const domain = JSON.parse(readFileSync(new URL("../standards/game_domain_package_graph_r1.json", import.meta.url), "utf8")) as any;

  assert.match(readme, /GAME_DESIGN_COUNTEREXAMPLE_MEMORY_R1\.md/);
  assert.match(readme, /knowledge:counterexamples/);
  assert.match(authority, /Design Counterexample Memory/i);
  for (const path of [
    "docs/GAME_DESIGN_COUNTEREXAMPLE_MEMORY_R1.md",
    "standards/game_design_counterexample_memory_r1.json",
    "scripts/design-counterexample-query.ts",
  ]) assert.match(project, new RegExp(path.replaceAll("/", "\\/")));

  assert.equal(domain.designCounterexampleMemory.path, "standards/game_design_counterexample_memory_r1.json");
  assert.equal(domain.designCounterexampleMemory.embeddedInGraph, false);
  assert.equal(domain.designCounterexampleMemory.canBlockNovelCombination, false);
  assert.equal(domain.designCounterexampleMemory.recommendationAuthority, "NONE");
});
