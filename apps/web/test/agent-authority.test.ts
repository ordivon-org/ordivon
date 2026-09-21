import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";

import { createWebApp } from "../src/app.ts";
import type { AgentRequestVerifier } from "../src/agent-authority.ts";
import type { WebConfig } from "../src/config.ts";
import type { VerifiedAgent } from "../src/model.ts";
import { WebStore } from "../src/store.ts";

const config: WebConfig = {
  host: "127.0.0.1",
  port: 8789,
  origin: "https://example.test",
  rpID: "example.test",
  rpName: "Ordivon Test",
  databasePath: ":memory:",
  bootstrapEnrollmentToken: "bootstrap-test",
  sessionIdleSeconds: 60,
  sessionAbsoluteSeconds: 300,
};

function effectId(label: string): string {
  return "sha256:" + createHash("sha256").update(label).digest("hex");
}

class FixedAgentVerifier implements AgentRequestVerifier {
  private readonly agent: VerifiedAgent;

  constructor(agent: VerifiedAgent) {
    this.agent = agent;
  }

  async verify() {
    return this.agent;
  }
}

async function fixture() {
  let currentTime = 1_800_000_000;
  const now = () => currentTime;
  const store = new WebStore(":memory:");
  store.ensurePrincipal("principal:test", "test-user", "Test User", now());
  store.putCredential(
    "principal:test",
    {
      id: "credential:test",
      publicKey: new Uint8Array([1, 2, 3]),
      counter: 0,
      transports: ["internal"],
      deviceType: "singleDevice",
      backedUp: false,
    },
    now(),
  );
  const agent: VerifiedAgent = {
    agentId: "oauth-client:agent-test",
    clientId: "agent-test",
    subject: "service-account-agent-test",
  };
  const grant = store.createAgentGrant(
    {
      grantId: "grant:test",
      principalId: "principal:test",
      agentId: agent.agentId,
      audience: config.origin,
      allowedActions: ["canary.note.create", "canary.note.publish"],
      resourcePrefixes: ["/canary/notes"],
      expiresAtEpochSeconds: now() + 3600,
      maxRiskClass: "R4",
      stepUpAtOrAbove: "R4",
      remainingEffects: 6,
    },
    now(),
  );
  const app = await createWebApp(config, {
    store,
    now,
    agentVerifier: new FixedAgentVerifier(agent),
  });
  return {
    app,
    store,
    agent,
    grant,
    now,
    advance(seconds: number) {
      currentTime += seconds;
    },
  };
}

test("Agent R2 create is admitted, exactly replayed, and conflicting reuse is rejected", async () => {
  const f = await fixture();
  const id = effectId("create-1");
  const first = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": id },
    payload: { content: "delegated draft" },
  });
  assert.equal(first.statusCode, 201);
  assert.equal(first.json().replayed, false);
  const receipt = first.json().receipt;
  assert.equal(receipt.agentId, f.agent.agentId);
  assert.equal(receipt.action, "canary.note.create");
  assert.equal(receipt.result.note.state, "DRAFT");

  const replay = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": id },
    payload: { content: "delegated draft" },
  });
  assert.equal(replay.statusCode, 200);
  assert.equal(replay.json().replayed, true);
  assert.deepEqual(replay.json().receipt, receipt);

  const conflict = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": id },
    payload: { content: "changed payload" },
  });
  assert.equal(conflict.statusCode, 409);
  assert.equal(conflict.json().title, "Effect conflict");

  const grant = f.store.getAgentGrant("grant:test");
  assert.equal(grant.remainingEffects, 5);
  assert.equal(grant.revision, 2);
  await f.app.close();
  f.store.close();
});

test("R4 publish requires effect-bound approval and consumes it exactly once", async () => {
  const f = await fixture();
  const create = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": effectId("draft-for-publish") },
    payload: { content: "publish me" },
  });
  assert.equal(create.statusCode, 201);
  const noteId = create.json().receipt.result.note.noteId as string;

  const publishId = effectId("publish-1");
  const firstPublish = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes/" + noteId + "/publish",
    headers: { "x-ordivon-effect-id": publishId },
  });
  assert.equal(firstPublish.statusCode, 428);
  const stepUp = firstPublish.json();
  assert.equal(stepUp.title, "Principal approval required");
  assert.equal(stepUp.effectId, publishId);

  const pending = f.store.requirePendingEffectApproval(
    "principal:test",
    publishId,
    f.now(),
  );
  f.store.putEffectApproval(
    "principal:test",
    "credential:test",
    publishId,
    pending.effectDigest,
    f.now(),
  );

  const approved = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes/" + noteId + "/publish",
    headers: { "x-ordivon-effect-id": publishId },
  });
  assert.equal(approved.statusCode, 200);
  assert.equal(approved.json().replayed, false);
  assert.equal(approved.json().receipt.result.note.state, "PUBLISHED");

  const approval = f.store.db
    .prepare("SELECT consumed_at FROM effect_approvals WHERE effect_id = ?")
    .get(publishId) as { consumed_at: number | null };
  assert.equal(approval.consumed_at, f.now());

  const replay = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes/" + noteId + "/publish",
    headers: { "x-ordivon-effect-id": publishId },
  });
  assert.equal(replay.statusCode, 200);
  assert.equal(replay.json().replayed, true);

  await f.app.close();
  f.store.close();
});

test("Grant revocation blocks future Effects without invalidating committed history", async () => {
  const f = await fixture();
  const committedId = effectId("before-revoke");
  const committed = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": committedId },
    payload: { content: "before revoke" },
  });
  assert.equal(committed.statusCode, 201);

  const grant = f.store.getAgentGrant("grant:test");
  const revoked = f.store.revokeAgentGrant(
    "principal:test",
    grant.grantId,
    grant.grantDigest,
    f.now(),
  );
  assert.equal(revoked.active, false);

  const future = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": effectId("after-revoke") },
    payload: { content: "must not commit" },
  });
  assert.equal(future.statusCode, 403);

  const historicalReplay = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": committedId },
    payload: { content: "before revoke" },
  });
  assert.equal(historicalReplay.statusCode, 200);
  assert.equal(historicalReplay.json().replayed, true);

  await f.app.close();
  f.store.close();
});

test("ambiguous matching Grants fail closed before admission", async () => {
  const f = await fixture();
  f.store.createAgentGrant(
    {
      grantId: "grant:duplicate",
      principalId: "principal:test",
      agentId: f.agent.agentId,
      audience: config.origin,
      allowedActions: ["canary.note.create"],
      resourcePrefixes: ["/canary/notes"],
      expiresAtEpochSeconds: f.now() + 3600,
      maxRiskClass: "R2",
      stepUpAtOrAbove: "R4",
      remainingEffects: 2,
    },
    f.now(),
  );

  const response = await f.app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": effectId("ambiguous") },
    payload: { content: "ambiguous" },
  });
  assert.equal(response.statusCode, 409);
  assert.equal(response.json().title, "Agent authority ambiguous");

  await f.app.close();
  f.store.close();
});

test("Agent routes fail closed when Security-owned Agent verification is absent", async () => {
  const store = new WebStore(":memory:");
  store.ensurePrincipal("principal:test", "test-user", "Test User", 100);
  const app = await createWebApp(config, { store, now: () => 100 });
  const response = await app.inject({
    method: "POST",
    url: "/api/agent/canary/notes",
    headers: { "x-ordivon-effect-id": effectId("no-verifier") },
    payload: { content: "blocked" },
  });
  assert.equal(response.statusCode, 503);
  assert.equal(response.json().title, "Agent verification unavailable");
  await app.close();
  store.close();
});
