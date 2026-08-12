import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import {
  StationZeroV3EntityDeparture,
  StationZeroV3EntityDepartureConflict,
  StationZeroV3EntityDepartureError,
  StationZeroV3Store,
  StationZeroV3TurnService,
  type StationZeroFactionId,
} from "../src/station-zero-v3/index.ts";
import { protocolDigest } from "../src/host-contract/canonical.ts";

const actors: Record<StationZeroFactionId, string> = {
  rescue: "medic-reyes",
  pirate: "pirate-captain-veyra",
  swarm: "hive-alpha",
};

function fixture(name: string) {
  const directory = mkdtempSync(join(tmpdir(), `ordivon-game-w2-departure-${name}-`));
  const dbPath = join(directory, "game.sqlite3");
  const runId = `run:w2-departure:${name}`;
  const store = new StationZeroV3Store(dbPath);
  store.createRun({ runId, seed: `w2-departure-${name}` });
  const service = new StationZeroV3TurnService(store);
  const planning = service.openPlanning(runId);
  for (const factionId of ["rescue", "pirate", "swarm"] as const) {
    const actorId = actors[factionId];
    service.submitPlan(runId, planning.planningId, {
      planId: `plan:w2-departure:${name}:${factionId}`,
      factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      standingOrderRevision: planning.standingOrderRevision,
      commanderActions: [],
      actorIntents: [factionId === "rescue" ? {
        intentId: `intent:w2-departure:${name}:extract`,
        actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "extract",
        extractionId: `extraction:w2-departure:${name}`,
      } : {
        intentId: `intent:w2-departure:${name}:${factionId}:wait`,
        actorId,
        factionId,
        expectedWorldRevision: planning.worldRevision,
        expectedTurn: planning.turn,
        kind: "wait",
      }],
      committedBy: factionId === "rescue" ? "player:w2-departure" : `agent:${factionId}`,
    });
  }
  service.execute(runId, planning.planningId);
  const turn = store.latestTurnReceipt(runId);
  if (!turn) throw new Error("missing retained Turn Receipt");
  const fact = turn.record.resolution.facts.find((candidate) =>
    candidate.kind === "actor_life_state_changed" &&
    candidate.actorId === "medic-reyes" &&
    candidate.after === "extracted");
  if (!fact) throw new Error("missing extracted Actor life-state Fact");
  return { directory, dbPath, runId, store, turn, fact };
}

function request(value: ReturnType<typeof fixture>, migrationId = "migration:w2:medic", destinationWorldId = "security-world:w2:B") {
  return {
    migrationId,
    destinationWorldId,
    entityId: "medic-reyes",
    turnBatchId: value.turn.turnBatchId,
    factId: value.fact.factId,
  };
}

test("verified retained extract authorizes one durable Entity departure without mutating Game state", () => {
  const value = fixture("durable");
  try {
    const before = value.turn.stateDigest;
    const departure = new StationZeroV3EntityDeparture(value.store);
    const receipt = departure.authorize(value.runId, request(value));
    assert.equal(receipt.kind, "ordivon.world.entity-departure-receipt");
    assert.equal(receipt.entityId, "medic-reyes");
    assert.equal(receipt.authority.evidence.resolutionStatus, "executed");
    assert.equal(receipt.authority.evidence.resolutionReason, "actor_extracted");
    assert.equal(receipt.authority.evidence.verificationPassed, true);
    assert.equal(receipt.authority.evidence.entityLifeStateAfter, "extracted");
    assert.equal(value.turn.state.actors["medic-reyes"]?.lifeState, "extracted");
    assert.equal(value.turn.state.actors["medic-reyes"]?.position.zoneId, "rescue-airlock");
    assert.deepEqual(departure.authorize(value.runId, request(value)), receipt);
    value.store.close();
    const fresh = new StationZeroV3Store(value.dbPath);
    try {
      const reopened = new StationZeroV3EntityDeparture(fresh).receipt(value.runId, receipt.migrationId);
      assert.deepEqual(reopened, receipt);
      assert.equal(fresh.latestTurnReceipt(value.runId)?.stateDigest, before);
      assert.equal(protocolDigest(reopened!), protocolDigest(receipt));
    } finally { fresh.close(); }
  } finally {
    try { value.store.close(); } catch {}
    rmSync(value.directory, { recursive: true, force: true });
  }
});

test("one source departure cannot authorize two Migration identities", () => {
  const value = fixture("no-fork");
  try {
    const departure = new StationZeroV3EntityDeparture(value.store);
    const first = departure.authorize(value.runId, request(value, "migration:w2:first"));
    assert.throws(
      () => departure.authorize(value.runId, request(value, "migration:w2:fork")),
      StationZeroV3EntityDepartureConflict,
    );
    assert.deepEqual(departure.receipt(value.runId, first.migrationId), first);
    const count = value.store.db.prepare(
      "SELECT COUNT(*) count FROM station_zero_v3_entity_departure WHERE run_id = ?",
    ).get(value.runId) as { count: number };
    assert.equal(count.count, 1);
  } finally { value.store.close(); rmSync(value.directory, { recursive: true, force: true }); }
});

test("one Migration identity cannot change destination after departure authorization", () => {
  const value = fixture("identity-conflict");
  try {
    const departure = new StationZeroV3EntityDeparture(value.store);
    departure.authorize(value.runId, request(value));
    assert.throws(
      () => departure.authorize(value.runId, request(value, "migration:w2:medic", "security-world:w2:C")),
      StationZeroV3EntityDepartureConflict,
    );
  } finally { value.store.close(); rmSync(value.directory, { recursive: true, force: true }); }
});

test("forged or non-departure Facts cannot authorize Entity migration", () => {
  const value = fixture("fact-validation");
  try {
    const departure = new StationZeroV3EntityDeparture(value.store);
    assert.throws(
      () => departure.authorize(value.runId, { ...request(value), factId: "fact:forged:departure" }),
      StationZeroV3EntityDepartureError,
    );
    const otherFact = value.turn.record.resolution.facts.find((candidate) =>
      candidate.factId !== value.fact.factId && candidate.kind !== "actor_life_state_changed");
    assert.ok(otherFact);
    assert.throws(
      () => departure.authorize(value.runId, { ...request(value), factId: otherFact.factId }),
      StationZeroV3EntityDepartureError,
    );
    const count = value.store.db.prepare(
      "SELECT COUNT(*) count FROM station_zero_v3_entity_departure WHERE run_id = ?",
    ).get(value.runId) as { count: number };
    assert.equal(count.count, 0);
  } finally { value.store.close(); rmSync(value.directory, { recursive: true, force: true }); }
});
