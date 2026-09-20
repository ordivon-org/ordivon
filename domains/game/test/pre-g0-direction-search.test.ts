import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const search = readFileSync(new URL("../docs/GAME_PRE_G0_DIRECTION_SEARCH.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");

test("old Pre-G0 direction search remains historical apparatus, not current creative authority", () => {
  assert.match(search, /HISTORICAL\/SUPPORTING RESEARCH/);
  assert.match(readme, /GAME_PRE_G0_DIRECTION_SEARCH\.md/);
  assert.match(readme, /Creative composition defaults open/);
});

test("historical direction search preserves its broad mechanism vocabulary for reuse", () => {
  for (const dimension of ["PlayerFantasy", "CoreVerbs / Cadence", "ControlTopology", "WorldForm", "InformationContract", "ContentSource", "SocialForm", "AgentParticipationProfile"]) assert.match(search, new RegExp(dimension.replace("/", "\\/")));
  for (let index = 1; index <= 16; index += 1) assert.match(search, new RegExp(`D${String(index).padStart(2, "0")}`));
});

test("its useful cheaper-mechanism and burden distinctions remain available as experience", () => {
  assert.match(search, /replacing Agent cognition with the cheapest adequate baseline/);
  assert.match(search, /GenerationNeed != AgentNeed/);
  assert.match(search, /TechnicalMaturity != PlayerValue evidence/);
});
