/** Native SQLite write boundary. Business identity, replay and policy remain with the caller. */
import type { DatabaseSync } from "node:sqlite";
import { WebProblem } from "./errors.ts";
import { quarantineOwnerConnection, requireUsableOwnerConnection } from "./store-connection-health.ts";

// SQLite primary result code SQLITE_BUSY (5); extended BUSY results share
// that low byte. Never classify a message string or a later COMMIT failure.
function isNativeBusy(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const native = error as Error & { code?: unknown; errcode?: unknown };
  return native.code === "ERR_SQLITE_ERROR" &&
    typeof native.errcode === "number" && Number.isSafeInteger(native.errcode) &&
    native.errcode >= 0 && (native.errcode & 0xff) === 5;
}

export type OwnerTransactionKind = "effect" | "challenge" | "dpop" | "note";

export function requireIdleOwnerConnection(db: DatabaseSync, kind: OwnerTransactionKind): void {
  requireUsableOwnerConnection(db);
  if (db.isTransaction) {
    throw new WebProblem(500, kind + "-transaction-active",
      kind === "effect" ? "Effect transaction unavailable" : "Owner transaction unavailable",
      kind === "effect" ? "The local Effect coordinator requires an idle owner connection."
        : "The local transaction requires an idle owner connection.");
  }
}

export function runOwnerTransaction<T>(db: DatabaseSync, kind: OwnerTransactionKind, write: () => T): T {
  requireIdleOwnerConnection(db, kind);
  let began = false;
  try {
    db.exec("BEGIN IMMEDIATE");
    began = true;
    const result = write();
    db.exec("COMMIT");
    return result;
  } catch (error) {
    // Classify only a native BUSY before acquisition. No synchronous retry or
    // wait; another writer may have committed the identity independently.
    if (!began && !db.isTransaction && isNativeBusy(error)) {
      throw new WebProblem(503, kind + "-writer-busy",
        kind === "effect" ? "Effect writer busy" : "Owner writer busy",
        kind === "effect" ? "The local writer transaction was not acquired. Observe the same Effect identity before an explicit new attempt."
          : "The local writer transaction was not acquired. Do not automatically retry an ambiguous operation.");
    }
    // A failed acknowledgement is not evidence that COMMIT did not occur.
    // Only roll back a transaction that is still active; never auto-reissue.
    if (db.isTransaction) {
      try {
        db.exec("ROLLBACK");
      } catch (rollbackError) {
        // Mark before close: close itself may fail while the transaction is live.
        quarantineOwnerConnection(db);
        const failures = [error, rollbackError];
        try {
          db.close();
        } catch (closeError) {
          failures.push(closeError);
        }
        throw new AggregateError(failures, (kind === "effect" ? "Effect" : "Owner") +
          " transaction and rollback failed; owner connection recovery required");
      }
    }
    throw error;
  }
}
