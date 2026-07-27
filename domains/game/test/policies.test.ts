import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { communicationsFirstPolicy, recoveryPolicy, runPolicy } from "../src/policies.ts";
import { assertWorldInvariants } from "../src/scenario.ts";

test("recovery policy wins with bounded power, time, and verified objectives", () => {
  const result = runPolicy(recoveryPolicy);
  assert.equal(result.state.mission.status, "victory");
  assert.equal(result.state.mission.reason, "rescue_signal_verified");
  assert.ok(result.state.turn <= result.state.mission.turnLimit);
  assert.ok(result.state.resources.batteryCharge > 0);
  assert.equal(result.state.mission.distressSent, true);
  assert.equal(result.state.crew["crew-01"]?.stabilized, true);
  assert.equal(result.state.hazards["maintenance-breach"]?.sealed, true);
  assertWorldInvariants(result.state);
});

test("communications-first policy fails from linked reactor escalation", () => {
  const result = runPolicy(communicationsFirstPolicy);
  assert.equal(result.state.mission.status, "failure");
  assert.equal(result.state.mission.reason, "reactor_meltdown");
  assert.equal(result.state.resources.reactorHeat, 100);
  assertWorldInvariants(result.state);
});

test("the same policy and seed reproduce the same terminal digest", () => {
  const first = runPolicy(recoveryPolicy);
  const second = runPolicy(recoveryPolicy);
  assert.equal(first.digest, second.digest);
  assert.equal(sha256(first.state), sha256(second.state));
  assert.deepEqual(first.events, second.events);
});
