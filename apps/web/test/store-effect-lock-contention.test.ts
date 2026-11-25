import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { WebStore } from "../src/store.ts";
import { WebProblem } from "../src/errors.ts";
import { runEffectTransaction } from "../src/store-effect-transaction.ts";
import { agentId, commit, effect, now, principalId, seed } from "./fixtures/effect-recovery.ts";

for (const release of ["commit", "rollback"] as const) {
  test("real WAL writer contention preserves peer state and returns a typed no-start result: " + release, () => {
    const dir = mkdtempSync(join(tmpdir(), "ordivon-effect-lock-"));
    const path = join(dir, "web.sqlite");
    const writer = new WebStore(path);
    const reader = new WebStore(path);
    try {
      const grant = seed(writer);
      const historical = commit(writer, grant, "historical");
      const current = writer.getAgentGrant(grant.grantId);
      writer.db.exec("BEGIN IMMEDIATE");
      try {
        // Existing replay must not need the writer lock.
        assert.deepEqual(commit(reader, grant, "historical"), { receipt: historical.receipt, replayed: true });
        assert.throws(() => commit(reader, current, "blocked"), (error: unknown) =>
          error instanceof WebProblem && error.status === 503 && error.code === "effect-writer-busy");
        assert.equal(reader.db.isTransaction, false);
        assert.equal(writer.db.isTransaction, true);
        assert.equal(reader.getAgentEffect(effect("blocked").effectId), null);
        assert.deepEqual(reader.getAgentGrant(grant.grantId), current);
      } finally { writer.db.exec(release === "commit" ? "COMMIT" : "ROLLBACK"); }
      // Deliberate new caller action, not an automatic retry.
      const result = commit(reader, current, "blocked");
      assert.equal(result.replayed, false);
      assert.equal(reader.getAgentGrant(grant.grantId).remainingEffects, 0);
      assert.equal(reader.db.prepare("SELECT count(*) AS n FROM agent_effects").get()?.n, 2);
      assert.equal(reader.db.prepare("SELECT count(*) AS n FROM canary_notes").get()?.n, 2);
      assert.equal(reader.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type = 'agent.effect.committed'").get()?.n, 2);
    } finally {
      reader.close(); writer.close(); rmSync(dir, { recursive: true, force: true });
    }
  });
}

// Obtain the actual native error from two real connections, then place it at
// alternate transaction phases to prove that classification is phase-specific.
for (const phase of ["begin-ack", "write", "commit-ack"] as const) {
  test("a native BUSY-shaped error is not a no-start result after acquisition: " + phase, () => {
    const dir = mkdtempSync(join(tmpdir(), "ordivon-effect-busy-phase-"));
    const path = join(dir, "web.sqlite");
    const writer = new WebStore(path);
    const reader = new WebStore(path);
    try {
      writer.db.exec("BEGIN IMMEDIATE");
      let busy: unknown;
      try {
        try { reader.db.exec("BEGIN IMMEDIATE"); } catch (error) { busy = error; }
        assert.ok(busy instanceof Error);
      } finally { writer.db.exec("ROLLBACK"); }
      const nativeExec = reader.db.exec.bind(reader.db);
      Object.defineProperty(reader.db, "exec", { configurable: true, value: (sql: string) => {
        nativeExec(sql);
        if ((phase === "begin-ack" && sql === "BEGIN IMMEDIATE") ||
            (phase === "commit-ack" && sql === "COMMIT")) throw busy;
      }});
      try {
        assert.throws(() => runEffectTransaction(reader.db, () => {
          reader.db.exec("INSERT INTO audit_events VALUES ('phase-test', NULL, 'test', NULL, NULL, '{}', 0)");
          if (phase === "write") throw busy;
        }), error => error === busy);
      } finally { Reflect.deleteProperty(reader.db, "exec"); }
      assert.equal(reader.db.isTransaction, false);
      assert.equal(writer.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_id = 'phase-test'").get()?.n,
        phase === "commit-ack" ? 1 : 0);
    } finally { reader.close(); writer.close(); rmSync(dir, { recursive: true, force: true }); }
  });
}

test("native writer contention does not consume an approval or publish a note", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-effect-publish-lock-"));
  const path = join(dir, "web.sqlite");
  const writer = new WebStore(path);
  const reader = new WebStore(path);
  try {
    seed(writer);
    writer.putCredential(principalId, {
      id: "credential:lock", publicKey: new Uint8Array([1, 2, 3]), counter: 0,
      transports: ["internal"], deviceType: "singleDevice", backedUp: false,
    }, now);
    const grant = writer.createAgentGrant({
      grantId: "grant:publish-lock", principalId, agentId, audience: "https://example.test",
      allowedActions: ["canary.note.publish"], resourcePrefixes: ["/canary/notes"],
      expiresAtEpochSeconds: now + 60, maxRiskClass: "R4", stepUpAtOrAbove: "R4", remainingEffects: 1,
    }, now);
    const note = writer.createCanaryNote(principalId, "draft", now);
    const request = { ...effect("publish-lock"), action: "canary.note.publish", resource: "/canary/notes/" + note.noteId,
      riskClass: "R4" as const, effectType: "website.canary.note.publish" };
    writer.putEffectApproval(principalId, "credential:lock", request.effectId, request.effectDigest, now);
    writer.db.exec("BEGIN IMMEDIATE");
    try {
      assert.throws(() => reader.commitAgentCanaryPublish(grant, agentId, request, note.noteId, now),
        error => error instanceof WebProblem && error.code === "effect-writer-busy");
      assert.equal(reader.effectApproval(principalId, request, now).verified, true);
      assert.equal(reader.getAgentEffect(request.effectId), null);
      assert.deepEqual(reader.getAgentGrant(grant.grantId), grant);
      assert.equal(reader.db.prepare("SELECT state FROM canary_notes WHERE note_id = ?").get(note.noteId)?.state, "DRAFT");
      assert.equal(reader.db.isTransaction, false);
    } finally { writer.db.exec("ROLLBACK"); }
    const result = reader.commitAgentCanaryPublish(grant, agentId, request, note.noteId, now);
    assert.equal(result.replayed, false);
    assert.equal(reader.effectApproval(principalId, request, now).verified, false);
    assert.equal(reader.getAgentGrant(grant.grantId).remainingEffects, 0);
    assert.equal(reader.db.prepare("SELECT state FROM canary_notes WHERE note_id = ?").get(note.noteId)?.state, "PUBLISHED");
  } finally { reader.close(); writer.close(); rmSync(dir, { recursive: true, force: true }); }
});

test("a separate native process holding the WAL writer lock cannot trigger an implicit Effect retry", { timeout: 15000 }, async () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-effect-process-lock-"));
  const path = join(dir, "web.sqlite");
  const store = new WebStore(path);
  const grant = seed(store);
  // Child owns a real SQLite writer transaction, not a mocked exec hook.
  // The IPC handshake establishes the lock before the parent attempts a write.
  const child = spawn(process.execPath, ["--input-type=module", "-e", `
    import { DatabaseSync } from "node:sqlite";
    const db = new DatabaseSync(process.argv[1]);
    db.exec("BEGIN IMMEDIATE");
    process.send("locked");
    process.once("message", message => {
      if (message !== "release") process.exit(2);
      db.exec("ROLLBACK");
      db.close();
      process.disconnect();
    });
  `, path], { stdio: ["ignore", "ignore", "pipe", "ipc"] });
  const exited = once(child, "exit");
  let released = false;
  try {
    const ready = await Promise.race([
      once(child, "message", { signal: AbortSignal.timeout(5000) }).then(([message]) => message),
      exited.then(([code, signal]) => { throw new Error("lock owner exited: " + code + "/" + signal); }),
    ]);
    assert.equal(ready, "locked");
    assert.throws(() => commit(store, grant, "process-lock"), error =>
      error instanceof WebProblem && error.code === "effect-writer-busy");
    assert.equal(store.db.isTransaction, false);
    assert.equal(store.getAgentEffect(effect("process-lock").effectId), null);
    assert.deepEqual(store.getAgentGrant(grant.grantId), grant);
    child.send("release");
    const [code, signal] = await exited;
    released = true;
    assert.equal(code, 0);
    assert.equal(signal, null);
    assert.equal(commit(store, grant, "process-lock").replayed, false);
    assert.equal(store.getAgentGrant(grant.grantId).remainingEffects, 1);
    assert.equal(store.db.prepare("SELECT count(*) AS n FROM agent_effects").get()?.n, 1);
  } finally {
    if (!released) {
      child.kill();
      await exited.catch(() => {});
    }
    store.close();
    rmSync(dir, { recursive: true, force: true });
  }
});
