import { createHash, randomBytes } from "node:crypto";
import { fileURLToPath } from "node:url";

import * as oauth from "oauth4webapi";
import { chromium } from "playwright";

function env(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (value === undefined || value === "") throw new Error(name + " is required");
  return value;
}

function freshEffectId(label: string): string {
  return "sha256:" + createHash("sha256").update(label).update(randomBytes(32)).digest("hex");
}

async function expectJson(
  response: Response,
  expectedStatus: number,
  label: string,
): Promise<Record<string, unknown>> {
  const body = (await response.json()) as Record<string, unknown>;
  if (response.status !== expectedStatus) {
    throw new Error(
      label + ": expected HTTP " + expectedStatus + ", got " + response.status + ": " + JSON.stringify(body),
    );
  }
  return body;
}

const audience = env("AGENT_ADMISSION_AUDIENCE", "http://127.0.0.1:8788");
const browserOrigin = env(
  "AGENT_ADMISSION_WEBAUTHN_ORIGIN",
  "http://localhost:8788",
);
const issuer = new URL(
  env(
    "AGENT_ADMISSION_ISSUER",
    "http://127.0.0.1:18080/realms/agent-admission-lab",
  ),
);
const enrollmentToken = env(
  "AGENT_ADMISSION_ENROLLMENT_TOKEN",
  "lab-enrollment-only",
);
const principalId = "principal:lab-owner";
const agentId = "oauth-client:agent-research-17";
const clientId = "agent-research-17";
const clientSecret = "lab-only-agent-secret";
const bundlePath = fileURLToPath(
  new URL(
    "../node_modules/@simplewebauthn/browser/dist/bundle/index.umd.min.js",
    import.meta.url,
  ),
);

const chromiumExecutable = env(
  "AGENT_ADMISSION_CHROMIUM_EXECUTABLE",
  chromium.executablePath(),
);
const browser = await chromium.launch({
  headless: true,
  executablePath: chromiumExecutable,
  args: ["--host-resolver-rules=MAP localhost 127.0.0.1"],
});
const context = await browser.newContext();
const page = await context.newPage();
const cdp = await context.newCDPSession(page);
await cdp.send("WebAuthn.enable");
const virtual = (await cdp.send("WebAuthn.addVirtualAuthenticator", {
  options: {
    protocol: "ctap2",
    transport: "internal",
    hasResidentKey: true,
    hasUserVerification: true,
    isUserVerified: true,
    automaticPresenceSimulation: true,
  },
})) as { authenticatorId: string };

try {
  await page.goto(browserOrigin + "/webauthn-lab", { waitUntil: "domcontentloaded" });
  await page.addScriptTag({ path: bundlePath });

  const enrollment = await page.evaluate(
    async ({ token, principal }) => {
      const api = (globalThis as unknown as {
        SimpleWebAuthnBrowser: {
          startRegistration(input: { optionsJSON: unknown }): Promise<unknown>;
        };
      }).SimpleWebAuthnBrowser;

      const optionsResponse = await fetch("/api/webauthn/enroll/options", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-lab-enrollment-token": token,
        },
        body: JSON.stringify({
          principalId: principal,
          userName: "lab-owner",
          displayName: "Lab Owner",
        }),
      });
      const optionsBody = (await optionsResponse.json()) as {
        challengeId: string;
        options: unknown;
      };
      const credential = await api.startRegistration({
        optionsJSON: optionsBody.options,
      });
      const verifyResponse = await fetch("/api/webauthn/enroll/verify", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-lab-enrollment-token": token,
        },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: credential,
        }),
      });
      const verifyBody = await verifyResponse.json();

      const replayResponse = await fetch("/api/webauthn/enroll/verify", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-lab-enrollment-token": token,
        },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: credential,
        }),
      });
      return {
        optionsStatus: optionsResponse.status,
        verifyStatus: verifyResponse.status,
        verifyBody,
        replayStatus: replayResponse.status,
        replayBody: await replayResponse.json(),
      };
    },
    { token: enrollmentToken, principal: principalId },
  );

  if (enrollment.optionsStatus !== 200 || enrollment.verifyStatus !== 201) {
    throw new Error("WebAuthn enrollment failed: " + JSON.stringify(enrollment));
  }
  if (enrollment.replayStatus !== 409) {
    throw new Error(
      "registration challenge replay expected 409, got " + enrollment.replayStatus,
    );
  }

  const grantIssue = await page.evaluate(
    async ({ principal, agent }) => {
      const api = (globalThis as unknown as {
        SimpleWebAuthnBrowser: {
          startAuthentication(input: { optionsJSON: unknown }): Promise<unknown>;
        };
      }).SimpleWebAuthnBrowser;

      const optionsResponse = await fetch("/api/webauthn/grants/options", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ principalId: principal, agentId: agent }),
      });
      const optionsBody = (await optionsResponse.json()) as {
        challengeId: string;
        options: unknown;
        grant: unknown;
      };
      const assertion = await api.startAuthentication({
        optionsJSON: optionsBody.options,
      });
      const verifyResponse = await fetch("/api/webauthn/grants/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: assertion,
        }),
      });
      const verifyBody = await verifyResponse.json();
      const replayResponse = await fetch("/api/webauthn/grants/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: assertion,
        }),
      });
      return {
        optionsStatus: optionsResponse.status,
        verifyStatus: verifyResponse.status,
        verifyBody,
        grant: optionsBody.grant,
        replayStatus: replayResponse.status,
        replayBody: await replayResponse.json(),
      };
    },
    { principal: principalId, agent: agentId },
  );

  if (grantIssue.verifyStatus !== 201 || grantIssue.replayStatus !== 409) {
    throw new Error("WebAuthn grant issuance failed: " + JSON.stringify(grantIssue));
  }

  const insecure = { [oauth.allowInsecureRequests]: true };
  const discovery = await oauth.discoveryRequest(issuer, insecure);
  const authorizationServer = await oauth.processDiscoveryResponse(issuer, discovery);
  const client: oauth.Client = { client_id: clientId };
  const clientAuth = oauth.ClientSecretBasic(clientSecret);
  const keyPair = await oauth.generateKeyPair("ES256");
  const DPoP = oauth.DPoP(client, keyPair);

  let tokenResponse = await oauth.clientCredentialsGrantRequest(
    authorizationServer,
    client,
    clientAuth,
    new URLSearchParams(),
    { ...insecure, DPoP },
  );
  let token: oauth.TokenEndpointResponse;
  try {
    token = await oauth.processClientCredentialsResponse(
      authorizationServer,
      client,
      tokenResponse,
    );
  } catch (error) {
    if (!oauth.isDPoPNonceError(error)) throw error;
    tokenResponse = await oauth.clientCredentialsGrantRequest(
      authorizationServer,
      client,
      clientAuth,
      new URLSearchParams(),
      { ...insecure, DPoP },
    );
    token = await oauth.processClientCredentialsResponse(
      authorizationServer,
      client,
      tokenResponse,
    );
  }
  if (typeof token.access_token !== "string") throw new Error("access token missing");

  async function protectedPost(
    path: string,
    effectId: string,
    body: Record<string, unknown>,
  ): Promise<Response> {
    return await oauth.protectedResourceRequest(
      token.access_token,
      "POST",
      new URL(path, audience),
      new Headers({
        "content-type": "application/json",
        "x-ordivon-effect-id": effectId,
      }),
      JSON.stringify(body),
      { ...insecure, DPoP },
    );
  }

  const commentEffect = freshEffectId("webauthn-comment");
  const comment = await protectedPost(
    "/api/articles/article-42/comments",
    commentEffect,
    { content: "WebAuthn-delegated Agent effect" },
  );
  const commentBody = await expectJson(comment, 201, "R2 comment");

  const effectA = freshEffectId("publish-A");
  const effectB = freshEffectId("publish-B");
  const publishA1 = await protectedPost("/api/publish-probe", effectA, {
    probe: "A",
  });
  const publishA1Body = await expectJson(publishA1, 428, "publish A initial");
  const publishB1 = await protectedPost("/api/publish-probe", effectB, {
    probe: "B",
  });
  const publishB1Body = await expectJson(publishB1, 428, "publish B initial");

  const approval = await page.evaluate(
    async ({ principal, effectId }) => {
      const api = (globalThis as unknown as {
        SimpleWebAuthnBrowser: {
          startAuthentication(input: { optionsJSON: unknown }): Promise<unknown>;
        };
      }).SimpleWebAuthnBrowser;
      const optionsResponse = await fetch("/api/webauthn/approvals/options", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ principalId: principal, effectId }),
      });
      const optionsBody = (await optionsResponse.json()) as {
        challengeId: string;
        options: unknown;
      };
      const assertion = await api.startAuthentication({
        optionsJSON: optionsBody.options,
      });
      const verifyResponse = await fetch("/api/webauthn/approvals/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: assertion,
        }),
      });
      const verifyBody = await verifyResponse.json();
      const replayResponse = await fetch("/api/webauthn/approvals/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: assertion,
        }),
      });
      return {
        optionsStatus: optionsResponse.status,
        verifyStatus: verifyResponse.status,
        verifyBody,
        replayStatus: replayResponse.status,
        replayBody: await replayResponse.json(),
      };
    },
    { principal: principalId, effectId: effectA },
  );

  if (approval.verifyStatus !== 201 || approval.replayStatus !== 409) {
    throw new Error("WebAuthn effect approval failed: " + JSON.stringify(approval));
  }

  const publishB2 = await protectedPost("/api/publish-probe", effectB, {
    probe: "B",
  });
  const publishB2Body = await expectJson(
    publishB2,
    428,
    "publish B after approving A",
  );
  const publishA2 = await protectedPost("/api/publish-probe", effectA, {
    probe: "A",
  });
  const publishA2Body = await expectJson(
    publishA2,
    200,
    "publish A after WebAuthn approval",
  );
  const publishA3 = await protectedPost("/api/publish-probe", effectA, {
    probe: "A",
  });
  const publishA3Body = await expectJson(
    publishA3,
    428,
    "publish A after approval consumption",
  );

  const issuedGrant = grantIssue.grant as { grantId?: unknown };
  if (typeof issuedGrant.grantId !== "string") {
    throw new Error("issued grant id is missing");
  }
  const revocation = await page.evaluate(
    async ({ principal, grantId }) => {
      const api = (globalThis as unknown as {
        SimpleWebAuthnBrowser: {
          startAuthentication(input: { optionsJSON: unknown }): Promise<unknown>;
        };
      }).SimpleWebAuthnBrowser;
      const optionsResponse = await fetch("/api/webauthn/grants/revoke/options", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ principalId: principal, grantId }),
      });
      const optionsBody = (await optionsResponse.json()) as {
        challengeId: string;
        options: unknown;
      };
      const assertion = await api.startAuthentication({
        optionsJSON: optionsBody.options,
      });
      const verifyResponse = await fetch("/api/webauthn/grants/revoke/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: assertion,
        }),
      });
      const verifyBody = await verifyResponse.json();
      const replayResponse = await fetch("/api/webauthn/grants/revoke/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          challengeId: optionsBody.challengeId,
          response: assertion,
        }),
      });
      return {
        optionsStatus: optionsResponse.status,
        verifyStatus: verifyResponse.status,
        verifyBody,
        replayStatus: replayResponse.status,
        replayBody: await replayResponse.json(),
      };
    },
    { principal: principalId, grantId: issuedGrant.grantId },
  );

  if (revocation.verifyStatus !== 200 || revocation.replayStatus !== 409) {
    throw new Error("WebAuthn grant revocation failed: " + JSON.stringify(revocation));
  }

  const postRevokeNew = await protectedPost(
    "/api/articles/article-42/comments",
    freshEffectId("post-revoke-new"),
    { content: "must be denied after grant revocation" },
  );
  const postRevokeNewBody = await expectJson(
    postRevokeNew,
    403,
    "new effect after grant revocation",
  );
  const postRevokeReplay = await protectedPost(
    "/api/articles/article-42/comments",
    commentEffect,
    { content: "WebAuthn-delegated Agent effect" },
  );
  const postRevokeReplayBody = await expectJson(
    postRevokeReplay,
    200,
    "historical effect replay after grant revocation",
  );

  console.log(
    JSON.stringify(
      {
        virtualAuthenticator: {
          protocol: "ctap2",
          transport: "internal",
          userVerification: true,
          authenticatorId: virtual.authenticatorId,
          productionHumanPresenceClaim: false,
        },
        enrollment,
        grantIssue,
        comment: { status: comment.status, body: commentBody },
        publishAInitial: { status: publishA1.status, body: publishA1Body },
        publishBInitial: { status: publishB1.status, body: publishB1Body },
        approval,
        publishBAfterApprovingA: { status: publishB2.status, body: publishB2Body },
        publishAApproved: { status: publishA2.status, body: publishA2Body },
        publishAAfterConsumption: { status: publishA3.status, body: publishA3Body },
        revocation,
        postRevokeNewEffect: {
          status: postRevokeNew.status,
          body: postRevokeNewBody,
        },
        postRevokeHistoricalReplay: {
          status: postRevokeReplay.status,
          body: postRevokeReplayBody,
        },
      },
      null,
      2,
    ),
  );
} finally {
  await cdp.send("WebAuthn.removeVirtualAuthenticator", {
    authenticatorId: virtual.authenticatorId,
  });
  await context.close();
  await browser.close();
}
