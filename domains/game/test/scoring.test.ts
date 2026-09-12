import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { initialTeamWorld } from "../products/station-zero-v2/src/scenario.ts";
import { scoreMission } from "../products/station-zero-v2/src/scoring.ts";

test("mission scoring is a pure read-only projection", () => {
  const state = initialTeamWorld();
  const before = sha256(state);
  const first = scoreMission(state);
  const second = scoreMission(state);
  assert.deepEqual(first, second);
  assert.equal(sha256(state), before);
  assert.equal(first.total, Object.values(first.components).reduce((total, value) => total + value, 0));
});
