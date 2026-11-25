import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { WebStore } from "../src/store.ts";
import { WebProblem } from "../src/errors.ts";
import { now, principalId, seed } from "./fixtures/effect-recovery.ts";

for (const consumer of ["challenge", "dpop"] as const) {
  for (const phase of ["begin-ack", "commit-ack", "rollback-close", "busy", "nested"] as const) {
    test(consumer + " native transaction recovery: " + phase, () => {
      const dir = mkdtempSync(join(tmpdir(), "ordivon-owner-transaction-"));
      const path = join(dir, "web.sqlite");
      const store = new WebStore(path);
      seed(store);
      const challenge = store.createChallenge("effect-approve", principalId, "fixture", now);
      const peer = new WebStore(path);
      const proof = "proof:" + phase;
      const operation = () => consumer === "challenge"
        ? store.consumeChallenge(challenge.challengeId, "effect-approve", now)
        : store.consumeDpopProof(proof, now);
      const observe = () => consumer === "challenge"
        ? peer.db.prepare("SELECT consumed_at AS observed FROM webauthn_challenges WHERE challenge_id = ?").get(challenge.challengeId)?.observed !== null
        : peer.db.prepare("SELECT count(*) AS n FROM dpop_proofs").get()?.n === 1;
      const nativeExec = store.db.exec.bind(store.db);
      const original = new Error("injected " + phase);
      const rollback = new Error("rollback before native call");
      const close = new Error("close before native call");
      try {
        if (phase === "busy") {
          peer.db.exec("BEGIN IMMEDIATE");
          try {
            assert.throws(operation, (e: unknown) => e instanceof WebProblem && e.status === 503 && e.code === consumer + "-writer-busy");
            assert.equal(store.db.isTransaction, false);
            assert.equal(peer.db.isTransaction, true);
          } finally { peer.db.exec("ROLLBACK"); }
          assert.equal(observe(), false);
          operation();
          assert.equal(observe(), true);
          return;
        }
        if (phase === "nested") {
          store.db.exec("BEGIN IMMEDIATE");
          try {
            assert.throws(operation, (e: unknown) => e instanceof WebProblem && e.code === consumer + "-transaction-active");
            assert.equal(store.db.isTransaction, true);
          } finally { store.db.exec("ROLLBACK"); }
          assert.equal(observe(), false);
          return;
        }
        Object.defineProperty(store.db, "exec", { configurable: true, value: (sql: string) => {
          if (phase === "rollback-close" && sql === "COMMIT") throw original;
          if (phase === "rollback-close" && sql === "ROLLBACK") throw rollback;
          nativeExec(sql);
          if ((phase === "begin-ack" && sql === "BEGIN IMMEDIATE") ||
              (phase === "commit-ack" && sql === "COMMIT")) throw original;
        }});
        if (phase === "rollback-close") {
          Object.defineProperty(store.db, "close", { configurable: true, value: () => { throw close; } });
        }
        try {
          assert.throws(operation, (e: unknown) => phase === "rollback-close"
            ? e instanceof AggregateError && e.errors[0] === original && e.errors[1] === rollback && e.errors[2] === close
            : e === original);
          assert.equal(observe(), phase === "commit-ack");
          if (phase === "rollback-close") {
            assert.equal(store.db.isOpen, true);
            assert.equal(store.db.isTransaction, true);
            assert.throws(() => store.getPrincipal(principalId), (e: unknown) => e instanceof WebProblem && e.code === "web-store-recovery-required");
          } else {
            assert.equal(store.db.isTransaction, false);
          }
        } finally {
          Reflect.deleteProperty(store.db, "exec");
          Reflect.deleteProperty(store.db, "close");
        }
        if (phase === "rollback-close") {
          store.close();
          assert.equal(observe(), false);
        } else if (phase === "commit-ack") {
          assert.throws(operation, (e: unknown) => e instanceof WebProblem && e.code === (consumer === "challenge" ? "challenge-invalid" : "dpop-proof-replayed"));
          assert.equal(observe(), true);
        } else {
          operation();
          assert.equal(observe(), true);
        }
      } finally {
        peer.close();
        store.close();
        rmSync(dir, { recursive: true, force: true });
      }
    });
  }
}

test("DPoP expiry cleanup, replay denial and insertion retain the original atomic boundary", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-owner-dpop-expiry-"));
  const path = join(dir, "web.sqlite");
  const store = new WebStore(path);
  const peer = new WebStore(path);
  try {
    store.consumeDpopProof("expired", now, 1);
    store.consumeDpopProof("live", now, 10);
    const before = peer.db.prepare("SELECT * FROM dpop_proofs ORDER BY proof_hash").all();
    assert.equal(before.length, 2);
    assert.throws(() => store.consumeDpopProof("live", now + 1), (e: unknown) =>
      e instanceof WebProblem && e.code === "dpop-proof-replayed");
    // A denied request may not commit its earlier expiry cleanup.
    assert.deepEqual(peer.db.prepare("SELECT * FROM dpop_proofs ORDER BY proof_hash").all(), before);
    store.consumeDpopProof("expired", now + 1, 10);
    const after = peer.db.prepare("SELECT * FROM dpop_proofs ORDER BY proof_hash").all();
    assert.equal(after.length, 2);
    assert.deepEqual(after.map(row => row.expires_at).sort(), [now + 10, now + 11]);
    assert.throws(() => peer.consumeDpopProof("expired", now + 1), (e: unknown) =>
      e instanceof WebProblem && e.code === "dpop-proof-replayed");
    assert.deepEqual(peer.db.prepare("SELECT * FROM dpop_proofs ORDER BY proof_hash").all(), after);
  } finally { peer.close(); store.close(); rmSync(dir, { recursive: true, force: true }); }
});

test("Challenge rejection preserves the independent DPoP and Challenge records", () => {
  const dir = mkdtempSync(join(tmpdir(), "ordivon-owner-cross-consumer-"));
  const path = join(dir, "web.sqlite");
  const store = new WebStore(path);
  seed(store);
  const peer = new WebStore(path);
  try {
    store.consumeDpopProof("live", now);
    const first = store.createChallenge("effect-approve", principalId, "first", now, 1, { n: 1 });
    const second = store.createChallenge("effect-approve", principalId, "second", now, 20, { n: 2 });
    const snapshot = () => ({
      proofs: peer.db.prepare("SELECT * FROM dpop_proofs ORDER BY proof_hash").all(),
      challenges: peer.db.prepare("SELECT * FROM webauthn_challenges ORDER BY challenge_id").all(),
    });
    const before = snapshot();
    for (const [id, purpose, at] of [[first.challengeId, "effect-approve", now+1], [second.challengeId, "grant-issue", now]] as const) {
      assert.throws(() => store.consumeChallenge(id, purpose, at), (e: unknown) =>
        e instanceof WebProblem && e.code === "challenge-invalid");
      assert.deepEqual(snapshot(), before);
    }
    assert.deepEqual(store.consumeChallenge(second.challengeId, "effect-approve", now), second);
    const after = snapshot();
    assert.deepEqual(after.proofs, before.proofs);
    assert.throws(() => peer.consumeChallenge(second.challengeId, "effect-approve", now), (e: unknown) =>
      e instanceof WebProblem && e.code === "challenge-invalid");
    assert.deepEqual(snapshot(), after);
  } finally { peer.close(); store.close(); rmSync(dir, { recursive: true, force: true }); }
});

test("DPoP identity byte-length and TTL validation do not mutate replay state", () => {
  const store = new WebStore(":memory:");
  try {
    const read = () => store.db.prepare("SELECT * FROM dpop_proofs ORDER BY proof_hash").all();
    store.consumeDpopProof("prior", now, 1);
    const prior = read();
    for (const [proof, ttl] of [
      ["", 600], ["a".repeat(257), 600], ["é".repeat(129), 600],
      ["valid", 0], ["valid", -1], ["valid", 1.5],
      ["valid", Number.MAX_SAFE_INTEGER + 1], ["valid", NaN],
    ] as const) {
      assert.throws(() => store.consumeDpopProof(proof, now + 1, ttl), (e: unknown) =>
        e instanceof WebProblem && e.status === 401 && e.code === "dpop-proof-invalid");
      assert.deepEqual(read(), prior);
      assert.equal(store.db.isTransaction, false);
    }
    store.consumeDpopProof("é".repeat(128), now + 1, 1);
    assert.equal(read().length, 1);
    assert.equal(read()[0]?.expires_at, now + 2);
    assert.throws(() => store.consumeDpopProof("é".repeat(128), now + 1), (e: unknown) =>
      e instanceof WebProblem && e.code === "dpop-proof-replayed");
  } finally { store.close(); }
});

test("Challenge native zero-row consumption cannot return a successful record", () => {
  const store = new WebStore(":memory:");
  try {
    seed(store);
    const challenge = store.createChallenge("effect-approve", principalId, "race", now);
    store.db.exec("CREATE TEMP TRIGGER skip_consume BEFORE UPDATE ON webauthn_challenges BEGIN SELECT RAISE(IGNORE); END;");
    assert.throws(() => store.consumeChallenge(challenge.challengeId, "effect-approve", now), (e: unknown) =>
      e instanceof WebProblem && e.code === "challenge-race");
    assert.equal(store.db.isTransaction, false);
    assert.equal(store.db.prepare("SELECT consumed_at FROM webauthn_challenges WHERE challenge_id = ?").get(challenge.challengeId)?.consumed_at, null);
    store.db.exec("DROP TRIGGER skip_consume");
    assert.deepEqual(store.consumeChallenge(challenge.challengeId, "effect-approve", now), challenge);
    assert.throws(() => store.consumeChallenge(challenge.challengeId, "effect-approve", now), (e: unknown) =>
      e instanceof WebProblem && e.code === "challenge-invalid");
  } finally { store.close(); }
});

test("Challenge payload without JSON representation does not create a row", () => {
  const store = new WebStore(":memory:");
  try {
    seed(store);
    assert.throws(() => store.createChallenge("effect-approve", principalId, "invalid", now, 120, Symbol("no JSON")), (e: unknown) =>
      e instanceof WebProblem && e.code === "challenge-payload-invalid");
    assert.equal(store.db.prepare("SELECT count(*) AS n FROM webauthn_challenges").get()?.n, 0);
  } finally { store.close(); }
});
