import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const scene = readFileSync("experiments/production-smoke-r1/godot/main.tscn", "utf8");
const harness = readFileSync("experiments/production-smoke-r1/run.ts", "utf8");
const doc = readFileSync("docs/GAME_PRODUCTION_COLD_START_R1.md", "utf8");

test("Godot production smoke persists node identity required by the current reproducibility boundary", () => {
  assert.match(scene, /\[node name="ColdStart" type="Node2D" unique_id=\d+\]/);
});

test("Godot production smoke mechanically compares two clean full exports", () => {
  assert.match(harness, /rmSync\(join\(cleanProject, "\.godot"\)/);
  assert.match(harness, /firstBuildDigest/);
  assert.match(harness, /secondBuildDigest/);
  assert.match(harness, /assert\.equal\([\s\S]*secondBuildDigest,[\s\S]*firstBuildDigest/);
  assert.match(harness, /linux_release\.x86_64/);
});

test("Godot reproducibility claim stays explicitly bounded", () => {
  assert.match(doc, /bit reproducibility only inside the declared acceptance boundary/i);
  assert.match(doc, /does \*\*not\*\* generalize/i);
  assert.match(doc, /exact historical PCK\/build artifacts remain release authority/i);
});
