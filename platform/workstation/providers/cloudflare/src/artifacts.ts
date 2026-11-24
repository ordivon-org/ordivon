import type { ExecutionLease } from "./execution.js";

const MAX_KEY_BYTES = 512;
const SAFE_SEGMENT = /^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$/;
const ALLOWED_NAMESPACES = new Set([
  "artifacts",
  "browser",
  "fetch",
  "receipts"
]);

export function validateArtifactKey(key: string): string {
  const encodedLength = new TextEncoder().encode(key).byteLength;
  if (encodedLength === 0 || encodedLength > MAX_KEY_BYTES) {
    throw new Error("artifact key length is outside the allowed range");
  }
  if (key.startsWith("/") || key.endsWith("/") || key.includes("\\")) {
    throw new Error("artifact key must be a normalized relative path");
  }
  const segments = key.split("/");
  const namespace = segments[0];
  if (namespace === undefined || !ALLOWED_NAMESPACES.has(namespace)) {
    throw new Error("artifact key namespace is not allowed");
  }
  if (segments.length < 2 || segments.some((segment) => !SAFE_SEGMENT.test(segment))) {
    throw new Error("artifact key contains an unsafe path segment");
  }
  return key;
}

/** Allocate an independent bundle identity for one physical execution.
 * Request IDs and generation numbers may recur after native state retention. */
export function newArtifactBundlePrefix(
  lease: Pick<ExecutionLease, "operation" | "request_id" | "lease_generation">
): string {
  const namespace = lease.operation === "fetch" ? "fetch" : "browser";
  return `${namespace}/v2/${lease.request_id}/g${lease.lease_generation}/${crypto.randomUUID()}`;
}
