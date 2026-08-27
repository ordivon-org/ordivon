import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const core = readFileSync(new URL("../docs/GAME_DEVELOPMENT_CORE.md", import.meta.url), "utf8");
const cases = readFileSync(new URL("../docs/GAME_DEVELOPMENT_CASE_PRESSURE_TESTS.md", import.meta.url), "utf8");
const d5 = readFileSync(new URL("../docs/GAME_CONTENT_PROGRESSION_ARCHITECTURE.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const navigation = readFileSync(new URL("../research/core/PRODUCT-AND-DIRECTION-RESEARCH.md", import.meta.url), "utf8");

test("real development histories pressure D1-D8 without admitting another top-level responsibility", () => {
  for (const name of ["Into the Breach", "Celeste", "Outer Wilds", "Factorio", "Hades", "Roblox"]) {
    assert.match(cases, new RegExp(name));
  }
  assert.match(cases, /No case forces D9/);
  assert.match(cases, /D1-D8 survives the first real-case pressure test/);
  assert.match(cases, /Existing playable experiments|No new local playable is justified/);
});

test("D4 now represents evidence horizon instead of favoring fast micro evidence", () => {
  assert.match(core, /EvidenceHorizon/);
  assert.match(core, /interaction \| encounter \| session \| run \| campaign \| cross-session \| population\/time-window/);
  assert.match(cases, /EvidenceFrequencyBias/);
  assert.match(cases, /EvidenceLatency must be represented/);
});

test("D5 aligns possibility player capability exposure and production instead of counting content", () => {
  for (const graph of ["Possibility Graph", "Player Capability / Model Graph", "Exposure / Content Graph", "Production Graph"]) {
    assert.match(d5, new RegExp(graph.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(d5, /D5Quality.*Possibility × Capability × Exposure × Production/s);
  assert.match(d5, /ContentGrammar != ContentList/);
  assert.match(d5, /Breadth != Depth/);
});

test("progression remains carrier-relative and content units can be design experiments", () => {
  for (const carrier of ["Skill progression", "Knowledge progression", "Possibility / access progression", "Complexity progression", "World transformation progression"]) {
    assert.match(d5, new RegExp(carrier.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(cases, /ContentUnit[\s\S]*ProductContent[\s\S]*DesignExperiment/);
  assert.match(d5, /ContentUnit may be|content unit/i);
  assert.match(d5, /Harder != BiggerNumber/);
});

test("D5 preserves production-agent leverage without creating content authority", () => {
  assert.match(d5, /Generator != ContentAuthority/);
  assert.match(d5, /SearchLeverage/);
  assert.match(d5, /ProductionLeverage/);
  assert.match(d5, /do not create a content service, universal level schema, or new Foundation/i);
});

test("owner navigation and authority expose D5 and case-pressure research", () => {
  assert.match(readme, /GAME_DEVELOPMENT_CASE_PRESSURE_TESTS\.md/);
  assert.match(readme, /GAME_CONTENT_PROGRESSION_ARCHITECTURE\.md/);
  assert.match(navigation, /Development Core Case Pressure Tests/);
  assert.match(navigation, /Content \/ Progression Architecture/);
  assert.match(authority, /GAME_CONTENT_PROGRESSION_ARCHITECTURE\.md.*neither creates product stage, Foundation, content database or runtime schema/s);
});
