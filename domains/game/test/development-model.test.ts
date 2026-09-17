import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const development = readFileSync(new URL("../docs/DEVELOPMENT_MODEL.md", import.meta.url), "utf8");
const stageSkill = readFileSync(new URL("../skills/game-stage-lens/SKILL.md", import.meta.url), "utf8");
const frontHalf = readFileSync(new URL("../docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md", import.meta.url), "utf8");

test("G0-G8 survives only as optional removable stage lens", () => {
  assert.match(development, /Creative-open correction — 2026-09-18/);
  assert.match(development, /G0–G8 is no longer canonical Game process or product-stage authority/);
  assert.match(stageSkill, /optional and advisory/i);
  assert.match(stageSkill, /skip, merge, reorder, rename, loop through, or entirely ignore/i);
  assert.match(stageSkill, /must not block creative composition/i);
});

test("historical model still preserves useful form and Agent-role distinctions", () => {
  assert.match(development, /Conventional Form Profile/);
  assert.match(development, /Production Agent Profile/);
  assert.match(development, /Runtime Agent Participation Profile/);
  assert.match(development, /AgentBuiltGame != AgentGame/);
});

test("Agentic Consequence Loop remains reusable runtime-agent pattern", () => {
  assert.match(development, /OBSERVE[\s\S]*COGNIZE[\s\S]*DECIDE[\s\S]*ADMIT[\s\S]*RESOLVE[\s\S]*FEEDBACK[\s\S]*ADAPT/);
  assert.match(development, /If the Agent mostly adds latency, cost and prose/);
});

test("external-reference front half remains technique source, not only creative path", () => {
  assert.match(frontHalf, /Reference learning/);
  assert.match(frontHalf, /claim-specific evidence/i);
  assert.match(stageSkill, /not the canonical lifecycle/i);
});
