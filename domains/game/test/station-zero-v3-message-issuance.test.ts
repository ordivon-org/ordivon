import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import {
  STATION_ZERO_V3_MESSAGE_KIND,
  StationZeroV3MessageIssuance,
  StationZeroV3MessageIssuanceConflict,
  StationZeroV3MessageIssuanceError,
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
  const directory = mkdtempSync(join(tmpdir(), `ordivon-game-w2-message-${name}-`));
  const dbPath = join(directory, "game.sqlite3");
  const runId = `run:w2-message:${name}`;
  const store = new StationZeroV3Store(dbPath);
  store.createRun({ runId, seed: `w2-message-${name}` });
  const service = new StationZeroV3TurnService(store);
  const planning = service.openPlanning(runId);
  for (const factionId of ["rescue", "pirate", "swarm"] as const) {
    const actorId = actors[factionId];
    service.submitPlan(runId, planning.planningId, {
      planId: `plan:w2-message:${name}:${factionId}`,
      factionId,
      expectedWorldRevision: planning.worldRevision,
      expectedTurn: planning.turn,
      standingOrderRevision: planning.standingOrderRevision,
      commanderActions: [],
      actorIntents: [factionId === "rescue" ? {
        intentId: `intent:w2-message:${name}:extract`, actorId, factionId,
        expectedWorldRevision: planning.worldRevision, expectedTurn: planning.turn,
        kind: "extract", extractionId: `extraction:w2-message:${name}`,
      } : {
        intentId: `intent:w2-message:${name}:${factionId}:wait`, actorId, factionId,
        expectedWorldRevision: planning.worldRevision, expectedTurn: planning.turn, kind: "wait",
      }],
      committedBy: factionId === "rescue" ? "player:w2-message" : `agent:${factionId}`,
    });
  }
  service.execute(runId, planning.planningId);
  const turn = store.latestTurnReceipt(runId);
  if (!turn) throw new Error("missing turn receipt");
  const fact = turn.record.resolution.facts.find((candidate) =>
    candidate.kind === "item_extracted" && candidate.actorId === "medic-reyes" && candidate.itemId === "medkit");
  if (!fact) throw new Error("missing extracted medkit fact");
  return { directory, dbPath, runId, store, turn, fact };
}

function request(value: ReturnType<typeof fixture>, messageId = "message:w2:one", destinationWorldId = "security-world:w2:B") {
  return {
    messageId,
    destinationWorldId,
    messageKind: STATION_ZERO_V3_MESSAGE_KIND,
    turnBatchId: value.turn.turnBatchId,
    factId: value.fact.factId,
    sourceFactionId: "rescue" as const,
  };
}

test("Message Issuance binds a visible retained Fact and survives reopen", () => {
  const value = fixture("reopen");
  try {
    const before = value.turn.stateDigest;
    const issuance = new StationZeroV3MessageIssuance(value.store);
    const issued = issuance.issue(value.runId, request(value));
    assert.equal(issued.receipt.kind, "ordivon.world.message-issuance-receipt");
    assert.equal(issued.receipt.provenanceDigest, protocolDigest(issued.provenance));
    assert.equal(issued.receipt.payloadDigest, protocolDigest(issued.payload));
    assert.equal(issued.payload.fact.factId, value.fact.factId);
    assert.equal(issued.provenance.visibleToSourceFaction, true);
    assert.deepEqual(issuance.issue(value.runId, request(value)), issued);
    value.store.close();
    const fresh = new StationZeroV3Store(value.dbPath);
    try {
      const reopened = new StationZeroV3MessageIssuance(fresh).issued(value.runId, issued.receipt.messageId);
      assert.deepEqual(reopened, issued);
      assert.equal(fresh.latestTurnReceipt(value.runId)?.stateDigest, before);
    } finally { fresh.close(); }
  } finally {
    try { value.store.close(); } catch {}
    rmSync(value.directory, { recursive: true, force: true });
  }
});

test("same Message identity cannot silently change destination", () => {
  const value = fixture("identity-conflict");
  try {
    const issuance = new StationZeroV3MessageIssuance(value.store);
    issuance.issue(value.runId, request(value));
    assert.throws(
      () => issuance.issue(value.runId, request(value, "message:w2:one", "security-world:w2:C")),
      StationZeroV3MessageIssuanceConflict,
    );
  } finally { value.store.close(); rmSync(value.directory, { recursive: true, force: true }); }
});

test("one source Fact can authorize multiple independently identified Messages", () => {
  const value = fixture("broadcast");
  try {
    const issuance = new StationZeroV3MessageIssuance(value.store);
    const first = issuance.issue(value.runId, request(value, "message:w2:first", "security-world:w2:B"));
    const second = issuance.issue(value.runId, request(value, "message:w2:second", "security-world:w2:C"));
    assert.equal(first.receipt.sourceOccurrenceId, second.receipt.sourceOccurrenceId);
    assert.equal(first.receipt.sourceOccurrenceDigest, second.receipt.sourceOccurrenceDigest);
    assert.notEqual(first.receipt.messageId, second.receipt.messageId);
    assert.notEqual(first.receipt.destinationWorldId, second.receipt.destinationWorldId);
    const count = value.store.db.prepare("SELECT COUNT(*) count FROM station_zero_v3_message_issuance WHERE run_id = ?")
      .get(value.runId) as { count: number };
    assert.equal(count.count, 2);
  } finally { value.store.close(); rmSync(value.directory, { recursive: true, force: true }); }
});

test("a faction cannot issue a retained Fact it did not observe", () => {
  const value = fixture("visibility");
  try {
    assert.equal(value.turn.record.resolution.observations.rescue.visibleFactIds.includes(value.fact.factId), true);
    assert.equal(value.turn.record.resolution.observations.pirate.visibleFactIds.includes(value.fact.factId), false);
    const issuance = new StationZeroV3MessageIssuance(value.store);
    assert.throws(
      () => issuance.issue(value.runId, { ...request(value), sourceFactionId: "pirate" }),
      StationZeroV3MessageIssuanceError,
    );
    const count = value.store.db.prepare("SELECT COUNT(*) count FROM station_zero_v3_message_issuance WHERE run_id = ?")
      .get(value.runId) as { count: number };
    assert.equal(count.count, 0);
  } finally { value.store.close(); rmSync(value.directory, { recursive: true, force: true }); }
});
