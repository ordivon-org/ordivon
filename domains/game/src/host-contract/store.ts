import type { ProtocolJson } from "./canonical.ts";
import { protocolDigest, validateProtocolJson } from "./canonical.ts";
import type { HostWorkloadObject } from "./model.ts";
import { validateHostWorkloadObject } from "./validate.ts";
import type { HostArtifact, HostJournalEvent } from "./journal.ts";
import type { HostStore } from "./journal.ts";

export interface HostContractEventPayload {
  schemaVersion: 1;
  kind: "ordivon.game.host-contract-event";
  contractDigest: `sha256:${string}`;
  contractKind: string;
  subjectRef: string;
  relatedDigests: `sha256:${string}`[];
}

export interface HostContractTranscriptEntry {
  eventId: string;
  eventType: string;
  subjectRef: string;
  contractDigest: `sha256:${string}`;
  contractKind: string;
  relatedDigests: `sha256:${string}`[];
  object: ProtocolJson;
  sequence: number;
}

interface ContractIndexRow {
  run_id: string;
  sequence: number;
  event_id: string;
  event_type: string;
  subject_ref: string;
  contract_kind: string;
  contract_digest: string;
  related_digests_json: string;
}

interface MissingJournalRow {
  run_id: string;
  sequence: number;
  event_id: string;
  event_type: string;
  payload_json: string;
}

function payload(value: unknown, eventId: string): HostContractEventPayload {
  const candidate = value as Partial<HostContractEventPayload>;
  if (
    candidate.schemaVersion !== 1 ||
    candidate.kind !== "ordivon.game.host-contract-event" ||
    typeof candidate.contractDigest !== "string" ||
    typeof candidate.contractKind !== "string" ||
    typeof candidate.subjectRef !== "string" ||
    !Array.isArray(candidate.relatedDigests) ||
    candidate.relatedDigests.some((digest) => typeof digest !== "string")
  ) throw new Error(`invalid Host Contract journal payload: ${eventId}`);
  return candidate as HostContractEventPayload;
}

export class HostContractStore {
  readonly host: HostStore;
  private activeRunId: string | null = null;
  private readonly indexedRuns = new Set<string>();

  constructor(host: HostStore) {
    this.host = host;
    this.host.db.exec(`
      CREATE TABLE IF NOT EXISTS host_contract_entries (
        run_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        event_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        subject_ref TEXT NOT NULL,
        contract_kind TEXT NOT NULL,
        contract_digest TEXT NOT NULL,
        related_digests_json TEXT NOT NULL,
        PRIMARY KEY (run_id, sequence),
        UNIQUE (run_id, event_id),
        FOREIGN KEY (run_id, sequence) REFERENCES host_journal(run_id, sequence)
      );
      CREATE INDEX IF NOT EXISTS host_contract_latest_idx
        ON host_contract_entries(run_id, subject_ref, contract_kind, sequence DESC);
      CREATE INDEX IF NOT EXISTS host_contract_kind_idx
        ON host_contract_entries(run_id, contract_kind, sequence);
    `);
  }

  batch<T>(runId: string, operation: () => T): T {
    if (this.activeRunId === runId) return operation();
    if (this.activeRunId !== null) throw new Error("Host Contract Store cannot nest batches for different Runs");
    return this.host.withTransaction(runId, () => {
      this.activeRunId = runId;
      try { return operation(); }
      finally { this.activeRunId = null; }
    });
  }

  putWireObject(
    runId: string, eventType: string, eventId: string, subjectRef: string, value: HostWorkloadObject,
    options: { relatedDigests?: `sha256:${string}`[]; createdAt?: string } = {},
  ): HostArtifact<HostWorkloadObject> {
    return this.putProtocolObject(runId, eventType, eventId, subjectRef, validateHostWorkloadObject(value), options);
  }

  putProtocolObject<T>(
    runId: string, eventType: string, eventId: string, subjectRef: string, value: T,
    options: { relatedDigests?: `sha256:${string}`[]; createdAt?: string; artifactKind?: string } = {},
  ): HostArtifact<T> {
    validateProtocolJson(value);
    if (!eventType.startsWith("host-contract.")) throw new TypeError("Host Contract event type must start with host-contract.");
    if (!eventId.startsWith("host-contract:")) throw new TypeError("Host Contract event identity must start with host-contract:");
    if (!subjectRef.trim()) throw new TypeError("Host Contract subjectRef is required");
    const contractKind = typeof value === "object" && value !== null && !Array.isArray(value) && typeof value.kind === "string"
      ? value.kind : options.artifactKind ?? "ordivon.protocol-object";
    const createdAt = options.createdAt ?? new Date().toISOString();
    const write = (): HostArtifact<T> => {
      const artifact = this.host.putProtocolArtifact(options.artifactKind ?? contractKind, value, createdAt);
      const eventPayload: HostContractEventPayload = {
        schemaVersion: 1, kind: "ordivon.game.host-contract-event",
        contractDigest: artifact.digest as `sha256:${string}`, contractKind, subjectRef,
        relatedDigests: [...new Set(options.relatedDigests ?? [])].sort(),
      };
      const event = this.host.appendEventInTransaction(runId, eventType, eventId, eventPayload, createdAt);
      this.putIndex(event, eventPayload);
      return artifact;
    };
    return this.activeRunId === runId ? write() : this.batch(runId, write);
  }

  get<T extends ProtocolJson>(digest: string): HostArtifact<T> { return this.host.getProtocolArtifact<T>(digest); }

  transcript(runId: string): HostContractTranscriptEntry[] {
    this.ensureIndexed(runId);
    const rows = this.host.db.prepare("SELECT * FROM host_contract_entries WHERE run_id = ? ORDER BY sequence").all(runId) as unknown as ContractIndexRow[];
    return rows.map((row) => this.entryFromIndex(row));
  }

  count(runId: string, contractKind: string): number {
    this.ensureIndexed(runId);
    const row = this.host.db.prepare("SELECT COUNT(*) count FROM host_contract_entries WHERE run_id = ? AND contract_kind = ?").get(runId, contractKind) as { count: number };
    return Number(row.count);
  }

  latest(runId: string, subjectRef: string, contractKind: string): HostContractTranscriptEntry | null {
    this.ensureIndexed(runId);
    const row = this.host.db.prepare(`SELECT * FROM host_contract_entries
      WHERE run_id = ? AND subject_ref = ? AND contract_kind = ? ORDER BY sequence DESC LIMIT 1`)
      .get(runId, subjectRef, contractKind) as ContractIndexRow | undefined;
    return row ? this.entryFromIndex(row) : null;
  }

  private ensureIndexed(runId: string): void {
    if (this.indexedRuns.has(runId)) return;
    const rows = this.host.db.prepare(`SELECT h.run_id, h.sequence, h.event_id, h.event_type, h.payload_json
      FROM host_journal h LEFT JOIN host_contract_entries i
        ON i.run_id = h.run_id AND i.sequence = h.sequence
      WHERE h.run_id = ? AND h.event_type LIKE 'host-contract.%' AND i.sequence IS NULL
      ORDER BY h.sequence`).all(runId) as unknown as MissingJournalRow[];
    if (rows.length > 0) this.host.withTransaction(runId, () => {
      for (const row of rows) {
        let parsed: unknown;
        try { parsed = JSON.parse(row.payload_json); }
        catch { throw new Error(`invalid Host Contract journal payload: ${row.event_id}`); }
        const contractPayload = payload(parsed, row.event_id);
        this.putIndex({
          runId: row.run_id, sequence: Number(row.sequence), eventId: row.event_id, eventType: row.event_type,
          payload: contractPayload, previousDigest: "", recordDigest: "", createdAt: "",
        }, contractPayload);
      }
    });
    this.indexedRuns.add(runId);
  }

  private putIndex(event: HostJournalEvent, contractPayload: HostContractEventPayload): void {
    this.host.db.prepare(`INSERT OR IGNORE INTO host_contract_entries
      (run_id, sequence, event_id, event_type, subject_ref, contract_kind, contract_digest, related_digests_json)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)`).run(
        event.runId, event.sequence, event.eventId, event.eventType, contractPayload.subjectRef,
        contractPayload.contractKind, contractPayload.contractDigest, JSON.stringify(contractPayload.relatedDigests),
      );
  }

  private entryFromIndex(row: ContractIndexRow): HostContractTranscriptEntry {
    const event = this.host.getJournalEvent(row.run_id, row.event_id);
    if (!event || event.sequence !== Number(row.sequence) || event.eventType !== row.event_type) {
      throw new Error(`Host Contract index differs from journal: ${row.event_id}`);
    }
    const contractPayload = payload(event.payload, event.eventId);
    const related = JSON.parse(row.related_digests_json) as unknown;
    if (
      contractPayload.subjectRef !== row.subject_ref || contractPayload.contractKind !== row.contract_kind ||
      contractPayload.contractDigest !== row.contract_digest || JSON.stringify(contractPayload.relatedDigests) !== JSON.stringify(related)
    ) throw new Error(`Host Contract index differs from journal: ${row.event_id}`);
    const artifact = this.host.getProtocolArtifact<ProtocolJson>(contractPayload.contractDigest);
    if (protocolDigest(artifact.content) !== contractPayload.contractDigest) throw new Error(`Host Contract Artifact digest mismatch: ${event.eventId}`);
    return {
      eventId: event.eventId, eventType: event.eventType, subjectRef: contractPayload.subjectRef,
      contractDigest: contractPayload.contractDigest, contractKind: contractPayload.contractKind,
      relatedDigests: contractPayload.relatedDigests, object: artifact.content, sequence: event.sequence,
    };
  }
}
