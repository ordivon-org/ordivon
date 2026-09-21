import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";

import { AdmissionLabError } from "../src/errors.ts";
import type { EffectRequest } from "../src/model.ts";
import { PrincipalStore } from "../src/principal-store.ts";

function effect(seed: string): EffectRequest {
  const id = `sha256:${createHash("sha256").update("id:" + seed).digest("hex")}`;
  const digest = `sha256:${createHash("sha256").update("digest:" + seed).digest("hex")}`;
  return {
    effectId: id,
    effectDigest: digest,
    action: "site.publish",
    resource: "/site/publish",
    audience: "https://example.test",
    riskClass: "R4",
    effectType: "website.site.publish",
  };
}

test("WebAuthn challenge is purpose-bound and one-shot", () => {
  const store = new PrincipalStore(":memory:");
  store.ensurePrincipal("principal:test", "test", "Test", 100);
  const created = store.createChallenge(
    "grant-issue",
    "principal:test",
    "challenge",
    { grantId: "g1" },
    200,
  );
  const consumed = store.consumeChallenge(created.challengeId, "grant-issue", 150);
  assert.equal(consumed.payloadDigest, created.payloadDigest);
  assert.throws(
    () => store.consumeChallenge(created.challengeId, "grant-issue", 151),
    (error: unknown) =>
      error instanceof AdmissionLabError &&
      error.code === "webauthn_challenge_invalid",
  );
  store.close();
});

test("effect approval is bound to principal, effect id, and effect digest, then consumed", () => {
  const store = new PrincipalStore(":memory:");
  store.ensurePrincipal("principal:test", "test", "Test", 100);
  store.putCredential(
    "principal:test",
    {
      id: "credential",
      publicKey: new Uint8Array([1, 2, 3]),
      counter: 0,
      transports: ["internal"],
      deviceType: "singleDevice",
      backedUp: false,
    },
    100,
  );

  const approved = effect("approved");
  const other = effect("other");
  store.registerPendingEffect("principal:test", approved, 100, 300);
  store.putEffectApproval(
    "principal:test",
    "credential",
    approved.effectId,
    approved.effectDigest,
    110,
    120,
  );

  assert.equal(
    store.lookupEffectApproval("principal:test", approved, 120).verified,
    true,
  );
  assert.equal(
    store.lookupEffectApproval("principal:test", other, 120).verified,
    false,
  );
  assert.equal(
    store.lookupEffectApproval("principal:other", approved, 120).verified,
    false,
  );

  store.consumeEffectApproval("principal:test", approved, 121);
  assert.equal(
    store.lookupEffectApproval("principal:test", approved, 122).verified,
    false,
  );
  store.close();
});

test("pending effect identity cannot be silently rebound to a different digest", () => {
  const store = new PrincipalStore(":memory:");
  store.ensurePrincipal("principal:test", "test", "Test", 100);
  const first = effect("first");
  const conflicting: EffectRequest = {
    ...first,
    effectDigest: `sha256:${"f".repeat(64)}`,
  };
  store.registerPendingEffect("principal:test", first, 100, 300);
  store.registerPendingEffect("principal:test", conflicting, 110, 300);
  const pending = store.requirePendingEffect("principal:test", first.effectId, 120);
  assert.equal(pending.effectDigest, first.effectDigest);
  store.close();
});
