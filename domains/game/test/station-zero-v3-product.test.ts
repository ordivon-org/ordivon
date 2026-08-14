import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const product = readFileSync(new URL("../docs/STATION_ZERO_V3_PRODUCT.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");

test("stable v3 product target owns human-facing G4 identity without registering v3", () => {
  assert.match(product, /^id: game\.product\.station-zero-v3$/m);
  assert.match(product, /Development stage: G5 admitted — bounded Production/);
  assert.match(product, /Delegated Agentic Tactical Command/);
  assert.match(product, /## Conventional Form Profile/);
  assert.match(product, /## Agent Participation Profile/);
  assert.match(product, /20 committed Turns maximum/);
  assert.match(product, /G3 strategic viability evidence/);
  assert.match(product, /G3 strategy plurality evidence/);
  assert.match(product, /G3 live-Agent evidence/);
  assert.match(product, /live Provider calls:\s+950/);
  assert.match(product, /v2 = registered product truth/);
  assert.match(product, /v3 = accepted G4 target/);
});

test("repository navigation and authority route v3 product identity through the stable document", () => {
  for (const source of [readme, authority, agents, project]) assert.match(source, /STATION_ZERO_V3_PRODUCT\.md/);
  assert.match(authority, /owns the stable human-facing definition/);
  assert.match(authority, /P0\/P1\/P2\/P3 remain canonical for their exact owner-local contracts/);
  assert.match(readme, /Current development stage: G5 bounded Production admitted/);
  assert.match(readme, /Encounter budget: 20 Turns/);
});
