/** Owner-local replay consumption. Cryptographic proof verification remains external. */
import type { DatabaseSync } from "node:sqlite";
import { hashToken } from "./identity-digests.ts";
import { WebProblem } from "./errors.ts";
import { runOwnerTransaction } from "./store-owner-transaction.ts";

export function consumeDpopProof(
  db: DatabaseSync,
  proofId: string,
  nowEpochSeconds: number,
  ttlSeconds = 600,
): void {
  const bytes = Buffer.byteLength(proofId, "utf8");
  if (
    bytes < 1 ||
    bytes > 256 ||
    !Number.isSafeInteger(ttlSeconds) ||
    ttlSeconds < 1
  ) {
    throw new WebProblem(
      401,
      "dpop-proof-invalid",
      "Agent verification failed",
      "The DPoP proof identity is invalid.",
    );
  }
  const proofHash = hashToken(proofId);
  runOwnerTransaction(db, "dpop", () => {
    db
      .prepare("DELETE FROM dpop_proofs WHERE expires_at <= ?")
      .run(nowEpochSeconds);
    const existing = db
      .prepare("SELECT proof_hash FROM dpop_proofs WHERE proof_hash = ?")
      .get(proofHash);
    if (existing !== undefined) {
      throw new WebProblem(
        401,
        "dpop-proof-replayed",
        "Agent verification failed",
        "The DPoP proof has already been consumed.",
      );
    }
    db
      .prepare("INSERT INTO dpop_proofs (proof_hash, expires_at) VALUES (?, ?)")
      .run(proofHash, nowEpochSeconds + ttlSeconds);
  });
}
