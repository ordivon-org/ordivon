import type {
  EdgeOperation,
  EdgeReceipt,
  ReceiptStatus
} from "./contracts.js";
import type { ExecutionLease } from "./execution.js";

export type EdgeLogWriter = (entry: Readonly<Record<string, unknown>>) => void;

export interface OperationLogOptions {
  readonly event:
    | "operation_acquired"
    | "operation_replayed"
    | "operation_completed"
    | "operation_commit_lost"
    | "receipt_mirror_failed";
  readonly operation: EdgeOperation;
  readonly requestId: string;
  readonly lease?: ExecutionLease;
  readonly receipt?: EdgeReceipt;
  readonly status?: ReceiptStatus | "pending";
  readonly replayed?: boolean;
  readonly errorCode?: string;
  readonly artifactBytes?: number;
  readonly browserMs?: number;
}

export function consoleLogWriter(entry: Readonly<Record<string, unknown>>): void {
  console.log(JSON.stringify(entry));
}

export function emitOperationLog(
  writer: EdgeLogWriter,
  options: OperationLogOptions
): void {
  writer({
    event: options.event,
    service: "ordivon-edge",
    request_id: options.requestId,
    operation: options.operation,
    status: options.receipt?.status ?? options.status,
    replayed: options.replayed ?? false,
    error_code: options.receipt?.error_code ?? options.errorCode,
    duration_ms: options.receipt?.duration_ms,
    artifact_bytes:
      options.artifactBytes ??
      options.receipt?.artifacts?.reduce((total, artifact) => total + artifact.bytes, 0) ??
      options.receipt?.artifact?.bytes,
    browser_ms: options.browserMs ?? options.receipt?.browser?.browser_ms,
    policy_version:
      options.receipt?.execution.policy_version ?? options.lease?.policy_version,
    capability_version:
      options.receipt?.execution.capability_version ?? options.lease?.capability_version,
    worker_version_id:
      options.receipt?.execution.worker_version_id ?? options.lease?.worker_version_id,
    worker_version_tag:
      options.receipt?.execution.worker_version_tag ?? options.lease?.worker_version_tag,
    lease_generation:
      options.receipt?.execution.lease_generation ?? options.lease?.lease_generation
  });
}
