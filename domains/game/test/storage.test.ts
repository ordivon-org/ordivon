import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import type { MoveCommand } from "../src/model.ts";
import { recoveryPolicy } from "./support/world-policies.ts";
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


test("a verified World Head invalidates when another Store commits a newer revision", () => {
  withDatabase((path) => {
    const first = new GameStore(path);
    const second = new GameStore(path);
    try {
      assert.equal(first.loadState().revision, 0);
      const action = recoveryPolicy.choose(second.loadState());
      assert.ok(action);
      const applied = second.apply(materializeAction(action, "external-head-update"));
      assert.equal(applied.result.status, "accepted");
      assert.equal(second.loadState().revision, 1);

      const refreshed = first.loadState();
      assert.equal(refreshed.revision, 1);
      assert.equal(first.verifyReplay().digest, second.verifyReplay().digest);
    } finally {
      second.close();
      first.close();
    }
  });
});
