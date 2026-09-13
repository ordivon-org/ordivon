import { RETENTION_POLICY } from "./policy.js";
import { CAPABILITY_VERSIONS } from "./version.js";

export const EDGE_SCHEMA_VERSION = 1 as const;
export const REQUEST_STATE_SCHEMA_VERSION = 2 as const;

export type EdgeOperation = "fetch" | "browser.run";

export type ReceiptStatus = "succeeded" | "failed" | "rejected";

export interface EdgeCapability {
  readonly id: EdgeOperation | "artifact.get" | "receipt";
  readonly version: string;
  readonly state: "ready";
  readonly reason: string;
}

export interface EdgeRetentionPolicy {
  readonly idempotency_days: number;
  readonly request_state_days: number;
  readonly receipt_mirror_days: number;
  readonly artifact_days: number;
  readonly cleanup_task_days: number;
}

export interface EdgeCapabilitiesDocument {
  readonly schema_version: typeof EDGE_SCHEMA_VERSION;
  readonly service: "ordivon-edge";
  readonly policy_version: string;
  readonly retention: EdgeRetentionPolicy;
  readonly capabilities: readonly EdgeCapability[];
}

export interface EdgeExecutionMetadata {
  readonly policy_version: string;
  readonly capability_version: string;
  readonly worker_version_id: string;
  readonly worker_version_tag: string;
  readonly worker_version_timestamp: string;
  readonly lease_generation: number;
}

export interface ArtifactReference {
  readonly key: string;
  readonly sha256: string;
  readonly bytes: number;
  readonly media_type: string;
  readonly etag?: string;
}

export interface FetchReceiptDetails {
  readonly requested_url: string;
  readonly final_url: string;
  readonly http_status: number;
  readonly redirect_count: number;
}

export interface BrowserReceiptDetails {
  readonly requested_url: string;
  readonly final_url_observed: boolean;
  readonly final_url?: string;
  readonly page_title: string;
  readonly page_status: number;
  readonly browser_ms: number;
  readonly viewport: {
    readonly width: number;
    readonly height: number;
  };
  readonly full_page: boolean;
}

export interface EdgeReceipt {
  readonly schema_version: typeof EDGE_SCHEMA_VERSION;
  readonly receipt_id: string;
  readonly request_digest: string;
  readonly operation: EdgeOperation;
  readonly status: ReceiptStatus;
  readonly started_at: string;
  readonly completed_at: string;
  readonly duration_ms: number;
  readonly execution: EdgeExecutionMetadata;
  readonly artifact?: ArtifactReference;
  readonly artifacts?: readonly ArtifactReference[];
  readonly fetch?: FetchReceiptDetails;
  readonly browser?: BrowserReceiptDetails;
  readonly error_code?: string;
}

export interface EdgePendingReceipt {
  readonly schema_version: typeof EDGE_SCHEMA_VERSION;
  readonly receipt_id: string;
  readonly request_digest: string;
  readonly operation: EdgeOperation;
  readonly status: "pending";
  readonly started_at: string;
  readonly lease_expires_at: string;
  readonly execution: EdgeExecutionMetadata;
}

export type EdgeReceiptRecord = EdgeReceipt | EdgePendingReceipt;

export interface EdgeReceiptEnvelope {
  readonly receipt: EdgeReceipt;
  readonly replayed: boolean;
}

export function capabilitiesDocument(
  policyVersion: string
): EdgeCapabilitiesDocument {
  return {
    schema_version: EDGE_SCHEMA_VERSION,
    service: "ordivon-edge",
    policy_version: policyVersion,
    retention: {
      idempotency_days: RETENTION_POLICY.idempotency,
      request_state_days: RETENTION_POLICY.request_state,
      receipt_mirror_days: RETENTION_POLICY.receipt_mirror,
      artifact_days: RETENTION_POLICY.artifacts,
      cleanup_task_days: RETENTION_POLICY.cleanup_tasks
    },
    capabilities: [
      {
        id: "artifact.get",
        version: CAPABILITY_VERSIONS["artifact.get"],
        state: "ready",
        reason: "Authenticated clients can retrieve validated private artifact keys."
      },
      {
        id: "fetch",
        version: CAPABILITY_VERSIONS.fetch,
        state: "ready",
        reason: "Signed requests can execute allowlisted, bounded HTTPS fetches with transactional receipts."
      },
      {
        id: "browser.run",
        version: CAPABILITY_VERSIONS["browser.run"],
        state: "ready",
        reason: "Signed requests can capture allowlisted same-origin browser snapshots with transactional artifacts."
      },
      {
        id: "receipt",
        version: "receipt.v2",
        state: "ready",
        reason: "Pending state, fenced leases, committed receipts, replay, and conflict detection are implemented."
      }
    ]
  };
}
