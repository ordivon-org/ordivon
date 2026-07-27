import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { sha256 } from "../src/digest.ts";
import { recoveryPolicy } from "../src/policies.ts";
import { GameStore, StorageError } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

function directory(): string {
  return mkdtempSync(join(tmpdir(), "ordivon-game-integrity-"));
}

function advance(store: GameStore, maximum = 64): void {
  let state = store.loadState();
  for (let step = 0; step < maximum && state.mission.status === "running"; step += 1) {
    const action = recoveryPolicy.choose(state);
    assert.ok(action);
    const result = store.apply(materializeAction(action, `integrity:${step}:${action.actionId}`));
    if (result.result.status !== "accepted") throw new Error(`${result.result.code}: ${result.result.reason}`);
    assert.equal(result.result.status, "accepted");
    state = result.result.state;
  }
}

function expectCorrupt(run: () => unknown): void {
  assert.throws(run, (error) => error instanceof StorageError && error.code === "storage_corrupt");
}

test("sparse snapshots support fast recovery and full verification", () => {
  const dir = directory();
  try {
    const store = new GameStore(join(dir, "world.sqlite3"));
    advance(store);
    assert.equal(store.eventCount(), 25);
    assert.equal(store.snapshotCount(), 5);
    const recovery = store.recover();
    const verify = store.verifyReplay();
    assert.equal(recovery.mode, "recovery");
    assert.equal(recovery.snapshotRevision, 25);
    assert.equal(recovery.replayedCommandCount, 0);
    assert.equal(verify.mode, "verify");
    assert.equal(verify.snapshotRevision, 0);
    assert.equal(verify.replayedCommandCount, 25);
    assert.equal(recovery.digest, verify.digest);
    store.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("snapshots are caches: deleting non-genesis snapshots still recovers from the journal", () => {
  const dir = directory();
  try {
    const store = new GameStore(join(dir, "world.sqlite3"));
    advance(store);
    const expected = sha256(store.loadState());
    store.db.prepare("DELETE FROM snapshots WHERE run_id = ? AND revision > 0").run(store.activeRunId);
    assert.equal(store.snapshotCount(), 1);
    const recovered = store.recover();
    assert.equal(recovered.snapshotRevision, 0);
    assert.equal(recovered.replayedCommandCount, 25);
    assert.equal(recovered.digest, expected);
    store.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("command and event hash chains detect retained-history tampering", () => {
  for (const table of ["commands", "events"] as const) {
    const dir = directory();
    try {
      const store = new GameStore(join(dir, `${table}.sqlite3`));
      advance(store, 3);
      if (table === "commands") {
        store.db.prepare("UPDATE commands SET command_json = command_json || ? WHERE command_sequence = 0").run(" ");
      } else {
        store.db.prepare("UPDATE events SET event_json = event_json || ? WHERE event_sequence = 0").run(" ");
      }
      expectCorrupt(() => store.verifyStream());
      store.close();
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  }
});

test("snapshot digest tampering blocks recovery", () => {
  const dir = directory();
  try {
    const store = new GameStore(join(dir, "world.sqlite3"));
    advance(store);
    store.db.prepare("UPDATE snapshots SET digest = ? WHERE revision = 25").run("tampered");
    expectCorrupt(() => store.recover());
    store.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("recent event queries read only the requested tail", () => {
  const dir = directory();
  try {
    const store = new GameStore(join(dir, "world.sqlite3"));
    advance(store, 10);
    const recent = store.recentJournalEvents(3);
    assert.deepEqual(recent.map((event) => event.commandSequence), [7, 8, 9]);
    store.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("SQLite writer contention maps to storage_busy without duplicate effects", () => {
  const dir = directory();
  const path = join(dir, "world.sqlite3");
  const first = new GameStore(path, { busyTimeoutMs: 1 });
  const second = new GameStore(path, { busyTimeoutMs: 1 });
  try {
    const state = second.loadState();
    const action = recoveryPolicy.choose(state);
    assert.ok(action);
    first.db.exec("BEGIN IMMEDIATE");
    assert.throws(
      () => second.apply(materializeAction(action, "busy-command")),
      (error) => error instanceof StorageError && error.code === "storage_busy",
    );
    first.db.exec("ROLLBACK");
    assert.equal(second.eventCount(), 0);
  } finally {
    try { first.db.exec("ROLLBACK"); } catch {}
    first.close();
    second.close();
    rmSync(dir, { recursive: true, force: true });
  }
});
