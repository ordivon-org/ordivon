import type { ProtocolJson } from "../host-contract/canonical.ts";
import { protocolCanonicalJson, protocolDigest, validateProtocolJson } from "../host-contract/canonical.ts";
import type { StationZeroActorIntent, StationZeroFact, StationZeroIntentResolution } from "./model.ts";
import type { StationZeroV3TurnReceipt } from "./p2-model.ts";
import { StationZeroV3Store } from "./persistence.ts";

export class StationZeroV3EntityDepartureError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3EntityDepartureError";
  }
}

export class StationZeroV3EntityDepartureConflict extends StationZeroV3EntityDepartureError {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "StationZeroV3EntityDepartureConflict";
  }
}

export interface EntityDepartureAuthorityEvidence {
  runId: string;
  turnSequence: number;
  turnBatchId: string;
  recordDigest: `sha256:${string}`;
  stateDigestAfter: `sha256:${string}`;
  factId: string;
  factDigest: `sha256:${string}`;
  intentId: string;
  intentDigest: `sha256:${string}`;
  resolutionStatus: "executed";
  resolutionReason: "actor_extracted";
  verificationPassed: true;
  entityLifeStateAfter: "extracted";
  retainedReplayVerified: true;
}

export interface EntityDepartureReceipt {
  schemaVersion: 1;
  kind: "ordivon.world.entity-departure-receipt";
  migrationId: string;
  entityId: string;
  sourceWorldId: string;
  destinationWorldId: string;
  sourceOccurrenceId: string;
  sourceOccurrenceDigest: `sha256:${string}`;
  authority: {
    authorityId: string;
    mechanism: "station-zero-v3-verified-extraction.v1";
    evidence: EntityDepartureAuthorityEvidence;
  };
}

export interface StationZeroV3EntityDepartureRequest {
  migrationId: string;
  destinationWorldId: string;
  entityId: string;
  turnBatchId: string;
  factId: string;
}

interface EntityDepartureRow {
  run_id: string;
  migration_id: string;
  source_occurrence_id: string;
  destination_world_id: string;
  entity_id: string;
  receipt_json: string;
  receipt_digest: string;
  created_at: string;
}

function prefixedDigest(value: string): `sha256:${string}` {
  const normalized = value.startsWith("sha256:") ? value : `sha256:${value}`;
  if (!/^sha256:[0-9a-f]{64}$/.test(normalized)) {
    throw new StationZeroV3EntityDepartureError("Retained Game digest is not sha256:<64 lowercase hex>");
  }
  return normalized as `sha256:${string}`;
}

function requireIdentity(value: string, label: string, prefix?: string): string {
  if (!value || value !== value.trim()) {
    throw new StationZeroV3EntityDepartureError(`${label} must be non-empty and trimmed`);
  }
  if (prefix && !value.startsWith(prefix)) {
    throw new StationZeroV3EntityDepartureError(`${label} must start with ${prefix}`);
  }
  return value;
}

function parsedReceipt(row: EntityDepartureRow): EntityDepartureReceipt {
  let parsed: unknown;
  try {
    parsed = JSON.parse(row.receipt_json);
  } catch (error) {
    throw new StationZeroV3EntityDepartureError("Retained Entity Departure receipt JSON is invalid", {
      cause: error,
    });
  }
  validateProtocolJson(parsed);
  if (protocolDigest(parsed) !== row.receipt_digest) {
    throw new StationZeroV3EntityDepartureError(
      "Retained Entity Departure receipt digest differs from content",
    );
  }
  if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new StationZeroV3EntityDepartureError("Retained Entity Departure receipt is not an object");
  }
  const receipt = parsed as unknown as EntityDepartureReceipt;
  if (
    receipt.schemaVersion !== 1 ||
    receipt.kind !== "ordivon.world.entity-departure-receipt" ||
    receipt.migrationId !== row.migration_id ||
    receipt.sourceWorldId !== row.run_id ||
    receipt.destinationWorldId !== row.destination_world_id ||
    receipt.entityId !== row.entity_id ||
    receipt.sourceOccurrenceId !== row.source_occurrence_id
  ) {
    throw new StationZeroV3EntityDepartureError(
      "Retained Entity Departure row differs from receipt content",
    );
  }
  return receipt;
}

function sourceFact(
  receipt: StationZeroV3TurnReceipt,
  factId: string,
  entityId: string,
): Extract<StationZeroFact, { kind: "actor_life_state_changed" }> {
  const fact = receipt.record.resolution.facts.find((candidate) => candidate.factId === factId);
  if (
    !fact ||
    fact.kind !== "actor_life_state_changed" ||
    fact.actorId !== entityId ||
    fact.after !== "extracted"
  ) {
    throw new StationZeroV3EntityDepartureError(
      `Fact ${factId} is not an extracted life-state consequence for ${entityId}`,
    );
  }
  return fact;
}

function sourceResolution(
  receipt: StationZeroV3TurnReceipt,
  factId: string,
  entityId: string,
): StationZeroIntentResolution {
  const resolution = receipt.record.resolution.intentResolutions.find((candidate) =>
    candidate.factIds.includes(factId));
  if (
    !resolution ||
    resolution.actorId !== entityId ||
    resolution.status !== "executed" ||
    resolution.reason !== "actor_extracted" ||
    !resolution.verificationPassed
  ) {
    throw new StationZeroV3EntityDepartureError(
      `Fact ${factId} is not bound to a verified executed actor_extracted resolution`,
    );
  }
  return resolution;
}

function sourceIntent(
  receipt: StationZeroV3TurnReceipt,
  resolution: StationZeroIntentResolution,
  entityId: string,
): Extract<StationZeroActorIntent, { kind: "extract" }> {
  for (const plan of receipt.record.batch.factionPlans) {
    const intent = plan.actorIntents.find((candidate) => candidate.intentId === resolution.intentId);
    if (intent) {
      if (intent.kind !== "extract" || intent.actorId !== entityId) {
        throw new StationZeroV3EntityDepartureError(
          `Intent ${resolution.intentId} is not the entity's retained extract Intent`,
        );
      }
      return intent;
    }
  }
  throw new StationZeroV3EntityDepartureError(
    `Retained Turn Batch does not contain Intent ${resolution.intentId}`,
  );
}

export class StationZeroV3EntityDeparture {
  readonly store: StationZeroV3Store;

  constructor(store: StationZeroV3Store) {
    this.store = store;
    this.store.db.exec(`
      CREATE TABLE IF NOT EXISTS station_zero_v3_entity_departure (
        run_id TEXT NOT NULL,
        migration_id TEXT NOT NULL,
        source_occurrence_id TEXT NOT NULL,
        destination_world_id TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        receipt_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (run_id, migration_id),
        UNIQUE (run_id, source_occurrence_id),
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
      );
    `);
  }

  authorize(
    runId: string,
    request: StationZeroV3EntityDepartureRequest,
  ): EntityDepartureReceipt {
    requireIdentity(runId, "Game Run identity", "run:");
    requireIdentity(request.migrationId, "Entity Migration identity", "migration:");
    requireIdentity(request.destinationWorldId, "Destination World identity");
    requireIdentity(request.entityId, "Entity identity");
    requireIdentity(request.turnBatchId, "Turn Batch identity", "turn-batch:");
    requireIdentity(request.factId, "Source Fact identity", "fact:");

    const turn = this.store.turnReceiptByBatch(runId, request.turnBatchId);
    if (!turn) {
      throw new StationZeroV3EntityDepartureError(
        `No retained Turn Receipt for ${request.turnBatchId}`,
      );
    }
    const fact = sourceFact(turn, request.factId, request.entityId);
    const resolution = sourceResolution(turn, fact.factId, request.entityId);
    const intent = sourceIntent(turn, resolution, request.entityId);
    const actor = turn.state.actors[request.entityId];
    if (!actor || actor.lifeState !== "extracted") {
      throw new StationZeroV3EntityDepartureError(
        `Retained state does not confirm extracted Entity ${request.entityId}`,
      );
    }

    const factDigest = protocolDigest(fact as unknown as ProtocolJson);
    const intentDigest = protocolDigest(intent as unknown as ProtocolJson);
    const recordDigest = prefixedDigest(turn.recordDigest);
    const stateDigestAfter = prefixedDigest(turn.stateDigest);
    const occurrence = {
      schemaVersion: 1,
      kind: "ordivon.game.station-zero-v3-entity-departure-occurrence",
      runId,
      turnBatchId: turn.turnBatchId,
      recordDigest,
      factId: fact.factId,
      factDigest,
      intentId: intent.intentId,
      intentDigest,
      entityId: request.entityId,
      lifeStateAfter: "extracted",
    } satisfies Record<string, ProtocolJson>;
    const sourceOccurrenceDigest = protocolDigest(occurrence);
    const receipt: EntityDepartureReceipt = {
      schemaVersion: 1,
      kind: "ordivon.world.entity-departure-receipt",
      migrationId: request.migrationId,
      entityId: request.entityId,
      sourceWorldId: runId,
      destinationWorldId: request.destinationWorldId,
      sourceOccurrenceId: `entity-departure:${sourceOccurrenceDigest.slice("sha256:".length)}`,
      sourceOccurrenceDigest,
      authority: {
        authorityId: `ordivon.game.station-zero-v3:${runId}`,
        mechanism: "station-zero-v3-verified-extraction.v1",
        evidence: {
          runId,
          turnSequence: turn.turnSequence,
          turnBatchId: turn.turnBatchId,
          recordDigest,
          stateDigestAfter,
          factId: fact.factId,
          factDigest,
          intentId: intent.intentId,
          intentDigest,
          resolutionStatus: "executed",
          resolutionReason: "actor_extracted",
          verificationPassed: true,
          entityLifeStateAfter: "extracted",
          retainedReplayVerified: true,
        },
      },
    };
    validateProtocolJson(receipt as unknown as ProtocolJson);
    return this.commitExact(runId, receipt);
  }

  receipt(runId: string, migrationId: string): EntityDepartureReceipt | null {
    const row = this.store.db.prepare(`SELECT * FROM station_zero_v3_entity_departure
      WHERE run_id = ? AND migration_id = ?`).get(runId, migrationId) as
      EntityDepartureRow | undefined;
    return row ? parsedReceipt(row) : null;
  }

  private commitExact(runId: string, receipt: EntityDepartureReceipt): EntityDepartureReceipt {
    const receiptJson = protocolCanonicalJson(receipt as unknown as ProtocolJson);
    const receiptDigest = protocolDigest(receipt as unknown as ProtocolJson);
    this.store.db.exec("BEGIN IMMEDIATE");
    try {
      const retainedByMigration = this.store.db.prepare(`SELECT * FROM station_zero_v3_entity_departure
        WHERE run_id = ? AND migration_id = ?`).get(runId, receipt.migrationId) as
        EntityDepartureRow | undefined;
      if (retainedByMigration) {
        const retained = parsedReceipt(retainedByMigration);
        if (
          retainedByMigration.receipt_digest !== receiptDigest ||
          retainedByMigration.receipt_json !== receiptJson
        ) {
          throw new StationZeroV3EntityDepartureConflict(
            "Entity Migration identity is already bound to another source departure meaning",
          );
        }
        this.store.db.exec("COMMIT");
        return retained;
      }
      const retainedByOccurrence = this.store.db.prepare(`SELECT * FROM station_zero_v3_entity_departure
        WHERE run_id = ? AND source_occurrence_id = ?`).get(runId, receipt.sourceOccurrenceId) as
        EntityDepartureRow | undefined;
      if (retainedByOccurrence) {
        throw new StationZeroV3EntityDepartureConflict(
          `Source Entity departure is already authorized by ${retainedByOccurrence.migration_id}`,
        );
      }
      this.store.db.prepare(`INSERT INTO station_zero_v3_entity_departure
        (run_id, migration_id, source_occurrence_id, destination_world_id, entity_id,
         receipt_json, receipt_digest, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)`).run(
          runId,
          receipt.migrationId,
          receipt.sourceOccurrenceId,
          receipt.destinationWorldId,
          receipt.entityId,
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
