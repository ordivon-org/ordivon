import { isValidRequestId, verifySignedRequest, type AuthEnvironment } from "./auth.js";
import { validateArtifactKey } from "./artifacts.js";
import { readBodyLimited } from "./body.js";
import { capabilitiesDocument, EDGE_SCHEMA_VERSION } from "./contracts.js";
import { asEdgeError, EdgeError } from "./errors.js";
import { loadReceiptRecord } from "./idempotency.js";
import { errorResponse, jsonResponse, methodNotAllowed } from "./http.js";
import {
  runOperation,
  type OperationDependencies,
  type OperationEnvironment
} from "./operation-lifecycle.js";
import { effectivePolicyVersion, REQUEST_POLICY } from "./policy.js";
import { workerDeploymentIdentity } from "./version.js";

const RECEIPT_PREFIX = "/v1/receipts/";
const ARTIFACT_PREFIX = "/v1/artifacts/";

export interface Env extends AuthEnvironment, OperationEnvironment {}
export type HandlerDependencies = OperationDependencies;

async function handleReceiptGet(
  environment: Env,
  requestId: string
): Promise<Response> {
  if (!isValidRequestId(requestId)) {
    throw new EdgeError(
      "invalid_receipt_id",
      400,
      "The receipt ID is invalid."
    );
  }
  const receipt = await loadReceiptRecord(environment.ARTIFACTS, requestId);
  if (receipt === null) {
    return jsonResponse({ error: "receipt_not_found" }, 404);
  }
  return jsonResponse(receipt, receipt.status === "pending" ? 202 : 200);
}

function decodeArtifactKey(pathname: string): string {
  const encoded = pathname.slice(ARTIFACT_PREFIX.length);
  if (/%2f|%5c/i.test(encoded)) {
    throw new EdgeError(
      "invalid_artifact_key",
      400,
      "The artifact key is invalid."
    );
  }
  let decoded: string;
  try {
    decoded = encoded
      .split("/")
      .map((segment) => decodeURIComponent(segment))
      .join("/");
  } catch {
    throw new EdgeError(
      "invalid_artifact_key",
      400,
      "The artifact key is invalid."
    );
  }
  try {
    return validateArtifactKey(decoded);
  } catch {
    throw new EdgeError(
      "invalid_artifact_key",
      400,
      "The artifact key is invalid."
    );
  }
}

async function handleArtifactGet(
  environment: Env,
  pathname: string
): Promise<Response> {
  const key = decodeArtifactKey(pathname);
  const object = await environment.ARTIFACTS.get(key);
  if (object === null || object.body === undefined) {
    return jsonResponse({ error: "artifact_not_found" }, 404);
  }
  const originalMediaType =
    object.httpMetadata?.contentType ?? "application/octet-stream";
  const headers = new Headers({
    "cache-control": "no-store, no-transform",
    "content-type": "application/octet-stream",
    "content-disposition": "attachment; filename=artifact.bin",
    "content-length": String(object.size),
    etag: object.httpEtag,
    "x-content-type-options": "nosniff",
    "x-ordivon-media-type": originalMediaType,
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'"
  });
  const sha256 = object.customMetadata?.sha256;
  if (sha256 !== undefined) {
    headers.set("x-ordivon-sha256", sha256);
  }
  return new Response(object.body, { headers });
}

export async function handleRequest(
  request: Request,
  environment: Env,
  dependencies: HandlerDependencies = {}
): Promise<Response> {
  try {
    const body = await readBodyLimited(request, REQUEST_POLICY.max_body_bytes);
    const auth = await verifySignedRequest(request, body, environment);
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      if (request.method !== "GET") return methodNotAllowed("GET");
      return jsonResponse({
        schema_version: EDGE_SCHEMA_VERSION,
        service: "ordivon-edge",
        status: "ok",
        policy_version: await effectivePolicyVersion(environment),
        worker_version: environment.CF_VERSION_METADATA,
        deployment_identity: workerDeploymentIdentity(
          environment.CF_VERSION_METADATA
        )
      });
    }

    if (url.pathname === "/v1/capabilities") {
      if (request.method !== "GET") return methodNotAllowed("GET");
      return jsonResponse({
        ...capabilitiesDocument(await effectivePolicyVersion(environment)),
        worker_version: environment.CF_VERSION_METADATA,
        deployment_identity: workerDeploymentIdentity(
          environment.CF_VERSION_METADATA
        )
      });
    }

    if (url.pathname === "/v1/fetch") {
      if (request.method !== "POST") return methodNotAllowed("POST");
      return await runOperation("fetch", environment, body, auth, dependencies);
    }

    if (url.pathname === "/v1/browser/run") {
      if (request.method !== "POST") return methodNotAllowed("POST");
      return await runOperation("browser.run", environment, body, auth, dependencies);
    }

    if (url.pathname.startsWith(RECEIPT_PREFIX)) {
      if (request.method !== "GET") return methodNotAllowed("GET");
      return await handleReceiptGet(
        environment,
        url.pathname.slice(RECEIPT_PREFIX.length)
      );
    }

    if (url.pathname.startsWith(ARTIFACT_PREFIX)) {
      if (request.method !== "GET") return methodNotAllowed("GET");
      return await handleArtifactGet(environment, url.pathname);
    }

    return jsonResponse({ error: "not_found" }, 404);
  } catch (error) {
    return errorResponse(asEdgeError(error));
  }
}

export default {
  fetch(request: Request, environment: Env): Promise<Response> {
    return handleRequest(request, environment);
  }
} satisfies ExportedHandler<Env>;
