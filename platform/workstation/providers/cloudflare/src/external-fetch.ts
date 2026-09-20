import { sha256Hex } from "./auth.js";
import type { ArtifactReference, FetchReceiptDetails } from "./contracts.js";
import type { ExecutionLease } from "./execution.js";
import { EdgeError } from "./errors.js";
import { FETCH_POLICY } from "./policy.js";
import {
  validateExternalUrl,
  type FetchPolicyEnvironment,
  type ValidatedFetchRequest
} from "./fetch-policy.js";

const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);

export interface FetchExecutionEnvironment extends FetchPolicyEnvironment {
  readonly ARTIFACTS: R2Bucket;
}

export interface FetchExecutionResult {
  readonly artifact: ArtifactReference;
  readonly artifacts: readonly ArtifactReference[];
  readonly fetch: FetchReceiptDetails;
}

export type ExternalFetcher = (
  input: RequestInfo | URL,
  init?: RequestInit
) => Promise<Response>;

async function readResponseLimited(
  response: Response,
  maximumBytes: number
): Promise<Uint8Array> {
  const declaredLength = response.headers.get("content-length");
  if (declaredLength !== null) {
    const parsed = Number.parseInt(declaredLength, 10);
    if (Number.isSafeInteger(parsed) && parsed > maximumBytes) {
      await response.body?.cancel("external response exceeded limit");
      throw new EdgeError(
        "response_too_large",
        502,
        "The external response exceeds the allowed size.",
        "failed"
      );
    }
  }

  if (response.body === null) {
    return new Uint8Array();
  }
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      total += value.byteLength;
      if (total > maximumBytes) {
        await reader.cancel("external response exceeded limit");
        throw new EdgeError(
          "response_too_large",
          502,
          "The external response exceeds the allowed size.",
          "failed"
        );
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

function mediaType(response: Response): string {
  const value = response.headers.get("content-type") ?? "application/octet-stream";
  if (value.length > 256 || /[\r\n\0]/.test(value)) {
    return "application/octet-stream";
  }
  return value;
}

export async function executeExternalFetch(
  environment: FetchExecutionEnvironment,
  lease: ExecutionLease,
  request: ValidatedFetchRequest,
  fetcher: ExternalFetcher = fetch
): Promise<FetchExecutionResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), request.timeoutMs);
  const visited = new Set<string>();
  const requestedUrl = request.url.toString();
  let currentUrl = request.url;
  let redirectCount = 0;
  let response: Response;

  try {
    while (true) {
      const serialized = currentUrl.toString();
      if (visited.has(serialized)) {
        throw new EdgeError("redirect_loop", 502, "The external request entered a redirect loop.", "failed");
      }
      visited.add(serialized);

      try {
        response = await fetcher(currentUrl, {
          method: "GET",
          redirect: "manual",
          signal: controller.signal,
          headers: {
            accept: request.accept,
            "user-agent": "Ordivon-Edge/0.1"
          }
        });
      } catch (error) {
        if (controller.signal.aborted) {
          throw new EdgeError("fetch_timeout", 504, "The external request exceeded its time budget.", "failed");
        }
        throw new EdgeError("fetch_failed", 502, "The external request failed.", "failed");
      }

      if (!REDIRECT_STATUSES.has(response.status)) {
        break;
      }
      if (redirectCount >= FETCH_POLICY.max_redirects) {
        await response.body?.cancel("redirect budget exceeded");
        throw new EdgeError("too_many_redirects", 502, "The external request exceeded its redirect budget.", "failed");
      }
      const location = response.headers.get("location");
      await response.body?.cancel("following validated redirect");
      if (location === null) {
        throw new EdgeError("invalid_redirect", 502, "The external response contains an invalid redirect.", "failed");
      }
      currentUrl = validateExternalUrl(new URL(location, currentUrl).toString(), environment);
      redirectCount += 1;
    }

    const body = await readResponseLimited(response, request.maximumBytes);
    const sha256 = await sha256Hex(body);
    const artifactKey = `fetch/v2/${lease.request_id}/g${lease.lease_generation}/body`;
    const contentType = mediaType(response);
    const stored = await environment.ARTIFACTS.put(artifactKey, body, {
      httpMetadata: { contentType },
      customMetadata: {
        receipt_id: lease.request_id,
        sha256,
        source_host: currentUrl.hostname,
        http_status: String(response.status),
        policy_version: lease.policy_version,
        capability_version: lease.capability_version,
        worker_version_id: lease.worker_version_id,
        lease_generation: String(lease.lease_generation)
      }
    });
    if (stored === null) {
      throw new EdgeError("artifact_store_failed", 500, "The external response could not be persisted.", "failed");
    }

    return {
      artifact: {
        key: artifactKey,
        sha256,
        bytes: body.byteLength,
        media_type: contentType,
        etag: stored.etag
      },
      artifacts: [
        {
          key: artifactKey,
          sha256,
          bytes: body.byteLength,
          media_type: contentType,
          etag: stored.etag
        }
      ],
      fetch: {
        requested_url: requestedUrl,
        final_url: currentUrl.toString(),
        http_status: response.status,
        redirect_count: redirectCount
      }
    };
  } finally {
    clearTimeout(timeout);
  }
}
