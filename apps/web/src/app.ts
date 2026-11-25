import cookie from "@fastify/cookie";
import csrfProtection from "@fastify/csrf-protection";
import helmet from "@fastify/helmet";
import rateLimit from "@fastify/rate-limit";
import Fastify, {
  type FastifyInstance,
  type FastifyReply,
  type FastifyRequest,
} from "fastify";
import type {
  AuthenticationResponseJSON,
  RegistrationResponseJSON,
} from "@simplewebauthn/server";

import type { WebConfig } from "./config.ts";
import { renderOperatorGrants } from "./operator-grants-view.ts";
import type { GrantObservation } from "./grant-observation.ts";
import { WebProblem } from "./errors.ts";
import { registerAgentCanaryRoutes } from "./agent-canary-routes.ts";
import {
  SecurityContractAdmissionEvaluator,
  type AgentAdmissionEvaluator,
  type AgentRequestVerifier,
} from "./agent-authority.ts";
import type {
  AuthenticatedSession,
} from "./model.ts";
import {
  CSRF_COOKIE,
  SESSION_COOKIE,
  asBody,
  clearSessionCookie,
  requireObject,
  requireString,
  sameOriginGuard,
  sessionCookie,
  textHeader,
} from "./browser-request-boundary.ts";
import { WebStore } from "./store.ts";
import { loadOperatorGrantsUi } from "./operator-grants-ui.ts";
import { WebAuthnAccountService } from "./webauthn.ts";

export interface WebDependencies {
  readonly store?: WebStore;
  readonly now?: () => number;
  readonly agentVerifier?: AgentRequestVerifier;
  readonly agentAdmission?: AgentAdmissionEvaluator;
}

export async function createWebApp(
  config: WebConfig,
  dependencies: WebDependencies = {},
): Promise<FastifyInstance> {
  const operatorUi = config.operatorGrantsDist === undefined ? null : loadOperatorGrantsUi(config.operatorGrantsDist);
  const app = Fastify({
    logger: false,
    trustProxy: false,
    genReqId: () => crypto.randomUUID(),
  });
  const store = dependencies.store ?? new WebStore(config.databasePath);
  const now = dependencies.now ?? (() => Math.floor(Date.now() / 1000));
  const webAuthn = new WebAuthnAccountService(store, config, now);
  const sameOrigin = sameOriginGuard(config);
  const agentAdmission =
    dependencies.agentAdmission ?? new SecurityContractAdmissionEvaluator();

  await app.register(cookie);
  await app.register(csrfProtection, {
    cookieKey: CSRF_COOKIE,
    cookieOpts: {
      path: "/",
      secure: true,
      httpOnly: true,
      sameSite: "strict",
    },
    getToken: (request) => textHeader(request.headers["x-csrf-token"]) ?? undefined,
  });
  await app.register(helmet, {
    global: true,
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'"],
        imgSrc: ["'self'", "data:"],
        connectSrc: ["'self'"],
        objectSrc: ["'none'"],
        baseUri: ["'none'"],
        frameAncestors: ["'none'"],
        formAction: ["'self'"],
      },
    },
    referrerPolicy: { policy: "no-referrer" },
    hsts: {
      maxAge: 63072000,
      includeSubDomains: true,
      preload: true,
    },
  });
  await app.register(rateLimit, {
    global: true,
    max: 120,
    timeWindow: "1 minute",
  });

  app.addHook("onSend", async (request, reply, payload) => {
    reply.header(
      "Permissions-Policy",
      "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    );
    if (
      request.url.startsWith("/api/") ||
      request.url.startsWith("/security/")
    ) {
      reply.header("Cache-Control", "no-store");
    }
    return payload;
  });

  function authenticated(request: FastifyRequest): AuthenticatedSession {
    const token = request.cookies[SESSION_COOKIE];
    if (typeof token !== "string" || token.length < 20) {
      throw new WebProblem(
        401,
        "session-missing",
        "Authentication required",
        "A valid browser session is required.",
      );
    }
    return store.authenticateSession(token, now(), config.sessionIdleSeconds);
  }

  app.setErrorHandler((error, request, reply) => {
    const known = error instanceof WebProblem;
    const externalStatus =
      typeof error === "object" &&
      error !== null &&
      "statusCode" in error &&
      typeof error.statusCode === "number"
        ? error.statusCode
        : 500;
    const status = known
      ? error.status
      : externalStatus >= 400
        ? externalStatus
        : 500;
    const code = known
      ? error.code
      : status === 429
        ? "rate-limit-exceeded"
        : "internal-error";
    const title = known
      ? error.title
      : status === 429
        ? "Too many requests"
        : "Internal server error";
    const detail = known
      ? error.message
      : status === 429
        ? "The request rate exceeded the configured limit."
        : "The request could not be completed.";
    reply
      .code(status)
      .type("application/problem+json")
      .send({
        type: config.origin + "/problems/" + code,
        title,
        status,
        detail,
        instance: request.url,
        requestId: request.id,
      });
  });

  app.get("/", async (_request, reply) => {
    return reply
      .type("text/html; charset=utf-8")
      .send("<!doctype html><meta charset=\"utf-8\"><title>Ordivon</title><main>Ordivon Web</main>");
  });

  app.get("/health", async () => ({
    status: "ok",
    component: "ordivon-web",
  }));

  app.post(
    "/api/auth/enroll/options",
    {
      onRequest: sameOrigin,
      config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    },
    async (request) => {
      if (
        config.bootstrapEnrollmentToken === undefined ||
        textHeader(request.headers["x-bootstrap-enrollment-token"]) !==
          config.bootstrapEnrollmentToken
      ) {
        throw new WebProblem(
          403,
          "enrollment-not-authorized",
          "Enrollment not authorized",
          "Initial Principal enrollment requires the canary bootstrap authority.",
        );
      }
      const body = asBody(request);
      return await webAuthn.registrationOptions(
        requireString(body, "principalId"),
        requireString(body, "userName"),
        requireString(body, "displayName"),
      );
    },
  );

  app.post(
    "/api/auth/enroll/verify",
    {
      onRequest: sameOrigin,
      config: { rateLimit: { max: 5, timeWindow: "1 minute" } },
    },
    async (request) => {
      if (
        config.bootstrapEnrollmentToken === undefined ||
        textHeader(request.headers["x-bootstrap-enrollment-token"]) !==
          config.bootstrapEnrollmentToken
      ) {
        throw new WebProblem(
          403,
          "enrollment-not-authorized",
          "Enrollment not authorized",
          "Initial Principal enrollment requires the canary bootstrap authority.",
        );
      }
      const body = asBody(request);
      const principal = await webAuthn.verifyRegistration(
        requireString(body, "challengeId"),
        requireObject(
          body,
          "response",
        ) as unknown as RegistrationResponseJSON,
      );
      return { principal };
    },
  );

  app.post(
    "/api/auth/login/options",
    {
      onRequest: sameOrigin,
      config: { rateLimit: { max: 10, timeWindow: "1 minute" } },
    },
    async (request) => {
      const body = asBody(request);
      return await webAuthn.loginOptions(requireString(body, "userName"));
    },
  );

  app.post(
    "/api/auth/login/verify",
    {
      onRequest: sameOrigin,
      config: { rateLimit: { max: 10, timeWindow: "1 minute" } },
    },
    async (request, reply) => {
      const body = asBody(request);
      const loggedIn = await webAuthn.verifyLogin(
        requireString(body, "challengeId"),
        requireObject(
          body,
          "response",
        ) as unknown as AuthenticationResponseJSON,
        textHeader(request.headers["user-agent"]),
      );
      sessionCookie(reply, loggedIn.token, config.sessionAbsoluteSeconds);
      return {
        principal: loggedIn.principal,
        session: loggedIn.session,
      };
    },
  );

  app.get("/api/me", async (request) => {
    const auth = authenticated(request);
    return {
      principal: auth.principal,
      session: auth.session,
    };
  });

  app.get("/api/session/csrf", async (request, reply) => {
    authenticated(request);
    const token = reply.generateCsrf();
    return { token };
  });

  app.get("/api/security/sessions", async (request) => {
    const auth = authenticated(request);
    return {
      currentSessionId: auth.session.sessionId,
      sessions: store.listSessions(auth.principal.principalId),
    };
  });

  app.get("/api/security/passkeys", async (request) => {
    const auth = authenticated(request);
    return {
      credentials: store
        .listCredentials(auth.principal.principalId)
        .map((credential) => ({
          credentialId: credential.credentialId,
          deviceType: credential.deviceType,
          backedUp: credential.backedUp,
          transports: credential.transports,
          createdAt: credential.createdAt,
          lastUsedAt: credential.lastUsedAt,
          revokedAt: credential.revokedAt,
        })),
    };
  });

  app.post(
    "/api/session/logout",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request, reply) => {
      const auth = authenticated(request);
      store.revokeSession(
        auth.principal.principalId,
        auth.session.sessionId,
        now(),
      );
      clearSessionCookie(reply);
      return { revoked: true };
    },
  );

  app.post(
    "/api/security/sessions/revoke-all",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request, reply) => {
      const auth = authenticated(request);
      const count = store.revokeAllSessions(auth.principal.principalId, now());
      clearSessionCookie(reply);
      return { revokedSessions: count };
    },
  );

  app.delete(
    "/api/security/sessions/:sessionId",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request) => {
      const auth = authenticated(request);
      const params = request.params as { sessionId?: unknown };
      if (typeof params.sessionId !== "string") {
        throw new WebProblem(
          422,
          "invalid-session-id",
          "Invalid session",
          "sessionId is required.",
        );
      }
      const revoked = store.revokeSession(
        auth.principal.principalId,
        params.sessionId,
        now(),
      );
      if (!revoked) {
        throw new WebProblem(
          404,
          "session-not-found",
          "Session not found",
          "No active session with that identifier belongs to this Principal.",
        );
      }
      return { revoked: true };
    },
  );

  app.get("/api/canary/notes", async (request) => {
    const auth = authenticated(request);
    return { notes: store.listCanaryNotes(auth.principal.principalId) };
  });

  app.post(
    "/api/canary/notes",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request, reply) => {
      const auth = authenticated(request);
      const body = asBody(request);
      const content = requireString(body, "content", 2000);
      const note = store.createCanaryNote(
        auth.principal.principalId,
        content,
        now(),
      );
      return reply.code(201).send({ note });
    },
  );

  // Build artifacts are public code only, never request-derived paths or owner data.
  if (operatorUi !== null) {
    for (const [path, asset] of operatorUi.assets) {
      app.get(path, async (_request, reply) => reply.header("Cache-Control", "no-store")
        .type(asset.contentType).send(asset.bytes));
    }
  }

  app.get("/operator/grants", async (request, reply) => {
    // Also cover authentication failures, not only the successful HTML.
    reply.header("Cache-Control", "no-store");
    const auth = authenticated(request);
    if (operatorUi !== null) return reply.type("text/html; charset=utf-8").send(operatorUi.html);
    const observedAt = now();
    const grants = store.listAgentGrants(auth.principal.principalId);
    return reply.type("text/html; charset=utf-8")
      .send(renderOperatorGrants(auth.principal, grants, observedAt));
  });

  app.get("/api/security/agents/grants", async (request): Promise<GrantObservation> => {
    const auth = authenticated(request);
    const observedAt = now();
    return {
      principalId: auth.principal.principalId,
      displayName: auth.principal.displayName,
      observedAt,
      grants: store.listAgentGrants(auth.principal.principalId),
    };
  });

  app.post(
    "/api/security/agents/grants/options",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request) => {
      const auth = authenticated(request);
      const body = asBody(request);
      return await webAuthn.agentGrantIssueOptions(
        auth.principal.principalId,
        requireString(body, "agentId"),
      );
    },
  );

  app.post(
    "/api/security/agents/grants/verify",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request, reply) => {
      const auth = authenticated(request);
      const body = asBody(request);
      const grant = await webAuthn.verifyAgentGrantIssue(
        requireString(body, "challengeId"),
        requireObject(
          body,
          "response",
        ) as unknown as AuthenticationResponseJSON,
      );
      if (grant.principalId !== auth.principal.principalId) {
        throw new WebProblem(
          403,
          "grant-principal-mismatch",
          "Agent Grant mismatch",
          "The signed Agent Grant belongs to a different Principal.",
        );
      }
      return reply.code(201).send({ grant });
    },
  );

  app.post(
    "/api/security/agents/grants/revoke/options",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request) => {
      const auth = authenticated(request);
      const body = asBody(request);
      return await webAuthn.agentGrantRevokeOptions(
        auth.principal.principalId,
        requireString(body, "grantId"),
      );
    },
  );

  app.post(
    "/api/security/agents/grants/revoke/verify",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request) => {
      const auth = authenticated(request);
      const body = asBody(request);
      const grant = await webAuthn.verifyAgentGrantRevoke(
        requireString(body, "challengeId"),
        requireObject(
          body,
          "response",
        ) as unknown as AuthenticationResponseJSON,
      );
      if (grant.principalId !== auth.principal.principalId) {
        throw new WebProblem(
          403,
          "grant-principal-mismatch",
          "Agent Grant mismatch",
          "The revoked Agent Grant belongs to a different Principal.",
        );
      }
      return { grant };
    },
  );

  app.post(
    "/api/security/agent-approvals/options",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request) => {
      const auth = authenticated(request);
      const body = asBody(request);
      return await webAuthn.effectApprovalOptions(
        auth.principal.principalId,
        requireString(body, "effectId"),
      );
    },
  );

  app.post(
    "/api/security/agent-approvals/verify",
    { onRequest: [sameOrigin, app.csrfProtection] },
    async (request, reply) => {
      const auth = authenticated(request);
      const body = asBody(request);
      const approved = await webAuthn.verifyEffectApproval(
        requireString(body, "challengeId"),
        requireObject(
          body,
          "response",
        ) as unknown as AuthenticationResponseJSON,
      );
      if (approved.principalId !== auth.principal.principalId) {
        throw new WebProblem(
          403,
          "approval-principal-mismatch",
          "Effect approval mismatch",
          "The approved Effect belongs to a different Principal.",
        );
      }
      return reply.code(201).send(approved);
    },
  );

  registerAgentCanaryRoutes(app, {
    config, store, now, agentAdmission, agentVerifier: dependencies.agentVerifier,
  });

  app.addHook("onClose", async () => {
    if (dependencies.store === undefined) {
      store.close();
    }
  });

  return app;
}
