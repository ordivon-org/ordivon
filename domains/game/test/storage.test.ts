import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { GameStore } from "../src/storage.ts";

function withDatabase(run: (path: string) => void): void {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-test-"));
  try {
    run(join(directory, "world.sqlite3"));
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("SQLite persists, recovers, and replays an admitted command", () => {
  withDatabase((path) => {
    const first = new GameStore(path);
    const applied = first.apply({
      kind: "restore_power",
      commandId: "storage-test-1",
      actorId: "engineer-01",
      targetId: "life-support",
      expectedRevision: 0,
    });
    assert.equal(applied.result.status, "accepted");
    const terminalDigest = sha256(applied.result.state);
    first.close();

    const reopened = new GameStore(path);
    assert.equal(sha256(reopened.loadState()), terminalDigest);
    const replay = reopened.replay();
    assert.equal(replay.digest, terminalDigest);
    assert.equal(replay.eventCount, 1);
    assert.equal(replay.verified, true);
    reopened.close();
  });
});

test("command identity is idempotent and conflicts fail closed", () => {
  withDatabase((path) => {
    const store = new GameStore(path);
    const command = {
      kind: "restore_power" as const,
      commandId: "storage-test-idempotent",
      actorId: "engineer-01",
      targetId: "life-support",
      expectedRevision: 0,
    };
    const first = store.apply(command);
    const duplicate = store.apply(command);
    const conflict = store.apply({ ...command, targetId: "different-target" });

    assert.equal(first.result.status, "accepted");
    assert.equal(duplicate.result.status, "accepted");
    assert.equal(duplicate.idempotent, true);
    assert.equal(conflict.result.status, "rejected");
    assert.equal(store.eventCount(), 1);
    store.close();
  });
});
