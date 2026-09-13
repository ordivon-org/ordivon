import type { ExecutionLease } from "./execution.js";

export const CLEANUP_TASK_SCHEMA_VERSION = 1 as const;

export interface CleanupTask {
  readonly schema_version: typeof CLEANUP_TASK_SCHEMA_VERSION;
  readonly request_id: string;
  readonly operation: ExecutionLease["operation"];
  readonly lease_generation: number;
  readonly artifact_keys: readonly string[];
  readonly reason: string;
  readonly created_at: string;
}

export function cleanupTaskKey(lease: ExecutionLease): string {
  return `cleanup/v2/${lease.request_id}/g${lease.lease_generation}.json`;
}

export async function cleanupArtifacts(
  bucket: R2Bucket,
  lease: ExecutionLease,
  artifactKeys: readonly string[],
  reason: string,
  now = new Date()
): Promise<void> {
  const keys = [...new Set(artifactKeys)];
  if (keys.length === 0) return;

  try {
    await bucket.delete(keys);
    return;
  } catch (error) {
    const task: CleanupTask = {
      schema_version: CLEANUP_TASK_SCHEMA_VERSION,
      request_id: lease.request_id,
      operation: lease.operation,
      lease_generation: lease.lease_generation,
      artifact_keys: keys,
      reason,
      created_at: now.toISOString()
    };
    try {
      await bucket.put(cleanupTaskKey(lease), JSON.stringify(task), {
        httpMetadata: { contentType: "application/json; charset=utf-8" },
        customMetadata: {
          request_id: lease.request_id,
          operation: lease.operation,
          lease_generation: String(lease.lease_generation),
          artifact_count: String(keys.length),
          reason
        }
      });
      console.error(
        JSON.stringify({
          event: "artifact_cleanup_deferred",
          service: "ordivon-edge",
          request_id: lease.request_id,
          operation: lease.operation,
          lease_generation: lease.lease_generation,
          artifact_count: keys.length,
          reason,
          error: error instanceof Error ? error.name : "unknown"
        })
      );
    } catch (scheduleError) {
      console.error(
        JSON.stringify({
          event: "artifact_cleanup_schedule_failed",
          service: "ordivon-edge",
          request_id: lease.request_id,
          operation: lease.operation,
          lease_generation: lease.lease_generation,
          artifact_count: keys.length,
          reason,
          cleanup_error: error instanceof Error ? error.name : "unknown",
          schedule_error:
            scheduleError instanceof Error ? scheduleError.name : "unknown"
        })
      );
    }
  }
}
