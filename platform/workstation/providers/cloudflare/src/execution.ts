import type {
  EdgeExecutionMetadata,
  EdgeOperation
} from "./contracts.js";
import { LEASE_POLICY } from "./policy.js";
import { CAPABILITY_VERSIONS } from "./version.js";

export interface ExecutionLease extends EdgeExecutionMetadata {
  readonly request_id: string;
  readonly request_digest: string;
  readonly operation: EdgeOperation;
  readonly lease_token: string;
  readonly acquired_at: string;
  readonly lease_expires_at: string;
  readonly state_etag: string;
}

export function executionMetadata(
  operation: EdgeOperation,
  policyVersion: string,
  workerVersion: WorkerVersionMetadata,
  leaseGeneration: number
): EdgeExecutionMetadata {
  return {
    policy_version: policyVersion,
    capability_version: CAPABILITY_VERSIONS[operation],
    worker_version_id: workerVersion.id,
    worker_version_tag: workerVersion.tag,
    worker_version_timestamp: workerVersion.timestamp,
    lease_generation: leaseGeneration
  };
}

export function leaseDurationMilliseconds(operation: EdgeOperation): number {
  return LEASE_POLICY[operation];
}
