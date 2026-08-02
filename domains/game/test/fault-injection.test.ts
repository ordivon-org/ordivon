import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { recoveryPolicy } from "./support/world-policies.ts";
import { GameStore, type StorageFaultPoint } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

const preCommitPoints: StorageFaultPoint[] = [
  "before_begin",
  "after_begin",
  "before_command_insert",
  "after_command_insert",
  "after_event_insert",
  "before_snapshot",
  "after_snapshot",
  "before_commit",
];

test("pre-commit fault points leave no partial world effect", () => {
  for (const point of preCommitPoints) {
    const directory = mkdtempSync(join(tmpdir(), `ordivon-game-fault-${point}-`));
    const path = join(directory, "world.sqlite3");
    let enabled = false;
    const store = new GameStore(path, {
      snapshotInterval: 1,
      faultInjector(current) {
        if (enabled && current === point) throw new Error(`injected:${point}`);
      },
    });
    try {
      const state = store.loadState();
      const action = recoveryPolicy.choose(state);
      assert.ok(action);
      const command = materializeAction(action, `fault:${point}`);
      enabled = true;
      assert.throws(() => store.apply(command), new RegExp(`injected:${point}`));
      enabled = false;
      assert.equal(store.eventCount(), 0, point);
      assert.equal(store.loadState().revision, 0, point);
      assert.equal(store.snapshotCount(), 1, point);
    } finally {
      store.close();
      rmSync(directory, { recursive: true, force: true });
    }
  }
});

test("an after-commit fault is recovered by idempotent retry", () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-after-commit-"));
  const path = join(directory, "world.sqlite3");
  let enabled = false;
  const store = new GameStore(path, {
    snapshotInterval: 1,
    faultInjector(point) {
      if (enabled && point === "after_commit") throw new Error("injected:after_commit");
    },
  });
  const state = store.loadState();
  const action = recoveryPolicy.choose(state);
  assert.ok(action);
  const command = materializeAction(action, "fault:after-commit");
  enabled = true;
  assert.throws(() => store.apply(command), /injected:after_commit/);
  store.close();

  const reopened = new GameStore(path, { snapshotInterval: 1 });
  try {
    assert.equal(reopened.eventCount(), 1);
    assert.equal(reopened.loadState().revision, 1);
    const retry = reopened.apply(command);
    assert.equal(retry.result.status, "accepted");
    assert.equal(retry.idempotent, true);
    assert.equal(reopened.eventCount(), 1);
  } finally {
    reopened.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
