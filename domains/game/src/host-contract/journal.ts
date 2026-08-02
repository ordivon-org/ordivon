import type { DatabaseSync } from "node:sqlite";
import { gunzipSync, gzipSync } from "node:zlib";

import { canonicalJson, sha256 } from "../digest.ts";
import {
  protocolCanonicalJson,
  protocolDigest,
  validateProtocolJson,
} from "../host-contract/canonical.ts";


export interface HostArtifact<T = unknown> {
  digest: string;
  kind: string;
  content: T;
  byteLength: number;
  createdAt: string;
}

export interface HostJournalEvent<T = unknown> {
  runId: string;
  sequence: number;
  eventId: string;
  eventType: string;
  payload: T;
  previousDigest: string;
  recordDigest: string;
  createdAt: string;
}

interface JournalRow {
  run_id: string;
  sequence: number;
  event_id: string;
  event_type: string;
  payload_json: string;
  previous_digest: string;
  record_digest: string;
  created_at: string;
}
interface ArtifactRow {
  digest: string;
  kind: string;
  content_json: string;
  byte_length: number;
  created_at: string;
}

const COMPRESSED_JSON_PREFIX = "gzip-base64:";

function encodeStoredJson(json: string, threshold: number): string {
  if (Buffer.byteLength(json) < threshold) return json;
  const compressed = gzipSync(Buffer.from(json), { level: 9 }).toString("base64");
  const encoded = `${COMPRESSED_JSON_PREFIX}${compressed}`;
  return Buffer.byteLength(encoded) < Buffer.byteLength(json) ? encoded : json;
}

function decodeStoredJson(text: string, label: string): string {
  if (!text.startsWith(COMPRESSED_JSON_PREFIX)) return text;
  try { return gunzipSync(Buffer.from(text.slice(COMPRESSED_JSON_PREFIX.length), "base64")).toString("utf8"); }
  catch (error) { throw new HostStoreError("host_corrupt", `${label} compressed JSON is invalid`, { cause: error }); }
}

interface HostTransactionState {
  runId: string;
  depth: number;
}

const transactionStates = new WeakMap<DatabaseSync, HostTransactionState>();

export class HostStoreError extends Error {
  readonly code: "host_corrupt" | "host_constraint";
  constructor(code: HostStoreError["code"], message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "HostStoreError";
    this.code = code;
  }
}

function recordDigest(row: Omit<JournalRow, "record_digest" | "created_at">): string {
  return sha256({
    kind: "ordivon.game.host-journal-record",
    runId: row.run_id,
    sequence: Number(row.sequence),
    eventId: row.event_id,
    eventType: row.event_type,
    payloadJson: row.payload_json,
    previousDigest: row.previous_digest,
  });
}

function parse<T>(text: string, label: string): T {
  try { return JSON.parse(text) as T; }
  catch (error) { throw new HostStoreError("host_corrupt", `${label} is invalid JSON`, { cause: error }); }
}

export class HostStore {
  readonly db: DatabaseSync;

  constructor(db: DatabaseSync) {
    this.db = db;
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS host_artifacts (
        digest TEXT PRIMARY KEY,
        kind TEXT NOT NULL,
        content_json TEXT NOT NULL,
        byte_length INTEGER NOT NULL,
        created_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS host_journal (
        run_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        event_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        previous_digest TEXT NOT NULL,
        record_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, sequence),
        UNIQUE (run_id, event_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);
  }

  putArtifact<T>(kind: string, content: T): HostArtifact<T> {
    if (!kind || kind !== kind.trim()) throw new TypeError("artifact kind must be non-empty and trimmed");
    const contentJson = canonicalJson(content);
    const storedJson = encodeStoredJson(contentJson, 4_096);
    const digest = sha256({ kind, content });
    const existing = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (existing) {
      if (existing.kind !== kind || decodeStoredJson(existing.content_json, "Host Artifact") !== contentJson) {
        throw new HostStoreError("host_corrupt", "artifact digest is bound to different content");
      }
      return { digest, kind, content, byteLength: Number(existing.byte_length), createdAt: existing.created_at };
    }
    const createdAt = new Date().toISOString();
    const byteLength = Buffer.byteLength(contentJson);
    this.db.prepare("INSERT OR IGNORE INTO host_artifacts (digest, kind, content_json, byte_length, created_at) VALUES (?, ?, ?, ?, ?)")
      .run(digest, kind, storedJson, byteLength, createdAt);
    const retained = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (!retained || retained.kind !== kind || decodeStoredJson(retained.content_json, "Host Artifact") !== contentJson) {
      throw new HostStoreError("host_corrupt", "artifact digest is bound to different content");
    }
    return { digest, kind, content, byteLength: Number(retained.byte_length), createdAt: retained.created_at };
  }

  getArtifact<T>(digest: string): HostArtifact<T> {
    const row = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (!row) throw new Error(`unknown Host Artifact: ${digest}`);
    const content = parse<T>(decodeStoredJson(row.content_json, "Host Artifact"), "Host Artifact");
    if (sha256({ kind: row.kind, content }) !== row.digest) {
      throw new HostStoreError("host_corrupt", "Host Artifact digest mismatch");
    }
    return { digest: row.digest, kind: row.kind, content, byteLength: Number(row.byte_length), createdAt: row.created_at };
  }

  putProtocolArtifact<T>(kind: string, content: T, createdAt = new Date().toISOString()): HostArtifact<T> {
    if (!kind || kind !== kind.trim()) throw new TypeError("artifact kind must be non-empty and trimmed");
    validateProtocolJson(content);
    const contentJson = protocolCanonicalJson(content);
    const storedJson = encodeStoredJson(contentJson, 4_096);
    const digest = protocolDigest(content);
    const existing = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (existing) {
      if (existing.kind !== kind || decodeStoredJson(existing.content_json, "Protocol Artifact") !== contentJson) {
        throw new HostStoreError("host_corrupt", "Protocol Artifact digest is bound to different content or kind");
      }
      return { digest, kind, content, byteLength: Number(existing.byte_length), createdAt: existing.created_at };
    }
    const byteLength = Buffer.byteLength(contentJson);
    this.db.prepare("INSERT OR IGNORE INTO host_artifacts (digest, kind, content_json, byte_length, created_at) VALUES (?, ?, ?, ?, ?)")
      .run(digest, kind, storedJson, byteLength, createdAt);
    const retained = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (!retained || retained.kind !== kind || decodeStoredJson(retained.content_json, "Protocol Artifact") !== contentJson) {
      throw new HostStoreError("host_corrupt", "Protocol Artifact digest is bound to different content or kind");
    }
    return { digest, kind, content, byteLength: Number(retained.byte_length), createdAt: retained.created_at };
  }

  getProtocolArtifact<T>(digest: string): HostArtifact<T> {
    const row = this.db.prepare("SELECT * FROM host_artifacts WHERE digest = ?").get(digest) as ArtifactRow | undefined;
    if (!row) throw new Error(`unknown Protocol Artifact: ${digest}`);
    const content = parse<T>(decodeStoredJson(row.content_json, "Protocol Artifact"), "Protocol Artifact");
    validateProtocolJson(content);
    if (protocolDigest(content) !== row.digest) {
      throw new HostStoreError("host_corrupt", "Protocol Artifact digest mismatch");
    }
    return { digest: row.digest, kind: row.kind, content, byteLength: Number(row.byte_length), createdAt: row.created_at };
  }

  appendEvent(runId: string, eventType: string, eventId: string, payload: unknown): HostJournalEvent {
    return this.withTransaction(runId, () => this.appendEventInTransaction(
      runId, eventType, eventId, payload, new Date().toISOString(),
    ));
  }

  withTransaction<T>(runId: string, operation: () => T): T {
    const active = transactionStates.get(this.db);
    if (active) {
      if (active.runId !== runId) throw new Error("Host transaction cannot span different Runs");
      active.depth += 1;
      try { return operation(); }
      finally { active.depth -= 1; }
    }
    const run = this.db.prepare("SELECT 1 AS present FROM runs WHERE run_id = ?").get(runId) as { present: number } | undefined;
    if (!run) throw new Error(`unknown run: ${runId}`);
    this.db.exec("BEGIN IMMEDIATE");
    transactionStates.set(this.db, { runId, depth: 1 });
    try {
      const result = operation();
      this.db.exec("COMMIT");
      return result;
    } catch (error) {
      try { this.db.exec("ROLLBACK"); } catch {}
      throw error;
    } finally {
      transactionStates.delete(this.db);
    }
  }

  appendEventInTransaction(
    runId: string,
    eventType: string,
    eventId: string,
    payload: unknown,
    createdAt: string,
  ): HostJournalEvent {
    const payloadJson = canonicalJson(payload);
    const storedPayloadJson = eventType.startsWith("host-contract.") ? payloadJson : encodeStoredJson(payloadJson, 256);
    const existing = this.db.prepare("SELECT * FROM host_journal WHERE run_id = ? AND event_id = ?")
      .get(runId, eventId) as JournalRow | undefined;
    if (existing) {
      if (existing.event_type !== eventType || decodeStoredJson(existing.payload_json, "Host Journal payload") !== payloadJson) {
        throw new HostStoreError("host_constraint", "Host Event identity is bound to different content");
      }
      return this.fromJournalRow(existing);
    }
    const last = this.db.prepare("SELECT sequence, record_digest FROM host_journal WHERE run_id = ? ORDER BY sequence DESC LIMIT 1")
      .get(runId) as { sequence: number; record_digest: string } | undefined;
    const base = {
      run_id: runId,
      sequence: Number(last?.sequence ?? -1) + 1,
      event_id: eventId,
      event_type: eventType,
      payload_json: storedPayloadJson,
      previous_digest: last?.record_digest ?? "",
    };
    const digest = recordDigest(base);
    this.db.prepare(`INSERT INTO host_journal
      (run_id, sequence, event_id, event_type, payload_json, previous_digest, record_digest, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
      .run(runId, base.sequence, eventId, eventType, storedPayloadJson, base.previous_digest, digest, createdAt);
    return {
      runId, sequence: base.sequence, eventId, eventType, payload,
      previousDigest: base.previous_digest, recordDigest: digest, createdAt,
    };
  }

  getJournalEvent(runId: string, eventId: string): HostJournalEvent | null {
    const row = this.db.prepare(
      "SELECT * FROM host_journal WHERE run_id = ? AND event_id = ?",
    ).get(runId, eventId) as JournalRow | undefined;
    if (!row) return null;
    if (recordDigest(row) !== row.record_digest) {
      throw new HostStoreError("host_corrupt", "Host Journal record digest mismatch");
    }
    return this.fromJournalRow(row);
  }

  listJournal(runId: string): HostJournalEvent[] {
    const rows = this.db.prepare("SELECT * FROM host_journal WHERE run_id = ? ORDER BY sequence")
      .all(runId) as unknown as JournalRow[];
    return rows.map((row) => this.fromJournalRow(row));
  }

  listEventTypes(runId: string): string[] {
    const rows = this.db.prepare(
      "SELECT event_type FROM host_journal WHERE run_id = ? ORDER BY sequence",
    ).all(runId) as unknown as Array<{ event_type: string }>;
    return rows.map((row) => row.event_type);
  }

  verifyJournal(runId: string): void {
    const rows = this.db.prepare("SELECT * FROM host_journal WHERE run_id = ? ORDER BY sequence")
      .all(runId) as unknown as JournalRow[];
    let previous = "";
    for (let index = 0; index < rows.length; index += 1) {
      const row = rows[index];
      if (!row || Number(row.sequence) !== index) {
        throw new HostStoreError("host_corrupt", "Host Journal sequence is discontinuous");
      }
      if (row.previous_digest !== previous) {
        throw new HostStoreError("host_corrupt", "Host Journal previous digest mismatch");
      }
      const actual = recordDigest(row);
      if (actual !== row.record_digest) {
        throw new HostStoreError("host_corrupt", "Host Journal record digest mismatch");
      }
      previous = actual;
    }
  }

  private fromJournalRow(row: JournalRow): HostJournalEvent {
    return {
      runId: row.run_id,
      sequence: Number(row.sequence),
      eventId: row.event_id,
      eventType: row.event_type,
      payload: parse(decodeStoredJson(row.payload_json, "Host Journal payload"), "Host Journal payload"),
      previousDigest: row.previous_digest,
      recordDigest: row.record_digest,
      createdAt: row.created_at,
    };
  }
}
