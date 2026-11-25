/** Effect-specific adapter preserves the existing transaction API. */
import type { DatabaseSync } from "node:sqlite";
import { requireIdleOwnerConnection, runOwnerTransaction } from "./store-owner-transaction.ts";

export function requireIdleEffectConnection(db: DatabaseSync): void {
  requireIdleOwnerConnection(db, "effect");
}

export function runEffectTransaction<T>(db: DatabaseSync, write: () => T): T {
  return runOwnerTransaction(db, "effect", write);
}
