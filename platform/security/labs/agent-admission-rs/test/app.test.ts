import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";

import { createAgentAdmissionApp } from "../src/app.ts";
import { GrantStore } from "../src/grant-store.ts";
import type { AgentVerifier } from "../src/oauth-verifier.ts";
import { OpaAdmissionEngine } from "../src/opa.ts";

const audience = "https://agent-admission.example.test";

const verifier: AgentVerifier = {
  async verify() {
    return {
      agentId: "oauth-client:agent-research-17",
      clientId: "agent-research-17",
      subject: "service-account-agent-research-17",
    };
  },
};

function id(seed: string): string {
  return `sha256:${createHash("sha256").update(seed).digest("hex")}`;
}

function request(effectId: string, content: string): Request {
  return new Request(`${audience}/api/articles/article-42/comments`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-ordivon-effect-id": effectId,
    },
    body: JSON.stringify({ content }),
  });
}

test("R2 effect commits once, exact replay survives budget exhaustion, changed reuse conflicts", async () => {
  const store = new GrantStore(":memory:");
  store.createGrant({
    grantId: "grant:test-comment",
    principalId: "principal:user-123",
    agentId: "oauth-client:agent-research-17",
    audience,
    allowedActions: ["comment.create"],
    resourcePrefixes: ["/comments/"],
    expiresAtEpochSeconds: 2_000_000_000,
    maxRiskClass: "R3",
    stepUpAtOrAbove: "R4",
    remainingEffects: 1,
  });
  const app = createAgentAdmissionApp({
    verifier,
    store,
    policy: new OpaAdmissionEngine(),
    audience,
    now: () => 1_800_000_000,
  });

  const effect = id("same-effect");
  const first = await app(request(effect, "hello"));
  assert.equal(first.status, 201);
  const firstBody = (await first.json()) as { replayed: boolean };
  assert.equal(firstBody.replayed, false);

  const replay = await app(request(effect, "hello"));
  assert.equal(replay.status, 200);
  const replayBody = (await replay.json()) as { replayed: boolean };
  assert.equal(replayBody.replayed, true);

  const conflict = await app(request(effect, "different"));
  assert.equal(conflict.status, 409);
  const conflictBody = (await conflict.json()) as { error: string };
  assert.equal(conflictBody.error, "effect_conflict");

  const exhausted = await app(request(id("second-effect"), "second"));
  assert.equal(exhausted.status, 403);
  const exhaustedBody = (await exhausted.json()) as { reason: string };
  assert.equal(exhaustedBody.reason, "effect-budget-exhausted");
  store.close();
});

test("ambiguous delegation fails closed before policy execution", async () => {
  const store = new GrantStore(":memory:");
  for (const grantId of ["grant:a", "grant:b"]) {
    store.createGrant({
      grantId,
      principalId: "principal:user-123",
      agentId: "oauth-client:agent-research-17",
      audience,
      allowedActions: ["comment.create"],
      resourcePrefixes: ["/comments/"],
      expiresAtEpochSeconds: 2_000_000_000,
      maxRiskClass: "R3",
      stepUpAtOrAbove: "R4",
      remainingEffects: 3,
    });
  }
  const app = createAgentAdmissionApp({
    verifier,
    store,
    policy: new OpaAdmissionEngine(),
    audience,
    now: () => 1_800_000_000,
  });
  const response = await app(request(id("ambiguous"), "hello"));
  assert.equal(response.status, 409);
  const body = (await response.json()) as { error: string };
  assert.equal(body.error, "grant_ambiguous");
  store.close();
});

test("R4 publish probe pauses for effect-bound principal step-up", async () => {
  const store = new GrantStore(":memory:");
  store.createGrant({
    grantId: "grant:publish",
    principalId: "principal:user-123",
    agentId: "oauth-client:agent-research-17",
    audience,
    allowedActions: ["site.publish"],
    resourcePrefixes: ["/site/"],
    expiresAtEpochSeconds: 2_000_000_000,
    maxRiskClass: "R4",
    stepUpAtOrAbove: "R4",
    remainingEffects: 1,
  });
  const app = createAgentAdmissionApp({
    verifier,
    store,
    policy: new OpaAdmissionEngine(),
    audience,
    now: () => 1_800_000_000,
  });
  const response = await app(
    new Request(`${audience}/api/publish-probe`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-ordivon-effect-id": id("publish"),
      },
      body: JSON.stringify({ probe: true }),
    }),
  );
  assert.equal(response.status, 428);
  const body = (await response.json()) as {
    outcome: string;
    reason: string;
  };
  assert.equal(body.outcome, "STEP_UP");
  assert.equal(body.reason, "principal-step-up-required");
  store.close();
});


test("DPoP proof replay ledger stores only a bounded hash and rejects reuse", () => {
  const store = new GrantStore(":memory:");
  store.consumeDpopProof("proof-jti-1", 1_800_000_000, 60);
  assert.throws(
    () => store.consumeDpopProof("proof-jti-1", 1_800_000_001, 60),
    (error: unknown) =>
      error instanceof Error &&
      "code" in error &&
      error.code === "dpop_proof_replayed",
  );
  store.consumeDpopProof("proof-jti-1", 1_800_000_061, 60);
  assert.throws(
    () => store.consumeDpopProof("x".repeat(257), 1_800_000_061, 60),
    (error: unknown) =>
      error instanceof Error &&
      "code" in error &&
      error.code === "dpop_proof_invalid",
  );
  store.close();
});


test("DPoP replay ledger consumes a proof once and expires it deterministically", () => {
  const store = new GrantStore(":memory:");
  store.consumeDpopProof("proof-jti-1", 1_800_000_000, 10);
  assert.throws(
    () => store.consumeDpopProof("proof-jti-1", 1_800_000_005, 10),
    (error: unknown) =>
      error instanceof Error &&
      "code" in error &&
      (error as { code: unknown }).code === "dpop_proof_replayed",
  );
  assert.doesNotThrow(() =>
    store.consumeDpopProof("proof-jti-1", 1_800_000_010, 10),
  );
  store.close();
});

test("a committed effect cannot be replayed by a different authenticated Agent", async () => {
  const store = new GrantStore(":memory:");
  store.createGrant({
    grantId: "grant:actor-bound",
    principalId: "principal:user-123",
    agentId: "oauth-client:agent-research-17",
    audience,
    allowedActions: ["comment.create"],
    resourcePrefixes: ["/comments/"],
    expiresAtEpochSeconds: 2_000_000_000,
    maxRiskClass: "R3",
    stepUpAtOrAbove: "R4",
    remainingEffects: 1,
  });
  const firstApp = createAgentAdmissionApp({
    verifier,
    store,
    policy: new OpaAdmissionEngine(),
    audience,
    now: () => 1_800_000_000,
  });
  const effect = id("actor-bound-effect");
  assert.equal((await firstApp(request(effect, "hello"))).status, 201);

  const otherVerifier: AgentVerifier = {
    async verify() {
      return {
        agentId: "oauth-client:agent-other",
        clientId: "agent-other",
        subject: "service-account-agent-other",
      };
    },
  };
  const otherApp = createAgentAdmissionApp({
    verifier: otherVerifier,
    store,
    policy: new OpaAdmissionEngine(),
    audience,
    now: () => 1_800_000_001,
  });
  const response = await otherApp(request(effect, "hello"));
  assert.equal(response.status, 403);
  const body = (await response.json()) as { error: string };
  assert.equal(body.error, "effect_actor_mismatch");
  store.close();
});

test("Grant paths cannot match sibling path names", () => {
  const store = new GrantStore(":memory:");
  store.createGrant({
    grantId: "grant:path-segment",
    principalId: "principal:user-123",
    agentId: "oauth-client:agent-research-17",
    audience,
    allowedActions: ["comment.create"],
    resourcePrefixes: ["/comments"],
    expiresAtEpochSeconds: 2_000_000_000,
    maxRiskClass: "R3",
    stepUpAtOrAbove: "R4",
    remainingEffects: 2,
  });
  assert.equal(
    store.resolveUniqueGrant("oauth-client:agent-research-17", audience, "comment.create", "/comments", 1_800_000_000).grantId,
    "grant:path-segment",
  );
  assert.equal(
    store.resolveUniqueGrant("oauth-client:agent-research-17", audience, "comment.create", "/comments/article-42", 1_800_000_000).grantId,
    "grant:path-segment",
  );
  assert.throws(
    () => store.resolveUniqueGrant("oauth-client:agent-research-17", audience, "comment.create", "/comments-private", 1_800_000_000),
    /No active delegation grant/,
  );
  store.close();
});


test("native GrantStore rejects path normalization aliases before admission", () => {
  const store = new GrantStore(":memory:");
  const base = {
    grantId: "grant:scope", principalId: "principal:proof",
    agentId: "agent:proof", audience, allowedActions: ["comment.create"],
    resourcePrefixes: ["/comments/"], expiresAtEpochSeconds: 2000000000,
    maxRiskClass: "R3" as const, stepUpAtOrAbove: "R4" as const,
    remainingEffects: 2,
  };
  store.createGrant(base);
  for (const resource of [
    "/comments/../account", "/comments/%2e%2e/account",
    "/comments//child", "/comments/./child",
    "/comments/child?admin=true", "/comments/child#private",
    "/comments\\..\\account", "/comments/\nadmin",
  ]) {
    assert.throws(() => store.resolveUniqueGrant(
      "agent:proof", audience, "comment.create", resource, 1800000000,
    ), (error: unknown) =>
      error instanceof Error && "code" in error && error.code === "grant_not_found",
      resource);
  }
  for (const prefix of ["/comments/../", "/comments//", "/comments%", "comments"]) {
    assert.throws(() => store.createGrant({
      ...base, grantId: "grant:invalid:" + prefix, resourcePrefixes: [prefix],
    }), (error: unknown) =>
      error instanceof Error && "code" in error && error.code === "invalid_grant",
      prefix);
  }
  assert.equal(store.resolveUniqueGrant(
    "agent:proof", audience, "comment.create", "/comments/article", 1800000000,
  ).grantId, base.grantId);
  store.close();
});


test("Lab commit PEP refuses changed materialized target, action, Principal and audience", () => {
  const store = new GrantStore(":memory:");
  const grant = store.createGrant({
    grantId: "grant:commit-pep", principalId: "principal:proof",
    agentId: "agent:proof", audience, allowedActions: ["comment.create"],
    resourcePrefixes: ["/comments/42"], expiresAtEpochSeconds: 2000000000,
    maxRiskClass: "R3", stepUpAtOrAbove: "R4", remainingEffects: 1,
  });
  const effect = {
    effectId: id("commit-pep"), effectDigest: id("commit-pep-content"),
    action: "comment.create", resource: "/comments/42", audience,
    riskClass: "R2" as const, effectType: "website.comment.create",
  };
  const reject = (candidate: typeof effect, articleId: string, selected = grant) => {
    assert.throws(() => store.commitComment(selected, candidate, articleId,
      "payload", 1800000000),
      (error: unknown) =>
        error instanceof Error && "code" in error && error.code === "effect_not_authorized",
    );
    assert.equal(store.getGrant(grant.grantId).remainingEffects, 1);
  };
  reject(effect, "43");
  reject({ ...effect, resource: "/comments/43" }, "43");
  reject({ ...effect, resource: "/comments/../42" }, "../42");
  reject({ ...effect, audience: "https://other.example" }, "42");
  reject({ ...effect, action: "comment.delete" }, "42");
  reject({ ...effect, effectType: "website.comment.delete" }, "42");
  reject(effect, "42", { ...grant, principalId: "principal:forged" });
  const committed = store.commitComment(grant, effect, "42", "payload", 1800000000);
  assert.equal(committed.replayed, false);
  assert.equal(committed.receipt.articleId, "42");
  assert.equal(store.getGrant(grant.grantId).remainingEffects, 0);
  store.close();
});
