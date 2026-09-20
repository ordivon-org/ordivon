import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";

import {
  ShadowHostReceiver,
  ShadowOutboxHarness,
} from "../experiments/game-e2e-r5/host-outbox-shadow.ts";

const RUN = "run:r5-shadow";

function commit(harness: ShadowOutboxHarness, eventId = "event:0", state: unknown = { revision: 1 }) {
  return harness.commit(RUN, eventId, "game.shadow-state-changed", state, { state });
}

test("R5 shadow outbox rolls back state and event together before commit", () => {
  const harness = new ShadowOutboxHarness();
  try {
    assert.throws(
      () => harness.commit(RUN, "event:rollback", "game.shadow", { value: 1 }, { value: 1 }, "before_commit"),
      /before-commit/,
    );
    assert.equal(harness.state(RUN), null);
    assert.deepEqual(harness.pending(RUN), []);
  } finally { harness.close(); }
});

test("R5 shadow outbox recovers commit response loss by stable event identity", () => {
  const harness = new ShadowOutboxHarness();
  try {
    assert.throws(
      () => harness.commit(RUN, "event:response-loss", "game.shadow", { value: 1 }, { value: 1 }, "after_commit_response_loss"),
      /response loss/,
    );
    assert.equal(harness.state(RUN)?.revision, 0);
    assert.equal(harness.pending(RUN).length, 1);
    const recovered = harness.commit(RUN, "event:response-loss", "game.shadow", { value: 1 }, { value: 1 });
    assert.equal(recovered.sequence, 0);
    assert.equal(harness.state(RUN)?.revision, 0, "retry must not re-apply committed Game state");
    assert.equal(harness.pending(RUN).length, 1);
  } finally { harness.close(); }
});

test("R5 shadow relay survives Host acceptance response loss without duplicate Host effect", () => {
  const harness = new ShadowOutboxHarness();
  const receiver = new ShadowHostReceiver();
  try {
    const event = commit(harness);
    assert.throws(() => harness.relayNext(RUN, receiver, "after_accept_before_ack"), /response loss/);
    assert.equal(receiver.count(RUN), 1);
    assert.equal(harness.pending(RUN).length, 1);
    const delivered = harness.relayNext(RUN, receiver);
    assert.equal(delivered?.outboxId, event.outboxId);
    assert.equal(receiver.count(RUN), 1, "stable identity must make duplicate relay harmless");
    assert.equal(harness.pending(RUN).length, 0);
  } finally { harness.close(); }
});

test("R5 shadow relay preserves per-Run ordering and rejects out-of-order admission", () => {
  const harness = new ShadowOutboxHarness();
  const receiver = new ShadowHostReceiver();
  try {
    const first = commit(harness, "event:first", { value: 1 });
    const second = commit(harness, "event:second", { value: 2 });
    assert.equal(first.sequence, 0);
    assert.equal(second.sequence, 1);
    assert.throws(() => receiver.accept(second), /out-of-order/);
    harness.relayNext(RUN, receiver);
    harness.relayNext(RUN, receiver);
    assert.equal(receiver.count(RUN), 2);
    assert.equal(harness.pending(RUN).length, 0);
  } finally { harness.close(); }
});

test("R5 shadow relay leaves committed Game state pending while Host is unavailable", () => {
  const harness = new ShadowOutboxHarness();
  const receiver = new ShadowHostReceiver();
  try {
    commit(harness);
    receiver.available = false;
    assert.throws(() => harness.relayNext(RUN, receiver), /unavailable/);
    assert.deepEqual(harness.state(RUN)?.value, { revision: 1 });
    assert.equal(harness.pending(RUN).length, 1);
    receiver.available = true;
    harness.relayNext(RUN, receiver);
    assert.equal(receiver.count(RUN), 1);
  } finally { harness.close(); }
});

test("R5 shadow outbox survives process-style reopen and resumes pending delivery", () => {
  const db = new DatabaseSync(":memory:");
  const first = new ShadowOutboxHarness(db);
  const receiver = new ShadowHostReceiver();
  commit(first);
  const second = new ShadowOutboxHarness(db);
  assert.equal(second.pending(RUN).length, 1);
  second.relayNext(RUN, receiver);
  assert.equal(receiver.count(RUN), 1);
  assert.equal(second.pending(RUN).length, 0);
  second.close();
});

test("R5 shadow outbox fails closed on retained payload tamper", () => {
  const harness = new ShadowOutboxHarness();
  try {
    const event = commit(harness);
    harness.db.prepare(
      "UPDATE r5_shadow_host_outbox SET payload_json = ? WHERE outbox_id = ?",
    ).run(JSON.stringify({ state: { revision: 999 } }), event.outboxId);
    assert.throws(() => harness.pending(RUN), /payload digest mismatch/);
  } finally { harness.close(); }
});
