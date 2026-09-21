import assert from "node:assert/strict";
import { createHash, randomUUID } from "node:crypto";
import { test } from "node:test";

import * as oauth from "oauth4webapi";

const encoder = new TextEncoder();
const issuer = new URL("https://issuer.example.test/");
const jwksUri = new URL("https://issuer.example.test/jwks");
const audience = "https://resource.example.test";
const resource = new URL("/agent/effect", audience);
const asKeyId = "as-test-key";

function encodedJson(value: unknown): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function sha256Base64Url(value: string): string {
  return createHash("sha256").update(value).digest("base64url");
}

function ecThumbprint(jwk: JsonWebKey): string {
  if (
    jwk.kty !== "EC" ||
    typeof jwk.crv !== "string" ||
    typeof jwk.x !== "string" ||
    typeof jwk.y !== "string"
  ) {
    throw new Error("expected EC public JWK");
  }
  return sha256Base64Url(
    JSON.stringify({
      crv: jwk.crv,
      kty: jwk.kty,
      x: jwk.x,
      y: jwk.y,
    }),
  );
}

async function signAccessToken(
  privateKey: CryptoKey,
  cnf: Record<string, unknown>,
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const header = encodedJson({ alg: "RS256", typ: "at+jwt", kid: asKeyId });
  const payload = encodedJson({
    iss: issuer.href,
    exp: now + 300,
    aud: audience,
    sub: "service-account-agent-test",
    iat: now,
    jti: randomUUID(),
    client_id: "agent-test",
    cnf,
  });
  const signingInput = header + "." + payload;
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    privateKey,
    encoder.encode(signingInput),
  );
  return signingInput + "." + Buffer.from(signature).toString("base64url");
}

interface Fixture {
  readonly authorizationServer: oauth.AuthorizationServer;
  readonly asPrivateKey: CryptoKey;
  readonly asPublicJwk: JsonWebKey;
  readonly dpop: ReturnType<typeof oauth.DPoP>;
  readonly dpopThumbprint: string;
}

async function fixture(): Promise<Fixture> {
  const asKeys = (await crypto.subtle.generateKey(
    {
      name: "RSASSA-PKCS1-v1_5",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true,
    ["sign", "verify"],
  )) as CryptoKeyPair;
  const asPublicJwk = await crypto.subtle.exportKey("jwk", asKeys.publicKey);
  Object.assign(asPublicJwk, {
    kid: asKeyId,
    alg: "RS256",
    use: "sig",
  });

  const dpopKeys = await oauth.generateKeyPair("ES256");
  const dpopPublicJwk = await crypto.subtle.exportKey("jwk", dpopKeys.publicKey);
  const client: oauth.Client = { client_id: "agent-test" };

  return {
    authorizationServer: {
      issuer: issuer.href,
      jwks_uri: jwksUri.href,
    },
    asPrivateKey: asKeys.privateKey,
    asPublicJwk,
    dpop: oauth.DPoP(client, dpopKeys),
    dpopThumbprint: ecThumbprint(dpopPublicJwk),
  };
}

async function protectedRequest(
  accessToken: string,
  dpop: ReturnType<typeof oauth.DPoP>,
): Promise<Request> {
  let captured: Headers | undefined;
  await oauth.protectedResourceRequest(
    accessToken,
    "POST",
    resource,
    new Headers({ "content-type": "application/json" }),
    JSON.stringify({ effect: true }),
    {
      DPoP: dpop,
      [oauth.customFetch]: async (_url, init) => {
        captured = new Headers(init.headers);
        return new Response(null, { status: 204 });
      },
    },
  );
  if (captured === undefined) {
    throw new Error("DPoP request headers were not captured");
  }
  return new Request(resource, {
    method: "POST",
    headers: captured,
  });
}

async function validate(
  f: Fixture,
  cnf: Record<string, unknown>,
): Promise<oauth.JWTAccessTokenClaims> {
  const token = await signAccessToken(f.asPrivateKey, cnf);
  const request = await protectedRequest(token, f.dpop);
  return await oauth.validateJwtAccessToken(
    f.authorizationServer,
    request,
    audience,
    {
      requireDPoP: true,
      signingAlgorithms: ["RS256", "ES256"],
      [oauth.customFetch]: async (url) => {
        assert.equal(new URL(url).href, jwksUri.href);
        return new Response(JSON.stringify({ keys: [f.asPublicJwk] }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      },
    },
  );
}

test("standard cnf.jkt DPoP token validates", async () => {
  const f = await fixture();
  const claims = await validate(f, { jkt: f.dpopThumbprint });
  assert.equal(claims.client_id, "agent-test");
});

test("Keycloak private cnf discriminator is ignored after validating jkt", async () => {
  const f = await fixture();
  const claims = await validate(f, {
    jkt: f.dpopThumbprint,
    "kc-jkt-type": "DPoP",
  });
  assert.equal(claims.cnf?.jkt, f.dpopThumbprint);
  assert.equal(
    (claims.cnf as Record<string, unknown>)["kc-jkt-type"],
    "DPoP",
  );
});

test("Keycloak private discriminator with a non-DPoP value fails closed", async () => {
  const f = await fixture();
  await assert.rejects(() =>
    validate(f, {
      jkt: f.dpopThumbprint,
      "kc-jkt-type": "Client-Attestation",
    }),
  );
});

test("private discriminator without cnf.jkt does not establish DPoP binding", async () => {
  const f = await fixture();
  await assert.rejects(() =>
    validate(f, {
      "kc-jkt-type": "DPoP",
    }),
  );
});

test("wrong cnf.jkt still fails oauth4webapi DPoP key binding", async () => {
  const f = await fixture();
  await assert.rejects(() =>
    validate(f, {
      jkt: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
      "kc-jkt-type": "DPoP",
    }),
  );
});
