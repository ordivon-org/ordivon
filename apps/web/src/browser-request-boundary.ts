/** Browser request validation and cookie policy; no server construction or state storage. */

import type { FastifyReply, FastifyRequest } from "fastify";

import type { WebConfig } from "./config.ts";
import { WebProblem } from "./errors.ts";

export const SESSION_COOKIE = "__Host-session";
export const CSRF_COOKIE = "__Host-csrf-secret";

export function textHeader(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export function requireString(
  body: Record<string, unknown>,
  name: string,
  maxLength = 256,
): string {
  const value = body[name];
  if (typeof value !== "string" || value.length < 1 || value.length > maxLength) {
    throw new WebProblem(
      422,
      "invalid-input",
      "Invalid input",
      name + " is invalid.",
    );
  }
  return value;
}

export function requireObject(
  body: Record<string, unknown>,
  name: string,
): Record<string, unknown> {
  const value = body[name];
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    throw new WebProblem(
      422,
      "invalid-input",
      "Invalid input",
      name + " must be an object.",
    );
  }
  return value as Record<string, unknown>;
}

export function asBody(request: FastifyRequest): Record<string, unknown> {
  const value: unknown = request.body;
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    throw new WebProblem(
      422,
      "invalid-input",
      "Invalid input",
      "Request body must be a JSON object.",
    );
  }
  return value as Record<string, unknown>;
}

function unsafeMethod(method: string): boolean {
  return method !== "GET" && method !== "HEAD" && method !== "OPTIONS";
}

export function sameOriginGuard(config: WebConfig) {
  return async function guard(request: FastifyRequest): Promise<void> {
    if (!unsafeMethod(request.method)) return;
    const origin = textHeader(request.headers.origin);
    if (origin !== config.origin) {
      throw new WebProblem(
        403,
        "origin-rejected",
        "Cross-site request rejected",
        "Unsafe browser requests must carry the configured Origin.",
      );
    }
    const fetchSite = textHeader(request.headers["sec-fetch-site"]);
    if (fetchSite === "cross-site") {
      throw new WebProblem(
        403,
        "fetch-metadata-rejected",
        "Cross-site request rejected",
        "Cross-site browser mutations are not admitted.",
      );
    }
  };
}

export function sessionCookie(reply: FastifyReply, token: string, maxAge: number): void {
  reply.setCookie(SESSION_COOKIE, token, {
    path: "/",
    secure: true,
    httpOnly: true,
    sameSite: "lax",
    maxAge,
    priority: "high",
  });
}

export function clearSessionCookie(reply: FastifyReply): void {
  reply.clearCookie(SESSION_COOKIE, {
    path: "/",
    secure: true,
    httpOnly: true,
    sameSite: "lax",
  });
}
