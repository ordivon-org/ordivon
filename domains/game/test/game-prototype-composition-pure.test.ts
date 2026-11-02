import assert from "node:assert/strict";
import test from "node:test";
import {
  projectPrototypeCompositions,
  type CompositionPlan,
  type CompositionSourceIndex,
} from "../src/prototype-composition.ts";

const source = { id: "godot-native-resource-composition", title: "Native Godot", url: "https://godotengine.org", currentness: "CURRENT_WITH_VERSION", nativeEngines: ["godot"] as const };
const plan: CompositionPlan = {
  recipes: [{
    id: "native",
    name: "Native",
    engine: "godot",
    intent: "Godot Resource and Scene composition",
    standing: "NATIVE_COMPONENT_EXECUTED",
    currentConsumer: "examples/native-composition/assert.gd",
    components: [{ role: "rule", sourceRef: source.id, integrationSeam: "Godot Resource", standing: "EXECUTED_NATIVE", required: true }],
    explicitGaps: ["No exported game"],
    nextFalsifier: "Native scene state and effect consumer",
  }],
};
const index: CompositionSourceIndex = { sources: [source] };

test("pure projection resolves source, preserves input identity and filters without file/CLI effects", () => {
  const before = JSON.stringify([plan, index]);
  const items = projectPrototypeCompositions(plan, index, { engine: "GoDot" }).items;
  assert.equal(items.length, 1);
  assert.equal(items[0]?.components[0]?.provider.title, source.title);
  assert.equal(items[0]?.standing, "NATIVE_COMPONENT_EXECUTED");
  assert.equal(projectPrototypeCompositions(plan, index, { id: "not-native" }).items.length, 0);
  assert.equal(JSON.stringify([plan, index]), before);
});

test("pure source relation fails on ungrounded provider or engine mismatch", () => {
  assert.throws(
    () => projectPrototypeCompositions(plan, { sources: [] }),
    /unknown source reference/,
  );
  assert.throws(
    () => projectPrototypeCompositions(plan, { sources: [source, source] }),
    /duplicate Game source/,
  );
  const changed: CompositionPlan = {
    recipes: [{ ...plan.recipes[0]!, engine: "bevy" }],
  };
  assert.throws(
    () => projectPrototypeCompositions(changed, index),
    /provider godot-native-resource-composition supports godot, not bevy/,
  );
});


test("pure projection rejects unconsumed execution claims without fabricating an engine proof", () => {
  const executedWithoutConsumer: CompositionPlan = {
    recipes: [{ ...plan.recipes[0]!, currentConsumer: "" }],
  };
  assert.throws(() => projectPrototypeCompositions(executedWithoutConsumer, index), /missing named consumer/);

  const unproven: CompositionPlan = {
    recipes: [{ ...plan.recipes[0]!, components: [
      { ...plan.recipes[0]!.components[0]!, standing: "SOURCE_DOCUMENTED" },
    ] }],
  };
  assert.throws(() => projectPrototypeCompositions(unproven, index), /without an executed component/);

  const duplicated: CompositionPlan = { recipes: [plan.recipes[0]!, plan.recipes[0]!] };
  assert.throws(() => projectPrototypeCompositions(duplicated, index), /duplicate Game composition/);
});

test("provider compatibility is declared by native interface, not ID naming", () => {
  const renamedProvider: CompositionSourceIndex = {
    sources: [{ ...source, id: "bevy-looking-provider", nativeEngines: ["godot"] }],
  };
  const renamedPlan: CompositionPlan = {
    recipes: [{
      ...plan.recipes[0]!,
      components: [{
        ...plan.recipes[0]!.components[0]!,
        sourceRef: "bevy-looking-provider",
      }],
    }],
  };
  assert.equal(projectPrototypeCompositions(renamedPlan, renamedProvider).items.length, 1);
  assert.throws(
    () => projectPrototypeCompositions({ recipes: [{ ...renamedPlan.recipes[0]!, engine: "bevy" }] }, renamedProvider),
    /provider bevy-looking-provider supports godot, not bevy/,
  );
});

test("executed slot in candidate requires a real scoped consumer", () => {
  const recipe = plan.recipes[0]!;
  assert.throws(
    () => projectPrototypeCompositions({
      recipes: [{
        ...recipe,
        standing: "DESIGN_CANDIDATE",
        components: [{ ...recipe.components[0]!, currentConsumer: " " }],
      }],
    }, index),
    /executed candidate slot missing scoped consumer/,
  );
});
