import assert from "node:assert/strict";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { applyWorldCommand, initialWorld } from "../src/world.ts";

const command = {
  kind: "restore_power" as const,
  commandId: "world-test-1",
  actorId: "engineer-01",
  targetId: "life-support",
  expectedRevision: 0,
};

test("restore_power produces one deterministic atomic transition", () => {
  const initial = initialWorld();
  const first = applyWorldCommand(initial, command);
  const second = applyWorldCommand(initialWorld(), command);

  assert.equal(first.status, "accepted");
  assert.equal(second.status, "accepted");
  if (first.status !== "accepted" || second.status !== "accepted") return;

  assert.equal(first.state.rooms["life-support"]?.powered, true);
  assert.equal(first.state.rooms["life-support"]?.oxygen, 80);
  assert.equal(first.state.revision, 1);
  assert.equal(first.event.afterDigest, second.event.afterDigest);
  assert.equal(sha256(first.state), first.event.afterDigest);
  assert.equal(initial.rooms["life-support"]?.powered, false);
});

test("a stale action is rejected without partial mutation", () => {
  const initial = initialWorld();
  const before = sha256(initial);
  const result = applyWorldCommand(initial, { ...command, expectedRevision: 7 });

  assert.equal(result.status, "rejected");
  assert.equal(sha256(result.state), before);
  assert.equal(initial.revision, 0);
  assert.equal(initial.rooms["life-support"]?.powered, false);
});
