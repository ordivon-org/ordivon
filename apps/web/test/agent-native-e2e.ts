import assert from "node:assert/strict";
import { createHash, randomBytes } from "node:crypto";
import { fileURLToPath } from "node:url";

import * as oauth from "oauth4webapi";
import { chromium } from "playwright";

import { createWebApp } from "../src/app.ts";
import type { WebConfig } from "../src/config.ts";
import { SecurityAgentRequestVerifier } from "../src/security-agent-verifier.ts";
import { WebStore } from "../src/store.ts";

function env(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (value === undefined || value === "") throw new Error(name + " is required");
  return value;
}

function freshEffectId(label: string): string {
  return (
    "sha256:" +
    createHash("sha256").update(label).update(randomBytes(32)).digest("hex")
  );
}

function jwtPart(value: string): Record<string, unknown> {
  return JSON.parse(Buffer.from(value, "base64url").toString("utf8")) as Record<
    string,
    unknown
  >;
}

const issuerText = env(
  "ORDIVON_WEB_AGENT_ISSUER",
  "http://127.0.0.1:18080/realms/agent-admission-lab",
);
const chromiumExecutable = env("ORDIVON_WEB_CHROMIUM_EXECUTABLE");
const clientId = "agent-research-17";
const clientSecret = "lab-only-agent-secret";

const config: WebConfig = {
  host: "127.0.0.1",
  port: 8791,
  origin: "http://localhost:8791",
  rpID: "localhost",
  rpName: "Ordivon Agent-Native E2E",
  databasePath: ":memory:",
  bootstrapEnrollmentToken: "agent-native-bootstrap",
  agentIssuer: issuerText,
  agentAllowInsecureIssuer: true,
  sessionIdleSeconds: 300,
  sessionAbsoluteSeconds: 3600,
};

const store = new WebStore(":memory:");
const agentVerifier = new SecurityAgentRequestVerifier(config, store);
const app = await createWebApp(config, { store, agentVerifier });
await app.listen({ host: config.host, port: config.port });

const browser = await chromium.launch({
  headless: true,
  executablePath: chromiumExecutable,
  args: ["--host-resolver-rules=MAP localhost 127.0.0.1"],
});
const context = await browser.newContext();
const bundlePath = fileURLToPath(
  new URL(
    "../node_modules/@simplewebauthn/browser/dist/bundle/index.umd.min.js",
    import.meta.url,
  ),
);
await context.addInitScript({ path: bundlePath });
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
  await page.goto(config.origin + "/", { waitUntil: "domcontentloaded" });

  const principal = await page.evaluate(
    async ({ bootstrapToken }) => {
      const api = (globalThis as unknown as {
        SimpleWebAuthnBrowser: {
          startRegistration(input: { optionsJSON: unknown }): Promise<unknown>;
          startAuthentication(input: { optionsJSON: unknown }): Promise<unknown>;
        };
      }).SimpleWebAuthnBrowser;

      const enrollOptions = await fetch("/api/auth/enroll/options", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-bootstrap-enrollment-token": bootstrapToken,
        },
        body: JSON.stringify({
          principalId: "principal:agent-native-e2e",
          userName: "agent-native-e2e",
          displayName: "Agent Native E2E",
        }),
      });
      const enroll = (await enrollOptions.json()) as {
        challengeId: string;
        options: unknown;
      };
      const registration = await api.startRegistration({
        optionsJSON: enroll.options,
      });
      const enrollVerify = await fetch("/api/auth/enroll/verify", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-bootstrap-enrollment-token": bootstrapToken,
        },
        body: JSON.stringify({
          challengeId: enroll.challengeId,
          response: registration,
        }),
      });

      const loginOptions = await fetch("/api/auth/login/options", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ userName: "agent-native-e2e" }),
      });
      const login = (await loginOptions.json()) as {
        challengeId: string;
        options: unknown;
      };
      const assertion = await api.startAuthentication({
        optionsJSON: login.options,
      });
      const loginVerify = await fetch("/api/auth/login/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          challengeId: login.challengeId,
          response: assertion,
        }),
      });
      return {
        enrollOptions: enrollOptions.status,
        enrollVerify: enrollVerify.status,
        loginOptions: loginOptions.status,
        loginVerify: loginVerify.status,
      };
    },
    { bootstrapToken: config.bootstrapEnrollmentToken! },
  );
  assert.deepEqual(principal, {
    enrollOptions: 200,
    enrollVerify: 200,
    loginOptions: 200,
    loginVerify: 200,
  });

  const grantFlow = await page.evaluate(async () => {
    const api = (globalThis as unknown as {
      SimpleWebAuthnBrowser: {
        startAuthentication(input: { optionsJSON: unknown }): Promise<unknown>;
      };
    }).SimpleWebAuthnBrowser;
    const csrf = await fetch("/api/session/csrf");
    const csrfToken = ((await csrf.json()) as { token: string }).token;
    const optionsResponse = await fetch("/api/security/agents/grants/options", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-csrf-token": csrfToken,
      },
      body: JSON.stringify({ agentId: "oauth-client:agent-research-17" }),
    });
    const options = (await optionsResponse.json()) as {
      challengeId: string;
      options: unknown;
      grant: { grantId: string };
    };
    const assertion = await api.startAuthentication({
      optionsJSON: options.options,
    });
    const verifyResponse = await fetch("/api/security/agents/grants/verify", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-csrf-token": csrfToken,
      },
      body: JSON.stringify({
        challengeId: options.challengeId,
        response: assertion,
      }),
    });
    return {
      optionsStatus: optionsResponse.status,
      verifyStatus: verifyResponse.status,
      verifyBody: await verifyResponse.json(),
    };
  });
  assert.equal(grantFlow.optionsStatus, 200);
  assert.equal(grantFlow.verifyStatus, 201);

  const issuer = new URL(issuerText);
  const insecure = { [oauth.allowInsecureRequests]: true };
  const discovery = await oauth.discoveryRequest(issuer, insecure);
  const authorizationServer = await oauth.processDiscoveryResponse(issuer, discovery);
  const client: oauth.Client = { client_id: clientId };
  const clientAuth = oauth.ClientSecretBasic(clientSecret);
  const keyPair = await oauth.generateKeyPair("ES256");
  const DPoP = oauth.DPoP(client, keyPair);

  async function tokenRequest(): Promise<oauth.TokenEndpointResponse> {
    let response = await oauth.clientCredentialsGrantRequest(
      authorizationServer,
      client,
      clientAuth,
      new URLSearchParams(),
      { ...insecure, DPoP },
    );
    try {
      return await oauth.processClientCredentialsResponse(
        authorizationServer,
        client,
        response,
      );
    } catch (error) {
      if (!oauth.isDPoPNonceError(error)) throw error;
      response = await oauth.clientCredentialsGrantRequest(
        authorizationServer,
        client,
        clientAuth,
        new URLSearchParams(),
        { ...insecure, DPoP },
      );
      return await oauth.processClientCredentialsResponse(
        authorizationServer,
        client,
        response,
      );
    }
  }

  const token = await tokenRequest();
  if (typeof token.access_token !== "string") throw new Error("access token missing");
  assert.equal(String(token.token_type).toLowerCase(), "dpop");
  const tokenParts = token.access_token.split(".");
  assert.equal(tokenParts.length, 3);
  const tokenPayload = jwtPart(tokenParts[1]!);
  const confirmation = tokenPayload.cnf as Record<string, unknown>;
  assert.equal(confirmation["kc-jkt-type"], "DPoP");

  const createUrl = new URL("/api/agent/canary/notes", config.origin);
  const createEffectId = freshEffectId("agent-native-create");
  const content = "real DPoP delegated draft";

  async function agentPost(
    url: URL,
    id: string,
    body: unknown,
    dpop = DPoP,
    captureHeaders?: (headers: Headers) => void,
  ): Promise<Response> {
    const options: oauth.ProtectedResourceRequestOptions = {
      ...insecure,
      DPoP: dpop,
    };
    if (captureHeaders !== undefined) {
      options[oauth.customFetch] = async (target, init) => {
        captureHeaders(new Headers(init.headers));
        return await fetch(target, {
          method: init.method,
          headers: init.headers,
          body: init.body === undefined ? null : (init.body as BodyInit),
          signal: init.signal ?? null,
        });
      };
    }
    return await oauth.protectedResourceRequest(
      token.access_token,
      "POST",
      url,
      new Headers({
        "content-type": "application/json",
        "x-ordivon-effect-id": id,
      }),
      JSON.stringify(body),
      options,
    );
  }

  const noProof = await fetch(createUrl, {
    method: "POST",
    headers: {
      authorization: "DPoP " + token.access_token,
      "content-type": "application/json",
      "x-ordivon-effect-id": freshEffectId("no-proof"),
    },
    body: JSON.stringify({ content: "must fail without proof" }),
  });
  assert.equal(noProof.status, 401);

  const wrongDPoP = oauth.DPoP(client, await oauth.generateKeyPair("ES256"));
  const wrongKey = await agentPost(
    createUrl,
    freshEffectId("wrong-key"),
    { content: "must fail wrong key" },
    wrongDPoP,
  );
  assert.equal(wrongKey.status, 401);

  let captured: Headers | undefined;
  const firstCreate = await agentPost(
    createUrl,
    createEffectId,
    { content },
    DPoP,
    (headers) => {
      captured = headers;
    },
  );
  assert.equal(firstCreate.status, 201);
  const firstCreateBody = (await firstCreate.json()) as {
    replayed: boolean;
    receipt: {
      effectId: string;
      result: { note: { noteId: string; state: string } };
    };
  };
  assert.equal(firstCreateBody.replayed, false);
  assert.equal(firstCreateBody.receipt.result.note.state, "DRAFT");
  const noteId = firstCreateBody.receipt.result.note.noteId;

  if (captured === undefined) throw new Error("failed to capture DPoP proof");
  const proofReplay = await fetch(createUrl, {
    method: "POST",
    headers: captured,
    body: JSON.stringify({ content }),
  });
  assert.equal(proofReplay.status, 401);

  const exactReplay = await agentPost(createUrl, createEffectId, { content });
  assert.equal(exactReplay.status, 200);
  const exactReplayBody = await exactReplay.json();
  assert.equal(exactReplayBody.replayed, true);
  assert.equal(exactReplayBody.receipt.effectId, firstCreateBody.receipt.effectId);

  const conflict = await agentPost(createUrl, createEffectId, {
    content: content + " changed",
  });
  assert.equal(conflict.status, 409);

  const publishEffectId = freshEffectId("agent-native-publish");
  const publishUrl = new URL(
    "/api/agent/canary/notes/" + noteId + "/publish",
    config.origin,
  );
  const publishStepUp = await agentPost(publishUrl, publishEffectId, {});
  assert.equal(publishStepUp.status, 428);
  const publishStepUpBody = (await publishStepUp.json()) as {
    effectId: string;
    effectDigest: string;
  };
  assert.equal(publishStepUpBody.effectId, publishEffectId);

  const approvalFlow = await page.evaluate(
    async ({ effectId }) => {
      const api = (globalThis as unknown as {
        SimpleWebAuthnBrowser: {
          startAuthentication(input: { optionsJSON: unknown }): Promise<unknown>;
        };
      }).SimpleWebAuthnBrowser;
      const csrf = await fetch("/api/session/csrf");
      const csrfToken = ((await csrf.json()) as { token: string }).token;
      const optionsResponse = await fetch("/api/security/agent-approvals/options", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-csrf-token": csrfToken,
        },
        body: JSON.stringify({ effectId }),
      });
      const options = (await optionsResponse.json()) as {
        challengeId: string;
        options: unknown;
      };
      const assertion = await api.startAuthentication({
        optionsJSON: options.options,
      });
      const verifyResponse = await fetch("/api/security/agent-approvals/verify", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-csrf-token": csrfToken,
        },
        body: JSON.stringify({
          challengeId: options.challengeId,
          response: assertion,
        }),
      });
      return {
        optionsStatus: optionsResponse.status,
        verifyStatus: verifyResponse.status,
        verifyBody: await verifyResponse.json(),
      };
    },
    { effectId: publishEffectId },
  );
  assert.equal(approvalFlow.optionsStatus, 200);
  assert.equal(approvalFlow.verifyStatus, 201);

  const publishApproved = await agentPost(publishUrl, publishEffectId, {});
  assert.equal(publishApproved.status, 200);
  const publishApprovedBody = await publishApproved.json();
  assert.equal(publishApprovedBody.replayed, false);
  assert.equal(publishApprovedBody.receipt.result.note.state, "PUBLISHED");

  const grantId = (grantFlow.verifyBody as { grant: { grantId: string } }).grant
    .grantId;
  const revokeFlow = await page.evaluate(
    async ({ grantId }) => {
      const api = (globalThis as unknown as {
        SimpleWebAuthnBrowser: {
          startAuthentication(input: { optionsJSON: unknown }): Promise<unknown>;
        };
      }).SimpleWebAuthnBrowser;
      const csrf = await fetch("/api/session/csrf");
      const csrfToken = ((await csrf.json()) as { token: string }).token;
      const optionsResponse = await fetch("/api/security/agents/grants/revoke/options", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-csrf-token": csrfToken,
        },
        body: JSON.stringify({ grantId }),
      });
      const options = (await optionsResponse.json()) as {
        challengeId: string;
        options: unknown;
      };
      const assertion = await api.startAuthentication({
        optionsJSON: options.options,
      });
      const verifyResponse = await fetch(
        "/api/security/agents/grants/revoke/verify",
        {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "x-csrf-token": csrfToken,
          },
          body: JSON.stringify({
            challengeId: options.challengeId,
            response: assertion,
          }),
        },
      );
      return {
        optionsStatus: optionsResponse.status,
        verifyStatus: verifyResponse.status,
        verifyBody: await verifyResponse.json(),
      };
    },
    { grantId },
  );
  assert.equal(revokeFlow.optionsStatus, 200);
  assert.equal(revokeFlow.verifyStatus, 200);
  assert.equal(revokeFlow.verifyBody.grant.active, false);

  const afterRevoke = await agentPost(
    createUrl,
    freshEffectId("after-revoke"),
    { content: "must be denied" },
  );
  assert.equal(afterRevoke.status, 403);

  const historicalReplay = await agentPost(createUrl, createEffectId, { content });
  assert.equal(historicalReplay.status, 200);
  const historicalReplayBody = await historicalReplay.json();
  assert.equal(historicalReplayBody.replayed, true);

  const approvalRow = store.db
    .prepare("SELECT consumed_at FROM effect_approvals WHERE effect_id = ?")
    .get(publishEffectId) as { consumed_at: number | null };
  assert.notEqual(approvalRow.consumed_at, null);

  console.log(
    JSON.stringify(
      {
        principal,
        token: {
          tokenType: token.token_type,
          confirmationKeys: Object.keys(confirmation).sort(),
          confirmationType: confirmation["kc-jkt-type"],
        },
        grant: grantFlow.verifyBody,
        matrix: {
          noProof: noProof.status,
          wrongKey: wrongKey.status,
          firstCreate: firstCreate.status,
          proofReplay: proofReplay.status,
          exactReplay: exactReplay.status,
          conflict: conflict.status,
          publishStepUp: publishStepUp.status,
          approval: approvalFlow.verifyStatus,
          publishApproved: publishApproved.status,
          revoke: revokeFlow.verifyStatus,
          newEffectAfterRevoke: afterRevoke.status,
          historicalReplayAfterRevoke: historicalReplay.status,
        },
        createReceipt: firstCreateBody.receipt,
        publishReceipt: publishApprovedBody.receipt,
        approvalConsumed: approvalRow.consumed_at !== null,
        productionHumanPresenceClaim: false,
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
  await app.close();
  store.close();
}
