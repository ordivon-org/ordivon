import type { ProtocolJson } from "../host-contract/canonical.ts";
import { protocolCanonicalJson, protocolDigest, validateProtocolJson } from "../host-contract/canonical.ts";
import type { StationZeroFactionId, StationZeroFact } from "./model.ts";
import { StationZeroV3Store } from "./persistence.ts";

export const STATION_ZERO_V3_MESSAGE_KIND = "station-zero-v3-fact-claim" as const;

export class StationZeroV3MessageIssuanceError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3MessageIssuanceError";
  }
}

export class StationZeroV3MessageIssuanceConflict extends StationZeroV3MessageIssuanceError {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3MessageIssuanceConflict";
  }
}

export interface StationZeroV3MessageProvenance {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-message-provenance";
  sourceWorldId: string;
  turnBatchId: string;
  turnRecordDigest: `sha256:${string}`;
  worldEventId: string;
  worldEventDigest: `sha256:${string}`;
  factId: string;
  factDigest: `sha256:${string}`;
  sourceFactionId: StationZeroFactionId;
  visibleToSourceFaction: true;
}

export interface StationZeroV3FactClaim {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-fact-claim";
  fact: StationZeroFact;
  sourceEpistemicStatus: "observed-in-source-world";
}

export interface MessageIssuanceAuthorityEvidence {
  runId: string;
  turnSequence: number;
  turnBatchId: string;
  recordDigest: `sha256:${string}`;
  factId: string;
  factDigest: `sha256:${string}`;
  sourceFactionId: StationZeroFactionId;
  visibleToSourceFaction: true;
  retainedReplayVerified: true;
}

export interface MessageIssuanceReceipt {
  schemaVersion: 1;
  kind: "ordivon.world.message-issuance-receipt";
  messageId: string;
  sourceWorldId: string;
  destinationWorldId: string;
  messageKind: typeof STATION_ZERO_V3_MESSAGE_KIND;
  provenanceDigest: `sha256:${string}`;
  payloadDigest: `sha256:${string}`;
  sourceOccurrenceId: string;
  sourceOccurrenceDigest: `sha256:${string}`;
  authority: {
    authorityId: string;
    mechanism: "station-zero-v3-visible-retained-fact.v1";
    evidence: MessageIssuanceAuthorityEvidence;
  };
}

export interface StationZeroV3MessageIssuanceRequest {
  messageId: string;
  destinationWorldId: string;
  messageKind: typeof STATION_ZERO_V3_MESSAGE_KIND;
  turnBatchId: string;
  factId: string;
  sourceFactionId: StationZeroFactionId;
}

export interface StationZeroV3IssuedMessage {
  receipt: MessageIssuanceReceipt;
  provenance: StationZeroV3MessageProvenance;
  payload: StationZeroV3FactClaim;
}

interface MessageIssuanceRow {
  run_id: string;
  message_id: string;
  destination_world_id: string;
  source_occurrence_id: string;
  receipt_json: string;
  receipt_digest: string;
  provenance_json: string;
  provenance_digest: string;
  payload_json: string;
  payload_digest: string;
  created_at: string;
}

function prefixedDigest(value: string): `sha256:${string}` {
  const normalized = value.startsWith("sha256:") ? value : `sha256:${value}`;
  if (!/^sha256:[0-9a-f]{64}$/.test(normalized)) {
    throw new StationZeroV3MessageIssuanceError("Retained Game digest is not sha256:<64 lowercase hex>");
  }
  return normalized as `sha256:${string}`;
}

function requireIdentity(value: string, label: string, prefix?: string): string {
  if (!value || value !== value.trim()) throw new StationZeroV3MessageIssuanceError(`${label} must be non-empty and trimmed`);
  if (prefix && !value.startsWith(prefix)) throw new StationZeroV3MessageIssuanceError(`${label} must start with ${prefix}`);
  return value;
}

function parsedProtocol<T>(text: string, label: string): T {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    throw new StationZeroV3MessageIssuanceError(`Retained ${label} JSON is invalid`, { cause: error });
  }
  validateProtocolJson(parsed);
  return parsed as T;
}

function issuedFromRow(row: MessageIssuanceRow): StationZeroV3IssuedMessage {
  const receipt = parsedProtocol<MessageIssuanceReceipt>(row.receipt_json, "Message Issuance receipt");
  const provenance = parsedProtocol<StationZeroV3MessageProvenance>(row.provenance_json, "Message provenance");
  const payload = parsedProtocol<StationZeroV3FactClaim>(row.payload_json, "Message payload");
  if (
    protocolDigest(receipt) !== row.receipt_digest ||
    protocolDigest(provenance) !== row.provenance_digest ||
    protocolDigest(payload) !== row.payload_digest
  ) {
    throw new StationZeroV3MessageIssuanceError("Retained Message Issuance digests differ from content");
  }
  if (
    receipt.schemaVersion !== 1 ||
    receipt.kind !== "ordivon.world.message-issuance-receipt" ||
    receipt.messageId !== row.message_id ||
    receipt.sourceWorldId !== row.run_id ||
    receipt.destinationWorldId !== row.destination_world_id ||
    receipt.sourceOccurrenceId !== row.source_occurrence_id ||
    receipt.provenanceDigest !== row.provenance_digest ||
    receipt.payloadDigest !== row.payload_digest
  ) {
    throw new StationZeroV3MessageIssuanceError("Retained Message Issuance row differs from receipt content");
  }
  return { receipt, provenance, payload };
}

export class StationZeroV3MessageIssuance {
  readonly store: StationZeroV3Store;

  constructor(store: StationZeroV3Store) {
    this.store = store;
    this.store.db.exec(`
      CREATE TABLE IF NOT EXISTS station_zero_v3_message_issuance (
        run_id TEXT NOT NULL,
        message_id TEXT NOT NULL,
        destination_world_id TEXT NOT NULL,
        source_occurrence_id TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        receipt_digest TEXT NOT NULL,
        provenance_json TEXT NOT NULL,
        provenance_digest TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, message_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);
  }

  issue(runId: string, request: StationZeroV3MessageIssuanceRequest): StationZeroV3IssuedMessage {
    requireIdentity(runId, "Game Run identity", "run:");
    requireIdentity(request.messageId, "Message identity", "message:");
    requireIdentity(request.destinationWorldId, "Destination World identity");
    requireIdentity(request.turnBatchId, "Turn Batch identity", "turn-batch:");
    requireIdentity(request.factId, "Source Fact identity", "fact:");
    if (request.messageKind !== STATION_ZERO_V3_MESSAGE_KIND) {
      throw new StationZeroV3MessageIssuanceError(`Unsupported Station Zero Message kind: ${request.messageKind}`);
    }

    const turn = this.store.turnReceiptByBatch(runId, request.turnBatchId);
    if (!turn) throw new StationZeroV3MessageIssuanceError(`No retained Turn Receipt for ${request.turnBatchId}`);
    const fact = turn.record.resolution.facts.find((candidate) => candidate.factId === request.factId);
    if (!fact) throw new StationZeroV3MessageIssuanceError(`Retained Turn Record does not contain Fact ${request.factId}`);
    const visible = turn.record.resolution.observations[request.sourceFactionId].visibleFactIds.includes(fact.factId);
    if (!visible) {
      throw new StationZeroV3MessageIssuanceError(
        `Fact ${fact.factId} is not visible to issuing faction ${request.sourceFactionId}`,
      );
    }

    const factDigest = protocolDigest(fact as unknown as ProtocolJson);
    const recordDigest = prefixedDigest(turn.recordDigest);
    const eventDigest = prefixedDigest(turn.eventDigest);
    const provenance: StationZeroV3MessageProvenance = {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-message-provenance",
      sourceWorldId: runId,
      turnBatchId: turn.turnBatchId,
      turnRecordDigest: recordDigest,
      worldEventId: turn.event.eventId,
      worldEventDigest: eventDigest,
      factId: fact.factId,
      factDigest,
      sourceFactionId: request.sourceFactionId,
      visibleToSourceFaction: true,
    };
    const payload: StationZeroV3FactClaim = {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-fact-claim",
      fact,
      sourceEpistemicStatus: "observed-in-source-world",
    };
    validateProtocolJson(provenance as unknown as ProtocolJson);
    validateProtocolJson(payload as unknown as ProtocolJson);

    const occurrence = {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-message-source-occurrence",
      runId,
      turnBatchId: turn.turnBatchId,
      factId: fact.factId,
      factDigest,
    } satisfies Record<string, ProtocolJson>;
    const sourceOccurrenceDigest = protocolDigest(occurrence);
    const sourceOccurrenceId = `message-source:${sourceOccurrenceDigest.slice("sha256:".length)}`;
    const receipt: MessageIssuanceReceipt = {
      schemaVersion: 1,
      kind: "ordivon.world.message-issuance-receipt",
      messageId: request.messageId,
      sourceWorldId: runId,
      destinationWorldId: request.destinationWorldId,
      messageKind: request.messageKind,
      provenanceDigest: protocolDigest(provenance as unknown as ProtocolJson),
      payloadDigest: protocolDigest(payload as unknown as ProtocolJson),
      sourceOccurrenceId,
      sourceOccurrenceDigest,
      authority: {
        authorityId: `ordivon.game.station-zero-v3:${runId}:faction:${request.sourceFactionId}`,
        mechanism: "station-zero-v3-visible-retained-fact.v1",
        evidence: {
          runId,
          turnSequence: turn.turnSequence,
          turnBatchId: turn.turnBatchId,
          recordDigest,
          factId: fact.factId,
          factDigest,
          sourceFactionId: request.sourceFactionId,
          visibleToSourceFaction: true,
          retainedReplayVerified: true,
        },
      },
    };
    validateProtocolJson(receipt as unknown as ProtocolJson);
    return this.commitExact(runId, { receipt, provenance, payload });
  }

  issued(runId: string, messageId: string): StationZeroV3IssuedMessage | null {
    const row = this.store.db.prepare(`SELECT * FROM station_zero_v3_message_issuance
      WHERE run_id = ? AND message_id = ?`).get(runId, messageId) as MessageIssuanceRow | undefined;
    return row ? issuedFromRow(row) : null;
  }

  private commitExact(runId: string, issued: StationZeroV3IssuedMessage): StationZeroV3IssuedMessage {
    const receiptJson = protocolCanonicalJson(issued.receipt as unknown as ProtocolJson);
    const receiptDigest = protocolDigest(issued.receipt as unknown as ProtocolJson);
    const provenanceJson = protocolCanonicalJson(issued.provenance as unknown as ProtocolJson);
    const provenanceDigest = protocolDigest(issued.provenance as unknown as ProtocolJson);
    const payloadJson = protocolCanonicalJson(issued.payload as unknown as ProtocolJson);
    const payloadDigest = protocolDigest(issued.payload as unknown as ProtocolJson);
    this.store.db.exec("BEGIN IMMEDIATE");
    try {
      const retained = this.store.db.prepare(`SELECT * FROM station_zero_v3_message_issuance
        WHERE run_id = ? AND message_id = ?`).get(runId, issued.receipt.messageId) as MessageIssuanceRow | undefined;
      if (retained) {
        const current = issuedFromRow(retained);
        if (retained.receipt_digest !== receiptDigest || retained.receipt_json !== receiptJson) {
          throw new StationZeroV3MessageIssuanceConflict(
            "Message identity is already bound to another source issuance meaning",
          );
        }
        this.store.db.exec("COMMIT");
        return current;
      }
      this.store.db.prepare(`INSERT INTO station_zero_v3_message_issuance
        (run_id, message_id, destination_world_id, source_occurrence_id,
         receipt_json, receipt_digest, provenance_json, provenance_digest,
         payload_json, payload_digest, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
          runId,
          issued.receipt.messageId,
          issued.receipt.destinationWorldId,
          issued.receipt.sourceOccurrenceId,
          receiptJson,
          receiptDigest,
          provenanceJson,
          provenanceDigest,
          payloadJson,
          payloadDigest,
          new Date().toISOString(),
        );
      this.store.db.exec("COMMIT");
      return issued;
    } catch (error) {
      try { this.store.db.exec("ROLLBACK"); } catch {}
      throw error;
    }
  }
}
