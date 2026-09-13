import { Buffer } from "node:buffer";
import { createHash, createHmac, randomBytes } from "node:crypto";

import type { Env } from "../src/index.js";

export const TEST_SECRET_BYTES = randomBytes(32);
export const TEST_SECRET = Buffer.from(TEST_SECRET_BYTES).toString("base64url");
export const TEST_ENV_BASE = {
  EDGE_HMAC_KEY_ID: "runtime-v1",
  EDGE_HMAC_SECRET: TEST_SECRET,
  FETCH_ALLOWED_HOSTS: "allowed.example.org,redirect.example.org"
} as const;

interface StoredObject {
  readonly bytes: Uint8Array;
  readonly etag: string;
  readonly uploaded: Date;
  readonly httpMetadata: R2HTTPMetadata;
  readonly customMetadata: Record<string, string>;
}

function bytesFrom(value: unknown): Promise<Uint8Array> | Uint8Array {
  if (value === null) return new Uint8Array();
  if (typeof value === "string") return new TextEncoder().encode(value);
  if (value instanceof Uint8Array) return value;
  if (value instanceof ArrayBuffer) return new Uint8Array(value);
  if (ArrayBuffer.isView(value)) {
    return new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
  }
  if (value instanceof Blob) return value.arrayBuffer().then((buffer) => new Uint8Array(buffer));
  if (value instanceof ReadableStream) {
    return new Response(value).arrayBuffer().then((buffer) => new Uint8Array(buffer));
  }
  throw new Error("unsupported fake R2 value");
}

function normalizeHttpMetadata(value: R2HTTPMetadata | Headers | undefined): R2HTTPMetadata {
  if (value === undefined) return {};
  if (value instanceof Headers) {
    const contentType = value.get("content-type");
    return contentType === null ? {} : { contentType };
  }
  return value;
}

export type PutFault = "throw_before" | "throw_after" | "return_null";

export class MemoryR2 {
  readonly objects = new Map<string, StoredObject>();
  readonly deletedKeys: string[] = [];
  private sequence = 0;
  private deleteFailuresRemaining = 0;
  private readonly putCounts = new Map<string, number>();
  private readonly putFaults = new Map<string, Map<number, PutFault>>();
  private readonly putWaiters = new Map<string, Set<() => void>>();

  waitForPut(key: string): Promise<void> {
    if (this.objects.has(key)) return Promise.resolve();
    return new Promise((resolve) => {
      const waiters = this.putWaiters.get(key) ?? new Set<() => void>();
      waiters.add(resolve);
      this.putWaiters.set(key, waiters);
    });
  }

  faultPut(key: string, callNumber: number, fault: PutFault): void {
    if (!Number.isInteger(callNumber) || callNumber < 1) {
      throw new Error("callNumber must be a positive integer");
    }
    const byCall = this.putFaults.get(key) ?? new Map<number, PutFault>();
    byCall.set(callNumber, fault);
    this.putFaults.set(key, byCall);
  }

  putCount(key: string): number {
    return this.putCounts.get(key) ?? 0;
  }

  failNextDelete(): void {
    this.deleteFailuresRemaining += 1;
  }

  asBucket(): R2Bucket {
    const self = this;
    return {
      async get(key: string): Promise<R2ObjectBody | null> {
        const stored = self.objects.get(key);
        if (stored === undefined) return null;
        const bodyBytes = stored.bytes.slice();
        return {
          key,
          version: stored.etag,
          size: bodyBytes.byteLength,
          etag: stored.etag,
          httpEtag: `"${stored.etag}"`,
          uploaded: stored.uploaded,
          httpMetadata: stored.httpMetadata,
          customMetadata: stored.customMetadata,
          range: undefined,
          checksums: {},
          storageClass: "Standard",
          body: new Blob([bodyBytes]).stream(),
          bodyUsed: false,
          async arrayBuffer() {
            return bodyBytes.buffer.slice(
              bodyBytes.byteOffset,
              bodyBytes.byteOffset + bodyBytes.byteLength
            );
          },
          async text() {
            return new TextDecoder().decode(bodyBytes);
          },
          async json<T>() {
            return JSON.parse(new TextDecoder().decode(bodyBytes)) as T;
          },
          async blob() {
            const type = stored.httpMetadata.contentType;
            return type === undefined
              ? new Blob([bodyBytes])
              : new Blob([bodyBytes], { type });
          },
          writeHttpMetadata(headers: Headers) {
            if (stored.httpMetadata.contentType !== undefined) {
              headers.set("content-type", stored.httpMetadata.contentType);
            }
          }
        } as unknown as R2ObjectBody;
      },
      async put(key: string, value: unknown, options?: R2PutOptions): Promise<R2Object | null> {
        const callNumber = (self.putCounts.get(key) ?? 0) + 1;
        self.putCounts.set(key, callNumber);
        const fault = self.putFaults.get(key)?.get(callNumber);
        if (fault === "throw_before") {
          throw new Error(`injected R2 put failure before write: ${key}`);
        }
        if (fault === "return_null") {
          return null;
        }
        const existing = self.objects.get(key);
        const onlyIf = options?.onlyIf;
        if (
          onlyIf !== undefined &&
          "etagDoesNotMatch" in onlyIf &&
          onlyIf.etagDoesNotMatch === "*" &&
          existing !== undefined
        ) {
          return null;
        }
        if (
          onlyIf !== undefined &&
          "etagMatches" in onlyIf &&
          existing?.etag !== onlyIf.etagMatches
        ) {
          return null;
        }
        const bytes = (await bytesFrom(value)).slice();
        self.sequence += 1;
        const etag = `etag-${self.sequence}`;
        const stored: StoredObject = {
          bytes,
          etag,
          uploaded: new Date(),
          httpMetadata: normalizeHttpMetadata(options?.httpMetadata),
          customMetadata: options?.customMetadata ?? {}
        };
        self.objects.set(key, stored);
        const waiters = self.putWaiters.get(key);
        if (waiters !== undefined) {
          self.putWaiters.delete(key);
          for (const resolve of waiters) resolve();
        }
        if (fault === "throw_after") {
          throw new Error(`injected R2 put failure after write: ${key}`);
        }
        return {
          key,
          version: etag,
          size: bytes.byteLength,
          etag,
          httpEtag: `"${etag}"`,
          uploaded: stored.uploaded,
          httpMetadata: stored.httpMetadata,
          customMetadata: stored.customMetadata,
          range: undefined,
          checksums: {},
          storageClass: "Standard",
          writeHttpMetadata() {}
        } as unknown as R2Object;
      },
      async delete(key: string | string[]) {
        if (self.deleteFailuresRemaining > 0) {
          self.deleteFailuresRemaining -= 1;
          throw new Error("injected R2 delete failure");
        }
        for (const candidate of Array.isArray(key) ? key : [key]) {
          self.deletedKeys.push(candidate);
          self.objects.delete(candidate);
        }
      }
    } as unknown as R2Bucket;
  }
}

export function makeEnv(memory = new MemoryR2()): Env {
  return {
    ...TEST_ENV_BASE,
    ARTIFACTS: memory.asBucket(),
    BROWSER: {
      async quickAction() {
        return new Response(
          JSON.stringify({
            success: false,
            errors: [{ message: "Browser runner was not injected in the test." }]
          }),
          { status: 503, headers: { "content-type": "application/json" } }
        );
      }
    } as unknown as BrowserRun,
    FETCH_RATE_LIMIT: {
      async limit() {
        return { success: true };
      }
    } as RateLimit,
    BROWSER_RATE_LIMIT: {
      async limit() {
        return { success: true };
      }
    } as RateLimit,
    CF_VERSION_METADATA: {
      id: "test-worker-version",
      tag: "test",
      timestamp: "2026-07-27T00:00:00.000Z"
    }
  };
}

export function signedRequest(
  url: string,
  options: {
    readonly method?: string;
    readonly body?: string;
    readonly requestId?: string;
    readonly timestamp?: number;
  } = {}
): Request {
  const method = options.method ?? "GET";
  const body = options.body ?? "";
  const requestId = options.requestId ?? "request_test_001";
  const timestamp = options.timestamp ?? Math.floor(Date.now() / 1000);
  const target = new URL(url);
  const bodySha256 = createHash("sha256").update(body).digest("hex");
  const canonical = [
    "ordivon-edge-v1",
    method.toUpperCase(),
    `${target.pathname}${target.search}`,
    requestId,
    String(timestamp),
    bodySha256
  ].join("\n");
  const signature = createHmac("sha256", TEST_SECRET_BYTES)
    .update(canonical)
    .digest("base64url");
  const init: RequestInit = {
    method,
    headers: {
      authorization: `Ordivon-HMAC runtime-v1:${signature}`,
      "x-ordivon-request-id": requestId,
      "x-ordivon-timestamp": String(timestamp),
      ...(body === "" ? {} : { "content-type": "application/json" })
    },
    ...(method === "GET" || method === "HEAD" ? {} : { body })
  };
  return new Request(url, init);
}
