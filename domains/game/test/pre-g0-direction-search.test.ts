import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const search = readFileSync(new URL("../docs/GAME_PRE_G0_DIRECTION_SEARCH.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");

test("Pre-G0 direction search is canonical research without selecting a G0 product", () => {
  assert.match(search, /^id: game\.pre-g0-direction-search$/m);
  assert.match(search, /It is not:[\s\S]*R30 Foundations[\s\S]*G0[\s\S]*Station Zero continuation[\s\S]*Casefile continuation/);
  assert.match(search, /DEVELOPMENT_MODEL\.md` remains the sole authority for G0–G8/);
  assert.match(search, /TechnicalMaturity = feasibility evidence\.[\s\S]*TechnicalMaturity != PlayerValue evidence/);
  assert.match(readme, /GAME_PRE_G0_DIRECTION_SEARCH\.md/);
  assert.match(agents, /GAME_PRE_G0_DIRECTION_SEARCH\.md/);
});

test("direction search opens a broad multidimensional candidate basis", () => {
  for (const dimension of [
    "PlayerFantasy",
    "PlayerValueHypothesis",
    "CoreVerbs / Cadence",
    "ControlTopology",
    "WorldForm",
    "InformationContract",
    "ContentSource",
    "SocialForm",
    "AgentParticipationProfile",
    "ExpressionDependency",
  ]) {
    assert.match(search, new RegExp(dimension.replace("/", "\\/")));
  }

  for (let index = 1; index <= 16; index += 1) {
    assert.match(search, new RegExp(`D${String(index).padStart(2, "0")}`));
  }

  assert.match(search, /D02 \| Legible Tactical Puzzle/);
  assert.match(search, /D11 \| Creative Construction Sandbox \/ UGC/);
  assert.match(search, /D13 \| Conversational Social Infiltration/);
  assert.match(search, /D16 \| Persistent Multi-Agent Society Sandbox/);
});

test("Agent necessity is tested against cheaper mechanisms and production burden stays vector-valued", () => {
  assert.match(search, /AgentNecessary\(candidate\)/);
  assert.match(search, /replacing Agent cognition with the cheapest adequate baseline/);
  assert.match(search, /static authored content[\s\S]*deterministic rule \/ script[\s\S]*FSM \/ utility policy[\s\S]*human-controlled role[\s\S]*model cognition/);
  assert.match(search, /GenerationNeed != AgentNeed/);
  assert.match(search, /C = repeated content authoring burden/);
  assert.match(search, /E = expression \/ art \/ animation \/ audio \/ UX burden/);
  assert.match(search, /S = systemic simulation \/ balance \/ state-space burden/);
  assert.match(search, /A = Agent\/model latency, cognition, authority and fallback burden/);
  assert.match(search, /O = online\/network\/live-operations\/provider burden/);
  assert.match(search, /V = validation\/evaluation burden/);
});

test("Foundations stay frozen unless a concrete reopen condition appears", () => {
  assert.match(search, /FoundationReopenCondition = NOT TRIGGERED/);
  assert.match(search, /Game Foundations v1 remains frozen/);
  assert.match(search, /Pre-G0 DS1 — Cheap Falsifier Battery/);
  assert.match(search, /Broadest candidate inherits the proof debts of its narrower components|broadest candidate inherits the proof debts of its narrower components/i);
});
