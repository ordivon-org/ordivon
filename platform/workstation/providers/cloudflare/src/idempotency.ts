import {
  EDGE_SCHEMA_VERSION,
  REQUEST_STATE_SCHEMA_VERSION,
  type EdgeExecutionMetadata,
  type EdgeOperation,
  type EdgePendingReceipt,
  type EdgeReceipt,
  type EdgeReceiptRecord
} from "./contracts.js";
import { cleanupArtifacts } from "./cleanup.js";
import { EdgeError } from "./errors.js";
import {
  executionMetadata,
  leaseDurationMilliseconds,
  type ExecutionLease
} from "./execution.js";
import { CAPABILITY_VERSIONS } from "./version.js";

interface PendingRequestState {
  readonly schema_version: typeof REQUEST_STATE_SCHEMA_VERSION;
  readonly state: "pending";
  readonly request_id: string;
  readonly request_digest: string;
  readonly operation: EdgeOperation;
  readonly execution: EdgeExecutionMetadata;
  readonly lease_token: string;
  readonly acquired_at: string;
  readonly lease_expires_at: string;
}

interface CommittedRequestState {
  readonly schema_version: typeof REQUEST_STATE_SCHEMA_VERSION;
  readonly state: "committed";
  readonly request_id: string;
  readonly request_digest: string;
  readonly operation: EdgeOperation;
  readonly execution: EdgeExecutionMetadata;
  readonly committed_at: string;
  readonly receipt: EdgeReceipt;
}

type RequestState = PendingRequestState | CommittedRequestState;

interface LegacyRequestLock {
  readonly request_digest?: string;
}

export interface BeginRequestOptions {
  readonly bucket: R2Bucket;
  readonly requestId: string;
  readonly requestDigest: string;
  readonly operation: EdgeOperation;
  readonly policyVersion: string;
  readonly workerVersion: WorkerVersionMetadata;
  readonly now?: Date;
  readonly tokenFactory?: () => string;
}

export type BeginRequestResult =
  | { readonly kind: "acquired"; readonly lease: ExecutionLease }
  | { readonly kind: "replayed"; readonly receipt: EdgeReceipt };

export interface CommitReceiptOptions {
  readonly bucket: R2Bucket;
  readonly lease: ExecutionLease;
  readonly receipt: EdgeReceipt;
  readonly artifactKeys?: readonly string[];
  readonly onMirrorFailure?: (error: unknown) => void;
}

export function requestStateKey(requestId: string): string {
  return `requests/v2/${requestId}.json`;
}

export function receiptMirrorKey(requestId: string): string {
  return `receipts/v2/${requestId}.json`;
}

function legacyRequestKey(requestId: string): string {
  return `requests/v1/${requestId}.json`;
}

function legacyReceiptKey(requestId: string): string {
  return `receipts/v1/${requestId}.json`;
}

async function readJson<T>(object: R2ObjectBody): Promise<T> {
  try {
    return JSON.parse(await object.text()) as T;
  } catch {
    throw new EdgeError(
      "execution_state_corrupt",
      500,
      "The stored execution state is invalid.",
      "failed"
    );
  }
}

async function loadRequestState(
  bucket: R2Bucket,
  requestId: string
): Promise<{ readonly object: R2ObjectBody; readonly state: RequestState } | null> {
  const object = await bucket.get(requestStateKey(requestId));
  if (object === null) return null;
  const state = await readJson<RequestState>(object);
  if (
    state.schema_version !== REQUEST_STATE_SCHEMA_VERSION ||
    state.request_id !== requestId ||
    (state.state !== "pending" && state.state !== "committed")
  ) {
    throw new EdgeError(
      "execution_state_corrupt",
      500,
      "The stored execution state is invalid.",
      "failed"
    );
  }
  return { object, state };
}

function normalizeLegacyReceipt(receipt: EdgeReceipt): EdgeReceipt {
  if (receipt.execution !== undefined) return receipt;
  return {
    ...receipt,
    execution: {
      policy_version: "legacy.p1",
      capability_version: `legacy.${receipt.operation}`,
      worker_version_id: "legacy",
      worker_version_tag: "legacy",
      worker_version_timestamp: receipt.completed_at,
      lease_generation: 1
    }
  };
}

async function loadLegacyReceipt(
  bucket: R2Bucket,
  requestId: string
): Promise<EdgeReceipt | null> {
  const object = await bucket.get(legacyReceiptKey(requestId));
  if (object === null) return null;
  return normalizeLegacyReceipt(await readJson<EdgeReceipt>(object));
}

function assertSameIntent(
  existingDigest: string,
  existingOperation: EdgeOperation,
  requestDigest: string,
  operation: EdgeOperation
): void {
  if (existingDigest !== requestDigest || existingOperation !== operation) {
    throw new EdgeError(
      "idempotency_conflict",
      409,
      "The request ID is already bound to different request content."
    );
  }
}

function pendingReceipt(state: PendingRequestState): EdgePendingReceipt {
  return {
    schema_version: EDGE_SCHEMA_VERSION,
    receipt_id: state.request_id,
    request_digest: state.request_digest,
    operation: state.operation,
    status: "pending",
    started_at: state.acquired_at,
    lease_expires_at: state.lease_expires_at,
    execution: state.execution
  };
}

function leaseFrom(
  state: PendingRequestState,
  stateEtag: string
): ExecutionLease {
  return {
    ...state.execution,
    request_id: state.request_id,
    request_digest: state.request_digest,
    operation: state.operation,
    lease_token: state.lease_token,
    acquired_at: state.acquired_at,
    lease_expires_at: state.lease_expires_at,
    state_etag: stateEtag
  };
}

function createPendingState(
  options: BeginRequestOptions,
  generation: number,
  now: Date
): PendingRequestState {
  return {
    schema_version: REQUEST_STATE_SCHEMA_VERSION,
    state: "pending",
    request_id: options.requestId,
    request_digest: options.requestDigest,
    operation: options.operation,
    execution: executionMetadata(
      options.operation,
      options.policyVersion,
      options.workerVersion,
      generation
    ),
    lease_token: options.tokenFactory?.() ?? crypto.randomUUID(),
    acquired_at: now.toISOString(),
    lease_expires_at: new Date(
      now.getTime() + leaseDurationMilliseconds(options.operation)
    ).toISOString()
  };
}

async function writePendingState(
  bucket: R2Bucket,
  state: PendingRequestState,
  onlyIf: R2Conditional
): Promise<R2Object | null> {
  return bucket.put(requestStateKey(state.request_id), JSON.stringify(state), {
    onlyIf,
    httpMetadata: { contentType: "application/json; charset=utf-8" },
    customMetadata: {
      request_digest: state.request_digest,
      operation: state.operation,
      state: state.state,
      policy_version: state.execution.policy_version,
      capability_version: state.execution.capability_version,
      lease_generation: String(state.execution.lease_generation)
    }
  });
}

async function checkLegacyState(options: BeginRequestOptions): Promise<EdgeReceipt | null> {
  const receipt = await loadLegacyReceipt(options.bucket, options.requestId);
  if (receipt !== null) {
    assertSameIntent(
      receipt.request_digest,
      receipt.operation,
      options.requestDigest,
      options.operation
    );
    return receipt;
  }
  const legacyLock = await options.bucket.get(legacyRequestKey(options.requestId));
  if (legacyLock === null) return null;
  const lock = await readJson<LegacyRequestLock>(legacyLock);
  if (lock.request_digest !== options.requestDigest) {
    throw new EdgeError(
      "idempotency_conflict",
      409,
      "The request ID is already bound to different legacy request content."
    );
  }
  throw new EdgeError(
    "legacy_request_unresolved",
    409,
    "The request ID belongs to an unfinished legacy execution; use a new request ID."
  );
}

export async function beginRequest(
  options: BeginRequestOptions,
  attempt = 0
): Promise<BeginRequestResult> {
  if (attempt > 3) {
    throw new EdgeError(
      "request_contention",
      409,
      "The request state changed concurrently; retry with the same request ID."
    );
  }
  const now = options.now ?? new Date();
  const existing = await loadRequestState(options.bucket, options.requestId);
  if (existing !== null) {
    assertSameIntent(
      existing.state.request_digest,
      existing.state.operation,
      options.requestDigest,
      options.operation
    );
    if (existing.state.state === "committed") {
      return { kind: "replayed", receipt: existing.state.receipt };
    }

    const expiresAt = Date.parse(existing.state.lease_expires_at);
    if (!Number.isFinite(expiresAt)) {
      throw new EdgeError(
        "execution_state_corrupt",
        500,
        "The stored execution lease is invalid.",
        "failed"
      );
    }
    if (now.getTime() < expiresAt) {
      throw new EdgeError(
        "request_in_progress",
        409,
        "The request is already in progress."
      );
    }
    if (
      existing.state.execution.policy_version !== options.policyVersion ||
      existing.state.execution.capability_version !==
        CAPABILITY_VERSIONS[options.operation]
    ) {
      throw new EdgeError(
        "request_policy_changed",
        409,
        "The expired request belongs to an older execution policy; use a new request ID."
      );
    }

    const replacement = createPendingState(
      options,
      existing.state.execution.lease_generation + 1,
      now
    );
    const replaced = await writePendingState(options.bucket, replacement, {
      etagMatches: existing.object.etag
    });
    if (replaced === null) {
      return beginRequest(options, attempt + 1);
    }
    return { kind: "acquired", lease: leaseFrom(replacement, replaced.etag) };
  }

  const legacyReceipt = await checkLegacyState(options);
  if (legacyReceipt !== null) {
    return { kind: "replayed", receipt: legacyReceipt };
  }

  const createdState = createPendingState(options, 1, now);
  const created = await writePendingState(options.bucket, createdState, {
    etagDoesNotMatch: "*"
  });
  if (created === null) {
    return beginRequest(options, attempt + 1);
  }
  return { kind: "acquired", lease: leaseFrom(createdState, created.etag) };
}

export async function loadReceiptRecord(
  bucket: R2Bucket,
  requestId: string
): Promise<EdgeReceiptRecord | null> {
  const state = await loadRequestState(bucket, requestId);
  if (state !== null) {
    return state.state.state === "committed"
      ? state.state.receipt
      : pendingReceipt(state.state);
  }
  return loadLegacyReceipt(bucket, requestId);
}

function receiptMatchesLease(
  receipt: EdgeReceipt,
  lease: ExecutionLease
): boolean {
  return (
    receipt.receipt_id === lease.request_id &&
    receipt.request_digest === lease.request_digest &&
    receipt.operation === lease.operation &&
    receipt.execution.policy_version === lease.policy_version &&
    receipt.execution.capability_version === lease.capability_version &&
    receipt.execution.lease_generation === lease.lease_generation
  );
}

async function mirrorReceipt(
  bucket: R2Bucket,
  receipt: EdgeReceipt,
  onMirrorFailure?: (error: unknown) => void
): Promise<void> {
  try {
    await bucket.put(receiptMirrorKey(receipt.receipt_id), JSON.stringify(receipt), {
      httpMetadata: { contentType: "application/json; charset=utf-8" },
      customMetadata: {
        request_digest: receipt.request_digest,
        operation: receipt.operation,
        status: receipt.status,
        policy_version: receipt.execution.policy_version,
        capability_version: receipt.execution.capability_version,
        lease_generation: String(receipt.execution.lease_generation)
      }
    });
  } catch (error) {
    onMirrorFailure?.(error);
  }
}

export async function commitReceipt(
  options: CommitReceiptOptions
): Promise<EdgeReceipt> {
  if (!receiptMatchesLease(options.receipt, options.lease)) {
    await cleanupArtifacts(
      options.bucket,
      options.lease,
      options.artifactKeys ?? [],
      "receipt_lease_mismatch"
    );
    throw new EdgeError(
      "receipt_lease_mismatch",
      500,
      "The receipt does not match its execution lease.",
      "failed"
    );
  }

  const committedState: CommittedRequestState = {
    schema_version: REQUEST_STATE_SCHEMA_VERSION,
    state: "committed",
    request_id: options.lease.request_id,
    request_digest: options.lease.request_digest,
    operation: options.lease.operation,
    execution: options.receipt.execution,
    committed_at: options.receipt.completed_at,
    receipt: options.receipt
  };

  let committed: R2Object | null;
  try {
    committed = await options.bucket.put(
      requestStateKey(options.lease.request_id),
      JSON.stringify(committedState),
      {
        onlyIf: { etagMatches: options.lease.state_etag },
        httpMetadata: { contentType: "application/json; charset=utf-8" },
        customMetadata: {
          request_digest: options.lease.request_digest,
          operation: options.lease.operation,
          state: committedState.state,
          status: options.receipt.status,
          policy_version: options.receipt.execution.policy_version,
          capability_version: options.receipt.execution.capability_version,
          lease_generation: String(options.receipt.execution.lease_generation)
        }
      }
    );
  } catch (error) {
    const current = await loadRequestState(
      options.bucket,
      options.lease.request_id
    ).catch(() => null);
    if (
      current?.state.state === "committed" &&
      receiptMatchesLease(current.state.receipt, options.lease)
    ) {
      await mirrorReceipt(
        options.bucket,
        current.state.receipt,
        options.onMirrorFailure
      );
      return current.state.receipt;
    }
    await cleanupArtifacts(
      options.bucket,
      options.lease,
      options.artifactKeys ?? [],
      "receipt_commit_unavailable"
    );
    throw new EdgeError(
      "receipt_commit_unavailable",
      503,
      "The execution result could not be committed.",
      "failed"
    );
  }

  if (committed === null) {
    await cleanupArtifacts(
      options.bucket,
      options.lease,
      options.artifactKeys ?? [],
      "execution_lease_lost"
    );
    throw new EdgeError(
      "execution_lease_lost",
      409,
      "The execution lease was replaced before the result could be committed."
    );
  }

  await mirrorReceipt(
    options.bucket,
    options.receipt,
    options.onMirrorFailure
  );
  return options.receipt;
}
