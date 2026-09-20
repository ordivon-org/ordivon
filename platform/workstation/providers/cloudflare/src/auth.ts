import { EdgeError } from "./errors.js";
import { REQUEST_POLICY } from "./policy.js";

const AUTH_SCHEME = "Ordivon-HMAC";
const REQUEST_ID_PATTERN = /^[a-z0-9][a-z0-9_-]{7,63}$/;
const KEY_ID_PATTERN = /^[a-z0-9][a-z0-9_-]{2,31}$/;
const encoder = new TextEncoder();

export interface AuthEnvironment {
  readonly EDGE_HMAC_KEY_ID: string;
  readonly EDGE_HMAC_SECRET: string;
}

export function isValidRequestId(value: string): boolean {
  return REQUEST_ID_PATTERN.test(value);
}

export interface AuthContext {
  readonly keyId: string;
  readonly requestId: string;
  readonly timestamp: number;
  readonly bodySha256: string;
  readonly requestDigest: string;
  readonly canonicalRequest: string;
}

export async function sha256Hex(value: Uint8Array | string): Promise<string> {
  const bytes = typeof value === "string" ? encoder.encode(value) : value;
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return [...digest].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function decodeBase64Url(value: string): Uint8Array {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) {
    throw new EdgeError("invalid_authentication", 401, "The request signature is invalid.");
  }
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  let decoded: string;
  try {
    decoded = atob(value.replace(/-/g, "+").replace(/_/g, "/") + padding);
  } catch {
    throw new EdgeError("invalid_authentication", 401, "The request signature is invalid.");
  }
  return Uint8Array.from(decoded, (character) => character.charCodeAt(0));
}

function constantTimeEqual(left: Uint8Array, right: Uint8Array): boolean {
  if (left.byteLength !== right.byteLength) {
    return false;
  }
  let difference = 0;
  for (let index = 0; index < left.byteLength; index += 1) {
    difference |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return difference === 0;
}

function parseAuthorization(value: string | null): { keyId: string; signature: Uint8Array } {
  if (value === null || !value.startsWith(`${AUTH_SCHEME} `)) {
    throw new EdgeError("authentication_required", 401, "A signed Ordivon request is required.");
  }
  const credentials = value.slice(AUTH_SCHEME.length + 1);
  const separator = credentials.indexOf(":");
  if (separator <= 0 || separator === credentials.length - 1) {
    throw new EdgeError("invalid_authentication", 401, "The request signature is invalid.");
  }
  const keyId = credentials.slice(0, separator);
  if (!KEY_ID_PATTERN.test(keyId)) {
    throw new EdgeError("invalid_authentication", 401, "The request signature is invalid.");
  }
  return { keyId, signature: decodeBase64Url(credentials.slice(separator + 1)) };
}

export async function verifySignedRequest(
  request: Request,
  body: Uint8Array,
  environment: AuthEnvironment,
  nowSeconds = Math.floor(Date.now() / 1000)
): Promise<AuthContext> {
  const { keyId, signature } = parseAuthorization(request.headers.get("authorization"));
  if (keyId !== environment.EDGE_HMAC_KEY_ID) {
    throw new EdgeError("invalid_authentication", 401, "The request signature is invalid.");
  }

  const requestId = request.headers.get("x-ordivon-request-id") ?? "";
  if (!REQUEST_ID_PATTERN.test(requestId)) {
    throw new EdgeError("invalid_request_id", 400, "X-Ordivon-Request-Id is missing or invalid.");
  }

  const timestampText = request.headers.get("x-ordivon-timestamp") ?? "";
  if (!/^\d{10}$/.test(timestampText)) {
    throw new EdgeError("invalid_timestamp", 401, "X-Ordivon-Timestamp is missing or invalid.");
  }
  const timestamp = Number.parseInt(timestampText, 10);
  if (Math.abs(nowSeconds - timestamp) > REQUEST_POLICY.clock_skew_seconds) {
    throw new EdgeError("stale_request", 401, "The signed request is outside the allowed time window.");
  }

  const bodySha256 = await sha256Hex(body);
  const url = new URL(request.url);
  const canonicalTarget = `${url.pathname}${url.search}`;
  const method = request.method.toUpperCase();
  const canonicalRequest = [
    "ordivon-edge-v1",
    method,
    canonicalTarget,
    requestId,
    timestampText,
    bodySha256
  ].join("\n");
  const idempotencyRequest = [
    "ordivon-edge-idempotency-v1",
    method,
    canonicalTarget,
    bodySha256
  ].join("\n");

  const secret = decodeBase64Url(environment.EDGE_HMAC_SECRET);
  if (secret.byteLength < 32) {
    throw new EdgeError("authentication_unavailable", 503, "The Edge authentication key is misconfigured.", "failed");
  }
  const key = await crypto.subtle.importKey(
    "raw",
    secret,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const expected = new Uint8Array(
    await crypto.subtle.sign("HMAC", key, encoder.encode(canonicalRequest))
  );
  if (!constantTimeEqual(signature, expected)) {
    throw new EdgeError("invalid_authentication", 401, "The request signature is invalid.");
  }

  return {
    keyId,
    requestId,
    timestamp,
    bodySha256,
    requestDigest: await sha256Hex(idempotencyRequest),
    canonicalRequest
  };
}
