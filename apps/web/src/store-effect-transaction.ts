/** Native SQLite write boundary. Business identity, replay and policy remain with the caller. */
import type { DatabaseSync } from "node:sqlite";
import { WebProblem } from "./errors.ts";

// SQLite primary result code SQLITE_BUSY (5); extended BUSY results share
// that low byte. Never classify a message string or a later COMMIT failure.
function isNativeBusy(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const native = error as Error & { code?: unknown; errcode?: unknown };
  return native.code === "ERR_SQLITE_ERROR" &&
    typeof native.errcode === "number" && Number.isSafeInteger(native.errcode) &&
    native.errcode >= 0 && (native.errcode & 0xff) === 5;
}

export function requireIdleEffectConnection(db: DatabaseSync): void {
  if (db.isTransaction) {
    throw new WebProblem(500, "effect-transaction-active", "Effect transaction unavailable",
      "The local Effect coordinator requires an idle owner connection.");
  }
}

export function runEffectTransaction<T>(db: DatabaseSync, write: () => T): T {
  requireIdleEffectConnection(db);
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
      throw new WebProblem(503, "effect-writer-busy", "Effect writer busy",
        "The local writer transaction was not acquired. Observe the same Effect identity before an explicit new attempt.");
    }
    // A failed acknowledgement is not evidence that COMMIT did not occur.
    // Only roll back a transaction that is still active; never auto-reissue.
    if (db.isTransaction) {
      try {
        db.exec("ROLLBACK");
      } catch (rollbackError) {
        const failures = [error, rollbackError];
        try {
          db.close();
        } catch (closeError) {
          failures.push(closeError);
        }
        throw new AggregateError(failures, "Effect transaction and rollback failed; owner connection recovery required");
      }
    }
    throw error;
  }
}
