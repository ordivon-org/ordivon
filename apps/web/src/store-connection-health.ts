/** Owner-local connection health; not a durable Effect outcome or a retry policy. */
import type { DatabaseSync } from "node:sqlite";
import { WebProblem } from "./errors.ts";

// Lifetime-bound marker: no registry, no retention of closed connections,
// and no way to clear the health of a previously failed connection.
const quarantined = new WeakSet<DatabaseSync>();

export function quarantineOwnerConnection(db: DatabaseSync): void {
  quarantined.add(db);
}

export function requireUsableOwnerConnection(db: DatabaseSync): void {
  if (quarantined.has(db)) {
    throw new WebProblem(503, "web-store-recovery-required", "Web Store recovery required",
      "The owner connection is quarantined. Explicitly close it and observe Effect state through a new usable connection.");
  }
}
