import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { LocalEvidenceJournal, LocalEvidenceError } from "../products/station-zero-v2/src/integration/local-evidence-journal.ts";
import { GameStore } from "../products/station-zero-v2/src/storage.ts";

function withStores(run: (game: GameStore, host: LocalEvidenceJournal) => void): void {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-local-evidence-"));
  try {
    const game = new GameStore(join(directory, "world.sqlite3"));
    try { run(game, new LocalEvidenceJournal(game.db)); } finally { game.close(); }
  } finally { rmSync(directory, { recursive: true, force: true }); }
}

test("LocalEvidenceJournal creates only Artifact and Journal authority tables", () => {
  withStores((game) => {
    const tables = (game.db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'host_%' ORDER BY name").all() as unknown as Array<{ name: string }>).map((row) => row.name);
    assert.deepEqual(tables, ["host_artifacts", "host_journal"]);
  });
});

test("Local Evidence Artifacts are content addressed and detect mutation", () => {
  withStores((game, host) => {
    const first = host.putArtifact("agent-context", { revision: 0, allowed: ["repair:cooling"] });
    const duplicate = host.putArtifact("agent-context", { allowed: ["repair:cooling"], revision: 0 });
    assert.equal(duplicate.digest, first.digest);
    assert.deepEqual(host.getArtifact(first.digest).content, first.content);
    game.db.prepare("UPDATE host_artifacts SET content_json = ? WHERE digest = ?").run('{"revision":1}', first.digest);
    assert.throws(() => host.getArtifact(first.digest), (error) => error instanceof LocalEvidenceError && error.code === "host_corrupt");
  });
});


test("Local Evidence Journal is idempotent and rejects conflicting identity or tampering", () => {
  withStores((game, host) => {
    const first = host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 1 });
    const duplicate = host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 1 });
    assert.equal(duplicate.recordDigest, first.recordDigest);
    assert.deepEqual(host.getJournalEvent(game.activeRunId, first.eventId), first);
    assert.equal(host.getJournalEvent(game.activeRunId, "host-event:missing"), null);
    assert.throws(() => host.appendEvent(game.activeRunId, "test_event", "host-event:test", { value: 2 }), (error) => error instanceof LocalEvidenceError && error.code === "host_constraint");
    host.appendEvent(game.activeRunId, "second", "host-event:second", { value: 2 });
    host.verifyJournal(game.activeRunId);
    game.db.prepare("UPDATE host_journal SET payload_json = ? WHERE event_id = ?").run('{"value":3}', "host-event:second");
    assert.throws(() => host.verifyJournal(game.activeRunId), /record digest mismatch/);
    game.db.prepare("UPDATE host_journal SET payload_json = ?, previous_digest = ? WHERE event_id = ?")
      .run('{"value":2}', "wrong", "host-event:second");
    assert.throws(() => host.verifyJournal(game.activeRunId), /previous digest mismatch/);
  });
});

test("LocalEvidenceJournal validates missing identities and transaction rollback", () => {
  withStores((game, host) => {
    assert.throws(() => host.getArtifact("missing"), /unknown Local Evidence Artifact/);
    assert.throws(() => host.putArtifact(" ", {}), /artifact kind/);
    assert.throws(() => host.appendEvent("run:missing", "test", "event", {}), /unknown run/);
    assert.throws(() => host.withTransaction(game.activeRunId, () => {
      host.appendEventInTransaction(game.activeRunId, "test", "host-event:rolled-back", {}, new Date().toISOString());
      throw new Error("rollback");
    }), /rollback/);
    assert.equal(host.listJournal(game.activeRunId).length, 0);
  });
});


test("Local Evidence Journal point reads reject tampered records", () => {
  withStores((game, host) => {
    const event = host.appendEvent(
      game.activeRunId,
      "audit-event",
      "host-event:audit-point-read",
      { value: 1 },
    );
    game.db.prepare("UPDATE host_journal SET payload_json = ? WHERE run_id = ? AND event_id = ?")
      .run('{"value":2}', game.activeRunId, event.eventId);
    assert.throws(
      () => host.getJournalEvent(game.activeRunId, event.eventId),
      (error: unknown) => error instanceof LocalEvidenceError && error.code === "host_corrupt" && /record digest mismatch/.test(error.message),
    );
  });
});


test("large Artifact and Journal JSON compress transparently without changing logical identity", () => {
  withStores((game, host) => {
    const content = { repeated: "station-zero:".repeat(1_000), values: Array.from({ length: 64 }, (_, index) => index) };
    const artifact = host.putArtifact("large-context", content);
    const artifactRow = game.db.prepare("SELECT content_json, byte_length FROM host_artifacts WHERE digest = ?")
      .get(artifact.digest) as { content_json: string; byte_length: number };
    assert.match(artifactRow.content_json, /^gzip-base64:/);
    assert.ok(Buffer.byteLength(artifactRow.content_json) < Number(artifactRow.byte_length));
    assert.deepEqual(host.getArtifact(artifact.digest).content, content);

    const event = host.appendEvent(game.activeRunId, "large-event", "host-event:large-compressed", content);
    const journalRow = game.db.prepare("SELECT payload_json FROM host_journal WHERE run_id = ? AND event_id = ?")
      .get(game.activeRunId, event.eventId) as { payload_json: string };
    assert.match(journalRow.payload_json, /^gzip-base64:/);
    assert.deepEqual(host.getJournalEvent(game.activeRunId, event.eventId)?.payload, content);
    host.verifyJournal(game.activeRunId);
  });
});
