import type {
  AuthenticationResponseJSON,
  RegistrationResponseJSON,
} from "@simplewebauthn/server";

import { asAdmissionLabError, AdmissionLabError } from "./errors.ts";
import type { WebAuthnPrincipalService } from "./webauthn-service.ts";

const MAX_BODY_BYTES = 64 * 1024;

function json(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

async function readObject(request: Request): Promise<Record<string, unknown>> {
  const bytes = new Uint8Array(await request.arrayBuffer());
  if (bytes.byteLength === 0 || bytes.byteLength > MAX_BODY_BYTES) {
    throw new AdmissionLabError("invalid_body", "Request body size is invalid.", 422);
  }
  const value: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    throw new AdmissionLabError("invalid_body", "Request body must be an object.", 422);
  }
  return value as Record<string, unknown>;
}

function requireString(
  body: Record<string, unknown>,
  name: string,
  maxLength = 256,
): string {
  const value = body[name];
  if (typeof value !== "string" || value.length < 1 || value.length > maxLength) {
    throw new AdmissionLabError("invalid_body", `${name} is invalid.`, 422);
  }
  return value;
}

function requireObject(
  body: Record<string, unknown>,
  name: string,
): Record<string, unknown> {
  const value = body[name];
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    throw new AdmissionLabError("invalid_body", `${name} must be an object.`, 422);
  }
  return value as Record<string, unknown>;
}

export interface WebAuthnRouterOptions {
  readonly enrollmentToken?: string;
}

export function createWebAuthnRouter(
  service: WebAuthnPrincipalService,
  options: WebAuthnRouterOptions,
) {
  return async function route(request: Request): Promise<Response | null> {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/webauthn-lab") {
      return new Response(
        `<!doctype html><meta charset="utf-8"><title>Ordivon WebAuthn Lab</title><main id="app">WebAuthn lab</main>`,
        {
          status: 200,
          headers: {
            "content-type": "text/html; charset=utf-8",
            "cache-control": "no-store",
          },
        },
      );
    }
    if (!url.pathname.startsWith("/api/webauthn/")) return null;

    try {
      if (request.method !== "POST") {
        return json({ error: "method_not_allowed" }, 405);
      }

      if (url.pathname.startsWith("/api/webauthn/enroll/")) {
        if (
          options.enrollmentToken === undefined ||
          request.headers.get("x-lab-enrollment-token") !== options.enrollmentToken
        ) {
          throw new AdmissionLabError(
            "enrollment_not_authorized",
            "Initial Principal enrollment is not authorized.",
            403,
          );
        }
      }

      const body = await readObject(request);

      if (url.pathname === "/api/webauthn/enroll/options") {
        const principalId = requireString(body, "principalId");
        const userName = requireString(body, "userName");
        const displayName = requireString(body, "displayName");
        return json(
          await service.registrationOptions(principalId, userName, displayName),
        );
      }

      if (url.pathname === "/api/webauthn/enroll/verify") {
        const challengeId = requireString(body, "challengeId");
        const response = requireObject(body, "response") as unknown as RegistrationResponseJSON;
        return json(await service.verifyRegistration(challengeId, response), 201);
      }

      if (url.pathname === "/api/webauthn/grants/options") {
        const principalId = requireString(body, "principalId");
        const agentId = requireString(body, "agentId");
        return json(await service.grantIssueOptions(principalId, agentId));
      }

      if (url.pathname === "/api/webauthn/grants/verify") {
        const challengeId = requireString(body, "challengeId");
        const response = requireObject(body, "response") as unknown as AuthenticationResponseJSON;
        return json(await service.verifyGrantIssue(challengeId, response), 201);
      }

      if (url.pathname === "/api/webauthn/grants/revoke/options") {
        const principalId = requireString(body, "principalId");
        const grantId = requireString(body, "grantId");
        return json(await service.grantRevokeOptions(principalId, grantId));
      }

      if (url.pathname === "/api/webauthn/grants/revoke/verify") {
        const challengeId = requireString(body, "challengeId");
        const response = requireObject(body, "response") as unknown as AuthenticationResponseJSON;
        return json(await service.verifyGrantRevoke(challengeId, response), 200);
      }

      if (url.pathname === "/api/webauthn/approvals/options") {
        const principalId = requireString(body, "principalId");
        const effectId = requireString(body, "effectId");
        return json(await service.effectApprovalOptions(principalId, effectId));
      }

      if (url.pathname === "/api/webauthn/approvals/verify") {
        const challengeId = requireString(body, "challengeId");
        const response = requireObject(body, "response") as unknown as AuthenticationResponseJSON;
        return json(await service.verifyEffectApproval(challengeId, response), 201);
      }

      return json({ error: "not_found" }, 404);
    } catch (error) {
      const normalized =
        error instanceof SyntaxError
          ? new AdmissionLabError("invalid_json", "Request body must be valid JSON.", 400)
          : asAdmissionLabError(error);
      return json(
        { error: normalized.code, message: normalized.message },
        normalized.httpStatus,
      );
    }
  };
}
