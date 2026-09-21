import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

import { createWebApp } from "../src/app.ts";
import type { WebConfig } from "../src/config.ts";
import { WebStore } from "../src/store.ts";

const config: WebConfig = {
  host: "127.0.0.1",
  port: 8790,
  origin: "http://localhost:8790",
  rpID: "localhost",
  rpName: "Ordivon Browser E2E",
  databasePath: ":memory:",
  bootstrapEnrollmentToken: "browser-bootstrap",
  sessionIdleSeconds: 300,
  sessionAbsoluteSeconds: 3600,
};

const chromiumExecutable = process.env.ORDIVON_WEB_CHROMIUM_EXECUTABLE;
if (chromiumExecutable === undefined || chromiumExecutable === "") {
  throw new Error("ORDIVON_WEB_CHROMIUM_EXECUTABLE is required");
}
const bootstrapToken = config.bootstrapEnrollmentToken;
if (bootstrapToken === undefined || bootstrapToken === "") {
  throw new Error("bootstrap enrollment token is required for browser e2e");
}

const store = new WebStore(":memory:");
const app = await createWebApp(config, { store });
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

  const auth = await page.evaluate(
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
          principalId: "principal:browser-e2e",
          userName: "browser-e2e",
          displayName: "Browser E2E",
        }),
      });
      const enrollment = (await enrollOptions.json()) as {
        challengeId: string;
        options: unknown;
      };
      const registration = await api.startRegistration({
        optionsJSON: enrollment.options,
      });
      const enrollVerify = await fetch("/api/auth/enroll/verify", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-bootstrap-enrollment-token": bootstrapToken,
        },
        body: JSON.stringify({
          challengeId: enrollment.challengeId,
          response: registration,
        }),
      });
      const enrollVerifyBody = await enrollVerify.json();

      const enrollReplay = await fetch("/api/auth/enroll/verify", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-bootstrap-enrollment-token": bootstrapToken,
        },
        body: JSON.stringify({
          challengeId: enrollment.challengeId,
          response: registration,
        }),
      });

      const loginOptions = await fetch("/api/auth/login/options", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ userName: "browser-e2e" }),
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
      const loginVerifyBody = await loginVerify.json();

      const loginReplay = await fetch("/api/auth/login/verify", {
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
        enrollVerifyBody,
        enrollReplay: enrollReplay.status,
        loginOptions: loginOptions.status,
        loginVerify: loginVerify.status,
        loginVerifyBody,
        loginReplay: loginReplay.status,
      };
    },
    { bootstrapToken },
  );

  assert.equal(auth.enrollOptions, 200);
  assert.equal(auth.enrollVerify, 200);
  assert.equal(auth.enrollReplay, 409);
  assert.equal(auth.loginOptions, 200);
  assert.equal(auth.loginVerify, 200);
  assert.equal(auth.loginReplay, 409);

  const cookies = await context.cookies(config.origin);
  const session = cookies.find((cookie) => cookie.name === "__Host-session");
  assert.ok(session);
  assert.equal(session.secure, true);
  assert.equal(session.httpOnly, true);
  assert.equal(session.sameSite, "Lax");
  assert.equal(session.path, "/");

  const browserFlow = await page.evaluate(async () => {
    const me = await fetch("/api/me");
    const meBody = await me.json();

    const csrf = await fetch("/api/session/csrf");
    const csrfBody = (await csrf.json()) as { token: string };

    const create = await fetch("/api/canary/notes", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-csrf-token": csrfBody.token,
      },
      body: JSON.stringify({ content: "browser canary draft" }),
    });
    const createBody = await create.json();

    const notes = await fetch("/api/canary/notes");
    const notesBody = await notes.json();

    const sessions = await fetch("/api/security/sessions");
    const sessionsBody = await sessions.json();

    const passkeys = await fetch("/api/security/passkeys");
    const passkeysBody = await passkeys.json();

    const logout = await fetch("/api/session/logout", {
      method: "POST",
      headers: { "x-csrf-token": csrfBody.token },
    });
    const logoutBody = await logout.json();

    const afterLogout = await fetch("/api/me");
    return {
      me: { status: me.status, body: meBody },
      create: { status: create.status, body: createBody },
      notes: { status: notes.status, body: notesBody },
      sessions: { status: sessions.status, body: sessionsBody },
      passkeys: { status: passkeys.status, body: passkeysBody },
      logout: { status: logout.status, body: logoutBody },
      afterLogout: {
        status: afterLogout.status,
        body: await afterLogout.json(),
      },
    };
  });

  assert.equal(browserFlow.me.status, 200);
  assert.equal(browserFlow.create.status, 201);
  assert.equal(browserFlow.create.body.note.state, "DRAFT");
  assert.equal(browserFlow.notes.body.notes.length, 1);
  assert.equal(browserFlow.sessions.body.sessions.length, 1);
  assert.equal(browserFlow.passkeys.body.credentials.length, 1);
  assert.equal(browserFlow.logout.status, 200);
  assert.equal(browserFlow.afterLogout.status, 401);

  const afterCookies = await context.cookies(config.origin);
  assert.equal(
    afterCookies.some((cookie) => cookie.name === "__Host-session"),
    false,
  );

  const auditCount = (
    store.db.prepare("SELECT count(*) AS n FROM audit_events").get() as {
      n: number;
    }
  ).n;
  assert.ok(auditCount >= 4);

  console.log(
    JSON.stringify(
      {
        auth,
        sessionCookie: {
          secure: session.secure,
          httpOnly: session.httpOnly,
          sameSite: session.sameSite,
          path: session.path,
        },
        browserFlow,
        auditCount,
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
