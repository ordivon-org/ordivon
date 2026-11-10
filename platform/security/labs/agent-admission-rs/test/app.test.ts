import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";

import { createAgentAdmissionApp } from "../src/app.ts";
import { GrantStore } from "../src/grant-store.ts";
import type { EffectRequest } from "../src/model.ts";
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


test("resource grant scopes are canonical path segments, never raw startswith", () => {
  const store = new GrantStore(":memory:");
  const grant = (id: string, prefixes: readonly string[]) =>
    store.createGrant({
      grantId: id,
      principalId: "principal:user-123",
      agentId: "oauth-client:agent-research-17",
      audience,
      allowedActions: ["comment.create"],
      resourcePrefixes: prefixes,
      expiresAtEpochSeconds: 2_000_000_000,
      maxRiskClass: "R3",
      stepUpAtOrAbove: "R4",
      remainingEffects: 4,
    });
  grant("grant:path", ["/comments"]);
  const matches = (resource: string) =>
    store.resolveUniqueGrant(
      "oauth-client:agent-research-17",
      audience,
      "comment.create",
      resource,
      1_800_000_000,
    );

  assert.equal(matches("/comments/article-42").grantId, "grant:path");
  assert.equal(matches("/comments").grantId, "grant:path");
  for (const resource of [
    "/comments-evil",
    "/comments/../account/recovery",
    "/comments/%2e%2e/account",
    "/comments/./article-42",
    "/comments//article-42",
    "/comments/article-42?admin=true",
    "/comments/article-42#fragment",
    "/comments\\..\\secret",
    "/comments/\nadmin",
  ]) {
    assert.throws(
      () => matches(resource),
      (error: unknown) => error instanceof Error && "code" in error && error.code === "grant_not_found",
      resource,
    );
  }
  for (const invalid of [
    "/comments/../", "/comments%", "/comments//", "comments/", "/comments/./",
  ]) {
    assert.throws(
      () => grant("invalid:" + invalid, [invalid]),
      (error: unknown) => error instanceof Error && "code" in error && error.code === "invalid_grant",
      invalid,
    );
  }
  store.close();
});


test("commitComment rejects authority and materialized target mismatch inside transaction", () => {
  const store = new GrantStore(":memory:");
  const grant = store.createGrant({
    grantId: "grant:commit-boundary",
    principalId: "principal:user-123",
    agentId: "oauth-client:agent-research-17",
    audience,
    allowedActions: ["comment.create"],
    resourcePrefixes: ["/comments/article-42"],
    expiresAtEpochSeconds: 2_000_000_000,
    maxRiskClass: "R3",
    stepUpAtOrAbove: "R4",
    remainingEffects: 1,
  });
  const effect: EffectRequest = {
    effectId: id("commit-boundary"),
    effectDigest: id("commit-boundary-content"),
    action: "comment.create",
    resource: "/comments/article-42",
    audience,
    riskClass: "R2",
    effectType: "website.comment.create",
  };

  const deny = (effectOverride: typeof effect, target: string, grantOverride = grant) => {
    assert.throws(
      () => store.commitComment(grantOverride, effectOverride, target, "content", 1_800_000_000),
      (error: unknown) =>
        error instanceof Error &&
        "code" in error &&
        error.code === "effect_not_authorized",
    );
    assert.equal(store.getGrant(grant.grantId).remainingEffects, 1);
  };

  // A caller cannot authorize article-42 then materialize article-43.
  deny(effect, "article-43");
  // An alternate resource, action, audience, or Principal cannot borrow an old ALLOW.
  deny({ ...effect, resource: "/comments/article-43" }, "article-43");
  deny({ ...effect, action: "comment.delete" }, "article-42");
  deny({ ...effect, audience: "https://other.example.test" }, "article-42");
  deny({ ...effect, effectType: "website.comment.delete" }, "article-42");
  deny(effect, "article-42", { ...grant, principalId: "principal:forged" });

  store.revokeGrant(grant.grantId);
  assert.throws(
    () => store.commitComment(grant, effect, "article-42", "content", 1_800_000_000),
    (error: unknown) =>
      error instanceof Error && "code" in error && error.code === "grant_changed",
  );
  assert.equal(store.getGrant(grant.grantId).remainingEffects, 1);
  store.close();
});

test("commitComment materializes the exact authorized resource once and consumes one budget", () => {
  const store = new GrantStore(":memory:");
  const grant = store.createGrant({
    grantId: "grant:valid-commit",
    principalId: "principal:user-123",
    agentId: "oauth-client:agent-research-17",
    audience,
    allowedActions: ["comment.create"],
    resourcePrefixes: ["/comments/article-42"],
    expiresAtEpochSeconds: 2_000_000_000,
    maxRiskClass: "R3",
    stepUpAtOrAbove: "R4",
    remainingEffects: 1,
  });
  const effect: EffectRequest = {
    effectId: id("valid-commit"),
    effectDigest: id("valid-commit-content"),
    action: "comment.create",
    resource: "/comments/article-42",
    audience,
    riskClass: "R2",
    effectType: "website.comment.create",
  };
  const first = store.commitComment(grant, effect, "article-42", "hello", 1_800_000_000);
  assert.equal(first.replayed, false);
  assert.equal(first.receipt.articleId, "article-42");
  assert.equal(first.receipt.principalId, grant.principalId);
  assert.equal(first.receipt.agentId, grant.agentId);
  assert.equal(store.getGrant(grant.grantId).remainingEffects, 0);
  const replay = store.commitComment(grant, effect, "article-42", "hello", 1_800_000_000);
  assert.equal(replay.replayed, true);
  assert.equal(replay.receipt.commentId, first.receipt.commentId);
  assert.equal(store.getGrant(grant.grantId).remainingEffects, 0);
  store.close();
});
