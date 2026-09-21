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
