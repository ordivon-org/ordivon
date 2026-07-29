import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { HostStore, HostStoreError } from "../src/host/store.ts";
import { GameStore } from "../src/storage.ts";

function withStores(run: (game: GameStore, host: HostStore) => void): void {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-host-store-"));
  try {
    const game = new GameStore(join(directory, "world.sqlite3"));
    try { run(game, new HostStore(game.db)); } finally { game.close(); }
  } finally { rmSync(directory, { recursive: true, force: true }); }
}

test("HostStore creates only Artifact and Journal authority tables", () => {
  withStores((game) => {
    const tables = (game.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'host_%' ORDER BY name").all() as unknown as Array<{ name: string }>).map((row) => row.name);
    assert.deepEqual(tables, ["host_artifacts", "host_journal"]);
  });
});

test("Host Artifacts are content addressed and detect mutation", () => {
  withStores((game, host) => {
    const first = host.putArtifact("agent-context", { revision: 0, allowed: ["repair:cooling"] });
    const duplicate = host.putArtifact("agent-context", { allowed: ["repair:cooling"], revision: 0 });
    assert.equal(duplicate.digest, first.digest);
    assert.deepEqual(host.getArtifact(first.digest).content, first.content);
    game.db.prepare("UPDATE host_artifacts SET content_json = ? WHERE digest = ?").run('{"revision":1}', first.digest);
    assert.throws(() => host.getArtifact(first.digest), (error) => error instanceof HostStoreError && error.code === "host_corrupt");
  });
});

test("Protocol Artifacts preserve exact kind and canonical digest", () => {
  withStores((game, host) => {
    const value = { schemaVersion: 1, kind: "ordivon.test-object", identity: "test:one" };
    const first = host.putProtocolArtifact(value.kind, value);
    assert.deepEqual(host.getProtocolArtifact(first.digest).content, value);
    assert.throws(() => host.getProtocolArtifact("sha256:missing"), /unknown Protocol Artifact/);
    const tampered = host.putProtocolArtifact("ordivon.test-object", { ...value, identity: "test:tampered" });
    game.db.prepare("UPDATE host_artifacts SET content_json = ? WHERE digest = ?")
      .run('{"identity":"test:changed","kind":"ordivon.test-object","schemaVersion":1}', tampered.digest);
    assert.throws(
      () => host.getProtocolArtifact(tampered.digest),
      (error) => error instanceof HostStoreError && error.code === "host_corrupt",
    );
    game.db.prepare("UPDATE host_artifacts SET kind = ? WHERE digest = ?").run("different", first.digest);
    assert.throws(() => host.putProtocolArtifact(value.kind, value), /different content or kind/);
  });
});

test("Host Journal is idempotent and rejects conflicting identity or tampering", () => {
  withStores((game, host) => {
    const first = host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 1 });
    const duplicate = host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 1 });
    assert.equal(duplicate.recordDigest, first.recordDigest);
    assert.throws(() => host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 2 }), (error) => error instanceof HostStoreError && error.code === "host_constraint");
    host.appendEvent(game.activeRunId, "second", "host-event:second", { value: 2 });
    host.verifyJournal(game.activeRunId);
    game.db.prepare("UPDATE host_journal SET payload_json = ? WHERE event_id = ?").run('{"value":3}', "host-event:second");
    assert.throws(() => host.verifyJournal(game.activeRunId), /record digest mismatch/);
    game.db.prepare("UPDATE host_journal SET payload_json = ?, previous_digest = ? WHERE event_id = ?")
      .run('{"value":2}', "wrong", "host-event:second");
    assert.throws(() => host.verifyJournal(game.activeRunId), /previous digest mismatch/);
  });
});

test("HostStore validates missing identities and transaction rollback", () => {
  withStores((game, host) => {
    assert.throws(() => host.getArtifact("missing"), /unknown Host Artifact/);
    assert.throws(() => host.putArtifact(" ", {}), /artifact kind/);
    assert.throws(() => host.appendEvent("run:missing", "test", "event", {}), /unknown run/);
    assert.throws(() => host.withTransaction(game.activeRunId, () => {
      host.appendEventInTransaction(game.activeRunId, "test", "host-event:rolled-back", {}, new Date().toISOString());
      throw new Error("rollback");
    }), /rollback/);
    assert.equal(host.listJournal(game.activeRunId).length, 0);
  });
});
