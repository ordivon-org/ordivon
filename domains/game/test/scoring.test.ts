import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { communicationsFirstPolicy, recoveryPolicy, runPolicy } from "../src/policies.ts";
import { initialWorld } from "../src/scenario.ts";
import { scoreMission } from "../src/scoring.ts";

test("mission scoring is a pure read-only projection", () => {
  const state = initialWorld();
  const before = sha256(state);
  const first = scoreMission(state);
  const second = scoreMission(state);
  assert.deepEqual(first, second);
  assert.equal(sha256(state), before);
  assert.equal(first.total, Object.values(first.components).reduce((total, value) => total + value, 0));
});

test("verified victory scores above a locally productive terminal failure", () => {
  const victory = scoreMission(runPolicy(recoveryPolicy).state);
  const failure = scoreMission(runPolicy(communicationsFirstPolicy).state);
  assert.equal(victory.components.verifiedVictory, 1_000);
  assert.equal(failure.components.verifiedVictory, 0);
  assert.equal(victory.total, 2_203);
  assert.equal(failure.total, 735);
  assert.ok(victory.total > failure.total);
});
