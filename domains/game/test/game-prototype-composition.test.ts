import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";
import { queryPrototypeCompositions } from "../scripts/prototype-composition-query.ts";

test("composition candidates resolve genuine external source evidence and expose execution limits", () => {
  const result = queryPrototypeCompositions();
  assert.equal(result.verifiedGameProducts, 0);
  assert.equal(result.items.length, 7);
  const ids = result.items.map((recipe) => recipe.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const recipe of result.items) {
    assert.ok(recipe.components.length >= 2, recipe.id);
    assert.ok(recipe.explicitGaps.length, recipe.id);
    for (const component of recipe.components) {
      assert.match(component.provider.url, /^https:\/\//, component.sourceRef);
      assert.ok(component.integrationSeam.length);
    }
  }
  const native = result.items.find((recipe) => recipe.id === "native-action-loop");
  assert.equal(native?.standing, "NATIVE_SUBSET_EXECUTED");
  assert.ok(native?.currentConsumer);
  assert.ok(existsSync(new URL("../" + native.currentConsumer, import.meta.url)));
  const bevy = result.items.find((recipe) => recipe.id === "rust-ecs-sandbox");
  assert.equal(bevy?.standing, "NATIVE_SOURCE_COMPILED");
  assert.ok(bevy?.currentConsumer);
  assert.ok(existsSync(new URL("../" + bevy.currentConsumer, import.meta.url)));
  const encounter = result.items.find((recipe) => recipe.id === "room-encounter");
  const avatar = result.items.find((recipe) => recipe.id === "kenney-avatar-appearance");
  assert.equal(encounter?.standing, "NATIVE_SUBSET_EXECUTED");
  assert.equal(avatar?.standing, "NATIVE_COMPONENT_EXECUTED");
  assert.ok(encounter?.currentConsumer);
  assert.ok(avatar?.currentConsumer);
  assert.ok(existsSync(new URL("../" + encounter.currentConsumer, import.meta.url)));
  assert.ok(existsSync(new URL("../" + avatar.currentConsumer, import.meta.url)));
  assert.ok(encounter?.components.every((slot) => slot.standing === "EXECUTED_NATIVE"));
  assert.ok(avatar?.components.every((slot) => slot.standing === "EXECUTED_NATIVE"));
  assert.ok(avatar?.explicitGaps.some((gap) => gap.includes("no player input")));
  const dialogueClosure = result.items.find((recipe) => recipe.id === "branching-dialogue-gate");
  assert.equal(dialogueClosure?.standing, "NATIVE_COMPONENT_EXECUTED");
  assert.ok(dialogueClosure?.currentConsumer);
  assert.ok(existsSync(new URL("../" + dialogueClosure.currentConsumer, import.meta.url)));
  assert.deepEqual(
    dialogueClosure?.components.map((slot) => slot.role),
    ["dialogue-runtime", "game-state", "choice-ui"],
  );
  assert.ok(dialogueClosure?.components.every((slot) => slot.standing === "EXECUTED_NATIVE"));
  assert.ok(dialogueClosure?.explicitGaps.some((gap) => gap.includes("not been integrated")));
  const other = result.items.filter((recipe) =>
    !["native-action-loop", "rust-ecs-sandbox", "room-encounter", "kenney-avatar-appearance", "branching-dialogue-gate"].includes(recipe.id)
  );
  assert.ok(other.every((recipe) => recipe.standing === "DESIGN_CANDIDATE"));
  // Do not infer complete game status from one executed capability.
  const documentedRecipes = result.items.filter((recipe) =>
    recipe.standing === "DESIGN_CANDIDATE" || recipe.standing === "NATIVE_SOURCE_COMPILED"
  );
  for (const recipe of documentedRecipes) {
    for (const component of recipe.components) {
      const expected = recipe.id === "dialogue-led-exploration" && component.role === "dialogue"
        ? "EXECUTED_NATIVE" : "SOURCE_DOCUMENTED";
      assert.equal(component.standing, expected, recipe.id + "/" + component.role);
    }
  }
  const snapshot = JSON.parse(readFileSync(new URL("../planning/prototype-composition-candidates-r1.json", import.meta.url), "utf8"));
  const dialogue = snapshot.recipes.find((recipe: any) => recipe.id === "dialogue-led-exploration");
  assert.equal(dialogue.standing, "DESIGN_CANDIDATE");
  const nativeDialogue = dialogue.components.find((component: any) => component.role === "dialogue");
  assert.equal(nativeDialogue.standing, "EXECUTED_NATIVE");
  assert.ok(existsSync(new URL("../" + nativeDialogue.currentConsumer, import.meta.url)));
});

test("source-backed candidate selection preserves engine constraints and does not invent implementation state", () => {
  const godot = queryPrototypeCompositions({ engine: "GoDot" });
  const bevy = queryPrototypeCompositions({ engine: "bevy" });
  assert.equal(godot.items.length, 6);
  assert.equal(bevy.items.length, 1);
  assert.ok(godot.items.every((item) => item.engine === "godot"));
  assert.ok(bevy.items.every((item) => item.engine === "bevy"));
  assert.equal(queryPrototypeCompositions({ id: "not-a-game" }).items.length, 0);
  assert.ok(queryPrototypeCompositions({ id: "native-action-loop" }).items.length === 1);
  const plan = JSON.parse(readFileSync(new URL("../planning/prototype-composition-candidates-r1.json", import.meta.url), "utf8"));
  assert.equal(plan.authority, "ADVISORY_SOURCE_BOUND_NOT_A_GAME_PRODUCT");
  assert.ok(plan.recipes.every((recipe: any) => recipe.nextFalsifier.length > 10));
});
