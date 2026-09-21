import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";

import { createWebApp } from "../src/app.ts";
import type { WebConfig } from "../src/config.ts";
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

function setCookieValues(value: string | string[] | undefined): string[] {
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

function cookiePair(setCookie: string, name: string): string {
  const match = new RegExp("(?:^|;\\\\s*)(" + name + "=[^;]+)").exec(setCookie);
  if (match?.[1] === undefined) {
    throw new Error("cookie not found: " + name + " in " + setCookie);
  }
  return match[1];
}

function sessionCookie(token: string): string {
  return "__Host-session=" + token;
}

async function fixture() {
  let currentTime = 1_800_000_000;
  const now = () => currentTime;
  const store = new WebStore(":memory:");
  store.ensurePrincipal("principal:test", "test-user", "Test User", now());
  const created = store.createSession(
    "principal:test",
    now(),
    config.sessionIdleSeconds,
    config.sessionAbsoluteSeconds,
    "test-agent",
  );
  const app = await createWebApp(config, { store, now });
  return {
    app,
    store,
    token: created.token,
    sessionId: created.session.sessionId,
    now,
    advance(seconds: number) {
      currentTime += seconds;
    },
  };
}

async function csrf(
  app: Awaited<ReturnType<typeof createWebApp>>,
  token: string,
): Promise<{ token: string; cookie: string }> {
  const response = await app.inject({
    method: "GET",
    url: "/api/session/csrf",
    headers: { cookie: sessionCookie(token) },
  });
  assert.equal(response.statusCode, 200);
  const body = response.json() as { token: string };
  const csrfSetCookie = setCookieValues(response.headers["set-cookie"]).find(
    (value) => value.startsWith("__Host-csrf-secret="),
  );
  assert.ok(csrfSetCookie);
  return {
    token: body.token,
    cookie: cookiePair(csrfSetCookie, "__Host-csrf-secret"),
  };
}

test("security headers are present on ordinary responses", async () => {
  const f = await fixture();
  const response = await f.app.inject({ method: "GET", url: "/health" });
  assert.equal(response.statusCode, 200);
  assert.match(String(response.headers["content-security-policy"]), /default-src 'self'/);
  assert.match(String(response.headers["strict-transport-security"]), /max-age=63072000/);
  assert.equal(response.headers["x-content-type-options"], "nosniff");
  assert.equal(response.headers["referrer-policy"], "no-referrer");
  assert.match(String(response.headers["permissions-policy"]), /camera=\(\)/);
  await f.app.close();
  f.store.close();
});

test("session token is opaque in the cookie and only its hash is stored", async () => {
  const f = await fixture();
  const row = f.store.db
    .prepare("SELECT token_hash FROM sessions WHERE session_id = ?")
    .get(f.sessionId) as { token_hash: string };
  assert.notEqual(row.token_hash, f.token);
  assert.equal(
    row.token_hash,
    createHash("sha256").update(f.token).digest("hex"),
  );

  const response = await f.app.inject({
    method: "GET",
    url: "/api/me",
    headers: { cookie: sessionCookie(f.token) },
  });
  assert.equal(response.statusCode, 200);
  const body = response.json() as { principal: { principalId: string } };
  assert.equal(body.principal.principalId, "principal:test");
  await f.app.close();
  f.store.close();
});

test("unsafe browser mutation requires same origin and CSRF", async () => {
  const f = await fixture();
  const antiCsrf = await csrf(f.app, f.token);
  const cookies = sessionCookie(f.token) + "; " + antiCsrf.cookie;

  const noOrigin = await f.app.inject({
    method: "POST",
    url: "/api/canary/notes",
    headers: {
      cookie: cookies,
      "x-csrf-token": antiCsrf.token,
    },
    payload: { content: "no origin" },
  });
  assert.equal(noOrigin.statusCode, 403);
  assert.equal(noOrigin.json().title, "Cross-site request rejected");

  const noCsrf = await f.app.inject({
    method: "POST",
    url: "/api/canary/notes",
    headers: {
      cookie: cookies,
      origin: config.origin,
    },
    payload: { content: "no csrf" },
  });
  assert.equal(noCsrf.statusCode, 403);

  const crossSite = await f.app.inject({
    method: "POST",
    url: "/api/canary/notes",
    headers: {
      cookie: cookies,
      origin: config.origin,
      "sec-fetch-site": "cross-site",
      "x-csrf-token": antiCsrf.token,
    },
    payload: { content: "cross site" },
  });
  assert.equal(crossSite.statusCode, 403);

  const allowed = await f.app.inject({
    method: "POST",
    url: "/api/canary/notes",
    headers: {
      cookie: cookies,
      origin: config.origin,
      "sec-fetch-site": "same-origin",
      "x-csrf-token": antiCsrf.token,
    },
    payload: { content: "allowed" },
  });
  assert.equal(allowed.statusCode, 201);
  assert.equal(allowed.json().note.state, "DRAFT");

  const listed = await f.app.inject({
    method: "GET",
    url: "/api/canary/notes",
    headers: { cookie: sessionCookie(f.token) },
  });
  assert.equal(listed.statusCode, 200);
  assert.equal(listed.json().notes.length, 1);
  await f.app.close();
  f.store.close();
});

test("sessions obey idle expiry and return RFC 9457-style problem details", async () => {
  const f = await fixture();
  f.advance(config.sessionIdleSeconds + 1);
  const response = await f.app.inject({
    method: "GET",
    url: "/api/me",
    headers: { cookie: sessionCookie(f.token) },
  });
  assert.equal(response.statusCode, 401);
  assert.match(String(response.headers["content-type"]), /application\/problem\+json/);
  const body = response.json();
  assert.equal(body.status, 401);
  assert.equal(body.title, "Authentication required");
  assert.equal(typeof body.requestId, "string");
  await f.app.close();
  f.store.close();
});

test("Principal can list and revoke sessions, including revoke-all", async () => {
  const f = await fixture();
  const second = f.store.createSession(
    "principal:test",
    f.now(),
    config.sessionIdleSeconds,
    config.sessionAbsoluteSeconds,
    "second-agent",
  );

  const sessions = await f.app.inject({
    method: "GET",
    url: "/api/security/sessions",
    headers: { cookie: sessionCookie(f.token) },
  });
  assert.equal(sessions.statusCode, 200);
  assert.equal(sessions.json().sessions.length, 2);

  const antiCsrf = await csrf(f.app, f.token);
  const cookies = sessionCookie(f.token) + "; " + antiCsrf.cookie;
  const revokeSecond = await f.app.inject({
    method: "DELETE",
    url: "/api/security/sessions/" + second.session.sessionId,
    headers: {
      cookie: cookies,
      origin: config.origin,
      "x-csrf-token": antiCsrf.token,
    },
  });
  assert.equal(revokeSecond.statusCode, 200);

  const secondUse = await f.app.inject({
    method: "GET",
    url: "/api/me",
    headers: { cookie: sessionCookie(second.token) },
  });
  assert.equal(secondUse.statusCode, 401);

  const revokeAll = await f.app.inject({
    method: "POST",
    url: "/api/security/sessions/revoke-all",
    headers: {
      cookie: cookies,
      origin: config.origin,
      "x-csrf-token": antiCsrf.token,
    },
  });
  assert.equal(revokeAll.statusCode, 200);
  assert.equal(revokeAll.json().revokedSessions, 1);

  const firstUse = await f.app.inject({
    method: "GET",
    url: "/api/me",
    headers: { cookie: sessionCookie(f.token) },
  });
  assert.equal(firstUse.statusCode, 401);
  await f.app.close();
  f.store.close();
});

test("WebAuthn challenges are one-shot even before browser ceremony tests", () => {
  const store = new WebStore(":memory:");
  store.ensurePrincipal("principal:test", "test-user", "Test User", 100);
  const challenge = store.createChallenge(
    "login",
    "principal:test",
    "challenge-value",
    100,
    60,
  );
  const consumed = store.consumeChallenge(challenge.challengeId, "login", 110);
  assert.equal(consumed.challenge, "challenge-value");
  assert.throws(
    () => store.consumeChallenge(challenge.challengeId, "login", 111),
    /missing, expired, consumed/,
  );
  store.close();
});
