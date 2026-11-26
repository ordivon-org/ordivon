import type { AuthContext } from "./auth.js";
import { parseJsonObject } from "./body.js";
import { validateBrowserRunRequest } from "./browser-policy.js";
import {
  executeBrowserRun,
  type BrowserExecutionEnvironment,
  type BrowserSnapshotRunner
} from "./browser-run.js";
import type { EdgeOperation, EdgeReceipt, EdgeReceiptEnvelope } from "./contracts.js";
import { asEdgeError, EdgeError } from "./errors.js";
import type { ExecutionLease } from "./execution.js";
import {
  executeExternalFetch,
  type ExternalFetcher,
  type FetchExecutionEnvironment
} from "./external-fetch.js";
import { validateFetchRequest } from "./fetch-policy.js";
import { beginRequest, commitReceipt } from "./idempotency.js";
import { jsonResponse } from "./http.js";
import { consoleLogWriter, emitOperationLog, type EdgeLogWriter } from "./observability.js";
import { effectivePolicyVersion } from "./policy.js";
import { createReceipt } from "./receipts.js";

export interface OperationEnvironment
  extends FetchExecutionEnvironment, BrowserExecutionEnvironment {
  readonly ARTIFACTS: R2Bucket;
  readonly BROWSER: BrowserRun;
  readonly FETCH_RATE_LIMIT: RateLimit;
  readonly BROWSER_RATE_LIMIT: RateLimit;
  readonly CF_VERSION_METADATA: WorkerVersionMetadata;
}

export interface OperationDependencies {
  readonly fetcher?: ExternalFetcher;
  readonly browserRunner?: BrowserSnapshotRunner;
  readonly now?: () => Date;
  readonly tokenFactory?: () => string;
  readonly logWriter?: EdgeLogWriter;
  readonly rateLimit?: (operation: EdgeOperation, key: string) => Promise<boolean>;
}

type OperationResult =
  | ({ readonly operation: "fetch" } & Awaited<ReturnType<typeof executeExternalFetch>>)
  | ({ readonly operation: "browser.run" } & Awaited<ReturnType<typeof executeBrowserRun>>);

function nowFrom(dependencies: OperationDependencies): Date {
  return dependencies.now?.() ?? new Date();
}

function logWriterFrom(dependencies: OperationDependencies): EdgeLogWriter {
  return dependencies.logWriter ?? consoleLogWriter;
}

function envelopeResponse(
  envelope: EdgeReceiptEnvelope,
  status = 200,
  retryAfterSeconds?: number
): Response {
  const response = jsonResponse(envelope, status);
  response.headers.set("x-ordivon-replayed", String(envelope.replayed));
  response.headers.set(
    "x-ordivon-worker-version",
    envelope.receipt.execution.worker_version_id
  );
  if (retryAfterSeconds !== undefined) {
    response.headers.set("retry-after", String(retryAfterSeconds));
  }
  return response;
}

async function enforceRateLimit(
  environment: OperationEnvironment,
  operation: EdgeOperation,
  keyId: string,
  dependencies: OperationDependencies
): Promise<void> {
  let allowed: boolean;
  try {
    if (dependencies.rateLimit !== undefined) {
      allowed = await dependencies.rateLimit(operation, keyId);
    } else {
      const limiter =
        operation === "browser.run"
          ? environment.BROWSER_RATE_LIMIT
          : environment.FETCH_RATE_LIMIT;
      allowed = (await limiter.limit({ key: keyId })).success;
    }
  } catch {
    throw new EdgeError(
      "rate_limit_unavailable",
      503,
      "The execution budget could not be checked.",
      "failed",
      10
    );
  }
  if (!allowed) {
    const browser = operation === "browser.run";
    throw new EdgeError(
      browser ? "browser_rate_limited" : "fetch_rate_limited",
      429,
      browser
        ? "Browser Run is rate limited."
        : "External Fetch is rate limited.",
      "failed",
      browser ? 10 : 60
    );
  }
}

async function persistReceipt(
  environment: OperationEnvironment,
  lease: ExecutionLease,
  receipt: EdgeReceipt,
  artifactKeys: readonly string[],
  dependencies: OperationDependencies
): Promise<EdgeReceipt> {
  const writer = logWriterFrom(dependencies);
  try {
    const committed = await commitReceipt({
      bucket: environment.ARTIFACTS,
      lease,
      receipt,
      artifactKeys,
      onMirrorFailure(error) {
        emitOperationLog(writer, {
          event: "receipt_mirror_failed",
          operation: lease.operation,
          requestId: lease.request_id,
          lease,
          status: receipt.status,
          errorCode: error instanceof Error ? error.name : "unknown"
        });
      }
    });
    emitOperationLog(writer, {
      event: "operation_completed",
      operation: lease.operation,
      requestId: lease.request_id,
      lease,
      receipt: committed
    });
    return committed;
  } catch (error) {
    const edgeError = asEdgeError(error);
    emitOperationLog(writer, {
      event: "operation_commit_lost",
      operation: lease.operation,
      requestId: lease.request_id,
      lease,
      status: edgeError.receiptStatus,
      errorCode: edgeError.code
    });
    throw edgeError;
  }
}

async function beginOperation(
  environment: OperationEnvironment,
  requestId: string,
  requestDigest: string,
  operation: EdgeOperation,
  dependencies: OperationDependencies
): Promise<
  | { readonly kind: "replayed"; readonly response: Response }
  | { readonly kind: "acquired"; readonly lease: ExecutionLease }
> {
  const begin = await beginRequest({
    bucket: environment.ARTIFACTS,
    requestId,
    requestDigest,
    operation,
    policyVersion: await effectivePolicyVersion(environment),
    workerVersion: environment.CF_VERSION_METADATA,
    now: nowFrom(dependencies),
    ...(dependencies.tokenFactory === undefined
      ? {}
      : { tokenFactory: dependencies.tokenFactory })
  });
  const writer = logWriterFrom(dependencies);
  if (begin.kind === "replayed") {
    emitOperationLog(writer, {
      event: "operation_replayed",
      operation,
      requestId,
      receipt: begin.receipt,
      replayed: true
    });
    return {
      kind: "replayed",
      response: envelopeResponse({ receipt: begin.receipt, replayed: true })
    };
  }
  emitOperationLog(writer, {
    event: "operation_acquired",
    operation,
    requestId,
    lease: begin.lease,
    status: "pending"
  });
  return { kind: "acquired", lease: begin.lease };
}

async function executeOperation(
  operation: EdgeOperation,
  environment: OperationEnvironment,
  lease: ExecutionLease,
  body: Uint8Array,
  dependencies: OperationDependencies
): Promise<OperationResult> {
  switch (operation) {
    case "fetch": {
      const input = validateFetchRequest(parseJsonObject(body), environment);
      const result = await executeExternalFetch(environment, lease, input, dependencies.fetcher);
      return { operation, ...result };
    }
    case "browser.run": {
      const input = validateBrowserRunRequest(parseJsonObject(body), environment);
      const result = await executeBrowserRun(
        environment,
        dependencies.browserRunner ?? environment.BROWSER,
        lease,
        input
      );
      return { operation, ...result };
    }
  }
}

/** Run an already authenticated operation. The commit boundary is deliberately
 * outside the execution catch: uncertain or lost commits are not execution failures. */
export async function runOperation(
  operation: EdgeOperation,
  environment: OperationEnvironment,
  body: Uint8Array,
  auth: Pick<AuthContext, "requestId" | "requestDigest" | "keyId">,
  dependencies: OperationDependencies
): Promise<Response> {
  const { requestId, requestDigest, keyId } = auth;
  const begin = await beginOperation(environment, requestId, requestDigest, operation, dependencies);
  if (begin.kind === "replayed") return begin.response;

  const lease = begin.lease;
  const startedAt = new Date(lease.acquired_at);
  let result: OperationResult;
  try {
    await enforceRateLimit(environment, operation, keyId, dependencies);
    result = await executeOperation(operation, environment, lease, body, dependencies);
  } catch (error) {
    const edgeError = asEdgeError(error);
    const receipt = createReceipt({
      operation,
      status: edgeError.receiptStatus,
      requestDigest,
      receiptId: requestId,
      startedAt,
      completedAt: nowFrom(dependencies),
      execution: lease,
      errorCode: edgeError.code
    });
    const committed = await persistReceipt(environment, lease, receipt, [], dependencies);
    return envelopeResponse(
      { receipt: committed, replayed: false },
      edgeError.httpStatus,
      edgeError.retryAfterSeconds
    );
  }

  const receipt = createReceipt({
    ...result,
    status: "succeeded",
    requestDigest,
    receiptId: requestId,
    startedAt,
    completedAt: nowFrom(dependencies),
    execution: lease
  });
  const committed = await persistReceipt(
    environment,
    lease,
    receipt,
    result.artifacts.map((artifact) => artifact.key),
    dependencies
  );
  return envelopeResponse({ receipt: committed, replayed: false });
}
