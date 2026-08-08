import type { ProtocolJson } from "../host-contract/canonical.ts";
import { protocolCanonicalJson, protocolDigest, validateProtocolJson } from "../host-contract/canonical.ts";
import type { StationZeroFact } from "./model.ts";
import type { StationZeroV3TurnReceipt } from "./p2-model.ts";
import { StationZeroV3Store } from "./persistence.ts";

export const STATION_ZERO_V3_RESOURCE_EGRESS_KIND = "station-zero-v3-item" as const;

export class StationZeroV3ResourceEgressError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3ResourceEgressError";
  }
}

export class StationZeroV3ResourceEgressConflict extends StationZeroV3ResourceEgressError {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3ResourceEgressConflict";
  }
}

export interface ResourceEgressAuthorityEvidence {
  runId: string;
  turnSequence: number;
  turnBatchId: string;
  recordDigest: `sha256:${string}`;
  factId: string;
  factDigest: `sha256:${string}`;
  stateDigestAfter: `sha256:${string}`;
  retainedReplayVerified: true;
}

export interface ResourceEgressReceipt {
  schemaVersion: 1;
  kind: "ordivon.world.resource-egress-receipt";
  transferId: string;
  sourceWorldId: string;
  destinationWorldId: string;
  resourceKind: string;
  payloadDigest: `sha256:${string}`;
  sourceOccurrenceId: string;
  sourceOccurrenceDigest: `sha256:${string}`;
  authority: {
    authorityId: string;
    mechanism: "station-zero-v3-retained-turn-replay.v1";
    evidence: ResourceEgressAuthorityEvidence;
  };
}

export interface StationZeroV3ResourceEgressRequest {
  transferId: string;
  destinationWorldId: string;
  resourceKind: typeof STATION_ZERO_V3_RESOURCE_EGRESS_KIND;
  turnBatchId: string;
  factId: string;
  payload: ProtocolJson;
}

interface ResourceEgressRow {
  run_id: string;
  transfer_id: string;
  source_occurrence_id: string;
  destination_world_id: string;
  resource_kind: string;
  payload_digest: string;
  receipt_json: string;
  receipt_digest: string;
  created_at: string;
}

function prefixedDigest(value: string): `sha256:${string}` {
  const normalized = value.startsWith("sha256:") ? value : `sha256:${value}`;
  if (!/^sha256:[0-9a-f]{64}$/.test(normalized)) {
    throw new StationZeroV3ResourceEgressError("Retained Game digest is not sha256:<64 lowercase hex>");
  }
  return normalized as `sha256:${string}`;
}

function requireIdentity(value: string, label: string, prefix?: string): string {
  if (!value || value !== value.trim()) throw new StationZeroV3ResourceEgressError(`${label} must be non-empty and trimmed`);
  if (prefix && !value.startsWith(prefix)) throw new StationZeroV3ResourceEgressError(`${label} must start with ${prefix}`);
  return value;
}

function payloadItemId(payload: ProtocolJson): string {
  if (payload === null || Array.isArray(payload) || typeof payload !== "object") {
    throw new StationZeroV3ResourceEgressError("Station Zero resource payload must be a JSON object");
  }
  const itemId = payload.itemId;
  if (typeof itemId !== "string" || !itemId) {
    throw new StationZeroV3ResourceEgressError("Station Zero resource payload must identify itemId");
  }
  return itemId;
}

function extractedFact(receipt: StationZeroV3TurnReceipt, factId: string): Extract<StationZeroFact, { kind: "item_extracted" }> {
  const fact = receipt.record.resolution.facts.find((candidate) => candidate.factId === factId);
  if (!fact) throw new StationZeroV3ResourceEgressError(`Retained Turn Record does not contain Fact ${factId}`);
  if (fact.kind !== "item_extracted") {
    throw new StationZeroV3ResourceEgressError(`Fact ${factId} is not an item_extracted source consequence`);
  }
  const resolution = receipt.record.resolution.intentResolutions.find((candidate) => candidate.factIds.includes(factId));
  if (!resolution || resolution.status !== "executed" || !resolution.verificationPassed) {
    throw new StationZeroV3ResourceEgressError(`Fact ${factId} is not bound to a verified executed Intent`);
  }
  return fact;
}

function receiptFromRow(row: ResourceEgressRow): ResourceEgressReceipt {
  let parsed: unknown;
  try {
    parsed = JSON.parse(row.receipt_json);
  } catch (error) {
    throw new StationZeroV3ResourceEgressError("Retained Resource Egress receipt JSON is invalid", { cause: error });
  }
  validateProtocolJson(parsed);
  if (protocolDigest(parsed) !== row.receipt_digest) {
    throw new StationZeroV3ResourceEgressError("Retained Resource Egress receipt digest differs from content");
  }
  if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new StationZeroV3ResourceEgressError("Retained Resource Egress receipt is not an object");
  }
  const receipt = parsed as unknown as ResourceEgressReceipt;
  if (
    receipt.schemaVersion !== 1 ||
    receipt.kind !== "ordivon.world.resource-egress-receipt" ||
    receipt.transferId !== row.transfer_id ||
    receipt.sourceWorldId !== row.run_id ||
    receipt.destinationWorldId !== row.destination_world_id ||
    receipt.resourceKind !== row.resource_kind ||
    receipt.payloadDigest !== row.payload_digest ||
    receipt.sourceOccurrenceId !== row.source_occurrence_id
  ) {
    throw new StationZeroV3ResourceEgressError("Retained Resource Egress row differs from receipt content");
  }
  return receipt;
}

export class StationZeroV3ResourceEgress {
  readonly store: StationZeroV3Store;

  constructor(store: StationZeroV3Store) {
    this.store = store;
    this.store.db.exec(`
      CREATE TABLE IF NOT EXISTS station_zero_v3_resource_egress (
        run_id TEXT NOT NULL,
        transfer_id TEXT NOT NULL,
        source_occurrence_id TEXT NOT NULL,
        destination_world_id TEXT NOT NULL,
        resource_kind TEXT NOT NULL,
        payload_digest TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        receipt_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, transfer_id),
        UNIQUE (run_id, source_occurrence_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);
  }

  admit(runId: string, request: StationZeroV3ResourceEgressRequest): ResourceEgressReceipt {
    requireIdentity(runId, "Game Run identity", "run:");
    requireIdentity(request.transferId, "Resource Transfer identity", "transfer:");
    requireIdentity(request.destinationWorldId, "Destination World identity");
    requireIdentity(request.turnBatchId, "Turn Batch identity", "turn-batch:");
    requireIdentity(request.factId, "Source Fact identity", "fact:");
    if (request.resourceKind !== STATION_ZERO_V3_RESOURCE_EGRESS_KIND) {
      throw new StationZeroV3ResourceEgressError(`Unsupported Station Zero Resource kind: ${request.resourceKind}`);
    }
    validateProtocolJson(request.payload);

    const turn = this.store.turnReceiptByBatch(runId, request.turnBatchId);
    if (!turn) throw new StationZeroV3ResourceEgressError(`No retained Turn Receipt for ${request.turnBatchId}`);
    const fact = extractedFact(turn, request.factId);
    if (payloadItemId(request.payload) !== fact.itemId) {
      throw new StationZeroV3ResourceEgressError("Portable Resource itemId differs from retained item_extracted Fact");
    }

    const payloadDigest = protocolDigest(request.payload);
    const factDigest = protocolDigest(fact as unknown as ProtocolJson);
    const recordDigest = prefixedDigest(turn.recordDigest);
    const stateDigestAfter = prefixedDigest(turn.stateDigest);
    const occurrence = {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-resource-occurrence",
      runId,
      turnSequence: turn.turnSequence,
      turnBatchId: turn.turnBatchId,
      recordDigest,
      factId: fact.factId,
      factDigest,
    } satisfies Record<string, ProtocolJson>;
    const sourceOccurrenceDigest = protocolDigest(occurrence);
    const sourceOccurrenceId = `resource-occurrence:${sourceOccurrenceDigest.slice("sha256:".length)}`;
    const receipt: ResourceEgressReceipt = {
      schemaVersion: 1,
      kind: "ordivon.world.resource-egress-receipt",
      transferId: request.transferId,
      sourceWorldId: runId,
      destinationWorldId: request.destinationWorldId,
      resourceKind: request.resourceKind,
      payloadDigest,
      sourceOccurrenceId,
      sourceOccurrenceDigest,
      authority: {
        authorityId: `ordivon.game.station-zero-v3:${runId}`,
        mechanism: "station-zero-v3-retained-turn-replay.v1",
        evidence: {
          runId,
          turnSequence: turn.turnSequence,
          turnBatchId: turn.turnBatchId,
          recordDigest,
          factId: fact.factId,
          factDigest,
          stateDigestAfter,
          retainedReplayVerified: true,
        },
      },
    };
    validateProtocolJson(receipt);
    return this.commitExact(runId, receipt);
  }

  receipt(runId: string, transferId: string): ResourceEgressReceipt | null {
    const row = this.store.db.prepare(`SELECT * FROM station_zero_v3_resource_egress
      WHERE run_id = ? AND transfer_id = ?`).get(runId, transferId) as ResourceEgressRow | undefined;
    return row ? receiptFromRow(row) : null;
  }

  private commitExact(runId: string, receipt: ResourceEgressReceipt): ResourceEgressReceipt {
    const receiptJson = protocolCanonicalJson(receipt);
    const receiptDigest = protocolDigest(receipt);
    this.store.db.exec("BEGIN IMMEDIATE");
    try {
      const retainedByTransfer = this.store.db.prepare(`SELECT * FROM station_zero_v3_resource_egress
        WHERE run_id = ? AND transfer_id = ?`).get(runId, receipt.transferId) as ResourceEgressRow | undefined;
      if (retainedByTransfer) {
        const retained = receiptFromRow(retainedByTransfer);
        if (retainedByTransfer.receipt_digest !== receiptDigest || retainedByTransfer.receipt_json !== receiptJson) {
          throw new StationZeroV3ResourceEgressConflict("Resource Transfer identity is already bound to another source egress meaning");
        }
        this.store.db.exec("COMMIT");
        return retained;
      }
      const retainedByOccurrence = this.store.db.prepare(`SELECT * FROM station_zero_v3_resource_egress
        WHERE run_id = ? AND source_occurrence_id = ?`).get(runId, receipt.sourceOccurrenceId) as ResourceEgressRow | undefined;
      if (retainedByOccurrence) {
        throw new StationZeroV3ResourceEgressConflict(
          `Source Resource occurrence is already authorized by ${retainedByOccurrence.transfer_id}`,
        );
      }
      this.store.db.prepare(`INSERT INTO station_zero_v3_resource_egress
        (run_id, transfer_id, source_occurrence_id, destination_world_id, resource_kind,
         payload_digest, receipt_json, receipt_digest, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
          runId,
          receipt.transferId,
          receipt.sourceOccurrenceId,
          receipt.destinationWorldId,
          receipt.resourceKind,
          receipt.payloadDigest,
          receiptJson,
          receiptDigest,
          new Date().toISOString(),
        );
      this.store.db.exec("COMMIT");
      return receipt;
    } catch (error) {
      try { this.store.db.exec("ROLLBACK"); } catch {}
      throw error;
    }
  }
}
