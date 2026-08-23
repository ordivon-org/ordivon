import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  StationZeroV3PlayService,
  StationZeroV3Store,
  createStationZeroV3Genesis,
} from "../src/station-zero-v3/index.ts";

const valueDoc = readFileSync(new URL("../docs/STATION_ZERO_V3_PRODUCT_VALUE.md", import.meta.url), "utf8");
const productDoc = readFileSync(new URL("../docs/STATION_ZERO_V3_PRODUCT.md", import.meta.url), "utf8");
const p0 = readFileSync(new URL("../docs/STATION_ZERO_V3_P0.md", import.meta.url), "utf8");
const p3 = readFileSync(new URL("../docs/STATION_ZERO_V3_P3.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");
const app = readFileSync(new URL("../web-v3/app.js", import.meta.url), "utf8");
const render = readFileSync(new URL("../web-v3/render.js", import.meta.url), "utf8");
const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

test("G4 Product Value authority records comparative design evidence and empirical subtraction", () => {
  for (const analogue of ["Frozen Synapse", "Phantom Brigade", "Radio Commander", "Duskers", "Door Kickers 2", "Aliens: Dark Descent", "Invisible, Inc."]) {
    assert.match(valueDoc, new RegExp(analogue.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(valueDoc, /39 \/ 40 Agent selections changed/);
  assert.match(valueDoc, /optional pickup contexts:\s+46/);
  assert.match(valueDoc, /ignore ↔ opportunistic changes:\s+0/);
  assert.match(valueDoc, /retreat threshold[\s\S]*OBSERVED_CONTEXTUAL_LEVERAGE/);
  assert.match(valueDoc, /priority target[\s\S]*OBSERVED_CONTEXTUAL_LEVERAGE/);
  assert.match(valueDoc, /Content Grammar v0/);
  assert.match(valueDoc, /one bounded second Case plus \*\*three\*\* independently proven outer axes/);
  assert.match(valueDoc, /objective-bearing civilian \/ Research Core placement = proven outer Content Grammar axis/);
  assert.match(valueDoc, /optional resource\/item placement = still unproven/);
  assert.match(valueDoc, /enemy directive doctrine = proven outer Content Grammar axis/);
  assert.match(valueDoc, /alternate enemy Objective package = still unproven/);
  assert.match(valueDoc, /mission factory/);
  assert.match(valueDoc, /G4 Product Value is accepted and bounded G5 Production is admitted/);
  assert.match(valueDoc, /Current Game Core research interpretation/);
  assert.match(valueDoc, /reference experiment/);
});

test("current player surface does not advertise controls that current G4 evidence rejected", () => {
  const store = new StationZeroV3Store(":memory:");
  try {
    const play = new StationZeroV3PlayService(store);
    const catalog = play.catalog();
    assert.equal("lootPolicies" in catalog, false);
    const view = play.initialize({ runId: "run:product-value:surface-contract" });
    assert.equal(view.experience.order?.lootPolicy, "mission-only");
  } finally {
    store.close();
  }
  assert.doesNotMatch(render, /name="lootPolicy"/);
  assert.doesNotMatch(app, /"lootPolicy",\s*$/m);
  assert.doesNotMatch(productDoc, /lethal\/collateral\/loot policy/);
  assert.match(p0, /does not surface collateral/);
  assert.match(p3, /internal loot policy field/);
});

test("bounded system observations expose causal evidence without reading unknown current systems", () => {
  const genesis = createStationZeroV3Genesis();
  assert.equal(genesis.factionKnowledge.rescue.knownSystems.cooling, undefined);
  assert.equal(genesis.factionKnowledge.rescue.knownSystems["power-grid"]?.observedIntegrity, 0.72);
  assert.match(render, /Last confirmed Turn/);
  assert.match(render, /known-system telemetry updates on visible system changes/);
  assert.match(app, /Power alone will not reduce heat until a local repair raises integrity to 60%/);
});

test("Product Value lane is canonical navigation and has a repeatable evaluator", () => {
  for (const source of [readme, authority, agents, project]) assert.match(source, /STATION_ZERO_V3_PRODUCT_VALUE\.md/);
  assert.equal(packageJson.scripts["eval:v3:product-value"], "node scripts/eval-station-zero-v3-product-value.ts");
  assert.equal(packageJson.scripts["eval:v3:product-value:information"], "node scripts/eval-station-zero-v3-product-value.ts --lane information");
  assert.equal(packageJson.scripts["eval:v3:product-value:targeted-controls"], "node scripts/eval-station-zero-v3-product-value.ts --lane targeted-controls");
  const evaluatorSource = readFileSync(new URL("../scripts/eval-station-zero-v3-product-value.ts", import.meta.url), "utf8");
  assert.match(evaluatorSource, /--lane/);
  assert.match(evaluatorSource, /Default: all lanes/);
  assert.match(valueDoc, /execution granularity only/);
});
