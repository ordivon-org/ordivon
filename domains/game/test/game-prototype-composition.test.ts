import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";
import { queryPrototypeCompositions } from "../scripts/prototype-composition-query.ts";

test("composition candidates resolve genuine external source evidence and expose execution limits", () => {
  const result = queryPrototypeCompositions();
  assert.equal(result.verifiedGameProducts, 0);
  assert.equal(result.items.length, 4);
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
  const other = result.items.filter((recipe) => recipe.id !== native?.id && recipe.id !== bevy?.id);
  assert.ok(other.every((recipe) => recipe.standing === "DESIGN_CANDIDATE"));
  // A native subcomponent can be executed without qualifying a whole game.
  for (const recipe of result.items.filter((recipe) => recipe.id !== native?.id)) {
    for (const component of recipe.components) {
      if (recipe.id === "dialogue-led-exploration" && component.role === "dialogue") {
        assert.equal(component.standing, "EXECUTED_NATIVE");
      } else {
        assert.equal(component.standing, "SOURCE_DOCUMENTED", recipe.id + "/" + component.role);
      }
    }
  }
  const plan = JSON.parse(readFileSync(new URL("../planning/prototype-composition-candidates-r1.json", import.meta.url), "utf8"));
  const dialogue = plan.recipes.find((recipe: any) => recipe.id === "dialogue-led-exploration");
  assert.equal(dialogue.standing, "DESIGN_CANDIDATE");
  const nativeDialogue = dialogue.components.find((component: any) => component.role === "dialogue");
  assert.equal(nativeDialogue.standing, "EXECUTED_NATIVE");
  assert.ok(existsSync(new URL("../" + nativeDialogue.currentConsumer, import.meta.url)));
});

test("source-backed candidate selection preserves engine constraints and does not invent implementation state", () => {
  const godot = queryPrototypeCompositions({ engine: "GoDot" });
  const bevy = queryPrototypeCompositions({ engine: "bevy" });
  assert.equal(godot.items.length, 3);
  assert.equal(bevy.items.length, 1);
  assert.ok(godot.items.every((item) => item.engine === "godot"));
  assert.ok(bevy.items.every((item) => item.engine === "bevy"));
  assert.equal(queryPrototypeCompositions({ id: "not-a-game" }).items.length, 0);
  assert.ok(queryPrototypeCompositions({ id: "native-action-loop" }).items.length === 1);
  const plan = JSON.parse(readFileSync(new URL("../planning/prototype-composition-candidates-r1.json", import.meta.url), "utf8"));
  assert.equal(plan.authority, "ADVISORY_SOURCE_BOUND_NOT_A_GAME_PRODUCT");
  assert.ok(plan.recipes.every((recipe: any) => recipe.nextFalsifier.length > 10));
});
