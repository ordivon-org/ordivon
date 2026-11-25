import assert from "node:assert/strict";
import { test } from "node:test";

import { WebProblem } from "../src/errors.ts";
import {
  credentialFromRow,
  effectReceiptFromRow,
  grantFromRow,
  principalFromRow,
  sessionFromRow,
} from "../src/store-row-projections.ts";

test("row projections preserve principal and session identities without DB access", () => {
  assert.deepEqual(principalFromRow({
    principal_id: "p1", user_name: "alice", display_name: "Alice",
  }), { principalId: "p1", userName: "alice", displayName: "Alice" });
  assert.deepEqual(sessionFromRow({
    session_id: "s1", token_hash: "hash", principal_id: "p1",
    created_at: 1, authenticated_at: 2, last_seen_at: 3,
    idle_expires_at: 4, absolute_expires_at: 5, revoked_at: null,
    authn_method: "webauthn", user_agent: null,
  }), {
    sessionId: "s1", principalId: "p1", createdAt: 1, authenticatedAt: 2,
    lastSeenAt: 3, idleExpiresAt: 4, absoluteExpiresAt: 5, revokedAt: null,
    authnMethod: "webauthn", userAgent: null,
  });
});

test("credential projection defensively copies key bytes and keeps corruption fail-closed", () => {
  const publicKey = Uint8Array.of(3, 7);
  const row = {
    credential_id: "c1", principal_id: "p1", public_key: publicKey,
    counter: 2, transports_json: '["usb"]', device_type: "singleDevice",
    backed_up: 1, created_at: 1, last_used_at: 2, revoked_at: null,
  };
  const credential = credentialFromRow(row);
  publicKey[0] = 99;
  assert.deepEqual([...credential.publicKey], [3, 7]);
  assert.equal(credential.backedUp, true);
  assert.deepEqual(credential.transports, ["usb"]);
  assert.throws(
    () => credentialFromRow({ ...row, transports_json: '["usb", 4]' }),
    (error: unknown) => error instanceof WebProblem &&
      error.status === 500 && error.code === "credential-corrupt",
  );
});

test("grant and committed effect projections retain exact security audit fields", () => {
  const grant = grantFromRow({
    grant_id: "g1", grant_digest: "digest:g1",
    principal_id: "p1", agent_id: "a1", audience: "test",
    allowed_actions_json: '["create","publish"]',
    resource_prefixes_json: '["resource:"]',
    expires_at: 100, max_risk_class: "R4", step_up_at_or_above: "R2",
    remaining_effects: 3, active: 1, revision: 7,
  });
  assert.deepEqual(grant.allowedActions, ["create", "publish"]);
  assert.equal(grant.active, true);
  assert.equal(grant.revision, 7);
  const effect = effectReceiptFromRow({
    effect_id: "e1", effect_digest: "digest:e1",
    principal_id: "p1", agent_id: "a1", grant_id: "g1",
    action: "publish", resource: "resource:r1",
    result_json: '{"ok":true}', committed_at: 12,
  });
  assert.deepEqual(effect.result, { ok: true });
  assert.equal(effect.committedAt, 12);
});

test("native Grant read projection rejects unrepresentable stored rows with Grant-specific error", async (t) => {
  const { DatabaseSync } = await import("node:sqlite");
  const { initializeWebStoreSchema } = await import("../src/store-schema.ts");
  const { AgentGrantStore } = await import("../src/store-agent-grants.ts");
  const cases = [
    ["agent_id", Uint8Array.of(97, 49)],
    ["audience", Uint8Array.of(119, 101, 98)],
    ["grant_digest", Uint8Array.of(100)],
    ["allowed_actions_json", "{broken"],
    ["resource_prefixes_json", '["/notes", 3]'],
    ["max_risk_class", "R9"],
    ["max_risk_class", "R4\n"],
    ["max_risk_class", Uint8Array.of(82, 52)],
    ["allowed_actions_json", new TextEncoder().encode('["create"]')],
    ["step_up_at_or_above", "unknown"],
    ["remaining_effects", 1.5],
    ["revision", 1.5],
    ["expires_at", "not-a-time"],
    ["expires_at", 1.5],
  ] as const;
  for (const [column, value] of cases) {
    await t.test(column + "=" + value, () => {
      const db = new DatabaseSync(":memory:");
      try {
        initializeWebStoreSchema(db);
        db.prepare("INSERT INTO principals VALUES (?, ?, ?, ?)").run("p1", "alice", "Alice", 1);
        const store = new AgentGrantStore(db, () => {});
        const created = store.createAgentGrant({
          grantId: "g1", principalId: "p1", agentId: "a1", audience: "web",
          allowedActions: ["create"], resourcePrefixes: ["/notes"],
          expiresAtEpochSeconds: 100, maxRiskClass: "R4",
          stepUpAtOrAbove: "R2", remainingEffects: 3,
        }, 1);
        assert.deepEqual(store.getAgentGrant("g1"), created);
        assert.deepEqual(store.listAgentGrants("p1"), [created]);
        db.prepare("UPDATE agent_grants SET remaining_effects = 0, active = 0, revision = 2 WHERE grant_id = ?").run("g1");
        assert.deepEqual(store.getAgentGrant("g1"), { ...created, remainingEffects: 0, active: false, revision: 2 });
        db.prepare("UPDATE agent_grants SET remaining_effects = 3, active = 1, revision = 1 WHERE grant_id = ?").run("g1");
        db.prepare("UPDATE agent_grants SET " + column + " = ? WHERE grant_id = ?").run(value, "g1");
        const invalid = (error: unknown) => error instanceof WebProblem &&
          error.status === 500 && error.code === "agent-grant-corrupt";
        assert.throws(() => store.getAgentGrant("g1"), invalid);
        assert.throws(() => store.listAgentGrants("p1"), invalid);
      } finally {
        db.close();
      }
    });
  }
});
