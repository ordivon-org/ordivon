import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const reset = readFileSync(new URL("../docs/G_SERIES_RESET.md", import.meta.url), "utf8");
const search = readFileSync(new URL("../docs/G_SERIES_PRODUCT_SEARCH.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const server = readFileSync(new URL("../src/server.ts", import.meta.url), "utf8");
const lab = readFileSync(new URL("../web-lab/app.js", import.meta.url), "utf8");
const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

test("G-series reset owns current product stage while preserving Station Zero as reference evidence", () => {
  assert.match(reset, /^id: game\.g-series\.reset$/m);
  assert.match(reset, /Station Zero[\s\S]*reference experiment/);
  assert.match(reset, /G0 Define \| \*\*reopened\*\*/);
  assert.match(reset, /G1 Preproduction \/ core design \| \*\*reopened\*\*/);
  assert.match(reset, /G5 Production \| not currently admitted/);
  assert.match(reset, /delight;[\s\S]*attachment;[\s\S]*desire to replay/);
  assert.match(readme, /Current player-product stage: G6 Casefile candidate active; human G6 exit OPEN/);
  assert.match(reset, /G5 Select \/ kill \| \*\*complete — Casefile selected\*\*/);
  assert.match(reset, /G6 True playable candidate \| \*\*active — implementation built; human exit open\*\*/);
  assert.doesNotMatch(readme, /Current development stage: G5 bounded Production admitted/);
  assert.match(authority, /G_SERIES_G6_CASEFILE\.md/);
  assert.match(authority, /human G6 exit is open/);
  assert.match(agents, /G_SERIES_RESET\.md/);
});

test("G1-G3 search keeps materially different concepts and explicit cheap baselines", () => {
  for (const concept of ["Delegated Crisis Command", "Social Detective", "Last Companion", "Adaptive Predator", "Living Outpost", "Creative Social World"]) {
    assert.match(search, new RegExp(concept));
  }
  assert.match(search, /Casefile \/ Social Detective/);
  assert.match(search, /Last Light \/ Persistent Companion/);
  assert.match(search, /Echo Hunt \/ Adaptive Predator/);
  assert.match(search, /Station Zero \/ Delegated Crisis Command\s+baseline/);
  assert.match(search, /Cheapest replacement/);
  assert.match(search, /cheaper baseline mode/);
});

test("Concept Lab is disposable browser scaffolding isolated from Station Zero product routes", () => {
  assert.match(server, /defaultLabWebRoot/);
  assert.match(server, /"\/lab"/);
  assert.match(server, /labStaticFiles/);
  assert.match(lab, /Casefile/);
  assert.match(lab, /Last Light/);
  assert.match(lab, /Echo Hunt/);
  assert.match(lab, /location\.href='\/v3'/);
  assert.equal(packageJson.scripts["e2e:lab"], "node scripts/e2e-g-series-concept-lab.ts");
  assert.match(packageJson.scripts.webcheck, /web-lab\/\*\.js/);
});
