import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const kb = JSON.parse(readFileSync(new URL("../standards/game_external_knowledge_base_r1.json", import.meta.url), "utf8")) as any;
const library = JSON.parse(readFileSync(new URL("../standards/game_mechanism_experience_library_r1.json", import.meta.url), "utf8")) as any;
const memory = JSON.parse(readFileSync(new URL("../standards/game_design_counterexample_memory_r1.json", import.meta.url), "utf8")) as any;

test("wave 4 adds AI-architecture primary developer evidence without duplicating Deus Ex", () => {
  const sourceIds = kb.sources.map((item: any) => item.id);
  assert.equal(sourceIds.filter((id: string) => id === "gdc-deus-ex-postmortem").length, 1);
  for (const id of [
    "gamedeveloper-thief-postmortem",
    "gamedeveloper-odyssey-immortals-ai-planning",
  ]) assert.ok(sourceIds.includes(id), `missing ${id}`);
});

test("wave 4 adds AI requirement, authority, modularity, pruning and pacing experiences", () => {
  const ids = new Set(library.experiences.map((item: any) => item.id));
  for (const id of [
    "exp.deusex.ai-capability-before-requirement-created-waste",
    "exp.deusex.borrowed-shooter-ai-foundation-created-patch-debt",
    "exp.thief.ai-built-before-stealth-requirements-mismatched-core",
    "exp.thief.delayed-ai-rewrite-amplified-cost",
    "exp.odyssey.planner-meta-ai-dual-authority-conflict",
    "exp.odyssey.legacy-complex-actions-preserved-coupling",
    "exp.immortals.random-action-cost-broke-planner-consistency",
    "exp.immortals.early-smart-object-pruning-lost-plan-context",
    "exp.odyssey.single-ai-pipeline-premature-convergence",
  ]) assert.ok(ids.has(id), `missing ${id}`);
});

test("wave 4 adds contextual AI architecture counterexamples rather than anti-AI rules", () => {
  const ids = new Set(memory.counterexamples.map((item: any) => item.id));
  for (const id of [
    "counterexample.deusex.ai-capability-before-requirement-can-create-waste",
    "counterexample.deusex.borrowed-ai-foundation-can-produce-patch-debt",
    "counterexample.thief.ai-built-for-wrong-gameplay-can-block-core",
    "counterexample.thief.delayed-rewrite-can-be-as-risky-as-premature-rewrite",
    "counterexample.odyssey.multiple-ai-authorities-can-fight-over-one-agent",
    "counterexample.odyssey.migration-shortcuts-can-preserve-legacy-coupling",
    "counterexample.immortals.random-variety-can-break-planner-consistency",
    "counterexample.immortals.early-pruning-can-remove-context-the-planner-needs",
    "counterexample.odyssey.one-ai-pipeline-can-be-premature-convergence",
  ]) assert.ok(ids.has(id), `missing ${id}`);

  assert.ok(memory.counterexamples.length >= 44);
  for (const item of memory.counterexamples) {
    assert.equal(item.canBlockNovelCombination, false);
    assert.equal(item.humanOutcomeEstablished, false);
    assert.ok(item.falseUniversalizations.length >= 2);
    assert.ok(item.cheapDiscriminator.length > 0);
  }
});

test("wave 4 keeps the exact existing counterexample record shape", () => {
  const allowed = [
    "id", "kind", "referenceGames", "assumption", "failureSignal", "context", "revisionOrSalvage",
    "transferBoundary", "falseUniversalizations", "cheapDiscriminator", "experienceRefs", "sourceRefs",
    "authority", "humanOutcomeEstablished", "canBlockNovelCombination",
  ].sort();
  for (const item of memory.counterexamples) assert.deepEqual(Object.keys(item).sort(), allowed, item.id);
});
