import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import type { MoveCommand } from "../src/model.ts";
import { recoveryPolicy, runPolicy } from "../src/policies.ts";
import { GameStore } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

function withDatabase(run: (path: string) => void): void {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-test-"));
  try {
    run(join(directory, "world.sqlite3"));
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("a complete winning mission persists, recovers, and replays", () => {
  withDatabase((path) => {
    const expected = runPolicy(recoveryPolicy);
    const store = new GameStore(path);
    let state = store.loadState();
    let step = 0;
    while (state.mission.status === "running") {
      const action = recoveryPolicy.choose(state);
      assert.ok(action);
      const applied = store.apply(materializeAction(action, `storage-policy:${step}:${action.actionId}`));
      assert.equal(applied.result.status, "accepted");
      if (applied.result.status !== "accepted") return;
      state = applied.result.state;
      step += 1;
    }
    assert.equal(sha256(state), expected.digest);
    store.close();

    const reopened = new GameStore(path);
    assert.equal(sha256(reopened.loadState()), expected.digest);
    const replay = reopened.replay();
    assert.equal(replay.digest, expected.digest);
    assert.equal(replay.eventCount, expected.events.length);
    assert.equal(replay.verified, true);
    reopened.close();
  });
});

test("command identity remains idempotent and conflicting reuse fails closed", () => {
  withDatabase((path) => {
    const store = new GameStore(path);
    const action = recoveryPolicy.choose(store.loadState());
    assert.ok(action);
    const command = materializeAction(action, "storage-idempotent");
    assert.equal(command.kind, "move");
    const first = store.apply(command);
    const duplicate = store.apply(command);
    const conflict: MoveCommand = {
      ...command,
      kind: "move",
      targetRoomId: "storage",
    };
    const rejected = store.apply(conflict);
    assert.equal(first.result.status, "accepted");
    assert.equal(duplicate.result.status, "accepted");
    assert.equal(duplicate.idempotent, true);
    assert.equal(rejected.result.status, "rejected");
    assert.equal(store.eventCount(), 1);
    store.close();
  });
});
