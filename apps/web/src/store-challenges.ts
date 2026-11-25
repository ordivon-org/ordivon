/** Challenge payload capture and one-shot persistence on the existing WebStore connection. */
import { randomUUID } from "node:crypto";
import type { DatabaseSync } from "node:sqlite";
import { stableDigest } from "./identity-digests.ts";
import { WebProblem } from "./errors.ts";
import { runOwnerTransaction } from "./store-owner-transaction.ts";
import type { ChallengePurpose, ChallengeRecord } from "./model.ts";
import type { ChallengeRow } from "./store-row-projections.ts";

export class ChallengeStore {
  private readonly db: DatabaseSync;

  constructor(db: DatabaseSync) {
    this.db = db;
  }

  createChallenge(
    purpose: ChallengePurpose,
    principalId: string,
    challenge: string,
    now: number,
    ttlSeconds = 120,
    payload: unknown = {},
  ): ChallengeRecord {
    const challengeId = randomUUID();
    // Capture one JSON snapshot, rather than serializing mutable input twice.
    const encoded = JSON.stringify(payload);
    if (encoded === undefined) {
      throw new WebProblem(422, "challenge-payload-invalid", "Invalid Challenge payload",
        "The Challenge payload must have a JSON representation.");
    }
    const snapshot: unknown = JSON.parse(encoded);
    const payloadDigest = stableDigest(snapshot);
    const record: ChallengeRecord = {
      challengeId,
      purpose,
      principalId,
      challenge,
      payloadDigest,
      payload: snapshot,
      expiresAt: now + ttlSeconds,
    };
    this.db
      .prepare(`
        INSERT INTO webauthn_challenges (
          challenge_id, purpose, principal_id, challenge,
          payload_digest, payload_json, expires_at, consumed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
      `)
      .run(
        record.challengeId,
        record.purpose,
        record.principalId,
        record.challenge,
        record.payloadDigest,
        encoded,
        record.expiresAt,
      );
    return record;
  }

  consumeChallenge(
    challengeId: string,
    purpose: ChallengePurpose,
    now: number,
  ): ChallengeRecord {
    return runOwnerTransaction(this.db, "challenge", () => {
      const row = this.db
        .prepare("SELECT * FROM webauthn_challenges WHERE challenge_id = ?")
        .get(challengeId) as ChallengeRow | undefined;
      if (
        row === undefined ||
        row.purpose !== purpose ||
        row.consumed_at !== null ||
        row.expires_at <= now
      ) {
        throw new WebProblem(
          409,
          "challenge-invalid",
          "Challenge unavailable",
          "The WebAuthn challenge is missing, expired, consumed, or has the wrong purpose.",
        );
      }
      // Verify the persisted payload before committing one-shot consumption.
      // A digest mismatch or invalid JSON is an owner integrity error, not a
      // valid ceremony. No invalid record is returned to WebAuthn.
      let payload: unknown;
      try {
        payload = JSON.parse(row.payload_json);
      } catch {
        throw new WebProblem(500, "challenge-corrupt", "Challenge integrity failure",
          "The stored Challenge payload cannot be decoded.");
      }
      if (stableDigest(payload) !== row.payload_digest) {
        throw new WebProblem(500, "challenge-corrupt", "Challenge integrity failure",
          "The stored Challenge payload does not match its recorded digest.");
      }
      const update = this.db
        .prepare(
          "UPDATE webauthn_challenges SET consumed_at = ? WHERE challenge_id = ? AND consumed_at IS NULL",
        )
        .run(now, challengeId);
      if (update.changes !== 1) {
        throw new WebProblem(
          409,
          "challenge-race",
          "Challenge already consumed",
          "The WebAuthn challenge was consumed concurrently.",
        );
      }
      const record: ChallengeRecord = {
        challengeId: row.challenge_id,
        purpose: row.purpose,
        principalId: row.principal_id,
        challenge: row.challenge,
        payloadDigest: row.payload_digest,
        payload,
        expiresAt: row.expires_at,
      };
      return record;
    });
  }
}
