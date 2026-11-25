import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { WebStore } from "../src/store.ts";
import { WebProblem } from "../src/errors.ts";
import { runEffectTransaction } from "../src/store-effect-transaction.ts";
import { agentId, commit, effect, now, principalId, seed } from "./fixtures/effect-recovery.ts";
import type { AgentGrantSnapshot } from "../src/model.ts";

function withDatabase(run: (path: string, store: WebStore, grant: AgentGrantSnapshot) => void) {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-effect-recovery-"));
  const path = join(dir, "web.sqlite");
  const store = new WebStore(path);
  try {
    run(path, store, seed(store));
  } finally {
    if (store.db.isOpen) store.close();
    rmSync(dir, { recursive: true, force: true });
  }
}
function assertCommitted(store: WebStore, grant: AgentGrantSnapshot, id: string) {
  assert.ok(store.getAgentEffect(effect(id).effectId));
  assert.equal(store.getAgentGrant(grant.grantId).remainingEffects, 1);
  assert.equal(store.getAgentGrant(grant.grantId).revision, grant.revision + 1);
  assert.equal(store.db.prepare("SELECT count(*) AS n FROM agent_effects").get()?.n, 1);
  assert.equal(store.db.prepare("SELECT count(*) AS n FROM canary_notes").get()?.n, 1);
  assert.equal(store.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type = 'agent.effect.committed'").get()?.n, 1);
}

test("BEGIN acknowledgement loss cannot leave the shared connection in an orphan transaction", () => {
  withDatabase((_path, store, grant) => {
    const nativeExec = store.db.exec.bind(store.db);
    const original = new Error("BEGIN acknowledgement lost");
    Object.defineProperty(store.db, "exec", { configurable: true, value: (sql: string) => {
      nativeExec(sql);
      if (sql === "BEGIN IMMEDIATE") throw original;
    }});
    try {
      assert.throws(() => commit(store, grant, "begin"), (error: unknown) => error === original);
    } finally {
      Reflect.deleteProperty(store.db, "exec");
    }
    assert.equal(store.db.isTransaction, false);
    assert.equal(store.getAgentEffect(effect("begin").effectId), null);
    assert.equal(commit(store, grant, "begin").replayed, false);
    assertCommitted(store, grant, "begin");
  });
});

test("a failed rollback quarantines the shared connection and preserves both failures", () => {
  withDatabase((path, store, grant) => {
    const nativeExec = store.db.exec.bind(store.db);
    const original = new Error("COMMIT failed before native call");
    const rollback = new Error("ROLLBACK failed before native call");
    Object.defineProperty(store.db, "exec", { configurable: true, value: (sql: string) => {
      if (sql === "COMMIT") throw original;
      if (sql === "ROLLBACK") throw rollback;
      nativeExec(sql);
    }});
    try {
      assert.throws(() => commit(store, grant, "rollback"), (error: unknown) =>
        error instanceof AggregateError && error.errors[0] === original && error.errors[1] === rollback);
    } finally {
      Reflect.deleteProperty(store.db, "exec");
    }
    assert.equal(store.db.isOpen, false);
    store.close(); // explicit owner shutdown is idempotent even after quarantine
    assert.throws(() => store.getAgentGrant(grant.grantId));
    const reopened = new WebStore(path);
    try {
      assert.equal(reopened.getAgentEffect(effect("rollback").effectId), null);
      assert.equal(commit(reopened, grant, "rollback").replayed, false);
      assertCommitted(reopened, grant, "rollback");
    } finally { reopened.close(); }
  });
});

test("effect transaction refuses an existing caller transaction without rolling it back", () => {
  withDatabase((_path, store, grant) => {
    store.db.exec("BEGIN IMMEDIATE");
    try {
      assert.throws(() => commit(store, grant, "nested"), (error: unknown) =>
        error instanceof WebProblem && error.code === "effect-transaction-active");
      assert.equal(store.db.isTransaction, true);
      assert.equal(store.getAgentEffect(effect("nested").effectId), null);
    } finally { store.db.exec("ROLLBACK"); }
    assert.equal(commit(store, grant, "nested").replayed, false);
    assertCommitted(store, grant, "nested");
  });
});

for (const phase of ["before-commit", "after-commit"] as const) {
  test("on-disk WAL survives abrupt child process termination: " + phase, () => {
    withDatabase((path, store, grant) => {
      store.close();
      const child = spawnSync(process.execPath, [fileURLToPath(new URL("./fixtures/effect-crash-child.ts", import.meta.url)), path, phase],
        { encoding: "utf8", timeout: 10000 });
      assert.equal(child.error, undefined);
      assert.equal(child.signal, "SIGKILL", child.stderr);
      assert.equal(child.stdout, "reached:" + phase + "\n");
      const reopened = new WebStore(path);
      try {
        const committed = phase === "after-commit";
        assert.equal(reopened.getAgentEffect(effect(phase).effectId) !== null, committed);
        assert.equal(reopened.getAgentGrant(grant.grantId).remainingEffects, committed ? 1 : 2);
        assert.equal(commit(reopened, grant, phase).replayed, committed);
        assertCommitted(reopened, grant, phase);
      } finally { reopened.close(); }
    });
  });
}

test("a close acknowledgement error retains the original transaction and rollback failures", () => {
  withDatabase((path, store, grant) => {
    const nativeExec = store.db.exec.bind(store.db);
    const nativeClose = store.db.close.bind(store.db);
    const original = new Error("commit fault");
    const rollback = new Error("rollback fault");
    const close = new Error("close acknowledgement lost");
    Object.defineProperty(store.db, "exec", { configurable: true, value: (sql: string) => {
      if (sql === "COMMIT") throw original;
      if (sql === "ROLLBACK") throw rollback;
      nativeExec(sql);
    }});
    Object.defineProperty(store.db, "close", { configurable: true, value: () => {
      nativeClose();
      throw close;
    }});
    try {
      assert.throws(() => commit(store, grant, "close-ack"), (error: unknown) =>
        error instanceof AggregateError && error.errors.length === 3 &&
        error.errors[0] === original && error.errors[1] === rollback && error.errors[2] === close);
    } finally {
      Reflect.deleteProperty(store.db, "exec");
      Reflect.deleteProperty(store.db, "close");
    }
    assert.equal(store.db.isOpen, false);
    const reopened = new WebStore(path);
    try {
      assert.equal(reopened.getAgentEffect(effect("close-ack").effectId), null);
      assert.equal(reopened.getAgentGrant(grant.grantId).remainingEffects, 2);
      assert.equal(reopened.db.prepare("SELECT count(*) AS n FROM canary_notes").get()?.n, 0);
    } finally { reopened.close(); }
  });
});

test("an existing caller transaction is also rejected on the historical replay fast path", () => {
  withDatabase((_path, store, grant) => {
    const committed = commit(store, grant, "historical");
    store.db.exec("BEGIN IMMEDIATE");
    try {
      assert.throws(() => commit(store, grant, "historical"), (error: unknown) =>
        error instanceof WebProblem && error.code === "effect-transaction-active");
      assert.equal(store.db.isTransaction, true);
    } finally { store.db.exec("ROLLBACK"); }
    assert.deepEqual(commit(store, grant, "historical"), { receipt: committed.receipt, replayed: true });
    assertCommitted(store, grant, "historical");
  });
});

test("approved publish cannot commit a missing or already published note", () => {
  withDatabase((_path, store) => {
    store.putCredential(principalId, {
      id: "credential:recovery", publicKey: new Uint8Array([1, 2, 3]),
      counter: 0, transports: ["internal"], deviceType: "singleDevice", backedUp: false,
    }, now);
    const grant = store.createAgentGrant({
      grantId: "grant:publish", principalId, agentId, audience: "https://example.test",
      allowedActions: ["canary.note.publish"], resourcePrefixes: ["/canary/notes"],
      expiresAtEpochSeconds: now + 60, maxRiskClass: "R4", stepUpAtOrAbove: "R4", remainingEffects: 2,
    }, now);
    const note = store.createCanaryNote(principalId, "draft", now);
    // Native fixture state, not a second publication path.
    store.db.prepare("UPDATE canary_notes SET state = 'PUBLISHED', published_at = ? WHERE note_id = ?").run(now, note.noteId);
    for (const noteId of ["missing", note.noteId]) {
      const request = { ...effect(noteId), action: "canary.note.publish", resource: "/canary/notes/" + noteId,
        riskClass: "R4" as const, effectType: "website.canary.note.publish" };
      store.putEffectApproval(principalId, "credential:recovery", request.effectId, request.effectDigest, now);
      assert.throws(() => store.commitAgentCanaryPublish(grant, agentId, request, noteId, now), (error: unknown) =>
        error instanceof WebProblem && error.code === "canary-note-not-publishable");
      assert.equal(store.effectApproval(principalId, request, now).verified, true);
      assert.equal(store.getAgentEffect(request.effectId), null);
      assert.deepEqual(store.getAgentGrant(grant.grantId), grant);
      assert.equal(store.db.isTransaction, false);
    }
  });
});

test("rollback and close failure before native close cannot expose tentative owner state", () => {
  withDatabase((path, store, grant) => {
    const nativeExec = store.db.exec.bind(store.db);
    const original = new Error("commit before native call");
    const rollback = new Error("rollback before native call");
    const close = new Error("close before native call");
    const historical = commit(store, grant, "quarantine-historical");
    const current = store.getAgentGrant(grant.grantId);
    const peer = new WebStore(path);
    try {
      Object.defineProperty(store.db, "exec", { configurable: true, value: (sql: string) => {
        if (sql === "COMMIT") throw original;
        if (sql === "ROLLBACK") throw rollback;
        nativeExec(sql);
      }});
      Object.defineProperty(store.db, "close", { configurable: true, value: () => { throw close; } });
      try {
        assert.throws(() => commit(store, current, "quarantine"), (error: unknown) =>
          error instanceof AggregateError && error.errors.length === 3 &&
          error.errors[0] === original && error.errors[1] === rollback && error.errors[2] === close);
        assert.equal(store.db.isOpen, true);
        assert.equal(store.db.isTransaction, true);
        assert.equal(peer.getAgentEffect(effect("quarantine").effectId), null);
        assert.deepEqual(peer.getAgentGrant(grant.grantId), current);
        assert.deepEqual(peer.getAgentEffect(effect("quarantine-historical").effectId), historical.receipt);

        const checks: [string, () => unknown][] = [
          ["receipt", () => store.getAgentEffect(effect("quarantine").effectId)],
          ["historical replay", () => store.resolveAgentEffectReplay(agentId, effect("quarantine-historical"))],
          ["grant", () => store.getAgentGrant(grant.grantId)],
          ["note read", () => store.listCanaryNotes(principalId)],
          ["note write", () => store.createCanaryNote(principalId, "must not write", now)],
          ["audit", () => store.audit("test", now, principalId, null, null, {})],
          ["principal", () => store.getPrincipal(principalId)],
          ["session read", () => store.listSessions(principalId)],
          ["challenge write", () => store.createChallenge("login", principalId, "test", now)],
          ["approval", () => store.effectApproval(principalId, effect("quarantine"), now)],
          ["effect retry", () => commit(store, current, "quarantine")],
          ["native coordinator", () => runEffectTransaction(store.db, () => assert.fail("quarantined write callback ran"))],
        ];
        for (const [name, operation] of checks) {
          assert.throws(operation, (error: unknown) =>
            error instanceof WebProblem && error.status === 503 && error.code === "web-store-recovery-required", name);
        }
      } finally {
        Reflect.deleteProperty(store.db, "exec");
        Reflect.deleteProperty(store.db, "close");
      }
      // Explicit owner shutdown is permitted; no automatic retry of the effect.
      store.close();
      assert.equal(store.db.isOpen, false);
      assert.equal(peer.getAgentEffect(effect("quarantine").effectId), null);
      assert.deepEqual(peer.getAgentGrant(grant.grantId), current);
      assert.equal(peer.listCanaryNotes(principalId).length, 1);
      assert.equal(commit(peer, current, "quarantine").replayed, false);
      assert.equal(peer.listCanaryNotes(principalId).length, 2);
      assert.equal(peer.getAgentGrant(grant.grantId).remainingEffects, 0);
      assert.equal(peer.db.prepare("SELECT count(*) AS n FROM audit_events WHERE event_type = 'agent.effect.committed'").get()?.n, 2);
    } finally { peer.close(); }
  });
});

test("quarantine survives loss of rollback acknowledgement even when native state is idle", () => {
  withDatabase((path, store, grant) => {
    const nativeExec = store.db.exec.bind(store.db);
    const original = new Error("commit failed before native call");
    const rollback = new Error("rollback acknowledgement lost");
    const close = new Error("close failed before native call");
    const peer = new WebStore(path);
    try {
      Object.defineProperty(store.db, "exec", { configurable: true, value: (sql: string) => {
        if (sql === "COMMIT") throw original;
        nativeExec(sql);
        if (sql === "ROLLBACK") throw rollback;
      }});
      Object.defineProperty(store.db, "close", { configurable: true, value: () => { throw close; } });
      try {
        assert.throws(() => commit(store, grant, "idle-quarantine"), (error: unknown) =>
          error instanceof AggregateError && error.errors[0] === original &&
          error.errors[1] === rollback && error.errors[2] === close);
        assert.equal(store.db.isOpen, true);
        assert.equal(store.db.isTransaction, false);
        assert.equal(peer.getAgentEffect(effect("idle-quarantine").effectId), null);
        assert.deepEqual(peer.getAgentGrant(grant.grantId), grant);
        for (const operation of [
          () => store.getAgentEffect(effect("idle-quarantine").effectId),
          () => commit(store, grant, "idle-quarantine"),
          () => runEffectTransaction(store.db, () => assert.fail("quarantined callback ran")),
        ]) {
          assert.throws(operation, (error: unknown) =>
            error instanceof WebProblem && error.code === "web-store-recovery-required");
        }
        // A distinct connection is not contaminated by this local health marker.
        assert.equal(commit(peer, grant, "idle-quarantine").replayed, false);
        assertCommitted(peer, grant, "idle-quarantine");
        assert.throws(() => store.getAgentEffect(effect("idle-quarantine").effectId),
          (error: unknown) => error instanceof WebProblem && error.code === "web-store-recovery-required");
      } finally {
        Reflect.deleteProperty(store.db, "exec");
        Reflect.deleteProperty(store.db, "close");
      }
      store.close();
      assert.equal(store.db.isOpen, false);
    } finally { peer.close(); }
  });
});
