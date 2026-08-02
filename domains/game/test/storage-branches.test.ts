import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { canonicalJson, sha256 } from "../src/digest.ts";
import { recoveryPolicy } from "./support/world-policies.ts";
import { GameStore, StorageError } from "../src/storage.ts";
import { materializeAction } from "../src/world.ts";

function temp(): { directory: string; path: string } {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-storage-branches-"));
  return { directory, path: join(directory, "world.sqlite3") };
}

function applyOne(store: GameStore, id = "storage-branch-command"): void {
  const state = store.loadState();
  const action = recoveryPolicy.choose(state);
  assert.ok(action);
  const result = store.apply(materializeAction(action, id));
  if (result.result.status !== "accepted") throw new Error(result.result.reason);
}

function corrupt(run: () => unknown): void {
  assert.throws(run, (error) => error instanceof StorageError && error.code === "storage_corrupt");
}

test("store options and active Run selection validate explicitly", () => {
  assert.throws(() => new GameStore(":memory:", { snapshotInterval: 0 }), /positive integer/);
  const { directory, path } = temp();
  try {
    const store = new GameStore(path);
    store.createRun({ runId: "run:second" });
    store.setActiveRun("run:second");
    assert.equal(store.activeRunId, "run:second");
    assert.equal(store.loadState().revision, 0);
    store.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("duplicate Run identity maps to storage_constraint", () => {
  const { directory, path } = temp();
  try {
    const store = new GameStore(path);
    assert.throws(
      () => store.createRun({ runId: "run:default" }),
      (error) => error instanceof StorageError && error.code === "storage_constraint",
    );
    store.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("an invalid SQLite file maps to storage_corrupt", () => {
  const { directory, path } = temp();
  try {
    writeFileSync(path, "not a sqlite database");
    assert.throws(
      () => new GameStore(path),
      (error) => error instanceof StorageError && error.code === "storage_corrupt",
    );
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("a stale persisted command rolls back and returns a typed world rejection", () => {
  const { directory, path } = temp();
  try {
    const store = new GameStore(path);
    const result = store.apply({
      kind: "wait",
      commandId: "storage-stale",
      actorId: "engineer-01",
      expectedRevision: 99,
    });
    assert.equal(result.result.status, "rejected");
    assert.equal(result.result.status === "rejected" ? result.result.code : null, "stale_revision");
    assert.equal(store.eventCount(), 0);
    store.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("missing Event rows are detected as stream divergence", () => {
  const { directory, path } = temp();
  try {
    const store = new GameStore(path);
    applyOne(store);
    store.db.prepare("DELETE FROM events WHERE event_sequence = 0").run();
    corrupt(() => store.verifyStream());
    store.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("a validly hashed but incompatible Genesis is rejected by replay digests", () => {
  const { directory, path } = temp();
  try {
    const store = new GameStore(path);
    applyOne(store);
    const row = store.db.prepare("SELECT state_json FROM snapshots WHERE revision = 0").get() as { state_json: string };
    const genesis = JSON.parse(row.state_json) as { resources: { oxygen: number } };
    genesis.resources.oxygen = 77;
    const json = canonicalJson(genesis);
    store.db.prepare("UPDATE snapshots SET state_json = ?, digest = ? WHERE revision = 0").run(json, sha256(genesis));
    corrupt(() => store.verifyReplay());
    store.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("individually valid Command and Event chains still reject cross-stream identity mismatch", () => {
  const { directory, path } = temp();
  try {
    const store = new GameStore(path);
    applyOne(store);
    const row = store.db.prepare(`SELECT event_sequence, event_json, before_digest, after_digest, previous_digest
      FROM events WHERE event_sequence = 0`).get() as {
        event_sequence: number; event_json: string; before_digest: string; after_digest: string; previous_digest: string;
      };
    const commandId = "different-event-command-id";
    const digest = sha256({
      kind: "event",
      runId: store.activeRunId,
      sequence: row.event_sequence,
      commandId,
      eventJson: row.event_json,
      beforeDigest: row.before_digest,
      afterDigest: row.after_digest,
      previousDigest: row.previous_digest ?? "",
    });
    store.db.prepare("UPDATE events SET command_id = ?, record_digest = ? WHERE event_sequence = 0")
      .run(commandId, digest);
    corrupt(() => store.verifyStream());
    store.close();
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
