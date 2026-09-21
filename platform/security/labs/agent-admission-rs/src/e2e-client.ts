import { createHash, randomBytes } from "node:crypto";

import * as oauth from "oauth4webapi";

function env(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (value === undefined || value === "") throw new Error(`${name} is required`);
  return value;
}

function freshEffectId(label: string): string {
  return `sha256:${createHash("sha256").update(label).update(randomBytes(32)).digest("hex")}`;
}

const issuer = new URL(
  env(
    "AGENT_ADMISSION_ISSUER",
    "http://127.0.0.1:18080/realms/agent-admission-lab",
  ),
);
const origin = env("AGENT_ADMISSION_AUDIENCE", "http://127.0.0.1:8788");
const resource = new URL(
  env(
    "AGENT_ADMISSION_RESOURCE",
    `${origin}/api/articles/article-42/comments`,
  ),
);
const publishProbe = new URL(`${origin}/api/publish-probe`);
const clientId = env("AGENT_ADMISSION_CLIENT_ID", "agent-research-17");
const clientSecret = env(
  "AGENT_ADMISSION_CLIENT_SECRET",
  "lab-only-agent-secret",
);
const content = env(
  "AGENT_ADMISSION_COMMENT",
  "Agent Admission DPoP E2E",
);
const effectId =
  process.env.AGENT_ADMISSION_EFFECT_ID ?? freshEffectId("comment");

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

const tokenParts = token.access_token.split(".");
if (tokenParts.length !== 3) throw new Error("access token is not a JWT");
const decodeJwtPart = (value: string): Record<string, unknown> =>
  JSON.parse(Buffer.from(value, "base64url").toString("utf8")) as Record<string, unknown>;
const tokenHeader = decodeJwtPart(tokenParts[0]!);
const tokenPayload = decodeJwtPart(tokenParts[1]!);
const confirmation = tokenPayload.cnf;
const confirmationKeys =
  confirmation !== null && typeof confirmation === "object" && !Array.isArray(confirmation)
    ? Object.keys(confirmation).sort()
    : null;
const confirmationType =
  confirmation !== null && typeof confirmation === "object" && !Array.isArray(confirmation)
    ? (confirmation as Record<string, unknown>)["kc-jkt-type"]
    : null;

async function commentRequest(
  bodyContent: string,
  id = effectId,
  dpop = DPoP,
  captureHeaders?: (headers: Headers) => void,
): Promise<Response> {
  const options: oauth.ProtectedResourceRequestOptions = {
    ...insecure,
    DPoP: dpop,
  };
  if (captureHeaders !== undefined) {
    options[oauth.customFetch] = async (url, init) => {
      captureHeaders(new Headers(init.headers));
      const requestInit: RequestInit = {
        method: init.method,
        headers: init.headers,
        body: init.body === undefined ? null : (init.body as BodyInit),
        signal: init.signal ?? null,
      };
      return await fetch(url, requestInit);
    };
  }
  return await oauth.protectedResourceRequest(
    token.access_token,
    "POST",
    resource,
    new Headers({
      "content-type": "application/json",
      "x-ordivon-effect-id": id,
    }),
    JSON.stringify({ content: bodyContent }),
    options,
  );
}

const noProof = await fetch(resource, {
  method: "POST",
  headers: {
    authorization: `DPoP ${token.access_token}`,
    "content-type": "application/json",
    "x-ordivon-effect-id": freshEffectId("no-proof"),
  },
  body: JSON.stringify({ content: "must not execute without DPoP proof" }),
});

const wrongKeyPair = await oauth.generateKeyPair("ES256");
const wrongDPoP = oauth.DPoP(client, wrongKeyPair);
const wrongKey = await commentRequest(
  "must not execute with wrong DPoP key",
  freshEffectId("wrong-key"),
  wrongDPoP,
);

let capturedFirstHeaders: Headers | undefined;
const first = await commentRequest(content, effectId, DPoP, (headers) => {
  capturedFirstHeaders = headers;
});
const firstBody = await first.json();
if (capturedFirstHeaders === undefined) {
  throw new Error("failed to capture the first DPoP proof request");
}
const proofReplay = await fetch(resource, {
  method: "POST",
  headers: capturedFirstHeaders,
  body: JSON.stringify({ content }),
});
const proofReplayBody = await proofReplay.json();
const replay = await commentRequest(content);
const replayBody = await replay.json();
const conflict = await commentRequest(`${content} changed`);
const conflictBody = await conflict.json();

const publish = await oauth.protectedResourceRequest(
  token.access_token,
  "POST",
  publishProbe,
  new Headers({
    "content-type": "application/json",
    "x-ordivon-effect-id": freshEffectId("publish"),
  }),
  JSON.stringify({ probe: true }),
  { ...insecure, DPoP },
);
const publishBody = await publish.json();

const statusMatrix: ReadonlyArray<readonly [string, Response, number]> = [
  ["noProof", noProof, 401],
  ["wrongKey", wrongKey, 401],
  ["first", first, 201],
  ["proofReplay", proofReplay, 401],
  ["replay", replay, 200],
  ["conflict", conflict, 409],
  ["publish", publish, 428],
];
for (const [name, response, expected] of statusMatrix) {
  if (response.status !== expected) {
    throw new Error(`${name}: expected HTTP ${expected}, got ${response.status}`);
  }
}
if (String(token.token_type).toLowerCase() !== "dpop") {
  throw new Error(`expected DPoP token_type, got ${String(token.token_type)}`);
}
if (
  confirmationKeys === null ||
  JSON.stringify(confirmationKeys) !== JSON.stringify(["jkt", "kc-jkt-type"])
) {
  throw new Error(
    `unexpected Keycloak confirmation members: ${JSON.stringify(confirmationKeys)}`,
  );
}
if (confirmationType !== "DPoP") {
  throw new Error(
    `expected Keycloak DPoP confirmation discriminator, got ${String(confirmationType)}`,
  );
}
const firstResult = firstBody as {
  replayed?: unknown;
  receipt?: { commentId?: unknown };
};
const replayResult = replayBody as {
  replayed?: unknown;
  receipt?: { commentId?: unknown };
};
const proofReplayResult = proofReplayBody as { error?: unknown };
if (
  firstResult.replayed !== false ||
  replayResult.replayed !== true ||
  typeof firstResult.receipt?.commentId !== "string" ||
  firstResult.receipt.commentId !== replayResult.receipt?.commentId
) {
  throw new Error("effect replay did not return the exact committed receipt");
}
if (proofReplayResult.error !== "dpop_proof_replayed") {
  throw new Error("DPoP proof replay was not rejected by the replay ledger");
}

console.log(
  JSON.stringify(
    {
      tokenType: token.token_type,
      tokenHeader: { alg: tokenHeader.alg, typ: tokenHeader.typ },
      confirmationKeys,
      confirmationType,
      effectId,
      noProof: { status: noProof.status, body: await noProof.json() },
      wrongKey: { status: wrongKey.status, body: await wrongKey.json() },
      first: { status: first.status, body: firstBody },
      proofReplay: { status: proofReplay.status, body: proofReplayBody },
      replay: { status: replay.status, body: replayBody },
      conflict: { status: conflict.status, body: conflictBody },
      publish: { status: publish.status, body: publishBody },
    },
    null,
    2,
  ),
);
