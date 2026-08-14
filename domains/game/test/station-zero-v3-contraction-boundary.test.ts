import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const index = readFileSync(new URL("../src/station-zero-v3/index.ts", import.meta.url), "utf8");
const model = readFileSync(new URL("../src/station-zero-v3/model.ts", import.meta.url), "utf8");
const content = readFileSync(new URL("../src/station-zero-v3/content.ts", import.meta.url), "utf8");

const removedModules = [
  "resource-egress",
  "message-issuance",
  "entity-departure",
  "agent-action-admission",
] as const;

test("rejected v3 research surfaces cannot silently return to the current public module graph", () => {
  for (const moduleName of removedModules) {
    assert.equal(existsSync(new URL(`../src/station-zero-v3/${moduleName}.ts`, import.meta.url)), false, moduleName);
    assert.doesNotMatch(index, new RegExp(moduleName));
  }
});

test("design history stays outside the v3 executable contract", () => {
  assert.doesNotMatch(model, /StationZeroP0Contract|StationZeroDesignInfluence/);
  assert.doesNotMatch(content, /STATION_ZERO_V3_P0_CONTRACT|retainedMechanics|rejectedMechanics|nonGoals/);
  assert.match(content, /STATION_ZERO_V3_TURN_LIMIT = 20/);
});
