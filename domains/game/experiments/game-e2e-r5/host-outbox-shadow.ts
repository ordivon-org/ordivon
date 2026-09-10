import { DatabaseSync } from "node:sqlite";

import { canonicalJson, sha256 } from "../../src/digest.ts";

export interface ShadowOutboxEvent {
  outboxId: string;
  runId: string;
  sequence: number;
  eventId: string;
  eventType: string;
  payload: unknown;
  payloadDigest: string;
  stateDigest: string;
  delivered: boolean;
}

interface OutboxRow {
  outbox_id: string;
  run_id: string;
  sequence: number;
  event_id: string;
  event_type: string;
  payload_json: string;
  payload_digest: string;
  state_digest: string;
  delivered: number;
}

function fromRow(row: OutboxRow): ShadowOutboxEvent {
  const payload = JSON.parse(row.payload_json);
  const digest = sha256(payload);
  if (digest !== row.payload_digest) throw new Error("shadow outbox payload digest mismatch");
  return {
    outboxId: row.outbox_id,
    runId: row.run_id,
    sequence: Number(row.sequence),
    eventId: row.event_id,
    eventType: row.event_type,
    payload,
    payloadDigest: row.payload_digest,
    stateDigest: row.state_digest,
    delivered: row.delivered === 1,
  };
}

export class ShadowHostReceiver {
  private readonly accepted = new Map<string, ShadowOutboxEvent>();
  private readonly lastSequence = new Map<string, number>();
  available = true;

  accept(event: ShadowOutboxEvent): void {
    if (!this.available) throw new Error("shadow Host unavailable");
    const retained = this.accepted.get(event.outboxId);
    if (retained) {
      if (canonicalJson(retained) !== canonicalJson(event)) throw new Error("shadow Host identity conflict");
      return;
    }
    const expected = (this.lastSequence.get(event.runId) ?? -1) + 1;
    if (event.sequence !== expected) {
      throw new Error(`shadow Host out-of-order event: expected ${expected}, received ${event.sequence}`);
    }
    if (sha256(event.payload) !== event.payloadDigest) throw new Error("shadow Host payload digest mismatch");
    this.accepted.set(event.outboxId, { ...event, delivered: false });
    this.lastSequence.set(event.runId, event.sequence);
  }

  count(runId: string): number {
    return [...this.accepted.values()].filter((event) => event.runId === runId).length;
  }

  get(outboxId: string): ShadowOutboxEvent | null {
    return this.accepted.get(outboxId) ?? null;
  }
}

export class ShadowOutboxHarness {
  readonly db: DatabaseSync;

  constructor(db: DatabaseSync = new DatabaseSync(":memory:")) {
    this.db = db;
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS r5_shadow_game_state (
        run_id TEXT PRIMARY KEY,
        revision INTEGER NOT NULL,
        value_json TEXT NOT NULL,
        state_digest TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS r5_shadow_host_outbox (
        outbox_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        event_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_digest TEXT NOT NULL,
        state_digest TEXT NOT NULL,
        delivered INTEGER NOT NULL DEFAULT 0,
        UNIQUE (run_id, sequence),
        UNIQUE (run_id, event_id)
      );
    `);
  }

  close(): void {
    this.db.close();
  }

  commit(
    runId: string,
    eventId: string,
    eventType: string,
    nextState: unknown,
    payload: unknown,
    fault: "none" | "before_commit" | "after_commit_response_loss" = "none",
  ): ShadowOutboxEvent {
    const stateDigest = sha256(nextState);
    const payloadDigest = sha256(payload);
    const existing = this.db.prepare(
      "SELECT * FROM r5_shadow_host_outbox WHERE run_id = ? AND event_id = ?",
    ).get(runId, eventId) as OutboxRow | undefined;
    if (existing) {
      const retained = fromRow(existing);
      if (retained.eventType !== eventType || retained.payloadDigest !== payloadDigest || retained.stateDigest !== stateDigest) {
        throw new Error("shadow outbox event identity conflict");
      }
      return retained;
    }

    this.db.exec("BEGIN IMMEDIATE");
    let committed = false;
    try {
      const current = this.db.prepare(
        "SELECT revision FROM r5_shadow_game_state WHERE run_id = ?",
      ).get(runId) as { revision?: number } | undefined;
      const revision = Number(current?.revision ?? -1) + 1;
      const sequenceRow = this.db.prepare(
        "SELECT MAX(sequence) AS sequence FROM r5_shadow_host_outbox WHERE run_id = ?",
      ).get(runId) as { sequence?: number | null } | undefined;
      const sequence = Number(sequenceRow?.sequence ?? -1) + 1;
      const outboxId = `shadow-outbox:${sha256({ runId, eventId })}`;
      this.db.prepare(`INSERT INTO r5_shadow_game_state (run_id, revision, value_json, state_digest)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET revision = excluded.revision, value_json = excluded.value_json, state_digest = excluded.state_digest`)
        .run(runId, revision, canonicalJson(nextState), stateDigest);
      this.db.prepare(`INSERT INTO r5_shadow_host_outbox
        (outbox_id, run_id, sequence, event_id, event_type, payload_json, payload_digest, state_digest, delivered)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)`)
        .run(outboxId, runId, sequence, eventId, eventType, canonicalJson(payload), payloadDigest, stateDigest);
      if (fault === "before_commit") throw new Error("injected before-commit failure");
      this.db.exec("COMMIT");
      committed = true;
      const row = this.db.prepare("SELECT * FROM r5_shadow_host_outbox WHERE outbox_id = ?").get(outboxId) as unknown as OutboxRow;
      const retained = fromRow(row);
      if (fault === "after_commit_response_loss") throw new Error("injected response loss after commit");
      return retained;
    } catch (error) {
      if (!committed) {
        try { this.db.exec("ROLLBACK"); } catch {}
      }
      throw error;
    }
  }

  state(runId: string): { revision: number; value: unknown; stateDigest: string } | null {
    const row = this.db.prepare(
      "SELECT revision, value_json, state_digest FROM r5_shadow_game_state WHERE run_id = ?",
    ).get(runId) as { revision: number; value_json: string; state_digest: string } | undefined;
    if (!row) return null;
    const value = JSON.parse(row.value_json);
    if (sha256(value) !== row.state_digest) throw new Error("shadow Game state digest mismatch");
    return { revision: Number(row.revision), value, stateDigest: row.state_digest };
  }

  pending(runId: string): ShadowOutboxEvent[] {
    const rows = this.db.prepare(
      "SELECT * FROM r5_shadow_host_outbox WHERE run_id = ? AND delivered = 0 ORDER BY sequence",
    ).all(runId) as unknown as OutboxRow[];
    return rows.map(fromRow);
  }

  relayNext(
    runId: string,
    receiver: ShadowHostReceiver,
    fault: "none" | "after_accept_before_ack" = "none",
  ): ShadowOutboxEvent | null {
    const event = this.pending(runId)[0] ?? null;
    if (!event) return null;
    receiver.accept(event);
    if (fault === "after_accept_before_ack") throw new Error("injected response loss after Host acceptance");
    const changed = this.db.prepare(
      "UPDATE r5_shadow_host_outbox SET delivered = 1 WHERE outbox_id = ? AND delivered = 0",
    ).run(event.outboxId);
    if (Number(changed.changes) !== 1) throw new Error("shadow outbox acknowledgement conflict");
    return { ...event, delivered: true };
  }

  rawOutboxRow(outboxId: string): OutboxRow | null {
    return this.db.prepare("SELECT * FROM r5_shadow_host_outbox WHERE outbox_id = ?").get(outboxId) as OutboxRow | undefined ?? null;
  }
}
